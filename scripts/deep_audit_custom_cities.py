#!/usr/bin/env python3
import json, os

ROOT = "/Users/gripet/.gemini/antigravity/scratch/breathe-window"
CAT = os.path.join(ROOT, "assets", "data", "catalog.json")
LOC = os.path.join(ROOT, "assets", "data", "locations.json")
SPEC = os.path.join(ROOT, "scripts", "window_generation_spec.json")
CORR = os.path.join(ROOT, "scripts", "window_correction_spec.json")

cat = json.load(open(CAT, encoding="utf-8"))
locs = json.load(open(LOC, encoding="utf-8"))
custom_cities = [l["name"] for l in locs if l.get("hasCustomImages")]
spec = json.load(open(SPEC, encoding="utf-8")) if os.path.exists(SPEC) else {}
corr = json.load(open(CORR, encoding="utf-8")) if os.path.exists(CORR) else {}

print(f"Found {len(custom_cities)} custom cities.")

audit_results = []

for city in custom_cities:
    cards = cat.get(city, [])
    city_spec = spec.get(city, {})
    spec_items = {item["bucket"]: item for item in city_spec.get("items", [])}
    
    city_corr = corr.get(city, {})
    corr_items = {item["bucket"]: item for item in city_corr.get("corrections", [])}
    
    city_report = {
        "city": city,
        "cards": []
    }
    
    for c in cards:
        bucket = c.get("bucket")
        title = c.get("title")
        body = c.get("body")
        img = c.get("image")
        
        spec_item = spec_items.get(bucket)
        corr_item = corr_items.get(bucket)
        
        prompt_zh = ""
        prompt_en = ""
        source = "none"
        
        if corr_item:
            prompt_zh = corr_item.get("zh", "")
            prompt_en = corr_item.get("en", "")
            source = "correction_spec"
        elif spec_item:
            prompt_zh = spec_item.get("zh", "")
            prompt_en = spec_item.get("en", "")
            source = "generation_spec"
            
        city_report["cards"].append({
            "bucket": bucket,
            "title": title,
            "body": body,
            "image": img,
            "source": source,
            "prompt_zh": prompt_zh,
            "prompt_en": prompt_en
        })
        
    audit_results.append(city_report)

with open(os.path.join(ROOT, "scratch", "full_city_audit.json"), "w", encoding="utf-8") as f:
    json.dump(audit_results, f, ensure_ascii=False, indent=2)

print("Saved full_city_audit.json")
