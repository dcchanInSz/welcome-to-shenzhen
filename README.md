# Welcome to Shenzhen / 深圳 APEC 2026 城市指南

**English-primary**, bilingual (English / 中文) static city guide for
**Shenzhen as host city of APEC 2026**.
Plain HTML/CSS/JS, zero runtime dependencies, zero external requests — works offline from the file system.

面向 **2026 年 APEC 中国年深圳会议** 的双语静态城市指南（默认英文，可切换中文）。

---

## 一、事实核对 / Verified facts

| 项目 | 内容 |
| --- | --- |
| 事件 | 亚太经合组织第三十三次领导人非正式会议（33rd APEC Economic Leaders' Meeting） |
| 时间 | **2026-11-18 → 2026-11-19**（周三至周四） |
| 工商峰会 | APEC CEO Summit，**2026-11-17 → 11-18**（周二至周三），中国贸促会主办 |
| 主题 | 构建亚太共同体，促进共同繁荣 |
| 峰会主题 | 促进共同繁荣，开创共赢未来 |
| 城市 | 中国广东省深圳市 |
| 背景 | 中国第三次主办 APEC、时隔 12 年；APEC「中国年」全年约 300 场活动分布多城 |

来源：深圳市政府门户（sz.gov.cn）、APEC 中国年官网（apec2026.cn）、新华社/中国政府网。

---

## 二、目录结构 / Layout

```
.
├── assets/                 源资源（CSS / JS / 图片）— 构建时复制进 dist/
├── robots.txt / sitemap.xml
├── dist/                   ★ 打包产物（部署 / 本地服务只看这里）
│   ├── *.html
│   ├── assets/
│   ├── robots.txt
│   └── sitemap.xml
│
└── src/
    ├── pages/*.html        13 个页面片段（真正要编辑的文件）
    ├── partials/base.html  全站外壳：header / nav / footer / 语言开关
    ├── build.py            → 输出到 dist/
    ├── serve.py            构建并在 dist/ 上起本地服务
    ├── check.py            校验 dist/
    ├── verify.mjs          Chrome 渲染校验（读 dist/）
    ├── probe.mjs / art.py
    └── CONTRACT.md
```

页面清单：`index` · `apec-2026` · `city` · `attractions` · `food` · `stay` ·
`transport` · `shopping` · `itineraries` · `business` · `services` · `faq` · `about`

**只改 `src/pages/` 与 `assets/`。** `dist/` 是生成结果，改了也会被下次 build 覆盖；已加入 `.gitignore`。

---

## 三、怎么用 / How to work on it

```bash
# 1) 改内容：编辑 src/pages/<页面>.html 或 assets/
# 2) 打包到 dist/
python3 src/build.py
# 3) 静态校验（针对 dist/）
python3 src/check.py
# 4) 渲染校验
node src/verify.mjs
# 5) 本地预览（推荐）：构建 + 在 dist/ 起服务
python3 src/serve.py
#    或已构建过：
python3 -m http.server 8000 --directory dist
```

打开 http://127.0.0.1:8000/ 。

### 部署到 Cloudflare（`langcode.app/shenzhen`）

```bash
npm run deploy   # build → dist/ → wrangler deploy
```

线上地址：https://langcode.app/shenzhen/  
Worker 路由：`langcode.app/shenzhen*`（配置见 `wrangler.jsonc` + `worker.js`）。

`verify.mjs` 只用 Node 内置能力（Node 18+）+ 本机 Chrome，无需 `npm install`。

### 新增一个页面

1. 复制任一 `src/pages/*.html`，开头保留 `<!--meta … nav: 新文件名.html -->` 头部；
2. 在 `src/partials/base.html` 的导航 `<ul>` 和页脚里加上链接；
3. 跑 `python3 src/build.py && python3 src/check.py`。

---

## 四、双语机制 / How bilingual works

**English is the default.** The shell ships with `<html lang="en" data-lang="en">`.
One file per page holds both languages; CSS toggles visibility:

```html
<p class="lang-en">English copy</p>
<p class="lang-zh">中文文案</p>
```

CSS：`[data-lang="en"] .lang-zh { display:none }` 与反向。
`assets/site.js` 读写 `data-lang`，偏好存入 `localStorage`（`sz-apec-lang`）；
无偏好时固定为英文（主站语言），点「中文」后会记住。无 Cookie、无追踪、无外链请求。

`<!--meta-->` 的 `title` / `desc` 用英文；canonical / `og:url` 由 `src/build.py` 注入，
域名可用环境变量 `SITE_ORIGIN` 覆盖（默认 `https://welcome-to-shenzhen.pages.dev`）。

新增文案必须成对提供 `lang-zh` / `lang-en`，否则 `src/check.py` 会报配平错误。

---

## 五、图片 / Images

`assets/img/` 现有资源：

| 文件 | 用途 | 现状 |
| --- | --- | --- |
| `hero-cover.png` | 首页英雄区背景 + 12 个内页页头背景 | ✅ 2400×1040，已调好裁切 |
| `cover-card.png` | 备用构图卡 | ⚠️ 当前无人引用 |
| `scene-bay/night/coast/tech/oldtown.png` | 内容配图 | ⚠️ bay/night/coast/oldtown 已用在 attractions，tech 未被引用 |
| `scene-metro.png` | 备用地铁站氛围图 | ✅ 资源保留 |
| `metro-system-map.jpg` | 官方风格线网图（首页 + 交通页） | ✅ 已引用 |
| `og-cover.png` | 社交分享预览图 | ✅ 1200×630 |
| `cover-card.png` | 城市概览配图 | ✅ 已用于 `city.html` |
| `scene-tech.png` | 商务页配图 | ✅ 已用于 `business.html` |
| `favicon.svg` | 站点图标 | ✅ |

这些插画由 `src/art.py` 程序化生成（numpy + Pillow），**无第三方图片版权**。
可按同名覆盖为已授权真图。`scene-*.png` 目前多为预览分辨率；全分辨率：`python3 src/art.py`。

**换成真实照片前请注意**：APEC 名称与标识有使用规范；不要直接抓取新闻图片。见 `TODO.md`。

---

## 六、设计系统 / Design system

`assets/style.css` 顶部是全站设计令牌（色板、圆角、阴影、字号），下面是全部组件类。
写作时请只用文档里列出的类名，不要临时造新类。完整类名清单见 **`src/CONTRACT.md` 第 4 节**。

主色：`--teal #0e7c86` · `--azure #1e93e8` · `--seafoam #3fd0c9` · `--coral #ff6b4a` ·
`--gold #f2b544` · 深底 `--ink #06141f`

---

## 七、当前状态 / Status

- **English-primary** bilingual site, 13 pages
- Social meta (`canonical`, `og:*`, `twitter:*`), `sitemap.xml`, `robots.txt`
- CI: `.github/workflows/ci.yml` runs `build.py` + `check.py` + `verify.mjs`
- Remaining manual work (real photos, fact audit, device QA): see `TODO.md` / `CHANGELOG.md`

本地校验：

```bash
python3 src/build.py && python3 src/check.py && node src/verify.mjs
```

---

## 八、已知取舍 / Known trade-offs

- **`dist/` 是唯一运行时目录**：源码在 `src/` + `assets/`，不要手改 `dist/`。
- **表格在手机上横向滚动**：`table` 有 `min-width: 520px`，外层 `.table-wrap` 负责滚动，
  因此页面本身不会横向溢出（已验证 `window.scrollX` 恒为 0）。
- **`lang-zh` / `lang-en` 配平按节点计数**：双语以「整页区块」为粒度配对属正常。
- **未使用任何 web 字体**：系统字体栈，保证离线可用、首屏无阻塞。
- **`src/probe.mjs` 是调试工具**，可随时删除。
