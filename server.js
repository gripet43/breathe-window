const express = require('express');
const path = require('path');
const fs = require('fs');

const app = express();
app.use(express.json());

// Load PORT from environment or default
const PORT = process.env.PORT || 3000;

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
  const { location } = req.body;
  let items = [];

  if (location && catalogData[location]) {
    items = catalogData[location];
    console.log(`[推开世界的窗] 从本地画册读取地点内容: {location}`);
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
});

// Serve frontend main page on other requests
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(PORT, () => {
  console.log("==================================================");
  console.log(`推开世界的窗 (Open World Window) Node/Express 服务已启动！`);
  console.log(`访问地址: http://localhost:${PORT}`);
  console.log("==================================================");
});
