#!/usr/bin/env python3
"""Compose the front cover: typography overlay on the generated cover artwork."""
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
BOOK = ROOT / 'books/eat-well-live-well-prostate'
SRC = BOOK / 'assets/cover-art.png'
DST = BOOK / 'assets/cover-final.png'

FONT_DIR = Path('/usr/share/fonts/truetype/dejavu')
F_BOLD = FONT_DIR / 'DejaVuSans-Bold.ttf'
F_SERIF_BOLD = FONT_DIR / 'DejaVuSerif-Bold.ttf'
F_SERIF = FONT_DIR / 'DejaVuSerif.ttf'
F_SANS = FONT_DIR / 'DejaVuSans.ttf'

INK = (23, 44, 59)          # deep navy
TEAL = (23, 107, 112)
GOLD = (183, 122, 36)
CREAM = (250, 247, 240)
WHITE = (255, 255, 255)
MUTED = (206, 218, 222)


def load_font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size)


def text_size(draw: ImageDraw.ImageDraw, text: str, font) -> tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def wrap(draw, text: str, font, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    cur = words[0]
    for w in words[1:]:
        trial = cur + ' ' + w
        if text_size(draw, trial, font)[0] <= max_width:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


def main() -> None:
    im = Image.open(SRC).convert('RGB')
    W, H = im.size
    # Scale artwork to a 2:3 trade-book cover canvas if needed.
    target_w = 1600
    target_h = 2400
    if (W, H) != (target_w, target_h):
        im = im.resize((target_w, target_h), Image.LANCZOS)
        W, H = target_w, target_h

    # Bottom scrim: deep ink gradient for text legibility.
    scrim = Image.new('L', (1, H), 0)
    for y in range(H):
        t = y / (H - 1)
        if t < 0.30:
            a = 0
        elif t < 0.46:
            u = (t - 0.30) / 0.16
            a = int(120 * u)
        else:
            u = (t - 0.46) / 0.54
            a = int(120 + 130 * (u ** 1.2))
        scrim.putpixel((0, y), min(a, 245))
    scrim = scrim.resize((W, H))
    ink_layer = Image.new('RGB', (W, H), INK)
    im = Image.composite(ink_layer, im, scrim)

    # Top-left subtle brand band.
    band_h = int(H * 0.085)
    band = Image.new('RGB', (W, H), INK)
    band_mask = Image.new('L', (W, H), 0)
    bd = ImageDraw.Draw(band_mask)
    bd.rectangle([0, 0, W, band_h], fill=190)
    band_mask = band_mask.filter(ImageFilter.GaussianBlur(6))
    im = Image.composite(band, im, band_mask)

    draw = ImageDraw.Draw(im)

    # Kicker in band.
    kicker_font = load_font(F_BOLD, 34)
    kicker = 'A COMPREHENSIVE EVIDENCE-BASED TEXTBOOK'
    kw, _ = text_size(draw, kicker, kicker_font)
    draw.text(((W - kw) // 2, int(band_h * 0.30)), kicker, font=kicker_font, fill=MUTED)

    # Title block.
    title_lines = [
        'EAT WELL,',
        'LIVE WELL,',
        'PROTECT YOUR',
        'PROSTATE',
    ]
    title_font = load_font(F_SERIF_BOLD, 132)
    line_h = 150
    title_top = int(H * 0.475)
    # Accent rule above the title.
    rule_y = title_top - 46
    draw.line([(W // 2 - 260, rule_y), (W // 2 + 260, rule_y)], fill=GOLD, width=5)

    y = title_top
    for line in title_lines:
        tw, _ = text_size(draw, line, title_font)
        x = (W - tw) // 2
        # soft shadow for depth
        draw.text((x + 3, y + 4), line, font=title_font, fill=(8, 16, 22))
        draw.text((x, y), line, font=title_font, fill=WHITE)
        y += line_h

    # Subtitle.
    sub_font = load_font(F_SERIF, 41)
    sub = ('A Comprehensive Guide to Prostate-Friendly Nutrition, Healthy Sexual '
           'Living, Weight Management, and Practical Strategies for Reducing '
           'Urinary Symptoms')
    sub_lines = wrap(draw, sub, sub_font, int(W * 0.80))
    y += 34
    for line in sub_lines:
        tw, _ = text_size(draw, line, sub_font)
        draw.text(((W - tw) // 2, y), line, font=sub_font, fill=CREAM)
        y += 56

    # Author / imprint.
    author_font = load_font(F_BOLD, 40)
    author = 'TRIUNE BIBLICAL UNIVERSITY GLOBAL EXTENSION USA'
    aw, _ = text_size(draw, author, author_font)
    ay = H - 150
    draw.line([(W // 2 - 300, ay - 34), (W // 2 + 300, ay - 34)], fill=GOLD, width=3)
    draw.text(((W - aw) // 2, ay), author, font=author_font, fill=WHITE)

    im.save(DST, 'PNG', optimize=True)
    print(f'wrote {DST} ({W}x{H})')


if __name__ == '__main__':
    main()
