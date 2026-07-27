#!/usr/bin/env python3
"""Optimize site images.

- City photos (loc_*.png, actually 1024^2 JPEG content): re-encode to 800px WebP q82, delete originals.
- catalog.json image paths: surgical string replace .png -> .webp for converted stems (format-preserving).
- Emblems (5): shrink in place to 800px JPEG q82 (name unchanged; content was already jpeg).
- Icons: resize favicon-32x32 -> 32px, apple-touch-icon -> 180px (PNG, in place).
- Optional cleanup: delete unused healing_bgm.wav.
- --dry-run: report plan without writing; estimates sizes via in-memory buffers.
"""
import os, io, json, glob, argparse
from PIL import Image, features

ROOT = "/Users/gripet/.gemini/antigravity/scratch/breathe-window"
IMG = os.path.join(ROOT, "public", "assets", "images")
CATALOG = os.path.join(ROOT, "public", "assets", "data", "catalog.json")
LOCATIONS = os.path.join(ROOT, "public", "assets", "data", "locations.json")
UNUSED_WAV = os.path.join(ROOT, "public", "assets", "audio", "healing_bgm.wav")

TARGET_W = 800
WEBP_Q = 82
EMBLEM_Q = 82
ICON_SIZES = {"favicon-32x32": 32, "apple-touch-icon": 180}
EMBLEMS = ["world_corner", "science_nature", "others_present", "spark_of_thought", "old_knowledge"]


def resized(img, w):
    h = max(1, int(img.height * w / img.width))
    out = img.copy()
    out.thumbnail((w, h), Image.LANCZOS)
    return out


def save_buf(img, fmt, **kw):
    buf = io.BytesIO()
    img.save(buf, fmt, **kw)
    return buf.tell()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-emblems", action="store_true")
    ap.add_argument("--no-icons", action="store_true")
    ap.add_argument("--no-catalog", action="store_true")
    args = ap.parse_args()

    assert features.check("webp"), "Pillow missing WebP support"

    rows = []          # (label, before_bytes, after_bytes)
    converted = []     # stems of converted city photos

    # 1. City photos -> webp
    for png in sorted(glob.glob(os.path.join(IMG, "loc_*.png"))):
        stem = os.path.splitext(os.path.basename(png))[0]
        webp = os.path.join(IMG, stem + ".webp")
        sb = os.path.getsize(png)
        with Image.open(png) as im:
            im.load()
            r = resized(im, min(TARGET_W, im.width))
            if args.dry_run:
                sa = save_buf(r, "WEBP", quality=WEBP_Q, method=4)
            else:
                r.save(webp, "WEBP", quality=WEBP_Q, method=4)
                os.remove(png)
                sa = os.path.getsize(webp)
        converted.append(stem)
        rows.append((stem, sb, sa))

    # 2. Emblems (keep name; shrink jpeg content)
    if not args.no_emblems:
        for name in EMBLEMS:
            p = os.path.join(IMG, name + ".png")
            if not os.path.exists(p):
                print("WARN emblem missing:", name); continue
            sb = os.path.getsize(p)
            with Image.open(p) as im:
                im.load()
                r = resized(im, TARGET_W)
                if args.dry_run:
                    sa = save_buf(r, "JPEG", quality=EMBLEM_Q, optimize=True)
                else:
                    r.save(p, "JPEG", quality=EMBLEM_Q, optimize=True)
                    sa = os.path.getsize(p)
            rows.append((name + " [emblem]", sb, sa))

    # 3. Icons (resize to declared sizes)
    if not args.no_icons:
        for name, sz in ICON_SIZES.items():
            p = os.path.join(IMG, name + ".png")
            if not os.path.exists(p):
                print("WARN icon missing:", name); continue
            sb = os.path.getsize(p)
            with Image.open(p) as im:
                im.load()
                r = im.resize((sz, sz), Image.LANCZOS)
                if args.dry_run:
                    sa = save_buf(r, "PNG", optimize=True)
                else:
                    r.save(p, "PNG", optimize=True)
                    sa = os.path.getsize(p)
            rows.append((name + f" [{sz}px]", sb, sa))

    # 4. catalog.json surgical rewrite
    cat_n = 0
    if not args.no_catalog:
        if args.dry_run:
            txt = open(CATALOG, encoding="utf-8").read()
            for stem in converted:
                cat_n += txt.count(f"/{stem}.png")
        else:
            txt = open(CATALOG, encoding="utf-8").read()
            for stem in converted:
                txt = txt.replace(f"/{stem}.png", f"/{stem}.webp")
                # also any bare reference without leading slash, just in case
            open(CATALOG, "w", encoding="utf-8").write(txt)
            cat_n = sum(txt.count(f"/{stem}.webp") for stem in converted)

    # 5. unused wav
    wav_action = ""
    if os.path.exists(UNUSED_WAV):
        wb = os.path.getsize(UNUSED_WAV)
        if not args.dry_run:
            os.remove(UNUSED_WAV)
        wav_action = f"delete healing_bgm.wav ({wb//1024}KB, unused)"

    # report
    before = sum(r[1] for r in rows)
    after = sum(r[2] for r in rows)
    print(f"[{'DRY-RUN' if args.dry_run else 'WRITE'}] city photos: {len(converted)} | catalog paths: {cat_n}")
    print(f"  before {before/1048576:6.2f}MB  after {after/1048576:6.2f}MB  saved {(1-after/max(before,1))*100:4.1f}%")
    if wav_action:
        print(f"  + {wav_action}")
    print("  samples:")
    for label, sb, sa in rows[:5] + rows[-3:]:
        print(f"    {label:34s} {sb//1024:5d}KB -> {sa//1024:4d}KB")

    # 6. verification (write mode only): custom-city catalog images must exist on disk
    if not args.dry_run:
        locs = json.load(open(LOCATIONS, encoding="utf-8"))
        custom = {l["name"] for l in locs if l.get("hasCustomImages")}
        cat = json.load(open(CATALOG, encoding="utf-8"))
        missing = []
        for city, cards in cat.items():
            if city not in custom:
                continue
            for card in cards:
                img = card.get("image", "")
                if img.startswith("/assets/images/loc_"):
                    dp = os.path.join(ROOT, "public", img.lstrip("/"))
                    if not os.path.isfile(dp):
                        missing.append((city, img))
        if missing:
            print(f"  !! {len(missing)} custom-city images missing on disk:")
            for m in missing[:10]:
                print("    ", m)
        else:
            print("  verification OK: all custom-city catalog images resolve on disk")


if __name__ == "__main__":
    main()
