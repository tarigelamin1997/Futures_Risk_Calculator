import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import os
import json

CONFIG_FILE = "fpsc_config.json"
INSTRUMENT_FILE = "apex_tradable_instruments.xlsx"

ACCOUNT_SIZES = [
    "25,000", "50,000", "100,000", "150,000", "250,000", "300,000", "Custom"
]

# ---- Load Instrument Data with Currency ----
def load_instruments():
    df = pd.read_excel(INSTRUMENT_FILE)
    instruments = []
    for _, row in df.iterrows():
        pv_raw = str(row["Point Value"]).strip()
        # Detect currency
        if "€" in pv_raw:
            currency = "EUR"
        elif "$" in pv_raw:
            currency = "USD"
        else:
            currency = "USD"  # fallback default

        point_value_str = pv_raw.replace("$", "").replace("€", "").replace(",", "").strip()
        try:
            tick_value = float(point_value_str)
        except ValueError:
            tick_value = 0.0  # fallback for any parse error

        instruments.append({
            "category": row.get("Category", "Other"),
            "name": row["Name"],
            "symbol": row["Symbol"],
            "exchange": row["Exchange"],
            "tick_size": float(row["Tick Size"]),
            "tick_value": tick_value,
            "currency": currency,
        })
    return instruments

INSTRUMENTS = load_instruments()

def filter_instruments(query):
    query = query.strip().lower()
    if not query:
        return INSTRUMENTS
    return [inst for inst in INSTRUMENTS if query in inst["name"].lower() or query in inst["symbol"].lower()]

def save_config(data):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f)
    except Exception:
        pass

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

class FPSCApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Futures Position Size Calculator")
        self.resizable(False, False)
        self.config(padx=16, pady=16)

        self.config_data = load_config()
        self.instrument_search_results = INSTRUMENTS.copy()

        # Define all StringVars *before* any method calls
        self.account_var = tk.StringVar()
        self.risk_var = tk.StringVar()
        self.stop_var = tk.StringVar()
        self.contract_type_var = tk.StringVar()
        self.instrument_search_var = tk.StringVar()
        self.instrument_var = tk.StringVar()
        self.tick_size_var = tk.StringVar()
        self.tick_value_var = tk.StringVar()
        self.currency_var = tk.StringVar()
        self.risk_mode = tk.StringVar(value="percent")

        # Account Size
        tk.Label(self, text="Account Size ($):").grid(row=0, column=0, sticky='e')
        self.account_combo = ttk.Combobox(self, values=ACCOUNT_SIZES, state='readonly', width=10)
        self.account_combo.grid(row=0, column=1, sticky='w')
        self.account_combo.bind("<<ComboboxSelected>>", self.account_size_selected)
        self.account_entry = tk.Entry(self, textvariable=self.account_var, width=12)
        self.account_entry.grid(row=0, column=2, sticky='w')
        tk.Label(self, text="").grid(row=0, column=3, sticky='w')  # Spacer

        # Risk per Trade
        tk.Label(self, text="Risk per Trade:").grid(row=1, column=0, sticky='e')
        self.risk_entry = tk.Entry(self, textvariable=self.risk_var, width=12)
        self.risk_entry.grid(row=1, column=1, sticky='w')

        self.percent_btn = ttk.Radiobutton(self, text="Percent", variable=self.risk_mode, value="percent")
        self.dollars_btn = ttk.Radiobutton(self, text="Dollars", variable=self.risk_mode, value="dollars")
        self.percent_btn.grid(row=1, column=2, sticky='w')
        self.dollars_btn.grid(row=1, column=3, sticky='w')

        # Stop Loss
        tk.Label(self, text="Stop Loss (Ticks):").grid(row=2, column=0, sticky='e')
        self.stop_entry = tk.Entry(self, textvariable=self.stop_var, width=12)
        self.stop_entry.grid(row=2, column=1, sticky='w')

        # Contract Type (Mini/Micro, etc.)
        tk.Label(self, text="Contract Type:").grid(row=3, column=0, sticky='e')
        self.contract_types = sorted(list({inst["category"] for inst in INSTRUMENTS}))
        self.contract_combo = ttk.Combobox(self, values=self.contract_types + ["All"], textvariable=self.contract_type_var, state='readonly', width=12)
        self.contract_combo.grid(row=3, column=1, sticky='w')
        self.contract_combo.set("All")
        self.contract_combo.bind("<<ComboboxSelected>>", self.update_instrument_dropdown)

        # Instrument search and dropdown
        tk.Label(self, text="Instrument:").grid(row=4, column=0, sticky='e')
        self.instrument_search_var.trace_add('write', self.update_instrument_dropdown)
        self.instrument_search = tk.Entry(self, textvariable=self.instrument_search_var, width=18)
        self.instrument_search.grid(row=4, column=1, sticky='w')

        self.instrument_combo = ttk.Combobox(self, textvariable=self.instrument_var, state='readonly', width=32)
        self.instrument_combo.grid(row=4, column=2, columnspan=2, sticky='w')
        self.instrument_combo.bind("<<ComboboxSelected>>", self.instrument_selected)
        self.update_instrument_dropdown()

        # Tick Size/Value/Currency
        tk.Label(self, text="Tick Size:").grid(row=5, column=0, sticky='e')
        tk.Entry(self, textvariable=self.tick_size_var, state='readonly', width=12).grid(row=5, column=1, sticky='w')

        tk.Label(self, text="Tick Value:").grid(row=5, column=2, sticky='e')
        tk.Entry(self, textvariable=self.tick_value_var, state='readonly', width=12).grid(row=5, column=3, sticky='w')

        tk.Label(self, text="Currency:").grid(row=6, column=0, sticky='e')
        tk.Entry(self, textvariable=self.currency_var, state='readonly', width=12).grid(row=6, column=1, sticky='w')

        # Calculate Button
        self.calc_btn = ttk.Button(self, text="Calculate", command=self.calculate)
        self.calc_btn.grid(row=7, column=0, columnspan=4, pady=(10, 0))

        # Result
        self.result_var = tk.StringVar(value="Contracts to Trade: -")
        self.result_label = tk.Label(self, textvariable=self.result_var, font=("Arial", 18, "bold"))
        self.result_label.grid(row=8, column=0, columnspan=4, pady=(10, 0))

        # Copy to clipboard
        self.copy_btn = ttk.Button(self, text="Copy Result", command=self.copy_result)
        self.copy_btn.grid(row=9, column=0, columnspan=4, pady=(4, 0))

        # Error message
        self.error_var = tk.StringVar(value="")
        self.error_label = tk.Label(self, textvariable=self.error_var, fg="red")
        self.error_label.grid(row=10, column=0, columnspan=4)

        self.load_last_used()

    def account_size_selected(self, event=None):
        selected = self.account_combo.get().replace(",", "")
        if selected.lower() == "custom":
            self.account_entry.config(state="normal")
            self.account_var.set("")
        else:
            self.account_entry.config(state="readonly")
            self.account_var.set(selected)

    def update_instrument_dropdown(self, *args):
        query = self.instrument_search_var.get().strip().lower()
        category = self.contract_type_var.get()
        if category == "All":
            filtered = filter_instruments(query)
        else:
            filtered = [inst for inst in filter_instruments(query) if inst["category"] == category]
        self.instrument_search_results = filtered
        names = [f"{inst['name']} ({inst['symbol']})" for inst in filtered]
        self.instrument_combo["values"] = names
        if names:
            self.instrument_combo.current(0)
            self.instrument_selected()
        else:
            self.tick_size_var.set("")
            self.tick_value_var.set("")
            self.currency_var.set("")

    def instrument_selected(self, event=None):
        idx = self.instrument_combo.current()
        if 0 <= idx < len(self.instrument_search_results):
            inst = self.instrument_search_results[idx]
            self.tick_size_var.set(str(inst["tick_size"]))
            self.tick_value_var.set(str(inst["tick_value"]))
            self.currency_var.set(inst["currency"])
        else:
            self.tick_size_var.set("")
            self.tick_value_var.set("")
            self.currency_var.set("")

    def calculate(self):
        # Clear error
        self.error_var.set("")
        try:
            account_size = float(self.account_var.get().replace(",", ""))
            risk = float(self.risk_var.get())
            stop_ticks = float(self.stop_var.get())
            tick_size = float(self.tick_size_var.get())
            tick_value = float(self.tick_value_var.get())
            mode = self.risk_mode.get()

            if account_size <= 0 or risk <= 0 or stop_ticks <= 0 or tick_size <= 0 or tick_value <= 0:
                raise ValueError

            # Calculate risk in dollars/euros
            risk_dollars = risk if mode == "dollars" else (account_size * risk / 100.0)
            dollar_risk_per_contract = stop_ticks * tick_value

            contracts = int(risk_dollars // dollar_risk_per_contract)
            self.result_var.set(f"Contracts to Trade: {contracts}")
            if contracts <= 0:
                self.result_label.config(fg="red")
            else:
                self.result_label.config(fg="green")

            # Save last used
            self.save_last_used()
        except Exception:
            self.result_var.set("Contracts to Trade: -")
            self.result_label.config(fg="red")
            self.error_var.set("Invalid input. Check your numbers and instrument.")

    def copy_result(self):
        self.clipboard_clear()
        self.clipboard_append(self.result_var.get())

    def load_last_used(self):
        cfg = self.config_data
        if not cfg: return
        try:
            if "account" in cfg:
                if cfg["account"] in ACCOUNT_SIZES:
                    self.account_combo.set(cfg["account"])
                    self.account_size_selected()
                else:
                    self.account_combo.set("Custom")
                    self.account_entry.config(state="normal")
                    self.account_var.set(cfg["account"])
            if "risk" in cfg:
                self.risk_var.set(cfg["risk"])
            if "risk_mode" in cfg:
                self.risk_mode.set(cfg["risk_mode"])
            if "stop" in cfg:
                self.stop_var.set(cfg["stop"])
            if "contract_type" in cfg and cfg["contract_type"] in self.contract_types:
                self.contract_combo.set(cfg["contract_type"])
            if "instrument" in cfg:
                self.instrument_search_var.set(cfg["instrument"])
                self.update_instrument_dropdown()
        except Exception:
            pass

    def save_last_used(self):
        config = {
            "account": self.account_var.get(),
            "risk": self.risk_var.get(),
            "risk_mode": self.risk_mode.get(),
            "stop": self.stop_var.get(),
            "contract_type": self.contract_type_var.get(),
            "instrument": self.instrument_search_var.get()
        }
        save_config(config)

if __name__ == "__main__":
    app = FPSCApp()
    app.mainloop()
