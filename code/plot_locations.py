#!/usr/bin/env python3
"""
Render a Leaflet HTML map from a JSON list of {image_name, latitude, longitude, altitude}.
Requires network access at view-time (loads Leaflet.js + OpenStreetMap tiles from CDN).

Usage:
  python3 plot_locations.py non_overlapping_locations.json --output map.html
"""

import argparse
import json
from pathlib import Path

TEMPLATE = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Non-overlapping image locations</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<style>
  html, body {{ margin: 0; padding: 0; height: 100%; font-family: -apple-system, sans-serif; }}
  #map {{ height: 100vh; width: 100%; }}
  .info-box {{
    position: absolute; top: 10px; right: 10px; z-index: 1000;
    background: white; padding: 10px 14px; border-radius: 6px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.3); font-size: 13px; max-width: 260px;
  }}
</style>
</head>
<body>
<div id="map"></div>
<div class="info-box"><b>{count}</b> non-overlapping image locations</div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
  const points = {points_json};

  const map = L.map('map');
  L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
    maxZoom: 22,
    attribution: '&copy; OpenStreetMap contributors'
  }}).addTo(map);

  const latlngs = points.map(p => [p.latitude, p.longitude]);
  const bounds = L.latLngBounds(latlngs);

  points.forEach((p, i) => {{
    L.circleMarker([p.latitude, p.longitude], {{
      radius: 6, color: '#1d4ed8', fillColor: '#3b82f6', fillOpacity: 0.85, weight: 1.5
    }})
    .bindPopup(`<b>${{p.image_name}}</b><br>lat: ${{p.latitude.toFixed(6)}}<br>lon: ${{p.longitude.toFixed(6)}}<br>alt: ${{p.altitude.toFixed(1)}} m`)
    .addTo(map);
  }});

  L.polyline(latlngs, {{ color: '#93c5fd', weight: 2, opacity: 0.6, dashArray: '4 4' }}).addTo(map);

  map.fitBounds(bounds, {{ padding: [40, 40] }});
</script>
</body>
</html>
"""


def main():
    parser = argparse.ArgumentParser(description="Render image locations on a Leaflet/OSM map.")
    parser.add_argument("locations_json", type=Path, help="JSON file: list of {image_name, latitude, longitude, altitude}")
    parser.add_argument("--output", type=Path, default=Path("map.html"), help="Output HTML file path")
    args = parser.parse_args()

    points = json.loads(args.locations_json.read_text())
    html = TEMPLATE.format(count=len(points), points_json=json.dumps(points))
    args.output.write_text(html)
    print(f"Wrote map with {len(points)} points to {args.output}")


if __name__ == "__main__":
    main()
