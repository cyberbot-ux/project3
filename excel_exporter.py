

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.utils.dataframe import dataframe_to_rows

def export_to_excel(df: pd.DataFrame, file_path: str):
  
    if df.empty:
        raise ValueError("The DataFrame is empty. Nothing to export.")

    wb = Workbook()
    ws = wb.active
    ws.title = "Report"

    # Write data from DataFrame
    for row_idx, row in enumerate(dataframe_to_rows(df, index=False, header=True), 1):
        ws.append(row)
        if row_idx == 1:  # Bold header
            for cell in ws[row_idx]:
                cell.font = Font(bold=True)

    # Auto-fit column widths
    for col in ws.columns:
        max_len = max((len(str(cell.value)) if cell.value is not None else 0) for cell in col)
        ws.column_dimensions[col[0].column_letter].width = max_len + 2

    wb.save(file_path)
