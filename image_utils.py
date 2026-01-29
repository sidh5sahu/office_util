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
