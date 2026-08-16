#!/usr/bin/env python3
import json, os

ROOT = "/Users/gripet/.gemini/antigravity/scratch/breathe-window"
CARDS_FILE = os.path.join(ROOT, "scratch", "sorted_mismatches.json")

data = json.load(open(CARDS_FILE, encoding="utf-8"))
with_prompt = [d for d in data if d["status"] != "NO_PROMPT"]

print(f"Total cards with recorded prompt: {len(with_prompt)}")

# Print lowest overlap cards with prompts
with open(os.path.join(ROOT, "scratch", "prompt_vs_catalog_ranked.txt"), "w", encoding="utf-8") as f:
    for idx, item in enumerate(with_prompt):
        f.write(f"#{idx+1} [Overlap: {item['overlap']:.3f}] {item['city']} | {item['bucket']}\n")
        f.write(f"  Title: {item['title']}\n")
        f.write(f"  Body:  {item['body']}\n")
        f.write(f"  Spec:  {item['prompt']}\n")
        f.write(f"  Image: {item['image']}\n\n")

print("Saved prompt_vs_catalog_ranked.txt")

# Let's inspect the bottom 30 with lowest overlap
for item in with_prompt[:25]:
    print(f"[{item['overlap']:.3f}] {item['city']} ({item['bucket']}): {item['title']}")
    print(f"  Text: {item['body'][:50]}...")
    print(f"  Spec: {item['prompt'][:50]}...")
    print()
