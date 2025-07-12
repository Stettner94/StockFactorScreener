import tkinter as tk
from tkinter import filedialog, ttk, messagebox, scrolledtext
import pandas as pd
import numpy as np

class ZScoreApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Z-Score + MSCI Kalkulator")

        self.label = tk.Label(root, text="Odaberi CSV datoteku s vrijednosnim podacima:")
        self.label.pack(pady=10)

        self.button = tk.Button(root, text="Učitaj CSV", command=self.load_csv)
        self.button.pack()

        self.analyze_button = tk.Button(root, text="Pokaži analizu", command=self.show_analysis)
        self.analyze_button.pack(pady=5)

        self.tree = None
        self.data = None

    def load_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV datoteke", "*.csv")])
        if not file_path:
            return

        try:
            df = pd.read_csv(file_path, delimiter=";")
        except Exception as e:
            messagebox.showerror("Greška", f"Ne mogu učitati CSV: {e}")
            return

        base_cols = ["Ticker", "Company", "P/E (Trailing)", "P/E (Forward)", "EBIT/TEV (%)", "P/B"]
        if not all(col in df.columns for col in base_cols):
            messagebox.showerror("Greška", "CSV mora sadržavati osnovne kolone: " + ", ".join(base_cols))
            return

        df_clean = df[base_cols].copy()
        df_clean.columns = ["ticker", "company", "pe_trailing", "pe_forward", "ebit_to_tev", "pb_ratio"]

        def to_float(col):
            return pd.to_numeric(col.astype(str).str.replace(",", "."), errors='coerce')

        for col in ["pe_trailing", "pe_forward", "ebit_to_tev", "pb_ratio"]:
            df_clean[col] = to_float(df_clean[col])

        def safe_z(col, invert=False):
            x = col.copy()
            if invert:
                x = -x
            mu = np.nanmean(x)
            sigma = np.nanstd(x)
            return (x - mu) / sigma if sigma > 0 else np.full_like(x, np.nan)

        df_clean["z_pe_trailing"] = safe_z(df_clean["pe_trailing"], invert=True)
        df_clean["z_pe_forward"] = safe_z(df_clean["pe_forward"], invert=True)
        df_clean["z_ebit_to_tev"] = safe_z(df_clean["ebit_to_tev"])
        df_clean["z_pb_ratio"] = safe_z(df_clean["pb_ratio"], invert=True)

        df_clean["composite_z"] = df_clean[
            ["z_pe_trailing", "z_pe_forward", "z_ebit_to_tev", "z_pb_ratio"]
        ].mean(axis=1)

        def get_recommendation(score):
            if score >= 0.5:
                return "Kupi"
            elif score < 0:
                return "Preskoci"
            else:
                return "Neutralno"

        df_clean["Preporuka"] = df_clean["composite_z"].apply(get_recommendation)

        self.data = df_clean.round(3)
        self.data.sort_values("composite_z", ascending=False, inplace=True)
        self.display_data()

    def display_data(self):
        if self.tree:
            self.tree.destroy()

        self.tree = ttk.Treeview(self.root)
        self.tree["columns"] = list(self.data.columns)
        self.tree["show"] = "headings"

        for col in self.data.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=120)

        for _, row in self.data.iterrows():
            self.tree.insert("", "end", values=list(row))

        self.tree.pack(padx=10, pady=10, fill="x")

        save_button = tk.Button(self.root, text="Spremi kao CSV", command=self.save_csv)
        save_button.pack(pady=5)

    def save_csv(self):
        if self.data is not None:
            file_path = filedialog.asksaveasfilename(defaultextension=".csv",
                                                     filetypes=[("CSV datoteka", "*.csv")])
            if file_path:
                self.data.to_csv(file_path, index=False)
                messagebox.showinfo("Uspjeh", "Podaci su spremljeni u CSV.")

    def show_analysis(self):
        if self.data is None:
            messagebox.showerror("Greška", "Prvo učitaj CSV datoteku.")
            return

        analysis_window = tk.Toplevel(self.root)
        analysis_window.title("Detaljna analiza dionica")
        text_area = scrolledtext.ScrolledText(analysis_window, wrap=tk.WORD, width=120, height=40)
        text_area.pack(padx=10, pady=10, fill="both", expand=True)

        for _, row in self.data.iterrows():
            t = row["ticker"]
            c = row["company"]
            p1 = row["pe_trailing"]
            p2 = row["pe_forward"]
            ebt = row["ebit_to_tev"]
            pb = row["pb_ratio"]
            z1 = row["z_pe_trailing"]
            z2 = row["z_pe_forward"]
            z3 = row["z_ebit_to_tev"]
            z4 = row["z_pb_ratio"]
            comp = row["composite_z"]
            rec = row["Preporuka"]

            explanation = f"""Ticker: {t}
Company: {c}

--- Metrike i Z-Score ---
P/E (Trailing): {p1} → Z: {z1} (niže = bolje)
P/E (Forward): {p2} → Z: {z2} (niže = bolje)
EBIT/TEV: {ebt} → Z: {z3} (više = bolje)
P/B: {pb} → Z: {z4} (niže = bolje)

--- Composite Z-Score ---
Prosjek: {comp}

--- Preporuka ---
{'✅ Kupi' if rec == 'Kupi' else '⚠️ Preskoci' if rec == 'Preskoci' else '➖ Neutralno'}: {rec} – na temelju kombiniranog z-score vrijednosti

------------------------------------------------------------
"""
            text_area.insert(tk.END, explanation)

        text_area.configure(state='disabled')

if __name__ == "__main__":
    root = tk.Tk()
    app = ZScoreApp(root)
    root.mainloop()
