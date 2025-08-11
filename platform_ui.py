
import sys
import tkinter as tk

def configure_root_for_platform(root: tk.Tk, bar_height: int = 30) -> None:
    """Configure a borderless ticker bar that sits at the bottom.
    Tries to stay below normal windows on Linux by lowering periodically.
    """
    root.overrideredirect(True)
    root.configure(bg="black")

    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    x_pos, y_pos = 0, screen_h - bar_height - 40  # small offset from screen bottom
    root.geometry(f"{screen_w}x{bar_height}+{x_pos}+{y_pos}")

    if sys.platform.startswith("win"):
        # On Windows you can still choose to keep it not-topmost
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
        try:
            # Some WMs honor these (X11). On Wayland they may be ignored.
            root.attributes("-type", "dock")
            root.attributes("-topmost", False)
        except tk.TclError:
            pass

        def keep_lowered():
            try:
                root.lower()
            finally:
                root.after(1500, keep_lowered)  # re-assert occasionally
        keep_lowered()
    else:
        # macOS and others: play it safe
        try:
            root.attributes("-topmost", False)
        except tk.TclError:
            pass