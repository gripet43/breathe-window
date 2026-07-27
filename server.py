import os
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

PORT = 3000
MAX_BODY_SIZE = 100 * 1024  # 100KB request body limit

# Helper to read .env file for custom PORT
def load_port():
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        k, v = line.split('=', 1)
                        if k.strip() == 'PORT':
                            return int(v.strip())
        except Exception:
            pass
    return PORT

PORT = load_port()

# Serve from public/ directory (not project root) to avoid exposing .git/, .env, source code
PUBLIC_DIR = os.path.join(os.path.dirname(__file__), 'public')
if not os.path.isdir(PUBLIC_DIR):
    PUBLIC_DIR = os.path.dirname(__file__)  # fallback if public/ doesn't exist

CATALOG_PATH = os.path.join(PUBLIC_DIR, 'assets', 'data', 'catalog.json')
if not os.path.exists(CATALOG_PATH):
    CATALOG_PATH = os.path.join(os.path.dirname(__file__), 'assets', 'data', 'catalog.json')
CATALOG_DATA = {}

def load_catalog():
    global CATALOG_DATA
    if os.path.exists(CATALOG_PATH):
        try:
            with open(CATALOG_PATH, 'r', encoding='utf-8') as f:
                CATALOG_DATA = json.load(f)
            print(f"[推开世界的窗] 成功加载本地图文画册，共计 {len(CATALOG_DATA)} 个地点。")
        except Exception as e:
            print(f"[推开世界的窗] 加载本地图文画册失败: {e}")
    else:
        print(f"[推开世界的窗] 警告: 未找到画册数据库 {CATALOG_PATH}")

load_catalog()

def handle_generate(location=None):
    global CATALOG_DATA
    if not CATALOG_DATA:
        load_catalog()

    # Validate input: location must be a string
    if not isinstance(location, str):
        location = None

    items = []
    if location and location in CATALOG_DATA:
        items = CATALOG_DATA[location]
        print(f"[推开世界的窗] 从本地画册读取地点内容: {location}")
    else:
        loc_key = list(CATALOG_DATA.keys())[0] if CATALOG_DATA else None
        if loc_key:
            items = CATALOG_DATA[loc_key]
            print(f"[推开世界的窗] 地点 {location or 'None'} 未找到，退回到: {loc_key}")
        else:
            items = [
                {
                    "bucket": "世界一角",
                    "title": "静谧的世界一角",
                    "body": "窗外风景正静静上演，时光在这里慢了下来。",
                    "image": "./assets/images/science_nature.png",
                    "ponder": ""
                }
            ]

    return {
        "items": items,
        "demoMode": False
    }


class BreatheRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=PUBLIC_DIR, **kwargs)

    def do_POST(self):
        if self.path.split('?')[0] == '/api/generate':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
            except (ValueError, TypeError):
                content_length = 0

            if content_length > MAX_BODY_SIZE:
                self.send_response(413)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'error': '请求体过大'}).encode('utf-8'))
                return

            post_data = self.rfile.read(content_length) if content_length > 0 else b'{}'
            try:
                req_body = json.loads(post_data.decode('utf-8'))
            except Exception:
                req_body = {}

            try:
                response_data = handle_generate(req_body.get('location', None))

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()

                self.wfile.write(json.dumps(response_data).encode('utf-8'))
            except Exception as e:
                print(f"[推开世界的窗] API 错误: {e}")
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()

                self.wfile.write(json.dumps({'error': '服务器内部错误'}).encode('utf-8'))
        else:
            self.send_response(404)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Not found'}).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()


def run():
    server_address = ('127.0.0.1', PORT)
    httpd = ThreadingHTTPServer(server_address, BreatheRequestHandler)
    print("==================================================")
    print("推开世界的窗 (Open World Window) 本地 Python 服务已启动！")
    print(f"访问地址: http://localhost:{PORT}")
    print("==================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n服务已关闭。")
        httpd.server_close()

if __name__ == '__main__':
    run()
