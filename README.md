# Futures Position Size Calculator

A no-BS, risk-focused position size calculator for futures traders and prop firm challenge hunters.  
Supports all major CME and Eurex futures plus *any* custom instrument — if you know the tick size, you can calculate.

## Features

- Account size presets and custom input
- Risk per trade in percent or dollars
- Automatic or manual contract calculation (bi-directional)
- Editable tick size and point value
- Search or select instruments, or use "Other" for custom trades
- Real-time min risk and total risk display
- Clean, fast UI (Tkinter, runs locally, no cloud BS)
- Auto-save/load of last used settings

## How to Use

1. Download or clone this repo.
2. Install Python 3.9+ and dependencies:  
   `pip install pandas openpyxl`
3. Run:  
   `python position_size_calculator.py`
4. (To build as an .exe: see build instructions below.)

## Screenshots

_Add a screenshot here if you want to look extra pro._

## Excel File

- The instrument list (`apex_tradable_instruments.xlsx`) can be edited/expanded as needed.

## Build as Standalone EXE

If you want a Windows .exe, run:  
`pyinstaller --onefile -w --add-data "apex_tradable_instruments.xlsx;." position_size_calculator.py`

## License

MIT (or whatever you prefer)

## Author

Tarig Ahmed

www.linkedin.com/in/tarigeahmed

