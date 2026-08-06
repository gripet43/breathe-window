#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json

project_dir = "/Users/gripet/.gemini/antigravity/scratch/breathe-window"
locations_path = os.path.join(project_dir, "public", "assets", "data", "locations.json")
catalog_path = os.path.join(project_dir, "public", "assets", "data", "catalog.json")
images_dir = os.path.join(project_dir, "public", "assets", "images")

PLACEHOLDER_SIZES = {790453, 981515, 1026331, 1076134}

def is_placeholder(img_path):
    if not os.path.exists(img_path):
        return True
    sz = os.path.getsize(img_path)
    if sz in PLACEHOLDER_SIZES or (os.path.basename(img_path) == "loc_suzhou.png" and sz == 1066786):
        return True
    return False

def main():
    with open(locations_path, "r", encoding="utf-8") as f:
        locations = json.load(f)
    with open(catalog_path, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    updated_count = 0
    for loc in locations:
        city_name = loc["name"]
        cards = catalog.get(city_name, [])
        if not cards or len(cards) != 5:
            loc["hasCustomImages"] = False
            continue

        has_all_custom = True
        for card in cards:
            img_rel_path = card.get("image", "")
            base_stem = os.path.splitext(os.path.basename(img_rel_path))[0]
            webp_path = os.path.join(images_dir, f"{base_stem}.webp")
            png_path = os.path.join(project_dir, "assets", "images", f"{base_stem}.png")
            
            target_img = webp_path if os.path.exists(webp_path) else png_path
            if is_placeholder(target_img):
                has_all_custom = False
                break

        old_val = loc.get("hasCustomImages", False)
        loc["hasCustomImages"] = has_all_custom
        if has_all_custom != old_val:
            print(f"City '{city_name}': hasCustomImages updated {old_val} -> {has_all_custom}")
            updated_count += 1

    with open(locations_path, "w", encoding="utf-8") as f:
        json.dump(locations, f, indent=2, ensure_ascii=False)

    root_locations_path = os.path.join(project_dir, "assets", "data", "locations.json")
    if os.path.exists(os.path.dirname(root_locations_path)):
        with open(root_locations_path, "w", encoding="utf-8") as f:
            json.dump(locations, f, indent=2, ensure_ascii=False)

    print(f"Finished updating locations.json. Updated {updated_count} cities.")

if __name__ == "__main__":
    main()
