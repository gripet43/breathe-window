#!/usr/bin/env python3
import json, os

ROOT = "/Users/gripet/.gemini/antigravity/scratch/breathe-window"
CAT = os.path.join(ROOT, "assets", "data", "catalog.json")
LOC = os.path.join(ROOT, "assets", "data", "locations.json")
SPEC = os.path.join(ROOT, "scripts", "window_generation_spec.json")

cat = json.load(open(CAT, encoding="utf-8"))
locs = json.load(open(LOC, encoding="utf-8"))
spec = json.load(open(SPEC, encoding="utf-8")) if os.path.exists(SPEC) else {}

custom_cities = [l["name"] for l in locs if l.get("hasCustomImages")]

print(f"Total custom cities: {len(custom_cities)}")

# Check which cities are in spec
in_spec = [c for c in custom_cities if c in spec]
not_in_spec = [c for c in custom_cities if c not in spec]

print(f"Custom cities present in window_generation_spec.json: {len(in_spec)}")
print(f"Custom cities NOT in window_generation_spec.json: {len(not_in_spec)}")

print("\nCustom cities in spec:")
for c in in_spec:
    print(" -", c)

print("\nCustom cities NOT in spec:")
for c in not_in_spec:
    print(" -", c)
