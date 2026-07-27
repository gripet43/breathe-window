#!/usr/bin/env python3
"""Audit per-city "window" coverage.

For every city in catalog.json, report whether its 5 card scene-images actually
exist on disk (= has unique window art) vs fall back to the category emblem,
and cross-check against locations.json's hasCustomImages flag. Surfaces dirty
data (flagged custom but missing art / flagged non-custom but art present),
frame-color (wood/stampColor/emblem) coverage, and continent spread of the
missing set to inform a generation plan.
"""
import json, os
from collections import Counter

ROOT = "/Users/gripet/.gemini/antigravity/scratch/breathe-window"
PUB = os.path.join(ROOT, "public")
CAT = os.path.join(PUB, "assets", "data", "catalog.json")
LOC = os.path.join(PUB, "assets", "data", "locations.json")

AMERICAS = {"us","ca","mx","br","ar","cl","pe","co","cu","cr","pa","jm","bo","ec","ve","uy","py","gt","do","hn","ni","tt","ht","sv","bz","sr","gy"}
EUROPE = {"gb","fr","de","it","es","pt","nl","be","ch","at","ie","se","no","fi","dk","is","gr","pl","cz","hu","ro","hr","ru","ua","tr","mt","lu","ee","lv","lt","rs","ba","bg","sk","si","by","al","mk","me","xk","md","cy","ge","am","az"}
AFRICA = {"eg","ma","za","ke","tz","et","ng","gh","sn","dz","tn","mu","sc","na","zw","ug","rw","mg","sd","ss","cd","cg","cm","ci","ml","bf","ne","td","so","mz","zm","bw","ao","ga","gq","lr","sl","gn","gw","gm","tg","bj","bi","ly","er","dj","st","cv","km"}
OCEANIA = {"au","nz","fj","pg","ws","sb","vu","to","ki","fm","pw","mh","tv","nr"}
def continent(cc):
    cc = (cc or "").lower()
    if cc in AMERICAS: return "美洲"
    if cc in EUROPE: return "欧洲"
    if cc in AFRICA: return "非洲"
    if cc in OCEANIA: return "大洋洲"
    return "亚洲"

def exists(p):
    if not p: return False
    dp = os.path.join(PUB, p.lstrip("/")) if p.startswith("/") else os.path.join(PUB, p)
    return os.path.isfile(dp)

locs = json.load(open(LOC, encoding="utf-8"))
byname = {l["name"]: l for l in locs}
cat = json.load(open(CAT, encoding="utf-8"))

rows = []
for city, cards in cat.items():
    paths = [c.get("image", "") for c in cards]
    n_exist = sum(1 for p in paths if exists(p))
    l = byname.get(city, {})
    rows.append(dict(city=city, flag=bool(l.get("hasCustomImages")),
                     n_exist=n_exist, n_cards=len(cards),
                     wood=l.get("wood"), stamp=l.get("stampColor"),
                     emblem=l.get("emblem"), cc=l.get("countryCode"),
                     paths=paths))

total = len(rows)
has_art = [r for r in rows if r["n_exist"] > 0]
no_art = [r for r in rows if r["n_exist"] == 0]
flag_true = [r for r in rows if r["flag"]]

dirty_flag_no_art = [r["city"] for r in rows if r["flag"] and r["n_exist"] < 5]
dirty_noflag_art = [r["city"] for r in rows if not r["flag"] and r["n_exist"] > 0]
wrong_cardcount = [r["city"] for r in rows if r["n_cards"] != 5]

print(f"=== TOTAL cities in catalog: {total} ===")
print(f"has unique window art (>=1 img on disk): {len(has_art)}")
print(f"NO art (emblem fallback only):           {len(no_art)}")
print(f"locations.json hasCustomImages=true:     {len(flag_true)}")
print(f"flag=true but <5 imgs (data gap):        {len(dirty_flag_no_art)} -> {dirty_flag_no_art[:20]}")
print(f"flag=false but imgs exist (orphan art):  {len(dirty_noflag_art)} -> {dirty_noflag_art[:20]}")
print(f"cities with !=5 cards:                   {len(wrong_cardcount)} -> {wrong_cardcount[:20]}")

# frame-color coverage among NO-art cities
defc = Counter((r["wood"], r["stamp"]) for r in no_art)
print(f"\n--- non-custom frame (wood,stamp) combos: {len(defc)} distinct; top5 ---")
for combo, n in defc.most_common(5):
    print(f"   {n:3d}x  wood={combo[0]} stamp={combo[1]}")
# how many no-art cities have NO frame color at all
no_frame = [r["city"] for r in no_art if not r["wood"] or not r["stamp"]]
print(f"non-custom cities missing wood/stamp: {len(no_frame)}")

# continent spread of the MISSING set
cc = Counter(continent(r["cc"]) for r in no_art)
print(f"\n--- missing-art spread by continent ({len(no_art)}) ---")
for k, v in cc.most_common():
    print(f"   {k}: {v}")
cc_has = Counter(continent(r["cc"]) for r in has_art)
print(f"--- HAS-art spread by continent ({len(has_art)}) ---")
for k, v in cc_has.most_common():
    print(f"   {k}: {v}")

# sample: 3 no-art cities with their referenced (missing) paths + frame colors
print("\n--- sample NO-art cities ---")
for r in no_art[:3]:
    print(f"  {r['city']}  cc={r['cc']} wood={r['wood']} stamp={r['stamp']} emblem={r['emblem']}")
    for p in r["paths"][:2]:
        print(f"      ref(missing): {p}")

# sample: confirm a HAS-art city's images resolve
print("\n--- sample HAS-art city ---")
r = has_art[0]
print(f"  {r['city']}  n_exist={r['n_exist']}/5  flag={r['flag']}")
for p in r["paths"]:
    print(f"      {'OK ' if exists(p) else 'MISS'} {p}")
