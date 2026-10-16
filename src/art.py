#!/usr/bin/env python3
"""Generate the original cover artwork for the Shenzhen / APEC 2026 site.

Everything here is procedurally drawn with numpy + Pillow, so the repository
ships zero third-party imagery and the site works completely offline.

Run from the project root:   python3 src/art.py
Output:                      assets/img/*.png
"""
from __future__ import annotations

import os
import pathlib

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "img"
OUT.mkdir(parents=True, exist_ok=True)

SS = 2      # supersampling factor for all vector drawing
SCALE = float(os.environ.get("ART_SCALE", "1.0"))  # render scale for fast iteration


def px(v):
    """Scale a design-unit pixel value to the render size."""
    return max(1, int(round(v * SCALE)))


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def lerp(a, b, t):
    return a + (b - a) * t


def vgrad(h, w, stops, span=None):
    """Vertical gradient. stops = [(pos0..1, (r,g,b)), ...].

    span=(y0, y1) confines the gradient to that pixel range (0..1 by default).
    """
    ys = np.linspace(0.0, 1.0, h)
    if span is not None:
        y0, y1 = span
        ys = (ys - y0) / max(y1 - y0, 1e-6)
        ys = np.clip(ys, 0.0, 1.0)
    cols = np.zeros((h, 3), dtype=np.float64)
    for i in range(len(stops) - 1):
        p0, c0 = stops[i]
        p1, c1 = stops[i + 1]
        m = (ys >= p0) & (ys <= p1)
        if not m.any():
            continue
        t = (ys[m] - p0) / max(p1 - p0, 1e-6)
        for ch in range(3):
            cols[m, ch] = lerp(c0[ch], c1[ch], t)
    return np.repeat(cols[:, None, :], w, axis=1)


def radial_glow(h, w, cx, cy, radius, colour, strength=1.0, falloff=2.0):
    """Additive light. Returns a layer meant to be *added*, not composited."""
    yy, xx = np.mgrid[0:h, 0:w]
    d = np.sqrt(((xx - cx) / radius) ** 2 + ((yy - cy) / radius) ** 2)
    a = np.clip(1.0 - d, 0.0, 1.0) ** falloff * strength
    layer = np.zeros((h, w, 3), dtype=np.float64)
    for ch in range(3):
        layer[:, :, ch] = colour[ch] * a
    return layer * 0.55


def over(base, layer, alpha):
    """alpha: HxW float 0..1 compositing layer over base."""
    a = alpha[:, :, None]
    return base * (1 - a) + layer * a


def draw_mask(h, w, fn):
    """Rasterise vector shapes into an anti-aliased float mask via Pillow."""
    img = Image.new("L", (w * SS, h * SS), 0)
    fn(ImageDraw.Draw(img), SS)
    img = img.resize((w, h), Image.LANCZOS)
    return np.asarray(img, dtype=np.float64) / 255.0


def draw_rgba(h, w, fn):
    """Rasterise vector shapes into an RGBA numpy layer (premultiplied not needed)."""
    img = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    fn(ImageDraw.Draw(img), SS)
    img = img.resize((w, h), Image.LANCZOS)
    arr = np.asarray(img, dtype=np.float64) / 255.0
    return arr[:, :, :3], arr[:, :, 3]


def grain(shape, rng, amount):
    return rng.normal(0.0, amount, shape)


def vignette(h, w, strength=0.35, power=1.6):
    yy, xx = np.mgrid[0:h, 0:w]
    nx = (xx / w - 0.5) * 2
    ny = (yy / h - 0.5) * 2
    d = np.sqrt(nx ** 2 + ny ** 2) / np.sqrt(2)
    v = 1.0 - strength * (d ** power)
    return v[:, :, None]


def haze_band(h, w, y0, y1, colour, top=0.0, bottom=0.6):
    ys = np.arange(h)
    a = np.zeros(h)
    inside = (ys >= y0) & (ys <= y1)
    t = (ys[inside] - y0) / max(y1 - y0, 1e-6)
    a[inside] = lerp(top, bottom, t)
    layer = np.zeros((h, w, 3))
    for ch in range(3):
        layer[:, :, ch] = colour[ch]
    return layer, np.repeat(a[:, None], w, axis=1)


def to_image(arr, h, w):
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")


# --------------------------------------------------------------------------- #
# skyline primitives
# --------------------------------------------------------------------------- #
def skyline(h, w, rng, base_y, min_h, max_h, colour, lit_ratio=0.5,
            window_colours=((255, 214, 150), (255, 236, 190), (190, 230, 255)),
            spire_chance=0.12, density=1.0):
    """Return (colour_layer, alpha_mask) for one row of buildings."""
    shapes = []
    x = -int(w * 0.04)
    while x < w * 1.04:
        bw = int(rng.integers(int(w * 0.018 / density), int(w * 0.062 / density)))
        bh = int(rng.integers(min_h, max_h))
        shapes.append((x, base_y - bh, x + bw, base_y + 4, bh, rng.random() < spire_chance))
        x += bw + int(rng.integers(2, max(4, int(w * 0.012))))

    col = np.zeros((h, w, 3), dtype=np.float64)
    for ch in range(3):
        col[:, :, ch] = colour[ch]
    alpha = np.zeros((h, w), dtype=np.float64)
    win_col = np.zeros((h, w, 3), dtype=np.float64)
    win_a = np.zeros((h, w), dtype=np.float64)

    for (x0, y0, x1, y1, bh, spire) in shapes:
        m = draw_mask(h, w, lambda d, s, x0=x0, y0=y0, x1=x1, y1=y1:
                      d.rectangle([x0 * s, y0 * s, x1 * s, y1 * s], fill=255))
        alpha = np.maximum(alpha, m)

        if spire:
            ww = max(2, int((x1 - x0) * 0.09))
            cx = (x0 + x1) // 2
            sm = draw_mask(h, w, lambda d, s, cx=cx, y0=y0, ww=ww:
                           d.rectangle([(cx - ww // 2) * s, (y0 - int(h * 0.05)) * s,
                                        (cx + ww // 2) * s, y0 * s], fill=255))
            alpha = np.maximum(alpha, sm)

        # windows
        gw = max(4, int(w * 0.0055))
        gh = max(4, int(h * 0.011))
        step_x = gw * 2
        step_y = gh * 2
        for wy in range(y0 + gh, y1 - gh, step_y):
            for wx in range(x0 + gw, x1 - gw, step_x):
                if rng.random() > lit_ratio:
                    continue
                c = window_colours[int(rng.integers(0, len(window_colours)))]
                jitter = rng.uniform(0.45, 1.0)
                box = [wx, wy, wx + gw, wy + gh]
                mm = draw_mask(h, w, lambda d, s, box=box: d.rectangle(
                    [box[0] * s, box[1] * s, box[2] * s, box[3] * s], fill=255))
                for ch in range(3):
                    win_col[:, :, ch] = np.where(mm > 0, np.maximum(
                        win_col[:, :, ch], c[ch] * jitter), win_col[:, :, ch])
                win_a = np.maximum(win_a, mm)

    col = over(col, win_col, win_a * (win_a > 0))
    return col, alpha


def landmark_tower_pingan(h, w, rng, x, base_y, height, colour):
    """Ping An Finance Centre: tapering shaft + spire."""
    top = base_y - height
    def fn(d, s):
        # shaft as a stack of narrowing slices
        n = 26
        for i in range(n):
            t = i / (n - 1)
            y0 = lerp(top, base_y, t)
            y1 = lerp(top, base_y, (i + 1) / (n - 1)) + 2
            half = lerp(w * 0.0055, w * 0.019, t ** 1.7)
            d.polygon([((x - half) * s, y0 * s), ((x + half) * s, y0 * s),
                       ((x + half) * s, y1 * s), ((x - half) * s, y1 * s)], fill=255)
        d.line([(x * s, (top - height * 0.14) * s), (x * s, top * s)], fill=255,
               width=max(2, int(w * 0.0016 * s)))
    m = draw_mask(h, w, fn)
    col = np.zeros((h, w, 3))
    for ch in range(3):
        col[:, :, ch] = colour[ch]
    # cool crown lighting
    col = over(col, np.dstack([np.full((h, w), 150.0), np.full((h, w), 215.0),
                               np.full((h, w), 255.0)]),
               draw_mask(h, w, lambda d, s: d.rectangle(
                   [x * s - w * 0.02 * s, (top - 4) * s, x * s + w * 0.02 * s,
                    (top + height * 0.05) * s], fill=90)))
    return col, m


def spring_tower(h, w, rng, x, base_y, height, colour, crown=(120, 245, 225)):
    """China Resources 'Spring Bamboo' — a bundle of tapering tubes."""
    top = base_y - height
    tubes = 8
    m = np.zeros((h, w))
    col = np.zeros((h, w, 3))
    for ch in range(3):
        col[:, :, ch] = colour[ch]
    for i in range(tubes):
        t0 = i / tubes
        t1 = (i + 1) / tubes
        x0 = x - w * 0.022 + t0 * w * 0.044
        x1 = x - w * 0.022 + t1 * w * 0.044
        top_i = top + height * (0.10 * abs(t0 - 0.5) * 2) + height * 0.06 * (i % 3)
        mm = draw_mask(h, w, lambda d, s, x0=x0, x1=x1, top_i=top_i:
                       d.rectangle([x0 * s, top_i * s, x1 * s, (base_y + 4) * s],
                                   fill=255, outline=0))
        m = np.maximum(m, mm)
    # diagrid glow
    def diag(d, s):
        for i in range(9):
            yy = top + height * (0.14 + i * 0.1)
            d.line([((x - w * 0.024) * s, yy * s), ((x + w * 0.024) * s, (yy + height * 0.03) * s)],
                   fill=70, width=max(1, int(w * 0.0011 * s)))
    gm = draw_mask(h, w, diag)
    crown_layer = np.dstack([np.full((h, w), float(crown[0])),
                             np.full((h, w), float(crown[1])),
                             np.full((h, w), float(crown[2]))])
    col = over(col, crown_layer, gm * 0.85)
    return col, m


def bay_bridge(h, w, rng, y, x0, x1, deck_col=(228, 238, 246), cable_col=(210, 226, 240)):
    """Shenzhen Bay Bridge: deck, two towers, stay cables."""
    def fn(d, s):
        y0 = y
        d.rectangle([x0 * s, (y0 - h * 0.006) * s, x1 * s, (y0 + h * 0.006) * s], fill=255)
        for tx in (x0 + (x1 - x0) * 0.30, x0 + (x1 - x0) * 0.70):
            d.rectangle([(tx - w * 0.0022) * s, (y0 - h * 0.075) * s,
                         (tx + w * 0.0022) * s, (y0 + h * 0.01) * s], fill=255)
            n = 12
            for i in range(n):
                tt = i / (n - 1)
                span = (x1 - x0) * 0.36
                lx = tx - lerp(0, span, tt)
                rx = tx + lerp(0, span, tt)
                d.line([(tx * s, (y0 - h * 0.072) * s), (lx * s, y0 * s)],
                       fill=150, width=max(1, int(w * 0.0009 * s)))
                d.line([(tx * s, (y0 - h * 0.072) * s), (rx * s, y0 * s)],
                       fill=150, width=max(1, int(w * 0.0009 * s)))
    m = draw_mask(h, w, fn)
    col = np.zeros((h, w, 3))
    for ch in range(3):
        col[:, :, ch] = deck_col[ch]
    return col, m


def water(h, w, rng, colour_top, colour_bottom, glints=240, glint_col=(255, 232, 200)):
    layer = vgrad(h, w, [(0.0, colour_top), (1.0, colour_bottom)])
    strength = np.linspace(0.85, 0.15, h)[:, None]
    for _ in range(glints):
        gy = int(rng.random() ** 1.6 * (h - 1))
        gx = int(rng.random() * w)
        glen = int(rng.integers(w // 260, w // 45))
        th = max(1, int(h / 420))
        a = (1.0 - gy / h) * 0.85
        x0, x1 = max(0, gx - glen // 2), min(w, gx + glen // 2)
        if x1 <= x0:
            continue
        band = np.zeros((h, w, 3))
        for ch in range(3):
            band[:, :, ch] = glint_col[ch]
        mask = np.zeros((h, w))
        mask[gy:gy + th, x0:x1] = a
        layer = over(layer, band, mask)
    return layer


def reflect(h, w, source, alpha, y_water, stretch=2.6, sway=1.05, fade=0.55):
    """Mirror the skyline into the water with a vertical stretch and blur."""
    sh = source.shape[0]
    band_h = h - y_water
    if band_h <= 4:
        return np.zeros((h, w, 3)), np.zeros((h, w))
    # take the part of the source above the water line
    take = min(int(band_h / stretch) + 2, sh)
    src = source[max(0, sh - take - int(sh * 0.15)):sh - int(sh * 0.15), :, :]
    if src.shape[0] < 2:
        src = source[-take:, :, :]
    idx = (np.linspace(0, src.shape[0] - 1, band_h)).astype(int)
    refl = src[idx]
    # horizontal wobble
    yy = np.arange(band_h)[:, None]
    wob = (np.sin(yy / 11.0) * sway + np.sin(yy / 4.3) * sway * 0.5).astype(int)
    cols = np.arange(w)[None, :] + wob
    cols = np.clip(cols, 0, w - 1)
    refl = np.take_along_axis(refl, np.repeat(cols[:, :, None], 3, axis=2), axis=1)
    a = np.linspace(1.0, 0.0, band_h)[:, None] * fade
    out = np.zeros((h, w, 3))
    out[y_water:] = refl
    am = np.zeros((h, w))
    am[y_water:] = a
    return out, am


def telegraph_grid(h, w, rng, horizon, colour=(120, 210, 255), alpha=0.16, spacing=None):
    """Faint perspective grid — the 'tech city' motif."""
    spacing = spacing or max(40, w // 26)
    def fn(d, s):
        for x in range(-spacing, w + spacing, spacing):
            d.line([(x * s, horizon * s), ((x + (x - w / 2) * 1.35) * s, h * s)],
                   fill=255, width=max(1, int(w * 0.0009 * s)))
        y = horizon
        step = max(6, (h - horizon) // 14)
        k = 1
        while y < h:
            d.line([(0, y * s), (w * s, y * s)], fill=200,
                   width=max(1, int(w * 0.0007 * s)))
            y += step
            step = int(step * 1.22)
            k += 1
    m = draw_mask(h, w, fn)
    layer = np.zeros((h, w, 3))
    for ch in range(3):
        layer[:, :, ch] = colour[ch]
    return layer, m * alpha


def stars(h, w, rng, max_y, count=420):
    layer = np.zeros((h, w, 3))
    am = np.zeros((h, w))
    for _ in range(count):
        y = int(rng.random() ** 2 * max_y)
        x = int(rng.random() * w)
        b = rng.uniform(0.25, 1.0)
        r = 1 if rng.random() < 0.9 else 2
        layer[max(0, y - r):y + r, max(0, x - r):x + r] = 255
        am[max(0, y - r):y + r, max(0, x - r):x + r] = b
    layer = layer * np.array([0.85, 0.95, 1.0])
    return layer, am


def old_town_roofs(h, w, rng, base_y, colour=(58, 34, 32), tiles=(176, 78, 62)):
    """Layered Hakka-style tiled roofs, settling toward the water line."""
    m = np.zeros((h, w))
    col = np.zeros((h, w, 3))
    for ch in range(3):
        col[:, :, ch] = colour[ch]

    layers = 6
    for li in range(layers):
        y = base_y - li * int(h * 0.055)
        near_layer = li < 3
        n = (4 if near_layer else 7) + li
        bw_unit = (0.15 if near_layer else 0.085)
        for i in range(n):
            cx = int(w * (0.06 + i * (0.88 / max(1, n - 1))) + rng.integers(-int(w * 0.012), int(w * 0.012)))
            bw = int(w * bw_unit * rng.uniform(0.85, 1.15))
            bh = int(h * (0.055 if near_layer else 0.032) * rng.uniform(0.85, 1.3))
            x0, x1 = cx - bw // 2, cx + bw // 2
            body = (34, 24, 28) if near_layer else colour
            c = tiles if (li % 2 == 0) else (150, 62, 50)

            def fn(d, s, x0=x0, x1=x1, y=y, bh=bh, body=body, c=c, w=w):
                d.rectangle([x0 * s, (y - bh) * s, x1 * s, (y + 5) * s], fill=255)
                over = w * 0.016
                d.polygon([((x0 - over) * s, (y - bh + 4) * s),
                           ((x1 + over) * s, (y - bh + 4) * s),
                           ((x1 + over * 0.35) * s, (y - bh - bh * 0.5) * s),
                           ((x0 - over * 0.35) * s, (y - bh - bh * 0.5) * s)],
                          fill=230)
            mm = draw_mask(h, w, fn)
            body_col = np.zeros((h, w, 3))
            for ch in range(3):
                body_col[:, :, ch] = c[ch]
            # roof band sits above the wall band
            arr_col = np.where(
                (np.arange(h)[:, None] < y - bh + int(h * 0.012)),
                c[0], body[0])
            for ch in range(3):
                v = c[ch] if ch == 0 else body[ch]
            col = over(col, body_col, mm)
            # wall body below the eave line
            wm = draw_mask(h, w, lambda d, s2, x0=x0, x1=x1, y=y, bh=bh:
                           d.rectangle([(x0 + w * 0.004) * s2, (y - bh * 0.55) * s2,
                                        (x1 - w * 0.004) * s2, (y + 5) * s2], fill=255))
            wall_col = np.zeros((h, w, 3))
            for ch in range(3):
                wall_col[:, :, ch] = body[ch]
            col = over(col, wall_col, np.maximum(wm - mm, 0))
            # warm window
            if rng.random() < 0.6:
                ww, wh = int(bw * 0.16), int(bh * 0.26)
                wx = cx - ww // 2
                wy = int(y - bh * 0.42)
                gm = draw_mask(h, w, lambda d, s2, wx=wx, wy=wy, ww=ww, wh=wh:
                               d.rectangle([wx * s2, wy * s2, (wx + ww) * s2,
                                            (wy + wh) * s2], fill=255))
                gcol = np.dstack([np.full((h, w), 255.0), np.full((h, w), 206.0),
                                  np.full((h, w), 140.0)])
                col = over(col, gcol, gm * 0.9)
            m = np.maximum(m, mm)
    return col, m


def bay_bridge(h, w, rng, y, x0, x1, deck_col=(228, 238, 246), cable_col=(210, 226, 240)):
    """Shenzhen Bay Bridge: deck, two towers, stay cables."""
    def fn(d, s):
        y0 = y
        d.rectangle([x0 * s, (y0 - h * 0.006) * s, x1 * s, (y0 + h * 0.006) * s], fill=255)
        for tx in (x0 + (x1 - x0) * 0.30, x0 + (x1 - x0) * 0.70):
            d.rectangle([(tx - w * 0.0022) * s, (y0 - h * 0.075) * s,
                         (tx + w * 0.0022) * s, (y0 + h * 0.01) * s], fill=255)
            n = 12
            for i in range(n):
                tt = i / (n - 1)
                span = (x1 - x0) * 0.36
                lx = tx - lerp(0, span, tt)
                rx = tx + lerp(0, span, tt)
                d.line([(tx * s, (y0 - h * 0.072) * s), (lx * s, y0 * s)],
                       fill=150, width=max(1, int(w * 0.0009 * s)))
                d.line([(tx * s, (y0 - h * 0.072) * s), (rx * s, y0 * s)],
                       fill=150, width=max(1, int(w * 0.0009 * s)))
    m = draw_mask(h, w, fn)
    col = np.zeros((h, w, 3))
    for ch in range(3):
        col[:, :, ch] = deck_col[ch]
    return col, m


def water(h, w, rng, colour_top, colour_bottom, glints=240, glint_col=(255, 232, 200)):
    layer = vgrad(h, w, [(0.0, colour_top), (1.0, colour_bottom)])
    strength = np.linspace(0.85, 0.15, h)[:, None]
    for _ in range(glints):
        gy = int(rng.random() ** 1.6 * (h - 1))
        gx = int(rng.random() * w)
        glen = int(rng.integers(w // 260, w // 45))
        th = max(1, int(h / 420))
        a = (1.0 - gy / h) * 0.85
        x0, x1 = max(0, gx - glen // 2), min(w, gx + glen // 2)
        if x1 <= x0:
            continue
        band = np.zeros((h, w, 3))
        for ch in range(3):
            band[:, :, ch] = glint_col[ch]
        mask = np.zeros((h, w))
        mask[gy:gy + th, x0:x1] = a
        layer = over(layer, band, mask)
    return layer


def reflect(h, w, source, alpha, y_water, stretch=2.6, sway=1.05, fade=0.55):
    """Mirror the skyline into the water with a vertical stretch and blur."""
    sh = source.shape[0]
    band_h = h - y_water
    if band_h <= 4:
        return np.zeros((h, w, 3)), np.zeros((h, w))
    # take the part of the source above the water line
    take = min(int(band_h / stretch) + 2, sh)
    src = source[max(0, sh - take - int(sh * 0.15)):sh - int(sh * 0.15), :, :]
    if src.shape[0] < 2:
        src = source[-take:, :, :]
    idx = (np.linspace(0, src.shape[0] - 1, band_h)).astype(int)
    refl = src[idx]
    # horizontal wobble
    yy = np.arange(band_h)[:, None]
    wob = (np.sin(yy / 11.0) * sway + np.sin(yy / 4.3) * sway * 0.5).astype(int)
    cols = np.arange(w)[None, :] + wob
    cols = np.clip(cols, 0, w - 1)
    refl = np.take_along_axis(refl, np.repeat(cols[:, :, None], 3, axis=2), axis=1)
    a = np.linspace(1.0, 0.0, band_h)[:, None] * fade
    out = np.zeros((h, w, 3))
    out[y_water:] = refl
    am = np.zeros((h, w))
    am[y_water:] = a
    return out, am


def telegraph_grid(h, w, rng, horizon, colour=(120, 210, 255), alpha=0.16, spacing=None):
    """Faint perspective grid — the 'tech city' motif."""
    spacing = spacing or max(40, w // 26)
    def fn(d, s):
        for x in range(-spacing, w + spacing, spacing):
            d.line([(x * s, horizon * s), ((x + (x - w / 2) * 1.35) * s, h * s)],
                   fill=255, width=max(1, int(w * 0.0009 * s)))
        y = horizon
        step = max(6, (h - horizon) // 14)
        k = 1
        while y < h:
            d.line([(0, y * s), (w * s, y * s)], fill=200,
                   width=max(1, int(w * 0.0007 * s)))
            y += step
            step = int(step * 1.22)
            k += 1
    m = draw_mask(h, w, fn)
    layer = np.zeros((h, w, 3))
    for ch in range(3):
        layer[:, :, ch] = colour[ch]
    return layer, m * alpha


def stars(h, w, rng, max_y, count=420):
    layer = np.zeros((h, w, 3))
    am = np.zeros((h, w))
    for _ in range(count):
        y = int(rng.random() ** 2 * max_y)
        x = int(rng.random() * w)
        b = rng.uniform(0.25, 1.0)
        r = 1 if rng.random() < 0.9 else 2
        layer[max(0, y - r):y + r, max(0, x - r):x + r] = 255
        am[max(0, y - r):y + r, max(0, x - r):x + r] = b
    layer = layer * np.array([0.85, 0.95, 1.0])
    return layer, am


def old_town_roofs(h, w, rng, base_y, colour=(58, 34, 32), tiles=(176, 78, 62)):
    """Layered Hakka/traditional roofs for the old-town scene."""
    m = np.zeros((h, w))
    col = np.zeros((h, w, 3))
    layers = 4
    for li in range(layers):
        y = base_y - li * int(h * 0.075)
        row_h = int(h * 0.035)
        n = 5 + li
        for i in range(n):
            cx = int(w * (0.08 + i * (0.86 / max(1, n - 1))) + rng.integers(-14, 14))
            bw = int(w * rng.uniform(0.10, 0.17))
            bh = int(row_h * rng.uniform(0.9, 1.5))
            x0, x1 = cx - bw // 2, cx + bw // 2
            c = tiles if li % 2 == 0 else colour

            def fn(d, s, x0=x0, x1=x1, y=y, bh=bh, c=c):
                d.rectangle([x0 * s, (y - bh) * s, x1 * s, (y + 6) * s], fill=255)
                d.polygon([((x0 - w * 0.012) * s, (y - bh + 3) * s),
                           ((x1 + w * 0.012) * s, (y - bh + 3) * s),
                           ((x1 + w * 0.004) * s, (y - bh - bh * 0.42) * s),
                           ((x0 - w * 0.004) * s, (y - bh - bh * 0.42) * s)], fill=220)
            mm = draw_mask(h, w, fn)
            for ch in range(3):
                col[:, :, ch] = np.where(mm > 0, c[ch], col[:, :, ch])
            m = np.maximum(m, mm)
    return col, m


# --------------------------------------------------------------------------- #
# scene composer
# --------------------------------------------------------------------------- #
def finish(arr, h, w, rng, vig=0.34, grain_amt=2.1, glow=None, bloom=0.0):
    if glow is not None:
        col, amt = glow
        arr = over(arr, col, amt)
    if bloom > 0:
        img = to_image(arr, h, w).filter(ImageFilter.GaussianBlur(max(2, w // 220)))
        blurred = np.asarray(img, dtype=np.float64)
        arr = np.clip(arr * (1 - bloom) + blurred * bloom + blurred * 0.35, 0, 255)
    arr = arr * vignette(h, w, vig)
    arr = arr + grain((h, w, 3), rng, grain_amt)
    return to_image(arr, h, w)


def render_skyline(scene, W, H, seed=7, horizon=0.62, variant="bay",
                   landmarks=True, bottom_fade=None):
    rng = np.random.default_rng(seed)
    h, w = H, W

    palettes = {
        "dusk": dict(
            sky=[(0.0, (10, 22, 46)), (0.34, (30, 62, 104)), (0.62, (196, 106, 86)),
                 (0.78, (247, 168, 108)), (1.0, (255, 208, 150))],
            sun=(255, 214, 160), sun_y=0.60, glow=(255, 190, 130), glow_s=0.55,
            far=(78, 96, 132), mid=(44, 62, 92), near=(16, 26, 44),
            water=((196, 132, 110), (22, 34, 58)), lit=0.55, stars=0,
            glow_a=0.95, bloom=0.16, vig=0.32, horizon_mist=0.30),
        "hero": dict(
            sky=[(0.0, (4, 14, 28)), (0.30, (12, 34, 62)), (0.58, (74, 74, 104)),
                 (0.76, (188, 108, 92)), (0.90, (240, 156, 104)),
                 (1.0, (252, 196, 146))],
            sun=(255, 222, 176), sun_y=0.80, glow=(255, 176, 118), glow_s=0.5,
            far=(92, 104, 138), mid=(40, 58, 88), near=(12, 22, 40),
            water=((196, 132, 110), (22, 34, 58)), lit=0.62, stars=0,
            glow_a=0.85, bloom=0.14, vig=0.22, horizon_mist=0.34),
        "night": dict(
            sky=[(0.0, (4, 12, 26)), (0.45, (9, 28, 52)), (0.8, (16, 52, 82)),
                 (1.0, (28, 84, 112))],
            sun=(210, 240, 255), sun_y=0.22, glow=(90, 170, 220), glow_s=0.30,
            far=(30, 50, 78), mid=(20, 36, 60), near=(9, 18, 32),
            water=((58, 122, 158), (8, 22, 42)), lit=0.78, stars=1,
            glow_a=0.8, bloom=0.34, vig=0.42, horizon_mist=0.18),
        "coast": dict(
            sky=[(0.0, (24, 122, 176)), (0.4, (86, 176, 214)), (0.72, (176, 224, 236)),
                 (1.0, (222, 244, 244))],
            sun=(255, 248, 220), sun_y=0.30, glow=(255, 240, 200), glow_s=0.45,
            far=(140, 186, 200), mid=(74, 132, 150), near=(30, 74, 92),
            water=((176, 226, 226), (26, 104, 128)), lit=0.34, stars=0,
            glow_a=0.8, bloom=0.16, vig=0.30, horizon_mist=0.20),
        "tech": dict(
            sky=[(0.0, (3, 14, 34)), (0.42, (7, 34, 72)), (0.78, (14, 90, 130)),
                 (1.0, (36, 176, 190))],
            sun=(150, 255, 245), sun_y=0.52, glow=(60, 230, 220), glow_s=0.55,
            far=(26, 78, 116), mid=(18, 54, 90), near=(8, 24, 48),
            water=((64, 205, 200), (6, 26, 48)), lit=0.74, stars=0,
            glow_a=1.35, bloom=0.24, vig=0.40, horizon_mist=0.12),
    } if variant != "oldtown" else {}

    if variant == "oldtown":
        sky = [(0.0, (40, 66, 108)), (0.34, (108, 108, 138)), (0.62, (218, 150, 118)),
               (0.82, (248, 196, 138)), (1.0, (255, 226, 178))]
        sun = (255, 226, 170); sun_y = 0.66; glow = (255, 200, 150); glow_s = 0.42
        far = (96, 92, 116); mid = (62, 50, 62); near = (34, 24, 28)
        water_c = ((244, 196, 150), (52, 38, 48)); lit = 0.4; stars_on = 0
        glow_a, bloom_a, vig_a, mist_a = 0.9, 0.10, 0.34, 0.22
    else:
        p = palettes[variant]
        sky, sun, sun_y = p["sky"], p["sun"], p["sun_y"]
        glow, glow_s = p["glow"], p["glow_s"]
        far, mid, near = p["far"], p["mid"], p["near"]
        water_c, lit, stars_on = p["water"], p["lit"], p["stars"]
        glow_a, bloom_a = p["glow_a"], p["bloom"]
        vig_a, mist_a = p["vig"], p["horizon_mist"]

    y_h = int(h * horizon)
    arr = vgrad(h, w, sky, span=(0.0, float(horizon)))

    if stars_on:
        sl, sa = stars(h, w, rng, int(h * horizon * 0.9), int(w * 0.25))
        arr = over(arr, sl, sa * 0.9)

    arr = np.clip(arr + radial_glow(h, w, int(w * 0.72), int(h * sun_y),
                                    int(h * 0.34), glow, glow_a, 2.4), 0, 255)
    # sun disc
    sm = draw_mask(h, w, lambda d, s: d.ellipse(
        [(w * 0.72 - h * 0.045) * s, (h * sun_y - h * 0.045) * s,
         (w * 0.72 + h * 0.045) * s, (h * sun_y + h * 0.045) * s], fill=255))
    arr = over(arr, np.dstack([np.full((h, w), float(sun[0])),
                               np.full((h, w), float(sun[1])),
                               np.full((h, w), float(sun[2]))]), sm * 0.95)

    if variant == "tech":
        gl, gm = telegraph_grid(h, w, rng, int(h * 0.30), (110, 235, 235), 0.18)
        arr = over(arr, gl, gm)

    # distant mountain / headland band
    def mountain(d, s):
        pts = [(0, int(h * horizon))]
        x = 0
        while x < w:
            x += int(rng.integers(w // 16, w // 7))
            pts.append((x, int(h * horizon) - int(rng.integers(h * 0.01, h * 0.075))))
        pts += [(w, int(h * horizon)), (w, h), (0, h)]
        d.polygon([(px * s, py * s) for px, py in pts], fill=255)
    mm = draw_mask(h, w, mountain)
    arr = over(arr, np.dstack([np.full((h, w), float(far[0])),
                               np.full((h, w), float(far[1])),
                               np.full((h, w), float(far[2]))]), mm * 0.85)

    if variant == "oldtown":
        bcol, bm = skyline(h, w, rng, y_h, int(h * 0.06), int(h * 0.18), far,
                           lit_ratio=0.35, density=1.6, spire_chance=0.05)
        arr = over(arr, bcol, bm * 0.8)
        col, m = old_town_roofs(h, w, rng, int(h * 0.86))
        arr = over(arr, col, m)
        # lanterns
        lm = draw_mask(h, w, lambda d, s: [d.ellipse(
            [((w * (0.12 + i * 0.19)) - w * 0.008) * s, (h * 0.62 + (i % 2) * h * 0.05) * s,
             ((w * (0.12 + i * 0.19)) + w * 0.008) * s, (h * 0.62 + (i % 2) * h * 0.05 + h * 0.026) * s],
            fill=255) for i in range(5)])
        arr = over(arr, np.dstack([np.full((h, w), 255.0), np.full((h, w), 170.0),
                                   np.full((h, w), 90.0)]), lm * 0.95)
        for i in range(5):
            arr = np.clip(arr + radial_glow(h, w, int(w * (0.12 + i * 0.19)),
                                            int(h * 0.635 + (i % 2) * h * 0.05),
                                            int(h * 0.09), (255, 150, 80), 0.5, 2.6), 0, 255)
        wl = water(h, w, rng, (240, 196, 156), (48, 36, 46),
                   glints=int(w * 0.10), glint_col=(255, 224, 180))
        wm2 = np.zeros((h, w))
        wm2[int(h * 0.90):] = 1.0
        arr = over(arr, wl, wm2 * 0.55)
        return finish(arr, h, w, rng, vig=vig_a, grain_amt=2.4, bloom=bloom_a)

    # skyline bands
    far_col, far_a = skyline(h, w, rng, y_h - int(h * 0.01), int(h * 0.05), int(h * 0.16), far,
                             lit_ratio=lit * 0.5, density=1.7, spire_chance=0.06)
    arr = over(arr, far_col, far_a * 0.92)
    hz, ha = haze_band(h, w, int(h * horizon * 0.55), y_h + 2,
                       (255, 210, 180) if variant != "tech" else (120, 230, 240),
                       0.0, mist_a)
    arr = over(arr, hz, ha)

    if variant == "coast":
        col, m = bay_bridge(h, w, rng, int(h * horizon * 0.90), int(w * 0.28), int(w * 0.86))
        arr = over(arr, col, m * 0.95)

    mid_col, mid_a = skyline(h, w, rng, y_h, int(h * 0.08), int(h * 0.24), mid,
                             lit_ratio=lit * 0.85, density=1.0, spire_chance=0.12)
    arr = over(arr, mid_col, mid_a)

    # signature landmarks
    for fn, args in (() if not landmarks else (
        (landmark_tower_pingan, dict(x=int(w * 0.60), height=int(h * 0.40))),
        (spring_tower, dict(x=int(w * 0.78), height=int(h * 0.30))),
    )):
        col, m = fn(h, w, rng, base_y=y_h, colour=near, **args)
        arr = over(arr, col, m * (0.55 if variant == "coast" else 1.0))

    near_col, near_a = skyline(h, w, rng, y_h, int(h * 0.10), int(h * 0.30), near,
                               lit_ratio=lit, density=0.8, spire_chance=0.16,
                               window_colours=((255, 214, 150), (255, 240, 205),
                                               (170, 225, 255), (255, 180, 130)))
    arr = over(arr, near_col, near_a)

    if variant == "hero":
        # no water on the hero plate: the skyline is anchored to the bottom edge
        return finish(arr, h, w, rng, vig=vig_a, grain_amt=2.0, bloom=bloom_a,
                      glow=None)

    # grounded mist between city and water
    hz2, ha2 = haze_band(h, w, y_h - int(h * 0.03), y_h + int(h * 0.01),
                         (255, 224, 196) if variant != "tech" else (150, 235, 245),
                         0.0, mist_a * 0.9)
    arr = over(arr, hz2, ha2)

    # water
    wl = water(h, w, rng, water_c[0], water_c[1],
               glints=int(w * 0.16) + 120,
               glint_col=(255, 236, 205) if variant != "tech" else (190, 255, 250))
    wmask = np.zeros((h, w))
    wmask[y_h:] = 1.0
    arr = over(arr, wl, wmask)
    rl, ra = reflect(h, w, arr, None, y_h, stretch=2.4, sway=1.2,
                     fade=0.55 if variant != "tech" else 0.62)
    arr = over(arr, rl, ra * 0.7)
    wglow = {"coast": 0.62, "night": 0.44, "dusk": 0.30, "tech": 0.22}.get(variant, 0.3)
    arr = np.clip(arr + radial_glow(h, w, int(w * 0.72), y_h + int(h * 0.06),
                                    int(h * 0.30), glow, wglow, 2.0), 0, 255)

    if bottom_fade:
        y0, y1, strength = bottom_fade
        fa = np.zeros((h, w))
        yy = np.arange(h)
        m = (yy >= y0) & (yy <= y1)
        t = (yy[m] - y0) / max(y1 - y0, 1e-6)
        fa[m] = (t ** 1.5) * strength
        fade = np.zeros((h, w, 3))
        fade[:, :, 0] = 4; fade[:, :, 1] = 15; fade[:, :, 2] = 27
        arr = over(arr, fade, np.repeat(fa[:, None], w, axis=1))

    return finish(arr, h, w, rng, vig=vig_a, grain_amt=2.0, bloom=bloom_a)


def render_metro(W, H, seed=11):
    """Abstract night transit diagram — lines, interchange nodes, glow."""
    rng = np.random.default_rng(seed)
    h, w = H, W
    arr = vgrad(h, w, [(0.0, (6, 16, 30)), (0.55, (10, 30, 52)), (1.0, (14, 46, 74))])
    for i in range(5):
        arr = np.clip(arr + radial_glow(h, w, int(w * (0.15 + i * 0.2)), int(h * 0.3),
                                        int(h * 0.5), (30, 120, 170), 0.30, 2.0), 0, 255)

    colours = [(63, 208, 201), (30, 147, 232), (255, 107, 74), (242, 181, 68),
               (155, 130, 245), (120, 230, 150)]
    lines = []
    for i, c in enumerate(colours):
        y0 = int(h * (0.16 + i * 0.14))
        pts = [(0, y0)]
        x = 0
        y = y0
        while x < w:
            x += int(rng.integers(w // 9, w // 4))
            y = int(np.clip(y + rng.integers(-int(h * 0.11), int(h * 0.11)),
                            h * 0.10, h * 0.90))
            pts.append((x, y))
        lines.append((pts, c))
    for pts, c in lines:
        glow_m = draw_mask(h, w, lambda d, s, pts=pts: d.line(
            [(x * s, y * s) for x, y in pts], fill=255, width=max(3, int(w * 0.007 * s)),
            joint="curve"))
        blurred = Image.fromarray((glow_m * 255).astype(np.uint8)).filter(
            ImageFilter.GaussianBlur(max(3, w // 110)))
        arr = over(arr, np.dstack([np.full((h, w), float(c[0])),
                                   np.full((h, w), float(c[1])),
                                   np.full((h, w), float(c[2]))]),
                   np.asarray(blurred, dtype=np.float64) / 255.0 * 0.55)
        m = draw_mask(h, w, lambda d, s, pts=pts: d.line(
            [(x * s, y * s) for x, y in pts], fill=255,
            width=max(2, int(w * 0.0026 * s)), joint="curve"))
        arr = over(arr, np.dstack([np.full((h, w), float(c[0] * 0.55 + 110)),
                                   np.full((h, w), float(c[1] * 0.55 + 110)),
                                   np.full((h, w), float(c[2] * 0.55 + 110))]), m)
        for (x, y) in pts:
            sm = draw_mask(h, w, lambda d, s, x=x, y=y: d.ellipse(
                [(x - w * 0.006) * s, (y - w * 0.006) * s,
                 (x + w * 0.006) * s, (y + w * 0.006) * s], fill=255))
            arr = over(arr, np.dstack([np.full((h, w), 255.0)] * 3), sm * 0.92)
            arr = np.clip(arr + radial_glow(h, w, x, y, int(w * 0.05), c, 0.5, 2.2), 0, 255)
    # faint district grid
    gl, gm = telegraph_grid(h, w, rng, int(h * 0.08), (120, 200, 255), 0.14,
                            spacing=max(48, w // 20))
    arr = over(arr, gl, gm)
    return finish(arr, h, w, rng, vig=0.42, grain_amt=2.2, bloom=0.28)


def stars_fn(h, w, rng, max_y, count):
    return stars(h, w, rng, max_y, count)


# --------------------------------------------------------------------------- #
# builds
# --------------------------------------------------------------------------- #
def save(img, name, colors=192):
    """Save as a palette PNG — keeps gradients smooth, files small."""
    p = OUT / name
    if img.mode != "RGB":
        img = img.convert("RGB")
    q = img.quantize(colors=colors, method=Image.MEDIANCUT, dither=Image.FLOYDSTEINBERG)
    q.save(p, "PNG", optimize=True)
    print(f"  {name:22s} {img.size[0]}x{img.size[1]}  {p.stat().st_size/1024:.0f} KB")


def build_hero_panorama():
    """Wide dusk panorama used as the landing hero background."""
    W, H = px(2400), px(1040)
    img = render_skyline("hero", W, H, seed=2026, horizon=0.62, variant="hero",
                         landmarks=False,
                         bottom_fade=(int(H * 0.80), H - 1, 0.72))
    # deepen the left half so the headline always has contrast
    arr = np.asarray(img, dtype=np.float64)
    ramp = np.clip(1.0 - np.linspace(0, 1, W)[None, :] / (W * 0.52), 0, 1) ** 1.5
    dark = np.zeros((H, W, 3))
    dark[:, :, 0] = 3; dark[:, :, 1] = 12; dark[:, :, 2] = 23
    arr = over(arr, dark, np.repeat(ramp * 0.82, H, axis=0))
    return to_image(arr, H, W)


def build_scenes():
    scenes = [
        ("scene-bay.png", "bay", 2400, 1400, 31, 0.58, "dusk"),
        ("scene-night.png", "night", 2400, 1400, 44, 0.66, "night"),
        ("scene-coast.png", "coast", 2400, 1400, 57, 0.60, "coast"),
        ("scene-tech.png", "tech", 2400, 1400, 68, 0.64, "tech"),
        ("scene-oldtown.png", "oldtown", 2400, 1400, 79, 0.62, "oldtown"),
    ]
    out = []
    for name, scene, W, H, seed, hz, variant in scenes:
        out.append((name, render_skyline(scene, px(W), px(H), seed=seed, horizon=hz,
                                         variant=variant)))
    out.append(("scene-metro.png", render_metro(px(2400), px(1400), seed=91)))
    return out


def build_cover_card():
    """Square-ish composition card reused in hero side panels."""
    W, H = px(1600), px(1200)
    return render_skyline("cover", W, H, seed=2026, horizon=0.64, variant="night")


def build_og():
    """Social preview card with a gradient band and the wordmark."""
    W, H = px(1200), px(630)
    img = render_skyline("og", W, H, seed=5, horizon=0.68, variant="dusk")
    arr = np.asarray(img.convert("RGB"), dtype=np.float64)
    arr = arr * 0.62
    base = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")
    d = ImageDraw.Draw(base)
    # translucent bottom band
    band = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(band)
    bd.rectangle([0, int(H * 0.60), W, H], fill=(4, 14, 26, 205))
    base = Image.alpha_composite(base.convert("RGBA"), band).convert("RGB")
    d = ImageDraw.Draw(base)
    d.rectangle([0, int(H * 0.60), W, int(H * 0.60) + 4], fill=(63, 208, 201))
    return base


def main():
    print("generating artwork →", OUT)
    save(build_hero_panorama(), "hero-cover.png")
    save(build_cover_card(), "cover-card.png")
    for name, img in build_scenes():
        save(img, name)
    save(build_og(), "og-cover.png")


if __name__ == "__main__":
    main()
