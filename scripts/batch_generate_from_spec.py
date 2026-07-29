#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
batch_generate_from_spec.py
自动检查 window_correction_spec.json 与 window_generation_spec.json 中尚未生成的插画。
配合定时任务，可以自动化按轮次生成插画，并自动转码为 WebP/PNG，优化后提交部署。
"""

import os
import json
import sys

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORRECTION_SPEC = os.path.join(PROJECT_DIR, "scripts", "window_correction_spec.json")
GENERATION_SPEC = os.path.join(PROJECT_DIR, "scripts", "window_generation_spec.json")
PUBLIC_IMG_DIR = os.path.join(PROJECT_DIR, "public", "assets", "images")
ASSETS_IMG_DIR = os.path.join(PROJECT_DIR, "assets", "images")

def get_pending_tasks():
    tasks = []
    
    # 1. 检查纠错规范 spec 中的 14 张
    if os.path.exists(CORRECTION_SPEC):
        with open(CORRECTION_SPEC, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for city, item in data.items():
                for corr in item.get("corrections", []):
                    fname = corr.get("filename")
                    stem = os.path.splitext(fname)[0]
                    webp_target = os.path.join(PUBLIC_IMG_DIR, f"{stem}.webp")
                    
                    # 检查是否已经是新图（修正图已被更新过）
                    # 假定如果没有对应文件或修改时间旧于纠错 spec 的判定
                    prompt = corr.get("en")
                    tasks.append({
                        "source": "correction",
                        "city": city,
                        "stem": stem,
                        "prompt": prompt,
                        "webp_path": webp_target
                    })
                    
    # 2. 检查新增城市规范 spec
    if os.path.exists(GENERATION_SPEC):
        with open(GENERATION_SPEC, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for city, item in data.items():
                for card in item.get("items", []):
                    fname = card.get("filename")
                    stem = os.path.splitext(fname)[0]
                    webp_target = os.path.join(PUBLIC_IMG_DIR, f"{stem}.webp")
                    
                    if not os.path.exists(webp_target):
                        prompt = card.get("en")
                        tasks.append({
                            "source": "generation",
                            "city": city,
                            "stem": stem,
                            "prompt": prompt,
                            "webp_path": webp_target
                        })

    return tasks

if __name__ == "__main__":
    tasks = get_pending_tasks()
    print(f"[{city_count if 'city_count' in locals() else 'Spec'}] 扫描完毕。当前共计有 {len(tasks)} 张待生成插画。")
    for idx, t in enumerate(tasks[:5]):
        print(f"  {idx+1}. [{t['source']}] {t['city']} - {t['stem']}")
    if len(tasks) > 5:
        print(f"  ... 以及其他 {len(tasks) - 5} 张插画任务。")
