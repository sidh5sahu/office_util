import os
import csv
import json
import xml.etree.ElementTree as ET
import pandas as pd

def split_csv(input_path, output_dir, rows_per_chunk):
    """Splits a CSV file into multiple smaller CSV files."""
    chunk_size = max(1, int(rows_per_chunk))
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        try:
            headers = next(reader)
        except StopIteration:
            return  # Empty file
            
        chunk_idx = 1
        current_rows = []
        
        for row in reader:
            current_rows.append(row)
            if len(current_rows) >= chunk_size:
                out_path = os.path.join(output_dir, f"{base_name}_part{chunk_idx}.csv")
                with open(out_path, 'w', newline='', encoding='utf-8') as out_f:
                    writer = csv.writer(out_f)
                    writer.writerow(headers)
                    writer.writerows(current_rows)
                current_rows = []
                chunk_idx += 1
                
        # Write remaining
        if current_rows:
            out_path = os.path.join(output_dir, f"{base_name}_part{chunk_idx}.csv")
            with open(out_path, 'w', newline='', encoding='utf-8') as out_f:
                writer = csv.writer(out_f)
                writer.writerow(headers)
                writer.writerows(current_rows)

def split_excel(input_path, output_dir, rows_per_chunk):
    """Splits the first sheet of an Excel file into multiple Excel files."""
    chunk_size = max(1, int(rows_per_chunk))
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    
    df = pd.read_excel(input_path)
    total_rows = len(df)
    
    for i, start_row in enumerate(range(0, total_rows, chunk_size)):
        chunk = df.iloc[start_row:start_row + chunk_size]
        out_path = os.path.join(output_dir, f"{base_name}_part{i+1}.xlsx")
        chunk.to_excel(out_path, index=False)

def xml_to_excel(input_path, output_path):
    """Converts a flat XML file to Excel."""
    tree = ET.parse(input_path)
    root = tree.getroot()
    
    data = []
    for child in root:
        row = {}
        for sub in child:
            row[sub.tag] = sub.text
        if row:
            data.append(row)
            
    if not data:
        raise ValueError("No tabular data found in XML.")
        
    df = pd.DataFrame(data)
    df.to_excel(output_path, index=False)

def excel_to_xml(input_path, output_path):
    """Converts an Excel file into a basic XML structure."""
    df = pd.read_excel(input_path)
    
    root = ET.Element("Data")
    for _, row in df.iterrows():
        record = ET.SubElement(root, "Record")
        for col_name, val in row.items():
            field = ET.SubElement(record, str(col_name).replace(" ", "_"))
            field.text = str(val) if pd.notna(val) else ""
            
    tree = ET.ElementTree(root)
    # Basic indentation
    ET.indent(tree, space="    ", level=0)
    tree.write(output_path, encoding='utf-8', xml_declaration=True)

def csv_to_excel(input_path, output_path):
    """Converts a CSV file to Excel."""
    df = pd.read_csv(input_path)
    df.to_excel(output_path, index=False)

def xml_to_csv(input_path, output_path):
    """Converts a flat XML file to CSV."""
    tree = ET.parse(input_path)
    root = tree.getroot()
    
    data = []
    for child in root:
        row = {}
        for sub in child:
            row[sub.tag] = sub.text
        if row:
            data.append(row)
            
    if not data:
        raise ValueError("No tabular data found in XML.")
        
    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)

def xml_to_json(input_path, output_path):
    """Converts a basic XML structure into a JSON array of objects."""
    tree = ET.parse(input_path)
    root = tree.getroot()
    
    data = []
    for child in root:
        row = {}
        for sub in child:
            row[sub.tag] = sub.text
        if row:
            data.append(row)
            
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
