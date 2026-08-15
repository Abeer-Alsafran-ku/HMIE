#!/usr/bin/env python3
"""
Near-duplicate / overlapping image detection using a custom SimHash + Hamming distance.

Algorithm (as specified):
  1. Compute a SimHash for every image in the pool.
  2. Pop the first image from the pool, add it (with its hash) to `seen`.
  3. While the pool is not empty:
       - pop the next image from the pool
       - compare its hash (Hamming distance) against every hash already in `seen`
       - if the closest match is within `threshold` bits, record it as an overlap
       - add the image to `seen` regardless, so later images can be compared against it too
  4. The final overlap list is the set of images that matched something already seen.

SimHash construction (Charikar-style weighted feature hashing, built from scratch):
  - Resize image to a GRID x GRID grid of cells and take the mean grayscale intensity
    of each cell as an "average" feature (weight = deviation from the image's global mean).
  - Add horizontal/vertical gradient-between-cells features (weighted higher) so the
    hash is sensitive to structure/edges, not just brightness.
  - Each feature is a token (e.g. "avg:2:5"); hash the token to get a pseudo-random
    BITS-bit vector; add +weight where that bit is 1, -weight where it's 0, accumulated
    across all features into a running float vector.
  - The final hash bit i is 1 if the accumulated vector's component i is >= 0, else 0.

Usage:
  python3 simhash_dedupe.py /path/to/image/folder --threshold 10
  python3 simhash_dedupe.py /path/to/image/folder --threshold 10 --output overlaps.json

Dependencies: Pillow, numpy (pip install pillow numpy)
"""

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

from PIL import Image
import numpy as np

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp", ".gif"}


def list_images(directory: Path):
    return sorted(
        p for p in directory.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    )


def extract_features(path: Path, grid: int, cell: int):
    img = Image.open(path).convert("L").resize((grid * cell, grid * cell))
    arr = np.asarray(img, dtype=np.float64)

    # average intensity per grid cell
    block_avg = arr.reshape(grid, cell, grid, cell).mean(axis=(1, 3))
    global_mean = block_avg.mean()

    features = []

    for i in range(grid):
        for j in range(grid):
            weight = block_avg[i, j] - global_mean
            features.append((f"avg:{i}:{j}", weight))

    # horizontal gradients between adjacent cells (weighted higher: edges carry more
    # perceptual signal than raw brightness and are more robust to lighting changes)
    for i in range(grid):
        for j in range(grid - 1):
            weight = (block_avg[i, j + 1] - block_avg[i, j]) * 2.0
            features.append((f"gx:{i}:{j}", weight))

    # vertical gradients between adjacent cells
    for i in range(grid - 1):
        for j in range(grid):
            weight = (block_avg[i + 1, j] - block_avg[i, j]) * 2.0
            features.append((f"gy:{i}:{j}", weight))

    return features


def simhash(features, bits: int) -> int:
    v = np.zeros(bits, dtype=np.float64)
    needed_bytes = math.ceil(bits / 8)

    for token, weight in features:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        hint = int.from_bytes(digest[:needed_bytes], "big")
        for b in range(bits):
            bit = (hint >> b) & 1
            v[b] += weight if bit else -weight

    hash_value = 0
    for b in range(bits):
        if v[b] >= 0:
            hash_value |= (1 << b)
    return hash_value


def hamming_distance(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


def compute_image_hash(path: Path, grid: int, cell: int, bits: int) -> int:
    features = extract_features(path, grid, cell)
    return simhash(features, bits)


def find_overlaps(image_paths, grid: int, cell: int, bits: int, threshold: int, verbose: bool):
    pool = [(p, compute_image_hash(p, grid, cell, bits)) for p in image_paths]

    if not pool:
        return [], []

    seen = [pool.pop(0)]
    if verbose:
        print(f"[seen]    {seen[0][0].name}  (first image, hash={seen[0][1]:0{bits}b})")

    overlaps = []

    while pool:
        path, h = pool.pop(0)

        best_match_path = None
        best_distance = None
        for seen_path, seen_hash in seen:
            d = hamming_distance(h, seen_hash)
            if best_distance is None or d < best_distance:
                best_distance = d
                best_match_path = seen_path

        if best_distance is not None and best_distance <= threshold:
            overlaps.append({
                "image": str(path),
                "matched_with": str(best_match_path),
                "hamming_distance": best_distance,
            })
            if verbose:
                print(f"[overlap] {path.name}  ~=  {best_match_path.name}  (distance={best_distance})")
        else:
            if verbose:
                print(f"[unique]  {path.name}  (closest distance={best_distance})")

        seen.append((path, h))

    return overlaps, seen


def main():
    parser = argparse.ArgumentParser(description="Detect overlapping/similar images via SimHash + Hamming distance.")
    parser.add_argument("directory", type=Path, help="Folder containing the images to compare")
    parser.add_argument("--threshold", type=int, default=10,
                         help="Max Hamming distance (out of --bits) to consider two images overlapping (default: 10)")
    parser.add_argument("--bits", type=int, default=64, help="SimHash length in bits (default: 64)")
    parser.add_argument("--grid", type=int, default=8, help="Grid size, grid x grid cells (default: 8)")
    parser.add_argument("--cell", type=int, default=8, help="Pixel size of each grid cell (default: 8)")
    parser.add_argument("--output", type=Path, default=None, help="Optional path to write overlaps as JSON")
    parser.add_argument("--quiet", action="store_true", help="Suppress per-image progress output")
    args = parser.parse_args()

    if not args.directory.is_dir():
        print(f"Error: {args.directory} is not a directory", file=sys.stderr)
        sys.exit(1)

    image_paths = list_images(args.directory)
    if not image_paths:
        print(f"No images found in {args.directory}", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(image_paths)} images in {args.directory}")
    print(f"threshold={args.threshold} bits (out of {args.bits})\n")

    overlaps, _ = find_overlaps(
        image_paths, grid=args.grid, cell=args.cell, bits=args.bits,
        threshold=args.threshold, verbose=not args.quiet,
    )

    print(f"\n{len(overlaps)} overlapping image(s) found out of {len(image_paths)} total:")
    for entry in overlaps:
        print(f"  {Path(entry['image']).name}  ~=  {Path(entry['matched_with']).name}  "
              f"(distance={entry['hamming_distance']})")

    if args.output:
        args.output.write_text(json.dumps(overlaps, indent=2))
        print(f"\nWrote {len(overlaps)} overlaps to {args.output}")


if __name__ == "__main__":
    main()
