import tkinter as tk
from tkinter import messagebox, simpledialog
import json

TICKER_FILE = "tickers.json"

class TickerManager:
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("Manage Watchlist")
        self.window.geometry("400x500")
        self.window.configure(bg="black")
        self.window.resizable(False, False)

        title = tk.Label(
            self.window,
            text="Ticker Manager",
            font=("Segoe UI", 16, "bold"),
            fg="lime",
            bg="black",
            pady=10
        )
        title.pack()

        self.ticker_listbox = tk.Listbox(
            self.window,
            selectmode=tk.SINGLE,
            font=("Courier New", 14),
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
            btn_frame,
            text="➕ Add",
            command=self.add_ticker,
            font=("Segoe UI", 12),
            bg="black",
            fg="lime",
            activebackground="lime",
            activeforeground="black",
            width=12,
            relief=tk.FLAT,
            borderwidth=1,
            highlightbackground="lime",
            highlightcolor="lime"
        )
        self.add_btn.grid(row=0, column=0, padx=5)

        self.remove_btn = tk.Button(
            btn_frame,
            text="❌ Remove",
            command=self.remove_selected,
            font=("Segoe UI", 12),
            bg="black",
            fg="lime",
            activebackground="lime",
            activeforeground="black",
            width=12,
            relief=tk.FLAT,
            borderwidth=1,
            highlightbackground="lime",
            highlightcolor="lime"
        )
        self.remove_btn.grid(row=0, column=1, padx=5)

        self.save_btn = tk.Button(
            self.window,
            text="💾 Save & Close",
            command=self.save_and_exit,
            font=("Segoe UI", 12),
            bg="black",
            fg="lime",
            activebackground="lime",
            activeforeground="black",
            width=25,
            relief=tk.FLAT,
            borderwidth=1,
            highlightbackground="lime",
            highlightcolor="lime"
        )
        self.save_btn.pack(pady=10)
        self.load_tickers()

    def load_tickers(self):
        try:
            with open(TICKER_FILE, "r") as f:
                self.tickers = json.load(f)
        except:
            self.tickers = []

        for ticker in self.tickers:
            self.ticker_listbox.insert(tk.END, ticker)

    def add_ticker(self):
        new_ticker = simpledialog.askstring("Add Ticker", "Enter ticker symbol (e.g., AAPL):")
        if new_ticker:
            new_ticker = new_ticker.strip().upper()
            if new_ticker not in self.tickers:
                self.ticker_listbox.insert(tk.END, new_ticker)
                self.tickers.append(new_ticker)
            else:
                messagebox.showinfo("Exists", "Ticker already in list.")

    def remove_selected(self):
        selected = self.ticker_listbox.curselection()
        if selected:
            index = selected[0]
            ticker = self.ticker_listbox.get(index)
            self.ticker_listbox.delete(index)
            self.tickers.remove(ticker)

    def save_and_exit(self):
        with open(TICKER_FILE, "w") as f:
            json.dump(self.tickers, f, indent=2)
        self.window.destroy()
