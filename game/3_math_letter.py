#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Minimal Symbol‑Shift Puzzle — EXACT look (no extra UI)
===================================================

Usage:
  python 3_math_letter.py --out_dir ./3_output_B --num 1 \
    --target_answer B --circle 2 --triangle 4 --seed 7

可选： --font_path 指定手写体 TTF（若不提供，使用系统常见字体）。
"""
from __future__ import annotations

import os
import json
import random
import argparse
from typing import Tuple, Dict, Any

from PIL import Image, ImageDraw, ImageFont

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

# ---------------------------- text & font ----------------------------

def load_font(size: int, font_path: str | None = None) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    if font_path and os.path.exists(font_path):
        try:
            return ImageFont.truetype(font_path, size=size)
        except Exception:
            pass
    for p in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf",
        "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Helvetica.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size=size)
            except Exception:
                pass
    return ImageFont.load_default()


def text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> Tuple[int,int]:
    l,t,r,b = draw.textbbox((0,0), text, font=font)
    return r-l, b-t

# ---------------------------- alphabet ops ----------------------------

def shift_letter(letter: str, k: int) -> str:
    letter = letter.upper()
    assert len(letter) == 1 and letter in ALPHABET
    idx = ALPHABET.index(letter)
    return ALPHABET[(idx + k) % 26]

# ---------------------------- shapes ----------------------------
RED = (230, 62, 54)
BLUE = (45, 123, 217)
NAVY = (22, 58, 120)
BG = (245, 245, 232)


def draw_red_circle(draw: ImageDraw.ImageDraw, bbox: Tuple[int,int,int,int]):
    draw.ellipse(bbox, outline=RED, width=6)


def draw_blue_triangle(draw: ImageDraw.ImageDraw, bbox: Tuple[int,int,int,int]):
    x0,y0,x1,y1 = bbox
    cx = (x0 + x1)//2
    pts = [(cx, y0), (x1, y1), (x0, y1)]
    draw.line([pts[0], pts[1]], fill=BLUE, width=6)
    draw.line([pts[1], pts[2]], fill=BLUE, width=6)
    draw.line([pts[2], pts[0]], fill=BLUE, width=6)

# ---------------------------- render one ----------------------------

def render_minimal(
    out_png: str,
    lines: Dict[str,Any],  # structured content
    size=(1010, 768),
    font_path: str | None = None,
):
    W,H = size
    img = Image.new("RGB", (W,H), BG)
    d = ImageDraw.Draw(img)

    # fonts（可切换手写体）
    big = load_font(120, font_path)   # letters
    sym = load_font(110, font_path)   # + - = ?

    # layout
    left_x = 90
    y0 = 100
    vgap = 140

    def draw_equation(y, L: str, op: str, shape: str, R: str):
        d.text((left_x, y), L, fill=NAVY, font=big)
        d.text((left_x+110, y), op, fill=NAVY, font=sym)
        sx0 = left_x + 230
        sx1 = sx0 + 120
        sy0 = y + 6
        sy1 = sy0 + 120
        if shape == 'circle':
            draw_red_circle(d, (sx0, sy0, sx1, sy1))
        elif shape == 'triangle':
            draw_blue_triangle(d, (sx0, sy0, sx1, sy1))
        d.text((sx1 + 40, y), '=', fill=NAVY, font=sym)
        d.text((sx1 + 160, y), R, fill=NAVY, font=big)

    def draw_final(y, base: str, shapes: list):
        d.text((left_x, y), base, fill=NAVY, font=big)
        curx = left_x + 110
        for shp in shapes:
            d.text((curx, y), '+', fill=NAVY, font=sym)
            curx += 120
            sx0 = curx
            sx1 = sx0 + 120
            sy0 = y + 6
            sy1 = sy0 + 120
            if shp == 'circle':
                draw_red_circle(d, (sx0, sy0, sx1, sy1))
            elif shp == 'triangle':
                draw_blue_triangle(d, (sx0, sy0, sx1, sy1))
            curx = sx1 + 40
        d.text((curx, y), '=', fill=NAVY, font=sym)
        d.text((curx + 120, y), '?', fill=NAVY, font=sym)

    # --- lines (仅四行) ---
    draw_equation(y0 + 0*vgap, lines['eq1']['L'], '+', 'circle',   lines['eq1']['R'])
    draw_equation(y0 + 1*vgap, lines['eq2']['L'], '-', 'circle',   lines['eq2']['R'])
    draw_equation(y0 + 2*vgap, lines['eq3']['L'], '+', 'triangle', lines['eq3']['R'])
    draw_final   (y0 + 3*vgap, lines['final']['base'], ['circle','triangle'])

    img.save(out_png)

# ---------------------------- pipeline ----------------------------

def validate_letter(x: str) -> str:
    if not x or len(x) != 1 or x.upper() not in ALPHABET:
        raise argparse.ArgumentTypeError('letter must be A-Z')
    return x.upper()


def generate_one(
    out_dir: str,
    seed: int,
    target_answer: str,
    circle: int | None,
    triangle: int | None,
    index: int,
    font_path: str | None,
) -> Dict[str,Any]:
    os.makedirs(out_dir, exist_ok=True)
    rnd = random.Random(seed)

    cshift = circle if circle is not None else rnd.randint(1,5)
    tshift = triangle if triangle is not None else rnd.randint(1,5)

    # hints letters固定 A、A、B；右值按位移计算，保证自洽
    eq1_L = 'A'; eq1_R = shift_letter(eq1_L,  cshift)
    eq2_L = 'A'; eq2_R = shift_letter(eq2_L, -cshift)
    eq3_L = 'B'; eq3_R = shift_letter(eq3_L,  tshift)

    # Final: base + cshift + tshift = target
    base = shift_letter(target_answer, -(cshift + tshift))

    png = os.path.join(out_dir, f"math_letter_{index:04d}.png")
    jsonp = os.path.join(out_dir, f"math_letter_{index:04d}.json")

    lines = {
        'eq1': {'L': eq1_L, 'R': eq1_R},
        'eq2': {'L': eq2_L, 'R': eq2_R},
        'eq3': {'L': eq3_L, 'R': eq3_R},
        'final': {'base': base}
    }

    render_minimal(png, lines, font_path=font_path)

    meta: Dict[str,Any] = {
        'type': 'symbol_shift_minimal',
        'target_answer': target_answer,
        'circle_shift': int(cshift),
        'triangle_shift': int(tshift),
        'final': {
            'base': base,
            'ops': ['circle','triangle'],
            'sum_shift': int(cshift + tshift)
        },
        'hints': [
            {'lhs':'A','op':'circle','rhs':eq1_R},
            {'lhs':'A','op':'-circle','rhs':eq2_R},
            {'lhs':'B','op':'triangle','rhs':eq3_R}
        ],
        'image_path': png,
        'seed': seed
    }

    # sanity check
    check = shift_letter(base, cshift + tshift)
    assert check == target_answer, f"computed {check} != target {target_answer}"

    with open(jsonp, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    return meta


def generate_batch(out_dir: str, num: int, seed: int, target_answer: str, circle: int|None, triangle: int|None, font_path: str | None):
    metas = []
    for i in range(1, num+1):
        metas.append(generate_one(out_dir, seed+(i-1), target_answer, circle, triangle, i, font_path))
    with open(os.path.join(out_dir, 'summary.jsonl'), 'w', encoding='utf-8') as f:
        for m in metas:
            f.write(json.dumps(m, ensure_ascii=False) + '')
    return metas

# ---------------------------- CLI ----------------------------

def parse_args():
    p = argparse.ArgumentParser(description='Minimal symbol-shift puzzle (exact look)')
    p.add_argument('--out_dir', type=str, default='./out_symmin')
    p.add_argument('--num', type=int, default=4)
    p.add_argument('--seed', type=int, default=0)
    p.add_argument('--target_answer', type=validate_letter, required=True)
    p.add_argument('--circle', type=int, default=None, help='Shift for red circle (1..25)')
    p.add_argument('--triangle', type=int, default=None, help='Shift for blue triangle (1..25)')
    p.add_argument('--font_path', type=str, default=None, help='Optional handwriting TTF path')
    return p.parse_args()


def main():
    args = parse_args()
    generate_batch(args.out_dir, args.num, args.seed, args.target_answer, args.circle, args.triangle, args.font_path)
    print(f'Done. Wrote {args.num} samples to {args.out_dir}')

if __name__ == '__main__':
    main()
