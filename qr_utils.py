import qrcode
from PIL import Image

# pyzbar is optional - requires zbar DLLs on Windows
decode = None
PYZBAR_ERROR = None
try:
    from pyzbar.pyzbar import decode
except ImportError as e:
    PYZBAR_ERROR = "pyzbar is not installed. Install with: pip install pyzbar"
except Exception as e:
    PYZBAR_ERROR = f"pyzbar failed to load (missing zbar DLLs on Windows). Error: {str(e)}"

def generate_qr(data, output_path, box_size=10, border=4):
    """Generate a QR code from text/URL and save as image."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(output_path)

def read_qr(image_path):
    """Read/decode QR code from an image. Returns list of decoded data."""
    if not decode:
        raise ImportError(PYZBAR_ERROR or "pyzbar is not available")
    
    img = Image.open(image_path)
    decoded_objects = decode(img)
    
    results = []
    for obj in decoded_objects:
        results.append({
            'type': obj.type,
            'data': obj.data.decode('utf-8')
        })
    
    return results
