#!/usr/bin/env python3
"""The picture that tastes of one ingredient: a tall stack of golden pancakes.

Procedural drawing, no assets, no network. Writes /output/entry.png (1024x1024).
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter

S = 2  # supersample factor
W = H = 1024
W2, H2 = W * S, H * S

random.seed(20261122)


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def ell(d, cx, cy, rx, ry, fill):
    d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=fill)


def main():
    img = Image.new("RGB", (W2, H2), (250, 233, 205))
    d = ImageDraw.Draw(img, "RGBA")

    # ---- warm background: radial glow + soft vignette ----
    for r in range(720, 0, -6):
        t = r / 720.0
        col = lerp((252, 236, 208), (232, 196, 148), t)
        ell(d, W2 // 2, H2 // 2 - 60, r, r, col)
    # wooden table band at bottom
    d.rectangle([0, H2 - 300, W2, H2], fill=(176, 124, 78))
    d.rectangle([0, H2 - 300, W2, H2 - 292], fill=(150, 102, 60))
    for i in range(14):
        y = H2 - 280 + i * 20
        d.line([0, y, W2, y], fill=(166, 116, 72), width=3)
    # soft light from upper left
    d.ellipse([-300, -300, 900, 500], fill=(255, 248, 225, 70))

    cx = W2 // 2
    plate_cy = 1560
    # ---- soft shadow under plate ----
    d.ellipse([cx - 700, plate_cy - 60, cx + 700, plate_cy + 150], fill=(120, 70, 35, 90))
    # ---- plate ----
    ell(d, cx, plate_cy, 760, 190, (244, 238, 226))
    ell(d, cx, plate_cy - 14, 700, 172, (250, 246, 236))
    ell(d, cx, plate_cy - 20, 560, 138, (236, 228, 210))
    d.ellipse([cx - 560, plate_cy - 158, cx + 560, plate_cy + 118],
              outline=(205, 192, 168), width=5)

    # ---- pancake stack ----
    # each pancake: side (golden-brown), top (lighter golden), toasted speckles
    layers = [
        (1180, 168, 205, 138, 62),
        (1030, 158, 192, 128, 54),
        (880, 148, 180, 118, 46),
        (730, 138, 168, 108, 38),
        (580, 128, 158, 98, 30),
    ]
    # draw bottom-up; pancake i sits at base_y - i*stack_step
    base_top = 1380
    step = 150
    for i, (cy_top, rx, ry, side_rx, side_h) in enumerate(layers):
        top_y = base_top - i * step
        side_y = top_y + side_h
        # side (golden brown, slightly darker at bottom edge)
        d.ellipse([cx - rx, top_y - ry + side_h, cx + rx, top_y + ry + side_h],
                  fill=(196, 128, 52))
        d.ellipse([cx - rx, top_y - ry + side_h, cx + rx, top_y + ry + side_h - 26],
                  fill=(212, 144, 62))
        # top surface (warm golden)
        ell(d, cx, top_y, rx, ry, (232, 176, 96))
        # toasted speckles on top
        for _ in range(90):
            a = random.uniform(0, 2 * math.pi)
            rr = random.uniform(0, 0.85)
            px = cx + math.cos(a) * rx * rr
            py = top_y + math.sin(a) * ry * rr
            r = random.uniform(3, 11)
            col = random.choice([(198, 128, 52), (214, 148, 66), (188, 116, 44)])
            d.ellipse([px - r, py - r * 0.55, px + r, py + r * 0.55], fill=col + (140,))

    # ---- maple syrup: glossy pool on top + drips down the stack ----
    syrup = (146, 74, 18)
    syrup_hi = (198, 118, 38)
    top_y = base_top - 4 * step
    ell(d, cx, top_y, 128, 92, syrup)
    ell(d, cx - 18, top_y - 14, 88, 58, syrup_hi)
    # drips
    drips = [(-150, 210, 26), (-88, 320, 30), (-10, 260, 24), (70, 360, 30),
             (140, 240, 24), (190, 170, 20), (-210, 120, 20)]
    for dx, length, w in drips:
        x0 = cx + dx
        d.rounded_rectangle([x0 - w, top_y - 20, x0 + w, top_y + length],
                            radius=w, fill=syrup)
        ell(d, x0, top_y + length, w + 4, w + 10, syrup)
        d.rounded_rectangle([x0 - w + 8, top_y - 10, x0 - w + 16, top_y + length - 30],
                            radius=6, fill=syrup_hi)
    # syrup pool on plate
    ell(d, cx + 420, plate_cy - 40, 180, 46, syrup)
    ell(d, cx + 400, plate_cy - 52, 120, 28, syrup_hi)

    # ---- melting butter pat on top ----
    bx, by = cx - 30, top_y - 52
    d.rounded_rectangle([bx - 95, by - 62, bx + 95, by + 22], radius=22, fill=(255, 222, 110))
    d.rounded_rectangle([bx - 95, by - 62, bx + 95, by - 18], radius=22, fill=(255, 236, 150))
    d.line([bx - 70, by - 40, bx + 70, by - 40], fill=(255, 246, 190), width=8)
    # butter melt dripping off the edge
    d.rounded_rectangle([bx + 55, by + 10, bx + 95, by + 78], radius=18, fill=(255, 222, 110))
    ell(d, bx + 75, by + 78, 24, 26, (255, 222, 110))

    # ---- blueberries on top and plate ----
    def blueberry(x, y, r):
        ell(d, x, y, r, r, (52, 68, 138))
        ell(d, x - r * 0.3, y - r * 0.35, r * 0.55, r * 0.45, (96, 118, 190))
        d.ellipse([x - r * 0.18, y - r * 0.9, x + r * 0.18, y - r * 0.45],
                  fill=(30, 40, 90))
    blueberry(cx + 120, top_y - 30, 52)
    blueberry(cx + 165, top_y + 18, 44)
    blueberry(cx - 170, top_y + 8, 46)
    blueberry(cx - 470, plate_cy - 70, 52)
    blueberry(cx - 380, plate_cy - 46, 44)
    blueberry(cx + 480, plate_cy - 74, 46)

    # ---- strawberry halves on the plate ----
    def strawberry(x, y, r, flip=False):
        # red half-berry, cut side up: pale pink flesh with seeds
        d.pieslice([x - r, y - r, x + r, y + r], 180, 360, fill=(214, 58, 64))
        d.ellipse([x - r * 0.82, y - r * 0.15, x + r * 0.82, y + r * 0.8],
                  fill=(246, 190, 186))
        for _ in range(26):
            a = random.uniform(-1.2, 1.2)
            rr = random.uniform(0.15, 0.7)
            px = x + math.sin(a) * r * rr * 0.9
            py = y + r * 0.35 - abs(math.cos(a)) * r * rr * 0.3
            d.ellipse([px - 4, py - 4, px + 4, py + 4], fill=(232, 120, 110))
        d.ellipse([x - r * 0.2, y + r * 0.55, x + r * 0.2, y + r * 0.8],
                  fill=(246, 190, 186))
    strawberry(cx + 330, plate_cy - 46, 84)
    strawberry(cx - 540, plate_cy - 66, 70)

    # ---- powdered sugar dusting on top pancake ----
    for _ in range(160):
        a = random.uniform(0, 2 * math.pi)
        rr = random.uniform(0.5, 0.95)
        px = cx + math.cos(a) * 128 * rr
        py = top_y + math.sin(a) * 92 * rr
        d.ellipse([px - 3, py - 2, px + 3, py + 2], fill=(255, 250, 240, 200))

    # ---- steam wisps above the stack (4 wisps, taller, softer glow) ----
    steam = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
    ds = ImageDraw.Draw(steam)
    for sx, phase, amp in [(cx - 220, 0.6, 52), (cx - 140, 0.0, 46),
                           (cx + 40, 1.4, 60), (cx + 210, 2.6, 42)]:
        pts = []
        for t in range(0, 121):
            yy = top_y - 150 - t * 5.4
            xx = sx + math.sin(t / 12.0 + phase) * amp * (t / 100.0 + 0.3)
            pts.append((xx, yy))
        ds.line(pts, fill=(255, 255, 255, 130), width=30, joint="curve")
    steam = steam.filter(ImageFilter.GaussianBlur(20))
    img = Image.alpha_composite(img.convert("RGBA"), steam).convert("RGB")

    # ---- honey-drizzle highlight across the top syrup pool ----
    d2 = ImageDraw.Draw(img, "RGBA")
    for k in range(5):
        x0 = cx - 96 + k * 40
        d2.arc([x0 - 26, top_y - 58, x0 + 26, top_y + 34], 200, 340,
               fill=(255, 214, 110, 190), width=7)
    d2.ellipse([cx - 58, top_y - 26, cx - 6, top_y - 2], fill=(255, 226, 140, 170))

    # ---- warmer plate rim light + deeper pancake-edge browning ----
    rim = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
    dr = ImageDraw.Draw(rim)
    # golden rim light hugging the lower edge of the plate
    dr.arc([cx - 760, plate_cy - 190, cx + 760, plate_cy + 190], 15, 165,
           fill=(255, 196, 110, 150), width=16)
    dr.arc([cx - 700, plate_cy - 172, cx + 700, plate_cy + 172], 25, 155,
           fill=(255, 220, 150, 110), width=8)
    # deeper toasted browning around the edge of each pancake top
    for i, (cy_top, rx, ry, side_rx, side_h) in enumerate(layers):
        top_y_i = base_top - i * step
        dr.ellipse([cx - rx, top_y_i - ry, cx + rx, top_y_i + ry],
                   outline=(172, 100, 34, 150), width=14)
    rim = rim.filter(ImageFilter.GaussianBlur(6))
    img = Image.alpha_composite(img.convert("RGBA"), rim).convert("RGB")

    # ---- soft vignette to lead the eye to the dish ----
    vig = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
    dv = ImageDraw.Draw(vig)
    for r in range(1500, 700, -10):
        t = (1500 - r) / 800.0
        a = int(70 * t * t)
        dv.ellipse([cx - r, H2 // 2 - 60 - r, cx + r, H2 // 2 - 60 + r],
                   outline=(60, 30, 10, a), width=10)
    vig = vig.filter(ImageFilter.GaussianBlur(30))
    img = Image.alpha_composite(img.convert("RGBA"), vig).convert("RGB")

    # ---- downscale, save ----
    img = img.resize((W, H), Image.LANCZOS)
    os.makedirs("/output", exist_ok=True)
    img.save("/output/entry.png", optimize=True)
    print("wrote /output/entry.png", img.size)


if __name__ == "__main__":
    main()
