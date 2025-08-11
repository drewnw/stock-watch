import sys
import tkinter as tk
import yfinance as yf
import json
# Windows-only imports guarded below
from platform_ui import configure_root_for_platform
from paths import config_path

# Optional: fonts that exist on both platforms
TITLE_FONT = ("Segoe UI", 12, "bold") if sys.platform.startswith("win") else ("DejaVu Sans", 12, "bold")
SYMBOL_FONT = ("Segoe UI Symbol", 12, "bold") if sys.platform.startswith("win") else ("DejaVu Sans", 12, "bold")
MONO_FONT = ("Courier New", 15) if sys.platform.startswith("win") else ("DejaVu Sans Mono", 15)

color_map = {
    "up": "lime",
    "down": "red",
    "neutral": "white",
    "error": "gray",
}

TICKER_FILE = str(config_path("tickers.json"))

class StockTickerApp:
    def __init__(self, root):
        self.padding_from_right = 50
        self.scroll_speed = 0.5
        self.scroll_offset = 0
        self.font = MONO_FONT
        self.height = 25

        self.root = root
        self.root.configure(bg="black")

        # Let the helper do borderless + placement + stacking behavior per-OS
        configure_root_for_platform(self.root, bar_height=30)

        # Windows-only: gently push window behind normal windows (safe to skip on Linux)
        if sys.platform.startswith("win"):
            try:
                import ctypes
                hwnd = self.root.winfo_id()
                # HWND_BOTTOM = 1, SWP_NOMOVE=0x2, SWP_NOSIZE=0x1
                ctypes.windll.user32.SetWindowPos(hwnd, 1, 0, 0, 0, 0, 0x0001 | 0x0002)
            except Exception:
                pass

        self.canvas = tk.Canvas(self.root, bg="black", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Ensure canvas has a real size before measuring
        self.root.update_idletasks()

        self.load_tickers()
        self.cache_previous_closes()
        self.formatted_ticker_data = self.fetch_prices()

        self.text_ids = self.create_colored_text(self.canvas.winfo_width(), 15)

        self.update_prices()
        self.move_text()

        manage_btn = tk.Button(
            self.root,
            text="⚙",
            command=self.open_ticker_manager,
            font=SYMBOL_FONT,
            fg="lime",
            bg="black",
            activeforeground="lime",
            activebackground="black",
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=0,
            cursor="hand2",
        )
        manage_btn.place(relx=1.0, rely=0.5, x=-10, anchor="e")

    def create_colored_text(self, x, y):
        parts = []
        # y centerline; use canvas height if available
        if y is None:
            h = self.canvas.winfo_height() or 30
            y = h // 2

        for text, color in self.formatted_ticker_data:
            part = self.canvas.create_text(
                x, y, text=text, font=self.font, fill=color, anchor="w"
            )
            bbox = self.canvas.bbox(part)
            if bbox:
                x = bbox[2]  # chain next segment right after previous
            parts.append(part)
        return parts

    def get_combined_text_width(self):
        combined_text = "".join([text for text, _ in self.formatted_ticker_data])
        dummy_id = self.canvas.create_text(0, 0, text=combined_text, font=self.font, anchor="w")
        bbox = self.canvas.bbox(dummy_id)
        self.canvas.delete(dummy_id)
        return (bbox[2] - bbox[0]) if bbox else 0

    def load_tickers(self):
        try:
            with open(TICKER_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.tickers = data if isinstance(data, list) else []
        except FileNotFoundError:
            self.tickers = ["AAPL", "MSFT"]
        except json.JSONDecodeError:
            self.tickers = ["AAPL", "MSFT"]

    def cache_previous_closes(self):
        self.prev_closes = {}
        for ticker in self.tickers:
            try:
                # .info is slow; but fine for now. Could swap to fast_info later.
                info = yf.Ticker(ticker).info
                prev = info.get("previousClose")
                self.prev_closes[ticker] = prev if prev is not None else None
            except Exception:
                self.prev_closes[ticker] = None

    def fetch_prices(self):
        formatted_data = []
        try:
            data = yf.download(
                tickers=" ".join(self.tickers),
                period="1d",
                interval="1m",
                progress=False,
                threads=True,
                auto_adjust=False,
            )
        except Exception:
            return [("Error fetching data", color_map["error"])]

        for ticker in self.tickers:
            try:
                if len(self.tickers) > 1:
                    price_series = data["Adj Close"][ticker]
                else:
                    price_series = data["Adj Close"]
                last_price = float(price_series.dropna().iloc[-1])
                prev = self.prev_closes.get(ticker)

                if prev:
                    change = ((last_price - prev) / prev) * 100
                    direction = "up" if change >= 0 else "down"
                    sign = "+" if change >= 0 else "-"
                    color = color_map[direction]
                    formatted_data.append(
                        (f"{ticker}: ${last_price:.2f} ({sign}{abs(change):.2f}%)   ", color)
                    )
                else:
                    formatted_data.append((f"{ticker}: ${last_price:.2f}   ", color_map["neutral"]))
            except Exception:
                formatted_data.append((f"{ticker}: N/A   ", color_map["error"]))

        return formatted_data

    def update_prices(self):
        if hasattr(self, "move_job"):
            self.root.after_cancel(self.move_job)

        self.formatted_ticker_data = self.fetch_prices()

        # Clear and redraw
        for tid in getattr(self, "text_ids", []):
            self.canvas.delete(tid)
        self.text_ids = self.create_colored_text(self.canvas.winfo_width(), 15)

        self.move_text()
        self.root.after(30000, self.update_prices)

    def move_text(self):
        if not self.text_ids:
            self.move_job = self.root.after(15, self.move_text)
            return

        for text_id in self.text_ids:
            self.canvas.move(text_id, -self.scroll_speed, 0)

        # Compute leftmost and rightmost x from first/last segments
        first_bbox = self.canvas.bbox(self.text_ids[0])
        last_bbox = self.canvas.bbox(self.text_ids[-1])
        if not first_bbox or not last_bbox:
            self.move_job = self.root.after(15, self.move_text)
            return

        x1 = first_bbox[0]
        x2 = last_bbox[2]
        text_width = x2 - x1

        # When the whole chain is off the left edge, jump to the right again
        if x2 < 0:
            dx = (self.canvas.winfo_width() or 600) + text_width
            for tid in self.text_ids:
                self.canvas.move(tid, dx, 0)

        self.move_job = self.root.after(15, self.move_text)

    def open_ticker_manager(self):
        import ticker_manager
        manager = ticker_manager.TickerManager(self.root)
        self.root.wait_window(manager.window)
        self.reload_tickers()

    def reload_tickers(self):
        self.load_tickers()
        self.cache_previous_closes()
        self.update_prices()

if __name__ == "__main__":
    main_window = tk.Tk()
    app = StockTickerApp(main_window)
    main_window.mainloop()
