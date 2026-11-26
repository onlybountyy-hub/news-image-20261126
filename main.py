"""news-image-20261126 v2 — one-day world news poster, Thursday 26 November 2026.

Pure Python standard library. Draws a flat editorial newspaper poster
(1024x1024) with a masthead + dateline, one hero story and four cards:

  HERO  US proposes new tariffs on 14 trade partners (NORTH AMERICA / TRADE)
  1     Houthi strike on a Saudi port and the Ras Tanura refinery
        (MIDDLE EAST / CONFLICT)
  2     Pakistan's first astronaut Zeeshan Ali reaches Tiangong on
        Shenzhou-24 (ASIA / SPACE)
  3     EU split over the EUR 45 BN Ukraine loan (EUROPE / POLITICS)
  4     Liverpool beat Club Brugge 3-0 in the Champions League
        (EUROPE / SPORT)

Deterministic: the same bytes on every run. Writes entry.png into
MAKEFUN_OUTPUT_DIR (default "out").
"""

import math
import os
import struct
import sys
import zlib

W = 1024
H = 1024

PAPER = (247, 243, 232)
INK = (20, 20, 20)
RED = (193, 18, 31)
WHITE = (255, 253, 246)
SAND = (239, 227, 200)
SKY = (217, 228, 239)
GREY = (231, 226, 214)
GREEN = (220, 231, 210)
STEEL = (122, 155, 181)

# 5x7 bitmap font. '#' is ink, '.' is clear. All text is set in capitals.
FONT = {
    "A": (" .###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#..##", "#.#.#", "#.#.#", "##..#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "...#.", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    "-": (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    "/": ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    "(": ("...##", "..#..", ".#...", ".#...", ".#...", "..#..", "...##"),
    ")": ("##...", "..#..", "...#.", "...#.", "...#.", "..#..", "##..."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "+": (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    "%": ("##..#", "##.#.", "...#.", "..#..", ".#...", "#.##.", "#..##"),
    "=": (".....", ".....", "#####", ".....", "#####", ".....", "....."),
}


class Img:
    def __init__(self):
        self.px = bytearray(bytes(PAPER) * (W * H))
        self.clip = (0, 0, W - 1, H - 1)

    def set_clip(self, x0, y0, x1, y1):
        self.clip = (max(0, x0), max(0, y0), min(W - 1, x1), min(H - 1, y1))

    def clear_clip(self):
        self.clip = (0, 0, W - 1, H - 1)

    def rect(self, x0, y0, x1, y1, color):
        cx0, cy0, cx1, cy1 = self.clip
        x0 = max(cx0, int(x0))
        y0 = max(cy0, int(y0))
        x1 = min(cx1, int(x1))
        y1 = min(cy1, int(y1))
        if x1 < x0 or y1 < y0:
            return
        row = bytes(color) * (x1 - x0 + 1)
        for y in range(y0, y1 + 1):
            s = (y * W + x0) * 3
            self.px[s:s + len(row)] = row

    def hline(self, x0, x1, y, color):
        self.rect(x0, y, x1, y, color)

    def fill_circle(self, cx, cy, r, color):
        for dy in range(-r, r + 1):
            dx = int(math.sqrt(max(0, r * r - dy * dy)))
            self.hline(cx - dx, cx + dx, cy + dy, color)

    def fill_poly(self, pts, color):
        ys = [p[1] for p in pts]
        n = len(pts)
        for y in range(min(ys), max(ys) + 1):
            xs = []
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    t = (y - y0) / (y1 - y0)
                    xs.append(x0 + t * (x1 - x0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self.hline(int(round(xs[i])), int(round(xs[i + 1])), y, color)

    def thick_line(self, x0, y0, x1, y1, color, w):
        steps = max(abs(x1 - x0), abs(y1 - y0), 1)
        for i in range(steps + 1):
            t = i / steps
            self.fill_circle(round(x0 + (x1 - x0) * t),
                             round(y0 + (y1 - y0) * t), max(1, w // 2), color)

    def outline_rect(self, x0, y0, x1, y1, color, t=3):
        self.rect(x0, y0, x1, y0 + t - 1, color)
        self.rect(x0, y1 - t + 1, x1, y1, color)
        self.rect(x0, y0, x0 + t - 1, y1, color)
        self.rect(x1 - t + 1, y0, x1, y1, color)

    # ---- text ----
    def text_w(self, s, scale, adv=6.0):
        if not s:
            return 0
        return int(round(((len(s) - 1) * adv + 5) * scale))

    def draw_text(self, x, y, s, scale, color, bold=True, adv=6.0):
        cx = float(x)
        for ch in s:
            g = FONT.get(ch)
            if g:
                for r in range(7):
                    row = g[r]
                    for c in range(5):
                        if row[c] == "#":
                            x0 = int(round(cx + c * scale))
                            x1 = int(round(cx + (c + 1) * scale))
                            y0 = int(round(y + r * scale))
                            y1 = int(round(y + (r + 1) * scale))
                            self.rect(x0, y0, x1 - 1, y1 - 1, color)
                            if bold:
                                dx = max(1, int(round(scale * 0.18)))
                                self.rect(x0 + dx, y0, x1 - 1 + dx, y1 - 1, color)
            cx += adv * scale
        return int(round(cx))

    def chip(self, x, y, s, scale, bg, fg):
        w = self.text_w(s, scale) + 20
        h = int(round(7 * scale)) + 10
        self.rect(x, y, x + w - 1, y + h - 1, bg)
        self.draw_text(x + 10, y + 5, s, scale, fg, bold=True)
        return w, h


def star(img, cx, cy, r, color):
    img.rect(cx - r, cy - 1, cx + r, cy + 1, color)
    img.rect(cx - 1, cy - r, cx + 1, cy + r, color)


def pentagon(img, cx, cy, r, color):
    pts = []
    for i in range(5):
        a = -math.pi / 2 + i * 2 * math.pi / 5
        pts.append((round(cx + r * math.cos(a)), round(cy + r * math.sin(a))))
    img.fill_poly(pts, color)


# ---------- illustration bands (drawn inside the card's top band) ----------

def band_refinery(img, bx, by):
    img.rect(bx, by, bx + 481, by + 104, SAND)
    img.rect(bx, by + 78, bx + 481, by + 104, INK)  # ground
    mx, my = bx + 368, by + 8
    img.rect(mx + 8, my + 8, mx + 20, my + 72, INK)    # tall tower
    img.rect(mx + 30, my + 26, mx + 40, my + 72, INK)  # short tower
    img.fill_circle(mx + 62, my + 58, 14, INK)         # tank
    img.rect(mx + 48, my + 58, mx + 76, my + 72, INK)  # tank base
    img.fill_circle(mx + 94, my + 62, 10, INK)         # small tank
    img.rect(mx + 84, my + 62, mx + 104, my + 72, INK)
    img.fill_poly([(mx + 9, my + 8), (mx + 19, my + 8), (mx + 14, my - 8)], RED)


def band_space(img, bx, by):
    img.rect(bx, by, bx + 481, by + 104, SKY)
    img.fill_circle(bx + 470, by + 121, 42, STEEL)  # planet arc, bottom right
    mx, my = bx + 368, by + 8
    star(img, mx + 8, my + 12, 4, INK)
    star(img, mx + 96, my + 10, 4, INK)
    star(img, mx + 88, my + 48, 3, INK)
    # rocket, upright, right side
    img.rect(mx + 32, my + 14, mx + 60, my + 68, INK)    # outline
    img.rect(mx + 34, my + 16, mx + 58, my + 66, WHITE)  # body
    img.fill_poly([(mx + 34, my + 16), (mx + 58, my + 16), (mx + 46, my + 2)], RED)
    img.fill_poly([(mx + 34, my + 50), (mx + 34, my + 70), (mx + 24, my + 70)], RED)
    img.fill_poly([(mx + 58, my + 50), (mx + 58, my + 70), (mx + 68, my + 70)], RED)
    img.fill_poly([(mx + 40, my + 70), (mx + 52, my + 70), (mx + 46, my + 86)], RED)
    img.fill_circle(mx + 46, my + 34, 4, INK)  # window


def band_politics(img, bx, by):
    img.rect(bx, by, bx + 481, by + 104, GREY)
    mx, my = bx + 368, by + 8
    img.fill_poly([(mx + 4, my + 30), (mx + 104, my + 30), (mx + 54, my + 10)], INK)
    img.rect(mx + 4, my + 30, mx + 104, my + 38, INK)
    for cx in (mx + 12, mx + 34, mx + 56, mx + 78):
        img.rect(cx, my + 38, cx + 9, my + 82, INK)
    img.rect(mx + 2, my + 86, mx + 106, my + 96, INK)
    crack = [(mx + 54, my + 10), (mx + 48, my + 34), (mx + 60, my + 56),
             (mx + 50, my + 78), (mx + 56, my + 96)]
    for a, b in zip(crack, crack[1:]):
        img.thick_line(a[0], a[1], b[0], b[1], RED, 4)


def band_sport(img, bx, by):
    img.rect(bx, by, bx + 481, by + 104, GREEN)
    mx, my = bx + 368, by + 8
    # goal with net
    img.rect(mx + 6, my + 16, mx + 100, my + 84, INK)
    img.rect(mx + 8, my + 18, mx + 98, my + 82, WHITE)
    for gx in range(mx + 20, mx + 96, 12):
        img.rect(gx, my + 28, gx, my + 82, INK)
    for gy in range(my + 30, my + 82, 12):
        img.rect(mx + 8, gy, mx + 98, gy, INK)
    img.rect(mx + 8, my + 18, mx + 16, my + 84, WHITE)
    img.rect(mx + 90, my + 18, mx + 98, my + 84, WHITE)
    img.rect(mx + 8, my + 18, mx + 98, my + 26, WHITE)
    # ball in front of the goal
    img.fill_circle(mx + 62, my + 74, 18, INK)
    img.fill_circle(mx + 62, my + 74, 16, WHITE)
    pentagon(img, mx + 62, my + 74, 6, INK)
    img.fill_circle(mx + 50, my + 62, 2, INK)
    img.fill_circle(mx + 74, my + 64, 2, INK)
    img.fill_circle(mx + 72, my + 86, 2, INK)


def draw_card(img, x0, y0, region, field, band_fn, head_lines, head_scale,
              subline, sub_scale):
    img.rect(x0, y0, x0 + 487, y0 + 275, WHITE)
    img.outline_rect(x0, y0, x0 + 487, y0 + 275, INK, 3)
    bx, by = x0 + 3, y0 + 3
    img.set_clip(bx, by, bx + 481, by + 104)
    band_fn(img, bx, by)
    img.clear_clip()
    img.chip(x0 + 12, y0 + 12, region, 5, INK, PAPER)
    img.chip(x0 + 12, y0 + 61, field, 5, RED, WHITE)
    img.rect(bx, by + 105, bx + 481, by + 107, RED)
    hy = y0 + 118 if head_scale == 7 else y0 + 120
    for i, line in enumerate(head_lines):
        img.draw_text(x0 + 12, hy + i * (int(round(7 * head_scale)) + 4),
                      line, head_scale, INK, bold=True)
    sy = y0 + 228 if sub_scale == 5 else y0 + 230
    img.draw_text(x0 + 12, sy, subline, sub_scale, INK, bold=True)
    img.rect(x0 + 12, y0 + 268, x0 + 60, y0 + 271, RED)


def build():
    img = Img()
    # outer frame
    img.rect(0, 0, W - 1, 5, INK)
    img.rect(0, H - 6, W - 1, H - 1, INK)
    img.rect(0, 0, 5, H - 1, INK)
    img.rect(W - 6, 0, W - 1, H - 1, INK)

    # ---- masthead ----
    name = "WORLD TODAY"
    nx = (W - img.text_w(name, 12)) // 2
    img.draw_text(nx, 14, name, 12, INK, bold=True)
    img.rect(24, 106, 999, 111, RED)
    date = "THURSDAY 26 NOVEMBER 2026"
    dx = (W - img.text_w(date, 5.5)) // 2
    img.draw_text(dx, 120, date, 5.5, INK, bold=True)
    img.rect(24, 166, 999, 168, INK)

    # ---- hero: US tariffs on 14 partners ----
    img.draw_text(44, 190, "14", 20, RED, bold=True)
    img.draw_text(44, 356, "PARTNERS", 5, INK, bold=True)
    img.rect(308, 182, 311, 442, INK)
    img.draw_text(336, 178, "NEW US", 12, INK, bold=True)
    img.draw_text(336, 266, "TARIFFS", 12, INK, bold=True)
    img.draw_text(336, 356, "CHINA EU JAPAN INDIA", 5, INK, bold=True)
    img.chip(336, 397, "NORTH AMERICA", 5, INK, PAPER)
    img.chip(753, 397, "TRADE", 5, RED, WHITE)
    img.rect(16, 444, 1007, 447, INK)

    # ---- four cards, 2 x 2 ----
    draw_card(img, 16, 452, "MIDDLE EAST", "CONFLICT", band_refinery,
              ["HOUTHI HIT", "SAUDI PORT"], 7, "RAS TANURA HIT", 5)
    draw_card(img, 520, 452, "ASIA", "SPACE", band_space,
              ["ZEESHAN ALI", "SHENZHOU-24"], 7, "PAKISTAN TIANGONG", 4.5)
    draw_card(img, 16, 740, "EUROPE", "POLITICS", band_politics,
              ["EU SPLIT ON", "EUR 45 BN"], 7, "UKRAINE LOAN", 5)
    draw_card(img, 520, 740, "EUROPE", "SPORT", band_sport,
              ["LIVERPOOL 3-0", "CLUB BRUGGE"], 6, "CHAMPIONS LEAGUE", 4.5)
    return img


def png_bytes(img):
    raw = bytearray()
    for y in range(H):
        raw.append(0)
        raw += img.px[y * W * 3:(y + 1) * W * 3]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(typ, data):
        out = struct.pack(">I", len(data)) + typ + data
        return out + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", comp) + chunk(b"IEND", b""))


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.environ.get(
        "MAKEFUN_OUTPUT_DIR", "out")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "entry.png"), "wb") as f:
        f.write(png_bytes(build()))


if __name__ == "__main__":
    main()
