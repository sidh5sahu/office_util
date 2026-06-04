import os
import csv
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter


# ─── Existing (kept as-is using comtypes for PDF export) ─────────────────────

def excel_to_pdf(input_path, output_path):
    import comtypes.client
    input_path = os.path.abspath(input_path)
    output_path = os.path.abspath(output_path)
    app = comtypes.client.CreateObject("Excel.Application")
    app.Visible = False
    try:
        wb = app.Workbooks.Open(input_path)
        wb.ExportAsFixedFormat(0, output_path)
        wb.Close(False)
    finally:
        app.Quit()


# ─── New: Create / Read / Edit / Export ───────────────────────────────────────

def create_excel(output_path, sheet_name="Sheet1", headers=None, rows=None, bold_headers=True):
    """
    Create a new Excel workbook with a single sheet.

    Args:
        output_path: .xlsx path to save.
        sheet_name: Name of the worksheet.
        headers: Optional list of column header strings (row 1, bold).
        rows: List of lists — each inner list is a row of cell values.
        bold_headers: Whether to bold the header row.
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet_name

    row_offset = 1
    if headers:
        for col_idx, header in enumerate(headers, start=1):
            cell = ws.cell(row=1, column=col_idx, value=header)
            if bold_headers:
                cell.font = Font(bold=True)
                cell.fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
            cell.alignment = Alignment(horizontal="center")
        row_offset = 2

    for r_idx, row_data in enumerate(rows or [], start=row_offset):
        for c_idx, val in enumerate(row_data, start=1):
            ws.cell(row=r_idx, column=c_idx, value=val)

    # Auto-fit column widths (approximate)
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            try:
                max_len = max(max_len, len(str(cell.value or "")))
            except Exception:
                pass
        ws.column_dimensions[col_letter].width = min(max_len + 4, 50)

    wb.save(output_path)
    print(f"Excel workbook created: {output_path}")


def read_excel(input_path):
    """
    Read all sheets from an .xlsx file.

    Returns:
        dict: { sheet_name: { 'headers': [...], 'rows': [[...], ...] } }
    """
    wb = openpyxl.load_workbook(input_path, data_only=True)
    result = {}
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        all_rows = []
        for row in ws.iter_rows(values_only=True):
            all_rows.append(['' if v is None else str(v) for v in row])
        result[sheet_name] = all_rows
    return result


def save_excel(output_path, sheet_name, headers, rows):
    """
    Save a full sheet (headers + rows) to a new workbook.
    Used after UI editing.
    """
    create_excel(output_path, sheet_name=sheet_name, headers=headers if headers else None, rows=rows)


def excel_to_csv(input_path, output_path):
    """Export the first sheet of an Excel workbook to CSV."""
    wb = openpyxl.load_workbook(input_path, data_only=True)
    ws = wb.active
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        for row in ws.iter_rows(values_only=True):
            writer.writerow(['' if v is None else str(v) for v in row])
    print(f"CSV exported: {output_path}")
