import tkinter as tk
import yfinance as yf
import json
import ctypes

color_map = {
    "up": "lime",
    "down": "red",
    "neutral": "white",
    "error": "gray"
}

class StockTickerApp:
    def __init__(self, root):
        self.padding_from_right = 50
        self.scroll_speed = 0.5
        self.scroll_offset = 0
        self.font = ("Courier New", 15)
        self.height = 25
        self.root = root
        self.root.overrideredirect(True)
        self.root.configure(bg="black")
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        width = screen_width
        height = 30
        x_pos = 0
        y_pos = screen_height - height - 40

        self.root.geometry(f"{width}x{height}+{x_pos}+{y_pos}")

        try:
            hwnd = self.root.winfo_id()
            ctypes.windll.user32.SetWindowPos(hwnd, -2, 0, 0, 0, 0, 0x0001 | 0x0002)
        except Exception:
            pass

        self.canvas = tk.Canvas(self.root, bg="black", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.load_tickers()
        self.cache_previous_closes()
        self.formatted_ticker_data = self.fetch_prices()

        self.text_ids = self.create_colored_text(self.canvas.winfo_width(), self.height // 2)

        self.update_prices()
        self.move_text()

        manage_btn = tk.Button(
            self.root,
            text="⚙",
            command=self.open_ticker_manager,
            font=("Segoe UI Symbol", 12, "bold"),
            fg="lime",
            bg="black",
            activeforeground="lime",
            activebackground="black",
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=0,
            cursor="hand2"
        )
        manage_btn.place(relx=1.0, rely=0.5, x=-10, anchor="e")

    def create_colored_text(self, x, y):
        parts = []
        for text, color in self.formatted_ticker_data:
            part = self.canvas.create_text(
                x, y,
                text=text,
                font=self.font,
                fill=color,
                anchor="w"
            )
            bbox = self.canvas.bbox(part)
            if bbox:
                x = bbox[2]
            parts.append(part)
        return parts

    def get_combined_text_width(self):
        combined_text = "".join([text for text, _ in self.formatted_ticker_data])
        dummy_id = self.canvas.create_text(0, 0, text=combined_text, font=self.font, anchor="w")
        bbox = self.canvas.bbox(dummy_id)
        self.canvas.delete(dummy_id)
        return bbox[2] if bbox else 0

    def load_tickers(self):
        try:
            with open("tickers.json", "r") as f:
                self.tickers = json.load(f)
        except:
            self.tickers = ["AAPL", "MSFT"]

    def cache_previous_closes(self):
        self.prev_closes = {}
        for ticker in self.tickers:
            try:
                info = yf.Ticker(ticker).info
                prev = info.get("previousClose")
                self.prev_closes[ticker] = prev if prev else None
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
                auto_adjust=False
            )
        except Exception:
            return [("Error fetching data", color_map["error"])]

        for ticker in self.tickers:
            try:
                price_series = data["Adj Close"][ticker] if len(self.tickers) > 1 else data["Adj Close"]
                last_price = price_series.dropna().iloc[-1]
                prev = self.prev_closes.get(ticker)
                if prev:
                    change = ((last_price - prev) / prev) * 100
                    direction = "up" if change >= 0 else "down"
                    sign = "+" if change >= 0 else "-"
                    color = color_map[direction]
                    formatted_data.append((f"{ticker}: ${last_price:.2f} ({sign}{abs(change):.2f}%)   ", color))
                else:
                    formatted_data.append((f"{ticker}: ${last_price:.2f}   ", color_map["neutral"]))
            except Exception:
                formatted_data.append((f"{ticker}: N/A   ", color_map["error"]))

        return formatted_data

    def update_prices(self):
        if hasattr(self, 'move_job'):
            self.root.after_cancel(self.move_job)

        self.formatted_ticker_data = self.fetch_prices()

        for tid in self.text_ids:
            self.canvas.delete(tid)

        self.text_ids = self.create_colored_text(self.canvas.winfo_width(), self.height // 2)

        self.move_text()
        self.root.after(30000, self.update_prices)

    def move_text(self):
        for text_id in self.text_ids:
            self.canvas.move(text_id, -self.scroll_speed, 0)

        x1, _, x2, _ = self.canvas.bbox(self.text_ids[0])[0], 0, self.canvas.bbox(self.text_ids[-1])[2], 0
        text_width = x2 - x1

        if x2 < 0:
            dx = self.canvas.winfo_width() + text_width
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
