#!/usr/bin/env python3
import json, os, re

ROOT = "/Users/gripet/.gemini/antigravity/scratch/breathe-window"
CARDS_FILE = os.path.join(ROOT, "scratch", "all_custom_cards_comparison.json")

cards = json.load(open(CARDS_FILE, encoding="utf-8"))

def get_char_bigrams(text):
    # normalize
    text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', '', text)
    if len(text) < 2:
        return set(text)
    return set(text[i:i+2] for i in range(len(text)-1))

results = []

for c in cards:
    if not c["has_prompt"]:
        results.append({
            "status": "NO_PROMPT",
            "city": c["city"],
            "bucket": c["bucket"],
            "title": c["title"],
            "body": c["body"],
            "image": c["image"],
            "prompt": c["prompt"],
            "overlap": 0
        })
        continue
        
    text_content = c["title"] + " " + c["body"]
    prompt = c["prompt"]
    
    bg_text = get_char_bigrams(text_content)
    bg_prompt = get_char_bigrams(prompt)
    
    if not bg_prompt:
        overlap_score = 0
    else:
        common = bg_text.intersection(bg_prompt)
        overlap_score = len(common) / min(len(bg_text), len(bg_prompt))
        
    results.append({
        "status": "CHECK",
        "city": c["city"],
        "bucket": c["bucket"],
        "title": c["title"],
        "body": c["body"],
        "image": c["image"],
        "prompt": prompt,
        "overlap": round(overlap_score, 3)
    })

# Sort by overlap ascending
sorted_results = sorted(results, key=lambda x: x["overlap"])

with open(os.path.join(ROOT, "scratch", "sorted_mismatches.json"), "w", encoding="utf-8") as f:
    json.dump(sorted_results, f, ensure_ascii=False, indent=2)

print("Top 30 lowest overlap cards:")
for item in sorted_results[:30]:
    print(f"[{item['overlap']:.3f}] {item['city']} ({item['bucket']}): {item['title']}")
    print(f"    Text: {item['body'][:45]}...")
    print(f"    Spec: {item['prompt'][:45]}...")
    print()
