import os
import comtypes.client

def excel_to_pdf(input_path, output_path):
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
