import tkinter as tk
from tkinter import messagebox, simpledialog
import json
from paths import config_path
import sys

# Cross-platform ticker file path
TICKER_FILE = str(config_path("tickers.json"))

# Optional: simple font choices (Segoe on Win, DejaVu on Linux)
TITLE_FONT = ("Segoe UI", 16, "bold") if sys.platform.startswith("win") else ("DejaVu Sans", 16, "bold")
BTN_FONT   = ("Segoe UI", 12)         if sys.platform.startswith("win") else ("DejaVu Sans", 12)
LIST_FONT  = ("Courier New", 14)      if sys.platform.startswith("win") else ("DejaVu Sans Mono", 14)

class TickerManager:
    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("Manage Watchlist")
        self.window.geometry("400x500")
        self.window.configure(bg="black")
        self.window.resizable(False, False)

        # Make modal-ish
        self.window.transient(parent)
        self.window.grab_set()
        self.window.focus_set()

        title = tk.Label(
            self.window,
            text="Ticker Manager",
            font=TITLE_FONT,
            fg="lime",
            bg="black",
            pady=10
        )
        title.pack()

        self.ticker_listbox = tk.Listbox(
            self.window,
            selectmode=tk.SINGLE,
            font=LIST_FONT,
            bg="black",
            fg="lime",
            highlightthickness=1,
            highlightbackground="lime",
            selectbackground="lime",
            selectforeground="black",
            bd=0
        )
        self.ticker_listbox.pack(fill=tk.BOTH, expand=True, padx=20, pady=(5, 10))

        btn_frame = tk.Frame(self.window, bg="black")
        btn_frame.pack(pady=5)

        self.add_btn = tk.Button(
            btn_frame, text="➕ Add", command=self.add_ticker,
            font=BTN_FONT, bg="black", fg="lime",
            activebackground="lime", activeforeground="black",
            width=12, relief=tk.FLAT, borderwidth=1,
            highlightbackground="lime", highlightcolor="lime"
        )
        self.add_btn.grid(row=0, column=0, padx=5)

        self.remove_btn = tk.Button(
            btn_frame, text="❌ Remove", command=self.remove_selected,
            font=BTN_FONT, bg="black", fg="lime",
            activebackground="lime", activeforeground="black",
            width=12, relief=tk.FLAT, borderwidth=1,
            highlightbackground="lime", highlightcolor="lime"
        )
        self.remove_btn.grid(row=0, column=1, padx=5)

        self.save_btn = tk.Button(
            self.window, text="💾 Save & Close", command=self.save_and_exit,
            font=BTN_FONT, bg="black", fg="lime",
            activebackground="lime", activeforeground="black",
            width=25, relief=tk.FLAT, borderwidth=1,
            highlightbackground="lime", highlightcolor="lime"
        )
        self.save_btn.pack(pady=10)

        self.window.protocol("WM_DELETE_WINDOW", self.save_and_exit)
        self.load_tickers()

    def load_tickers(self):
        try:
            with open(TICKER_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.tickers = data if isinstance(data, list) else []
        except FileNotFoundError:
            self.tickers = []
        except json.JSONDecodeError:
            messagebox.showwarning("Invalid file", "tickers.json is corrupted. Starting fresh.")
            self.tickers = []

        self.ticker_listbox.delete(0, tk.END)
        for ticker in self.tickers:
            self.ticker_listbox.insert(tk.END, ticker)

    def add_ticker(self):
        new_ticker = simpledialog.askstring("Add Ticker", "Enter ticker symbol (e.g., AAPL):", parent=self.window)
        if new_ticker:
            new_ticker = new_ticker.strip().upper()
            if new_ticker and new_ticker not in self.tickers:
                self.ticker_listbox.insert(tk.END, new_ticker)
                self.tickers.append(new_ticker)
            else:
                messagebox.showinfo("Exists", "Ticker already in list.", parent=self.window)

    def remove_selected(self):
        selected = self.ticker_listbox.curselection()
        if selected:
            index = selected[0]
            ticker = self.ticker_listbox.get(index)
            self.ticker_listbox.delete(index)
            try:
                self.tickers.remove(ticker)
            except ValueError:
                pass

    def save_and_exit(self):
        try:
            with open(TICKER_FILE, "w", encoding="utf-8") as f:
                json.dump(self.tickers, f, indent=2, ensure_ascii=False)
        except OSError as e:
            messagebox.showerror("Save failed", f"Could not save tickers:\n{e}", parent=self.window)
        finally:
            self.window.grab_release()
            self.window.destroy()
