
import sys
import shutil
try:
    import image_utils
    has_image_utils = True
except ImportError:
    has_image_utils = False

print("Checking dependencies...")

# Check rembg (now in image_utils)
if has_image_utils and image_utils.remove_bg:
    print("rembg: OK")
else:
    print("rembg: MISSING (ImportError during image_utils import)")

# Check Tesseract
try:
    import pytesseract
    # This just checks if the library is there, not the exe
    print("pytesseract lib: OK")
    # minimal check if exe is reachable (requires an image, skipping for now)
except ImportError:
    print("pytesseract: MISSING")

# Check Comtypes (Windows only)
try:
    import comtypes.client
    print("comtypes: OK")
except ImportError:
    print("comtypes: MISSING")

# Check MoviePy
try:
    import moviepy.editor
    print("moviepy: OK")
except ImportError:
    print("moviepy: MISSING")

print("Check complete.")
