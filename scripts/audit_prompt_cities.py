#!/usr/bin/env python3
import json, os

ROOT = "/Users/gripet/.gemini/antigravity/scratch/breathe-window"
CAT = os.path.join(ROOT, "assets", "data", "catalog.json")
LOC = os.path.join(ROOT, "assets", "data", "locations.json")
SPEC = os.path.join(ROOT, "scripts", "window_generation_spec.json")
CORR = os.path.join(ROOT, "scripts", "window_correction_spec.json")

cat = json.load(open(CAT, encoding="utf-8"))
locs = json.load(open(LOC, encoding="utf-8"))
spec = json.load(open(SPEC, encoding="utf-8")) if os.path.exists(SPEC) else {}
corr = json.load(open(CORR, encoding="utf-8")) if os.path.exists(CORR) else {}

custom_cities = [l["name"] for l in locs if l.get("hasCustomImages")]

print("=== CHECKING ALL 80 CUSTOM CITIES ===")

mismatched_summary = []

for city in custom_cities:
    cards = cat.get(city, [])
    city_spec = spec.get(city, {})
    city_corr = corr.get(city, {})
    
    spec_items = {item["bucket"]: item for item in city_spec.get("items", [])}
    corr_items = {item["bucket"]: item for item in city_corr.get("corrections", [])}
    
    city_mismatches = []
    
    for c in cards:
        bucket = c.get("bucket")
        title = c.get("title", "")
        body = c.get("body", "")
        img = c.get("image", "")
        
        prompt = ""
        src = ""
        if bucket in corr_items:
            prompt = corr_items[bucket].get("zh", "")
            src = "correction"
        elif bucket in spec_items:
            prompt = spec_items[bucket].get("zh", "")
            src = "spec"
            
        if prompt:
            city_mismatches.append({
                "bucket": bucket,
                "title": title,
                "body": body,
                "prompt": prompt,
                "source": src,
                "image": img
            })
            
    if city_mismatches:
        mismatched_summary.append({
            "city": city,
            "count": len(city_mismatches),
            "cards": city_mismatches
        })

print(f"Total custom cities with spec/correction prompts: {len(mismatched_summary)}")

for item in mismatched_summary:
    print(f"\n==================================================")
    print(f"CITY: {item['city']} ({item['count']} cards with prompts)")
    print(f"==================================================")
    for c in item["cards"]:
        print(f"[{c['bucket']}] Title: {c['title']}")
        print(f"   Catalog: {c['body'][:65]}...")
        print(f"   Prompt:  {c['prompt'][:65]}...")
        print()

with open(os.path.join(ROOT, "scratch", "mismatched_summary.json"), "w", encoding="utf-8") as f:
    json.dump(mismatched_summary, f, ensure_ascii=False, indent=2)
