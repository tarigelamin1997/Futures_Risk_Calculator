
import tkinter as tk
from tkinter import ttk, messagebox

instrument_data = {'MES': {'name': 'Micro E-mini S&P 500', 'tick_size': 0.25, 'tick_value_mini': 1.25, 'tick_value_macro': None}, 'MNQ': {'name': 'Micro E-mini Nasdaq-100', 'tick_size': 0.25, 'tick_value_mini': 0.5, 'tick_value_macro': 5.0}, 'MYM': {'name': 'Micro E-mini Dow', 'tick_size': 1, 'tick_value_mini': 0.5, 'tick_value_macro': 5.0}, 'M2K': {'name': 'Micro E-mini Russell 2000', 'tick_size': 0.1, 'tick_value_mini': 0.5, 'tick_value_macro': None}, 'MCL': {'name': 'Micro Crude Oil', 'tick_size': 0.01, 'tick_value_mini': 1.0, 'tick_value_macro': 10.0}, 'MBT': {'name': 'Micro Bitcoin Futures', 'tick_size': 5, 'tick_value_mini': 0.5, 'tick_value_macro': None}, 'NQ': {'name': 'E-mini Nasdaq-100', 'tick_size': 0.25, 'tick_value_mini': 0.5, 'tick_value_macro': 5.0}, 'ES': {'name': 'E-mini S&P 500', 'tick_size': 0.25, 'tick_value_mini': 1.25, 'tick_value_macro': 12.5}, 'CL': {'name': 'Crude Oil', 'tick_size': 0.01, 'tick_value_mini': 1.0, 'tick_value_macro': 10.0}, 'GC': {'name': 'Gold Futures', 'tick_size': 0.1, 'tick_value_mini': 1.0, 'tick_value_macro': 10.0}}

def update_tick_value(*args):
    selected_symbol = instrument_var.get()
    contract_type = contract_type_var.get()
    if selected_symbol and contract_type:
        data = instrument_data[selected_symbol]
        tick_value = data.get(f"tick_value_{contract_type.lower()}")
        if tick_value is not None:
            tick_value_var.set(str(tick_value))
        else:
            tick_value_var.set("N/A")

def calculate_position_size():
    try:
        account_size = float(entry_account_size.get())
        stop_loss_ticks = float(entry_stop_loss.get())
        tick_value = float(tick_value_var.get())

        if risk_type_var.get() == "Percentage":
            risk_input = float(entry_risk_value.get())
            max_risk = account_size * (risk_input / 100)
        else:
            max_risk = float(entry_risk_value.get())

        risk_per_contract = stop_loss_ticks * tick_value
        contracts = int(max_risk // risk_per_contract)

        result_var.set(f"Contracts to Trade: {contracts}")
    except ValueError:
        messagebox.showerror("Invalid input", "Please enter valid numbers.")

root = tk.Tk()
root.title("Futures Position Size Calculator")

# Inputs
tk.Label(root, text="Account Size ($):").grid(row=0, column=0)
entry_account_size = tk.Entry(root)
entry_account_size.grid(row=0, column=1)

tk.Label(root, text="Risk Type:").grid(row=1, column=0)
risk_type_var = tk.StringVar(value="Percentage")
risk_type_menu = ttk.Combobox(root, textvariable=risk_type_var, values=["Percentage", "Dollars"], state="readonly")
risk_type_menu.grid(row=1, column=1)

tk.Label(root, text="Risk Amount (% or $):").grid(row=2, column=0)
entry_risk_value = tk.Entry(root)
entry_risk_value.grid(row=2, column=1)

tk.Label(root, text="Stop Loss (Ticks):").grid(row=3, column=0)
entry_stop_loss = tk.Entry(root)
entry_stop_loss.grid(row=3, column=1)

tk.Label(root, text="Instrument:").grid(row=4, column=0)
instrument_var = tk.StringVar()
instrument_menu = ttk.Combobox(root, textvariable=instrument_var, values=list(instrument_data.keys()), state="readonly")
instrument_menu.grid(row=4, column=1)

tk.Label(root, text="Contract Type:").grid(row=5, column=0)
contract_type_var = tk.StringVar(value="mini")
contract_type_menu = ttk.Combobox(root, textvariable=contract_type_var, values=["mini", "macro"], state="readonly")
contract_type_menu.grid(row=5, column=1)

tk.Label(root, text="Tick Value ($):").grid(row=6, column=0)
tick_value_var = tk.StringVar()
entry_tick_value = tk.Entry(root, textvariable=tick_value_var, state="readonly")
entry_tick_value.grid(row=6, column=1)

# Link dropdown events
instrument_var.trace_add("write", update_tick_value)
contract_type_var.trace_add("write", update_tick_value)

# Button
tk.Button(root, text="Calculate", command=calculate_position_size).grid(row=7, column=0, columnspan=2, pady=10)

# Output
result_var = tk.StringVar()
tk.Label(root, textvariable=result_var, font=("Arial", 14)).grid(row=8, column=0, columnspan=2)

root.mainloop()
