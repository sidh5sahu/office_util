import os
import comtypes.client
from pdf_utils import pdf_to_images # Dependency on PDF utils for rendering

def ppt_to_pdf(input_path, output_path):
    input_path = os.path.abspath(input_path)
    output_path = os.path.abspath(output_path)
    powerpoint = comtypes.client.CreateObject("Powerpoint.Application")
    try:
        deck = powerpoint.Presentations.Open(input_path)
        deck.SaveAs(output_path, 32) # 32=ppSaveAsPDF
        deck.Close()
    finally:
        powerpoint.Quit()

def ppt_to_images(input_path, output_dir):
    input_path = os.path.abspath(input_path)
    output_dir = os.path.abspath(output_dir)
    app = comtypes.client.CreateObject("Powerpoint.Application")
    try:
        prs = app.Presentations.Open(input_path, WithWindow=False)
        base = os.path.splitext(os.path.basename(input_path))[0]
        for i, slide in enumerate(prs.Slides):
            out_name = os.path.join(output_dir, f"{base}_slide_{i+1}.jpg")
            slide.Export(out_name, "JPG")
        prs.Close()
    finally:
        app.Quit()
