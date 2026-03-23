#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Odd-Letter Spot — Visual Mini‑Game (Find the only different token)
=================================================================
在一大片相同字母的网格里，只有**一个格子**的字母串不同；玩家需要找出该格并读出那组字母作为答案。
- 纯文字、极简风格；默认无标题、无网格线。
- 支持 1~3 个字符的“字母组”（例如 A / AA / AAA）。
- 可通过 `--answer_token` 指定那组不同的字母；否则自动生成（与底板不同）。
- 支持自定义手写体 `--font_path`。

示例：
    python 5_odd_letter.py --out_dir ./5_output_m --num 1 \
      --rows 8 --cols 12 --token_len 1 --seed 42 --answer_token m

输出：每题一张 PNG + JSON（包含 `answer_token`、`answer_pos` 行列坐标、底板 token 等）。
"""
from __future__ import annotations

import os
import json
import random
import argparse
from typing import List, Tuple, Dict, Any

from PIL import Image, ImageDraw, ImageFont

SAFE_ALPHA = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"  # 避免 I/O/Q 混淆
NAVY = (22, 58, 120)
BG   = (245, 245, 232)

# ---------------- Font helpers ----------------

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


def fit_font(draw: ImageDraw.ImageDraw, text: str, max_w: int, max_h: int, base: int, min_size:int=10) -> ImageFont.ImageFont:
    s = base
    while s >= min_size:
        f = load_font(s)
        w,h = text_size(draw, text, f)
        if w <= max_w and h <= max_h:
            return f
        s -= 1
    return load_font(min_size)

# ---------------- Generation ----------------

def make_base_token(rnd: random.Random, token_len:int, base_char:str|None=None) -> str:
    if base_char is None:
        base_char = rnd.choice(SAFE_ALPHA)
    else:
        base_char = base_char.upper()
        if base_char not in SAFE_ALPHA:
            raise ValueError("base_char must be in SAFE_ALPHA")
    return base_char * token_len


def mutate_token(rnd: random.Random, base: str) -> str:
    """变成与 base 不同的 token：
    - 单字符：换成别的安全字母
    - 多字符：随机挑若干位置把字母换成别的
    保证结果 != base。
    """
    if len(base) == 1:
        choices = [c for c in SAFE_ALPHA if c != base]
        return rnd.choice(choices)
    token = list(base)
    # 改变 1~len(base) 中的 1 或 2 个位置（尽量只改 1 个以保证难度）
    k = 1 if len(base) <= 2 else rnd.choice([1,2])
    idxs = rnd.sample(range(len(base)), k=k)
    for i in idxs:
        choices = [c for c in SAFE_ALPHA if c != token[i]]
        token[i] = rnd.choice(choices)
    out = "".join(token)
    if out == base:
        # 极小概率回到了原值，强制再改一位
        j = rnd.randrange(len(base))
        choices = [c for c in SAFE_ALPHA if c != token[j]]
        token[j] = rnd.choice(choices)
        out = "".join(token)
    return out

# ---------------- Rendering ----------------

def render_grid(
    out_png: str,
    rows:int, cols:int,
    tokens: List[List[str]],
    cell_w:int=100, cell_h:int=100,
    margin:int=60,
    font_path: str | None = None,
    draw_grid_lines: bool = False,
):
    W = margin*2 + cols*cell_w
    H = margin*2 + rows*cell_h
    img = Image.new("RGB", (W,H), BG)
    d = ImageDraw.Draw(img)

    if draw_grid_lines:
        for r in range(rows+1):
            y = margin + r*cell_h
            d.line((margin, y, W-margin, y), fill=(215,215,205), width=1)
        for c in range(cols+1):
            x = margin + c*cell_w
            d.line((x, margin, x, H-margin), fill=(215,215,205), width=1)

    # Draw tokens centered
    for r in range(rows):
        for c in range(cols):
            txt = tokens[r][c]
            max_w = cell_w - 12
            max_h = cell_h - 12
            f = fit_font(d, txt, max_w, max_h, base=min(72, int(cell_h*0.7)))
            tw, th = text_size(d, txt, f)
            x = margin + c*cell_w + (cell_w - tw)//2
            y = margin + r*cell_h + (cell_h - th)//2
            d.text((x, y), txt, fill=NAVY, font=f)

    img.save(out_png)

# ---------------- Orchestration ----------------

def generate_one(
    out_dir: str,
    seed: int,
    rows:int=8, cols:int=12,
    token_len:int=2,
    answer_token: str | None = None,
    base_char: str | None = None,
    font_path: str | None = None,
    draw_grid_lines: bool = False,
    index:int|None=None,
) -> Dict[str,Any]:
    os.makedirs(out_dir, exist_ok=True)
    rnd = random.Random(seed)

    if token_len < 1 or token_len > 3:
        raise ValueError("token_len must be 1..3")

    base_token = make_base_token(rnd, token_len, base_char)
    if answer_token is not None:
        answer_token = answer_token.upper()
        if len(answer_token) != token_len:
            raise ValueError("answer_token length must equal token_len")
        if answer_token == base_token:
            raise ValueError("answer_token must differ from base_token")
        # ensure all chars safe
        for ch in answer_token:
            if ch not in SAFE_ALPHA:
                raise ValueError("answer_token must use safe letters: " + SAFE_ALPHA)
        odd = answer_token
    else:
        odd = mutate_token(rnd, base_token)

    # place odd at random pos
    rr = rnd.randrange(rows)
    cc = rnd.randrange(cols)

    tokens = [[base_token for _ in range(cols)] for _ in range(rows)]
    tokens[rr][cc] = odd

    base = f"odd_{index:04d}" if index is not None else f"odd_seed{seed}"
    png = os.path.join(out_dir, base + ".png")
    jsn = os.path.join(out_dir, base + ".json")

    render_grid(png, rows, cols, tokens, font_path=font_path, draw_grid_lines=draw_grid_lines)

    meta = {
        "type": "odd_letter_spot",
        "rows": rows, "cols": cols,
        "token_len": token_len,
        "base_token": base_token,
        "answer_token": odd,
        "answer_pos": [rr, cc],  # 0-indexed (row, col)
        "image_path": png,
        "seed": seed,
        "params": {
            "base_char": (base_char.upper() if base_char else None),
            "draw_grid_lines": bool(draw_grid_lines)
        }
    }

    with open(jsn, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    return meta


def generate_batch(
    out_dir: str,
    num:int,
    seed:int=0,
    rows:int=8, cols:int=12,
    token_len:int=2,
    answer_token: str | None = None,
    base_char: str | None = None,
    font_path: str | None = None,
    draw_grid_lines: bool = False,
    summary_jsonl: str | None = None,
) -> List[Dict[str,Any]]:
    metas: List[Dict[str,Any]] = []
    for i in range(num):
        meta = generate_one(
            out_dir=out_dir,
            seed=seed + i,
            rows=rows, cols=cols,
            token_len=token_len,
            answer_token=answer_token,
            base_char=base_char,
            font_path=font_path,
            draw_grid_lines=draw_grid_lines,
            index=i+1,
        )
        metas.append(meta)

    if summary_jsonl:
        with open(os.path.join(out_dir, summary_jsonl), "w", encoding="utf-8") as f:
            for m in metas:
                f.write(json.dumps(m, ensure_ascii=False) + "\n")
    return metas

# ---------------- CLI ----------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Odd-letter spot puzzle generator")
    p.add_argument("--out_dir", type=str, default="./out_odd")
    p.add_argument("--num", type=int, default=8)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--rows", type=int, default=8)
    p.add_argument("--cols", type=int, default=12)
    p.add_argument("--token_len", type=int, default=2, help="Length of each token (1..3)")
    p.add_argument("--answer_token", type=str, default=None, help="Explicit odd token (length must equal token_len)")
    p.add_argument("--base_char", type=str, default=None, help="Base letter to repeat (single A-Z from SAFE set)")
    p.add_argument("--font_path", type=str, default=None)
    p.add_argument("--draw_grid_lines", action="store_true", help="Draw faint grid lines")
    p.add_argument("--summary", type=str, default="summary.jsonl")
    return p.parse_args()


def main():
    args = parse_args()
    generate_batch(
        out_dir=args.out_dir,
        num=args.num,
        seed=args.seed,
        rows=args.rows, cols=args.cols,
        token_len=args.token_len,
        answer_token=args.answer_token,
        base_char=args.base_char,
        font_path=args.font_path,
        draw_grid_lines=args.draw_grid_lines,
        summary_jsonl=args.summary,
    )
    print(f"Done. Wrote {args.num} samples to {args.out_dir}")

if __name__ == "__main__":
    main()
