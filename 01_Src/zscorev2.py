"""
Z-Score Kalkulator za Dionice (Value faktor)
--------------------------------------------

Ova aplikacija omogućuje korisniku da učita CSV datoteku s financijskim pokazateljima za dionice
i izračuna tzv. "composite z-score" – relativni pokazatelj koliko je neka dionica podcijenjena
ili precijenjena s obzirom na ostale.

Z-Score se računa za 4 metrike:
    - P/E Trailing (što niže = bolje) → invertira se
    - P/E Forward  (što niže = bolje) → invertira se
    - EBIT/TEV     (što više = bolje)
    - P/B          (što niže = bolje) → invertira se

Zatim se izračuna prosjek svih z-score rezultata → "composite_z".

Na temelju toga dajemo preporuku:
    - composite_z >= 0.5     → "Kupi"
    - 0 <= composite_z < 0.5 → "Neutralno"
    - composite_z < 0        → "Preskoci"

Rezultati su sortirani silazno (najbolje dionice na vrhu).

CSV mora imati barem ove kolone:
Ticker, Company, P/E (Trailing), P/E (Forward), EBIT/TEV (%), P/B
"""

import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import pandas as pd
import numpy as np

class ZScoreApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Z-Score Kalkulator za Dionice")

        self.label = tk.Label(root, text="Odaberi CSV datoteku s vrijednosnim podacima:")
        self.label.pack(pady=10)

        self.button = tk.Button(root, text="Učitaj CSV", command=self.load_csv)
        self.button.pack()

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

        required_cols = ["Ticker", "Company", "P/E (Trailing)", "P/E (Forward)", "EBIT/TEV (%)", "P/B"]
        if not all(col in df.columns for col in required_cols):
            messagebox.showerror("Greška", "CSV mora sadržavati kolone: " + ", ".join(required_cols))
            return

        df_clean = df[required_cols].copy()
        df_clean.columns = ["ticker", "company", "pe_trailing", "pe_forward", "ebit_to_tev", "pb_ratio"]

        # Konverzija vrijednosti iz stringa s "," u brojeve
        for col in ["pe_trailing", "pe_forward", "ebit_to_tev", "pb_ratio"]:
            df_clean[col] = pd.to_numeric(df_clean[col].astype(str).str.replace(",", "."), errors='coerce')

        # Funkcija za izračun z-score, s mogućim inverzijama
        def safe_z(col, invert=False):
            x = col.copy()
            if invert:
                x = -x
            mu = np.nanmean(x)
            sigma = np.nanstd(x)
            return (x - mu) / sigma if sigma > 0 else np.full_like(x, np.nan)

        # Izračun z-score za sve metrike
        df_clean["z_pe_trailing"] = safe_z(df_clean["pe_trailing"], invert=True)
        df_clean["z_pe_forward"] = safe_z(df_clean["pe_forward"], invert=True)
        df_clean["z_ebit_to_tev"] = safe_z(df_clean["ebit_to_tev"])
        df_clean["z_pb_ratio"] = safe_z(df_clean["pb_ratio"], invert=True)

        # Kompozitni z-score
        df_clean["composite_z"] = df_clean[
            ["z_pe_trailing", "z_pe_forward", "z_ebit_to_tev", "z_pb_ratio"]
        ].mean(axis=1)

        # Generiraj preporuku
        def get_recommendation(score):
            if score >= 0.5:
                return "Kupi"
            elif score < 0:
                return "Preskoci"
            else:
                return "Neutralno"

        df_clean["Preporuka"] = df_clean["composite_z"].apply(get_recommendation)

        # Sortiraj po score-u
        df_clean.sort_values("composite_z", ascending=False, inplace=True)

        self.data = df_clean.round(3)
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

if __name__ == "__main__":
    root = tk.Tk()
    app = ZScoreApp(root)
    root.mainloop()
