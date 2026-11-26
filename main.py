#!/usr/bin/env python3
"""news-image-20261126 v3 -- one-page newspaper front page.

Sums up Thursday 26 November 2026 in a single 1024x1024 PNG.
Pure Python standard library only (os, struct, sys, zlib).
Draws everything procedurally: own PNG encoder, own 5x7 bitmap font.
Deterministic: the same input always produces the same bytes.

Run:  MAKEFUN_OUTPUT_DIR=out python3 -P -s main.py
Writes entry.png into MAKEFUN_OUTPUT_DIR.
"""

import os
import struct
import sys
import zlib

W = 1024
H = 1024

PAPER = (247, 243, 232)   # light editorial paper
INK = (20, 20, 20)        # near-black ink
RED = (193, 18, 31)       # accent red
WHITE = (255, 255, 255)
CARD = (255, 253, 245)    # card fill, a touch lighter than the paper


# ---------------------------------------------------------------- font
# Procedural 5x7 bitmap font, defined fresh here. One row per string,
# '#' is an inked pixel, '.' is blank. Covers everything the page uses:
# A-Z, 0-9, space, apostrophe, hyphen, percent, period, comma, slash,
# colon, parentheses, plus.
FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
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
    "N": ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
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
    "0": (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    "'": ("..#..", "..#..", "..#..", ".....", ".....", ".....", "....."),
    "-": (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    "%": ("##..#", "##.#.", "...#.", "..#..", ".#...", "#.##.", "#..##"),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".....", ".##..", ".#..."),
    "/": ("....#", "...#.", "...#.", "..#..", ".#...", ".#...", "#...."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    "(": ("...##", "..#..", ".#...", ".#...", ".#...", "..#..", "...##"),
    ")": ("##...", "..#..", "...#.", "...#.", "...#.", "..#..", "##..."),
    "+": (".....", "..#..", "..#..", ".###.", "..#..", "..#..", "....."),
}


def text_width(text, scale):
    """Pixel width of text at a scale (5 px glyph + 1 px gap per char)."""
    return len(text) * 6 * scale - scale


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bytes(bg) * (w * h))

    def fill_rect(self, x, y, w, h, color):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(color) * (x1 - x0)
        for yy in range(y0, y1):
            off = (yy * self.w + x0) * 3
            self.px[off:off + len(row)] = row

    def outline_rect(self, x, y, w, h, t, color):
        self.fill_rect(x, y, w, t, color)
        self.fill_rect(x, y + h - t, w, t, color)
        self.fill_rect(x, y, t, h, color)
        self.fill_rect(x + w - t, y, t, h, color)

    def _draw_text_once(self, x, y, text, scale, color):
        for ci, ch in enumerate(text):
            glyph = FONT.get(ch)
            if glyph is None:
                raise ValueError("no glyph for %r" % ch)
            cx = x + ci * 6 * scale
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits[col] == "#":
                        self.fill_rect(cx + col * scale, y + row * scale,
                                       scale, scale, color)

    def draw_text(self, x, y, text, scale, color, bold=False):
        self._draw_text_once(x, y, text, scale, color)
        if bold:
            # Second pass, shifted right, for a heavier stroke.
            self._draw_text_once(x + max(1, scale // 3), y, text, scale,
                                 color)

    def draw_text_centered(self, cx, y, text, scale, color, bold=False):
        x = cx - text_width(text, scale) // 2
        self.draw_text(x, y, text, scale, color, bold=bold)
        return x

    def draw_text_right(self, right, y, text, scale, color, bold=False):
        x = right - text_width(text, scale)
        self.draw_text(x, y, text, scale, color, bold=bold)
        return x


# ---------------------------------------------------------------- PNG
def png_bytes(cv):
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)  # filter: none
        raw += cv.px[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        return out + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", comp)
            + chunk(b"IEND", b""))


# ---------------------------------------------------------------- page
def draw_card(cv, x, y, w, h, chip, headline, sublines, source):
    cv.fill_rect(x, y, w, h, CARD)
    cv.outline_rect(x, y, w, h, 2, INK)
    # Region chip (red, white text) top-left; source line top-right.
    chip_w = text_width(chip, 2) + 16
    cv.fill_rect(x + 14, y + 12, chip_w, 26, RED)
    cv.draw_text(x + 14 + 8, y + 18, chip, 2, WHITE, bold=True)
    cv.draw_text_right(x + w - 14, y + 18, source, 2, RED, bold=True)
    # Headline, bold, scale 3.
    hy = y + 50
    for line in headline:
        assert text_width(line, 3) <= w - 28, line
        cv.draw_text(x + 14, hy, line, 3, INK, bold=True)
        hy += 26
    # Subline, scale 2.
    sy = hy + 10
    for line in sublines:
        assert text_width(line, 2) <= w - 28, line
        cv.draw_text(x + 14, sy, line, 2, INK)
        sy += 18


def draw_page(cv):
    # Outer frame.
    cv.outline_rect(16, 16, W - 32, H - 32, 3, INK)

    # Masthead.
    masthead = "THE WORLD TODAY"
    mx = cv.draw_text_centered(W // 2, 44, masthead, 6, INK, bold=True)
    cv.fill_rect(mx - 30, 58, 14, 14, RED)
    cv.fill_rect(mx + text_width(masthead, 6) + 16, 58, 14, 14, RED)
    # Double rule under the masthead.
    cv.fill_rect(40, 100, 944, 3, INK)
    cv.fill_rect(40, 107, 944, 1, INK)

    # Red dateline band.
    cv.fill_rect(40, 118, 944, 50, RED)
    date_line = "THURSDAY, 26 NOVEMBER 2026"
    dx = cv.draw_text_centered(W // 2, 125, date_line, 5, WHITE, bold=True)
    # Thin ink rule directly under the date line, inside the band.
    cv.fill_rect(dx, 162, text_width(date_line, 5), 2, INK)

    # Hero headline -- the largest text on the page.
    cv.draw_text_centered(W // 2, 190, "TRUMP PROPOSES", 7, INK, bold=True)
    # Line 2 with the key figure oversized: "20%" at scale 9 against
    # scale 7 for the rest, both runs sharing one baseline (y=306), so
    # the number still reads when the page shrinks to thumbnail size.
    num, rest = "20%", "TARIFFS ON CHINA"
    num_w = text_width(num, 9)
    rest_w = text_width(rest, 7)
    hx = W // 2 - (num_w + 6 * 7 + rest_w) // 2
    cv.draw_text(hx, 306 - 7 * 9, num, 9, INK, bold=True)
    cv.draw_text(hx + num_w + 6 * 7, 306 - 7 * 7, rest, 7, INK, bold=True)
    # Hero subline, one line.
    cv.draw_text_centered(
        W // 2, 322, "USTR PROPOSES 20-40% DUTIES ON 14 TRADING PARTNERS",
        3, INK)

    # Hero illustration: giant "20%" + tariff-rate bars.
    cv.draw_text(70, 390, "20%", 14, RED, bold=True)
    cv.fill_rect(70, 502, 238, 4, RED)
    cv.draw_text_centered(680, 352, "PROPOSED TARIFF RATES", 2, INK,
                          bold=True)
    bars = [("CHINA", "20%", 20, RED),
            ("VIETNAM", "35%", 35, INK),
            ("INDIA", "25%", 25, INK),
            ("EU", "15%", 15, INK)]
    baseline = 545
    for i, (name, val, rate, color) in enumerate(bars):
        bx = 400 + i * 153
        bh = rate * 4
        top = baseline - bh
        cv.fill_rect(bx, top, 100, bh, color)
        cv.draw_text_centered(bx + 50, top - 20, val, 2, RED, bold=True)
        cv.draw_text_centered(bx + 50, baseline + 6, name, 2, INK)

    # Divider between hero and the card grid.
    cv.fill_rect(40, 596, 944, 2, INK)

    # 2x2 card grid.
    cards = [
        (40, 612, "MIDDLE EAST / CONFLICT",
         ["HOUTHI STRIKE HITS", "RAS TANURA"],
         ["SAUDI PORT AND REFINERY ATTACKED"], "NEWS WIRES"),
        (520, 612, "ASIA / SPACE",
         ["PAKISTAN'S FIRST", "ASTRONAUT REACHES", "TIANGONG"],
         ["ZEESHAN ALI ARRIVES ABOARD", "SHENZHOU-24"], "REUTERS"),
        (40, 806, "NORTH AMERICA / TECH",
         ["NVIDIA -3.9% AS AI", "SELL-OFF DEEPENS"],
         ["NASDAQ 100 BRIEFLY ENTERS", "BEAR MARKET"], "CNN"),
        (520, 806, "EUROPE / SPORT",
         ["LIVERPOOL BEAT CLUB", "BRUGGE 3-0"],
         ["CHAMPIONS LEAGUE GROUP STAGE"], "NEWS WIRES"),
    ]
    for x, y, chip, headline, sublines, source in cards:
        draw_card(cv, x, y, 464, 178, chip, headline, sublines, source)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "out")
    os.makedirs(out_dir, exist_ok=True)
    cv = Canvas(W, H, PAPER)
    draw_page(cv)
    data = png_bytes(cv)
    with open(os.path.join(out_dir, "entry.png"), "wb") as f:
        f.write(data)
    return 0


if __name__ == "__main__":
    sys.exit(main())
