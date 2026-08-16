#!/usr/bin/env python3
import json, os

ROOT = "/Users/gripet/.gemini/antigravity/scratch/breathe-window"
CAT = os.path.join(ROOT, "assets", "data", "catalog.json")
SPEC = os.path.join(ROOT, "scripts", "window_generation_spec.json")
CORR = os.path.join(ROOT, "scripts", "window_correction_spec.json")

cat = json.load(open(CAT, encoding="utf-8"))
spec = json.load(open(SPEC, encoding="utf-8")) if os.path.exists(SPEC) else {}
corr = json.load(open(CORR, encoding="utf-8")) if os.path.exists(CORR) else {}

# Check all cities in spec
print(f"--- DETAILED COMPARISON FOR ALL SPEC CITIES ---")

for city, s_data in spec.items():
    if city not in cat:
        continue
    c_cards = {c["bucket"]: c for c in cat[city]}
    s_items = {i["bucket"]: i for i in s_data.get("items", [])}
    
    print(f"\n=======================================================")
    print(f"CITY: {city}")
    print(f"=======================================================")
    
    for bucket in ["世界一角", "科学自然", "他人在场", "思想火花", "旧物新看"]:
        card = c_cards.get(bucket)
        item = s_items.get(bucket)
        
        if not card or not item:
            continue
            
        print(f"\n>>> [{bucket}] Image: {card.get('image')}")
        print(f"    [CATALOG Title] {card.get('title')}")
        print(f"    [CATALOG Body]  {card.get('body')}")
        print(f"    [SPEC PromptZH] {item.get('zh')}")
