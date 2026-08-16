#!/usr/bin/env python3
import json, os

ROOT = "/Users/gripet/.gemini/antigravity/scratch/breathe-window"
CAT = os.path.join(ROOT, "assets", "data", "catalog.json")
LOC = os.path.join(ROOT, "assets", "data", "locations.json")

cat = json.load(open(CAT, encoding="utf-8"))
locs = json.load(open(LOC, encoding="utf-8"))
custom_cities = [l["name"] for l in locs if l.get("hasCustomImages")]

print(f"Total custom cities: {len(custom_cities)}")

for city in custom_cities:
    cards = cat.get(city, [])
    print(f"\nCITY: {city}")
    for c in cards:
        print(f"  [{c['bucket']}] {c['title']} -> {c['image']}")
        print(f"      {c['body']}")
