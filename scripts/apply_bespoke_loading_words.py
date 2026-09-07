#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Apply the 240 bespoke loading quotes to index.html and public/index.html.
Preserves the 62 original hand-crafted cities in their original order.
"""

import os, sys, re, json

ROOT = "/Users/gripet/.gemini/antigravity/scratch/breathe-window"
sys.path.insert(0, ROOT)

from scratch.quotes_asia import ASIA_QUOTES
from scratch.quotes_europe import EUROPE_QUOTES
from scratch.quotes_americas import AMERICAS_QUOTES
from scratch.quotes_africa_oceania import AFRICA_OCEANIA_QUOTES
INDEX_PATH = os.path.join(ROOT, "index.html")

all_new = {}
all_new.update(ASIA_QUOTES)
all_new.update(EUROPE_QUOTES)
all_new.update(AMERICAS_QUOTES)
all_new.update(AFRICA_OCEANIA_QUOTES)

with open(INDEX_PATH, "r", encoding="utf-8") as f:
    html = f.read()

# Locate locMap
start_marker = "const locMap = {"
start_idx = html.find(start_marker)
if start_idx == -1:
    raise ValueError("const locMap = { not found in index.html")

end_marker = "};"
end_idx = html.find(end_marker, start_idx)
if end_idx == -1:
    raise ValueError("}; closing locMap not found in index.html")

# Parse existing entries to keep their exact keys and preserve the 62 handcrafted ones
block = html[start_idx:end_idx+2]
entries = re.findall(r'\"([^\"]+)\":\s*\[(.*?)\]', block, re.DOTALL)

templates = [
    '正在穿过.*的街巷',
    '感受到.*的微风吹拂',
    '正在攀越.*的云雾',
    '正在聆听.*海浪的低语',
    '正触摸着.*斑驳的城墙',
    '正在走进.*的葱郁深处',
    '凝视着.*残留的辉煌',
    '的水波正轻轻荡漾'
]
tpl_regex = re.compile('|'.join(templates))

final_map = {}
for city, qstr in entries:
    quotes = [s.strip().strip('\"\'') for s in qstr.split(',') if s.strip()]
    if any(tpl_regex.search(q) for q in quotes):
        # Needs replacement
        if city in all_new:
            final_map[city] = all_new[city]
        else:
            print(f"Warning: {city} not found in all_new, keeping original")
            final_map[city] = quotes
    else:
        # Handcrafted keep
        final_map[city] = quotes

print(f"Total entries in final locMap: {len(final_map)}")

# Format the new locMap nicely
lines = ["const locMap = {"]
for i, (city, quotes) in enumerate(final_map.items()):
    lines.append(f'      "{city}": [')
    for j, q in enumerate(quotes):
        comma = "," if j < len(quotes) - 1 else ""
        lines.append(f'        "{q}"{comma}')
    comma_entry = "," if i < len(final_map) - 1 else ""
    lines.append(f'      ]{comma_entry}')
lines.append("    };")

new_block = "\n".join(lines)

# Replace in html
new_html = html[:start_idx] + new_block + html[end_idx+2:]

with open(INDEX_PATH, "w", encoding="utf-8") as f:
    f.write(new_html)

print("Successfully injected new locMap into index.html!")
