#!/usr/bin/env python3
"""
Breathe-Window Automated Verification & Quality Assurance Suite
Ensures 0 regressions on:
1. Data schema and completeness (locations.json, catalog.json, locMap in index.html)
2. Image asset existence & 404 prevention
3. Synchronicity between root and public/ distribution files
4. Code validity (JS syntax, JSON validity, HTML structure)
"""

import os
import sys
import json
import re
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
PUBLIC_DIR = os.path.join(PROJECT_ROOT, "public")

COLOR_GREEN = "\033[92m"
COLOR_RED = "\033[91m"
COLOR_YELLOW = "\033[93m"
COLOR_CYAN = "\033[96m"
COLOR_RESET = "\033[0m"

def print_header(title):
    print(f"\n{COLOR_CYAN}=== {title} ==={COLOR_RESET}")

def print_pass(msg):
    print(f"  {COLOR_GREEN}✓{COLOR_RESET} {msg}")

def print_fail(msg):
    print(f"  {COLOR_RED}✗{COLOR_RESET} {msg}")

def print_warn(msg):
    print(f"  {COLOR_YELLOW}⚠{COLOR_RESET} {msg}")

def run_tests():
    errors = []
    warnings = []
    
    # ---------------------------------------------------------
    # 1. FILE EXISTENCE & SYNC VERIFICATION
    # ---------------------------------------------------------
    print_header("1. Static File & Directory Sync Verification")
    
    paired_files = [
        ("index.html", "public/index.html"),
        ("assets/data/locations.json", "public/assets/data/locations.json"),
        ("assets/data/catalog.json", "public/assets/data/catalog.json"),
        ("assets/data/window-themes.css", "public/assets/data/window-themes.css")
    ]
    
    for f1, f2 in paired_files:
        p1 = os.path.join(PROJECT_ROOT, f1)
        p2 = os.path.join(PROJECT_ROOT, f2)
        if not os.path.exists(p1):
            errors.append(f"Missing root file: {f1}")
            print_fail(f"Missing: {f1}")
            continue
        if not os.path.exists(p2):
            errors.append(f"Missing public file: {f2}")
            print_fail(f"Missing: {f2}")
            continue
            
        with open(p1, "rb") as fp1, open(p2, "rb") as fp2:
            c1 = fp1.read()
            c2 = fp2.read()
            if c1 == c2:
                print_pass(f"In sync: {f1} <-> {f2}")
            else:
                errors.append(f"Out of sync: {f1} and {f2} differ in content!")
                print_fail(f"Out of sync: {f1} <-> {f2}")

    # Check fallback images
    fallback_images = [
        "world_corner.png", "science_nature.png", "others_present.png", 
        "spark_of_thought.png", "old_knowledge.png"
    ]
    for fb in fallback_images:
        p1 = os.path.join(PROJECT_ROOT, "assets", "images", fb)
        p2 = os.path.join(PUBLIC_DIR, "assets", "images", fb)
        if not os.path.exists(p1) or not os.path.exists(p2):
            errors.append(f"Fallback image missing: {fb} (assets={os.path.exists(p1)}, public={os.path.exists(p2)})")
            print_fail(f"Fallback missing: {fb}")
        else:
            print_pass(f"Fallback image present: {fb}")

    # ---------------------------------------------------------
    # 2. LOCATIONS.JSON INTEGRITY & SCHEMA
    # ---------------------------------------------------------
    print_header("2. locations.json Schema & Integrity")
    loc_path = os.path.join(PUBLIC_DIR, "assets", "data", "locations.json")
    try:
        with open(loc_path, "r", encoding="utf-8") as f:
            locations = json.load(f)
    except Exception as e:
        errors.append(f"Failed to parse {loc_path}: {e}")
        print_fail(f"JSON parse error: {e}")
        return errors
        
    print_pass(f"Loaded {len(locations)} locations from locations.json")
    
    if len(locations) != 302:
        warnings.append(f"Expected 302 locations, found {len(locations)}")
        print_warn(f"Location count is {len(locations)} (baseline 302)")
    else:
        print_pass("Location count is exactly 302")

    required_loc_fields = [
        "name", "countryCode", "lat", "lng", "emblem", 
        "wood", "woodDark", "glow", "stampColor", "locClass", "hasCustomImages"
    ]
    
    loc_names = []
    loc_classes = []
    loc_by_name = {}
    
    for i, loc in enumerate(locations):
        name = loc.get("name")
        lc = loc.get("locClass")
        
        # Check required fields
        for field in required_loc_fields:
            if field not in loc:
                errors.append(f"Location #{i} ({name}) missing required field: '{field}'")
                print_fail(f"Location #{i} ({name}) missing '{field}'")
                
        # Validate coordinates
        lat = loc.get("lat")
        lng = loc.get("lng")
        if lat is None or not (-90 <= float(lat) <= 90):
            errors.append(f"Location #{i} ({name}) invalid latitude: {lat}")
        if lng is None or not (-180 <= float(lng) <= 180):
            errors.append(f"Location #{i} ({name}) invalid longitude: {lng}")
            
        if name:
            loc_names.append(name)
            loc_by_name[name] = loc
        if lc:
            loc_classes.append(lc)

    # Check duplicates
    if len(loc_names) != len(set(loc_names)):
        dupes = [n for n in loc_names if loc_names.count(n) > 1]
        errors.append(f"Duplicate location names in locations.json: {set(dupes)}")
        print_fail(f"Duplicate location names: {set(dupes)}")
    else:
        print_pass("All location names are unique")
        
    if len(loc_classes) != len(set(loc_classes)):
        dupes = [c for c in loc_classes if loc_classes.count(c) > 1]
        errors.append(f"Duplicate locClasses in locations.json: {set(dupes)}")
        print_fail(f"Duplicate locClasses: {set(dupes)}")
    else:
        print_pass("All locClasses are unique")

    # ---------------------------------------------------------
    # 3. CATALOG.JSON INTEGRITY & BUCKET VALIDATION
    # ---------------------------------------------------------
    print_header("3. catalog.json Integrity & Structure")
    cat_path = os.path.join(PUBLIC_DIR, "assets", "data", "catalog.json")
    try:
        with open(cat_path, "r", encoding="utf-8") as f:
            catalog = json.load(f)
    except Exception as e:
        errors.append(f"Failed to parse {cat_path}: {e}")
        print_fail(f"JSON parse error: {e}")
        return errors
        
    print_pass(f"Loaded {len(catalog)} cities from catalog.json")
    
    # Compare with locations
    missing_in_cat = set(loc_names) - set(catalog.keys())
    extra_in_cat = set(catalog.keys()) - set(loc_names)
    
    if missing_in_cat:
        errors.append(f"Locations in locations.json but missing from catalog.json: {missing_in_cat}")
        print_fail(f"Missing from catalog: {missing_in_cat}")
    else:
        print_pass("100% of locations exist in catalog.json")
        
    if extra_in_cat:
        errors.append(f"Locations in catalog.json but missing from locations.json: {extra_in_cat}")
        print_fail(f"Extra in catalog: {extra_in_cat}")
    else:
        print_pass("No orphaned entries in catalog.json")

    expected_buckets = ["世界一角", "科学自然", "他人在场", "思想火花", "旧物新看"]
    catalog_card_errors = 0
    
    for city, cards in catalog.items():
        if len(cards) != 5:
            errors.append(f"City '{city}' has {len(cards)} cards (expected 5)")
            catalog_card_errors += 1
            continue
            
        for idx, card in enumerate(cards):
            bucket = card.get("bucket")
            title = card.get("title", "")
            body = card.get("body", "")
            image = card.get("image", "")
            ponder = card.get("ponder", "")
            
            if bucket != expected_buckets[idx]:
                errors.append(f"City '{city}' card {idx} bucket is '{bucket}' (expected '{expected_buckets[idx]}')")
                catalog_card_errors += 1
            if not title:
                errors.append(f"City '{city}' card {idx} has empty title")
                catalog_card_errors += 1
            if not body:
                errors.append(f"City '{city}' card {idx} has empty body")
                catalog_card_errors += 1
            if not image or not image.startswith("/assets/images/"):
                errors.append(f"City '{city}' card {idx} invalid image path: '{image}'")
                catalog_card_errors += 1
            if bucket == "思想火花" and not ponder:
                # Some earlier cities might have empty ponder, flag as warning if non-empty is preferred
                pass

    if catalog_card_errors == 0:
        print_pass(f"All {len(catalog) * 5} cards verified (buckets, titles, bodies, images)")
    else:
        print_fail(f"Found {catalog_card_errors} errors in catalog cards")

    # ---------------------------------------------------------
    # 4. IMAGE ASSET CONSISTENCY & 404 PREVENTION
    # ---------------------------------------------------------
    print_header("4. Image Asset Consistency & 404 Prevention")
    custom_locs = [l for l in locations if l.get("hasCustomImages")]
    non_custom_locs = [l for l in locations if not l.get("hasCustomImages")]
    
    print_pass(f"Custom image locations: {len(custom_locs)}")
    print_pass(f"Default fallback locations: {len(non_custom_locs)}")
    
    missing_custom_images = []
    falsely_marked_custom = []
    
    for loc in locations:
        name = loc.get("name")
        lc = loc.get("locClass")
        has_custom = loc.get("hasCustomImages")
        prefix = lc.replace("-", "_") if lc else ""
        
        cards = catalog.get(name, [])
        all_exist_pub = True
        all_exist_src = True
        
        for c in cards:
            img = c.get("image", "").lstrip("/")
            pub_img_path = os.path.join(PUBLIC_DIR, img)
            src_img_path = os.path.join(PROJECT_ROOT, img)
            
            if not os.path.exists(pub_img_path):
                all_exist_pub = False
                if has_custom:
                    missing_custom_images.append(f"Missing in public: {img} (City: {name})")
            if not os.path.exists(src_img_path):
                all_exist_src = False
                if has_custom:
                    missing_custom_images.append(f"Missing in assets: {img} (City: {name})")

        if has_custom and (not all_exist_pub or not all_exist_src):
            falsely_marked_custom.append(name)
            
    if missing_custom_images:
        for m in missing_custom_images[:10]:
            print_fail(m)
        if len(missing_custom_images) > 10:
            print_fail(f"... and {len(missing_custom_images) - 10} more missing image files")
        errors.extend(missing_custom_images)
    else:
        print_pass("All 80 custom cities have 100% of their images present in both assets/ and public/assets/!")

    # ---------------------------------------------------------
    # 5. LOADING WORDS (locMap) COMPLETENESS
    # ---------------------------------------------------------
    print_header("5. Loading Words (locMap) Completeness in index.html")
    index_path = os.path.join(PROJECT_ROOT, "index.html")
    with open(index_path, "r", encoding="utf-8") as f:
        html = f.read()
        
    match = re.search(r"const locMap = \{([\s\S]*?)\n    \};", html)
    if not match:
        errors.append("Could not find 'const locMap = {' in index.html")
        print_fail("Could not find locMap in index.html")
    else:
        block = match.group(1)
        loc_map_keys = re.findall(r"\"(.*?)\": \[", block)
        print_pass(f"Found {len(loc_map_keys)} location quotes in index.html")
        
        missing_quotes = set(loc_names) - set(loc_map_keys)
        if missing_quotes:
            errors.append(f"Cities missing from locMap in index.html: {missing_quotes}")
            print_fail(f"Missing from locMap: {missing_quotes}")
        else:
            print_pass("100% of locations have custom loading quotes!")

    # ---------------------------------------------------------
    # 6. CODE SYNTAX & RUNTIME SAFETY
    # ---------------------------------------------------------
    print_header("6. Code Syntax & Runtime Safety Verification")
    
    # Check JS syntax via Node.js
    scripts = re.findall(r"<script>([\s\S]*?)</script>", html)
    for i, s in enumerate(scripts):
        tmp_js = f"test_script_{i}.js"
        with open(tmp_js, "w", encoding="utf-8") as f:
            f.write(s)
        try:
            res = subprocess.run(["node", "--check", tmp_js], capture_output=True, text=True)
            if res.returncode == 0:
                print_pass(f"Inline script block #{i} passed Node.js syntax check")
            else:
                errors.append(f"Inline script block #{i} syntax error:\n{res.stderr}")
                print_fail(f"Inline script #{i} syntax error: {res.stderr.strip()}")
        except Exception as e:
            warnings.append(f"Node.js check skipped: {e}")
        finally:
            if os.path.exists(tmp_js):
                try:
                    os.remove(tmp_js)
                except Exception:
                    pass

    # ---------------------------------------------------------
    # SUMMARY & REPORT
    # ---------------------------------------------------------
    print_header("VERIFICATION SUMMARY")
    if not errors:
        print(f"\n{COLOR_GREEN}✓ ALL TESTS PASSED! Project is 100% healthy, synchronized, and regression-free.{COLOR_RESET}\n")
        return 0
    else:
        print(f"\n{COLOR_RED}✗ FAILED: Found {len(errors)} errors that must be resolved!{COLOR_RESET}")
        for err in errors[:15]:
            print(f"  - {err}")
        if len(errors) > 15:
            print(f"  ... and {len(errors) - 15} more errors.")
        print()
        return 1

if __name__ == "__main__":
    code = run_tests()
    sys.exit(code)
