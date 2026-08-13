#!/usr/bin/env python3
"""
Breathe-Window One-Stop Build & Sync Automation Script
Run this script whenever any code, data, or image is modified.

It performs:
1. Bidirectional sync between root files and public/ distribution files
2. Real-time filesystem scan: automatically aligns hasCustomImages in locations.json
3. Image path format alignment in catalog.json (.webp vs .png)
4. Window themes CSS regeneration for all cities
5. Automated verification test suite execution
"""

import os
import sys
import json
import shutil
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
PUBLIC_DIR = os.path.join(PROJECT_ROOT, "public")

def log(msg):
    print(f"[BUILD] {msg}")

def main():
    log("Starting Breathe-Window build & sync pipeline...")
    
    # -------------------------------------------------------------
    # 1. Sync index.html -> public/index.html
    # -------------------------------------------------------------
    src_html = os.path.join(PROJECT_ROOT, "index.html")
    pub_html = os.path.join(PUBLIC_DIR, "index.html")
    
    # Determine newer file if both modified
    if os.path.exists(src_html) and os.path.exists(pub_html):
        mtime_src = os.path.getmtime(src_html)
        mtime_pub = os.path.getmtime(pub_html)
        if mtime_pub > mtime_src:
            shutil.copyfile(pub_html, src_html)
            log("Synced public/index.html -> index.html (public was newer)")
        else:
            shutil.copyfile(src_html, pub_html)
            log("Synced index.html -> public/index.html (root was newer)")
    elif os.path.exists(src_html):
        shutil.copyfile(src_html, pub_html)
        log("Copied index.html -> public/index.html")
        
    # -------------------------------------------------------------
    # 2. Sync Assets Directory (Images, Styles, Data)
    # -------------------------------------------------------------
    src_assets = os.path.join(PROJECT_ROOT, "assets")
    pub_assets = os.path.join(PUBLIC_DIR, "assets")
    os.makedirs(os.path.join(pub_assets, "images"), exist_ok=True)
    os.makedirs(os.path.join(pub_assets, "data"), exist_ok=True)
    os.makedirs(os.path.join(src_assets, "images"), exist_ok=True)
    os.makedirs(os.path.join(src_assets, "data"), exist_ok=True)

    # Sync webp images to public and assets
    for img_file in os.listdir(os.path.join(pub_assets, "images")):
        src_path = os.path.join(src_assets, "images", img_file)
        pub_path = os.path.join(pub_assets, "images", img_file)
        if not os.path.exists(src_path):
            shutil.copyfile(pub_path, src_path)

    for img_file in os.listdir(os.path.join(src_assets, "images")):
        src_path = os.path.join(src_assets, "images", img_file)
        pub_path = os.path.join(pub_assets, "images", img_file)
        if img_file.endswith(".webp") and not os.path.exists(pub_path):
            shutil.copyfile(src_path, pub_path)

    # -------------------------------------------------------------
    # 3. Synchronize locations.json and recalculate hasCustomImages
    # -------------------------------------------------------------
    loc_file = os.path.join(pub_assets, "data", "locations.json")
    with open(loc_file, "r", encoding="utf-8") as f:
        locations = json.load(f)

    custom_count = 0
    for loc in locations:
        lc = loc.get("locClass")
        if not lc: continue
        prefix = lc.replace("-", "_")
        # Check if all 5 webp images exist
        files = [f for f in os.listdir(os.path.join(pub_assets, "images")) 
                 if f.startswith(prefix) and f.endswith(".webp")]
        if len(files) == 5:
            loc["hasCustomImages"] = True
            custom_count += 1
        else:
            loc["hasCustomImages"] = False

    with open(os.path.join(pub_assets, "data", "locations.json"), "w", encoding="utf-8") as f:
        json.dump(locations, f, ensure_ascii=False, indent=2)
    with open(os.path.join(src_assets, "data", "locations.json"), "w", encoding="utf-8") as f:
        json.dump(locations, f, ensure_ascii=False, indent=2)

    log(f"Updated locations.json: {custom_count} locations with full custom images.")

    # -------------------------------------------------------------
    # 4. Synchronize catalog.json and update image extension
    # -------------------------------------------------------------
    cat_file = os.path.join(pub_assets, "data", "catalog.json")
    with open(cat_file, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    for loc in locations:
        name = loc.get("name")
        has_custom = loc.get("hasCustomImages")
        if name in catalog and has_custom:
            for card in catalog[name]:
                img = card.get("image", "")
                if img.endswith(".png"):
                    card["image"] = img[:-4] + ".webp"

    with open(os.path.join(pub_assets, "data", "catalog.json"), "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)
    with open(os.path.join(src_assets, "data", "catalog.json"), "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)

    log("Synchronized catalog.json.")

    # -------------------------------------------------------------
    # 5. Regenerate Window Themes CSS
    # -------------------------------------------------------------
    css_gen_script = os.path.join(SCRIPT_DIR, "generate_window_css.py")
    if os.path.exists(css_gen_script):
        subprocess.run([sys.executable, css_gen_script], check=True)
        shutil.copyfile(
            os.path.join(pub_assets, "data", "window-themes.css"),
            os.path.join(src_assets, "data", "window-themes.css")
        )
        log("Regenerated window-themes.css.")

    # -------------------------------------------------------------
    # 6. Run Full Verification Suite
    # -------------------------------------------------------------
    log("Running verification suite...")
    verify_script = os.path.join(SCRIPT_DIR, "verify_project.py")
    res = subprocess.run([sys.executable, verify_script])
    if res.returncode != 0:
        log("BUILD FAILED: Verification test suite reported errors.")
        sys.exit(res.returncode)
        
    log("BUILD SUCCESSFUL! All files synchronized and verified.")

if __name__ == "__main__":
    main()
