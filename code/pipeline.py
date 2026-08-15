#!/usr/bin/env python3
"""
Full pipeline, LSH-accelerated: image folder -> SimHash fingerprints -> overlap
detection via HammingLSHIndex -> join non-overlapping images to their geotags ->
render the interactive map. One command instead of the three-script Makefile
flow, built for pools too large for the O(n^2) exhaustive scan in
simhash_dedupe.find_overlaps() (see lsh.py for why).

Usage:
  python3 pipeline.py <image_dir> <geotags.csv> --threshold 10
  python3 pipeline.py <image_dir> <geotags.csv> --threshold 10 --num-bands 12 --output-map map.html

Dependencies: Pillow, numpy (same as simhash_dedupe.py)
"""

import argparse
import csv
import json
import sys
import time
from pathlib import Path

from simhash_dedupe import list_images, compute_image_hash, hamming_distance
from lsh import HammingLSHIndex, recommended_num_bands
from plot_locations import TEMPLATE as MAP_TEMPLATE


def format_elapsed(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.2f}s"
    minutes, seconds = divmod(seconds, 60)
    return f"{int(minutes)}m {seconds:.1f}s"


def find_overlaps_lsh(image_paths, grid, cell, bits, threshold, num_bands, verbose):
    """Same pool/seen algorithm as simhash_dedupe.find_overlaps(), but each new
    image is checked against an LSH index instead of scanning every seen hash."""
    index = HammingLSHIndex(bits=bits, num_bands=num_bands)
    overlaps = []

    if not image_paths:
        return overlaps

    first = image_paths[0]
    first_hash = compute_image_hash(first, grid, cell, bits)
    index.insert(first, first_hash)
    if verbose:
        print(f"[seen]    {first.name}  (first image)")

    for path in image_paths[1:]:
        h = compute_image_hash(path, grid, cell, bits)
        matches = index.query_within(h, threshold, hamming_distance)

        if matches:
            best_path, best_distance = matches[0]
            overlaps.append({
                "image": str(path),
                "matched_with": str(best_path),
                "hamming_distance": best_distance,
            })
            if verbose:
                print(f"[overlap] {path.name}  ~=  {best_path.name}  (distance={best_distance})")
        else:
            if verbose:
                print(f"[unique]  {path.name}  (no candidate within threshold)")

        index.insert(path, h)

    return overlaps


def load_geotags(csv_path: Path, names: set):
    rows = {}
    with open(csv_path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row["image_name"] in names:
                rows[row["image_name"]] = row
    return rows


def main():
    parser = argparse.ArgumentParser(
        description="LSH-accelerated overlap detection + geotag join + map render, in one pass."
    )
    parser.add_argument("image_dir", type=Path, help="Folder of images")
    parser.add_argument("geotags_csv", type=Path, help="CSV with image_name, latitude, longitude, altitude [meter]")
    parser.add_argument("--threshold", type=int, default=10,
                         help="Max Hamming distance to consider two images overlapping (default: 10)")
    parser.add_argument("--bits", type=int, default=64, help="SimHash length in bits (default: 64)")
    parser.add_argument("--grid", type=int, default=8, help="Grid size, grid x grid cells (default: 8)")
    parser.add_argument("--cell", type=int, default=8, help="Pixel size of each grid cell (default: 8)")
    parser.add_argument("--num-bands", type=int, default=None,
                         help="LSH band count (default: threshold + 1, the minimum that guarantees recall)")
    parser.add_argument("--output-overlaps", type=Path, default=Path("overlaps.json"))
    parser.add_argument("--output-locations", type=Path, default=Path("non_overlapping_locations.json"))
    parser.add_argument("--output-map", type=Path, default=Path("map.html"))
    parser.add_argument("--quiet", action="store_true", help="Suppress per-image progress output")
    args = parser.parse_args()

    if not args.image_dir.is_dir():
        print(f"Error: {args.image_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    pipeline_start = time.perf_counter()

    step_start = time.perf_counter()
    image_paths = list_images(args.image_dir)
    if not image_paths:
        print(f"No images found in {args.image_dir}", file=sys.stderr)
        sys.exit(1)
    list_elapsed = time.perf_counter() - step_start

    num_bands = args.num_bands or recommended_num_bands(args.threshold)
    if num_bands <= args.threshold:
        print(f"Warning: --num-bands {num_bands} <= threshold {args.threshold}; "
              f"recall is not guaranteed (some true matches may be missed). "
              f"Use at least {recommended_num_bands(args.threshold)} bands to guarantee recall.",
              file=sys.stderr)

    print(f"Found {len(image_paths)} images in {args.image_dir}  [{format_elapsed(list_elapsed)}]")
    print(f"threshold={args.threshold} bits (out of {args.bits}), num_bands={num_bands}\n")

    step_start = time.perf_counter()
    overlaps = find_overlaps_lsh(
        image_paths, grid=args.grid, cell=args.cell, bits=args.bits,
        threshold=args.threshold, num_bands=num_bands, verbose=not args.quiet,
    )
    args.output_overlaps.write_text(json.dumps(overlaps, indent=2))
    overlap_elapsed = time.perf_counter() - step_start
    print(f"\n{len(overlaps)} overlapping image(s) found out of {len(image_paths)} total. "
          f"Wrote {args.output_overlaps}  [{format_elapsed(overlap_elapsed)}]")

    step_start = time.perf_counter()
    all_names = {p.name for p in image_paths}
    overlapping_names = {Path(entry["image"]).name for entry in overlaps}
    nonoverlapping_names = all_names - overlapping_names

    rows = load_geotags(args.geotags_csv, nonoverlapping_names)
    missing = nonoverlapping_names - set(rows.keys())
    if missing:
        print(f"Warning: {len(missing)} non-overlapping image(s) had no CSV row: {sorted(missing)[:5]}...")

    points = []
    for name in sorted(rows.keys()):
        row = rows[name]
        points.append({
            "image_name": name,
            "latitude": float(row["latitude"]),
            "longitude": float(row["longitude"]),
            "altitude": float(row["altitude [meter]"]),
        })
    args.output_locations.write_text(json.dumps(points, indent=2))
    join_elapsed = time.perf_counter() - step_start
    print(f"{len(points)} non-overlapping image(s) with coordinates. Wrote {args.output_locations}  "
          f"[{format_elapsed(join_elapsed)}]")

    step_start = time.perf_counter()
    html = MAP_TEMPLATE.format(count=len(points), points_json=json.dumps(points))
    args.output_map.write_text(html)
    map_elapsed = time.perf_counter() - step_start
    print(f"Wrote map with {len(points)} points to {args.output_map}  [{format_elapsed(map_elapsed)}]")

    total_elapsed = time.perf_counter() - pipeline_start
    print(f"\nTotal time: {format_elapsed(total_elapsed)}")


if __name__ == "__main__":
    main()
