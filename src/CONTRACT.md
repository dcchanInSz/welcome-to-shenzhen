# Design & content contract — Welcome to Shenzhen (APEC 2026)

Read this fully before writing any page fragment. It is the shared contract that
keeps every page consistent.

## 1. What we are building

A **static, bilingual (English primary / 中文), dependency-free** city guide website
for **Shenzhen as the host city of APEC 2026**. English is the default site language
and meta surface; Chinese remains a full peer translation. Every page must serve two
audiences at once: the APEC 2026 delegate / business traveller, and the general visitor.

Edit `src/pages/` and `assets/`. Run `python3 src/build.py` to emit the deployable
site into **`dist/`** — never hand-edit files under `dist/`.

Verified, non-negotiable core facts:

| Fact | Value |
| --- | --- |
| Event | 33rd APEC Economic Leaders' Meeting (亚太经合组织第三十三次领导人非正式会议) |
| Dates | **2026-11-18 → 2026-11-19** (leaders' meeting week) |
| APEC CEO Summit | **2026-11-17 → 2026-11-18**, organised by CCPIT (中国贸促会) |
| City | Shenzhen, Guangdong, People's Republic of China |
| Theme | "Building an Asia-Pacific Community to Prosper Together"（构建亚太共同体，促进共同繁荣） |
| CEO Summit theme | "promoting prosperity together for a win-win future" |
| Context | China's 3rd time hosting APEC, 1st time in 12 years; ~300 APEC "China Year" events in multiple Chinese cities; Shenzhen is the host city of the leaders' meeting |
| Other APEC 2026 host cities | Beijing, Shanghai, Guangzhou, Dalian, Nanjing, Suzhou, Hangzhou, Chengdu, plus Hong Kong SAR and Macao SAR |
| APEC membership | 21 member economies |

Anything beyond this must be researched. **Verify with a web search before you
assert a number, price, address or date.** When something is genuinely uncertain
or changes often (fares, opening hours, ticketing rules), write it with an
explicit hedge and put it in a `.note-src` block — never invent precision.

## 2. Language: the hard requirement

There is **one HTML file per page**, containing **both languages**. A language
switch in the header toggles `data-lang` on `<html>`; CSS then shows/hides:

```html
<p class="lang-zh">中文文案</p>
<p class="lang-en">English copy</p>
```

Rules:

1. Every piece of human-readable text gets a pair: `<span class="lang-en">` /
   `<span class="lang-zh">` for inline, or block elements with those classes.
2. Inside a heading: `<h2><span class="lang-en">Heading</span><span class="lang-zh">标题</span></h2>`
   (existing pages may still list `lang-zh` before `lang-en`; both are fine as long
   as pairs stay balanced — CSS, not source order, controls visibility).
3. **Both languages carry the same information, the same component order and the
   same links.** English is the default voice visitors see first — natural, warm,
   concrete. Chinese is a full peer, not a stub.
4. Prefer `lang-en` first, `lang-zh` second in new chrome and meta; page bodies may
   keep either order.
5. Tables: put a complete `<table>` inside `.lang-zh` and a complete `<table>`
   inside `.lang-en` (same columns, same rows). Do **not** put lang spans inside
   `<td>`.
6. The shell sets `<html lang="en" data-lang="en">` by default. Do not invent
   per-language URLs.

## 3. Page fragment format

Create exactly one file per page at `src/pages/<slug>.html`:

```html
<!--meta
title: English page title (short; builder appends "· Shenzhen")
desc: One English sentence for meta description (about 120–200 characters).
keywords: English,keywords,深圳,optional-chinese
nav: attractions.html
-->
<section class="page-hero">
  <div class="wrap">
    <p class="crumbs"><a href="index.html"><span class="lang-en">Home</span><span class="lang-zh">首页</span></a><span>›</span><span class="lang-en">Attractions</span><span class="lang-zh">景点</span></p>
    <h1><span class="lang-en">Title</span><span class="lang-zh">标题</span></h1>
    <p class="lede" style="max-width:70ch"><span class="lang-en">Intro…</span><span class="lang-zh">导语…</span></p>
    <div class="chip-row" style="margin-top:1rem">
      <span class="chip chip--ghost"><span class="lang-en">Tag</span><span class="lang-zh">标签</span></span>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">…</div>
</section>
```

Then the rest of the page, alternating:

```html
<div class="lang-zh"> … the whole Chinese page body … </div>
<div class="lang-en"> … the whole English page body … </div>
```

for long pages, **or** interleaved per section (`<section>` twice, once per
language) for medium pages. Pick one approach per file and be consistent.
Both language bodies must be inside `<main>`-level sections — never nest one
language block inside the other.

`nav:` must be the exact filename of the page (this is how the builder marks the
active nav item), e.g. `food.html`. If you don't know it, use the page filename.

## 4. Classes available (use these, don't invent new global names)

Layout: `.wrap` · `.section` · `.section--tight` · `.section--alt` (white band)
`.section--ink` (dark band) · `.grid .grid--2|--3|--4` · `.grid--sidebar`
`.stack` · `.center` · `.mt-1 .mt-2 .mt-3 .mb-1 .mb-2 .mb-3`

Text: `.display` · `.lede` · `.muted` · `.small` · `.tiny` · `.mono`
`.eyebrow` · `.grad-text` · `.section-head` · `.tag`

Header: `.page-hero` · `.crumbs`

Blocks: `.card` `.card--pad-lg` `.card--hover` `.card--flat` `.card--ink`
`.card--accent` `.card-icon` `.card-link` · `.badge`
`.callout` `.callout--warn` `.callout--coral` + `.callout-title`
`.kv` (list of `<li><span class="k">…</span><span class="v">…</span></li>`)
`.table-wrap` + `<table>` · `.stat` + `.stat-row` · `.chip-row` + `.chip`
`.chip--coral .chip--gold .chip--ghost .chip--muted`
`.steps` (numbered `<ol>` — let the CSS do the numbering) · `.timeline`
`.ticks` `.ticks--check` · `.media` `.media--tall` · `.tile`
`.faq` (`<details><summary>…</summary><div class="faq-body">…</div></details>`)
`.note-src` · `.btn-row` + `.btn .btn--primary|--coral|--ghost|--line|--sm`
`.reveal` (opt-in scroll animation — add to major cards/sections, sparingly)

`<style>` inside the fragment is allowed **only** if prefixed by the page's own
root id, e.g.

```html
<section class="section" id="page-food">…</section>
<style>#page-food .spice { color: var(--coral); }</style>
```

## 5. Hard prohibitions

- **No external resources.** No Google Fonts, no CDN, no `<img src="http…">`,
  no iframes, no maps embeds, no third-party JS. The site must work fully offline
  from the file system. Do not add `<script>`.
- **No external links** (`<a href="http…">`). Mention official sources by name
  in text (深圳市政府门户 sz.gov.cn、APEC 2026 中国年官网 apec2026.cn、深圳地铁
  szmc.net、12306、i深圳 App、深圳机场 szairport.com、微信/支付宝 etc.).
  Internal page links only.
- **Images:** only these local files exist. Reference them only if useful, with
  real `<img src="assets/img/…" alt="…" loading="lazy" width= height=>`:
  `assets/img/hero-cover.png`, `assets/img/og-cover.png`,
  `assets/img/scene-bay.png`, `assets/img/scene-metro.png`,
  `assets/img/scene-tech.png`, `assets/img/scene-night.png`,
  `assets/img/scene-coast.png`, `assets/img/scene-oldtown.png`,
  `assets/img/metro-system-map.jpg` (Shenzhen Metro system map; attribute source).
- No `target="_blank"`, no `onclick=`, no inline `style` used to fake a design
  system (small spacing tweaks like `style="margin-top:1rem"` or
  `style="max-width:70ch"` are fine).
- No lorem ipsum, no "TODO", no placeholder text in the delivered page. If you
  don't know something, describe how the reader finds out, or omit it.

## 6. Internal link map (flat site, all files at root)

`index.html` · `apec-2026.html` · `city.html` · `attractions.html` · `food.html`
`stay.html` · `transport.html` · `shopping.html` · `itineraries.html`
`business.html` · `services.html` · `faq.html` · `about.html`

Cross-link generously: a food page should link to `attractions.html` and
`transport.html`; a business page to `stay.html`, `transport.html`, `faq.html`;
every page ends with a related-links band.

## 7. Quality bar for every page

1. **Depth over decoration.** Real, specific, checkable content: named
   neighbourhoods, what a dish tastes like, how a metro transfer works, what
   time to leave for the airport, what to wear in November in Shenzhen.
2. **Practical blocks.** At least one `.table-wrap`/`.kv` comparison, one
   `.callout` with a genuinely useful tip, one `.faq` or `.steps` block.
3. **November/APEC lens.** Shenzhen in mid-November: ~20–27 °C, mild and dry,
   light layers + a jacket for air conditioning, occasional shower. Traffic and
   hotel demand around the meeting are higher than usual — advise realistic
   buffers, advance booking, and ID/passport habits (real-name ticket rules).
4. **A11y & semantics.** One `<h1>` per page (in the page hero), sequential
   `<h2>`/`<h3>`, real `<table>` with `<thead>`, `alt` on every image, no empty
   links, no colour-only meaning.
5. **Voice.** Warm, confident, concrete, lightly opinionated ("if you only have
   one evening, do this"). No marketing fluff, no exaggerated superlatives that
   you cannot support.

## 8. Self-check before you finish

- Both language versions present for every text node? (grep your own file for
  `<h2>` and `<td>` to confirm.)
- `<!--meta … -->` header present with title/desc/keywords/nav?
- Zero `http` occurrences except in plain-text mentions of domain names? (a
  domain like `sz.gov.cn` written as text is fine; `href="https://…"` is not)
- No `<script>`, no external `<img>`, no invented CSS class names?
- File written to `src/pages/<slug>.html`?

When you are done, reply with: the file path you wrote, a ≤12-line outline of
its sections, and any fact you deliberately hedged or could not verify.
