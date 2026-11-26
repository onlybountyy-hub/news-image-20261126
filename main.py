#!/usr/bin/env python3
"""news-image-20261126: front page of THE WORLD TODAY, Thursday 26 November 2026.

Pure Python stdlib. Draws a 1024x1024 newspaper front page procedurally
(vector shapes + a procedural 5x7 bitmap font, no font files, no network,
no third-party packages) and writes entry.png to $MAKEFUN_OUTPUT_DIR
(default "out/"). Fully deterministic: fixed geometry, no randomness,
no timestamps in the output.
"""

import math
import os
import struct
import zlib

W = H = 1024
px = bytearray(W * H * 3)

# ---------------------------------------------------------------- palette
PAPER = (247, 242, 227)
INK = (17, 17, 17)
RED = (163, 22, 33)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)


# ---------------------------------------------------------------- canvas
def fill_rect(x0, y0, x1, y1, color):
    x0 = max(int(x0), 0)
    y0 = max(int(y0), 0)
    x1 = min(int(x1), W)
    y1 = min(int(y1), H)
    if x0 >= x1 or y0 >= y1:
        return
    row = bytes(color) * (x1 - x0)
    for y in range(y0, y1):
        px[y * W * 3 + x0 * 3: y * W * 3 + x1 * 3] = row


def blend_row(y, x0, x1, color, alpha):
    x0 = max(int(x0), 0)
    x1 = min(int(x1), W - 1)
    if x0 > x1 or y < 0 or y >= H:
        return
    r, g, b = color
    base = y * W * 3
    for x in range(x0, x1 + 1):
        i = base + x * 3
        px[i] = int(px[i] + (r - px[i]) * alpha)
        px[i + 1] = int(px[i + 1] + (g - px[i + 1]) * alpha)
        px[i + 2] = int(px[i + 2] + (b - px[i + 2]) * alpha)


def circle(cx, cy, r, color, alpha=1.0):
    for dy in range(-r, r + 1):
        y = cy + dy
        if y < 0 or y >= H:
            continue
        dx = math.isqrt(max(r * r - dy * dy, 0))
        if alpha >= 1.0:
            fill_rect(cx - dx, y, cx + dx + 1, y + 1, color)
        else:
            blend_row(y, cx - dx, cx + dx, color, alpha)


def ellipse(cx, cy, rx, ry, color, alpha=1.0):
    for dy in range(-ry, ry + 1):
        y = cy + dy
        if y < 0 or y >= H:
            continue
        t = 1.0 - (dy * dy) / float(ry * ry)
        dx = int(rx * math.sqrt(max(t, 0.0)))
        if alpha >= 1.0:
            fill_rect(cx - dx, y, cx + dx + 1, y + 1, color)
        else:
            blend_row(y, cx - dx, cx + dx, color, alpha)


def polygon(points, color):
    ys = [p[1] for p in points]
    ymin, ymax = int(min(ys)), int(max(ys))
    n = len(points)
    for y in range(max(ymin, 0), min(ymax, H - 1) + 1):
        xs = []
        for i in range(n):
            x0, y0 = points[i]
            x1, y1 = points[(i + 1) % n]
            if (y0 <= y < y1) or (y1 <= y < y0):
                xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            fill_rect(xs[i], y, xs[i + 1] + 1, y + 1, color)


def thick_line(x0, y0, x1, y1, w, color):
    dx, dy = x1 - x0, y1 - y0
    length = math.hypot(dx, dy)
    if length == 0:
        return
    nx, ny = -dy / length * w / 2.0, dx / length * w / 2.0
    polygon([(x0 + nx, y0 + ny), (x1 + nx, y1 + ny),
             (x1 - nx, y1 - ny), (x0 - nx, y0 - ny)], color)


def vgrad(y0, y1, stops):
    """Vertical gradient; stops = sorted [(y, (r, g, b)), ...]."""
    for y in range(y0, y1):
        if y <= stops[0][0]:
            c = stops[0][1]
        elif y >= stops[-1][0]:
            c = stops[-1][1]
        else:
            c = stops[-1][1]
            for i in range(len(stops) - 1):
                ya, ca = stops[i]
                yb, cb = stops[i + 1]
                if ya <= y <= yb:
                    t = (y - ya) / float(max(yb - ya, 1))
                    c = tuple(int(ca[k] + (cb[k] - ca[k]) * t) for k in range(3))
                    break
        fill_rect(0, y, W, y + 1, c)


# ---------------------------------------------------------------- 5x7 font
FONT = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01111", "10000", "10000", "10000", "10000", "10000", "01111"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01111", "10000", "10000", "10111", "10001", "10001", "01110"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("11111", "00100", "00100", "00100", "00100", "00100", "11111"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "11001", "10101", "10011", "10011", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    '0': ("01110", "10011", "10101", "11001", "10001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    '3': ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00010", "00100", "00100", "00100"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ',': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    '.': ("00000", "00000", "00000", "00000", "00000", "00000", "01100"),
    ':': ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '-': ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    '%': ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
}


def text_width(s, scale):
    return len(s) * 6 * scale - scale


def draw_text(s, y, scale, color, cx=None, x=None):
    """Draw uppercase text; centre on cx if given, else start at x."""
    if cx is not None:
        x = cx - text_width(s, scale) // 2
    for ci, ch in enumerate(s):
        glyph = FONT[ch]
        gx = x + ci * 6 * scale
        for r, row in enumerate(glyph):
            for c, bit in enumerate(row):
                if bit == '1':
                    fill_rect(gx + c * scale, y + r * scale,
                              gx + (c + 1) * scale, y + (r + 1) * scale, color)


# ---------------------------------------------------------------- scene
def flame_tongue(cx, base_y, height, width, color, lean=0):
    polygon([
        (cx - width // 2, base_y),
        (cx - int(width * 0.35), base_y - int(height * 0.55)),
        (cx - int(width * 0.10), base_y - int(height * 0.78)),
        (cx + lean, base_y - height),
        (cx + int(width * 0.28), base_y - int(height * 0.68)),
        (cx + int(width * 0.42), base_y - int(height * 0.42)),
        (cx + width // 2, base_y),
    ], color)


def draw_hero():
    # Night sky, fire glow near the horizon.
    vgrad(158, 522, [
        (158, (13, 21, 38)),
        (300, (30, 34, 51)),
        (420, (74, 42, 32)),
        (522, (138, 59, 18)),
    ])
    # Distant city silhouette.
    for bx, bw, bh in [(0, 90, 26), (95, 60, 40), (160, 120, 22), (285, 70, 48),
                       (360, 110, 30), (700, 80, 44), (785, 130, 26),
                       (920, 104, 38)]:
        fill_rect(bx, 522 - bh, bx + bw, 522, (20, 16, 12))
    # Road.
    fill_rect(0, 522, W, 640, (31, 31, 31))
    thick_line(150, 522, 40, 640, 4, (200, 200, 190))
    thick_line(874, 522, 984, 640, 4, (200, 200, 190))
    # Perspective centre dashes, growing toward the viewer.
    for i, y in enumerate(range(526, 640, 16)):
        wdt = 5 + i
        fill_rect(512 - wdt // 2, y, 512 + wdt // 2, y + 9, (214, 178, 60))

    # Fire glow on the road and behind the flames.
    ellipse(540, 600, 230, 46, (255, 122, 26), 0.28)
    ellipse(540, 470, 230, 130, (255, 122, 26), 0.22)

    # --- tanker truck (silhouette against the fire) ---
    ellipse(545, 562, 200, 14, BLACK, 0.45)  # ground shadow
    # tank body
    fill_rect(400, 478, 650, 545, (199, 203, 208))
    circle(400, 511, 33, (199, 203, 208))
    circle(650, 511, 33, (199, 203, 208))
    fill_rect(400, 478, 650, 490, (233, 235, 237))   # top highlight
    fill_rect(400, 530, 650, 545, (135, 140, 145))   # bottom shade
    # cab
    fill_rect(650, 492, 712, 545, (38, 40, 44))
    fill_rect(668, 500, 700, 520, (62, 90, 112))     # windshield
    fill_rect(700, 530, 712, 545, (17, 17, 17))
    # wheels
    for wx in (440, 600, 680):
        circle(wx, 548, 16, (10, 10, 10))
        circle(wx, 548, 6, (120, 124, 128))

    # --- flames engulfing the tanker (non-graphic: fire, smoke, light) ---
    for cx, h, w, lean in [(430, 150, 70, -8), (500, 195, 82, 4),
                           (570, 168, 76, 10), (632, 132, 60, 14)]:
        flame_tongue(cx, 505, h, w, (214, 58, 18), lean)
    for cx, h, w, lean in [(452, 132, 55, -4), (520, 162, 62, 2),
                           (592, 136, 56, 8)]:
        flame_tongue(cx, 505, h, w, (240, 122, 26), lean)
    for cx, h, w in [(472, 100, 40), (532, 126, 46), (592, 96, 38)]:
        flame_tongue(cx, 505, h, w, (255, 201, 60))
    # embers
    for ex, ey, er in [(470, 330, 4), (540, 300, 5), (610, 330, 4),
                       (505, 360, 3), (575, 290, 3)]:
        circle(ex, ey, er, (255, 190, 80))

    # --- smoke rising ---
    for sx, sy, sr, sc, al in [
            (455, 335, 42, (64, 64, 64), 0.50),
            (500, 300, 50, (78, 78, 78), 0.45),
            (545, 318, 46, (60, 60, 60), 0.50),
            (600, 275, 52, (82, 82, 82), 0.45),
            (645, 300, 40, (66, 66, 66), 0.50),
            (490, 235, 48, (70, 70, 70), 0.50),
            (560, 215, 50, (80, 80, 80), 0.45),
            (620, 195, 44, (64, 64, 64), 0.50),
            (530, 165, 42, (74, 74, 74), 0.45),
            (585, 140, 36, (66, 66, 66), 0.50)]:
        circle(sx, sy, sr, sc, al)

    # --- emergency vehicle + flashing lights (left), glow (right) ---
    fill_rect(150, 520, 262, 556, (16, 20, 24))
    fill_rect(185, 512, 225, 520, (200, 30, 30))
    fill_rect(205, 512, 225, 520, (30, 80, 220))
    circle(195, 516, 48, (220, 40, 40), 0.16)
    circle(215, 516, 48, (50, 90, 230), 0.16)
    fill_rect(800, 525, 900, 556, (16, 20, 24))
    circle(830, 530, 44, (220, 40, 40), 0.13)
    circle(870, 530, 44, (50, 90, 230), 0.13)

    # --- headline bar ---
    fill_rect(0, 640, W, 725, BLACK)
    draw_text("TANKER FIRE KILLS", 648, 5, WHITE, cx=512)
    draw_text("AT LEAST 30 NEAR CAIRO", 688, 5, WHITE, cx=512)


def card_border(x0, y0, x1, y1):
    fill_rect(x0, y0, x1, y0 + 3, INK)
    fill_rect(x0, y1 - 3, x1, y1, INK)
    fill_rect(x0, y0, x0 + 3, y1, INK)
    fill_rect(x1 - 3, y0, x1, y1, INK)


def draw_card_a():
    # BepiColombo reaches Mercury.
    x0, x1, y0, y1 = 16, 336, 725, 950
    fill_rect(x0, y0, x1, y1, WHITE)
    card_border(x0, y0, x1, y1)
    fill_rect(x0 + 3, y0 + 3, x1 - 3, 856, (11, 16, 38))
    for sx, sy in [(50, 745), (90, 770), (300, 745), (315, 800), (60, 830),
                   (280, 835), (120, 745), (200, 840)]:
        fill_rect(sx, sy, sx + 3, sy + 3, WHITE)
    # Mercury with craters.
    circle(176, 792, 46, (181, 173, 160))
    for cx, cy, cr in [(160, 778, 7), (192, 800, 9), (168, 812, 5),
                       (190, 772, 5), (150, 796, 6)]:
        circle(cx, cy, cr, (138, 130, 120))
    # Spacecraft with solar panels, on a dashed trajectory.
    for t in range(0, 11):
        ax = 268 - t * 8
        ay = 752 + t * 3 + t * t // 6
        circle(ax, ay, 2, WHITE)
    fill_rect(232, 750, 258, 758, (46, 95, 163))
    fill_rect(278, 750, 304, 758, (46, 95, 163))
    fill_rect(258, 748, 278, 760, (216, 221, 226))
    circle(268, 744, 4, (216, 221, 226))
    draw_text("BEPICOLOMBO", 863, 3, INK, cx=176)
    draw_text("REACHES MERCURY", 889, 3, INK, cx=176)
    draw_text("AFTER 8-YEAR TRIP", 918, 2, (68, 68, 68), cx=176)


def draw_card_b():
    # Nvidia: Huang resigns, shares -5%.
    x0, x1, y0, y1 = 352, 672, 725, 950
    fill_rect(x0, y0, x1, y1, WHITE)
    card_border(x0, y0, x1, y1)
    fill_rect(x0 + 3, y0 + 3, x1 - 3, 856, (251, 247, 236))
    for gy in (752, 782, 812, 842):
        fill_rect(x0 + 18, gy, x1 - 18, gy + 2, (221, 213, 194))
    pts = [(370, 758), (430, 744), (480, 770), (540, 800), (600, 790),
           (650, 836)]
    for i in range(len(pts) - 1):
        thick_line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1],
                   5, (192, 57, 43))
    for px_, py_ in pts:
        circle(px_, py_, 5, (192, 57, 43))
    polygon([(616, 792), (652, 792), (634, 830)], (192, 57, 43))
    draw_text("HUANG RESIGNS", 863, 3, INK, cx=512)
    draw_text("NVIDIA -5%", 889, 3, INK, cx=512)
    draw_text("AMID SPY PROBE", 918, 2, (68, 68, 68), cx=512)


def draw_card_c():
    # Democrats retake the US Congress.
    x0, x1, y0, y1 = 688, 1008, 725, 950
    fill_rect(x0, y0, x1, y1, WHITE)
    card_border(x0, y0, x1, y1)
    fill_rect(x0 + 3, y0 + 3, x1 - 3, 856, (168, 196, 222))
    fill_rect(x0 + 3, 830, x1 - 3, 856, (122, 154, 91))
    # Capitol dome (flattened ellipse, not a ball).
    ellipse(848, 800, 58, 42, WHITE)
    fill_rect(790, 800, 906, 830, WHITE)
    fill_rect(800, 790, 896, 800, WHITE)
    fill_rect(842, 750, 854, 758, WHITE)
    thick_line(848, 758, 848, 720, 3, INK)
    fill_rect(848, 722, 868, 732, (192, 57, 43))
    # Columns.
    for cx in range(776, 922, 26):
        fill_rect(cx, 800, cx + 10, 830, (178, 178, 178))
    fill_rect(760, 830, 936, 836, (200, 200, 200))
    draw_text("DEMOCRATS RETAKE", 863, 3, INK, cx=848)
    draw_text("CONGRESS", 889, 3, INK, cx=848)
    draw_text("2026 MIDTERMS", 918, 2, (68, 68, 68), cx=848)


def draw_page():
    fill_rect(0, 0, W, H, PAPER)
    # Masthead.
    draw_text("THE WORLD TODAY", 20, 9, INK, cx=512)
    fill_rect(0, 90, W, 93, INK)
    fill_rect(0, 97, W, 98, INK)
    # Date band — the day must be unmistakable.
    fill_rect(0, 106, W, 158, RED)
    draw_text("THURSDAY, 26 NOVEMBER 2026", 114, 5, WHITE, cx=512)
    # Hero + cards + strip.
    draw_hero()
    draw_card_a()
    draw_card_b()
    draw_card_c()
    fill_rect(0, 950, W, H, BLACK)
    draw_text("RUSSIA'S OWN FIGURES: NEARLY 500,000 LOST IN UKRAINE WAR",
              982, 2, WHITE, cx=512)


# ---------------------------------------------------------------- PNG out
def png_chunk(typ, data):
    out = struct.pack(">I", len(data)) + typ + data
    out += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
    return out


def write_png(path):
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    raw = b"".join(b"\x00" + bytes(px[y * W * 3:(y + 1) * W * 3])
                   for y in range(H))
    png = (b"\x89PNG\r\n\x1a\n"
           + png_chunk(b"IHDR", ihdr)
           + png_chunk(b"IDAT", zlib.compress(raw, 9))
           + png_chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "out"
    os.makedirs(outdir, exist_ok=True)
    draw_page()
    size = write_png(os.path.join(outdir, "entry.png"))
    print("wrote %s (%d bytes)" % (os.path.join(outdir, "entry.png"), size))


if __name__ == "__main__":
    main()
