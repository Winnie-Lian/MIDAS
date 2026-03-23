#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Compass Grid — Visual Reasoning Mini‑Game Generator (Color‑Cued Start, Strict)
=============================================================================
Example CLI usage:
    python 1_compass.py --out_dir ./1_ouput_o --num 1 --grid 5 \
      --min_steps 1 --max_steps 2 --seed 73 --ensure_end_diff --min_manhattan 1 \
    --target_answer o

"""
from __future__ import annotations

import os
import json
import random
import argparse
from typing import List, Tuple, Dict, Any

from PIL import Image, ImageDraw, ImageFont

# ---------------------------- Drawing helpers ----------------------------

def try_load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Helvetica.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size=size)
            except Exception:
                pass
    return ImageFont.load_default()


def draw_centered_text(draw: ImageDraw.ImageDraw, xy: Tuple[int, int], text: str, font: ImageFont.ImageFont, fill=(0,0,0)) -> None:
    left, top, right, bottom = draw.textbbox((0,0), text, font=font)
    w, h = right - left, bottom - top
    x, y = xy
    draw.text((x - w//2, y - h//2), text, fill=fill, font=font)


def draw_compass(draw: ImageDraw.ImageDraw, x: int, y: int, r: int, font: ImageFont.ImageFont) -> None:
    draw.ellipse((x - r, y - r, x + r, y + r), outline=(30,30,30), width=2)
    draw.line((x, y - r + 4, x, y + r - 4), fill=(30,30,30), width=2)
    draw.line((x - r + 4, y, x + r - 4, y), fill=(30,30,30), width=2)
    draw_centered_text(draw, (x, y - r - 12), "N", font)
    draw_centered_text(draw, (x + r + 12, y), "E", font)
    draw_centered_text(draw, (x, y + r + 8), "S", font)
    draw_centered_text(draw, (x - r - 12, y), "W", font)


# ---------------------------- Core generation ----------------------------

def _valid_options(grid:int, r:int, c:int, max_stride:int) -> List[Tuple[str,int]]:
    opts: List[Tuple[str,int]] = []
    for d in ("N","E","S","W"):
        if d == "N":
            max_legal = min(max_stride, r)
        elif d == "S":
            max_legal = min(max_stride, grid - 1 - r)
        elif d == "W":
            max_legal = min(max_stride, c)
        else:  # E
            max_legal = min(max_stride, grid - 1 - c)
        for s in range(1, max_legal + 1):
            opts.append((d, s))
    return opts


def gen_moves_strict(
    rnd: random.Random,
    grid: int,
    start: Tuple[int,int],
    min_steps: int,
    max_steps: int,
    max_stride: int = 3,
    ensure_end_diff: bool = True,
    min_manhattan: int = 0,
    max_attempts: int = 512,
) -> List[str]:
    for _ in range(max_attempts):
        n_moves = rnd.randint(min_steps, max_steps)
        r, c = start
        seq: List[str] = []
        prev_d = None
        success = True
        for _ in range(n_moves):
            options = _valid_options(grid, r, c, max_stride)
            if prev_d:
                opposites = {"N":"S","S":"N","E":"W","W":"E"}
                options = [(d,s) for (d,s) in options if d != opposites.get(prev_d, "")] or options
            if not options:
                success = False
                break
            d, s = rnd.choice(options)
            seq.append(f"{d}{s}")
            prev_d = d
            if d == "N": r -= s
            elif d == "S": r += s
            elif d == "W": c -= s
            else: c += s
        if not success:
            continue
        end_r, end_c = r, c
        if ensure_end_diff and (end_r, end_c) == start:
            continue
        if abs(end_r - start[0]) + abs(end_c - start[1]) < min_manhattan:
            continue
        return seq
    raise RuntimeError("Failed to generate a legal move sequence under constraints.")


def apply_moves_strict(grid: int, start: Tuple[int,int], moves: List[str]) -> Tuple[int,int,List[Tuple[int,int]]]:
    r, c = start
    coords = [(r, c)]
    for token in moves:
        d = token[0]
        s = int(token[1:])
        if d == "N": r -= s
        elif d == "S": r += s
        elif d == "W": c -= s
        else: c += s
        assert 0 <= r < grid and 0 <= c < grid, "Move sequence left the grid!"
        coords.append((r, c))
    return r, c, coords


def unique_code_grid(rnd: random.Random, grid: int, pair_len:int=2) -> List[List[str]]:
    alphabet = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
    used = set()
    G: List[List[str]] = []
    for _ in range(grid):
        row: List[str] = []
        for _ in range(grid):
            while True:
                
                 # 随机生成长度为2-4的代码
                code_len = rnd.randint(1, 2)
                code = "".join(rnd.choice(alphabet) for _ in range(code_len))
                if code not in used:
                    used.add(code)
                    row.append(code)
                    break
        G.append(row)
    return G


def pick_distractors(rnd: random.Random, grid:int, start:Tuple[int,int], end:Tuple[int,int], k_range=(1,2)) -> List[Tuple[int,int,Tuple[int,int,int]]]:
    """Pick 1–2 non-start, non-end cells to color as distractors. Return list of (r,c,fill_rgb)."""
    palette = [
        (253, 236, 200),  # light orange
        (205, 230, 255),  # light blue
        (230, 210, 255),  # lavender
        (255, 210, 220),  # pink
        (235, 235, 235),  # light gray
        (255, 243, 207),  # light yellow
    ]
    k = rnd.randint(*k_range)
    chosen: List[Tuple[int,int,Tuple[int,int,int]]] = []
    used = {start, end}
    attempts = 0
    while len(chosen) < k and attempts < 200:
        attempts += 1
        r = rnd.randrange(grid)
        c = rnd.randrange(grid)
        if (r, c) in used:
            continue
        used.add((r, c))
        fill = rnd.choice(palette)
        chosen.append((r, c, fill))
    return chosen


# ---------------------------- Rendering ----------------------------

def _wrap_tokens_to_lines(draw: ImageDraw.ImageDraw, tokens: List[str], font: ImageFont.ImageFont, max_width: int) -> List[str]:
    lines: List[str] = []
    cur: List[str] = []
    for t in tokens:
        test = ", ".join(cur + [t])
        w = draw.textlength(test, font=font)
        if w <= max_width or not cur:
            cur.append(t)
        else:
            lines.append(", ".join(cur))
            cur = [t]
    if cur:
        lines.append(", ".join(cur))
    return lines


def _fit_code_font(draw: ImageDraw.ImageDraw, code: str, max_w: int, max_h:int, base_size:int) -> ImageFont.ImageFont:
    size = base_size
    while size >= 10:
        f = try_load_font(size)
        left, top, right, bottom = draw.textbbox((0,0), code, font=f)
        w, h = right - left, bottom - top
        if w <= max_w and h <= max_h:
            return f
        size -= 1
    return try_load_font(10)


def render_sample(
    grid: int,
    cell_size: int,
    start: Tuple[int,int],
    moves: List[str],
    codes: List[List[str]],
    out_path_png: str,
    start_fill=(208, 244, 215),      # light green
    start_text=(17, 135, 74),        # green text
    distractors: List[Tuple[int,int,Tuple[int,int,int]]] | None = None,
    show_path: bool = False,
) -> None:
    margin = 40
    header_h = 132
    gutter = 2

    W = margin * 2 + grid * cell_size
    H = header_h + margin + grid * cell_size + margin

    img = Image.new("RGB", (W, H), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Fonts
    title_font = try_load_font(28)
    small_font = try_load_font(22)
    code_base = max(22, cell_size // 3)

    # Header bar
    draw.rectangle((0, 0, W, header_h), fill=(240, 242, 247))

    # Moves with wrapping (reserve right space for compass)
    usable_w = W - 40 - 130
    lines = _wrap_tokens_to_lines(draw, moves, title_font, usable_w)
    y = 12
    for i, line in enumerate(lines[:2]):
        prefix = "Moves: " if i == 0 else ""
        draw.text((margin, y), prefix + line, fill=(10,10,10), font=title_font)
        y += 36
    # Explicit instruction about GREEN start
    note1 = "Start from the GREEN cell"
    draw.text((margin, y), note1, fill=(10,120,10), font=title_font)
    y += 34
    note2 = "Follow moves in order and read the destination code."
    draw.text((margin, y), note2, fill=(80,80,80), font=small_font)

    # Compass
    draw_compass(draw, W - 60, header_h//2, 22, small_font)

    # Grid origin
    gx0, gy0 = margin, header_h + margin

    def cell_bbox(r: int, c: int) -> Tuple[int,int,int,int]:
        x0 = gx0 + c * cell_size + gutter
        y0 = gy0 + r * cell_size + gutter
        x1 = x0 + cell_size - 2*gutter
        y1 = y0 + cell_size - 2*gutter
        return x0, y0, x1, y1

    # --- Cell backgrounds (start + distractors) BEFORE grid lines ---
    sr, sc = start
    # Start cell fill
    sx0, sy0, sx1, sy1 = cell_bbox(sr, sc)
    draw.rectangle((sx0, sy0, sx1, sy1), fill=start_fill)

    # # Distractors
    # if distractors:
    #     for (dr, dc, fill) in distractors:
    #         x0, y0, x1, y1 = cell_bbox(dr, dc)
    #         draw.rectangle((x0, y0, x1, y1), fill=fill)

    # Grid lines on top
    for i in range(grid + 1):
        yline = gy0 + i * cell_size
        draw.line((gx0, yline, gx0 + grid * cell_size, yline), fill=(120, 120, 120), width=1)
        xline = gx0 + i * cell_size
        draw.line((xline, gy0, xline, gy0 + grid * cell_size), fill=(120, 120, 120), width=1)

    # Draw centered codes
    pad = 12  # inner padding for font fit
    for r in range(grid):
        for c in range(grid):
            code = codes[r][c]
            x0, y0, x1, y1 = cell_bbox(r, c)
            max_w = (x1 - x0) - pad*2
            max_h = (y1 - y0) - pad*2
            f = _fit_code_font(draw, code, max_w, max_h, code_base)
            cx = (x0 + x1)//2
            cy = (y0 + y1)//2
            # Start cell uses green text, others black
            color = start_text if (r, c) == (sr, sc) else (20, 20, 20)
            draw_centered_text(draw, (cx, cy), code, f, fill=color)

    # Optional path overlay for debugging（连格中心）
    if show_path and moves:
        # 注意：为避免遮挡代码，使用较细线
        r0, c0 = sr, sc
        pts = []
        for token in moves:
            x0, y0, x1, y1 = cell_bbox(r0, c0)
            pts.append(((x0 + x1)//2, (y0 + y1)//2))
            d = token[0]
            s = int(token[1:])
            if d == "N": r0 -= s
            elif d == "S": r0 += s
            elif d == "W": c0 -= s
            else: c0 += s
        x0, y0, x1, y1 = cell_bbox(r0, c0)
        pts.append(((x0 + x1)//2, (y0 + y1)//2))
        draw.line(pts, fill=(255, 99, 71), width=2)

    img.save(out_path_png)


# ---------------------------- Orchestration ----------------------------

def generate_one(
    out_dir: str,
    seed: int,
    grid: int = 5,
    cell_size: int = 120,
    min_steps: int = 3,
    max_steps: int = 6,
    max_stride: int = 3,
    min_manhattan: int = 0,
    ensure_end_diff: bool = True,
    show_path: bool = False,
    index: int | None = None,
    target_answer: str | None = None,  # 新增参数：指定答案
) -> Dict[str, Any]:
    os.makedirs(out_dir, exist_ok=True)
    rnd = random.Random(seed)

    start = (rnd.randrange(grid), rnd.randrange(grid))
    moves = gen_moves_strict(
        rnd, grid, start,
        min_steps=min_steps, max_steps=max_steps, max_stride=max_stride,
        ensure_end_diff=ensure_end_diff, min_manhattan=min_manhattan
    )
    end_r, end_c, coords = apply_moves_strict(grid, start, moves)

    codes = unique_code_grid(rnd, grid)
    
    # 如果指定了目标答案，则替换终点位置的代码
    if target_answer is not None:
        codes[end_r][end_c] = target_answer
        answer = target_answer
    else:
        answer = codes[end_r][end_c]

    # Distractor color blocks
    distractor_cells = pick_distractors(rnd, grid, start, (end_r, end_c))

    # filenames
    base = f"cg_{index:04d}" if index is not None else f"cg_seed{seed}"
    img_path = os.path.join(out_dir, base + ".png")
    json_path = os.path.join(out_dir, base + ".json")

    render_sample(
        grid, cell_size, start, moves, codes, img_path,
        distractors=distractor_cells, show_path=show_path,
    )

    meta = {
        "type": "compass_grid",
        "grid_size": grid,
        "cell_size": cell_size,
        "start": list(start),
        "moves": moves,
        "answer_cell": [end_r, end_c],
        "answer": answer,
        "codes": codes,
        "image_path": img_path,
        "seed": seed,
        "path_coords": coords,
        "colored_cells": {
            "start": {"row": start[0], "col": start[1], "fill": [208,244,215], "text": [17,135,74]},
            "distractors": [{"row": r, "col": c, "fill": list(fill)} for (r,c,fill) in distractor_cells]
        }
    }

    assert 0 <= end_r < grid and 0 <= end_c < grid, "End cell out of bounds"
    assert answer == codes[end_r][end_c], "Answer/code mismatch"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    return meta


def generate_batch(
    out_dir: str,
    num: int,
    seed: int = 0,
    grid: int = 5,
    cell_size: int = 120,
    min_steps: int = 3,
    max_steps: int = 6,
    max_stride: int = 3,
    min_manhattan: int = 0,
    ensure_end_diff: bool = True,
    show_path: bool = False,
    summary_jsonl: str | None = None,
    target_answer: str | None = None,  # 新增参数
) -> List[Dict[str, Any]]:
    metas: List[Dict[str, Any]] = []
    for i in range(num):
        meta = generate_one(
            out_dir=out_dir,
            seed=seed + i,
            grid=grid,
            cell_size=cell_size,
            min_steps=min_steps,
            max_steps=max_steps,
            max_stride=max_stride,
            min_manhattan=min_manhattan,
            ensure_end_diff=ensure_end_diff,
            show_path=show_path,
            index=i+1,
            target_answer=target_answer,  # 传递参数
        )
        metas.append(meta)

    if summary_jsonl:
        with open(os.path.join(out_dir, summary_jsonl), "w", encoding="utf-8") as f:
            for m in metas:
                f.write(json.dumps(m, ensure_ascii=False) + "")

    return metas


# ---------------------------- CLI ----------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Compass Grid generator (color‑cued start, strict)")
    p.add_argument("--out_dir", type=str, default="./out_cg", help="Output directory")
    p.add_argument("--num", type=int, default=8, help="Number of samples to generate")
    p.add_argument("--grid", type=int, default=5, help="Grid size N")
    p.add_argument("--cell_size", type=int, default=120, help="Cell size in pixels")
    p.add_argument("--min_steps", type=int, default=1, help="Minimum number of moves")
    p.add_argument("--max_steps", type=int, default=3, help="Maximum number of moves")
    p.add_argument("--max_stride", type=int, default=3, help="Max stride per move (1..k)")
    p.add_argument("--min_manhattan", type=int, default=0, help="Min Manhattan distance between start and end")
    p.add_argument("--seed", type=int, default=4, help="Base seed for reproducibility")
    p.add_argument("--ensure_end_diff", action="store_true", help="Force end cell != start cell")
    p.add_argument("--show_path", action="store_true", help="Overlay the path for debugging")
    p.add_argument("--summary", type=str, default="summary.jsonl", help="Summary JSONL filename")
    p.add_argument("--target_answer", type=str, default="Boob", help="Specify the target answer code")  # 新增参数
    return p.parse_args()


def main():
    args = parse_args()
    generate_batch(
        out_dir=args.out_dir,
        num=args.num,
        seed=args.seed,
        grid=args.grid,
        cell_size=args.cell_size,
        min_steps=args.min_steps,
        max_steps=args.max_steps,
        max_stride=args.max_stride,
        min_manhattan=args.min_manhattan,
        ensure_end_diff=args.ensure_end_diff,
        show_path=args.show_path,
        summary_jsonl=args.summary,
        target_answer=args.target_answer,  # 传递参数
    )
    print(f"Done. Wrote {args.num} samples to {args.out_dir}")


if __name__ == "__main__":
    main()
