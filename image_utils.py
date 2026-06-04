import os
from PIL import Image, ImageOps, ImageFilter, ImageDraw
import cv2
import numpy as np
try:
    from rembg import remove as remove_bg
except ImportError:
    remove_bg = None
import pytesseract
from psd_tools import PSDImage
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM
import moviepy.editor as mp # For gif to mp4 in convert_image

# Supported HEIC/AVIF
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError: pass
try:
    import pillow_avif
except ImportError: pass

def get_thumbnail(path, max_size=(300, 300)):
    try:
        base, ext = os.path.splitext(path)
        ext = ext.lower()
        img = None
        
        if ext in ['.png', '.jpg', '.jpeg', '.webp', '.bmp', '.gif', '.tiff', '.ico']:
            img = Image.open(path)
        elif ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
            cap = cv2.VideoCapture(path)
            ret, frame = cap.read()
            cap.release()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame)
        
        if img:
            img.thumbnail(max_size)
            return img
    except Exception:
        pass
    return None

def remove_background(input_path, output_path):
    if not remove_bg:
        raise ImportError("rembg not installed properly")
    with open(input_path, 'rb') as i:
        input_data = i.read()
        output_data = remove_bg(input_data)
    with open(output_path, 'wb') as o:
        o.write(output_data)

def upscale_image(input_path, output_path, scale=2):
    img = Image.open(input_path)
    w, h = img.size
    img = img.resize((w*scale, h*scale), Image.BICUBIC)
    img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=150))
    img.save(output_path)

def unblur_image(input_path, output_path):
    img = cv2.imread(input_path)
    # Sharpening kernel
    kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
    sharpened = cv2.filter2D(img, -1, kernel)
    cv2.imwrite(output_path, sharpened)

def grayscale_image(input_path, output_path):
    img = Image.open(input_path).convert('L')
    img.save(output_path)

def pixelate_image(input_path, output_path, pixel_size=10):
    img = Image.open(input_path)
    w, h = img.size
    img = img.resize((w//pixel_size, h//pixel_size), Image.NEAREST)
    img = img.resize((w, h), Image.NEAREST)
    img.save(output_path)

def add_border(input_path, output_path, color="black", width=10):
    img = Image.open(input_path)
    img_with_border = ImageOps.expand(img, border=int(width), fill=color)
    img_with_border.save(output_path)

def make_round_image(input_path, output_path):
    img = Image.open(input_path).convert("RGBA")
    mask = Image.new("L", img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + img.size, fill=255)
    result = ImageOps.fit(img, mask.size, centering=(0.5, 0.5))
    result.putalpha(mask)
    result.save(output_path)

def extract_text_ocr(input_path, output_path):
    try:
        text = pytesseract.image_to_string(Image.open(input_path))
        with open(output_path, "w", encoding='utf-8') as f:
            f.write(text)
    except pytesseract.TesseractNotFoundError:
        raise Exception("Tesseract is not installed or not in PATH.")

def convert_image_format(input_path, output_path, format_name=None):
    base, ext = os.path.splitext(input_path)
    ext = ext.lower()
    
    if ext == ".psd":
        psd = PSDImage.open(input_path)
        psd.composite().save(output_path)
        return
        
    if ext == ".svg":
        drawing = svg2rlg(input_path)
        renderPM.drawToFile(drawing, output_path, fmt=os.path.splitext(output_path)[1][1:].upper())
        return

    if ext == ".gif" and output_path.lower().endswith(".mp4"):
        clip = mp.VideoFileClip(input_path)
        clip.write_videofile(output_path)
        return

    img = Image.open(input_path)
    if img.mode in ("RGBA", "P") and output_path.lower().endswith((".jpg", ".jpeg")):
        img = img.convert("RGB")
    
    img.save(output_path)

def resize_image(input_path, output_path, width, height):
    img = Image.open(input_path)
    img = img.resize((int(width), int(height)), Image.LANCZOS)
    img.save(output_path)

def crop_image_rel(input_path, output_path, left, top, right, bottom):
    img = Image.open(input_path)
    w, h = img.size
    box = (left, top, w - right, h - bottom)
    img = img.crop(box)
    img.save(output_path)

def flip_image(input_path, output_path, direction="horizontal"):
    img = Image.open(input_path)
    if "hor" in direction.lower():
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
    else:
        img = img.transpose(Image.FLIP_TOP_BOTTOM)
    img.save(output_path)

def rotate_image(input_path, output_path, angle):
    img = Image.open(input_path)
    img = img.rotate(int(angle), expand=True)
    img.save(output_path)

def change_image_background(input_path, output_path, color=(255, 255, 255)):
    img = Image.open(input_path)
    if img.mode in ('RGBA', 'LA'):
        background = Image.new(img.mode[:-1], img.size, color)
        background.paste(img, img.split()[-1])
        img = background
    img.save(output_path)

def compress_image(input_path, output_path, quality=50):
    img = Image.open(input_path)
    # Save with quality
    if img.mode == 'RGBA':
        img = img.convert('RGB')
    img.save(output_path, "JPEG", optimize=True, quality=quality)

def add_text_to_image(input_path, output_path, text, x=10, y=10, font_size=24, color="white"):
    """Add text/caption to an image."""
    from PIL import ImageFont
    
    img = Image.open(input_path).convert("RGBA")
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    # Add slight shadow for visibility
    shadow_offset = 2
    draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill="black")
    draw.text((x, y), text, font=font, fill=color)
    
    img.save(output_path)

def adjust_brightness_contrast(input_path, output_path, brightness=1.0, contrast=1.0):
    """Adjust brightness and contrast of an image. 1.0 = no change."""
    from PIL import ImageEnhance
    
    img = Image.open(input_path)
    
    # Brightness adjustment
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(brightness)
    
    # Contrast adjustment
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(contrast)
    
    img.save(output_path)

def blur_faces(input_path, output_path, blur_strength=30):
    """Detect and blur faces in an image for privacy."""
    img = cv2.imread(input_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Load face cascade
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    
    for (x, y, w, h) in faces:
        face_region = img[y:y+h, x:x+w]
        blurred_face = cv2.GaussianBlur(face_region, (blur_strength, blur_strength), 0)
        img[y:y+h, x:x+w] = blurred_face
    
    cv2.imwrite(output_path, img)


def batch_process(input_paths, output_dir, operation="resize", **kwargs):
    """Apply an operation to many images at once.
    Operations: resize, grayscale, compress, convert, rotate, flip
    """
    os.makedirs(output_dir, exist_ok=True)
    processed = 0
    for path in input_paths:
        try:
            base = os.path.basename(path)
            name, ext = os.path.splitext(base)
            out_path = os.path.join(output_dir, base)

            if operation == "resize":
                w = kwargs.get("width", 800)
                h = kwargs.get("height", 600)
                resize_image(path, out_path, w, h)
            elif operation == "grayscale":
                grayscale_image(path, out_path)
            elif operation == "compress":
                quality = kwargs.get("quality", 50)
                compress_image(path, out_path, quality)
            elif operation == "convert":
                fmt = kwargs.get("format", "png")
                out_path = os.path.join(output_dir, f"{name}.{fmt}")
                convert_image_format(path, out_path)
            elif operation == "rotate":
                angle = kwargs.get("angle", 90)
                rotate_image(path, out_path, angle)
            elif operation == "flip":
                direction = kwargs.get("direction", "horizontal")
                flip_image(path, out_path, direction)
            else:
                continue

            processed += 1
            print(f"  Processed: {base}")
        except Exception as e:
            print(f"  Failed: {base} — {e}")
    return processed


def extract_color_palette(input_path, num_colors=6):
    """Extract dominant colors from an image using k-means clustering.
    Returns list of hex color strings.
    """
    img = cv2.imread(input_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    # Resize for speed
    img = cv2.resize(img, (150, 150))
    pixels = img.reshape(-1, 3).astype(np.float32)

    # k-means clustering
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)
    _, labels, centers = cv2.kmeans(pixels, num_colors, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
    centers = centers.astype(int)

    # Sort by frequency
    counts = np.bincount(labels.flatten())
    sorted_indices = np.argsort(-counts)

    palette = []
    for idx in sorted_indices:
        r, g, b = centers[idx]
        hex_color = f"#{r:02x}{g:02x}{b:02x}"
        palette.append(hex_color)

    return palette


def create_collage(image_paths, output_path, cols=3, thumb_size=300, padding=10):
    """Create a grid collage from multiple images."""
    if not image_paths:
        raise ValueError("No images provided")

    images = []
    for p in image_paths:
        try:
            img = Image.open(p).convert("RGB")
            img.thumbnail((thumb_size, thumb_size), Image.LANCZOS)
            images.append(img)
        except Exception as e:
            print(f"  Skipping {os.path.basename(p)}: {e}")

    if not images:
        raise ValueError("No valid images to create collage")

    rows = (len(images) + cols - 1) // cols
    canvas_w = cols * (thumb_size + padding) + padding
    canvas_h = rows * (thumb_size + padding) + padding

    canvas = Image.new("RGB", (canvas_w, canvas_h), (30, 30, 30))

    for i, img in enumerate(images):
        row = i // cols
        col = i % cols
        x = padding + col * (thumb_size + padding) + (thumb_size - img.width) // 2
        y = padding + row * (thumb_size + padding) + (thumb_size - img.height) // 2
        canvas.paste(img, (x, y))

    canvas.save(output_path)
    print(f"Collage created: {len(images)} images in {rows}x{cols} grid")
