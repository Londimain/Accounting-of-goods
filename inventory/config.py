import os
import sys


def _get_base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


BASE_PATH = _get_base_path()
DB_PATH = "inventory.db"
ICON_PATH = os.path.join(BASE_PATH, "ico")

APP_NAME = "Товарный расчёт"
APP_VERSION = "2.0"


class Colors:
    BG_MAIN = "#2b2b2b"
    BG_PANEL = "#3c3c3c"
    BG_INPUT = "#4a4a4a"
    FG_TEXT = "#ffffff"
    FG_LIGHT = "#4070a7"
    FG_DARK = "#2b2b2b"
    BLUE = "#249e80"
    GREEN = "#5cb85c"
    RED = "#d9534f"
    YELLOW = "#f0ad4e"
    ORANGE = "#f39c12"
    HEADER = "#2b2b2b"
    CANCEL = "#f39c12"