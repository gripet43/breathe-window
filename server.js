import 'dotenv/config';
import express from 'express';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
app.use(express.json({ limit: '100kb' }));

// Load PORT from environment or default
const PORT = process.env.PORT || 3000;

// CORS headers for all responses
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') {
    return res.sendStatus(200);
  }
  next();
});

// Serve public directory statically
app.use(express.static(path.join(__dirname, 'public')));

const catalogPath = path.join(__dirname, 'public', 'assets', 'data', 'catalog.json');
let catalogData = {};

function loadCatalog() {
  if (fs.existsSync(catalogPath)) {
    try {
      const dataRaw = fs.readFileSync(catalogPath, 'utf8');
      catalogData = JSON.parse(dataRaw);
      console.log(`[推开世界的窗] 成功加载本地图文画册，共计 ${Object.keys(catalogData).length} 个地点。`);
    } catch (e) {
      console.error(`[推开世界的窗] 加载本地图文画册失败: ${e.message}`);
    }
  } else {
    console.warn(`[推开世界的窗] 警告: 未找到画册数据库 ${catalogPath}`);
  }
}

loadCatalog();

app.post('/api/generate', (req, res) => {
  try {
    const location = req.body && typeof req.body.location === 'string' ? req.body.location : null;
    let items = [];

    if (location && catalogData[location]) {
      items = catalogData[location];
      console.log(`[推开世界的窗] 从本地画册读取地点内容: ${location}`);
    } else {
      const keys = Object.keys(catalogData);
      const locKey = keys.length > 0 ? keys[0] : null;
      if (locKey) {
        items = catalogData[locKey];
        console.log(`[推开世界的窗] 地点 ${location || 'None'} 未找到，退回到: ${locKey}`);
      } else {
        items = [
          {
            bucket: "世界一角",
            title: "静谧的世界一角",
            body: "窗外风景正静静上演，时光在这里慢了下来。",
            image: "/assets/images/science_nature.png",
            ponder: ""
          }
        ];
      }
    }

    res.json({
      items: items,
      demoMode: false
    });
  } catch (e) {
    console.error(`[推开世界的窗] API 错误: ${e.message}`);
    res.status(500).json({ error: '服务器内部错误' });
  }
});

// Serve frontend main page on non-API, non-asset GET requests
app.get('*', (req, res) => {
  // Let express.static handle real files; only fall back to index.html for page routes
  if (req.path.startsWith('/api/') || req.path.includes('.')) {
    return res.status(404).json({ error: 'Not found' });
  }
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

const server = app.listen(PORT, () => {
  console.log("==================================================");
  console.log(`推开世界的窗 (Open World Window) Node/Express 服务已启动！`);
  console.log(`访问地址: http://localhost:${PORT}`);
  console.log("==================================================");
});

server.on('error', (e) => {
  if (e.code === 'EADDRINUSE') {
    console.error(`[推开世界的窗] 端口 ${PORT} 已被占用，请关闭其他服务或修改 .env 中的 PORT。`);
  } else {
    console.error(`[推开世界的窗] 服务启动失败: ${e.message}`);
  }
  process.exit(1);
});
