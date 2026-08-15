#!/usr/bin/env python3
"""
Build a {image_name, latitude, longitude, altitude} JSON for the images that did NOT
overlap with anything, by combining:
  - the image folder (full set of images that went into simhash_dedupe.py)
  - overlaps.json produced by simhash_dedupe.py (--output overlaps.json)
  - the geotag CSV (must have columns: image_name, latitude, longitude, altitude [meter])

Non-overlapping = images in the folder whose name does not appear as "image" in overlaps.json.

Usage:
  python3 nonoverlap_locations.py <image_dir> <overlaps.json> <geotags.csv> --output non_overlapping_locations.json
"""

import argparse
import csv
import json
from pathlib import Path

from simhash_dedupe import list_images


def main():
    parser = argparse.ArgumentParser(description="Join non-overlapping images with their lat/lon from a geotag CSV.")
    parser.add_argument("image_dir", type=Path, help="Folder of images (same one passed to simhash_dedupe.py)")
    parser.add_argument("overlaps_json", type=Path, help="overlaps.json produced by simhash_dedupe.py")
    parser.add_argument("geotags_csv", type=Path, help="CSV with image_name, latitude, longitude, altitude [meter] columns")
    parser.add_argument("--output", type=Path, default=Path("non_overlapping_locations.json"))
    args = parser.parse_args()

    all_names = {p.name for p in list_images(args.image_dir)}

    overlaps = json.loads(args.overlaps_json.read_text())
    overlapping_names = {Path(entry["image"]).name for entry in overlaps}

    nonoverlapping_names = all_names - overlapping_names

    rows = {}
    with open(args.geotags_csv, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row["image_name"] in nonoverlapping_names:
                rows[row["image_name"]] = row

    missing = nonoverlapping_names - set(rows.keys())
    if missing:
        print(f"Warning: {len(missing)} non-overlapping image(s) had no CSV row: {sorted(missing)[:5]}...")

    out = []
    for name in sorted(rows.keys()):
        row = rows[name]
        out.append({
            "image_name": name,
            "latitude": float(row["latitude"]),
            "longitude": float(row["longitude"]),
            "altitude": float(row["altitude [meter]"]),
        })

    args.output.write_text(json.dumps(out, indent=2))
    print(f"{len(all_names)} total images, {len(overlapping_names)} overlapping, "
          f"{len(out)} non-overlapping with coordinates written to {args.output}")


if __name__ == "__main__":
    main()
