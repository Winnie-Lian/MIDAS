#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jigsaw Puzzle — Visual Reasoning Mini‑Game Generator (Rectangular Pieces with Text Overlay)
==========================================================================================

Example CLI usage:
    # Use default hardcoded image (8.jpg)
    python 6_jigsaw_puzzle.py --out_dir ./6_jigsaw_output --num 3 \
        --text_overlay b --grid_rows 5 --grid_cols 5 --seed 42
    
    # Use custom image
    python 6_jigsaw_puzzle.py --out_dir ./6_jigsaw_output --num 3 \
        --text_overlay b --grid_rows 5 --grid_cols 5 --seed 42 \
        --base_image /path/to/custom.jpg
"""
from __future__ import annotations

import os
import json
import random
import argparse
from typing import List, Tuple, Dict, Any

from PIL import Image, ImageOps, ImageFilter, ImageDraw, ImageFont

# ---------------------------- Configuration ----------------------------

# Default configuration
DEFAULT_GRID_ROWS = 5
DEFAULT_GRID_COLS = 5
DEFAULT_TEXT_OVERLAY = "b"
DEFAULT_TEXT_COLOR = (0, 220, 90, 255)
DEFAULT_STROKE_COLOR = (0, 0, 0, 255)
DEFAULT_STROKE_WIDTH = 3
DEFAULT_BORDER_WIDTH = 0
DEFAULT_MAX_ROTATION = 4
DEFAULT_CELL_GAP = 28
DEFAULT_GRID_GAP = 15

# Hardcoded image path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_BASE_IMAGE = os.path.join(SCRIPT_DIR, "discracted", "8.jpg")

# Font candidates
PREFERRED_FONTS = [
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/Library/Fonts/Arial Unicode.ttf",
    "/Library/Fonts/Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "C:/Windows/Fonts/arial.ttf",
]

# ---------------------------- Font & text helpers ----------------------------

def try_load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Try to load a commonly available TTF; fallback to default if missing."""
    for path in PREFERRED_FONTS:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size=size)
            except Exception:
                pass
    return ImageFont.load_default()


def is_cjk(ch: str) -> bool:
    """Check if character is Chinese, Japanese, or Korean."""
    code = ord(ch)
    return (0x4E00 <= code <= 0x9FFF) or (0x3400 <= code <= 0x4DBF) or (0x20000 <= code <= 0x2A6DF) or \
           (0x2A700 <= code <= 0x2B73F) or (0x2B740 <= code <= 0x2B81F) or (0x2B820 <= code <= 0x2CEAF) or \
           (0xF900 <= code <= 0xFAFF) or (0x2F800 <= code <= 0x2FA1F)


def tokenize_for_wrap(text: str) -> List[str]:
    """Tokenize text for proper line wrapping."""
    tokens, buf, mode = [], "", None
    for ch in text:
        if ch.isspace():
            if buf:
                tokens.append(buf)
                buf = ""
                mode = None
            tokens.append(" ")
            continue
        now = "cjk" if is_cjk(ch) else "latin"
        if mode is None:
            buf, mode = ch, now
        elif mode == now:
            if now == "cjk":
                tokens.append(ch)
            else:
                buf += ch
        else:
            if buf:
                tokens.append(buf)
            buf, mode = ch, now
        if now == "cjk":
            buf = ""
            mode = None
    if buf:
        tokens.append(buf)
    return tokens


def measure_lines(draw: ImageDraw.ImageDraw, lines: List[str], font: ImageFont.ImageFont, 
                  spacing: int, stroke_w: int) -> Tuple[int, int]:
    """Measure total width and height of text lines."""
    max_w, total_h = 0, 0
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font, stroke_width=stroke_w)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        max_w = max(max_w, w)
        total_h += h
        if i < len(lines) - 1:
            total_h += spacing
    return max_w, total_h


def wrap_text(text: str, font: ImageFont.ImageFont, max_w: int, draw: ImageDraw.ImageDraw, 
              stroke_w: int) -> List[str]:
    """Wrap text to fit within maximum width."""
    tokens = tokenize_for_wrap(text)
    lines, cur = [], ""
    for tok in tokens:
        probe = (cur + tok) if cur else tok
        w, _ = measure_lines(draw, [probe], font, 0, stroke_w)
        if tok == " ":
            if cur:
                cur += tok
            continue
        if w <= max_w:
            cur = probe
        else:
            if cur:
                lines.append(cur.rstrip())
                cur = ""
            if tok != " ":
                buf = ""
                for ch in tok:
                    w2, _ = measure_lines(draw, [buf + ch], font, 0, stroke_w)
                    if w2 <= max_w:
                        buf += ch
                    else:
                        if buf:
                            lines.append(buf)
                            buf = ch
                        else:
                            lines.append(ch)
                            buf = ""
                if buf:
                    cur = buf
    if cur:
        lines.append(cur.rstrip())
    return lines


def find_max_font(img_w: int, img_h: int, text: str, box_wh: Tuple[int, int], 
                  margin_px: int, stroke_w: int, line_spacing_ratio: float) -> Tuple[int, List[str], ImageFont.ImageFont]:
    """Find the largest font size that fits the text in the given box."""
    draw = ImageDraw.Draw(Image.new("RGBA", (img_w, img_h)))
    lo, hi = 8, max(20, min(img_w, img_h))
    chosen_lines, chosen_font = [], try_load_font(lo)
    while lo <= hi:
        mid = (lo + hi) // 2
        font = try_load_font(mid)
        spacing = max(1, int(mid * line_spacing_ratio))
        lines = wrap_text(text, font, box_wh[0] - 2 * margin_px, draw, stroke_w)
        w, h = measure_lines(draw, lines, font, spacing, stroke_w)
        if w + 2 * margin_px <= box_wh[0] and h + 2 * margin_px <= box_wh[1]:
            chosen_lines, chosen_font = lines, font
            lo = mid + 1
        else:
            hi = mid - 1
    return hi, chosen_lines, chosen_font


def draw_text_overlay(base: Image.Image, text: str, text_color: Tuple[int, int, int, int] = None,
                      stroke_color: Tuple[int, int, int, int] = None, stroke_width: int = 3,
                      drop_shadow: bool = True) -> Image.Image:
    """Draw text overlay on the base image."""
    if text_color is None:
        text_color = DEFAULT_TEXT_COLOR
    if stroke_color is None:
        stroke_color = DEFAULT_STROKE_COLOR
    
    img = base.convert("RGBA")
    W, H = img.size
    
    # Text box configuration
    text_box_w_frac = 0.68
    text_box_h_frac = 0.68
    text_margin_frac = 0.04
    text_box_pos = ("center", "middle")
    text_align = "center"
    line_spacing = 0.15
    
    box_w = int(W * text_box_w_frac)
    box_h = int(H * text_box_h_frac)
    short = min(W, H)
    margin_px = max(2, int(short * text_margin_frac))
    
    # Calculate text box position
    xa, ya = text_box_pos
    bx = margin_px if xa == "left" else ((W - box_w) // 2 if xa == "center" else W - box_w - margin_px)
    by = margin_px if ya == "top" else ((H - box_h) // 2 if ya == "middle" else H - box_h - margin_px)
    
    # Find optimal font size
    best_size, lines, font = find_max_font(W, H, text, (box_w, box_h), margin_px, stroke_width, line_spacing)
    spacing = max(1, int(best_size * line_spacing))
    
    # Create text overlay
    tmp = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(tmp)
    w_all, h_all = measure_lines(d, lines, font, spacing, stroke_width)
    
    # Calculate text position
    tx = bx + margin_px if text_align == "left" else (bx + (box_w - w_all) // 2 if text_align == "center" else bx + box_w - w_all - margin_px)
    ty = by + (box_h - h_all) // 2
    
    # Draw shadow if enabled
    if drop_shadow:
        shadow_offset = (2, 2)
        shadow_blur = 4
        shadow_alpha = 140
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d2 = ImageDraw.Draw(sh)
        cy = ty
        for line in lines:
            d2.text((tx + shadow_offset[0], cy + shadow_offset[1]), line,
                    font=font, fill=(0, 0, 0, shadow_alpha),
                    stroke_width=stroke_width, stroke_fill=(0, 0, 0, shadow_alpha))
            bbox = d2.textbbox((tx, cy), line, font=font, stroke_width=stroke_width)
            cy += (bbox[3] - bbox[1]) + spacing
        sh = sh.filter(ImageFilter.GaussianBlur(shadow_blur))
        img = Image.alpha_composite(img, sh)
    
    # Draw main text
    cy = ty
    for line in lines:
        d.text((tx, cy), line, font=font, fill=text_color,
               stroke_width=stroke_width, stroke_fill=stroke_color, align=text_align)
        bbox = d.textbbox((tx, cy), line, font=font, stroke_width=stroke_width)
        cy += (bbox[3] - bbox[1]) + spacing
    
    return Image.alpha_composite(img, tmp)

# ---------------------------- Puzzle generation ----------------------------

def split_grid_rects(W: int, H: int, rows: int, cols: int) -> List[Tuple[int, int, int, int]]:
    """Split image into grid rectangles."""
    xs = [round(i * W / cols) for i in range(cols + 1)]
    ys = [round(i * H / rows) for i in range(rows + 1)]
    rects = []
    for r in range(rows):
        for c in range(cols):
            rects.append((xs[c], ys[r], xs[c + 1], ys[r + 1]))
    return rects


def generate_rect_pieces(img: Image.Image, rows: int, cols: int, 
                        add_border: bool = False, border_width: int = 0,
                        allow_rotation: bool = True, max_rotation: float = 4.0,
                        add_shadow: bool = False) -> List[Dict[str, Any]]:
    """Generate rectangular puzzle pieces from image."""
    W, H = img.size
    rects = split_grid_rects(W, H, rows, cols)
    
    pieces = []
    for rect in rects:
        x0, y0, x1, y1 = rect
        crop_img = img.crop((x0, y0, x1, y1)).convert("RGBA")
        
        # Add border if enabled
        if add_border and border_width > 0:
            w, h = crop_img.size
            overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            d = ImageDraw.Draw(overlay)
            inset = max(1, border_width // 2)
            d.rectangle([inset, inset, w - 1 - inset, h - 1 - inset],
                        outline=(255, 255, 255, 255), width=border_width)
            crop_img = Image.alpha_composite(crop_img, overlay)
        
        piece = crop_img
        
        # Add rotation if enabled
        if allow_rotation and abs(max_rotation) > 0:
            deg = random.uniform(-max_rotation, max_rotation)
            piece = piece.rotate(deg, expand=True, resample=Image.BICUBIC)
        
        # Add shadow if enabled
        shadow = None
        shadow_offset = (0, 0)
        if add_shadow:
            shadow_alpha = 120
            shadow_blur = 12
            shadow_offset = (6, 6)
            alpha = Image.new("L", piece.size, 255)
            shadow_color = Image.new("RGBA", piece.size, (0, 0, 0, shadow_alpha))
            shadow = Image.new("RGBA", piece.size, (0, 0, 0, 0))
            shadow.paste(shadow_color, (0, 0), mask=alpha)
            shadow = shadow.filter(ImageFilter.GaussianBlur(shadow_blur))
        
        pieces.append({
            "img": piece,
            "shadow": shadow,
            "shadow_offset": shadow_offset
        })
    
    return pieces

# ---------------------------- Layout rendering ----------------------------

def render_scattered_layout(pieces: List[Dict[str, Any]], rows: int, cols: int, 
                           out_path: str, cell_gap: int = 28, canvas_padding: int = 40,
                           background_color: Tuple[int, int, int, int] = (255, 255, 255, 255)) -> None:
    """Render pieces in scattered layout."""
    max_w = max(p["img"].size[0] for p in pieces) + abs(pieces[0]["shadow_offset"][0])
    max_h = max(p["img"].size[1] for p in pieces) + abs(pieces[0]["shadow_offset"][1])
    cell_inner_jitter = 16
    cell_w = max_w + cell_inner_jitter * 2
    cell_h = max_h + cell_inner_jitter * 2
    
    canvas_w = (cell_w * cols) + (cell_gap * (cols - 1)) + canvas_padding * 2
    canvas_h = (cell_h * rows) + (cell_gap * (rows - 1)) + canvas_padding * 2
    canvas = Image.new("RGBA", (canvas_w, canvas_h), background_color)
    
    idx = 0
    for r in range(rows):
        for c in range(cols):
            if idx >= len(pieces):
                break
            p = pieces[idx]
            idx += 1
            cell_x = canvas_padding + c * (cell_w + cell_gap)
            cell_y = canvas_padding + r * (cell_h + cell_gap)
            free_x = max(0, cell_w - p["img"].size[0])
            free_y = max(0, cell_h - p["img"].size[1])
            base_x = cell_x + free_x // 2
            base_y = cell_y + free_y // 2
            jx = random.randint(-cell_inner_jitter, cell_inner_jitter)
            jy = random.randint(-cell_inner_jitter, cell_inner_jitter)
            x = min(max(base_x + jx, cell_x), cell_x + cell_w - p["img"].size[0])
            y = min(max(base_y + jy, cell_y), cell_y + cell_h - p["img"].size[1])
            
            if p["shadow"] is not None:
                sx, sy = p["shadow_offset"]
                canvas.alpha_composite(p["shadow"], (x + sx, y + sy))
            canvas.alpha_composite(p["img"], (x, y))
    
    out = canvas.convert("RGB")
    out.save(out_path, quality=95)
    print(f"[OK] Scattered layout saved => {out_path}")


def render_grid_layout(pieces: List[Dict[str, Any]], rows: int, cols: int, 
                      out_path: str, grid_gap: int = 15, canvas_padding: int = 36,
                      background_color: Tuple[int, int, int, int] = (255, 255, 255, 255)) -> None:
    """Render pieces in neat grid layout."""
    max_w = max(p["img"].size[0] for p in pieces) + abs(pieces[0]["shadow_offset"][0])
    max_h = max(p["img"].size[1] for p in pieces) + abs(pieces[0]["shadow_offset"][1])
    canvas_w = cols * max_w + (cols - 1) * grid_gap + 2 * canvas_padding
    canvas_h = rows * max_h + (rows - 1) * grid_gap + 2 * canvas_padding
    canvas = Image.new("RGBA", (canvas_w, canvas_h), background_color)
    
    idx = 0
    for r in range(rows):
        for c in range(cols):
            if idx >= len(pieces):
                break
            p = pieces[idx]
            idx += 1
            x = canvas_padding + c * (max_w + grid_gap)
            y = canvas_padding + r * (max_h + grid_gap)
            if p["shadow"] is not None:
                sx, sy = p["shadow_offset"]
                canvas.alpha_composite(p["shadow"], (x + sx, y + sy))
            canvas.alpha_composite(p["img"], (x, y))
    
    out = canvas.convert("RGB")
    out.save(out_path, quality=95)
    print(f"[OK] Grid layout saved => {out_path}")

# ---------------------------- Core generation ----------------------------

def generate_one(
    out_dir: str,
    seed: int,
    base_image: str,
    text_overlay: str,
    grid_rows: int = 5,
    grid_cols: int = 5,
    text_color: Tuple[int, int, int, int] = None,
    stroke_color: Tuple[int, int, int, int] = None,
    stroke_width: int = 3,
    add_border: bool = False,
    border_width: int = 0,
    allow_rotation: bool = True,
    max_rotation: float = 4.0,
    add_shadow: bool = False,
    cell_gap: int = 28,
    grid_gap: int = 15,
    index: int = None,
) -> Dict[str, Any]:
    """Generate one jigsaw puzzle sample."""
    os.makedirs(out_dir, exist_ok=True)
    random.seed(seed)
    
    # Load and process base image
    base = Image.open(base_image).convert("RGB")
    img_with_text = draw_text_overlay(base, text_overlay, text_color, stroke_color, stroke_width)
    
    # Generate puzzle pieces
    pieces = generate_rect_pieces(
        img_with_text, grid_rows, grid_cols, add_border, border_width,
        allow_rotation, max_rotation, add_shadow
    )
    
    # Generate filenames
    base_name = f"jigsaw_{index:04d}" if index is not None else f"jigsaw_seed{seed}"
    scatter_path = os.path.join(out_dir, base_name + "_scatter.png")
    grid_path = os.path.join(out_dir, base_name + "_grid.png")
    json_path = os.path.join(out_dir, base_name + ".json")
    
    # Render layouts
    render_scattered_layout(pieces, grid_rows, grid_cols, scatter_path, cell_gap)
    render_grid_layout(pieces, grid_rows, grid_cols, grid_path, grid_gap)
    
    # Metadata
    meta: Dict[str, Any] = {
        "type": "jigsaw_puzzle",
        "grid_rows": grid_rows,
        "grid_cols": grid_cols,
        "text_overlay": text_overlay,
        "base_image_path": base_image,
        "scattered_image_path": scatter_path,
        "grid_image_path": grid_path,
        "seed": seed,
        "params": {
            "text_color": list(text_color) if text_color else list(DEFAULT_TEXT_COLOR),
            "stroke_color": list(stroke_color) if stroke_color else list(DEFAULT_STROKE_COLOR),
            "stroke_width": stroke_width,
            "add_border": add_border,
            "border_width": border_width,
            "allow_rotation": allow_rotation,
            "max_rotation": max_rotation,
            "add_shadow": add_shadow,
            "cell_gap": cell_gap,
            "grid_gap": grid_gap,
        }
    }
    
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    
    return meta


def generate_batch(
    out_dir: str,
    num: int,
    seed: int = 0,
    base_image: str = None,
    text_overlay: str = "b",
    grid_rows: int = 5,
    grid_cols: int = 5,
    text_color: Tuple[int, int, int, int] = None,
    stroke_color: Tuple[int, int, int, int] = None,
    stroke_width: int = 3,
    add_border: bool = False,
    border_width: int = 0,
    allow_rotation: bool = True,
    max_rotation: float = 4.0,
    add_shadow: bool = False,
    cell_gap: int = 28,
    grid_gap: int = 15,
    summary_jsonl: str = None,
) -> List[Dict[str, Any]]:
    """Generate multiple jigsaw puzzle samples."""
    if not base_image:
        base_image = DEFAULT_BASE_IMAGE
    
    metas: List[Dict[str, Any]] = []
    for i in range(num):
        meta = generate_one(
            out_dir=out_dir,
            seed=seed + i,
            base_image=base_image,
            text_overlay=text_overlay,
            grid_rows=grid_rows,
            grid_cols=grid_cols,
            text_color=text_color,
            stroke_color=stroke_color,
            stroke_width=stroke_width,
            add_border=add_border,
            border_width=border_width,
            allow_rotation=allow_rotation,
            max_rotation=max_rotation,
            add_shadow=add_shadow,
            cell_gap=cell_gap,
            grid_gap=grid_gap,
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
    p = argparse.ArgumentParser(description="Jigsaw Puzzle generator (rectangular pieces with text overlay)")
    p.add_argument("--out_dir", type=str, default="./out_jigsaw", help="Output directory")
    p.add_argument("--num", type=int, default=8, help="Number of samples to generate")
    p.add_argument("--seed", type=int, default=0, help="Base seed for reproducibility")
    
    # Image configuration
    p.add_argument("--base_image", type=str, default=DEFAULT_BASE_IMAGE, help="Base image path (default: uses hardcoded 8.jpg)")
    p.add_argument("--text_overlay", type=str, default="b", help="Text to overlay on the image")
    
    # Grid configuration
    p.add_argument("--grid_rows", type=int, default=5, help="Number of grid rows")
    p.add_argument("--grid_cols", type=int, default=5, help="Number of grid columns")
    
    # Text styling
    p.add_argument("--text_color", type=int, nargs=4, default=[0, 220, 90, 255], help="Text color (RGBA)")
    p.add_argument("--stroke_color", type=int, nargs=4, default=[0, 0, 0, 255], help="Stroke color (RGBA)")
    p.add_argument("--stroke_width", type=int, default=3, help="Stroke width")
    
    # Piece styling
    p.add_argument("--add_border", action="store_true", help="Add white border to pieces")
    p.add_argument("--border_width", type=int, default=0, help="Border width")
    p.add_argument("--allow_rotation", action="store_true", default=True, help="Allow piece rotation")
    p.add_argument("--no_rotation", action="store_true", help="Disable piece rotation")
    p.add_argument("--max_rotation", type=float, default=4.0, help="Maximum rotation angle")
    p.add_argument("--add_shadow", action="store_true", help="Add shadow to pieces")
    
    # Layout configuration
    p.add_argument("--cell_gap", type=int, default=28, help="Gap between cells in scattered layout")
    p.add_argument("--grid_gap", type=int, default=5, help="Gap between pieces in grid layout")
    
    # Output configuration
    p.add_argument("--summary", type=str, default="summary.jsonl", help="Summary JSONL filename")
    
    return p.parse_args()


def main():
    args = parse_args()
    
    # Handle rotation setting
    allow_rotation = args.allow_rotation and not args.no_rotation
    
    generate_batch(
        out_dir=args.out_dir,
        num=args.num,
        seed=args.seed,
        base_image=args.base_image,
        text_overlay=args.text_overlay,
        grid_rows=args.grid_rows,
        grid_cols=args.grid_cols,
        text_color=tuple(args.text_color),
        stroke_color=tuple(args.stroke_color),
        stroke_width=args.stroke_width,
        add_border=args.add_border,
        border_width=args.border_width,
        allow_rotation=allow_rotation,
        max_rotation=args.max_rotation,
        add_shadow=args.add_shadow,
        cell_gap=args.cell_gap,
        grid_gap=args.grid_gap,
        summary_jsonl=args.summary,
    )
    print(f"Done. Wrote {args.num} samples to {args.out_dir}")


if __name__ == "__main__":
    main()
