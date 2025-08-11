import sys
import json
import tkinter as tk
import yfinance as yf

from platform_ui import configure_root_for_platform
from paths import config_path

# Fonts and colors

TITLE_FONT  = ("Segoe UI", 12, "bold")        if sys.platform.startswith("win") else ("DejaVu Sans", 12, "bold")
SYMBOL_FONT = ("Segoe UI Symbol", 12, "bold") if sys.platform.startswith("win") else ("DejaVu Sans", 12, "bold")
MONO_FONT   = ("Courier New", 15)             if sys.platform.startswith("win") else ("DejaVu Sans Mono", 15)

color_map = {
    "up": "lime",
    "down": "red",
    "neutral": "white",
    "error": "gray",
}

# Files
TICKER_FILE    = str(config_path("tickers.json"))
SETTINGS_FILE  = "settings.json"

DEFAULT_SETTINGS = {
    "width":  0,   # 0 = full screen width
    "height": 30,
}

DEFAULT_OFFSET = 40

def load_settings():
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            s = json.load(f)
            return {**DEFAULT_SETTINGS, **s}
    except Exception:
        return DEFAULT_SETTINGS.copy()

def save_settings(s):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(s, f, indent=2)
    except Exception:
        pass

# Settings
class SizeSettingsDialog(tk.Toplevel):
    def __init__(self, parent, current):
        super().__init__(parent)
        self.title("Size")
        self.configure(bg="black")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.var_width  = tk.IntVar(value=int(current.get("width", 0)))
        self.var_height = tk.IntVar(value=int(current.get("height", 30)))

        def row(r, label, widget):
            tk.Label(self, text=label, fg="lime", bg="black").grid(row=r, column=0, padx=10, pady=6, sticky="e")
            widget.grid(row=r, column=1, padx=10, pady=6, sticky="w")

        row(0, "Width (px, 0 = full):", tk.Entry(self, textvariable=self.var_width, width=8))
        row(1, "Height (px):",          tk.Entry(self, textvariable=self.var_height, width=8))

        btns = tk.Frame(self, bg="black")
        btns.grid(row=2, column=0, columnspan=2, pady=10)
        tk.Button(btns, text="Apply",   command=self._apply,   bg="black", fg="lime").pack(side="left", padx=8)
        tk.Button(btns, text="Default", command=self._default, bg="black", fg="lime").pack(side="left", padx=8)
        tk.Button(btns, text="Cancel",  command=self._cancel,  bg="black", fg="lime").pack(side="left", padx=8)

        self.result = None

    def _apply(self):
        try:
            w = max(0, int(self.var_width.get()))
            h = max(20, int(self.var_height.get()))
            self.result = {"width": w, "height": h}
        except Exception:
            self.result = None
        self.destroy()

    def _default(self):
        self.result = {"_default": True, "width": 0, "height": DEFAULT_SETTINGS["height"]}
        self.destroy()

    def _cancel(self):
        self.result = None
        self.destroy()

class StockTickerApp:
    def __init__(self, root):
        self.scroll_speed = 0.5
        self.font = MONO_FONT

        self.root = root
        self.root.configure(bg="black")

        configure_root_for_platform(self.root, bar_height=DEFAULT_SETTINGS["height"])
        self.root.update_idletasks()

        # For dragging the application
        self.locked = True
        self._drag_start = (0, 0)
        self._win_start  = (0, 0)

        self.canvas = tk.Canvas(self.root, bg="black", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.root.bind("<Button-1>", self._on_press)
        self.root.bind("<B1-Motion>", self._on_drag)
        self.root.bind("<ButtonRelease-1>", self._on_release)

        self.gear_btn = tk.Button(
            self.root, text="⚙",
            command=lambda: self.open_menu(self.gear_btn),
            font=SYMBOL_FONT, fg="lime", bg="black",
            activeforeground="lime", activebackground="black",
            relief=tk.FLAT, borderwidth=0, highlightthickness=0, cursor="hand2",
        )

        self.lock_btn = tk.Button(
            self.root, text="🔒", command=self.toggle_lock,
            font=SYMBOL_FONT, fg="lime", bg="black",
            activeforeground="lime", activebackground="black",
            relief=tk.FLAT, borderwidth=0, highlightthickness=0, cursor="hand2",
        )
        self.close_btn = tk.Button(
            self.root, text="✖", command=self.terminate,
            font=SYMBOL_FONT, fg="lime", bg="black",
            activeforeground="lime", activebackground="black",
            relief=tk.FLAT, borderwidth=0, highlightthickness=0, cursor="hand2",
        )

        self._place_controls()

        # Data
        self.load_tickers()
        self.cache_previous_closes()
        self.formatted_ticker_data = self.fetch_prices()
        self.text_ids = self.create_colored_text(self.canvas.winfo_width(), None)

        # Loops
        self.update_prices()
        self.move_text()

        # Apply saved size at startup
        self.apply_saved_size()

    # UI Controls
    def _place_controls(self):
        self.gear_btn.place(relx=1.0, rely=0.5, x=-10, anchor="e")
        self.lock_btn.place(relx=1.0, rely=0.5, x=-34, anchor="e")
        self.close_btn.place(relx=1.0, rely=0.5, x=-58, anchor="e")

    # Drag logic when the program is unlocked
    def toggle_lock(self):
        self.locked = not self.locked
        self.lock_btn.config(text="🔒" if self.locked else "🔓")

    def _on_press(self, e):
        if self.locked:
            return
        self._drag_start = (e.x_root, e.y_root)
        try:
            geo = self.root.wm_geometry()
            parts = geo.split("+")
            if len(parts) >= 3:
                x = int(parts[-2]); y = int(parts[-1])
            else:
                x = self.root.winfo_x(); y = self.root.winfo_y()
        except Exception:
            x = self.root.winfo_x(); y = self.root.winfo_y()
        self._win_start = (x, y)

    def _on_drag(self, e):
        if self.locked:
            return
        dx = e.x_root - self._drag_start[0]
        dy = e.y_root - self._drag_start[1]
        nx = self._win_start[0] + dx
        ny = self._win_start[1] + dy
        try:
            w = self.root.winfo_width()
            h = self.root.winfo_height()
            self.root.geometry(f"{w}x{h}+{nx}+{ny}")
        except Exception:
            pass

    def _on_release(self, e):
        pass

    # Settings for dimensions part (H/W)
    def open_menu(self, widget):
        m = tk.Menu(self.root, tearoff=0, bg="black", fg="lime",
                    activebackground="lime", activeforeground="black")
        m.add_command(label="Manage Watchlist", command=self.open_ticker_manager)
        m.add_command(label="Size", command=self.open_size_settings)
        try:
            x = widget.winfo_rootx()
            y = widget.winfo_rooty() + widget.winfo_height()
            m.tk_popup(x, y)
        finally:
            m.grab_release()

    def open_size_settings(self):
        s = load_settings()
        dlg = SizeSettingsDialog(self.root, s)
        self.root.wait_window(dlg)
        if not dlg.result:
            return

        if dlg.result.get("_default"):
            s.update({"width": 0, "height": DEFAULT_SETTINGS["height"]})
            save_settings(s)
            self.apply_default_size(height=s["height"])
        else:
            s.update(dlg.result)
            save_settings(s)
            self.apply_size(s["width"], s["height"])

    def apply_saved_size(self):
        s = load_settings()
        w = s.get("width", 0)
        h = s.get("height", DEFAULT_SETTINGS["height"])
        if int(w) == 0:
            self.apply_default_size(height=h)
        else:
            self.apply_size(w, h)

    def apply_default_size(self, height=None):
        h  = max(20, int(height if height is not None else DEFAULT_SETTINGS["height"]))
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        y  = max(0, sh - h - DEFAULT_OFFSET)
        self.root.geometry(f"{sw}x{h}+0+{y}")
        self.root.update_idletasks()

    def apply_size(self, width_px, height_px):
        h = max(20, int(height_px))
        if int(width_px) == 0:
            self.apply_default_size(height=h)
            return

        w  = max(200, int(width_px))
        x  = self.root.winfo_x()
        y  = self.root.winfo_y()

        sh = self.root.winfo_screenheight()
        # If it's within 80px of bottom, keep the default offset alignment
        if abs((y + self.root.winfo_height()) - sh) <= 80:
            y = max(0, sh - h - DEFAULT_OFFSET)

        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.root.update_idletasks()

    # Terminate program
    def terminate(self):
        self.root.destroy()

    # Render the text
    def create_colored_text(self, x, y):
        parts = []
        if y is None:
            h = self.canvas.winfo_height() or 30
            y = h // 2
        for text, color in self.formatted_ticker_data:
            part = self.canvas.create_text(x, y, text=text, font=self.font, fill=color, anchor="w")
            bbox = self.canvas.bbox(part)
            if bbox:
                x = bbox[2]
            parts.append(part)
        return parts

    # Ticker data
    def load_tickers(self):
        try:
            with open(TICKER_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.tickers = data if isinstance(data, list) else []
        except (FileNotFoundError, json.JSONDecodeError):
            self.tickers = ["AAPL", "MSFT"]

    def cache_previous_closes(self):
        self.prev_closes = {}
        for ticker in self.tickers:
            try:
                info = yf.Ticker(ticker).info
                self.prev_closes[ticker] = info.get("previousClose")
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
            return [("Error fetching data   ", color_map["error"])]

        for ticker in self.tickers:
            try:
                price_series = data["Adj Close"][ticker] if len(self.tickers) > 1 else data["Adj Close"]
                last_price = float(price_series.dropna().iloc[-1].item())
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

    # Loops for pricing and text
    def update_prices(self):
        if hasattr(self, "move_job"):
            self.root.after_cancel(self.move_job)

        self.formatted_ticker_data = self.fetch_prices()

        for tid in getattr(self, "text_ids", []):
            self.canvas.delete(tid)
        self.text_ids = self.create_colored_text(self.canvas.winfo_width(), None)

        self.move_text()
        self.root.after(30000, self.update_prices)

    def move_text(self):
        if not self.text_ids:
            self.move_job = self.root.after(15, self.move_text)
            return

        for text_id in self.text_ids:
            self.canvas.move(text_id, -self.scroll_speed, 0)

        first_bbox = self.canvas.bbox(self.text_ids[0])
        last_bbox  = self.canvas.bbox(self.text_ids[-1])
        if not first_bbox or not last_bbox:
            self.move_job = self.root.after(15, self.move_text)
            return

        x2 = last_bbox[2]
        text_width = last_bbox[2] - first_bbox[0]
        if x2 < 0:
            dx = (self.canvas.winfo_width() or 600) + text_width
            for tid in self.text_ids:
                self.canvas.move(tid, dx, 0)

        self.move_job = self.root.after(15, self.move_text)

    # Watchlist for tickers
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
