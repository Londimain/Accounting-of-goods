import base64
import io
import os
import tempfile
import atexit

from PIL import Image, ImageTk

from .config import ICON_PATH

try:
    from .embedded_icons import ICONS_DATA
except ImportError:
    ICONS_DATA = {}


ICON_SIZES = {
    "products": (28, 28),
    "operations": (28, 28),
    "balances": (28, 28),
    "add": (22, 22),
    "cancel": (22, 22),
    "up": (22, 22),
    "down": (22, 22),
    "edit": (22, 22),
    "delete": (22, 22),
    "save": (22, 22),
    "calendar": (22, 22),
    "about": (24, 24),
    "excel": (22, 22),          # <-- ДОБАВЛЕНО
}

ICON_FILES = {
    "products": "products.png",
    "operations": "operations.png",
    "balances": "balances.png",
    "add": "add.png",
    "cancel": "cancel.png",
    "up": "up.png",
    "down": "down.png",
    "edit": "edit.png",
    "delete": "delete.png",
    "save": "save.png",
    "calendar": "calendar.png",
    "about": "about.png",
    "excel": "excel.png",       # <-- ДОБАВЛЕНО
}


def _open_pil_image(filename):
    """Возвращает PIL.Image: сначала пробует файл, потом встроенные данные."""
    filepath = os.path.join(ICON_PATH, filename)
    if os.path.exists(filepath):
        try:
            return Image.open(filepath)
        except Exception:
            pass
    if filename in ICONS_DATA:
        try:
            raw = base64.b64decode(ICONS_DATA[filename])
            return Image.open(io.BytesIO(raw))
        except Exception:
            pass
    return None


def load_icons():
    icons = {}
    for key, filename in ICON_FILES.items():
        try:
            img = _open_pil_image(filename)
            if img is None:
                icons[key] = None
                continue
            img = img.copy()
            size = ICON_SIZES.get(key, (24, 24))
            img.thumbnail(size, Image.Resampling.LANCZOS)
            icons[key] = ImageTk.PhotoImage(img)
        except Exception as e:
            print(f"Не удалось загрузить иконку {filename}: {e}")
            icons[key] = None
    return icons


_app_ico_temp_path = None


def materialize_app_ico():
    global _app_ico_temp_path
    if _app_ico_temp_path and os.path.exists(_app_ico_temp_path):
        return _app_ico_temp_path

    filepath = os.path.join(ICON_PATH, "app.ico")
    if os.path.exists(filepath):
        return filepath

    if "app.ico" not in ICONS_DATA:
        return None

    try:
        raw = base64.b64decode(ICONS_DATA["app.ico"])
    except Exception:
        return None

    try:
        fd, tmp = tempfile.mkstemp(suffix=".ico", prefix="inv_app_")
        with os.fdopen(fd, "wb") as f:
            f.write(raw)
        atexit.register(lambda: os.path.exists(tmp) and os.remove(tmp))
        _app_ico_temp_path = tmp
        return tmp
    except Exception:
        return None


def get_app_icon_image():
    return _open_pil_image("app.ico")