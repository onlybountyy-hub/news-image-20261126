#!/usr/bin/env python3
"""news-image-20261126 v6 — front-page news summary, pure stdlib.

Renders one deterministic 1024x1024 PNG (entry.png) into MAKEFUN_OUTPUT_DIR
using only the Python standard library (no PIL, no third-party imports).
Text is drawn with a built-in 5x7 bitmap font defined below.
"""
import os
import struct
import sys
import zlib

W = 1024
H = 1024

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARK = (40, 40, 40)
GREY = (110, 110, 110)
LIGHT = (232, 232, 232)
NAVY = (25, 45, 95)
RED = (178, 30, 30)

# ---------------------------------------------------------------- 5x7 font
# Each glyph: 7 rows of 5 bits ("#" = on, "." = off).
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
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
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
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "+": (".....", "00100", "00100", "11111", "00100", "00100", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", "01100", "01100"),
    ",": (".....", ".....", ".....", ".....", "01100", "00100", "01000"),
    ":": (".....", "01100", "01100", ".....", "01100", "01100", "....."),
    "-": (".....", ".....", ".....", "11111", ".....", ".....", "....."),
    "'": ("00100", "00100", "01000", ".....", ".....", ".....", "....."),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "\u00b7": (".....", ".....", "01100", "01100", ".....", ".....", "....."),
    "\u2264": (".....", "..1..", ".1...", "1....", ".1...", "..1..", "11111"),
}

# ---------------------------------------------------------------- content
MASTHEAD = "THE WORLD TODAY"
DATE = "26 NOVEMBER 2026"
HERO_L1 = "TRUMP PROPOSES 20% TARIFFS"
HERO_L2 = "ON CHINA"
BADGE = "20%"
SUB = "14 TRADING PARTNERS \u00b7 UP TO 40% \u00b7 JAN 10 DEADLINE"
CHART_TITLE = "PROPOSED TARIFFS BY ECONOMY"
CEILING_LABEL = "CEILING 40%"
# (name, value, deal value or None, deal text or None, colour)
BARS = [
    ("CHINA", 20, None, None, RED),
    ("VIETNAM", 35, 20, "20% WITH DEAL", NAVY),
    ("INDIA", 25, 17, "17% WITH DEAL", NAVY),
    ("JAPAN", 15, None, None, NAVY),
    ("EU", 15, None, None, NAVY),
]
BAR_LABELS = ["CHINA 20%", "CEILING 40%", "JAPAN \u226415%",
              "EU \u226415%", "VIETNAM 35% 20% WITH DEAL",
              "INDIA 25% 17% WITH DEAL"]
CARDS = [
    ("THANKSGIVING STORM",
     "724,000+ HOMES WITHOUT POWER AS MAJOR BRIDGES CLOSE"),
    ("CAIRO FUEL TANKER FIRE", "31 KILLED IN BLAZE"),
    ("NORTH KOREA", "KIM VOWS TO BUILD MORE NUCLEAR WEAPONS"),
    ("BANGKOK OIL DEPOT BLAST", "SEVERAL HURT AS BANGCHAK SHUTS ALL UNITS"),
    ("CHINA RESPONDS", "BEIJING VOWS NECESSARY MEASURES OVER TARIFFS"),
    ("DRONE DOWNED OVER KUWAIT",
     "IRAN-LINKED DRONE INTERCEPTED 2 ITALIAN TECHNICIANS KILLED"),
]
WIDE_CARD = ("CHINA RETALIATION",
             "BEIJING READIES COUNTERMEASURES IF TARIFFS RISE")
FOOTER = "ALL FIGURES VERIFIED FROM REUTERS AND FRANCE24"

ALL_TEXT = ([MASTHEAD, DATE, HERO_L1, HERO_L2, BADGE, SUB, CHART_TITLE]
            + BAR_LABELS
            + [t for title, body in CARDS for t in (title, body)]
            + [WIDE_CARD[0], WIDE_CARD[1], FOOTER])


def word_count():
    n = 0
    for s in ALL_TEXT:
        n += len([t for t in s.split() if t != "\u00b7"])
    return n


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.px = bytearray([255]) * (w * h * 3)

    def rect(self, x, y, w, h, color):
        r, g, b = color
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.px[i] = r
                self.px[i + 1] = g
                self.px[i + 2] = b

    def hline(self, x, y, w, color, thick=1):
        self.rect(x, y, w, thick, color)

    def vline(self, x, y, h, color, thick=1):
        self.rect(x, y, thick, h, color)

    def text_width(self, s, scale):
        return len(s) * 6 * scale - scale

    def char(self, ch, x, y, scale, color):
        glyph = FONT.get(ch)
        if glyph is None:
            raise ValueError("no glyph for %r" % ch)
        r, g, b = color
        for row in range(7):
            bits = glyph[row]
            for col in range(5):
                if bits[col] == "1":
                    px = x + col * scale
                    py = y + row * scale
                    for dy in range(scale):
                        base = ((py + dy) * self.w + px) * 3
                        for dx in range(scale):
                            i = base + dx * 3
                            self.px[i] = r
                            self.px[i + 1] = g
                            self.px[i + 2] = b

    def text(self, s, x, y, scale, color):
        cx = x
        for ch in s:
            self.char(ch, cx, y, scale, color)
            cx += 6 * scale

    def text_center(self, s, cx, y, scale, color):
        self.text(s, cx - self.text_width(s, scale) // 2, y, scale, color)


def wrap(text, max_chars):
    words = text.split()
    lines = []
    cur = ""
    for word in words:
        nxt = word if not cur else cur + " " + word
        if len(nxt) <= max_chars:
            cur = nxt
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- render
def render():
    c = Canvas(W, H)
    # outer frame
    c.rect(0, 0, W, 4, BLACK)
    c.rect(0, H - 4, W, 4, BLACK)
    c.rect(0, 0, 4, H, BLACK)
    c.rect(W - 4, 0, 4, H, BLACK)

    # masthead
    c.text_center(MASTHEAD, W // 2, 34, 6, BLACK)
    c.text_center(DATE, W // 2, 92, 3, RED)
    c.hline(40, 126, W - 80, BLACK, 3)
    c.hline(40, 132, W - 80, BLACK, 1)

    # hero
    c.text_center(HERO_L1, W // 2, 152, 5, BLACK)
    c.text_center(HERO_L2, 470, 198, 5, BLACK)
    # badge "20%" in red box, right of "ON CHINA"
    bx, by, bw, bh = 660, 192, 116, 48
    c.rect(bx, by, bw, bh, RED)
    c.text_center(BADGE, bx + bw // 2, by + 7, 4, WHITE)
    # sub-line
    c.text_center(SUB, W // 2, 258, 3, RED)
    c.hline(40, 296, W - 80, BLACK, 3)

    # bar chart
    c.text(CHART_TITLE, 40, 314, 3, BLACK)
    c.text(CEILING_LABEL, 786, 314, 2, RED)
    bar_x0 = 200
    bar_max_w = 740          # value 45 -> full width
    max_val = 45.0
    row_y = 352
    row_h = 40
    bar_h = 22
    ceiling_x = bar_x0 + int(40 / max_val * bar_max_w)
    for i, (name, val, deal, deal_text, color) in enumerate(BARS):
        y = row_y + i * row_h
        c.text(name, 40, y + 3, 2, BLACK)
        bw = int(val / max_val * bar_max_w)
        c.rect(bar_x0, y, bar_max_w, bar_h, LIGHT)
        c.rect(bar_x0, y, bw, bar_h, color)
        vx = bar_x0 + bw + 10
        label = "%d%%" % val if name not in ("JAPAN", "EU") else "\u2264%d%%" % val
        c.text(label, vx, y + 3, 2, BLACK)
        if deal_text:
            # deal note on a second line under the bar, clear of the
            # ceiling marker and the value label
            c.text(deal_text, bar_x0, y + 25, 2, GREY)
            # deal marker tick on the bar
            dx = bar_x0 + int(deal / max_val * bar_max_w)
            c.vline(dx, y - 3, bar_h + 6, GREY, 3)
    # ceiling marker: dashed red vertical line at 40%
    top = row_y - 6
    bottom = row_y + 5 * row_h - 6
    yy = top
    while yy < bottom:
        c.rect(ceiling_x, yy, 3, 8, RED)
        yy += 16
    c.hline(40, 572, W - 80, BLACK, 3)

    # cards: 3 rows x 2 cols, then one wide card
    card_w = 452
    card_h = 88
    xs = [40, 532]
    ys = [590, 688, 786]
    for idx, (title, body) in enumerate(CARDS):
        x = xs[idx % 2]
        y = ys[idx // 2]
        c.rect(x, y, card_w, card_h, WHITE)
        c.rect(x, y, card_w, 2, BLACK)
        c.rect(x, y, 2, card_h, BLACK)
        c.rect(x + card_w - 2, y, 2, card_h, BLACK)
        c.rect(x, y + card_h - 2, card_w, 2, BLACK)
        c.text(title, x + 12, y + 10, 2, RED)
        lines = wrap(body, 35)
        for j, line in enumerate(lines):
            c.text(line, x + 12, y + 36 + j * 24, 2, BLACK)
    # wide card
    wx, wy = 40, 884
    c.rect(wx, wy, W - 80, card_h, WHITE)
    c.rect(wx, wy, W - 80, 2, BLACK)
    c.rect(wx, wy, 2, card_h, BLACK)
    c.rect(wx + W - 82, wy, 2, card_h, BLACK)
    c.rect(wx, wy + card_h - 2, W - 80, 2, BLACK)
    c.text(WIDE_CARD[0], wx + 12, wy + 10, 2, RED)
    c.text(WIDE_CARD[1], wx + 12, wy + 36, 2, BLACK)

    # footer
    c.text_center(FOOTER, W // 2, 986, 2, GREY)
    return c


# ---------------------------------------------------------------- PNG out
def write_png(canvas, path):
    raw = bytearray()
    stride = W * 3
    for y in range(H):
        raw.append(0)  # filter: none
        raw += canvas.px[y * stride:(y + 1) * stride]

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", ihdr)
           + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
           + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)


def main():
    n = word_count()
    print("WORDS: %d" % n)
    if not (110 <= n <= 130):
        print("ERROR: word count outside 110-130", file=sys.stderr)
        sys.exit(1)
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "."
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    canvas = render()
    write_png(canvas, path)
    print("WROTE: %s (%dx%d)" % (path, W, H))


if __name__ == "__main__":
    main()
