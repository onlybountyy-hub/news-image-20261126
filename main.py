#!/usr/bin/env python3
"""news-image-20261126 v4: one-image summary of Thursday 26 November 2026.

Pure Python standard library. Draws a 1024x1024 newspaper-style poster
with a hand-built variable-width bitmap font and its own PNG encoder, and
writes entry.png to $MAKEFUN_OUTPUT_DIR.

Stories (all 26 Nov 2026, first reported that day):
  HERO  US proposes new tariffs on 14 trading partners (USTR)
  1     Houthis hit Ras Tanura oil port (Middle East)
  2     First Pakistani astronaut reaches Tiangong (Asia)
  3     EU split over a 45bn euro Ukraine loan (Europe)
  4     13 miners trapped in a flooded Bogor mine (Southeast Asia)
"""

import math
import os
import struct
import zlib

W = 1024
H = 1024

PAPER = (247, 243, 232)
INK = (20, 20, 20)
RED = (193, 18, 31)
TEAL = (15, 76, 92)
OCHRE = (217, 164, 65)

# ---------------------------------------------------------------- canvas

buf = bytearray(bytes(PAPER) * (W * H))


def fill_rect(x0, y0, x1, y1, color):
    """Fill [x0, x1) x [y0, y1) with color, clipped to the canvas."""
    x0 = max(0, x0)
    y0 = max(0, y0)
    x1 = min(W, x1)
    y1 = min(H, y1)
    if x1 <= x0 or y1 <= y0:
        return
    row = bytes(color) * (x1 - x0)
    for y in range(y0, y1):
        o = (y * W + x0) * 3
        buf[o:o + len(row)] = row


def disc(cx, cy, r, color):
    """Filled circle."""
    for dy in range(-r, r + 1):
        dx = int(math.sqrt(r * r - dy * dy))
        fill_rect(cx - dx, cy + dy, cx + dx + 1, cy + dy + 1, color)


def ring(cx, cy, r, t, color):
    """Circle outline of thickness t."""
    ri = r - t
    for dy in range(-r, r + 1):
        dxo = int(math.sqrt(r * r - dy * dy))
        if abs(dy) < ri:
            dxi = int(math.sqrt(ri * ri - dy * dy))
            fill_rect(cx - dxo, cy + dy, cx - dxi, cy + dy + 1, color)
            fill_rect(cx + dxi + 1, cy + dy, cx + dxo + 1, cy + dy + 1, color)
        else:
            fill_rect(cx - dxo, cy + dy, cx + dxo + 1, cy + dy + 1, color)


def poly(points, color):
    """Scanline-filled polygon."""
    ys = [p[1] for p in points]
    ymin, ymax = min(ys), max(ys)
    n = len(points)
    for y in range(ymin, ymax + 1):
        xs = []
        for i in range(n):
            x0, y0 = points[i]
            x1, y1 = points[(i + 1) % n]
            if (y0 <= y < y1) or (y1 <= y < y0):
                xs.append(x0 + (y - y0 + 0.5) * (x1 - x0) / (y1 - y0))
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            fill_rect(int(math.ceil(xs[i])), y,
                      int(math.floor(xs[i + 1])) + 1, y + 1, color)


def plus(x, y, color):
    """Small 4-point star, 9x9 centred on (x, y)."""
    fill_rect(x - 1, y - 4, x + 1, y + 5, color)
    fill_rect(x - 4, y - 1, x + 5, y + 1, color)


# ---------------------------------------------------------------- font
# Variable-width 7-row bitmap caps. Each glyph: (width_in_cells, 7 rows).
# Advance of a glyph is width + 1 cell (one blank cell of tracking).
# Glyphs are drawn bold: every set cell paints a 2x2 block of cells,
# clipped to the glyph box, so strokes stay >= 6 px at every size used.

FONT = {
    'A': (5, [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"]),
    'B': (5, ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."]),
    'C': (5, [".####", "#...#", "#....", "#....", "#....", "#...#", ".####"]),
    'D': (5, ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."]),
    'E': (5, ["#####", "#....", "#....", "####.", "#....", "#....", "#####"]),
    'F': (4, ["####", "#...", "#...", "###.", "#...", "#...", "#..."]),
    'G': (5, [".####", "#...#", "#....", "#.###", "#...#", "#...#", ".###."]),
    'H': (5, ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"]),
    'I': (3, ["###", ".#.", ".#.", ".#.", ".#.", ".#.", "###"]),
    'J': (4, [".###", "...#", "...#", "...#", "...#", "#..#", ".##."]),
    'K': (5, ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"]),
    'L': (4, ["#...", "#...", "#...", "#...", "#...", "#...", "####"]),
    'M': (6, ["#....#", "##..##", "#.#..#", "#.#..#", "#....#", "#....#", "#....#"]),
    'N': (5, ["#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"]),
    'O': (5, [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."]),
    'P': (5, ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."]),
    'Q': (5, [".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"]),
    'R': (5, ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"]),
    'S': (5, [".####", "#...#", "#....", ".###.", "....#", "#...#", "####."]),
    'T': (4, ["####", ".#..", ".#..", ".#..", ".#..", ".#..", ".#.."]),
    'U': (5, ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."]),
    'V': (5, ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."]),
    'W': (6, ["#....#", "#....#", "#....#", "#.#..#", "#.#..#", "##..##", "#....#"]),
    'X': (5, ["#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"]),
    'Y': (5, ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."]),
    'Z': (5, ["#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"]),
    '0': (5, [".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."]),
    '1': (3, [".#.", "##.", ".#.", ".#.", ".#.", ".#.", "###"]),
    '2': (5, [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"]),
    '3': (5, ["####.", "....#", "....#", ".###.", "....#", "....#", "####."]),
    '4': (5, ["#...#", "#...#", "#...#", "#...#", "#####", "....#", "....#"]),
    '5': (5, ["#####", "#....", "####.", "....#", "....#", "#...#", ".###."]),
    '6': (5, [".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."]),
    '7': (5, ["#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."]),
    '8': (5, [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."]),
    '9': (5, [".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."]),
    "'": (2, ["##", "##", "#.", "..", "..", "..", ".."]),
    '\u20ac': (5, [".###.", "#...#", "###..", "#....", "###..", "#...#", ".###."]),
    ' ': (2, ["..", "..", "..", "..", "..", "..", ".."]),
}


def _adv(ch):
    return FONT[ch][0] + 1


def text_width_cells(s):
    """Width of s in cells, no trailing gap."""
    return sum(_adv(c) for c in s) - 1


def text_width(s, sx):
    return text_width_cells(s) * sx


def draw_text(x, y, sx, sy, s, color):
    """Draw s with its top-left at (x, y). sx/sy = px per font cell."""
    cx = x
    for ch in s:
        w, rows = FONT[ch]
        gx1 = cx + w * sx
        gy1 = y + 7 * sy
        for ry, row in enumerate(rows):
            for rx, bit in enumerate(row):
                if bit == '#':
                    bx0 = cx + rx * sx
                    by0 = y + ry * sy
                    bx1 = min(bx0 + 2 * sx, gx1)
                    by1 = min(by0 + 2 * sy, gy1)
                    fill_rect(bx0, by0, bx1, by1, color)
        cx += (w + 1) * sx
    return cx


def draw_text_centered(cx, y, sx, sy, s, color):
    draw_text(cx - text_width(s, sx) // 2, y, sx, sy, s, color)


def wrap_words(s, max_cells):
    """Greedy word wrap; returns lines whose width is <= max_cells."""
    lines = []
    cur = ""
    for word in s.split(" "):
        cand = word if not cur else cur + " " + word
        if text_width_cells(cand) <= max_cells:
            cur = cand
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines

# ---------------------------------------------------------------- pictograms
# Each pictogram draws inside a 128x56 box whose top-left is (px, py).

def pic_port(px, py):
    """Houthi strike: port crane, containers, smoke, sea."""
    # smoke puffs
    disc(px + 24, py + 8, 6, RED)
    disc(px + 36, py + 6, 5, RED)
    disc(px + 48, py + 8, 5, RED)
    # containers on the pier
    fill_rect(px + 16, py + 22, px + 38, py + 36, OCHRE)
    fill_rect(px + 40, py + 26, px + 62, py + 36, RED)
    # crane: post, jib, cable, hanging box
    fill_rect(px + 86, py + 6, px + 91, py + 42, INK)
    fill_rect(px + 86, py + 6, px + 120, py + 11, INK)
    fill_rect(px + 116, py + 11, px + 118, py + 21, INK)
    fill_rect(px + 108, py + 21, px + 124, py + 32, TEAL)
    # pier deck and posts
    fill_rect(px + 8, py + 36, px + 78, py + 41, INK)
    fill_rect(px + 12, py + 41, px + 17, py + 56, INK)
    fill_rect(px + 66, py + 41, px + 71, py + 56, INK)
    # sea with wave dashes
    fill_rect(px, py + 42, px + 128, py + 56, TEAL)
    fill_rect(px + 8, py + 46, px + 26, py + 49, PAPER)
    fill_rect(px + 48, py + 49, px + 66, py + 52, PAPER)
    fill_rect(px + 88, py + 46, px + 106, py + 49, PAPER)


def pic_rocket(px, py):
    """Tiangong: rocket, station ring, stars."""
    plus(px + 10, py + 8, OCHRE)
    plus(px + 112, py + 12, OCHRE)
    plus(px + 104, py + 44, OCHRE)
    plus(px + 16, py + 46, OCHRE)
    # station ring with a module bar
    ring(px + 102, py + 22, 12, 5, TEAL)
    fill_rect(px + 88, py + 20, px + 96, py + 24, TEAL)
    # rocket body, nose, window, fins, flame
    poly([(px + 52, py + 10), (px + 68, py + 10), (px + 60, py + 0)], INK)
    fill_rect(px + 52, py + 10, px + 68, py + 38, INK)
    disc(px + 60, py + 22, 4, OCHRE)
    poly([(px + 52, py + 32), (px + 40, py + 46), (px + 52, py + 40)], RED)
    poly([(px + 68, py + 32), (px + 80, py + 46), (px + 68, py + 40)], RED)
    poly([(px + 54, py + 38), (px + 66, py + 38), (px + 60, py + 52)], RED)
    poly([(px + 56, py + 38), (px + 64, py + 38), (px + 60, py + 47)], OCHRE)


def pic_parliament(px, py):
    """EU loan: parliament building and a euro coin."""
    # coin with euro bars
    disc(px + 106, py + 18, 13, OCHRE)
    fill_rect(px + 99, py + 12, px + 113, py + 15, INK)
    fill_rect(px + 99, py + 22, px + 113, py + 25, INK)
    fill_rect(px + 101, py + 7, px + 104, py + 29, INK)
    # pediment, columns, door, base, ground line
    poly([(px + 8, py + 24), (px + 84, py + 24), (px + 46, py + 10)], INK)
    fill_rect(px + 14, py + 24, px + 19, py + 44, INK)
    fill_rect(px + 30, py + 24, px + 35, py + 44, INK)
    fill_rect(px + 46, py + 24, px + 51, py + 44, INK)
    fill_rect(px + 62, py + 24, px + 67, py + 44, INK)
    fill_rect(px + 36, py + 36, px + 46, py + 44, OCHRE)
    fill_rect(px + 8, py + 44, px + 92, py + 50, INK)
    fill_rect(px + 8, py + 52, px + 120, py + 56, TEAL)


def pic_mine(px, py):
    """Bogor mine: flooded shaft entrance, rain, life ring."""
    # mine entrance frame with arched opening
    fill_rect(px + 8, py + 20, px + 52, py + 56, INK)
    fill_rect(px + 20, py + 32, px + 40, py + 56, PAPER)
    disc(px + 30, py + 32, 10, PAPER)
    # flood water with wave dashes
    fill_rect(px, py + 46, px + 128, py + 56, TEAL)
    fill_rect(px + 10, py + 49, px + 28, py + 52, PAPER)
    fill_rect(px + 52, py + 52, px + 70, py + 55, PAPER)
    fill_rect(px + 94, py + 49, px + 112, py + 52, PAPER)
    # rain streaks
    fill_rect(px + 76, py + 4, px + 79, py + 12, INK)
    fill_rect(px + 90, py + 10, px + 93, py + 18, INK)
    fill_rect(px + 104, py + 4, px + 107, py + 12, INK)
    fill_rect(px + 116, py + 10, px + 119, py + 18, INK)
    # life ring floating on the water
    ring(px + 100, py + 50, 7, 4, OCHRE)


def pic_ship(x0, y0):
    """Hero pictogram: container ship with stacked boxes, bridge, smoke."""
    # stacked containers
    fill_rect(768, 440, 820, 470, RED)
    fill_rect(824, 440, 876, 470, OCHRE)
    fill_rect(740, 470, 792, 500, OCHRE)
    fill_rect(796, 470, 848, 500, RED)
    fill_rect(852, 470, 904, 500, TEAL)
    # bridge with lit windows
    fill_rect(912, 472, 948, 500, INK)
    fill_rect(918, 480, 926, 486, PAPER)
    fill_rect(930, 480, 938, 486, PAPER)
    fill_rect(940, 480, 946, 486, PAPER)
    # mast and smoke
    fill_rect(956, 436, 960, 500, INK)
    disc(966, 428, 6, RED)
    disc(976, 420, 5, RED)
    # hull with red waterline stripe
    poly([(716, 500), (968, 500), (948, 532), (736, 532)], INK)
    fill_rect(716, 500, 968, 506, RED)
    # waves
    fill_rect(700, 536, 984, 546, TEAL)
    fill_rect(716, 540, 740, 544, PAPER)
    fill_rect(780, 544, 804, 548, PAPER)
    fill_rect(850, 540, 874, 544, PAPER)
    fill_rect(920, 544, 944, 548, PAPER)

# ---------------------------------------------------------------- layout

# Every visible word on the page, in reading order (for the word count).
WORDS = (
    "THE WORLD TODAY".split()
    + "THURSDAY 26 NOVEMBER 2026".split()
    + ["14"]
    + "14 NEW US TARIFFS".split()
    + "USTR PROPOSES DUTIES ON PARTNERS".split()
    + "NORTH AMERICA".split()
    + ["REUTERS"]
    + "HOUTHIS HIT RAS TANURA OIL PORT".split()
    + "MIDDLE EAST".split()
    + ["REUTERS"]
    + "FIRST PAKISTANI REACHES TIANGONG".split()
    + ["ASIA"]
    + ["REUTERS"]
    + "EU SPLIT OVER \u20ac45 BN UKRAINE LOAN".split()
    + ["EUROPE"]
    + "NEWS WIRES".split()
    + "13 MINERS TRAPPED IN FLOODED BOGOR MINE".split()
    + "SOUTHEAST ASIA".split()
    + ["REUTERS"]
)

CARDS = [
    # (x, y, headline, chip, source, pictogram)
    (24, 556, "HOUTHIS HIT RAS TANURA OIL PORT",
     "MIDDLE EAST", "REUTERS", pic_port),
    (520, 556, "FIRST PAKISTANI REACHES TIANGONG",
     "ASIA", "REUTERS", pic_rocket),
    (24, 796, "EU SPLIT OVER \u20ac45 BN UKRAINE LOAN",
     "EUROPE", "NEWS WIRES", pic_parliament),
    (520, 796, "13 MINERS TRAPPED IN FLOODED BOGOR MINE",
     "SOUTHEAST ASIA", "REUTERS", pic_mine),
]


def draw_card(x0, y0, headline, chip, source, pic):
    # card body + 6 px ink border
    fill_rect(x0, y0, x0 + 480, y0 + 224, PAPER)
    fill_rect(x0, y0, x0 + 480, y0 + 6, INK)
    fill_rect(x0, y0 + 218, x0 + 480, y0 + 224, INK)
    fill_rect(x0, y0, x0 + 6, y0 + 224, INK)
    fill_rect(x0 + 474, y0, x0 + 480, y0 + 224, INK)
    ix, iy = x0 + 6, y0 + 6  # inner origin; inner box is 468 x 212
    # pictogram top-left, source top-right
    pic(ix + 10, iy + 8)
    draw_text(ix + 154, iy + 20, 5, 5, source, INK)
    # headline, two lines, condensed (sx 4, sy 5 -> cap 35)
    lines = wrap_words(headline, 109)
    draw_text(ix + 10, iy + 76, 4, 5, lines[0], INK)
    draw_text(ix + 10, iy + 123, 4, 5, lines[1], INK)
    # region chip: teal pill, paper text
    cw = text_width(chip, 5)
    fill_rect(ix + 10, iy + 170, ix + 10 + cw + 32, iy + 211, TEAL)
    draw_text(ix + 26, iy + 174, 5, 5, chip, PAPER)


def draw():
    # masthead
    draw_text_centered(512, 20, 8, 8, "THE WORLD TODAY", INK)
    fill_rect(0, 88, 1024, 94, RED)
    # date band
    fill_rect(0, 96, 1024, 160, RED)
    draw_text_centered(512, 109, 6, 6, "THURSDAY 26 NOVEMBER 2026", PAPER)
    # hero: giant number + headline + subline + chip + source + ship
    draw_text(48, 186, 22, 22, "14", RED)
    draw_text(280, 196, 12, 12, "14 NEW US", INK)
    draw_text(280, 306, 12, 12, "TARIFFS", INK)
    draw_text_centered(512, 416, 5, 5, "USTR PROPOSES DUTIES ON PARTNERS", INK)
    cw = text_width("NORTH AMERICA", 5)
    fill_rect(48, 470, 48 + cw + 32, 514, RED)
    draw_text(64, 474, 5, 5, "NORTH AMERICA", PAPER)
    draw_text(48 + cw + 32 + 24, 474, 5, 5, "REUTERS", INK)
    pic_ship(700, 436)
    # four story cards
    for (x0, y0, headline, chip, source, pic) in CARDS:
        draw_card(x0, y0, headline, chip, source, pic)


# ---------------------------------------------------------------- PNG writer

def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def write_png(path):
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    raw = bytearray()
    for y in range(H):
        raw.append(0)  # filter: none
        raw += buf[y * W * 3:(y + 1) * W * 3]
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", ihdr)
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += _chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "out")
    os.makedirs(out_dir, exist_ok=True)
    draw()
    path = os.path.join(out_dir, "entry.png")
    size = write_png(path)
    import hashlib
    sha = hashlib.sha256(open(path, "rb").read()).hexdigest()
    print("wrote %s (%d bytes, %dx%d)" % (path, size, W, H))
    print("sha256 %s" % sha)
    print("words on page: %d" % len(WORDS))


if __name__ == "__main__":
    main()
