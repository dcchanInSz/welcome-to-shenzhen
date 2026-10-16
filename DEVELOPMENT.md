# 开发指南

面向维护与二次开发。访客请看 [README.md](./README.md)；线上站点：[langcode.app/shenzhen](https://langcode.app/shenzhen/)。

English-primary 双语静态站：纯 HTML/CSS/JS，零运行时依赖，构建产物在 `dist/`。

---

## 目录结构

```
.
├── assets/                 源资源（CSS / JS / 图片）— 构建时复制进 dist/
├── dist/                   打包产物（部署 / 本地服务只看这里，已 gitignore）
├── src/
│   ├── pages/*.html        13 个页面片段（真正要编辑的文件）
│   ├── partials/base.html  全站外壳：header / nav / footer / 语言开关 / SEO
│   ├── build.py            → 输出到 dist/（含 sitemap、robots、JSON-LD）
│   ├── serve.py            构建并在 dist/ 上起本地服务
│   ├── check.py            校验 dist/
│   ├── verify.mjs          Chrome 渲染校验（读 dist/）
│   ├── probe.mjs / art.py
│   └── CONTRACT.md         设计系统 / 类名契约
├── worker.js               Cloudflare Worker（/shenzhen 路由与 308）
└── wrangler.jsonc
```

页面：`index` · `apec-2026` · `city` · `attractions` · `food` · `stay` ·
`transport` · `shopping` · `itineraries` · `business` · `services` · `faq` · `about`

**只改 `src/pages/` 与 `assets/`。** 不要手改 `dist/`，下次 build 会覆盖。

---

## 本地开发

```bash
# 1) 改内容：编辑 src/pages/<页面>.html 或 assets/
# 2) 打包到 dist/
python3 src/build.py
# 或：SITE_ORIGIN=https://langcode.app/shenzhen python3 src/build.py

# 3) 静态校验
python3 src/check.py

# 4) 渲染校验（Node 18+ + 本机 Chrome，无需 npm install）
node src/verify.mjs

# 5) 本地预览
python3 src/serve.py
# 或已构建过：
python3 -m http.server 8000 --directory dist
```

打开 http://127.0.0.1:8000/ 。

快捷脚本（需 Node，用于 wrangler）：

```bash
npm run build    # SITE_ORIGIN=https://langcode.app/shenzhen python3 src/build.py
npm run check
npm run serve
npm run deploy   # build → wrangler deploy
```

---

## 部署（Cloudflare）

```bash
npm run deploy
```

- 线上：https://langcode.app/shenzhen/
- 路由：`langcode.app/shenzhen*`（见 `wrangler.jsonc` + `worker.js`）
- 首页 canonical：`/shenzhen/`（Worker 对 `/shenzhen`、`/shenzhen/index.html` 做 308）

Hub 站点在独立仓库/目录 `langcode/`，不在本项目内。

---

## 新增页面

1. 复制任一 `src/pages/*.html`，保留 `<!--meta … nav: 新文件名.html -->` 头部；
2. 在 `src/partials/base.html` 的导航与页脚加上链接；
3. 跑 `python3 src/build.py && python3 src/check.py`。

`build.py` 会按 `src/pages` 扫描更新 sitemap，并为内页注入 BreadcrumbList；`faq.html` / `apec-2026.html` 另有 FAQPage / Event JSON-LD。

---

## 双语机制

默认英文：`<html lang="en" data-lang="en">`。同一文件内双语并存，CSS 切换可见性：

```html
<p class="lang-en">English copy</p>
<p class="lang-zh">中文文案</p>
```

- CSS：`[data-lang="en"] .lang-zh { display:none }` 与反向
- `assets/site.js` 读写 `data-lang`，偏好存 `localStorage`（`sz-apec-lang`）
- 无 Cookie、无追踪、无外链请求
- `<!--meta-->` 的 `title` / `desc` 用英文；canonical / OG 由 `build.py` 注入
- 域名可用 `SITE_ORIGIN` 覆盖（默认 `https://langcode.app/shenzhen`）
- 新增文案必须成对 `lang-zh` / `lang-en`，否则 `check.py` 会报配平错误

---

## 图片

| 文件 | 用途 |
| --- | --- |
| `hero-cover.png` | 首页英雄区 + 内页页头背景 |
| `cover-card.png` | 城市概览配图 |
| `scene-bay/night/coast/tech/oldtown.png` | 景点 / 商务等内容配图 |
| `metro-system-map.jpg` | 地铁线网图（首页 + 交通页） |
| `og-cover.png` | 社交分享 1200×630 |
| `favicon.svg` | 站点图标 |

插画可由 `src/art.py` 生成（numpy + Pillow）。换成实拍前注意 APEC 标识使用规范，勿直接抓取新闻图。见 `TODO.md`。

---

## 设计系统

令牌与组件在 `assets/style.css` 顶部。写作时只用 `src/CONTRACT.md` 第 4 节列出的类名。

主色：`--teal #0e7c86` · `--azure #1e93e8` · `--seafoam #3fd0c9` · `--coral #ff6b4a` · `--gold #f2b544` · `--ink #06141f`

---

## 校验与 CI

```bash
python3 src/build.py && python3 src/check.py && node src/verify.mjs
```

`.github/workflows/ci.yml` 跑同上流程。若推送 workflow 被拒，需 `gh auth refresh -s workflow`。

更多待办见 `TODO.md` / `CHANGELOG.md`。

---

## 已知取舍

- **`dist/` 是唯一运行时目录**：源码在 `src/` + `assets/`。
- **表格在手机上横向滚动**：`table` 有 `min-width`，外层 `.table-wrap` 负责滚动。
- **`lang-zh` / `lang-en` 配平按节点计数**：整页区块配对属正常。
- **未使用 web 字体**：系统字体栈，保证离线可用。
- **本阶段不做**：去扩展名 clean URL；ZH/EN 分 URL + hreflang。
