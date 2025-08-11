
from pathlib import Path
try:
    from appdirs import user_data_dir
except Exception:
    user_data_dir = None

APP_NAME = "StockWatch"
APP_AUTHOR = "You"

def data_dir() -> Path:
    if user_data_dir is None:
        return Path.cwd() / ".stockwatch_data"
    return Path(user_data_dir(APP_NAME, APP_AUTHOR))

def ensure_data_dir() -> Path:
    d = data_dir()
    d.mkdir(parents=True, exist_ok=True)
    return d

def config_path(filename: str = "tickers.json") -> Path:
    return ensure_data_dir() / filename