#!/usr/bin/env python3
import json, os, glob, time

ROOT = "/Users/gripet/.gemini/antigravity/scratch/breathe-window"
CAT = os.path.join(ROOT, "assets", "data", "catalog.json")
LOC = os.path.join(ROOT, "assets", "data", "locations.json")
SPEC = os.path.join(ROOT, "scripts", "window_generation_spec.json")
IMG_DIR = os.path.join(ROOT, "assets", "images")

cat = json.load(open(CAT, encoding="utf-8"))
locs = json.load(open(LOC, encoding="utf-8"))
spec = json.load(open(SPEC, encoding="utf-8")) if os.path.exists(SPEC) else {}

custom_cities = [l["name"] for l in locs if l.get("hasCustomImages")]

for city in custom_cities:
    cards = cat.get(city, [])
    print(f"\n==========================================")
    print(f"CITY: {city} (in spec: {city in spec})")
    print(f"==========================================")
    
    city_spec = spec.get(city, {})
    spec_items = {item["bucket"]: item for item in city_spec.get("items", [])}
    
    for c in cards:
        bucket = c.get("bucket")
        title = c.get("title")
        body = c.get("body")
        img = c.get("image")
        
        img_basename = os.path.basename(img)
        img_path = os.path.join(IMG_DIR, img_basename)
        mtime_str = "N/A"
        size_str = "N/A"
        if os.path.exists(img_path):
            mtime = os.path.getmtime(img_path)
            mtime_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(mtime))
            size_str = f"{os.path.getsize(img_path)//1024}KB"
            
        spec_item = spec_items.get(bucket)
        spec_zh = spec_item.get("zh", "NO SPEC") if spec_item else "NO SPEC"
        
        print(f"[{bucket}] {title} | {img_basename} ({size_str}, {mtime_str})")
        print(f"  Catalog: {body[:60]}...")
        if spec_zh != "NO SPEC":
            print(f"  SpecZH:  {spec_zh[:80]}...")
