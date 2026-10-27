# 待办清单 / Remaining work

已完成事项见 `CHANGELOG.md`（2026-10-13）与下方 G 节。下面是**还没做完**的事项。

图例：🔴 高优先级 · 🟡 中优先级 · 🟢 锦上添花

---

## A. 图片与合规（需你本人出图 / 授权确认）

- [x] 🟡 **地标风格配图已生成**（AI 生成，非新闻实拍）：`hero-cover` / `scene-*` / `cover-card` / `og-cover`
  - 若要真摄影或更高分辨率，同名覆盖 `assets/img/` 后重建 `dist/`
- [ ] 🔴 **图片版权确认**：AI 生成图用于本站自用一般可接受；若商用/冠名发布请再核对平台条款；勿用新闻实拍；APEC 标识勿使用
- [x] 🟡 **APEC 相关表述合规**：已改为中性描述 + 「以官方公告为准」+ 命名说明 callout
- [x] 🟡 **真实深圳地铁线路图**已接入（`metro-system-map.jpg`，首页 + 交通页；注明来源深圳地铁）
- [ ] 🟢 为每张图补更准确的 `alt` 文案

---

## B. 事实与数据复核（人工）

- [ ] 🔴 **逐页复核数字与政策**（`apec-2026` / `services` / `transport` / `shopping` / `stay` / `attractions` / `city` / `food`）
- [ ] 🔴 **给关键数据加来源脚注**（统一「来源 + 年份 + 查询日期」）
- [x] 🟡 **会议场地信息**：已明确「以官方最终公布为准」，代表页不再写死上下客点
- [ ] 🟡 **核对 11 月气候数据**（可补历史极值 / 统计区间）
- [ ] 🟡 **复核「深圳有 16 个口岸」等口径**与通关时间
- [ ] 🟢 核对 APEC 成员经济体数量、中国历次主办年份等背景数据

---

## C. 视觉与体验

- [x] 🟡 **`.card-icon` 改内联 SVG**（首页 / 住宿 / 景点）
- [x] 🟡 **首页英雄区背景裁切**：换真实照片后已重调（天际线留在画面中部，遮罩变薄；窄屏改从右侧取景）
- [x] 🟡 **`cover-card.png` 已用于 `city.html`**
- [x] 🟡 **`scene-tech.png` 已用于 `business.html`**
- [x] 🟢 **为更多内容页补配图**：食 / 住 / 购 / 行程 / APEC / 服务
- [x] 🟢 **`.timeline` / `.steps` 滚动渐进高亮**
- [x] 🟢 **深色模式**（`prefers-color-scheme: dark`）
- [x] 🟢 **打印样式**：退税随身卡 + 基础打印隐藏

---

## D. 内容深度与功能

- [ ] 🟡 **英文文案母语润色**（尤其 `attractions.html`、`faq.html`）
- [x] 🟡 **参会代表专用内容**（邀请/注册、安检、接送占位、实时信息占位）
- [x] 🟡 **购物退税可打印清单**（`shopping.html#tax-refund-checklist`）
- [ ] 🟡 **中文繁简**（可扩展 `lang-zh-Hant`）
- [ ] 🟢 **站内搜索**
- [ ] 🟢 **离线地图**（静态手绘）
- [ ] 🟢 **行程可导出**（.ics / PDF）
- [x] 🟢 **会议周实时信息占位区**（`apec-2026.html`）

---

## E. 工程 / 校验 / 部署

- [ ] 🔴 **真机实测**（iOS Safari / Android Chrome）
- [ ] 🟡 **无障碍复核**（键盘 / 读屏 / 对比度）
- [x] 🟡 **`og:url` / `canonical` / `twitter:*`**
- [x] 🟡 **`sitemap.xml` 与 `robots.txt`**
- [x] 🟡 **CI**：`.github/workflows/ci.yml`（build + check + verify）
- [ ] 🟢 **`src/verify.mjs` 语言截图对比**
- [ ] 🟢 **部署时排除 `src/`**（可选）
- [x] 🟢 **`CHANGELOG.md`**

---

## F. 已知问题

| 位置 | 现象 | 影响 | 处理建议 |
| --- | --- | --- | --- |
| `assets/img/scene-*.png` | 预览分辨率约 0.45× | 放大偏糊 | 换真图或 `python3 src/art.py` |
| `dist/` | 构建产物（gitignore） | 直接改会被覆盖 | 改 `src/pages/` / `assets/` 后跑 `build.py` |
| `SITE_ORIGIN` | 默认 `welcome-to-shenzhen.pages.dev` | canonical/og 域名 | 部署时设环境变量 |
| 全体数字 | 整理值，非官方实时 | 可能过期 | 按 B 节复核 |

---

## G. 本轮已完成（2026-10-13）

- ✅ **英文主站**：默认 `data-lang="en"`、EN 标题/描述、导航与页脚 EN 优先
- ✅ 社交元信息、sitemap、robots、og 1200×630
- ✅ SVG 图标；启用 `scene-tech` / `cover-card`
- ✅ 代表专用内容 + 退税打印清单 + APEC 命名说明
- ✅ 打印样式、滚动高亮、CI、CHANGELOG
- ✅ 既有：13 页双语、设计系统、构建/校验链路、程序化插画
