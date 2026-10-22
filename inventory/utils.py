import os
from datetime import datetime


def fmt_date(d):
    if not d:
        return "-"
    try:
        dt = datetime.strptime(d, "%Y-%m-%d")
        return dt.strftime("%d.%m.%Y")
    except Exception:
        return d


def fmt_qty_clean(value):
    if value is None:
        return "0"
    v = float(value)
    if v == int(v):
        return str(int(v))
    return str(v).rstrip('0').rstrip('.') if '.' in str(v) else str(v)


def get_desktop_path():
    """Возвращает путь к рабочему столу. Работает и при редиректе в OneDrive."""
    # Windows: используем Shell API (учитывает перемещённый Desktop)
    try:
        import ctypes
        from ctypes import wintypes
        CSIDL_DESKTOPDIRECTORY = 0x0010
        buf = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
        res = ctypes.windll.shell32.SHGetFolderPathW(
            None, CSIDL_DESKTOPDIRECTORY, None, 0, buf)
        if res == 0 and buf.value:
            return buf.value
    except Exception:
        pass

    # Fallback для всех ОС
    home = os.path.expanduser("~")
    for candidate in ("Desktop", "Рабочий стол"):
        p = os.path.join(home, candidate)
        if os.path.isdir(p):
            return p
    return home