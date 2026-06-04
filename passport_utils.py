"""
passport_utils.py
Backend utilities for Passport Photo Studio.
"""

import os
import io
from PIL import Image, ImageDraw, ImageColor

# ── Passport size definitions (width_mm, height_mm) ─────────────────────────
PASSPORT_SIZES = {
    "India  (35×45 mm)": (35, 45),
    "USA    (51×51 mm)": (51, 51),
    "UK     (35×45 mm)": (35, 45),
    "EU/Schengen (35×45 mm)": (35, 45),
    "China  (33×48 mm)": (33, 48),
    "Custom (enter below)": None,   # handled separately
}

A4_W_MM = 210
A4_H_MM = 297
MARGIN_MM = 5   # default outer margin

# Layout presets: (margin_mm, gap_mm, label)
LAYOUT_PRESETS = {
    "Compact – 36 photos (0mm gap)": (0, 0),
    "Standard – with 5mm margins"  : (5, 5),
    "Medium – 2mm gap"             : (2, 2),
}


def mm_to_px(mm, dpi=300):
    return int(round(mm / 25.4 * dpi))


# ── Background removal ────────────────────────────────────────────────────────
def remove_background(input_path: str) -> Image.Image:
    """Return a PIL Image with background removed (RGBA).
    Uses rembg; if not available raises ImportError.
    """
    try:
        from rembg import remove as _remove
    except ImportError:
        raise ImportError("rembg is not installed. Run: pip install rembg")

    with open(input_path, "rb") as f:
        data = f.read()
    out_bytes = _remove(data)
    return Image.open(io.BytesIO(out_bytes)).convert("RGBA")


# ── Color parsing and helper ──────────────────────────────────────────────────
def parse_color(color_str: str) -> tuple:
    """Parse hex, rgb, or color name to (R, G, B) tuple. Fallback to white."""
    try:
        rgb = ImageColor.getrgb(color_str)
        return rgb[:3]
    except Exception:
        return (255, 255, 255)


def draw_checkerboard(size, square_size=16):
    """Generate a checkerboard pattern image of the given size."""
    board = Image.new("RGB", size, (255, 255, 255))
    draw = ImageDraw.Draw(board)
    for y in range(0, size[1], square_size):
        for x in range(0, size[0], square_size):
            if ((x // square_size) + (y // square_size)) % 2 == 1:
                draw.rectangle([x, y, x + square_size - 1, y + square_size - 1], fill=(230, 230, 230))
    return board


def preview_transparency(rgba_image: Image.Image) -> Image.Image:
    """Composite an RGBA image onto a checkerboard background for previewing."""
    checkerboard = draw_checkerboard(rgba_image.size)
    checkerboard.paste(rgba_image, mask=rgba_image.split()[3])
    return checkerboard


# ── Background color fill ─────────────────────────────────────────────────────
def apply_background_color(rgba_image: Image.Image, bg_color: str) -> Image.Image:
    """Composite an RGBA image onto a solid-color background.
    bg_color: hex string like '#FFFFFF' or color name.
    Returns RGB image.
    """
    color = parse_color(bg_color)
    background = Image.new("RGBA", rgba_image.size, color + (255,))
    background.paste(rgba_image, mask=rgba_image.split()[3])  # use alpha channel as mask
    return background.convert("RGB")


# ── Crop / resize to passport size ───────────────────────────────────────────
def crop_to_passport(rgb_image: Image.Image, width_mm: int, height_mm: int,
                     dpi: int = 300) -> Image.Image:
    """Resize (with aspect-preserving center-crop) to exact passport pixel size."""
    target_w = mm_to_px(width_mm, dpi)
    target_h = mm_to_px(height_mm, dpi)

    img = rgb_image.copy()
    src_w, src_h = img.size
    src_ratio = src_w / src_h
    tgt_ratio = target_w / target_h

    if src_ratio > tgt_ratio:
        # Image is wider than target — crop sides
        new_w = int(src_h * tgt_ratio)
        left = (src_w - new_w) // 2
        img = img.crop((left, 0, left + new_w, src_h))
    else:
        # Image is taller — crop top/bottom (bias slightly upward for face)
        new_h = int(src_w / tgt_ratio)
        top = max(0, int((src_h - new_h) * 0.35))  # 35% from top keeps face centered
        img = img.crop((0, top, src_w, top + new_h))

    return img.resize((target_w, target_h), Image.LANCZOS)


# ── A4 sheet layout ──────────────────────────────────────────────────────────
def calculate_grid(photo_w_mm: int, photo_h_mm: int,
                   margin_mm: int = MARGIN_MM, gap_mm: int = MARGIN_MM):
    """Return (cols, rows) that fit on A4 with given margin/gap."""
    usable_w = A4_W_MM - 2 * margin_mm
    usable_h = A4_H_MM - 2 * margin_mm
    if gap_mm == 0:
        cols = max(1, int(usable_w // photo_w_mm))
        rows = max(1, int(usable_h // photo_h_mm))
    else:
        cols = max(1, int((usable_w + gap_mm) // (photo_w_mm + gap_mm)))
        rows = max(1, int((usable_h + gap_mm) // (photo_h_mm + gap_mm)))
    return cols, rows


def create_a4_sheet(passport_photo: Image.Image,
                    photo_w_mm: int,
                    photo_h_mm: int,
                    dpi: int = 300,
                    bg_color: str = "#FFFFFF",
                    margin_mm: int = 0,
                    gap_mm: int = 0) -> Image.Image:
    """
    Tile *passport_photo* on an A4 canvas.
    Returns the A4 PIL Image (RGB, at *dpi* resolution).
    """
    a4_w = mm_to_px(A4_W_MM, dpi)
    a4_h = mm_to_px(A4_H_MM, dpi)
    margin = mm_to_px(margin_mm, dpi)
    gap = mm_to_px(gap_mm, dpi)

    bg = parse_color(bg_color)

    canvas = Image.new("RGB", (a4_w, a4_h), bg)

    photo_w_px = mm_to_px(photo_w_mm, dpi)
    photo_h_px = mm_to_px(photo_h_mm, dpi)

    # Resize photo to exact pixels
    photo = passport_photo.resize((photo_w_px, photo_h_px), Image.LANCZOS)

    cols, rows = calculate_grid(photo_w_mm, photo_h_mm, margin_mm, gap_mm)

    # Draw thin separator lines for cutting guidance
    draw = ImageDraw.Draw(canvas)
    line_color = (180, 180, 180)

    for row in range(rows):
        for col in range(cols):
            x = margin + col * (photo_w_px + gap)
            y = margin + row * (photo_h_px + gap)
            canvas.paste(photo, (x, y))
            # draw thin cut-line border
            draw.rectangle([x, y, x + photo_w_px - 1, y + photo_h_px - 1],
                            outline=line_color, width=max(1, dpi // 150))

    return canvas


# ── Export functions ─────────────────────────────────────────────────────────
def export_as_pdf(a4_image: Image.Image, output_path: str, dpi: int = 300):
    """Save A4 PIL image as a single-page PDF."""
    rgb = a4_image.convert("RGB")
    rgb.save(output_path, "PDF", resolution=dpi, save_all=True)
    print(f"PDF saved: {output_path}")


def export_as_jpeg(a4_image: Image.Image, output_path: str, dpi: int = 300, quality: int = 95):
    """Save A4 PIL image as JPEG."""
    rgb = a4_image.convert("RGB")
    rgb.save(output_path, "JPEG", dpi=(dpi, dpi), quality=quality)
    print(f"JPEG saved: {output_path}")


def export_as_docx(a4_image: Image.Image, output_path: str, dpi: int = 300):
    """Save A4 PIL image embedded in a Word document."""
    try:
        from docx import Document
        from docx.shared import Mm
    except ImportError:
        raise ImportError("python-docx not installed. Run: pip install python-docx")

    # Save image to temp bytes buffer
    buf = io.BytesIO()
    a4_image.convert("RGB").save(buf, format="PNG")
    buf.seek(0)

    doc = Document()

    # Remove default margins for A4 full-bleed layout
    section = doc.sections[0]
    section.page_width = Mm(210)
    section.page_height = Mm(297)
    section.left_margin = Mm(0)
    section.right_margin = Mm(0)
    section.top_margin = Mm(0)
    section.bottom_margin = Mm(0)

    # Clear default empty paragraph
    for para in doc.paragraphs:
        para.clear()

    # Add image — width 210 mm = full A4 width
    paragraph = doc.paragraphs[0] if doc.paragraphs else doc.add_paragraph()
    paragraph.paragraph_format.space_before = Mm(0)
    paragraph.paragraph_format.space_after = Mm(0)
    run = paragraph.add_run()
    run.add_picture(buf, width=Mm(210))

    doc.save(output_path)
    print(f"DOCX saved: {output_path}")
