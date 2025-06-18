# exporters/pdf_exporter.py

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
import pandas as pd

def export_to_pdf(df: pd.DataFrame, file_path: str):

    if df.empty:
        raise ValueError("DataFrame is empty. Nothing to export.")

    doc = SimpleDocTemplate(file_path, pagesize=letter)
    data = [list(df.columns)] + df.values.tolist()  # header + rows

    table = Table(data, repeatRows=1)

    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.gray),  # header background
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),  # header font color
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # header font
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.black),
    ])

    table.setStyle(style)
    elements = [table]

    doc.build(elements)
