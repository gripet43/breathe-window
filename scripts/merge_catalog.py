import json
import os
import glob

project_dir = "/Users/gripet/.gemini/antigravity/scratch/breathe-window"
data_dir = os.path.join(project_dir, "public", "assets", "data")
catalog_path = os.path.join(data_dir, "catalog.json")

def merge_catalog():
    if not os.path.exists(catalog_path):
        print(f"Error: Catalog not found at {catalog_path}")
        return

    with open(catalog_path, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    print(f"Initial catalog has {len(catalog)} cities.")

    # Find all batch_*.json files
    batch_files = glob.glob(os.path.join(data_dir, "batch_*.json"))
    batch_files.sort(key=lambda x: int(os.path.basename(x).split('_')[1].split('.')[0]))

    merged_count = 0
    for batch_path in batch_files:
        try:
            with open(batch_path, "r", encoding="utf-8") as f:
                batch_data = json.load(f)
            for city, cards in batch_data.items():
                catalog[city] = cards
                merged_count += 1
            print(f"Merged {os.path.basename(batch_path)}: added {len(batch_data)} cities.")
        except Exception as e:
            print(f"Error reading {os.path.basename(batch_path)}: {e}")

    with open(catalog_path, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)

    print(f"Merge completed. Total cities in catalog: {len(catalog)} (added {merged_count} new cities).")

if __name__ == "__main__":
    merge_catalog()

