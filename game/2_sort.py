#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sort-&-Index Cards — Visual Reasoning Mini‑Game Generator (Strict, Batchable)
============================================================================

Game mechanics
--------------
Display N cards horizontally. Each card shows a big number (the "value") and a
small two‑character code in its bottom‑right corner. The task title instructs:
  - sort the cards by value (ascending or descending), then
  - pick the code on the k‑th card of the sorted order.

Outputs per sample
------------------
- PNG image: cards, title, and codes rendered.
- JSON metadata with full reproducibility and evaluation fields, e.g.:
{
  "type": "sort_index",
  "order": "asc",
  "k": 2,
  "cards": [
    {"value": 42, "code": "QK"},
    {"value": 17, "code": "AB"},
    ...
  ],
  "sorted_indices": [1, 3, 0, 2, 4],    # indices into the original cards list
  "answer_index": 1,                    # original index of the k‑th in sorted order
  "answer": "AB",
  "image_path": ".../sort_0001.png",
  "seed": 123
}

Strictness & clarity features
-----------------------------
- Optional uniqueness of values (default: unique) to avoid tie ambiguity. If
  duplicates are allowed, ties are broken by original left‑to‑right index and
  the rule is stated in the title.
- Large fonts with auto‑fitting to ensure readability after compression.
- Deterministic rendering by seed; all parameters captured in JSON.

Dependencies: Pillow
    pip install pillow

Example CLI usage:
    python sort_index_cards_generator.py --out_dir ./2_sort --num 12 \
        --cards 5 --order asc --k 2 --seed 7 --min_value 0 --max_value 99\
        --target_answer AB

"""
from __future__ import annotations

import os
import json
import random
import argparse
from typing import List, Tuple, Dict, Any

from PIL import Image, ImageDraw, ImageFont

# ---------------------------- Font & text helpers ----------------------------

def try_load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Try to load a commonly available TTF; fallback to default if missing."""
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf",
        "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Helvetica.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size=size)
            except Exception:
                pass
    return ImageFont.load_default()


def text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> Tuple[int, int]:
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    return right - left, bottom - top


def draw_centered_text(draw: ImageDraw.ImageDraw, xy: Tuple[int, int], text: str,
                       font: ImageFont.ImageFont, fill=(0, 0, 0)) -> None:
    w, h = text_size(draw, text, font)
    x, y = xy
    draw.text((x - w // 2, y - h // 2), text, fill=fill, font=font)


def fit_font_to_box(draw: ImageDraw.ImageDraw, text: str, max_w: int, max_h: int,
                    base_size: int, min_size: int = 12) -> ImageFont.ImageFont:
    size = base_size
    while size >= min_size:
        f = try_load_font(size)
        w, h = text_size(draw, text, f)
        if w <= max_w and h <= max_h:
            return f
        size -= 1
    return try_load_font(min_size)

# ---------------------------- Core generation ----------------------------

PALETTE = [
    (245, 248, 255),   # very light blue
    (253, 246, 236),   # very light orange
    (241, 253, 240),   # very light green
    (252, 240, 252),   # very light purple
    (250, 250, 250),   # near white
]

EDGE = (120, 120, 120)
TITLE_BG = (240, 242, 247)
TITLE_TXT = (10, 10, 10)
SUB_TXT = (80, 80, 80)
CODE_TXT = (30, 30, 30)
VALUE_TXT = (20, 20, 20)


def unique_codes(rnd: random.Random, n: int, pair_len: int = 2) -> List[str]:
    alphabet = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
    used = set()
    out: List[str] = []
    while len(out) < n:
        code = "".join(rnd.choice(alphabet) for _ in range(pair_len))
        if code not in used:
            used.add(code)
            out.append(code)
    return out


def sample_values(rnd: random.Random, n: int, min_v: int, max_v: int, allow_dupes: bool) -> List[int]:
    if allow_dupes:
        return [rnd.randint(min_v, max_v) for _ in range(n)]
    # ensure uniqueness — widen range if needed
    span = max_v - min_v + 1
    if span < n:
        raise ValueError(f"Range [{min_v}, {max_v}] too small for {n} unique values.")
    return rnd.sample(range(min_v, max_v + 1), k=n)


# ---------------------------- Rendering ----------------------------

def render_sample(
    out_path_png: str,
    values: List[int],
    codes: List[str],
    order: str,  # "asc" | "desc"
    k: int,
    sorted_indices: List[int],
    image_w: int = 1400,
    image_h: int = 600,
    card_w: int = 220,
    card_h: int = 300,
    margin: int = 40,
) -> None:
    n = len(values)
    # Compute horizontal layout: equal spacing between cards
    total_cards_w = n * card_w
    if image_w < total_cards_w + 2 * margin:
        image_w = total_cards_w + 2 * margin

    header_h = 120
    H = max(image_h, header_h + card_h + 2 * margin)
    W = image_w

    img = Image.new("RGB", (W, H), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Fonts
    title_font = try_load_font(36)
    sub_font = try_load_font(22)

    # Title
    draw.rectangle((0, 0, W, header_h), fill=TITLE_BG)
    ord_text = "ascending" if order == "asc" else "descending"
    title = f"Sort the cards in {ord_text} order and read the code on the {k}-th card."
    draw.text((margin, 20), title, fill=TITLE_TXT, font=title_font)

    if order == "asc":
        tie_rule = "If values tie, keep original left-to-right order."
    else:
        tie_rule = "If values tie, keep original left-to-right order."
    draw.text((margin, 70), tie_rule, fill=SUB_TXT, font=sub_font)

    # Compute X positions
    usable_w = W - 2 * margin
    gap = 0
    if n > 1:
        gap = (usable_w - n * card_w) // (n - 1)
        gap = max(gap, 16)
        # If too wide, we keep minimum 16px gap and center block
        block_w = n * card_w + (n - 1) * gap
        x0 = (W - block_w) // 2
    else:
        x0 = (W - card_w) // 2

    # Render each card
    value_font_base = 140
    code_font_base = 36

    for i in range(n):
        x = x0 + i * (card_w + gap)
        y = header_h + (H - header_h - card_h) // 2
        # Background
        fill = PALETTE[i % len(PALETTE)]
        draw.rounded_rectangle((x, y, x + card_w, y + card_h), radius=16, fill=fill, outline=EDGE, width=2)

        # Big value text (centered)
        vtxt = str(values[i])
        v_font = fit_font_to_box(draw, vtxt, max_w=card_w - 40, max_h=card_h - 120, base_size=value_font_base)
        cx = x + card_w // 2
        cy = y + card_h // 2 - 10
        draw_centered_text(draw, (cx, cy), vtxt, v_font, fill=VALUE_TXT)

        # Small code at bottom-right with padding
        code = codes[i]
        c_font = fit_font_to_box(draw, code, max_w=card_w - 40, max_h=40, base_size=code_font_base, min_size=14)
        cw, ch = text_size(draw, code, c_font)
        draw.text((x + card_w - 16 - cw, y + card_h - 14 - ch), code, fill=CODE_TXT, font=c_font)

    # Optionally, draw visual indicator for k-th position after sorting (debug)
    # (You can enable this during dataset authoring if needed.)

    img.save(out_path_png)


# ---------------------------- Orchestration ----------------------------

def generate_one(
    out_dir: str,
    seed: int,
    n_cards: int = 5,
    order: str = "asc",   # "asc" | "desc" | "rand"
    k: int = 2,
    min_value: int = 0,
    max_value: int = 99,
    allow_dupes: bool = False,
    index: int | None = None,
    target_answer: str | None = None,  # 新增参数：指定答案
) -> Dict[str, Any]:
    os.makedirs(out_dir, exist_ok=True)
    rnd = random.Random(seed)

    if order == "rand":
        order_real = rnd.choice(["asc", "desc"])
    else:
        order_real = order
    assert order_real in ("asc", "desc")

    # Sample values & codes
    values = sample_values(rnd, n_cards, min_value, max_value, allow_dupes)
    codes = unique_codes(rnd, n_cards)

    # Prepare sorting (stable sort). Python's sort is stable — ties keep original order.
    orig_indices = list(range(n_cards))
    if order_real == "asc":
        sorted_tuple = sorted(orig_indices, key=lambda i: (values[i], i))
    else:
        sorted_tuple = sorted(orig_indices, key=lambda i: (-values[i], i))

    if not (1 <= k <= n_cards):
        raise ValueError(f"k must be within 1..{n_cards}, got {k}")

    answer_index = sorted_tuple[k - 1]
    
    # 如果指定了目标答案，则替换对应位置的代码
    if target_answer is not None:
        codes[answer_index] = target_answer
        answer = target_answer
    else:
        answer = codes[answer_index]

    # Render
    base = f"sort_{index:04d}" if index is not None else f"sort_seed{seed}"
    img_path = os.path.join(out_dir, base + ".png")
    json_path = os.path.join(out_dir, base + ".json")

    render_sample(
        out_path_png=img_path,
        values=values,
        codes=codes,
        order=order_real,
        k=k,
        sorted_indices=sorted_tuple,
    )

    meta: Dict[str, Any] = {
        "type": "sort_index",
        "order": order_real,
        "k": k,
        "cards": [{"value": int(values[i]), "code": codes[i]} for i in range(n_cards)],
        "sorted_indices": list(map(int, sorted_tuple)),
        "answer_index": int(answer_index),
        "answer": answer,
        "image_path": img_path,
        "seed": seed,
        "params": {
            "n_cards": n_cards,
            "min_value": min_value,
            "max_value": max_value,
            "allow_dupes": allow_dupes,
        },
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    return meta


def generate_batch(
    out_dir: str,
    num: int,
    seed: int = 0,
    n_cards: int = 5,
    order: str = "asc",
    k: int = 2,
    min_value: int = 0,
    max_value: int = 99,
    allow_dupes: bool = False,
    summary_jsonl: str | None = None,
    target_answer: str | None = None,  # 新增参数
) -> List[Dict[str, Any]]:
    metas: List[Dict[str, Any]] = []
    for i in range(num):
        meta = generate_one(
            out_dir=out_dir,
            seed=seed + i,
            n_cards=n_cards,
            order=order,
            k=k,
            min_value=min_value,
            max_value=max_value,
            allow_dupes=allow_dupes,
            index=i + 1,
            target_answer=target_answer,  # 传递参数
        )
        metas.append(meta)

    if summary_jsonl:
        with open(os.path.join(out_dir, summary_jsonl), "w", encoding="utf-8") as f:
            for m in metas:
                f.write(json.dumps(m, ensure_ascii=False) + "\n")

    return metas


# ---------------------------- CLI ----------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Sort-&-Index Cards generator (strict)")
    p.add_argument("--out_dir", type=str, default="./out_sort", help="Output directory")
    p.add_argument("--num", type=int, default=8, help="Number of samples to generate")
    p.add_argument("--cards", type=int, default=5, help="Number of cards per image")
    p.add_argument("--order", type=str, default="asc", choices=["asc", "desc", "rand"], help="Sorting order")
    p.add_argument("--k", type=int, default=2, help="Pick the code of the k-th card after sorting")
    p.add_argument("--min_value", type=int, default=0, help="Minimum value for card numbers")
    p.add_argument("--max_value", type=int, default=99, help="Maximum value for card numbers")
    p.add_argument("--allow_dupes", action="store_true", help="Allow duplicate values (ties keep original order)")
    p.add_argument("--seed", type=int, default=0, help="Base seed for reproducibility")
    p.add_argument("--summary", type=str, default="summary.jsonl", help="Summary JSONL filename")
    p.add_argument("--target_answer", type=str, default="Bo", help="Specify the target answer code")  # 新增参数
    return p.parse_args()


def main():
    args = parse_args()
    generate_batch(
        out_dir=args.out_dir,
        num=args.num,
        seed=args.seed,
        n_cards=args.cards,
        order=args.order,
        k=args.k,
        min_value=args.min_value,
        max_value=args.max_value,
        allow_dupes=args.allow_dupes,
        summary_jsonl=args.summary,
        target_answer=args.target_answer,  # 传递参数
    )
    print(f"Done. Wrote {args.num} samples to {args.out_dir}")


if __name__ == "__main__":
    main()
