import os
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx2pdf import convert as docx_convert
from pdf_utils import pdf_to_images


# ─── Existing conversion functions ────────────────────────────────────────────

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


# ─── New: Create / Edit / Read ─────────────────────────────────────────────────

def create_word_doc(output_path, title="", paragraphs=None, font_name="Calibri", font_size=12):
    """
    Create a new Word document from scratch.

    Args:
        output_path: .docx file path to write.
        title: Optional heading string (will be styled as Heading 1).
        paragraphs: List of dicts, each:
            {
              'text': str,
              'bold': bool,
              'italic': bool,
              'underline': bool,
              'align': 'left' | 'center' | 'right' | 'justify',
              'size': int (pt),
              'color': '#RRGGBB' hex string (optional)
            }
        font_name: Default font.
        font_size: Default font size in points.
    """
    doc = Document()

    # Global default style
    style = doc.styles['Normal']
    style.font.name = font_name
    style.font.size = Pt(font_size)

    if title:
        heading = doc.add_heading(title, level=1)
        heading.runs[0].font.name = font_name

    for para_data in (paragraphs or []):
        text = para_data.get('text', '')
        if text == '---':
            # Separator
            doc.add_paragraph('─' * 60)
            continue

        style_name = para_data.get('style', 'Normal')  # 'Heading 1', 'Heading 2', 'Normal'
        try:
            p = doc.add_paragraph(style=style_name)
        except KeyError:
            p = doc.add_paragraph()

        run = p.add_run(text)
        run.bold = para_data.get('bold', False)
        run.italic = para_data.get('italic', False)
        run.underline = para_data.get('underline', False)

        sz = para_data.get('size', font_size)
        run.font.size = Pt(sz)
        run.font.name = font_name

        hex_color = para_data.get('color', '')
        if hex_color:
            try:
                hex_color = hex_color.lstrip('#')
                r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
                run.font.color.rgb = RGBColor(r, g, b)
            except Exception:
                pass

        align = para_data.get('align', 'left')
        align_map = {
            'left': WD_ALIGN_PARAGRAPH.LEFT,
            'center': WD_ALIGN_PARAGRAPH.CENTER,
            'right': WD_ALIGN_PARAGRAPH.RIGHT,
            'justify': WD_ALIGN_PARAGRAPH.JUSTIFY,
        }
        p.alignment = align_map.get(align, WD_ALIGN_PARAGRAPH.LEFT)

    doc.save(output_path)
    print(f"Word document created: {output_path}")


def read_word_doc(input_path):
    """
    Read a .docx and return its content as a list of paragraph dicts.

    Returns:
        List of dicts:
            {
              'text': str,
              'style': str,   # paragraph style name
              'bold': bool,
              'italic': bool,
              'underline': bool,
              'align': str
            }
    """
    doc = Document(input_path)
    result = []
    align_map = {
        WD_ALIGN_PARAGRAPH.LEFT: 'left',
        WD_ALIGN_PARAGRAPH.CENTER: 'center',
        WD_ALIGN_PARAGRAPH.RIGHT: 'right',
        WD_ALIGN_PARAGRAPH.JUSTIFY: 'justify',
        None: 'left',
    }

    for para in doc.paragraphs:
        if not para.text.strip():
            result.append({'text': '', 'style': 'Normal', 'bold': False, 'italic': False, 'underline': False, 'align': 'left'})
            continue

        bold = any(run.bold for run in para.runs if run.bold)
        italic = any(run.italic for run in para.runs if run.italic)
        underline = any(run.underline for run in para.runs if run.underline)

        result.append({
            'text': para.text,
            'style': para.style.name,
            'bold': bold,
            'italic': italic,
            'underline': underline,
            'align': align_map.get(para.alignment, 'left'),
        })
    return result


def save_word_doc(input_path, output_path, paragraphs):
    """
    Overwrite an existing document with updated paragraphs list.  The original
    file is read to preserve its style, then content is replaced.
    """
    doc = Document()
    for para_data in paragraphs:
        text = para_data.get('text', '')
        style_name = para_data.get('style', 'Normal')
        try:
            p = doc.add_paragraph(style=style_name)
        except KeyError:
            p = doc.add_paragraph()
        run = p.add_run(text)
        run.bold = para_data.get('bold', False)
        run.italic = para_data.get('italic', False)
        run.underline = para_data.get('underline', False)
    doc.save(output_path)
    print(f"Word document saved: {output_path}")


def insert_image_word(input_path, output_path, img_path, width_cm=10):
    """Insert an image into an existing Word document at the end."""
    doc = Document(input_path)
    doc.add_picture(img_path, width=Inches(width_cm / 2.54))
    doc.save(output_path)
    print(f"Image inserted into Word document: {output_path}")
