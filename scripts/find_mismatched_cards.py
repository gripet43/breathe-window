#!/usr/bin/env python3
import json, os, re

ROOT = "/Users/gripet/.gemini/antigravity/scratch/breathe-window"
AUDIT_FILE = os.path.join(ROOT, "scratch", "full_city_audit.json")

data = json.load(open(AUDIT_FILE, encoding="utf-8"))

print(f"Auditing {len(data)} cities...")

cards_list = []

for city_obj in data:
    city = city_obj["city"]
    for c in city_obj["cards"]:
        title = c["title"]
        body = c["body"]
        prompt = c["prompt_zh"]
        img = c["image"]
        bucket = c["bucket"]
        
        if not prompt or prompt == "":
            cards_list.append({
                "city": city,
                "bucket": bucket,
                "title": title,
                "body": body,
                "prompt": "(NO PROMPT RECORDED)",
                "image": img,
                "has_prompt": False
            })
            continue
            
        clean_p = prompt.replace("栏目：", "").replace("柔和水彩水粉手绘", "").replace("细微纸纹", "").replace("温润低饱和", "").replace("方形构图", "").replace("画面无任何文字", "").replace("主色", "")
        
        cards_list.append({
            "city": city,
            "bucket": bucket,
            "title": title,
            "body": body,
            "prompt": clean_p.strip(),
            "image": img,
            "has_prompt": True
        })

print(f"Total cards processed: {len(cards_list)}")

with open(os.path.join(ROOT, "scratch", "all_custom_cards_comparison.json"), "w", encoding="utf-8") as f:
    json.dump(cards_list, f, ensure_ascii=False, indent=2)

print("Saved all_custom_cards_comparison.json")
