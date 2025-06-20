#designed and developed by prem patel
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sys
import shutil
import pandas as pd
from tksheet import Sheet
from program_manager import add_file_to_cache, get_transactions
from report_analyzer import group_by_date_with_summary, group_by_date_totals_only, ebt_summary_report
from pdf_exporter import export_to_pdf
from excel_exporter import export_to_excel

def get_app_base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

class TransactionViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Card Transactions Viewer")
        self.root.geometry("1000x700")

        self.base_path = get_app_base_path()
        self.xml_folder = os.path.join(self.base_path, "xml_files")
        os.makedirs(self.xml_folder, exist_ok=True)

        self.file_list = []
        self.dataframe = pd.DataFrame()

        self.setup_ui()
        self.auto_load_existing_files()
        self.refresh_file_list()

        if self.file_list:
            self.file_selector.set("All Files")
            self.update_table()

    def setup_ui(self):
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(toolbar, text="Sort:").pack(side=tk.LEFT)
        self.sort_order = ttk.Combobox(toolbar, values=["Newest to Oldest", "Oldest to Newest"], state="readonly")
        self.sort_order.current(0)
        self.sort_order.pack(side=tk.LEFT, padx=5)
        self.sort_order.bind("<<ComboboxSelected>>", lambda e: self.on_view_option_change())

        ttk.Label(toolbar, text="Option:").pack(side=tk.LEFT)
        self.view_option = ttk.Combobox(toolbar, values=["With EBT food", "Group by Date", "Daily Totals"], state="readonly")
        self.view_option.current(0)
        self.view_option.pack(side=tk.LEFT, padx=5)
        self.view_option.bind("<<ComboboxSelected>>", lambda e: self.on_view_option_change())

        ttk.Label(toolbar, text="File:").pack(side=tk.LEFT)
        self.file_selector = ttk.Combobox(toolbar, postcommand=self.refresh_file_list, state="readonly")
        self.file_selector.pack(side=tk.LEFT, padx=5)
        self.file_selector.bind("<<ComboboxSelected>>", lambda e: self.on_view_option_change())

        self.show_totals_only = tk.BooleanVar()
        self.totals_only_checkbox = ttk.Checkbutton(toolbar, text="Totals Only", variable=self.show_totals_only, command=self.update_table)
        self.totals_only_checkbox.pack(side=tk.LEFT, padx=5)

        ttk.Button(toolbar, text="Add XML File", command=self.import_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Export PDF", command=self.export_pdf).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Export Excel", command=self.export_excel).pack(side=tk.LEFT, padx=5)

        ttk.Label(toolbar, text="Font Size:").pack(side=tk.LEFT, padx=(20, 2))
        self.font_size_spin = ttk.Spinbox(toolbar, from_=8, to=24, width=5, command=self.update_font_size)
        self.font_size_spin.set(11)
        self.font_size_spin.pack(side=tk.LEFT)

        branding = ttk.Label(self.root, text="© Sant Corporation", font=("Segoe UI", 10, "italic"))
        branding.pack(pady=(0, 5))

        self.sheet_frame = tk.Frame(self.root)
        self.sheet_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.sheet = Sheet(
            self.sheet_frame,
            headers=[],
            data=[],
            show_x_scrollbar=True,
            show_y_scrollbar=True,
            font=("Segoe UI", 11,"normal"),
            header_font=("Segoe UI", 11, "bold")
        )
        self.sheet.enable_bindings(
            "row_select", "column_width_resize", "arrowkeys", "right_click_popup_menu",
            "rc_select", "copy", "paste", "delete", "undo", "edit_cell"
        )
        self.sheet.grid(row=0, column=0, sticky="nswe")
        self.sheet_frame.grid_rowconfigure(0, weight=1)
        self.sheet_frame.grid_columnconfigure(0, weight=1)
        self.sheet.row_height("all", 28)

    def update_font_size(self):
        size = int(self.font_size_spin.get())
        self.sheet.font(newfont=("Segoe UI", size))
        self.sheet.header_font(newfont=("Segoe UI", size, "bold"))
        self.sheet.refresh()

    def auto_load_existing_files(self):
        for file in os.listdir(self.xml_folder):
            if file.endswith(".xml"):
                path = os.path.join(self.xml_folder, file)
                add_file_to_cache(path)
                if file not in self.file_list:
                    self.file_list.append(file)

    def refresh_file_list(self):
        self.file_selector['values'] = ["All Files"] + self.file_list
        if not self.file_selector.get():
            self.file_selector.set("All Files")

    def import_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("XML files", "*.xml")])
        if not file_path:
            return

        filename = os.path.basename(file_path)
        dest_path = os.path.join(self.xml_folder, filename)

        shutil.copy(file_path, dest_path)
        add_file_to_cache(dest_path)

        if filename not in self.file_list:
            self.file_list.append(filename)

        self.refresh_file_list()
        self.file_selector.set(filename)
        self.update_table()

    def update_table(self):
        if not self.file_list:
            return

        file_name = self.file_selector.get()
        sort_asc = self.sort_order.get() == "Oldest to Newest"
        transactions = get_transactions(file_name)
        view_mode = self.view_option.get()

        report_dispatch = {
            "With EBT food": lambda: ebt_summary_report(transactions, ascending=sort_asc),
            "Daily Totals": lambda: group_by_date_totals_only(transactions, ascending=sort_asc),
            "Group by Date": lambda: group_by_date_with_summary(transactions, ascending=sort_asc, hide_transactions=self.show_totals_only.get())
        }

        df = report_dispatch.get(view_mode, lambda: pd.DataFrame())()
        self.dataframe = df.copy()
        self.update_sheet_from_dataframe()

    def update_sheet_from_dataframe(self):
        self.sheet.set_sheet_data(self.dataframe.values.tolist(), reset_col_positions=True, reset_row_positions=True)
        self.sheet.headers(self.dataframe.columns.tolist())
        self.sheet.total_columns(len(self.dataframe.columns))  
        self.sheet.set_all_column_widths()
        self.sheet.refresh()


    def export_pdf(self):
        if self.dataframe.empty:
            messagebox.showwarning("No Data", "No data to export.")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF Files", "*.pdf")])
        if file_path:
            try:
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                export_to_pdf(self.dataframe, file_path)
                messagebox.showinfo("Success", f"PDF saved: {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save PDF:\n{e}")

    def export_excel(self):
        if self.dataframe.empty:
            messagebox.showwarning("No Data", "No data to export.")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel Files", "*.xlsx")])
        if file_path:
            try:
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                export_to_excel(self.dataframe, file_path)
                messagebox.showinfo("Success", f"Excel saved: {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save Excel:\n{e}")

    def on_view_option_change(self, event=None):
        selected = self.view_option.get()
        if selected == "Group by Date":
            self.totals_only_checkbox.state(["!disabled"])
        else:
            self.totals_only_checkbox.state(["disabled"])
            self.show_totals_only.set(False)
        self.update_table()

if __name__ == "__main__":
    root = tk.Tk()
    app = TransactionViewerApp(root)
    root.mainloop()