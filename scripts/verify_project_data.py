import json
import os
import re

project_dir = "/Users/gripet/.gemini/antigravity/scratch/breathe-window"
public_dir = os.path.join(project_dir, "public")
locations_path = os.path.join(public_dir, "assets", "data", "locations.json")
catalog_path = os.path.join(public_dir, "assets", "data", "catalog.json")

def verify_data():
    errors = []
    warnings = []

    # 1. Load files
    if not os.path.exists(locations_path):
        errors.append(f"Missing locations.json at {locations_path}")
        return errors
    if not os.path.exists(catalog_path):
        errors.append(f"Missing catalog.json at {catalog_path}")
        return errors

    with open(locations_path, "r", encoding="utf-8") as f:
        locations = json.load(f)
    with open(catalog_path, "r", encoding="utf-8") as f:
        catalog = json.load(f)
        
    print(f"Loaded {len(locations)} locations from locations.json.")
    print(f"Loaded {len(catalog)} cities from catalog.json.")

    # Build name -> location lookup for image existence checks
    loc_by_name = {l["name"]: l for l in locations}

    # 2. Count verification
    if len(locations) != 300:
        errors.append(f"locations.json count is {len(locations)}, expected 300")
    if len(catalog) != 300:
        errors.append(f"catalog.json count is {len(catalog)}, expected 300")
        
    # 3. Match names
    loc_names = set(l["name"] for l in locations)
    cat_names = set(catalog.keys())
    
    only_in_loc = loc_names - cat_names
    only_in_cat = cat_names - loc_names
    
    if only_in_loc:
        errors.append(f"Cities in locations.json but missing from catalog.json: {only_in_loc}")
    if only_in_cat:
        errors.append(f"Cities in catalog.json but missing from locations.json: {only_in_cat}")
        
    # 4. Detailed card validation
    english_word_re = re.compile(r'[a-zA-Z]{3,}') # Find english words with 3 or more letters
    original_cities = {
        "日本 · 京都", "冰岛 · 雷克雅未克", "中国 · 四川竹海", "法国 · 巴黎", "摩洛哥 · 马拉喀什",
        "挪威 · 特罗姆瑟", "瑞士 · 阿尔卑斯山小镇", "意大利 · 威尼斯", "希腊 · 圣托里尼", "英国 · 伦敦",
        "加拿大 · 魁北克枫林", "埃及 · 开罗", "芬兰 · 罗瓦涅米", "新西兰 · 霍比屯", "中国 · 苏州园林"
    }
    
    for city, cards in catalog.items():
        if city in original_cities:
            continue
            
        if len(cards) != 5:
            errors.append(f"City '{city}' has {len(cards)} cards instead of 5")
            continue
            
        buckets = ["世界一角", "科学自然", "他人在场", "思想火花", "旧物新看"]
        for idx, card in enumerate(cards):
            # Check bucket order
            expected_bucket = buckets[idx]
            actual_bucket = card.get("bucket")
            if actual_bucket != expected_bucket:
                errors.append(f"City '{city}' card at index {idx} has bucket '{actual_bucket}', expected '{expected_bucket}'")
                
            # Check title length
            title = card.get("title", "")
            if len(title) > 12:
                errors.append(f"City '{city}' - '{actual_bucket}' title is too long ({len(title)} chars): '{title}'")
            if not title:
                errors.append(f"City '{city}' - '{actual_bucket}' has empty title")
                
            # Check body length
            body = card.get("body", "")
            if not (60 <= len(body) <= 80):
                errors.append(f"City '{city}' - '{actual_bucket}' body length is {len(body)} chars (expected 60-80): '{body}'")
            if not body:
                errors.append(f"City '{city}' - '{actual_bucket}' has empty body")
                
            # Check english words in body
            eng_words = english_word_re.findall(body)
            if eng_words:
                errors.append(f"City '{city}' - '{actual_bucket}' contains English words: {eng_words} in body: '{body}'")
                
            # Check ponder field rules
            ponder = card.get("ponder", "")
            if actual_bucket == "思想火花":
                if not ponder:
                    errors.append(f"City '{city}' - '思想火花' has empty ponder field")
            else:
                if ponder:
                    errors.append(f"City '{city}' - '{actual_bucket}' has non-empty ponder: '{ponder}', expected empty")
                    
            # Check image path format
            image = card.get("image", "")
            if not image.startswith("/assets/images/loc_"):
                errors.append(f"City '{city}' - '{actual_bucket}' image path is invalid: '{image}'")

            # Check image file existence on disk
            if image.startswith("/"):
                image_disk_path = os.path.join(public_dir, image.lstrip("/"))
                if not os.path.isfile(image_disk_path):
                    # Only flag as error if the city has custom images enabled
                    loc_entry = loc_by_name.get(city)
                    if loc_entry and loc_entry.get("hasCustomImages"):
                        errors.append(f"City '{city}' - '{actual_bucket}' references missing image file: '{image}'")
                    else:
                        warnings.append(f"City '{city}' - '{actual_bucket}' references non-existent image (non-custom city): '{image}'")
                
    if not errors:
        print("✓ All 300 cities successfully validated! No errors found.")
    else:
        print(f"✗ Found {len(errors)} validation errors:")
        for err in errors[:20]: # show first 20 errors
            print(f"  - {err}")
        if len(errors) > 20:
            print(f"  ... and {len(errors) - 20} more errors.")

    if warnings:
        print(f"\n⚠ Found {len(warnings)} warnings (non-blocking):")
        for warn in warnings[:10]:
            print(f"  - {warn}")
        if len(warnings) > 10:
            print(f"  ... and {len(warnings) - 10} more warnings.")

    # Save all errors and warnings to scratch/errors.txt
    os.makedirs(os.path.join(project_dir, "scratch"), exist_ok=True)
    errors_path = os.path.join(project_dir, "scratch", "errors.txt")
    with open(errors_path, "w", encoding="utf-8") as f:
        f.write(f"=== ERRORS ({len(errors)}) ===\n")
        for err in errors:
            f.write(err + "\n")
        f.write(f"\n=== WARNINGS ({len(warnings)}) ===\n")
        for warn in warnings:
            f.write(warn + "\n")
    print(f"All errors and warnings written to {errors_path}")
            
    return errors

if __name__ == "__main__":
    verify_data()
