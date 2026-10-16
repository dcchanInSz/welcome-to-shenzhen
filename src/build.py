#!/usr/bin/env python3
"""Static site builder for the Shenzhen / APEC 2026 bilingual guide.

Writes finished HTML + assets + generated sitemap/robots into dist/.
English is the primary site surface for meta and JSON-LD.
"""
from __future__ import annotations

import datetime as _dt
import html as _html
import json
import os
import pathlib
import re
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGES = ROOT / "src" / "pages"
BASE = ROOT / "src" / "partials" / "base.html"
ASSETS = ROOT / "assets"
DIST = ROOT / "dist"

SITE_ORIGIN = os.environ.get(
    "SITE_ORIGIN", "https://langcode.app/shenzhen"
).rstrip("/")

META_RE = re.compile(r"<!--meta\s*(?P<body>.*?)-->", re.S)
KV_RE = re.compile(r"^\s*([a-zA-Z_]+)\s*:\s*(.*?)\s*$")
# Display labels for BreadcrumbList (English, matches default site language).
PAGE_LABELS = {
    "index.html": "Home",
    "apec-2026.html": "APEC 2026",
    "city.html": "The City",
    "attractions.html": "Attractions",
    "food.html": "Eat",
    "stay.html": "Stay",
    "transport.html": "Getting Around",
    "shopping.html": "Shopping",
    "itineraries.html": "Itineraries",
    "business.html": "Business",
    "services.html": "Services",
    "faq.html": "FAQ",
    "about.html": "About",
}

SITEMAP_PRIORITY = {
    "index.html": ("1.0", "weekly"),
    "apec-2026.html": ("0.9", "weekly"),
    "city.html": ("0.8", "monthly"),
    "attractions.html": ("0.8", "monthly"),
    "transport.html": ("0.8", "monthly"),
    "itineraries.html": ("0.8", "monthly"),
    "services.html": ("0.8", "monthly"),
    "food.html": ("0.7", "monthly"),
    "stay.html": ("0.7", "monthly"),
    "shopping.html": ("0.7", "monthly"),
    "business.html": ("0.7", "monthly"),
    "faq.html": ("0.7", "monthly"),
    "about.html": ("0.4", "yearly"),
}

# High-value English FAQ pairs for FAQPage JSON-LD (kept short for payload size).
FAQ_JSONLD = [
    (
        "Do I need a Chinese visa?",
        "Visa categories and transit-without-visa schemes change. Check the latest notice from your nearest Chinese embassy or consulate and the National Immigration Administration (12367) before you travel.",
    ),
    (
        "What is November weather like, and what should I pack?",
        "November in Shenzhen is typically mild and relatively dry, about 20–27 °C. Light layers plus a jacket for air-conditioned indoors work well for meetings.",
    ),
    (
        "How do I get from Bao'an Airport to the city?",
        "Metro Line 11 (Airport Line) from the GTC is usually the fastest affordable option into Futian and Nanshan. Taxis and ride-hailing are available; allow extra time at peak and during meeting week.",
    ),
    (
        "Coming from Hong Kong, which border crossing should I use?",
        "Futian and Luohu are common for metro connections; Shenzhen Bay suits Nanshan; Huanggang offers 24-hour passenger clearance. Choose by destination district and opening hours.",
    ),
    (
        "How does the metro work, and how much does it cost?",
        "Fares are distance-based from about RMB 2. Use a Shenzhen Tong card, phone QR code, or a single-journey ticket. Stations have security screening — budget queue time at peak.",
    ),
    (
        "Which district should I stay in?",
        "Futian for meetings and CBD access, Nanshan for tech and the bay, Luohu for Hong Kong crossings, Shekou for a coastal base. In Shenzhen the district usually matters more than the hotel brand.",
    ),
    (
        "Will roads be closed during the meeting week (17–19 November)?",
        "Temporary controls are common around Futian and Xiangmihu. Prefer the metro, allow buffer time, and follow announcements on sz.gov.cn and apec2026.cn.",
    ),
    (
        "Where is the venue? Can I visit it?",
        "APEC-related facilities are concentrated in Futian District around Xiangmihu. Specific venues are subject to the official final announcement; leaders' meetings are closed to the public.",
    ),
    (
        "What should I wear to the CEO Summit or formal meetings?",
        "Business formal is the safe default: dark suit and leather shoes, or a tailored suit or dress. Bring a light jacket for air-conditioned rooms.",
    ),
    (
        "I have lost my passport. What now?",
        "Contact your embassy or consulate for an emergency travel document, report the loss to the police (110) if required, and keep digital copies of your documents to speed replacement.",
    ),
]


def parse_meta(text: str) -> tuple[dict[str, str], str]:
    m = META_RE.search(text)
    if not m:
        raise SystemExit("missing <!--meta ... --> header")
    meta: dict[str, str] = {}
    for line in m.group("body").splitlines():
        line = line.strip()
        if not line:
            continue
        kv = KV_RE.match(line)
        if kv:
            meta[kv.group(1).lower()] = kv.group(2)
    return meta, text[m.end():].lstrip("\n")


def title_full(title: str) -> str:
    """Append site suffix without doubling 'Shenzhen'."""
    t = title.strip()
    if re.search(r"\bShenzhen\b", t, re.I):
        return t
    return f"{t} · Shenzhen"


def page_url(name: str) -> str:
    if name == "index.html":
        return f"{SITE_ORIGIN}/"
    return f"{SITE_ORIGIN}/{name}"


def json_ld_script(data: list[dict] | dict) -> str:
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return (
        '<script type="application/ld+json">\n'
        f"{payload}\n"
        "</script>"
    )


def website_org_graph() -> list[dict]:
    return [
        {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "name": "Welcome to Shenzhen · APEC 2026",
            "url": f"{SITE_ORIGIN}/",
            "inLanguage": ["en", "zh-Hans"],
            "description": (
                "A bilingual city guide for Shenzhen as host city of APEC 2026 — "
                "food, stay, transport, attractions, business and practical services."
            ),
            "publisher": {"@id": f"{SITE_ORIGIN}/#organization"},
        },
        {
            "@context": "https://schema.org",
            "@type": "Organization",
            "@id": f"{SITE_ORIGIN}/#organization",
            "name": "Welcome to Shenzhen",
            "url": f"{SITE_ORIGIN}/",
            "parentOrganization": {
                "@type": "Organization",
                "name": "Langcode",
                "url": "https://langcode.app/",
            },
        },
    ]


def breadcrumb_ld(name: str) -> dict | None:
    if name == "index.html":
        return None
    items = [
        {
            "@type": "ListItem",
            "position": 1,
            "name": "Home",
            "item": f"{SITE_ORIGIN}/",
        },
        {
            "@type": "ListItem",
            "position": 2,
            "name": PAGE_LABELS.get(name, name.replace(".html", "")),
            "item": page_url(name),
        },
    ]
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": items,
    }


def event_ld() -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "Event",
        "name": "33rd APEC Economic Leaders' Meeting",
        "description": (
            "The 33rd APEC Economic Leaders' Meeting takes place in Shenzhen, China, "
            "on 18–19 November 2026, with the APEC CEO Summit on 17–18 November."
        ),
        "startDate": "2026-11-18",
        "endDate": "2026-11-19",
        "eventStatus": "https://schema.org/EventScheduled",
        "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
        "location": {
            "@type": "Place",
            "name": "Shenzhen, Guangdong, China",
            "address": {
                "@type": "PostalAddress",
                "addressLocality": "Shenzhen",
                "addressRegion": "Guangdong",
                "addressCountry": "CN",
            },
        },
        "organizer": {
            "@type": "Organization",
            "name": "APEC China 2026",
            "url": "https://langcode.app/shenzhen/apec-2026.html",
        },
        "url": f"{SITE_ORIGIN}/apec-2026.html",
        "inLanguage": "en",
    }


def faq_ld() -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {"@type": "Answer", "text": a},
            }
            for q, a in FAQ_JSONLD
        ],
    }


def build_json_ld(name: str) -> str:
    blocks: list[dict] = list(website_org_graph())
    crumb = breadcrumb_ld(name)
    if crumb:
        blocks.append(crumb)
    if name == "faq.html":
        blocks.append(faq_ld())
    if name == "apec-2026.html":
        blocks.append(event_ld())
    return json_ld_script(blocks)


def write_sitemap(page_names: list[str], today: str) -> None:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    # Home first, then the rest alphabetically but keep index out of loop order
    ordered = ["index.html"] + [n for n in page_names if n != "index.html"]
    for name in ordered:
        pri, freq = SITEMAP_PRIORITY.get(name, ("0.5", "monthly"))
        loc = _html.escape(page_url(name), quote=True)
        lines.append("  <url>")
        lines.append(f"    <loc>{loc}</loc>")
        lines.append(f"    <lastmod>{today}</lastmod>")
        lines.append(f"    <changefreq>{freq}</changefreq>")
        lines.append(f"    <priority>{pri}</priority>")
        lines.append("  </url>")
    lines.append("</urlset>")
    lines.append("")
    (DIST / "sitemap.xml").write_text("\n".join(lines), encoding="utf-8")


def write_robots() -> None:
    text = (
        "User-agent: *\n"
        "Allow: /\n"
        "\n"
        f"Sitemap: {SITE_ORIGIN}/sitemap.xml\n"
    )
    (DIST / "robots.txt").write_text(text, encoding="utf-8")


def clean_dist() -> None:
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)


def copy_assets() -> None:
    if not ASSETS.is_dir():
        raise SystemExit(f"missing assets directory: {ASSETS}")
    shutil.copytree(ASSETS, DIST / "assets")


def build() -> int:
    clean_dist()
    copy_assets()

    base = BASE.read_text(encoding="utf-8")
    year = _dt.date.today().year
    today = _dt.date.today().isoformat()
    pages = sorted(p for p in PAGES.glob("*.html"))
    if not pages:
        raise SystemExit("no page fragments found in src/pages")

    built: list[str] = []
    for src in pages:
        meta, body = parse_meta(src.read_text(encoding="utf-8"))
        title = meta.get("title") or src.stem
        desc = meta.get("desc", "")
        keywords = meta.get(
            "keywords",
            "Shenzhen,APEC 2026,Shenzhen travel guide,深圳,深圳旅游",
        )
        full_title = title_full(title)
        canonical = page_url(src.name)
        og_image = f"{SITE_ORIGIN}/assets/img/og-cover.png"
        json_ld = build_json_ld(src.name)
        html = (
            base.replace("@@TITLE@@", title)
            .replace("@@TITLE_FULL@@", full_title)
            .replace("@@DESC@@", desc)
            .replace("@@KEYWORDS@@", keywords)
            .replace("@@CANONICAL@@", canonical)
            .replace("@@OG_IMAGE@@", og_image)
            .replace("@@JSON_LD@@", json_ld)
            .replace("@@BODY@@", body.rstrip() + "\n")
            .replace('id="yr">2026', f'id="yr">{year}')
        )
        nav_name = meta.get("nav", src.name)
        if nav_name:
            html = html.replace(
                f'<li><a href="{nav_name}">',
                f'<li><a href="{nav_name}" aria-current="page">',
            )
        (DIST / src.name).write_text(html, encoding="utf-8")
        built.append(src.name)

    write_sitemap(built, today)
    write_robots()

    print(f"built {len(built)} page(s) → {DIST}/")
    print(f"  pages: " + ", ".join(built))
    print(f"  canonical origin: {SITE_ORIGIN}")
    print(f"  wrote sitemap.xml + robots.txt")
    print(f"serve:  python3 -m http.server 8000 --directory dist")
    return 0


if __name__ == "__main__":
    sys.exit(build())
