#!/usr/bin/env python3
"""news-image-20261126 v5 — one-page front page summing up Thursday 26 November 2026.

Pure Python standard library. Draws a 1024x1024 typographic front page with a
5x7 bitmap font (scaled), writes it as a deterministic PNG to
$MAKEFUN_OUTPUT_DIR/entry.png (default /output/entry.png).

Content plan (DeepAI DeepSeek V4.1 Flash repair advice, 27 Nov 2026):
  * proposition hero: TRUMP PROPOSES 20% TARIFFS ON CHINA, "20%" as a badge
    inside the headline, plus the 14-partner subline;
  * 6 story cards, every card carrying at least two checkable tokens
    (proper noun + number, or country + event);
  * "THE DAY IN NUMBERS" bar chart (5 labelled bars) restored at the bottom;
  * ~130 words total; clean 2-column card grid kept from v4.
"""
import os
import struct
import zlib

W = 1024
H = 1024

# ---------------------------------------------------------------- 5x7 font
# Each glyph is 7 rows of 5 cells; '1' is ink, '0' is blank. Uppercase,
# digits and the punctuation this poster needs.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "*": ("00000", "00100", "10101", "01110", "10101", "00100", "00000"),
}


def glyph(ch):
    """Glyph rows for one character; unknown characters render blank."""
    return FONT.get(ch, FONT[" "])


# ---------------------------------------------------------------- canvas
PAPER = (246, 241, 231)
INK = (20, 33, 61)
RED = (193, 39, 45)
BLUE = (29, 78, 137)
GOLD = (176, 124, 22)
TEAL = (46, 125, 91)
PURPLE = (91, 74, 138)
GREEN = (52, 110, 58)
WHITE = (255, 255, 255)
LIGHT = (216, 210, 196)
GREY = (110, 104, 90)
SOFT = (238, 233, 220)


class Canvas:
    """A plain RGB framebuffer with filled rectangles and bitmap text."""

    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(w * h * 3)
        self.fill(bg)

    def fill(self, color):
        r, g, b = color
        self.px[:] = bytes((r, g, b)) * (self.w * self.h)

    def rect(self, x, y, w, h, color):
        r, g, b = color
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        row = bytes((r, g, b)) * (x1 - x0)
        for yy in range(y0, y1):
            off = (yy * self.w + x0) * 3
            self.px[off:off + len(row)] = row

    def text_width(self, text, scale):
        # 5 cells + 1 spacing per character, last character has no trailing gap
        if not text:
            return 0
        return (len(text) * 6 - 1) * scale

    def text(self, x, y, text, scale, color):
        cx = x
        for ch in text:
            rows = glyph(ch)
            for ry, row in enumerate(rows):
                for rx, bit in enumerate(row):
                    if bit == "1":
                        self.rect(cx + rx * scale, y + ry * scale,
                                  scale, scale, color)
            cx += 6 * scale
        return cx

    def text_center(self, cx, y, text, scale, color):
        self.text(cx - self.text_width(text, scale) // 2, y, text, scale, color)

    def text_right(self, x, y, text, scale, color):
        self.text(x - self.text_width(text, scale), y, text, scale, color)

    def wrap(self, text, scale, max_w):
        """Greedy word wrap; returns a list of lines that fit max_w."""
        words = text.split(" ")
        lines = []
        cur = ""
        for word in words:
            trial = word if not cur else cur + " " + word
            if self.text_width(trial, scale) <= max_w:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        return lines

    def paragraph(self, x, y, text, scale, max_w, color, leading=None):
        lh = leading if leading is not None else 7 * scale + 4
        for line in self.wrap(text, scale, max_w):
            self.text(x, y, line, scale, color)
            y += lh
        return y


# ---------------------------------------------------------------- PNG writer
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def png_bytes(canvas):
    raw = bytearray()
    stride = canvas.w * 3
    for y in range(canvas.h):
        raw.append(0)  # filter: none
        raw += canvas.px[y * stride:(y + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + _chunk(b"IHDR", ihdr)
            + _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + _chunk(b"IEND", b""))


# ---------------------------------------------------------------- content
# Every story below was verified from 26 Nov 2026 reporting (see the
# session's fact notes): US tariff proposal to 14 partners; Ukraine's
# Savasleyka strike (5 jets: 3 MiG-31, 2 Su-34); Nvidia -3.9% AI sell-off;
# EU split over a 45bn-euro Ukraine loan in Brussels; Houthi strike on a
# Saudi port and the Ras Tanura refinery; first Pakistani astronaut
# Muhammad Zeeshan Ali reaching Tiangong on Shenzhou-24; 13 miners trapped
# in a flooded illegal gold mine in Bogor, Indonesia.
LIGHT_RED = (238, 120, 110)
LIGHT_GREY = (205, 210, 220)

HERO_SUB = "NEW LEVIES ON 14 PARTNERS: EU, JAPAN, INDIA"

CARDS = [
    ("WAR IN EUROPE", RED,
     "UKRAINE HITS SAVASLEYKA AIRBASE",
     "5 JETS DAMAGED: 3 MIG-31S, 2 SU-34S"),
    ("MARKETS", BLUE,
     "NVIDIA SLIDES 3.9% IN AI SELL-OFF",
     "NASDAQ NEARS BEAR MARKET"),
    ("EUROPE", GOLD,
     "EU SPLITS OVER 45BN EURO UKRAINE LOAN",
     "LEADERS CLASH IN BRUSSELS"),
    ("MIDDLE EAST", TEAL,
     "HOUTHIS STRIKE SAUDI PORT AND REFINERY",
     "RAS TANURA FACILITY HIT"),
    ("SPACE", PURPLE,
     "PAKISTANI ASTRONAUT REACHES TIANGONG",
     "MUHAMMAD ZEESHAN ALI, SHENZHOU-24"),
    ("ASIA", GREEN,
     "13 MINERS TRAPPED IN FLOODED BOGOR MINE",
     "RESCUE UNDER WAY IN INDONESIA"),
]

CHART_TITLE = "THE DAY IN NUMBERS"
CHART_ROWS = [
    ("US TARIFF ON CHINA", 20, "20%", RED),
    ("TRADE PARTNERS TARGETED", 14, "14", BLUE),
    ("EU LOAN ROW FOR UKRAINE", 45, "45BN EURO", GOLD),
    ("JETS DAMAGED AT SAVASLEYKA", 5, "5", TEAL),
    ("MINERS TRAPPED IN BOGOR", 13, "13", PURPLE),
]

FOOTER = "26 NOVEMBER 2026 - WORLD NEWS IN ONE IMAGE"


def draw_card(cv, x, y, w, h, label, color, headline, detail):
    cv.rect(x, y, w, h, LIGHT)
    cv.rect(x + 2, y + 2, w - 4, h - 4, WHITE)
    cv.rect(x + 2, y + 2, 8, h - 4, color)
    lx = x + 22
    chip_w = cv.text_width(label, 2) + 18
    cv.rect(lx, y + 14, chip_w, 22, color)
    cv.text(lx + 9, y + 18, label, 2, WHITE)
    tx = x + 22
    ty = y + 46
    for line in cv.wrap(headline, 3, w - 44):
        cv.text(tx, ty, line, 3, INK)
        ty += 25
    ty += 2
    for line in cv.wrap(detail, 2, w - 44):
        cv.text(tx, ty, line, 2, GREY)
        ty += 18


def draw(cv):
    # Masthead: title left, full date right, red rule below.
    cv.text(28, 26, "THE WORLD IN ONE DAY", 4, INK)
    cv.text_right(996, 30, "THURSDAY 26 NOVEMBER 2026", 3, RED)
    cv.rect(28, 66, 968, 4, RED)

    # Hero band: proposition headline with "20%" as a badge inside it.
    cv.rect(28, 76, 968, 280, INK)
    cv.text(52, 100, "TOP STORY", 2, LIGHT_RED)
    cv.text(52, 126, "TRUMP PROPOSES", 7, WHITE)
    badge_w = cv.text_width("20%", 7) + 32
    cv.rect(52, 186, badge_w, 56, RED)
    cv.text(52 + 16, 190, "20%", 7, WHITE)
    cv.text(52 + badge_w + 16, 190, "TARIFFS", 7, WHITE)
    cv.text(52, 248, "ON CHINA", 7, WHITE)
    cv.text(52, 318, HERO_SUB, 3, LIGHT_GREY)

    # Story cards: 2 columns x 3 rows.
    cw, ch, gap = 474, 132, 20
    for i, (label, color, headline, detail) in enumerate(CARDS):
        cx = 28 + (i % 2) * (cw + gap)
        cy = 372 + (i // 2) * (ch + 16)
        draw_card(cv, cx, cy, cw, ch, label, color, headline, detail)

    # Bar chart: the day in numbers.
    cv.text(28, 818, CHART_TITLE, 3, INK)
    cv.rect(28, 844, 968, 3, RED)
    max_v = max(v for _, v, _, _ in CHART_ROWS)
    bar_x, bar_w = 340, 480
    for i, (label, value, shown, color) in enumerate(CHART_ROWS):
        ry = 858 + i * 24
        cv.text(28, ry + 2, label, 2, INK)
        bw = max(8, int(bar_w * value / max_v))
        cv.rect(bar_x, ry + 3, bw, 16, color)
        cv.text_right(996, ry, shown, 3, INK)

    # Footer.
    cv.text_center(512, 986, FOOTER, 2, GREY)


def word_count():
    parts = ["THE WORLD IN ONE DAY", "THURSDAY 26 NOVEMBER 2026",
             "TOP STORY", "TRUMP PROPOSES 20% TARIFFS ON CHINA", HERO_SUB]
    for label, _c, headline, detail in CARDS:
        parts += [label, headline, detail]
    parts.append(CHART_TITLE)
    for label, _v, shown, _c in CHART_ROWS:
        parts += [label, shown]
    parts.append(FOOTER)
    return sum(len(p.split(" ")) for p in parts)


def main():
    cv = Canvas(W, H, PAPER)
    draw(cv)
    data = png_bytes(cv)
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)
    print("wrote %s (%d bytes, %dx%d, words=%d)"
          % (path, len(data), W, H, word_count()))


if __name__ == "__main__":
    main()
