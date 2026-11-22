"""Pancake stack — a warm breakfast-table picture, drawn from scratch.

Pure standard library only. The picture is built in a 2048x2048 RGB buffer
with small scanline helpers, downsampled 2x2 to 1024x1024, and encoded as a
PNG by hand (zlib + struct chunk framing). No assets, no network.
"""

import math
import os
import random
import struct
import zlib

random.seed(20261122)

BIG = 2048          # working buffer size (2x the final picture)
FINAL = 1024        # output picture size
W = BIG


def _clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


class Canvas:
    """A flat RGB byte buffer with scanline drawing helpers."""

    def __init__(self, size):
        self.size = size
        self.px = bytearray(size * size * 3)

    def run(self, y, x0, x1, color):
        """Fill a horizontal run of pixels on row y (clipped)."""
        if y < 0 or y >= self.size:
            return
        x0 = _clamp(x0, 0, self.size)
        x1 = _clamp(x1, 0, self.size)
        if x1 <= x0:
            return
        r, g, b = color
        base = (y * self.size + x0) * 3
        span = (x1 - x0) * 3
        self.px[base:base + span] = bytes((r, g, b)) * (x1 - x0)

    def rect(self, x0, y0, x1, y1, color):
        for y in range(max(0, y0), min(self.size, y1)):
            self.run(y, x0, x1, color)

    def ellipse(self, cx, cy, rx, ry, color):
        """Fill an ellipse by scanning rows and using the circle equation."""
        if rx <= 0 or ry <= 0:
            return
        for y in range(max(0, cy - ry), min(self.size, cy + ry + 1)):
            t = (y - cy) / ry
            if t < -1.0 or t > 1.0:
                continue
            half = int(rx * math.sqrt(1.0 - t * t))
            self.run(y, cx - half, cx + half + 1, color)

    def disc(self, cx, cy, radius, color):
        self.ellipse(cx, cy, radius, radius, color)

    def rounded_rect(self, x0, y0, x1, y1, corner, color):
        """Rounded rectangle via per-row insets near the top/bottom."""
        for y in range(max(0, y0), min(self.size, y1)):
            inset = 0
            if y - y0 < corner:
                dy = corner - (y - y0)
                inset = corner - int(math.sqrt(max(0, corner * corner - dy * dy)))
            elif y1 - 1 - y < corner:
                dy = corner - (y1 - 1 - y)
                inset = corner - int(math.sqrt(max(0, corner * corner - dy * dy)))
            self.run(y, x0 + inset, x1 - inset, color)

    def arc_chain(self, cx, cy, radius, a0, a1, steps, dot_r, color):
        """Draw an arc as a chain of small discs."""
        for i in range(steps + 1):
            a = a0 + (a1 - a0) * i / steps
            self.disc(int(cx + radius * math.cos(a)),
                      int(cy + radius * math.sin(a)), dot_r, color)

    def half_ellipse(self, cx, cy, rx, ry, color):
        """Fill only the lower half of an ellipse (flat top edge)."""
        for y in range(max(0, cy), min(self.size, cy + ry + 1)):
            t = (y - cy) / ry
            if t < -1.0 or t > 1.0:
                continue
            half = int(rx * math.sqrt(1.0 - t * t))
            self.run(y, cx - half, cx + half + 1, color)


def blend(a, b, t):
    """Linear blend between two RGB triples."""
    return (int(a[0] + (b[0] - a[0]) * t),
            int(a[1] + (b[1] - a[1]) * t),
            int(a[2] + (b[2] - a[2]) * t))


# --- palette (my own numbers) ---
GLOW_EDGE = (74, 38, 14)
GLOW_MID = (176, 108, 42)
GLOW_CORE = (255, 214, 138)
WOOD = (122, 74, 34)
WOOD_DARK = (96, 56, 24)
WOOD_LIGHT = (148, 94, 46)
SHADOW = (52, 30, 12)
PLATE_RIM = (214, 202, 186)
PLATE = (248, 244, 236)
PANCAKE_SIDE = (176, 106, 34)
PANCAKE_SIDE_DARK = (146, 84, 24)
PANCAKE_TOP = (238, 184, 96)
PANCAKE_TOP_LIGHT = (246, 204, 128)
TOAST = (150, 88, 26)
SYRUP = (176, 92, 8)
SYRUP_LIGHT = (232, 148, 32)
SYRUP_DARK = (128, 62, 4)
BUTTER = (252, 226, 120)
BUTTER_EDGE = (232, 196, 82)
BERRY = (38, 48, 118)
BERRY_LIGHT = (92, 108, 196)
STRAW_RED = (206, 52, 64)
STRAW_FLESH = (250, 178, 172)
SEED = (252, 232, 150)
SUGAR = (255, 252, 246)
STEAM = (255, 246, 228)


def draw_background(cv):
    """Warm radial glow: concentric circles stepping dark -> light."""
    cx, cy = 1024, 860
    steps = 42
    for i in range(steps, -1, -1):
        t = i / steps
        radius = int(300 + (1520 - 300) * t)
        if t < 0.55:
            col = blend(GLOW_EDGE, GLOW_MID, t / 0.55)
        else:
            col = blend(GLOW_MID, GLOW_CORE, (t - 0.55) / 0.45)
        cv.ellipse(cx, cy, radius, radius, col)


def draw_table(cv):
    """Wooden table band across the bottom with plank seams and grain."""
    cv.rect(0, 1490, BIG, BIG, WOOD)
    for y in (1620, 1760, 1900):
        cv.rect(0, y, BIG, y + 7, WOOD_DARK)
    for _ in range(90):
        gx = random.randint(0, BIG - 260)
        gy = random.randint(1500, BIG - 12)
        gl = random.randint(90, 260)
        cv.run(gy, gx, gx + gl, WOOD_LIGHT if random.random() < 0.5 else WOOD_DARK)
    # soft top edge highlight where the table meets the wall
    cv.rect(0, 1490, BIG, 1498, WOOD_LIGHT)


def draw_plate(cv):
    """Soft shadow, then the round white plate with a rim ring."""
    cv.ellipse(1024, 1560, 700, 118, SHADOW)
    cv.ellipse(1024, 1420, 660, 178, PLATE_RIM)
    cv.ellipse(1024, 1412, 628, 164, PLATE)
    cv.arc_chain(1024, 1412, 560, 0.15, math.pi - 0.15, 90, 5, (228, 220, 206))


def draw_syrup_pool_on_plate(cv):
    cv.ellipse(1024, 1510, 430, 58, SYRUP)
    cv.ellipse(1024, 1504, 380, 46, SYRUP_LIGHT)
    cv.ellipse(1024, 1500, 300, 34, SYRUP)


PANCAKES = [
    # (top_y, half_width) bottom -> top
    (1330, 468),
    (1236, 436),
    (1142, 402),
    (1048, 368),
    (954, 332),
]


def draw_pancake(cv, top_y, rx):
    """One pancake: golden-brown side, lighter toasted top, speckles."""
    side_cy = top_y + 58
    cv.ellipse(1024, side_cy, rx, 62, PANCAKE_SIDE)
    cv.ellipse(1024, side_cy + 26, rx - 6, 40, PANCAKE_SIDE_DARK)
    cv.ellipse(1024, top_y, rx, 52, PANCAKE_TOP)
    cv.ellipse(1024, top_y - 6, rx - 26, 40, PANCAKE_TOP_LIGHT)
    # toasted speckles scattered inside the top ellipse
    for _ in range(46):
        ang = random.random() * 2.0 * math.pi
        rr = math.sqrt(random.random())
        sx = int(1024 + (rx - 34) * rr * math.cos(ang))
        sy = int(top_y - 4 + 38 * rr * math.sin(ang))
        cv.disc(sx, sy, random.randint(3, 7), TOAST)


def draw_stack(cv):
    for top_y, rx in PANCAKES:
        draw_pancake(cv, top_y, rx)


def draw_drip(cv, x, y0, length, width):
    """A syrup drip: vertical rounded bar with a rounded end + gloss."""
    cv.rect(x - width // 2, y0, x + width // 2, y0 + length, SYRUP)
    cv.disc(x, y0 + length, width // 2, SYRUP)
    cv.disc(x, y0, width // 2, SYRUP)
    for yy in range(y0 + 10, y0 + length - 6, 3):
        cv.run(yy, x - width // 2 + 5, x - width // 2 + 8, SYRUP_LIGHT)


def draw_syrup(cv):
    """Glossy pool on the top pancake, drips down the stack, gloss arcs."""
    top_y, rx = PANCAKES[-1]
    cv.ellipse(1024, top_y - 2, rx - 42, 44, SYRUP)
    cv.ellipse(1024, top_y - 8, rx - 78, 34, SYRUP_LIGHT)
    cv.ellipse(1024, top_y - 4, rx - 130, 26, SYRUP)
    cv.arc_chain(1024, top_y - 6, rx - 120, math.pi * 1.08, math.pi * 1.92, 40, 7,
                 SYRUP_LIGHT)
    # drips running down the stack sides
    draw_drip(cv, 700, top_y + 6, 210, 30)
    draw_drip(cv, 806, top_y + 2, 330, 26)
    draw_drip(cv, 1330, top_y + 4, 260, 28)
    draw_drip(cv, 1422, top_y + 8, 150, 24)
    draw_drip(cv, 1024, top_y + 10, 120, 26)


def draw_butter(cv):
    """Melting square pat of butter on top, with a drip off its edge."""
    cv.rounded_rect(950, 862, 1110, 946, 22, BUTTER_EDGE)
    cv.rounded_rect(958, 868, 1102, 938, 18, BUTTER)
    cv.rect(972, 880, 1090, 892, (255, 240, 160))
    # butter melting: a drip sliding off the right edge
    cv.rect(1096, 920, 1120, 968, BUTTER)
    cv.disc(1108, 968, 12, BUTTER)
    cv.disc(1108, 968, 6, BUTTER_EDGE)


def draw_blueberry(cv, cx, cy, r):
    cv.disc(cx, cy, r, BERRY)
    cv.disc(cx - r // 3, cy - r // 3, r // 2, BERRY_LIGHT)
    cv.disc(cx + r // 4, cy + r // 4, r // 5, (20, 26, 70))
    # little crown dent on top
    cv.disc(cx, cy - r + 6, r // 4, (16, 20, 58))


def draw_strawberry_half(cv, cx, cy):
    """Halved strawberry on the plate: red rim, pale cut flesh, seeds."""
    cv.half_ellipse(cx, cy - 46, 96, 104, STRAW_RED)
    cv.half_ellipse(cx, cy - 40, 80, 88, STRAW_FLESH)
    cv.half_ellipse(cx, cy - 40, 58, 64, (252, 196, 188))
    for _ in range(16):
        ang = random.random() * math.pi  # lower half only
        rr = math.sqrt(random.random())
        sx = int(cx + 62 * rr * math.cos(ang))
        sy = int(cy - 40 + 66 * rr * math.sin(ang))
        cv.disc(sx, sy, 4, SEED)
    # leafy top
    cv.disc(cx - 26, cy - 44, 12, (46, 120, 52))
    cv.disc(cx + 26, cy - 44, 12, (46, 120, 52))
    cv.disc(cx, cy - 52, 12, (58, 138, 60))


def draw_sugar(cv):
    top_y, rx = PANCAKES[-1]
    for _ in range(150):
        ang = random.random() * 2.0 * math.pi
        rr = math.sqrt(random.random())
        sx = int(1024 + (rx - 60) * rr * math.cos(ang))
        sy = int(top_y - 6 + 36 * rr * math.sin(ang))
        cv.disc(sx, sy, random.randint(2, 4), SUGAR)


def draw_steam(cv):
    """Thin wavy steam wisps: chains of pale discs rising above the stack."""
    for base_x, phase, amp in ((880, 0.0, 34), (1024, 1.7, 44),
                              (1170, 3.4, 30), (960, 4.6, 26)):
        y = 900
        step = 0
        while y > 240:
            sway = int(amp * math.sin(y / 170.0 + phase))
            r = 16 + int(12 * math.sin(step * 0.55) ** 2)
            cv.disc(base_x + sway, y, r, STEAM)
            y -= 34
            step += 1


def downsample(cv):
    """2x2 average down to 1024x1024, applying a corner vignette.

    Vignette factors come from a lookup table indexed by normalized
    squared distance from the centre, so the per-pixel work stays cheap.
    """
    table = []
    for i in range(1025):
        t = i / 1024.0
        table.append(1.0 - 0.30 * (t ** 1.6))
    out = bytearray(FINAL * FINAL * 3)
    src = cv.px
    sw = BIG * 3
    for oy in range(FINAL):
        dy = oy - FINAL // 2
        sy = oy * 2
        orow = oy * FINAL * 3
        srow0 = sy * sw
        srow1 = srow0 + sw
        for ox in range(FINAL):
            dx = ox - FINAL // 2
            d2 = (dx * dx + dy * dy) * 1024 // (512 * 512 * 2)
            if d2 > 1024:
                d2 = 1024
            f = table[d2]
            sx = ox * 2 * 3
            i00 = srow0 + sx
            i01 = i00 + 3
            i10 = srow1 + sx
            i11 = i10 + 3
            o = orow + ox * 3
            out[o] = int((src[i00] + src[i01] + src[i10] + src[i11]) * 0.25 * f)
            out[o + 1] = int((src[i00 + 1] + src[i01 + 1] + src[i10 + 1] + src[i11 + 1]) * 0.25 * f)
            out[o + 2] = int((src[i00 + 2] + src[i01 + 2] + src[i10 + 2] + src[i11 + 2]) * 0.25 * f)
    return bytes(out)


def encode_png(rgb, size):
    """Hand-rolled PNG: signature, IHDR, zlib IDAT, IEND."""
    def chunk(tag, payload):
        return (struct.pack(">I", len(payload)) + tag + payload +
                struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)
    stride = size * 3
    raw = bytearray()
    for y in range(size):
        raw.append(0)  # filter: none
        raw += rgb[y * stride:(y + 1) * stride]
    data = zlib.compress(bytes(raw), 6)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) +
            chunk(b"IDAT", data) + chunk(b"IEND", b""))


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")

    cv = Canvas(BIG)
    draw_background(cv)
    draw_table(cv)
    draw_plate(cv)
    draw_syrup_pool_on_plate(cv)
    draw_stack(cv)
    draw_syrup(cv)
    draw_butter(cv)
    draw_blueberry(cv, 872, 906, 52)
    draw_blueberry(cv, 1176, 898, 48)
    draw_blueberry(cv, 1084, 856, 42)
    draw_blueberry(cv, 636, 1496, 50)
    draw_blueberry(cv, 1448, 1484, 54)
    draw_strawberry_half(cv, 742, 1560)
    draw_strawberry_half(cv, 1330, 1572)
    draw_sugar(cv)
    draw_steam(cv)

    png = encode_png(downsample(cv), FINAL)
    with open(path, "wb") as fh:
        fh.write(png)
    print("wrote %s (%d bytes)" % (path, len(png)))


if __name__ == "__main__":
    main()
