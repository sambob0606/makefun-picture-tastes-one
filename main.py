#!/usr/bin/env python3
"""The picture that tastes of one ingredient: a tall stack of golden pancakes.

Pure Python standard library only (no Pillow): a 2x supersampled RGB
framebuffer, span-fill drawing helpers, 2x2 box downsample, and a hand-rolled
PNG encoder (zlib + struct). Writes $MAKEFUN_OUTPUT_DIR/entry.png (1024x1024).
"""
import math
import os
import random
import struct
import zlib

S = 2  # supersample factor
W = H = 1024
W2, H2 = W * S, H * S

random.seed(20261122)

# ---- framebuffer (2x), pre-filled with the warm background base ----
buf = bytearray(bytes((250, 233, 205)) * (W2 * H2))


def span(y, x0, x1, rgb):
    if y < 0 or y >= H2:
        return
    if x0 < 0:
        x0 = 0
    if x1 > W2 - 1:
        x1 = W2 - 1
    if x1 < x0:
        return
    i = (y * W2 + x0) * 3
    buf[i:i + (x1 - x0 + 1) * 3] = bytes(rgb) * (x1 - x0 + 1)


def ellipse(cx, cy, rx, ry, rgb):
    if rx <= 0 or ry <= 0:
        return
    for y in range(cy - ry, cy + ry + 1):
        dy = y - cy
        t = 1.0 - (dy * dy) / float(ry * ry)
        if t <= 0:
            continue
        dx = int(rx * math.sqrt(t))
        span(y, cx - dx, cx + dx, rgb)


def disc(x, y, r, rgb):
    ellipse(x, y, r, r, rgb)


def ellipse_ring(cx, cy, rx, ry, w, rgb):
    """Filled ellipse outline of thickness w."""
    if rx <= 0 or ry <= 0:
        return
    irx, iry = rx - w, ry - w
    for y in range(cy - ry, cy + ry + 1):
        dy = y - cy
        t = 1.0 - (dy * dy) / float(ry * ry)
        if t <= 0:
            continue
        dx = int(rx * math.sqrt(t))
        if irx <= 0 or iry <= 0:
            span(y, cx - dx, cx + dx, rgb)
            continue
        t2 = 1.0 - (dy * dy) / float(iry * iry)
        if t2 <= 0:
            span(y, cx - dx, cx + dx, rgb)
            continue
        idx = int(irx * math.sqrt(t2))
        span(y, cx - dx, cx - idx, rgb)
        span(y, cx + idx, cx + dx, rgb)


def rect(x0, y0, x1, y1, rgb):
    for y in range(max(0, y0), min(H2, y1 + 1)):
        span(y, x0, x1, rgb)


def rrect(x0, y0, x1, y1, r, rgb):
    """Rounded rectangle, corners of radius r."""
    for y in range(y0, y1 + 1):
        if y < y0 + r:
            d = r - (y - y0)
            inset = r - int(math.sqrt(max(0, r * r - d * d)))
            span(y, x0 + inset, x1 - inset, rgb)
        elif y > y1 - r:
            d = r - (y1 - y)
            inset = r - int(math.sqrt(max(0, r * r - d * d)))
            span(y, x0 + inset, x1 - inset, rgb)
        else:
            span(y, x0, x1, rgb)


def half_ellipse_top(cx, cy, rx, ry, rgb):
    """Upper half of a filled ellipse (strawberry cut side)."""
    for y in range(cy - ry, cy + 1):
        dy = y - cy
        t = 1.0 - (dy * dy) / float(ry * ry)
        if t <= 0:
            continue
        dx = int(rx * math.sqrt(t))
        span(y, cx - dx, cx + dx, rgb)


def arc_discs(cx, cy, rx, ry, a0, a1, step_deg, r, rgb):
    a = a0
    while a <= a1:
        rad = math.radians(a)
        disc(int(cx + rx * math.cos(rad)), int(cy + ry * math.sin(rad)), r, rgb)
        a += step_deg


def lerp(a, b, t):
    return (int(a[0] + (b[0] - a[0]) * t),
            int(a[1] + (b[1] - a[1]) * t),
            int(a[2] + (b[2] - a[2]) * t))


def main():
    # ---- warm background: radial glow ----
    for r in range(720, 0, -6):
        t = r / 720.0
        ellipse(W2 // 2, H2 // 2 - 60, r, r,
                lerp((252, 236, 208), (232, 196, 148), t))
    # wooden table band at bottom
    rect(0, H2 - 300, W2, H2, (176, 124, 78))
    rect(0, H2 - 300, W2, H2 - 292, (150, 102, 60))
    for i in range(14):
        y = H2 - 280 + i * 20
        rect(0, y, W2, y + 2, (166, 116, 72))
    # soft light from upper left (matches original: bbox [-300,-300,900,500])
    ellipse(300, 100, 600, 400, (255, 248, 225))

    cx = W2 // 2
    plate_cy = 1560
    # ---- soft shadow under plate ----
    ellipse(cx, plate_cy + 45, 700, 105, (120, 70, 35))
    # ---- plate ----
    ellipse(cx, plate_cy, 760, 190, (244, 238, 226))
    ellipse(cx, plate_cy - 14, 700, 172, (250, 246, 236))
    ellipse(cx, plate_cy - 20, 560, 138, (236, 228, 210))
    ellipse_ring(cx, plate_cy - 20, 560, 138, 5, (205, 192, 168))

    # ---- pancake stack ----
    layers = [
        (1180, 168, 205, 138, 62),
        (1030, 158, 192, 128, 54),
        (880, 148, 180, 118, 46),
        (730, 138, 168, 108, 38),
        (580, 128, 158, 98, 30),
    ]
    base_top = 1380
    step = 150
    for i, (cy_top, rx, ry, side_rx, side_h) in enumerate(layers):
        top_y = base_top - i * step
        # side (golden brown, slightly darker at bottom edge)
        ellipse(cx, top_y + side_h, rx, ry, (196, 128, 52))
        ellipse(cx, top_y + side_h - 13, rx, ry, (212, 144, 62))
        # toasted edge ring around the top surface
        ellipse_ring(cx, top_y, rx, ry, 14, (172, 100, 34))
        # top surface (warm golden)
        ellipse(cx, top_y, rx, ry, (232, 176, 96))
        # toasted speckles on top
        for _ in range(90):
            a = random.uniform(0, 2 * math.pi)
            rr = random.uniform(0, 0.85)
            px = int(cx + math.cos(a) * rx * rr)
            py = int(top_y + math.sin(a) * ry * rr)
            r = random.uniform(3, 11)
            col = random.choice([(198, 128, 52), (214, 148, 66), (188, 116, 44)])
            ellipse(px, py, int(r), max(1, int(r * 0.55)), col)

    # ---- maple syrup: glossy pool on top + drips down the stack ----
    syrup = (146, 74, 18)
    syrup_hi = (198, 118, 38)
    top_y = base_top - 4 * step
    ellipse(cx, top_y, 128, 92, syrup)
    ellipse(cx - 18, top_y - 14, 88, 58, syrup_hi)
    drips = [(-150, 210, 26), (-88, 320, 30), (-10, 260, 24), (70, 360, 30),
             (140, 240, 24), (190, 170, 20), (-210, 120, 20)]
    for dx, length, w in drips:
        x0 = cx + dx
        rrect(x0 - w, top_y - 20, x0 + w, top_y + length, w, syrup)
        ellipse(x0, top_y + length, w + 4, w + 10, syrup)
        rrect(x0 - w + 8, top_y - 10, x0 - w + 16, top_y + length - 30, 6, syrup_hi)
    # syrup pool on plate
    ellipse(cx + 420, plate_cy - 40, 180, 46, syrup)
    ellipse(cx + 400, plate_cy - 52, 120, 28, syrup_hi)

    # ---- melting butter pat on top ----
    bx, by = cx - 30, top_y - 52
    rrect(bx - 95, by - 62, bx + 95, by + 22, 22, (255, 222, 110))
    rrect(bx - 95, by - 62, bx + 95, by - 18, 22, (255, 236, 150))
    rect(bx - 70, by - 44, bx + 70, by - 36, (255, 246, 190))
    # butter melt dripping off the edge
    rrect(bx + 55, by + 10, bx + 95, by + 78, 18, (255, 222, 110))
    ellipse(bx + 75, by + 78, 24, 26, (255, 222, 110))

    # ---- blueberries on top and plate ----
    def blueberry(x, y, r):
        ellipse(x, y, r, r, (52, 68, 138))
        ellipse(int(x - r * 0.3), int(y - r * 0.35),
                int(r * 0.55), int(r * 0.45), (96, 118, 190))
        ellipse(x, int(y - r * 0.68), int(r * 0.18), int(r * 0.22), (30, 40, 90))

    blueberry(cx + 120, top_y - 30, 52)
    blueberry(cx + 165, top_y + 18, 44)
    blueberry(cx - 170, top_y + 8, 46)
    blueberry(cx - 470, plate_cy - 70, 52)
    blueberry(cx - 380, plate_cy - 46, 44)
    blueberry(cx + 480, plate_cy - 74, 46)

    # ---- strawberry halves on the plate ----
    def strawberry(x, y, r):
        half_ellipse_top(x, y, r, r, (214, 58, 64))
        ellipse(x, int(y + r * 0.32), int(r * 0.82), int(r * 0.48), (246, 190, 186))
        for _ in range(26):
            a = random.uniform(-1.2, 1.2)
            rr = random.uniform(0.15, 0.7)
            px = int(x + math.sin(a) * r * rr * 0.9)
            py = int(y + r * 0.35 - abs(math.cos(a)) * r * rr * 0.3)
            disc(px, py, 4, (232, 120, 110))
        ellipse(x, int(y + r * 0.68), int(r * 0.2), int(r * 0.12), (246, 190, 186))

    strawberry(cx + 330, plate_cy - 46, 84)
    strawberry(cx - 540, plate_cy - 66, 70)

    # ---- powdered sugar dusting on top pancake ----
    for _ in range(160):
        a = random.uniform(0, 2 * math.pi)
        rr = random.uniform(0.5, 0.95)
        px = int(cx + math.cos(a) * 128 * rr)
        py = int(top_y + math.sin(a) * 92 * rr)
        ellipse(px, py, 3, 2, (255, 250, 240))

    # ---- steam wisps above the stack (chains of pale discs, two passes:
    # a wider faint wisp plus a brighter narrow core so they read clearly) ----
    for sx, phase, amp in [(cx - 220, 0.6, 52), (cx - 140, 0.0, 46),
                           (cx + 40, 1.4, 60), (cx + 210, 2.6, 42)]:
        for t in range(0, 121):
            yy = int(top_y - 150 - t * 5.4)
            xx = int(sx + math.sin(t / 12.0 + phase) * amp * (t / 100.0 + 0.3))
            disc(xx, yy, 20, (255, 252, 242))
            disc(xx, yy, 10, (255, 255, 255))

    # ---- honey-drizzle highlight across the top syrup pool ----
    for k in range(5):
        x0 = cx - 96 + k * 40
        arc_discs(x0, top_y - 12, 26, 46, 200, 340, 6, 4, (255, 214, 110))
    ellipse(cx - 32, top_y - 14, 26, 12, (255, 226, 140))

    # ---- golden rim light hugging the lower edge of the plate ----
    arc_discs(cx, plate_cy, 760, 190, 15, 165, 2, 8, (255, 196, 110))
    arc_discs(cx, plate_cy, 700, 172, 25, 155, 2, 4, (255, 220, 150))

    # ---- downsample 2048 -> 1024 (2x2 box average) with radial vignette ----
    col2 = [(x - 512) * (x - 512) for x in range(W)]
    vig = []
    for b in range(1025):
        r = math.sqrt(b * 512.0)
        if r <= 560.0:
            vig.append(1.0)
        else:
            t = min(1.0, (r - 560.0) / 190.0)
            vig.append(1.0 - 0.28 * t * t)
    out = bytearray(W * H * 3)
    for y in range(H):
        dy2 = (y - 512) * (y - 512)
        base0 = (2 * y) * W2 * 3
        base1 = base0 + W2 * 3
        orow = y * W * 3
        for x in range(W):
            i0 = base0 + x * 6
            i1 = base1 + x * 6
            f = vig[(dy2 + col2[x]) >> 9]
            o = orow + x * 3
            out[o] = int(((buf[i0] + buf[i0 + 3] + buf[i1] + buf[i1 + 3]) >> 2) * f)
            out[o + 1] = int(((buf[i0 + 1] + buf[i0 + 4] + buf[i1 + 1] + buf[i1 + 4]) >> 2) * f)
            out[o + 2] = int(((buf[i0 + 2] + buf[i0 + 5] + buf[i1 + 2] + buf[i1 + 5]) >> 2) * f)

    # ---- PNG encode: filter 0 per row, zlib level 6 ----
    raw = bytearray()
    for y in range(H):
        raw.append(0)
        raw += out[y * W * 3:(y + 1) * W * 3]
    comp = zlib.compress(bytes(raw), 6)

    def chunk(typ, payload):
        return (struct.pack(">I", len(payload)) + typ + payload +
                struct.pack(">I", zlib.crc32(typ + payload) & 0xFFFFFFFF))

    png = (b"\x89PNG\r\n\x1a\n" +
           chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)) +
           chunk(b"IDAT", comp) +
           chunk(b"IEND", b""))

    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "entry.png")
    with open(path, "wb") as fh:
        fh.write(png)
    print("wrote %s %d bytes %dx%d" % (path, len(png), W, H))


if __name__ == "__main__":
    main()
