#!/usr/bin/env python3
import json, os

ROOT = "/Users/gripet/.gemini/antigravity/scratch/breathe-window"
CAT = os.path.join(ROOT, "assets", "data", "catalog.json")
LOC = os.path.join(ROOT, "assets", "data", "locations.json")
SPEC = os.path.join(ROOT, "scripts", "window_generation_spec.json")

cat = json.load(open(CAT, encoding="utf-8"))
locs = json.load(open(LOC, encoding="utf-8"))
custom_cities = [l["name"] for l in locs if l.get("hasCustomImages")]
spec = json.load(open(SPEC, encoding="utf-8")) if os.path.exists(SPEC) else {}

print(f"Total custom cities: {len(custom_cities)}")

differences = []

for city in custom_cities:
    cards = cat.get(city, [])
    city_spec = spec.get(city, {})
    spec_items = {item["bucket"]: item for item in city_spec.get("items", [])}
    
    city_diffs = []
    for c in cards:
        bucket = c.get("bucket")
        title = c.get("title")
        body = c.get("body")
        img = c.get("image")
        
        spec_item = spec_items.get(bucket)
        if spec_item:
            spec_zh = spec_item.get("zh", "")
            city_diffs.append({
                "bucket": bucket,
                "title": title,
                "body": body[:60] + "...",
                "spec_zh": spec_zh,
                "image": img
            })
        else:
            city_diffs.append({
                "bucket": bucket,
                "title": title,
                "body": body[:60] + "...",
                "spec_zh": "(NO SPEC ITEM)",
                "image": img
            })
    differences.append((city, city_diffs))

os.makedirs(os.path.join(ROOT, "scratch"), exist_ok=True)
with open(os.path.join(ROOT, "scratch", "city_spec_vs_catalog.json"), "w", encoding="utf-8") as f:
    json.dump(differences, f, ensure_ascii=False, indent=2)

print("Dumped city_spec_vs_catalog.json for all custom cities.")
