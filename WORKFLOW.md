# Breathe-Window 开发与防回归工作流规范 (Development & Anti-Regression Workflow)

为了确保每次修改代码、新增城市、更新图片或优化样式时，**绝不会破坏已有功能或引入新的 Bug**，请严格遵守以下工程规范与自动化流程。

---

## 🛠️ 自动化工具与命令

本项目已建立全自动化的构建、同步与测试套件：

| 命令 | 说明 | 适用场景 |
| :--- | :--- | :--- |
| `npm run build` 或 `python3 scripts/build.py` | **一键构建与自动同步**：自动双向同步根目录与 `public/`、自动扫描真实图片文件重新计算 `hasCustomImages`、自动修复图片格式扩展名、重新生成 CSS 主题并运行完整测试 | 任何代码/数据/图片修改后运行 |
| `npm run verify` 或 `python3 scripts/verify_project.py` | **全自动化防回归测试套件**：执行 6 大维度（数据模式、图片存在性、文件同步、代码语法、加载文案完整性等）的严格校验 | 提交代码前校验 |
| `python3 scripts/install_hooks.py` | **安装 Git Pre-commit 拦截钩子**：每次 `git commit` 时会自动触发防回归测试，有任何报错将直接拒绝提交 | 首次克隆或环境初始化时运行 |

---

## 🛡️ 核心防回归原则 (Zero Regression Principles)

### 1. 双端同步一致性 (Sync Rule)
- 线上部署默认使用 `public/` 目录，本地测试或服务也使用根目录与 `public/`。
- **规则**：修改 `index.html` 或 `assets/` 数据后，必须运行 `npm run build` 确保 `public/` 与根目录 100% 字节一致。

### 2. 图片真实存在性与 404 兜底机制 (Asset Integrity Rule)
- **规则**：`locations.json` 中的 `hasCustomImages` 只能由 `scripts/build.py` 依据磁盘上实际存在的 5 张全套 `.webp` 文件自动计算，**严禁人工手动全量置为 `true`**。
- 如果某城市仅生成了 1~4 张图片（未满 5 张），`hasCustomImages` 保持 `false`，确保其余卡片安全走默认优雅插画，绝不报 404。

### 3. 数据完整性与 Schema 统一 (Data Schema Rule)
- 所有城市必须包含 11 个标准字段：`name`, `countryCode`, `lat`, `lng`, `emblem`, `wood`, `woodDark`, `glow`, `stampColor`, `locClass`, `hasCustomImages`。
- 每个城市在 `catalog.json` 中必须严格拥有 5 张卡片（顺序为：世界一角、科学自然、他人在场、思想火花、旧物新看）。
- 每个城市在 `index.html` 的 `locMap` 中必须拥有 4 句专属诗意 Loading 词。

### 4. 图片生成防文字注入规范 (Image Generation Prompt Rule)
- 新生成图片必须严格包含强力去字负面约束提示词：
  `NO TEXT, NO LETTERS, NO WORDS, NO SIGNBOARDS, NO LABELS, NO WATERMARK, NO SIGNATURE, NO HIEROGLYPHICS, NO LOGO`
- 生成完成后应使用 `Pillow` 自动转为高质量 `.webp` 格式并同时放置于 `assets/images/` 与 `public/assets/images/`。

---

## 🚀 标准开发步骤 (Step-by-Step SOP)

1. **进行代码或数据修改**（例如新增城市数据、修改前端样式、生成新批次插画等）。
2. **执行一键构建与自检**：
   ```bash
   npm run build
   ```
3. **查看测试输出**：
   - 若全部通过（`✓ ALL TESTS PASSED!`），可安全提交。
   - 若有报错，根据终端提示进行修复后再次执行 `npm run build`。
4. **提交并推送至 GitHub**：
   ```bash
   git add .
   git commit -m "Your descriptive commit message"
   git push origin main
   ```
   *（如果触发了 Pre-commit Hook 报错，Git 会自动阻止提交，保障线上环境 100% 稳定）*
