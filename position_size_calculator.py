import tkinter as tk
from tkinter import ttk
import pandas as pd
import os
import json
import sys

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

CONFIG_FILE = "fpsc_config.json"
INSTRUMENT_FILE = resource_path("apex_tradable_instruments.xlsx")
ACCOUNT_SIZES = ["25,000", "50,000", "100,000", "150,000", "250,000", "300,000", "Custom"]

def load_instruments():
    if not os.path.exists(INSTRUMENT_FILE):
        return []
    df = pd.read_excel(INSTRUMENT_FILE)
    instruments = []
    for _, row in df.iterrows():
        try:
            tick_size = float(row["Tick Size"])
        except Exception:
            tick_size = 0.0
        try:
            tick_value = float(row["Point Value"])
        except Exception:
            tick_value = 0.0
        instruments.append({
            "category": row.get("Category", "Other"),
            "name": row["Name"],
            "symbol": row["Symbol"],
            "exchange": row.get("Exchange", ""),
            "tick_size": tick_size,
            "tick_value": tick_value,
        })
    return instruments

INSTRUMENTS = load_instruments()

def filter_instruments(query, category=None):
    query = query.strip().lower()
    results = INSTRUMENTS
    if category and category != "All":
        results = [inst for inst in results if inst["category"] == category]
    if query:
        results = [inst for inst in results if query in inst["name"].lower() or query in inst["symbol"].lower()]
    return results

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

        # --- Variables
        self.account_var = tk.StringVar()
        self.risk_var = tk.StringVar()
        self.stop_var = tk.StringVar()
        self.contract_type_var = tk.StringVar()
        self.instrument_search_var = tk.StringVar()
        self.instrument_var = tk.StringVar()
        self.tick_size_var = tk.StringVar()
        self.tick_value_var = tk.StringVar()
        self.contracts_var = tk.StringVar()
        self.risk_mode = tk.StringVar(value="percent")
        self.is_updating = False
        self.error_var = tk.StringVar(value="")
        self.result_var = tk.StringVar(value="Contracts to Trade: -")
        self.active_field = None

        # --- UI
        self.create_widgets()
        self.update_instrument_dropdown()
        self.account_size_selected()
        self.load_last_used()

    def create_widgets(self):
        # Account Size
        tk.Label(self, text="Account Size ($):").grid(row=0, column=0, sticky='e')
        self.account_combo = ttk.Combobox(self, values=ACCOUNT_SIZES, state='readonly', width=10)
        self.account_combo.grid(row=0, column=1, sticky='w')
        self.account_combo.bind("<<ComboboxSelected>>", self.account_size_selected)
        self.account_entry = tk.Entry(self, textvariable=self.account_var, width=12)
        self.account_entry.grid(row=0, column=2, sticky='w')

        # Risk per Trade
        tk.Label(self, text="Risk per Trade:").grid(row=1, column=0, sticky='e')
        risk_frame = tk.Frame(self)
        risk_frame.grid(row=1, column=1, columnspan=3, sticky='w')
        self.risk_entry = tk.Entry(risk_frame, textvariable=self.risk_var, width=12)
        self.risk_entry.pack(side="left")
        self.percent_btn = ttk.Radiobutton(risk_frame, text="Percent", variable=self.risk_mode, value="percent", command=self.on_risk_mode_change)
        self.percent_btn.pack(side="left", padx=(6,0))
        self.dollars_btn = ttk.Radiobutton(risk_frame, text="Dollars", variable=self.risk_mode, value="dollars", command=self.on_risk_mode_change)
        self.dollars_btn.pack(side="left", padx=(6,0))
        self.risk_unit_label = tk.Label(risk_frame, text="%")
        self.risk_unit_label.pack(side="left", padx=(6,0))

        # Contracts to Trade
        tk.Label(self, text="Contracts to Trade:").grid(row=2, column=0, sticky='e')
        self.contracts_entry = tk.Entry(self, textvariable=self.contracts_var, width=12)
        self.contracts_entry.grid(row=2, column=1, sticky='w')

        # Minimum Risk Label
        self.min_risk_label = tk.Label(self, text="Min risk to trade with current stop loss: -", fg="grey")
        self.min_risk_label.grid(row=3, column=1, columnspan=3, sticky='w')

        # Total risk for N contracts
        self.total_risk_label = tk.Label(self, text="Total risk for X contracts: -", fg="grey")
        self.total_risk_label.grid(row=4, column=1, columnspan=3, sticky='w')

        # Stop Loss
        tk.Label(self, text="Stop Loss (Ticks):").grid(row=5, column=0, sticky='e')
        self.stop_entry = tk.Entry(self, textvariable=self.stop_var, width=12)
        self.stop_entry.grid(row=5, column=1, sticky='w')

        # Contract Type
        tk.Label(self, text="Contract Type:").grid(row=6, column=0, sticky='e')
        self.contract_types = sorted(list({inst["category"] for inst in INSTRUMENTS}))
        self.contract_combo = ttk.Combobox(self, values=self.contract_types + ["All"], textvariable=self.contract_type_var, state='readonly', width=12)
        self.contract_combo.grid(row=6, column=1, sticky='w')
        self.contract_combo.set("All")
        self.contract_combo.bind("<<ComboboxSelected>>", self.update_instrument_dropdown)

        # Instrument search and dropdown
        tk.Label(self, text="Instrument:").grid(row=7, column=0, sticky='e')
        self.instrument_search_var.trace_add('write', self.update_instrument_dropdown)
        self.instrument_search = tk.Entry(self, textvariable=self.instrument_search_var, width=18)
        self.instrument_search.grid(row=7, column=1, sticky='w')

        self.instrument_combo = ttk.Combobox(self, textvariable=self.instrument_var, state='readonly', width=32)
        self.instrument_combo.grid(row=7, column=2, columnspan=2, sticky='w')
        self.instrument_combo.bind("<<ComboboxSelected>>", self.instrument_selected)

        # Tick Size/Value -- now ALWAYS editable
        tk.Label(self, text="Tick Size:").grid(row=8, column=0, sticky='e')
        self.tick_size_entry = tk.Entry(self, textvariable=self.tick_size_var, width=12)
        self.tick_size_entry.grid(row=8, column=1, sticky='w')
        tk.Label(self, text="Tick Value:").grid(row=8, column=2, sticky='e')
        self.tick_value_entry = tk.Entry(self, textvariable=self.tick_value_var, width=12)
        self.tick_value_entry.grid(row=8, column=3, sticky='w')

        # Result
        self.result_label = tk.Label(self, textvariable=self.result_var, font=("Arial", 18, "bold"))
        self.result_label.grid(row=9, column=0, columnspan=4, pady=(10, 0))

        # Copy to clipboard
        self.copy_btn = ttk.Button(self, text="Copy Result", command=self.copy_result)
        self.copy_btn.grid(row=10, column=0, columnspan=4, pady=(4, 0))

        # Error message
        self.error_label = tk.Label(self, textvariable=self.error_var, fg="red")
        self.error_label.grid(row=11, column=0, columnspan=4)

        # Bindings for one-way input logic
        self.risk_entry.bind("<FocusIn>", self.on_risk_focus_in)
        self.risk_entry.bind("<FocusOut>", self.on_focus_out)
        self.contracts_entry.bind("<FocusIn>", self.on_contracts_focus_in)
        self.contracts_entry.bind("<FocusOut>", self.on_focus_out)

        # Variable traces
        self.account_var.trace_add('write', lambda *a, **kw: self.calculate())
        self.risk_var.trace_add('write', lambda *a, **kw: self.one_way_risk_edited())
        self.contracts_var.trace_add('write', lambda *a, **kw: self.one_way_contracts_edited())
        self.stop_var.trace_add('write', lambda *a, **kw: self.calculate())
        self.contract_type_var.trace_add('write', lambda *a, **kw: self.calculate())
        self.instrument_var.trace_add('write', lambda *a, **kw: self.calculate())
        self.tick_size_var.trace_add('write', lambda *a, **kw: self.calculate())
        self.tick_value_var.trace_add('write', lambda *a, **kw: self.calculate())
        self.risk_mode.trace_add('write', self.on_risk_mode_change)
        self.account_combo.bind("<<ComboboxSelected>>", lambda e: self.calculate())
        self.contract_combo.bind("<<ComboboxSelected>>", lambda e: self.calculate())
        self.instrument_combo.bind("<<ComboboxSelected>>", lambda e: self.calculate())

    def on_risk_focus_in(self, event):
        self.active_field = "risk"
    def on_contracts_focus_in(self, event):
        self.active_field = "contracts"
    def on_focus_out(self, event):
        self.active_field = None
    def on_risk_mode_change(self, *args):
        if self.risk_mode.get() == "percent":
            self.risk_unit_label.config(text="%")
        else:
            self.risk_unit_label.config(text="$")
        self.risk_var.set("")
        self.contracts_var.set("")
        self.calculate()
    def highlight_entry(self, entry_widget, is_error):
        try:
            entry_widget.config(bg="#ffd4d4" if is_error else "white")
        except Exception:
            pass
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
        filtered = filter_instruments(query, category)
        self.instrument_search_results = filtered + [{"name": "Other (Manual Input)", "symbol": "OTHER", "tick_size": "", "tick_value": ""}]
        names = [f"{inst['name']} ({inst['symbol']})" for inst in self.instrument_search_results]
        self.instrument_combo["values"] = names
        if names:
            self.instrument_combo.current(0)
            self.instrument_selected()
    def instrument_selected(self, event=None):
        idx = self.instrument_combo.current()
        if 0 <= idx < len(self.instrument_search_results):
            inst = self.instrument_search_results[idx]
            # Only fill if it's not "Other"
            if inst["symbol"] != "OTHER":
                self.tick_size_var.set(str(inst.get("tick_size", "")))
                self.tick_value_var.set(str(inst.get("tick_value", "")))
            else:
                self.tick_size_var.set("")
                self.tick_value_var.set("")
        self.calculate()
    def one_way_risk_edited(self, *args):
        if self.active_field != "risk":
            return
        self.is_updating = True
        try:
            risk_str = self.risk_var.get().strip()
            if not risk_str:
                self.contracts_var.set("")
                self.is_updating = False
                self.calculate()
                return
            account_size = float(self.account_var.get().replace(",", "") or "0")
            risk = float(risk_str)
            stop_ticks = float(self.stop_var.get() or "0")
            tick_value = float(self.tick_value_var.get() or "0")
            mode = self.risk_mode.get()
            if stop_ticks > 0 and tick_value > 0:
                risk_dollars = risk if mode == "dollars" else (account_size * risk / 100.0)
                dollar_risk_per_contract = stop_ticks * tick_value
                contracts = int(risk_dollars // dollar_risk_per_contract)
                self.contracts_var.set(str(contracts if contracts >= 0 else ""))
        except Exception:
            self.contracts_var.set("")
        self.is_updating = False
        self.calculate()
    def one_way_contracts_edited(self, *args):
        if self.active_field != "contracts":
            return
        self.is_updating = True
        try:
            contracts_str = self.contracts_var.get().strip()
            if not contracts_str:
                self.risk_var.set("")
                self.is_updating = False
                self.calculate()
                return
            account_size = float(self.account_var.get().replace(",", "") or "0")
            stop_ticks = float(self.stop_var.get() or "0")
            tick_value = float(self.tick_value_var.get() or "0")
            contracts = float(contracts_str)
            dollar_risk_per_contract = stop_ticks * tick_value
            risk_dollars = contracts * dollar_risk_per_contract
            mode = self.risk_mode.get()
            if mode == "dollars":
                self.risk_var.set(str(round(risk_dollars, 2) if risk_dollars > 0 else ""))
            else:
                risk_percent = (risk_dollars / account_size * 100) if account_size else 0
                self.risk_var.set(str(round(risk_percent, 2) if risk_percent > 0 else ""))
        except Exception:
            self.risk_var.set("")
        self.is_updating = False
        self.calculate()
    def calculate(self, *args):
        self.error_var.set("")
        error = False

        self.highlight_entry(self.account_entry, False)
        self.highlight_entry(self.risk_entry, False)
        self.highlight_entry(self.stop_entry, False)
        self.highlight_entry(self.contracts_entry, False)

        try:
            account_size = float(self.account_var.get().replace(",", "") or "0")
            risk_str = self.risk_var.get().strip()
            contracts_str = self.contracts_var.get().strip()
            stop_ticks = float(self.stop_var.get() or "0")
            tick_size = float(self.tick_size_var.get() or "0")
            tick_value = float(self.tick_value_var.get() or "0")
            contracts = int(contracts_str) if contracts_str and contracts_str.isdigit() else 0
            mode = self.risk_mode.get()

            if account_size <= 0:
                self.error_var.set("Account size must be positive.")
                self.highlight_entry(self.account_entry, True)
                error = True

            if stop_ticks <= 0:
                self.error_var.set("Stop loss (ticks) must be positive.")
                self.highlight_entry(self.stop_entry, True)
                error = True

            if tick_size <= 0 or tick_value <= 0:
                self.error_var.set("Invalid tick size or tick value.")
                error = True

            min_risk_required = stop_ticks * tick_value if stop_ticks and tick_value else 0
            self.min_risk_label.config(text=f"Min risk to trade with current stop loss: ${min_risk_required:.2f}", fg="grey")
            total_risk = contracts * min_risk_required
            self.total_risk_label.config(text=f"Total risk for {contracts} contracts: ${total_risk:.2f}", fg="grey")

            if error:
                self.result_var.set("Contracts to Trade: -")
                self.result_label.config(fg="red")
                return

            risk = float(risk_str) if risk_str else 0
            risk_dollars = risk if mode == "dollars" else (account_size * risk / 100.0 if risk_str else 0)
            dollar_risk_per_contract = stop_ticks * tick_value

            if risk_str and self.active_field == "risk" and not self.is_updating:
                contracts_calc = int(risk_dollars // dollar_risk_per_contract) if dollar_risk_per_contract else 0
                self.contracts_var.set(str(contracts_calc if contracts_calc > 0 else ""))
                contracts = contracts_calc

            if risk_dollars < min_risk_required and risk_dollars > 0:
                self.result_var.set("Contracts to Trade: -")
                self.result_label.config(fg="red")
                self.error_var.set(f"Risk per trade is too low. Must be ≥ ${min_risk_required:.2f}")
                return

            if contracts > 0:
                self.result_var.set(f"Contracts to Trade: {contracts}")
                self.result_label.config(fg="green")
            else:
                self.result_var.set("Contracts to Trade: -")
                self.result_label.config(fg="red")
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
            if "stop" in cfg:
                self.stop_var.set(cfg["stop"])
            if "contracts" in cfg:
                self.contracts_var.set(cfg["contracts"])
            if "risk_mode" in cfg:
                self.risk_mode.set(cfg["risk_mode"])
            if "contract_type" in cfg:
                self.contract_type_var.set(cfg["contract_type"])
            if "instrument" in cfg:
                self.instrument_search_var.set(cfg["instrument"])
            self.calculate()
        except Exception:
            pass

    def save_last_used(self):
        config = {
            "account": self.account_var.get(),
            "risk": self.risk_var.get(),
            "risk_mode": self.risk_mode.get(),
            "stop": self.stop_var.get(),
            "contracts": self.contracts_var.get(),
            "contract_type": self.contract_type_var.get(),
            "instrument": self.instrument_search_var.get()
        }
        save_config(config)

if __name__ == "__main__":
    app = FPSCApp()
    app.mainloop()
