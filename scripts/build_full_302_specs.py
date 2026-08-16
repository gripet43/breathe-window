#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
build_full_302_specs.py
Complete 302-City High-Standard Prompt Specification & Catalog Harmonizer.
1. Ensures all 302 cities have full 5-card rich, culturally-accurate prompts in window_generation_spec.json.
2. Synchronizes catalog.json copy for all 222 non-custom cities so that Title, Body, and Image prompts are 100% harmonized.
3. Adds rich prompt specs for the 62 existing custom cities and completes Bagan.
"""

import json, os, re, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOC_PATH = os.path.join(ROOT, "assets", "data", "locations.json")
CAT_PATH = os.path.join(ROOT, "assets", "data", "catalog.json")
PUB_CAT_PATH = os.path.join(ROOT, "public", "assets", "data", "catalog.json")
SPEC_PATH = os.path.join(ROOT, "scripts", "window_generation_spec.json")

def load_data():
    with open(LOC_PATH, "r", encoding="utf-8") as f:
        locs = json.load(f)
    with open(CAT_PATH, "r", encoding="utf-8") as f:
        cat = json.load(f)
    with open(SPEC_PATH, "r", encoding="utf-8") as f:
        spec = json.load(f)
    return locs, cat, spec

def clean_prompt_for_body(zh, city_name, bucket):
    # Remove column prefix
    text = re.sub(r'^(世界一角|科学自然|他人在场|思想火花|旧物新看)栏目[：:]\s*', '', zh)
    # Remove technical style suffixes
    text = re.sub(r'[，,]\s*(主色.*?)?(柔和水彩.*|水彩水粉.*|水粉手绘.*|细微纸纹.*|温润低饱和.*|方形构图.*|画面无任何文字.*)$', '', text)
    text = re.sub(r'[，,]\s*带原来如此的知识感.*', '', text)
    text = re.sub(r'[，,]\s*画面无任何文字.*', '', text)
    text = re.sub(r'[，,]\s*明信片视角.*', '', text)
    text = re.sub(r'[，,]\s*色调呼应.*', '', text)
    text = text.strip()
    if not text.endswith('。') and not text.endswith('？') and not text.endswith('！'):
        text += '。'
    return text

def derive_title(cleaned_text, city_name, bucket, original_title=""):
    # Extract concise, evocative title
    # e.g., if starts with 从...望出去 -> extract landmark
    m_window = re.search(r'从(.*?)望出去[，,]\s*看见(.*?)[，,。]', cleaned_text)
    if m_window:
        target = m_window.group(2).strip()
        # clean parenthetical
        target = re.sub(r'\(.*?\)', '', target).strip()
        if len(target) > 10:
            target = target[:10]
        return f"{target}晨景" if "晨" in cleaned_text else (f"{target}暮色" if "黄昏" in cleaned_text or "暮" in cleaned_text else target)
    
    # Check special patterns
    m_te = re.search(r'特写(.*?)[，,。]', cleaned_text)
    if m_te:
        target = re.sub(r'\(.*?\)', '', m_te.group(1)).strip()
        if len(target) <= 12 and len(target) >= 4:
            return target
            
    m_eco = re.search(r'(.*?)生态切面', cleaned_text)
    if m_eco:
        target = re.sub(r'\(.*?\)', '', m_eco.group(1)).strip()
        if len(target) <= 12 and len(target) >= 4:
            return f"{target}生态"

    # Fallback to existing poetic title if reasonable, or extract first clause
    if original_title and len(original_title) >= 4 and len(original_title) <= 14:
        return original_title
        
    first_clause = re.split(r'[，,。]', cleaned_text)[0].strip()
    first_clause = re.sub(r'\(.*?\)', '', first_clause).strip()
    if len(first_clause) > 12:
        first_clause = first_clause[:12]
    return first_clause if len(first_clause) >= 4 else f"{city_name.split('·')[-1].strip()}{bucket}"

def main():
    locs, cat, spec = load_data()
    loc_by_name = {l["name"]: l for l in locs}
    
    print(f"Loaded {len(locs)} locations, {len(cat)} catalog entries, {len(spec)} spec entries.")
    
    # 1. Complete Bagan in spec
    if "缅甸 · 蒲甘" in spec:
        bagan_items = spec["缅甸 · 蒲甘"]["items"]
        existing_buckets = {it["bucket"] for it in bagan_items}
        if "世界一角" not in existing_buckets:
            bagan_items.insert(0, {
                "bucket": "世界一角",
                "filename": "loc_bagan.png",
                "path": "/assets/images/loc_bagan.png",
                "zh": "世界一角栏目：从古老佛塔的砖石拱窗望出去，万千座砖红与金黄塔尖散落在晨雾弥漫的蒲甘平原上，远方几只热气球迎着朝阳缓缓升空，明信片视角，主色赭金与砖红，柔和水彩水粉手绘，细微纸纹，温润低饱和，方形构图，画面无任何文字",
                "en": "world corner column: view through the arched brick window of an ancient temple, thousands of brick-red and gilded pagoda spires scattered across the misty plain of Bagan, hot air balloons rising slowly in the dawn sun beyond, postcard view, palette of ochre gold and brick red, soft watercolor and gouache illustration, subtle paper grain, warm muted natural palette, painterly, square 1:1, no text, no words, no letters, no signage"
            })
        if "科学自然" not in existing_buckets:
            bagan_items.insert(1, {
                "bucket": "科学自然",
                "filename": "loc_bagan_nature.png",
                "path": "/assets/images/loc_bagan_nature.png",
                "zh": "科学自然栏目：蒲甘干旱红土地貌生态切面，耐旱的金合欢树(acacia)与沙地仙人掌，伊洛瓦底江在远处流过，带原来如此的知识感，主色赭红与沙黄，柔和水彩水粉手绘，细微纸纹，温润低饱和，方形构图，画面无任何文字",
                "en": "nature column: the arid red-earth ecology of Bagan, drought-resistant acacia trees and sandy soil, the Irrawaddy river flowing in the distance, an aha-moment of dry-zone natural knowledge, palette of ochre red and sand yellow, soft watercolor and gouache illustration, subtle paper grain, warm muted natural palette, painterly, square 1:1, no text, no words, no letters, no signage"
            })

    # 2. Add prompt specs for the 62 custom cities missing in spec
    custom_missing = [l["name"] for l in locs if l.get("hasCustomImages") and l["name"] not in spec]
    print(f"Generating rich spec entries for {len(custom_missing)} custom cities...")
    
    bucket_en_map = {
        "世界一角": "world corner column",
        "科学自然": "nature column",
        "他人在场": "people column",
        "思想火花": "spark column",
        "旧物新看": "old column"
    }
    
    for city_name in custom_missing:
        l = loc_by_name[city_name]
        cards = cat.get(city_name, [])
        items = []
        
        lc = l.get("locClass", "loc-custom")
        prefix = lc.replace("-", "_")
        
        for c in cards:
            b = c.get("bucket", "世界一角")
            title = c.get("title", "")
            body = c.get("body", "")
            
            b_suffix = ""
            if b == "科学自然": b_suffix = "_nature"
            elif b == "他人在场": b_suffix = "_people"
            elif b == "思想火花": b_suffix = "_spark"
            elif b == "旧物新看": b_suffix = "_old"
            
            fname = f"{prefix}{b_suffix}.png"
            fpath = f"/assets/images/{prefix}{b_suffix}.png"
            
            zh_prompt = f"{b}栏目：{title}。{body}柔和水彩水粉手绘，细微纸纹，温润低饱和，方形构图，画面无任何文字"
            en_prompt = f"{bucket_en_map.get(b, 'column')}: {title}. {body} soft watercolor and gouache illustration, subtle paper grain, warm muted natural palette, painterly, square 1:1, no text, no words, no letters, no signage"
            
            items.append({
                "bucket": b,
                "filename": fname,
                "path": fpath,
                "zh": zh_prompt,
                "en": en_prompt
            })
            
        spec[city_name] = {
            "countryCode": l.get("countryCode", ""),
            "continent": l.get("continent", "亚洲"),
            "emblem": l.get("emblem", "🌍"),
            "wood": l.get("wood", "#8B5A2B"),
            "stampColor": l.get("stampColor", "#8B5A2B"),
            "hasCustomImages": True,
            "identity": cards[0]["title"] if cards else city_name,
            "items": items
        }

    # 3. Synchronize catalog.json for all 222 non-custom cities
    no_custom = [l["name"] for l in locs if not l.get("hasCustomImages")]
    print(f"Synchronizing catalog copy with prompts for {len(no_custom)} non-custom cities...")
    
    updated_cards = 0
    for city_name in no_custom:
        if city_name not in spec or city_name not in cat:
            continue
        spec_items = {it["bucket"]: it for it in spec[city_name].get("items", [])}
        for card in cat[city_name]:
            b = card.get("bucket")
            s = spec_items.get(b)
            if s:
                zh = s.get("zh", "")
                cleaned_body = clean_prompt_for_body(zh, city_name, b)
                card_title = derive_title(cleaned_body, city_name, b, card.get("title", ""))
                card["title"] = card_title
                card["body"] = cleaned_body
                updated_cards += 1

    print(f"Updated {updated_cards} cards across 222 cities in catalog.json.")
    
    # Save window_generation_spec.json (now all 302 cities!)
    with open(SPEC_PATH, "w", encoding="utf-8") as f:
        json.dump(spec, f, ensure_ascii=False, indent=2)
    print(f"Successfully saved {len(spec)} cities to window_generation_spec.json.")

    # Save catalog.json to both src and pub
    with open(CAT_PATH, "w", encoding="utf-8") as f:
        json.dump(cat, f, ensure_ascii=False, indent=2)
    with open(PUB_CAT_PATH, "w", encoding="utf-8") as f:
        json.dump(cat, f, ensure_ascii=False, indent=2)
    print("Successfully saved catalog.json to src and public.")

if __name__ == "__main__":
    main()
