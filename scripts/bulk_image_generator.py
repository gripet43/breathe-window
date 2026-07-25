#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
bulk_image_generator.py
用于批量替换 breathe-window 中所有仍然是占位图的插画。
支持两种模式：
1. "sd_webui" (默认): 调用本地部署的 Stable Diffusion WebUI API (适合零成本、配合 LoRA 进行水彩画风格大批量跑图)。
2. "dalle3": 调用 OpenAI DALL-E 3 接口进行高质量单张生成。

配置环境变量：
- 如果使用 OpenAI: export OPENAI_API_KEY="your-key"
- 如果使用 Stable Diffusion: 请确保 WebUI 启动时带上了 --api 参数（默认监听 http://127.0.0.1:7860）
"""

import os
import json
import base64
import requests
import time

# ==================== 配置区 ====================
MODE = "gemini"  # 可选: "sd_webui", "dalle3" 或 "gemini"

# Stable Diffusion API 配置
SD_API_URL = "http://127.0.0.1:7860/sdapi/v1/txt2img"
SD_NEGATIVE_PROMPT = "blurry, low quality, photorealistic, realistic, photograph, 3d render, distorted faces, text, watermark"

# DALL-E 3 API 配置
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

# Gemini API 配置
def load_gemini_key():
    key = os.environ.get("GEMINI_API_KEY", "")
    if not key:
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env_path = os.path.join(project_dir, ".env")
        if os.path.exists(env_path):
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            k, v = line.split('=', 1)
                            if k.strip() == "GEMINI_API_KEY":
                                return v.strip()
            except Exception:
                pass
    return key

GEMINI_API_KEY = load_gemini_key()

# 占位图特征尺寸 (大小匹配这四个的文件属于模板占位图)
PLACEHOLDER_SIZES = {790453, 981515, 1026331, 1076134}
# ===============================================

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOG_PATH = os.path.join(PROJECT_DIR, "public", "assets", "data", "catalog.json")
IMAGES_DIR = os.path.join(PROJECT_DIR, "public", "assets", "images")

def is_placeholder(img_path):
    if not os.path.exists(img_path):
        return True
    
    sz = os.path.getsize(img_path)
    # 如果大小和基础模版一致，或者是苏州的首图占位图 (大小1066786)
    if sz in PLACEHOLDER_SIZES or (os.path.basename(img_path) == "loc_suzhou.png" and sz == 1066786):
        return True
    return False

def generate_via_sd(prompt, save_path):
    # 针对水彩画风做出的 Prompt 微调
    kaiti_prompt = f"{prompt}, warm watercolor style illustration, warm tones, soft colors, cozy and peaceful, cream paper texture, hand-drawn vector elements, minimal lineart"
    
    payload = {
        "prompt": kaiti_prompt,
        "negative_prompt": SD_NEGATIVE_PROMPT,
        "steps": 25,
        "cfg_scale": 7.0,
        "width": 1024,
        "height": 1024,
        "sampler_name": "Euler a",
        # 如果你有专门的水彩 LoRA，可以在此填入，例如:
        # "prompt": f"<lora:watercolor:0.8> {kaiti_prompt}",
    }
    
    try:
        response = requests.post(SD_API_URL, json=payload, timeout=120)
        if response.status_code == 200:
            r = response.json()
            # 获取 base64 并保存
            img_data = base64.b64decode(r['images'][0])
            with open(save_path, 'wb') as f:
                f.write(img_data)
            print(f"✓ [SD] 生成成功并保存至: {os.path.basename(save_path)}")
            return True
        else:
            print(f"✗ [SD] API 报错，状态码: {response.status_code}, 内容: {response.text}")
            return False
    except Exception as e:
        print(f"✗ [SD] 无法连接到 SD WebUI API ({SD_API_URL}): {e}")
        return False

def generate_via_dalle(prompt, save_path):
    if not OPENAI_API_KEY:
        print("✗ [DALL-E] 错误: 未配置环境变量 OPENAI_API_KEY")
        return False
        
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    
    payload = {
        "model": "dall-e-3",
        "prompt": prompt,
        "n": 1,
        "size": "1024x1024",
        "quality": "standard"
    }
    
    try:
        url = "https://api.openai.com/v1/images/generations"
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        if response.status_code == 200:
            data = response.json()
            img_url = data['data'][0]['url']
            
            # 下载图片
            img_response = requests.get(img_url, timeout=30)
            if img_response.status_code == 200:
                with open(save_path, 'wb') as f:
                    f.write(img_response.content)
                print(f"✓ [DALL-E] 生成成功并保存至: {os.path.basename(save_path)}")
                return True
        elif response.status_code == 429:
            print("✗ [DALL-E] 触及 OpenAI 接口频率上限 (429)，将进行等待...")
            return "429"
        else:
            print(f"✗ [DALL-E] API 报错: {response.status_code}, 内容: {response.text}")
            return False
    except Exception as e:
        print(f"✗ [DALL-E] 接口调用异常: {e}")
        return False

def generate_via_gemini(prompt, save_path):
    if not GEMINI_API_KEY:
        print("✗ [Gemini] 错误: 未配置环境变量或 .env 中的 GEMINI_API_KEY")
        return False
        
    model = "gemini-3.1-flash-image"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    # 针对水彩画风做出的 Prompt 微调
    kaiti_prompt = f"{prompt}, warm watercolor style illustration, warm tones, soft colors, cozy and peaceful, cream paper texture, hand-drawn vector elements, minimal lineart"
    
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": kaiti_prompt
                    }
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "image/png"
        }
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=90)
        if response.status_code == 200:
            data = response.json()
            try:
                parts = data['candidates'][0]['content']['parts']
                image_b64 = None
                for part in parts:
                    if 'inlineData' in part:
                        image_b64 = part['inlineData']['data']
                        break
                if image_b64:
                    img_data = base64.b64decode(image_b64)
                    with open(save_path, 'wb') as f:
                        f.write(img_data)
                    print(f"✓ [Gemini] 生成成功并保存至: {os.path.basename(save_path)}")
                    return True
                else:
                    print(f"✗ [Gemini] 响应中未找到图片数据: {data}")
                    return False
            except Exception as e:
                print(f"✗ [Gemini] 解析响应 JSON 失败: {e}, 原始响应内容: {data}")
                return False
        else:
            print(f"✗ [Gemini] API 报错，状态码: {response.status_code}, 内容: {response.text}")
            return False
    except Exception as e:
        print(f"✗ [Gemini] 接口调用异常: {e}")
        return False


def main():
    if not os.path.exists(CATALOG_PATH):
        print(f"Error: 找不到数据目录 {CATALOG_PATH}")
        return
        
    with open(CATALOG_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 扫描需要重新生成的占位图
    queue = []
    for city_name, cards in data.items():
        for idx, card in enumerate(cards):
            img_rel_path = card.get("image")
            img_name = os.path.basename(img_rel_path)
            img_abs_path = os.path.join(IMAGES_DIR, img_name)
            
            if is_placeholder(img_abs_path):
                title = card.get("title")
                body = card.get("body")
                # 构造符合当期水彩风格的绘画 Prompt
                prompt = f"A warm watercolor style illustration of {title}. {body} warm tones, soft colors, cozy and peaceful, cream paper texture"
                queue.append({
                    "city": city_name,
                    "card_idx": idx + 1,
                    "prompt": prompt,
                    "save_path": img_abs_path,
                    "name": img_name
                })
                
    print(f"扫描完毕。当前共计有 {len(queue)} 张占位图等待批量渲染生成。")
    if not queue:
        print("所有图片均已是定制插画！无需生成。")
        return
        
    print(f"当前渲染模式: {MODE.upper()}")
    
    success_count = 0
    for task in queue:
        print(f"\n正在为 [{task['city']}] 生成 Card {task['card_idx']} ({task['name']})...")
        print(f"Prompt: {task['prompt']}")
        
        if MODE == "sd_webui":
            success = generate_via_sd(task['prompt'], task['save_path'])
            if success:
                success_count += 1
            # 延时 1s 防止本地压力太大
            time.sleep(1)
        elif MODE == "gemini":
            success = generate_via_gemini(task['prompt'], task['save_path'])
            if success:
                success_count += 1
            # 稍微延时 1s 防止超出 API 限频
            time.sleep(1)
        else:
            # DALL-E 3 模式
            result = generate_via_dalle(task['prompt'], task['save_path'])
            if result == True:
                success_count += 1
                time.sleep(5)  # 礼貌性延时
            elif result == "429":
                print("等待 30 秒后重试此任务...")
                time.sleep(30)
                # 再次重试
                if generate_via_dalle(task['prompt'], task['save_path']) == True:
                    success_count += 1
            else:
                time.sleep(2)
                
    print(f"\n批量生成管线运行结束！共成功渲染并覆盖 {success_count} / {len(queue)} 张插画。")

if __name__ == "__main__":
    main()
