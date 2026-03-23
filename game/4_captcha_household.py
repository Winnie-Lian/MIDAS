#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Household Captcha — Visual Reasoning Mini‑Game Generator (Image Selection with Text Overlay)
===========================================================================================

Example CLI usage:
    # Use default hardcoded images (target.jpg and 1-8.jpg)
    python 4_captcha_household.py --out_dir ./4_captcha_output --num 5 \
        --target_sentence dog --grid_rows 3 --grid_cols 3 --seed 42
    
    # Use custom images
    python 4_captcha_household.py --out_dir ./4_captcha_output --num 5 \
        --target_sentence dog --grid_rows 3 --grid_cols 3 --seed 42 \
        --target_paths /path/to/fish1.jpg /path/to/fish2.jpg \
        --distractor_paths /path/to/cat1.jpg /path/to/dog1.jpg /path/to/car1.jpg
"""
from __future__ import annotations

import os
import json
import random
import argparse
import re
from typing import List, Set, Tuple, Dict, Any

from PIL import Image, ImageOps, ImageDraw, ImageFont

# ---------------------------- Configuration ----------------------------

# Default configuration
DEFAULT_HEADER_TEXT = "UGxlYXNlIHNlbGVjdCBhbGwgcGljdHVyZXMgY29udGFpbmluZyBkb2c="
DEFAULT_GRID_ROWS = 3
DEFAULT_GRID_COLS = 3
DEFAULT_TILE_SIZE = 256
DEFAULT_GRID_GUTTER = 6
DEFAULT_HEADER_HEIGHT = 168
DEFAULT_BUTTON_TEXT = "Verify"
DEFAULT_BUTTON_FONT_PATH = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"

# Hardcoded image paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_TARGET_PATHS = [
    os.path.join(SCRIPT_DIR, "discracted", "target.jpg")
]
DEFAULT_DISTRACTOR_PATHS = [
    os.path.join(SCRIPT_DIR, "discracted", "1.jpg"),
    os.path.join(SCRIPT_DIR, "discracted", "2.jpg"),
    os.path.join(SCRIPT_DIR, "discracted", "3.jpg"),
    os.path.join(SCRIPT_DIR, "discracted", "4.jpg"),
    os.path.join(SCRIPT_DIR, "discracted", "5.jpg"),
    os.path.join(SCRIPT_DIR, "discracted", "6.jpg"),
    os.path.join(SCRIPT_DIR, "discracted", "7.jpg"),
    os.path.join(SCRIPT_DIR, "discracted", "8.jpg"),
]

# Text overlay settings
DEFAULT_PUT_TEXT_ON_DISTRACTORS = True
DEFAULT_DISTRACTOR_TEXT_MODE = "alnum"
DEFAULT_DISTRACTOR_TEXT_PROB = 0.5
DEFAULT_DISTRACTOR_LEN_RANGE = (2, 6)
DEFAULT_DISTRACTOR_ROTATE_MAX_DEG = 30

# Image extensions
IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".JPG", ".JPEG", ".PNG", ".BMP", ".WEBP"}

# ---------------------------- Font & text helpers ----------------------------

def try_load_font(size: int, preferred: str = None) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Try to load a commonly available TTF; fallback to default if missing."""
    # User specified font first
    if preferred and os.path.isfile(preferred):
        try:
            return ImageFont.truetype(preferred, size=size)
        except Exception:
            pass
    
    # Common font candidates
    candidates = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",  # Linux common
        "/System/Library/Fonts/PingFang.ttc",                     # macOS
        "/System/Library/Fonts/STHeiti Light.ttc",                # macOS old
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",           # WenQuanYi
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",        # Western fallback
        "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf",
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

# ---------------------------- Text generation helpers ----------------------------

_ALNUM = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz0123456789"
_B64ISH = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="


def rand_text(mode: str, length: int) -> str:
    """Generate random text for distractor overlays."""
    if mode == "words":
        # Simple fake words
        syll = ["la", "ke", "vo", "mi", "su", "ta", "re", "ko", "zi", "no", "fi", "du", "qa", "ra", "ti", "sa", "pa", "ze", "to", "up", "tjf"]
        n = max(1, length // 3)
        return " ".join("".join(random.choice(syll) for _ in range(random.randint(1, 3))) for _ in range(n))
    chars = _B64ISH if mode == "base64ish" else _ALNUM
    return "".join(random.choice(chars) for _ in range(length))


def split_sentence(sentence: str, n: int, mode: str = "auto") -> List[str]:
    """Split sentence into n chunks for target image overlays."""
    s = (sentence or "").strip()
    if not s:
        return [""] * n
    
    def is_chinese(x):
        return any('\u4e00' <= ch <= '\u9fff' for ch in x)
    
    if mode == "auto":
        mode = "chars" if (is_chinese(s) and " " not in s) else "words"
    
    toks = list(s) if mode == "chars" else [t for t in re.split(r"\s+", s) if t]
    if len(toks) <= n:
        out = ["".join(toks) if mode == "chars" else " ".join(toks)]
        out += [""] * (n - 1)
        return out
    
    avg = len(toks) / n
    chunks = []
    last = 0.0
    for _ in range(n):
        st = int(round(last))
        last += avg
        ed = int(round(last))
        seg = toks[st:ed]
        chunks.append("".join(seg) if mode == "chars" else " ".join(seg))
    return chunks

# ---------------------------- Image processing helpers ----------------------------

def _is_img(path: str) -> bool:
    return os.path.splitext(path)[1] in IMG_EXTS


def _random_child(path: str) -> List[str]:
    try:
        return os.listdir(path)
    except Exception:
        return []


def pick_random_file_by_descend(root: str) -> str:
    """Randomly descend directory tree to pick an image file."""
    top = _random_child(root)
    if not top:
        return ""
    for _ in range(256):
        cur = os.path.join(root, random.choice(top))
        if os.path.isfile(cur) and _is_img(cur):
            return cur
        if os.path.isdir(cur):
            path = cur
            for __ in range(32):
                items = _random_child(path)
                if not items:
                    break
                imgs = [os.path.join(path, x) for x in items if _is_img(x)]
                if imgs:
                    return random.choice(imgs)
                subs = [os.path.join(path, x) for x in items if os.path.isdir(os.path.join(path, x))]
                if not subs:
                    break
                path = random.choice(subs)
    return ""


def choose_distractors_from_list(image_paths: List[str], exclude: Set[str], k: int) -> List[str]:
    """Choose k distractor images from a provided list."""
    available = [fp for fp in image_paths if fp not in exclude and os.path.isfile(fp) and _is_img(fp)]
    if len(available) < k:
        raise RuntimeError(f"Only found {len(available)} available distractor images (need {k}). Check image paths list.")
    return random.sample(available, k)


def load_and_fit(fp: str, tile_size: int) -> Image.Image:
    """Load and resize image to fit tile size."""
    im = Image.open(fp).convert("RGB")
    im = ImageOps.fit(im, (tile_size, tile_size), method=Image.LANCZOS)
    return im

# ---------------------------- Text overlay rendering ----------------------------

def draw_outlined_text(im: Image.Image, text: str, font: ImageFont.ImageFont, rotate_deg: float = 0.0) -> Image.Image:
    """Draw outlined text on image with optional rotation."""
    if not text:
        return im
    
    # Get image dimensions
    img_w, img_h = im.size
    
    # Random font size (18-32)
    font_size = random.randint(18, 32)
    dynamic_font = try_load_font(font_size, preferred=font.path if hasattr(font, 'path') else None)
    
    # Calculate text bounding box
    d = ImageDraw.Draw(Image.new("RGBA", (1, 1), (0, 0, 0, 0)))
    bbox = d.textbbox((0, 0), text, font=dynamic_font, stroke_width=2)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    # Random position, ensuring text is completely within image
    margin = 8  # margin
    max_x = img_w - text_w - margin
    max_y = img_h - text_h - margin
    
    if max_x > margin and max_y > margin:
        # If text can fit, choose random position
        dx = random.randint(margin, max_x)
        dy = random.randint(margin, max_y)
    else:
        # If text is too large, center it
        dx = (img_w - text_w) // 2
        dy = (img_h - text_h) // 2
    
    # Draw on separate layer, supporting slight rotation
    txt = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(txt)
    d.text((dx, dy), text, font=dynamic_font, fill=(255, 255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0, 255))
    
    if abs(rotate_deg) > 0.1:
        txt = txt.rotate(rotate_deg, resample=Image.BICUBIC, center=(dx, dy), expand=False)
    
    im.paste(txt, (0, 0), txt)
    return im


def wrap_text_to_box(draw: ImageDraw.ImageDraw, text: str,
                     max_w: int, max_h: int,
                     start_size: int = 80, min_size: int = 18,
                     line_gap: int = 6, ellipsis: str = "…") -> Tuple[List[str], ImageFont.ImageFont]:
    """Character-wise line wrapping; try fonts from large to small; add ellipsis if needed."""
    def break_lines(font: ImageFont.ImageFont) -> List[str]:
        lines, cur = [], ""
        for ch in text:
            trial = cur + ch
            if draw.textlength(trial, font=font) <= max_w:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                    cur = ch
                else:
                    lines.append(ch)
                    cur = ""
        if cur:
            lines.append(cur)
        return lines

    for size in range(start_size, min_size - 1, -2):
        font = try_load_font(size)
        lines = break_lines(font)
        line_h = max(font.getbbox("Hg")[3] - font.getbbox("Hg")[1], 1)
        total_h = line_h * len(lines) + line_gap * (len(lines) - 1 if lines else 0)
        if total_h <= max_h and lines:
            return lines, font

    # Shrink to minimum still can't fit: truncate last line and add ellipsis
    font = try_load_font(min_size)
    lines = break_lines(font)
    line_h = max(font.getbbox("Hg")[3] - font.getbbox("Hg")[1], 1)
    max_lines = max((max_h + line_gap) // (line_h + line_gap), 1)
    lines = lines[:max_lines] if lines else [""]

    last = lines[-1]
    while draw.textlength(last + ellipsis, font=font) > max_w and len(last) > 0:
        last = last[:-1]
    lines[-1] = (last + ellipsis) if last else ellipsis
    return lines, font

# ---------------------------- Main rendering ----------------------------

def render_captcha(
    tiles: List[Tuple[Image.Image, bool, str]],
    out_path: str,
    header_text: str,
    grid_rows: int,
    grid_cols: int,
    tile_size: int,
    grid_gutter: int,
    header_height: int,
    button_text: str,
    button_font_path: str = None,
    put_text_on_distractors: bool = True,
    distractor_text_mode: str = "alnum",
    distractor_text_prob: float = 0.5,
    distractor_len_range: Tuple[int, int] = (2, 6),
    distractor_rotate_max_deg: int = 30,
) -> None:
    """Render the complete captcha image."""
    total = grid_rows * grid_cols
    assert len(tiles) == total

    grid_w = grid_cols * tile_size + (grid_cols - 1) * grid_gutter
    grid_h = grid_rows * tile_size + (grid_rows - 1) * grid_gutter
    canvas_w = max(560, grid_w + 40)
    footer_h = 120
    canvas_h = header_height + grid_h + footer_h + 40

    canvas = Image.new("RGB", (canvas_w, canvas_h), (245, 245, 245))
    D = ImageDraw.Draw(canvas)

    # Blue header bar (full width) + character-wise line wrapping & scaling
    D.rectangle((0, 0, canvas_w, header_height), fill=(33, 150, 243))
    left_x = 24
    box_w = canvas_w - left_x - 24
    box_h = header_height - 18 - 10
    lines, fnt = wrap_text_to_box(D, header_text, box_w, box_h, start_size=80, min_size=18, line_gap=6)
    y = 18
    line_h = max(fnt.getbbox("Hg")[3] - fnt.getbbox("Hg")[1], 1)
    for ln in lines:
        D.text((left_x, y), ln, font=fnt, fill=(255, 255, 255))
        y += line_h + 6

    # Grid + target/distractor text overlays
    ox = (canvas_w - grid_w) // 2
    oy = header_height + 24
    k = 0
    font_small = try_load_font(22, preferred=button_font_path)  # More stable with Chinese
    for r in range(grid_rows):
        for c in range(grid_cols):
            img, is_target, chunk = tiles[k]
            img = img.copy()
            if is_target:
                # Target: write specified chunk, position and size random
                draw_outlined_text(img, chunk, font_small, rotate_deg=random.uniform(-3, 3))
            else:
                # Distractor: write random string by probability (style/length/position/rotation random)
                if put_text_on_distractors and random.random() < distractor_text_prob:
                    L = random.randint(*distractor_len_range)
                    txt = rand_text(distractor_text_mode, L)
                    deg = random.uniform(-distractor_rotate_max_deg, distractor_rotate_max_deg)
                    draw_outlined_text(img, txt, font_small, rotate_deg=deg)
            x = ox + c * (tile_size + grid_gutter)
            y = oy + r * (tile_size + grid_gutter)
            canvas.paste(img, (x, y))
            k += 1

    # "Verify" button
    btn_w, btn_h = 180, 64
    bx = canvas_w - btn_w - 40
    by = oy + grid_h + 20 + (footer_h - btn_h) // 2
    D.rounded_rectangle((bx, by, bx + btn_w, by + btn_h), radius=12, fill=(33, 150, 243))

    contains_cjk = any('\u4e00' <= ch <= '\u9fff' for ch in button_text)
    btn_font = try_load_font(28, preferred=button_font_path if contains_cjk else None)
    btn_label = button_text
    if contains_cjk and D.textlength(btn_label, font=btn_font) < 10:
        btn_label = "Verify"
        btn_font = try_load_font(28)

    tw = D.textlength(btn_label, font=btn_font)
    D.text((int(bx + (btn_w - tw) / 2), by + 16), btn_label, font=btn_font, fill=(255, 255, 255))

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    canvas.save(out_path)
    print(f"[OK] saved => {out_path}")

# ---------------------------- Core generation ----------------------------

def generate_one(
    out_dir: str,
    seed: int,
    target_paths: List[str],
    distractor_paths: List[str],
    target_sentence: str = "dog",
    grid_rows: int = 3,
    grid_cols: int = 3,
    tile_size: int = 256,
    grid_gutter: int = 6,
    header_height: int = 168,
    header_text: str = DEFAULT_HEADER_TEXT,
    button_text: str = DEFAULT_BUTTON_TEXT,
    button_font_path: str = None,
    put_text_on_distractors: bool = True,
    distractor_text_mode: str = "alnum",
    distractor_text_prob: float = 0.5,
    distractor_len_range: Tuple[int, int] = (2, 6),
    distractor_rotate_max_deg: int = 30,
    overlay_split_mode: str = "auto",
    index: int = None,
) -> Dict[str, Any]:
    """Generate one captcha sample."""
    os.makedirs(out_dir, exist_ok=True)
    random.seed(seed)

    total_tiles = grid_rows * grid_cols
    n_targets = len(target_paths)
    n_distracts = total_tiles - n_targets

    if n_targets <= 0:
        raise ValueError("At least one target path must be provided")
    if n_distracts < 0:
        raise ValueError("Too many target paths for grid size")

    # Target sampling & text chunks (prioritize sentence splitting)
    if target_sentence:
        chunks = split_sentence(target_sentence, n_targets, overlay_split_mode)
    else:
        chunks = [""] * n_targets

    # Distractor sampling from provided list
    exclude = set(target_paths)
    distracts = choose_distractors_from_list(distractor_paths, exclude=exclude, k=n_distracts)

    # Read + combine (img, is_target, text_chunk)
    tiles: List[Tuple[Image.Image, bool, str]] = []
    for fp, chunk in zip(target_paths, chunks):
        tiles.append((load_and_fit(fp, tile_size), True, chunk))
    for fp in distracts:
        tiles.append((load_and_fit(fp, tile_size), False, ""))

    random.shuffle(tiles)

    # Generate filenames
    base = f"captcha_{index:04d}" if index is not None else f"captcha_seed{seed}"
    img_path = os.path.join(out_dir, base + ".png")
    json_path = os.path.join(out_dir, base + ".json")

    # Render
    render_captcha(
        tiles, img_path, header_text, grid_rows, grid_cols, tile_size, grid_gutter,
        header_height, button_text, button_font_path, put_text_on_distractors,
        distractor_text_mode, distractor_text_prob, distractor_len_range, distractor_rotate_max_deg
    )

    # Metadata
    meta: Dict[str, Any] = {
        "type": "household_captcha",
        "grid_rows": grid_rows,
        "grid_cols": grid_cols,
        "tile_size": tile_size,
        "target_sentence": target_sentence,
        "target_paths": target_paths,
        "distractor_paths": distracts,
        "text_chunks": chunks,
        "answer": target_sentence,
        "image_path": img_path,
        "seed": seed,
        "params": {
            "header_text": header_text,
            "button_text": button_text,
            "put_text_on_distractors": put_text_on_distractors,
            "distractor_text_mode": distractor_text_mode,
            "distractor_text_prob": distractor_text_prob,
            "distractor_len_range": list(distractor_len_range),
            "distractor_rotate_max_deg": distractor_rotate_max_deg,
            "overlay_split_mode": overlay_split_mode,
        }
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    return meta


def generate_batch(
    out_dir: str,
    num: int,
    seed: int = 0,
    target_paths: List[str] = None,
    distractor_paths: List[str] = None,
    target_sentence: str = "dog",
    grid_rows: int = 3,
    grid_cols: int = 3,
    tile_size: int = 256,
    grid_gutter: int = 6,
    header_height: int = 168,
    header_text: str = DEFAULT_HEADER_TEXT,
    button_text: str = DEFAULT_BUTTON_TEXT,
    button_font_path: str = None,
    put_text_on_distractors: bool = True,
    distractor_text_mode: str = "alnum",
    distractor_text_prob: float = 0.5,
    distractor_len_range: Tuple[int, int] = (2, 6),
    distractor_rotate_max_deg: int = 30,
    overlay_split_mode: str = "auto",
    summary_jsonl: str = None,
) -> List[Dict[str, Any]]:
    """Generate multiple captcha samples."""
    # Use default paths if not provided
    if not target_paths:
        target_paths = DEFAULT_TARGET_PATHS
    if not distractor_paths:
        distractor_paths = DEFAULT_DISTRACTOR_PATHS

    metas: List[Dict[str, Any]] = []
    for i in range(num):
        meta = generate_one(
            out_dir=out_dir,
            seed=seed + i,
            target_paths=target_paths,
            distractor_paths=distractor_paths,
            target_sentence=target_sentence,
            grid_rows=grid_rows,
            grid_cols=grid_cols,
            tile_size=tile_size,
            grid_gutter=grid_gutter,
            header_height=header_height,
            header_text=header_text,
            button_text=button_text,
            button_font_path=button_font_path,
            put_text_on_distractors=put_text_on_distractors,
            distractor_text_mode=distractor_text_mode,
            distractor_text_prob=distractor_text_prob,
            distractor_len_range=distractor_len_range,
            distractor_rotate_max_deg=distractor_rotate_max_deg,
            overlay_split_mode=overlay_split_mode,
            index=i + 1,
        )
        metas.append(meta)

    if summary_jsonl:
        with open(os.path.join(out_dir, summary_jsonl), "w", encoding="utf-8") as f:
            for m in metas:
                f.write(json.dumps(m, ensure_ascii=False) + "\n")

    return metas

# ---------------------------- CLI ----------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Household Captcha generator (image selection with text overlay)")
    p.add_argument("--out_dir", type=str, default="./out_captcha", help="Output directory")
    p.add_argument("--num", type=int, default=8, help="Number of samples to generate")
    p.add_argument("--seed", type=int, default=0, help="Base seed for reproducibility")
    
    # Grid configuration
    p.add_argument("--grid_rows", type=int, default=3, help="Number of grid rows")
    p.add_argument("--grid_cols", type=int, default=3, help="Number of grid columns")
    p.add_argument("--tile_size", type=int, default=256, help="Size of each image tile in pixels")
    p.add_argument("--grid_gutter", type=int, default=6, help="Gap between grid tiles")
    
    # Target configuration
    p.add_argument("--target_paths", type=str, nargs="+", default=DEFAULT_TARGET_PATHS, help="Paths to target images (default: uses hardcoded target.jpg)")
    p.add_argument("--distractor_paths", type=str, nargs="+", default=DEFAULT_DISTRACTOR_PATHS, help="Paths to distractor images (default: uses hardcoded 1-8.jpg)")
    p.add_argument("--target_sentence", type=str, default="dog", help="Target sentence to overlay on target images")
    p.add_argument("--overlay_split_mode", type=str, default="auto", choices=["auto", "words", "chars"], help="How to split target sentence")
    
    # Visual configuration
    p.add_argument("--header_text", type=str, default=DEFAULT_HEADER_TEXT, help="Header text to display")
    p.add_argument("--header_height", type=int, default=168, help="Height of header area")
    p.add_argument("--button_text", type=str, default=DEFAULT_BUTTON_TEXT, help="Text for verify button")
    p.add_argument("--button_font_path", type=str, default=None, help="Path to font for button text")
    
    # Distractor text configuration
    p.add_argument("--put_text_on_distractors", action="store_true", default=True, help="Add random text to distractor images")
    p.add_argument("--no_text_on_distractors", action="store_true", help="Disable text on distractor images")
    p.add_argument("--distractor_text_mode", type=str, default="alnum", choices=["base64ish", "alnum", "words"], help="Style of distractor text")
    p.add_argument("--distractor_text_prob", type=float, default=0.5, help="Probability of adding text to distractor images")
    p.add_argument("--distractor_len_range", type=int, nargs=2, default=[2, 6], help="Length range for distractor text")
    p.add_argument("--distractor_rotate_max_deg", type=int, default=30, help="Maximum rotation angle for distractor text")
    
    # Output configuration
    p.add_argument("--summary", type=str, default="summary.jsonl", help="Summary JSONL filename")
    
    return p.parse_args()


def main():
    args = parse_args()
    
    # Handle distractor text setting
    put_text_on_distractors = args.put_text_on_distractors and not args.no_text_on_distractors
    
    generate_batch(
        out_dir=args.out_dir,
        num=args.num,
        seed=args.seed,
        target_paths=args.target_paths,
        distractor_paths=args.distractor_paths,
        target_sentence=args.target_sentence,
        grid_rows=args.grid_rows,
        grid_cols=args.grid_cols,
        tile_size=args.tile_size,
        grid_gutter=args.grid_gutter,
        header_height=args.header_height,
        header_text=args.header_text,
        button_text=args.button_text,
        button_font_path=args.button_font_path,
        put_text_on_distractors=put_text_on_distractors,
        distractor_text_mode=args.distractor_text_mode,
        distractor_text_prob=args.distractor_text_prob,
        distractor_len_range=tuple(args.distractor_len_range),
        distractor_rotate_max_deg=args.distractor_rotate_max_deg,
        overlay_split_mode=args.overlay_split_mode,
        summary_jsonl=args.summary,
    )
    print(f"Done. Wrote {args.num} samples to {args.out_dir}")


if __name__ == "__main__":
    main()
