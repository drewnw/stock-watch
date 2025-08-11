import sys
import tkinter as tk

def configure_root_for_platform(root: tk.Tk, bar_height: int = 30) -> None:
    # Linux: do NOT force 'keep lowered' so the bar remains clickable
    root.overrideredirect(True)
    root.configure(bg="black")

    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    x_pos, y_pos = 0, screen_h - bar_height - 40
    root.geometry(f"{screen_w}x{bar_height}+{x_pos}+{y_pos}")

    if sys.platform.startswith("win"):
        # For Windows, keep it non-topmost, nudge to bottom of stack once
        try:
            import ctypes
            hwnd = root.winfo_id()
            # HWND_BOTTOM = 1, SWP_NOMOVE=0x2, SWP_NOSIZE=0x1
            ctypes.windll.user32.SetWindowPos(hwnd, 1, 0, 0, 0, 0, 0x0001 | 0x0002)
        except Exception:
            pass
        try:
            root.attributes("-topmost", False)
        except tk.TclError:
            pass

    elif sys.platform.startswith("linux"):
        # For Linux, keep borderless, don't auto-lower so it's clickable
        try:
            root.attributes("-type", "dock")
        except tk.TclError:
            pass
        try:
            root.attributes("-topmost", False)
        except tk.TclError:
            pass
        try:
            root.lift()
        except Exception:
            pass

    else:
        # For macOS/others: best effort non-topmost
        try:
            root.attributes("-topmost", False)
        except tk.TclError:
            pass