# Changelog

All notable fact and site updates for Welcome to Shenzhen · APEC 2026.

## 2026-10-13

- Replaced procedural placeholders with AI landmark illustrations (Shenzhen Bay, CBD night, Dapeng coast, Nantou, tech campus, metro, hero, OG).
- Build output moved to **`dist/`**; root HTML removed. Serve with `python3 src/serve.py` or `python3 -m http.server 8000 --directory dist`.
- English is now the primary site surface (default `data-lang="en"`, English titles/meta, EN-first chrome).
- Added `canonical`, `og:url`, Twitter card meta; `sitemap.xml` and `robots.txt`.
- Regenerated `og-cover.png` at 1200×630.
- Replaced emoji / symbol card icons with inline SVG.
- Wired previously unused `scene-tech.png` (business) and `cover-card.png` (city).
- Added delegate registration / screening notes and a meeting-week updates placeholder on `apec-2026.html`.
- Added a printable departure tax-refund checklist on `shopping.html`.
- Softened venue wording to “subject to official notice”; clarified APEC naming is descriptive only.
- Added GitHub Actions CI (`build` + `check` + Chrome verify).
- Information cut-off remains **October 2026** — confirm schedules, fares and policies with official sources before travel.
