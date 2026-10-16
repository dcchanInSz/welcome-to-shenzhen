#!/usr/bin/env python3
"""Validate the built site in dist/: links, assets, structure, bilingual coverage.

Run from the project root:   python3 src/check.py
Exits non-zero when a blocking problem is found.
"""
from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
PAGES = sorted(DIST.glob("*.html"))
problems: list[str] = []
warnings: list[str] = []


def check_page(p: pathlib.Path) -> None:
    s = p.read_text(encoding="utf-8")
    name = p.name

    # structure
    if s.count("<h1") != 1:
        problems.append(f"{name}: expected exactly one <h1>, found {s.count('<h1')}")
    for tag in ("html", "head", "body", "main", "header", "footer"):
        # negative lookahead so <head> is not counted inside <header>
        o = len(re.findall(rf"<{tag}(?![\w-])", s))
        c = len(re.findall(rf"</{tag}>", s))
        if o != c:
            problems.append(f"{name}: unbalanced <{tag}> ({o} open / {c} close)")
    for tag in ("div", "section", "table", "details", "ul", "ol", "li", "tr", "td", "p", "span"):
        o = len(re.findall(rf"<{tag}[\s>]", s))
        c = len(re.findall(rf"</{tag}>", s))
        if o != c:
            problems.append(f"{name}: unbalanced <{tag}> ({o} open / {c} close)")

    # required shell pieces
    for needle in ('class="site-header"', 'class="site-footer"', 'assets/style.css',
                   'assets/site.js', 'lang-switch', 'data-setlang="en"', 'id="main"'):
        if needle not in s:
            problems.append(f"{name}: missing {needle}")

    # language coverage
    zh, en = s.count('class="lang-zh"'), s.count('class="lang-en"')
    if zh != en:
        problems.append(f"{name}: lang-zh={zh} != lang-en={en}")
    if zh < 4:
        warnings.append(f"{name}: only {zh} bilingual pairs")

    # external references (allow absolute canonical / social meta only)
    for m in re.finditer(r'(?:href|src)="((?:https?:)?//[^"]*)"', s):
        # <link rel="canonical" href="https://…"> is intentional for SEO.
        before = s[max(0, m.start() - 80):m.start()]
        if 'rel="canonical"' in before or "rel='canonical'" in before:
            continue
        problems.append(f"{name}: external resource {m.group(0)[:70]}")
    if "<script" in s and s.count("<script") != 1:
        problems.append(f"{name}: unexpected extra <script> tags")

    # internal links resolve (relative .html only)
    for m in re.finditer(r'href="([^"#?]+\.html)(#[^"]*)?"', s):
        href = m.group(1)
        if href.startswith("http://") or href.startswith("https://") or href.startswith("//"):
            continue
        target = DIST / href
        if not target.exists():
            problems.append(f"{name}: broken link -> {href}")
    # asset references resolve inside dist/
    for m in re.finditer(r'(?:src|href)="(assets/[^"]+)"', s):
        if not (DIST / m.group(1)).exists():
            problems.append(f"{name}: missing asset {m.group(1)}")
    # in-page anchors resolve
    ids = set(re.findall(r'id="([^"]+)"', s))
    for m in re.finditer(r'href="#([^"]+)"', s):
        if m.group(1) not in ids:
            warnings.append(f"{name}: anchor #{m.group(1)} has no target on the page")

    # meta
    if "<title>" not in s or s.count("<title>") != 1:
        problems.append(f"{name}: bad <title>")
    md = re.search(r'<meta name="description" content="([^"]*)"', s)
    if not md or len(md.group(1)) < 30:
        problems.append(f"{name}: missing or too-short meta description")
    if 'rel="icon"' not in s:
        warnings.append(f"{name}: no favicon link")

    # alt text
    for m in re.finditer(r"<img\b[^>]*>", s):
        if "alt=" not in m.group(0):
            problems.append(f"{name}: <img> without alt")

    # active nav
    if 'aria-current="page"' not in s:
        warnings.append(f"{name}: nav item not marked aria-current")


def check_assets() -> None:
    img = DIST / "assets" / "img"
    if not img.is_dir():
        problems.append("dist/assets/img missing — run src/build.py")
        return
    for p in sorted(img.glob("*.png")):
        if p.stat().st_size < 4096:
            warnings.append(f"asset suspiciously small: {p.name}")


def cross_reference() -> None:
    """Every page should be reachable from the navigation."""
    index = DIST / "index.html"
    if not index.exists():
        problems.append("dist/index.html missing")
        return
    base = index.read_text(encoding="utf-8")
    for p in PAGES:
        if p.name == "index.html":
            continue
        if f'href="{p.name}"' not in base:
            warnings.append(f"{p.name}: not linked from the global navigation")


def main() -> int:
    if not DIST.is_dir() or not PAGES:
        print("no built pages found — run src/build.py first (output → dist/)")
        return 1
    for p in PAGES:
        check_page(p)
    check_assets()
    cross_reference()

    print(f"checked {len(PAGES)} page(s) in dist/")
    for w in warnings:
        print(f"  warning: {w}")
    if problems:
        print(f"\n{len(problems)} problem(s):")
        for pr in problems:
            print(f"  ERROR: {pr}")
        return 1
    print("no blocking problems found")
    return 0


if __name__ == "__main__":
    sys.exit(main())
