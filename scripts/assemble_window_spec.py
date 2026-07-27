#!/usr/bin/env python3
"""Assemble the machine-executable window-generation spec.

Sources of truth:
- backlog.json        -> authoritative missing (bucket, filename) per city; the
                         filename equals what catalog.json currently references.
- locations.json      -> authoritative frame colors (wood / stampColor), emblem,
                         countryCode, hasCustomImages (backlog's stamp is null).
- spec_part_*.json     -> authored identity + zh/en prompts only (6 part files,
                         40 cities each, produced by the author subagents).

Output: scripts/window_generation_spec.json, keyed by city, items in fixed
bucket order, ready to drive image generation + a later catalog update.
"""
import json, glob, os
from collections import Counter

ROOT = "/Users/gripet/.gemini/antigravity/scratch/breathe-window"
SCRATCH = os.path.join(ROOT, "scratch")
PUB = os.path.join(ROOT, "public")
OUT = os.path.join(ROOT, "scripts", "window_generation_spec.json")

BUCKET_ORDER = ["世界一角", "科学自然", "他人在场", "思想火花", "旧物新看"]

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


def main():
    bl = json.load(open(os.path.join(SCRATCH, "backlog.json"), encoding="utf-8"))
    locs = json.load(open(os.path.join(PUB, "assets", "data", "locations.json"), encoding="utf-8"))
    byname = {l["name"]: l for l in locs}

    # merge authored parts
    merged, dupes = {}, []
    parts = sorted(glob.glob(os.path.join(SCRATCH, "spec_part_*.json")))
    for f in parts:
        d = json.load(open(f, encoding="utf-8"))
        for city, v in d.items():
            if city in merged:
                dupes.append(city)
            merged[city] = v

    spec, errors = {}, []
    for city, e in bl.items():
        bl_buckets = {m["bucket"]: m["filename"] for m in e["missing"]}
        l = byname.get(city, {})
        if city not in byname:
            errors.append(f"{city}: not found in locations.json")
        agent = merged.get(city)
        if agent is None:
            errors.append(f"{city}: no authored spec part")
            agent_items = {}
        else:
            agent_items = {it["bucket"]: it for it in agent.get("items", [])}

        items = []
        for b in BUCKET_ORDER:
            if b not in bl_buckets:
                continue  # bucket already has art (e.g. Bagan's 2 present images)
            fn = bl_buckets[b]
            ai = agent_items.get(b)
            if ai is None:
                errors.append(f"{city}/{b}: authored prompt missing")
                zh = en = ""
            else:
                zh, en = ai.get("zh", ""), ai.get("en", "")
            if not zh.strip():
                errors.append(f"{city}/{b}: empty zh prompt")
            if not en.strip():
                errors.append(f"{city}/{b}: empty en prompt")
            items.append({"bucket": b, "filename": fn,
                          "path": "/assets/images/" + fn, "zh": zh, "en": en})

        cc = (l.get("countryCode") or "")
        spec[city] = {
            "countryCode": cc,
            "continent": continent(cc),
            "emblem": l.get("emblem"),
            "wood": l.get("wood"),
            "stampColor": l.get("stampColor"),
            "hasCustomImages": bool(l.get("hasCustomImages")),
            "identity": (agent or {}).get("identity", ""),
            "items": items,
        }

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(spec, fh, ensure_ascii=False, indent=2)

    # report
    total_items = sum(len(v["items"]) for v in spec.values())
    per = Counter(len(v["items"]) for v in spec.values())
    cont = Counter(v["continent"] for v in spec.values())
    item_cont = Counter()
    for v in spec.values():
        if v["items"]:
            item_cont[v["continent"]] += len(v["items"])
    print(f"parts merged: {len(parts)}  | dupes: {len(dupes)} {dupes[:5]}")
    print(f"cities: {len(spec)}  | total image prompts: {total_items}")
    print(f"items-per-city histogram: {dict(per)}")
    print(f"errors: {len(errors)}")
    for er in errors[:20]:
        print("   ", er)
    print("--- cities by continent ---")
    for k, v in cont.most_common():
        print(f"   {k}: {v} cities / {item_cont[k]} images")
    print(f"written -> {OUT}")


if __name__ == "__main__":
    main()
