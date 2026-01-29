import os
from docx2pdf import convert as docx_convert
from pdf_utils import pdf_to_images

def word_to_pdf(input_path, output_path):
    input_path = os.path.abspath(input_path)
    output_path = os.path.abspath(output_path)
    docx_convert(input_path, output_path)

def word_to_images(input_path, output_dir):
    temp_pdf = os.path.join(output_dir, "temp_render.pdf")
    try:
        word_to_pdf(input_path, temp_pdf)
        pdf_to_images(temp_pdf, output_dir)
    except Exception as e:
        raise e
    finally:
        if os.path.exists(temp_pdf):
             try: os.remove(temp_pdf)
             except: pass
