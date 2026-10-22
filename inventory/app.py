import hashlib
import webbrowser
from tkinter import Tk, Frame, Label, Button, Toplevel, Text, Scrollbar
import tkinter.ttk as ttk

from PIL import Image, ImageTk

from .config import Colors, APP_NAME, APP_VERSION
from .db import get_db_connection, init_db
from .icons import load_icons, materialize_app_ico, get_app_icon_image
from .styles import apply_styles
from .widgets import WidgetHelpersMixin
from .products_tab import ProductsTabMixin
from .movements_tab import MovementsTabMixin
from .balances_tab import BalancesTabMixin


class InventoryApp(WidgetHelpersMixin, ProductsTabMixin,
                   MovementsTabMixin, BalancesTabMixin):

    def __init__(self, root):
        self.root = root
        self.root.withdraw()
        self.root.title(f"Склад: учёт товаров и операций — v{APP_VERSION}")

        # --- Иконка окна/панели задач ---
        ico_path = materialize_app_ico()
        if ico_path:
            try:
                self.root.iconbitmap(ico_path)
            except Exception:
                pass
        try:
            img = get_app_icon_image()
            if img is not None:
                photo = ImageTk.PhotoImage(img)
                self.root.iconphoto(True, photo)
                self.root._app_icon_photo = photo
        except Exception:
            pass

        self.root.geometry("1400x850")
        self.root.minsize(900, 600)
        self.root.configure(bg=Colors.BG_MAIN)
        self.root.state('zoomed')

        self.icons = load_icons()

        self.bg_main = Colors.BG_MAIN
        self.bg_panel = Colors.BG_PANEL
        self.bg_input = Colors.BG_INPUT
        self.fg_text = Colors.FG_TEXT
        self.fg_light = Colors.FG_LIGHT
        self.fg_dark = Colors.FG_DARK
        self.color_blue = Colors.BLUE
        self.color_green = Colors.GREEN
        self.color_red = Colors.RED
        self.color_yellow = Colors.YELLOW
        self.color_orange = Colors.ORANGE
        self.color_header = Colors.HEADER
        self.color_cancel = Colors.CANCEL

        self.editing_product_id = None
        self.editing_movement_id = None
        self.products_by_name = {}

        self.last_known_products_hash = ""
        self.last_known_movements_hash = ""

        apply_styles(
            bg_panel=self.bg_panel,
            bg_input=self.bg_input,
            fg_text=self.fg_text,
            fg_dark=self.fg_dark,
            color_blue=self.color_blue,
            color_header=self.color_header,
        )

        main_container = Frame(root, bg=self.bg_main)
        main_container.pack(fill="both", expand=True)

        top_panel = Frame(main_container, bg=self.bg_main)
        top_panel.pack(fill="x", padx=10, pady=(15, 10))

        left_buttons = Frame(top_panel, bg=self.bg_main)
        left_buttons.pack(side="left")

        img_products = self.icons.get("products")
        img_operations = self.icons.get("operations")
        img_balances = self.icons.get("balances")

        self.tab_buttons = []
        btn_product = self._make_tab_button(left_buttons, " Товары ", 0, img_products)
        btn_product.pack(side="left", padx=2)
        self.tab_buttons.append(btn_product)

        btn_operation = self._make_tab_button(left_buttons, " Операции ", 1, img_operations)
        btn_operation.pack(side="left", padx=2)
        self.tab_buttons.append(btn_operation)

        btn_balance = self._make_tab_button(left_buttons, " Остатки ", 2, img_balances)
        btn_balance.pack(side="left", padx=2)
        self.tab_buttons.append(btn_balance)

        about_icon = self.icons.get("about")
        
        # 1. Сначала создаём и упаковываем кнопку "Выход" (она будет самой правой)
        self.exit_btn = Button(
            top_panel, text="Выход", command=self.root.destroy,
            bg=self.bg_panel, fg=self.fg_light,
            font=("Segoe UI", 11, "bold"),
            padx=15, pady=2,
            relief="solid",
            borderwidth=1,
            highlightthickness=2,
            highlightcolor="#000000",
            highlightbackground="#000000",
            cursor="hand2",
            compound="left")
        self.exit_btn.pack(side="right", padx=(5, 5))

        # 2. Затем создаём кнопку "О программе" (она встанет слева от "Выхода")
        self.about_btn = Button(
            top_panel, text="О программе", command=self.show_about,
            bg=self.bg_panel, fg=self.fg_light,
            font=("Segoe UI", 11, "bold"),
            padx=15, pady=2,
            relief="solid",
            borderwidth=1,
            highlightthickness=2,
            highlightcolor="#000000",
            highlightbackground="#000000",
            cursor="hand2",
            compound="left")
        if about_icon:
            self.about_btn.config(image=about_icon)
        self.about_btn.pack(side="right", padx=(5, 5))

        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.tab_products = Frame(self.notebook, bg=self.bg_panel)
        self.tab_movements = Frame(self.notebook, bg=self.bg_panel)
        self.tab_balances = Frame(self.notebook, bg=self.bg_panel)

        self.notebook.add(self.tab_products, text="")
        self.notebook.add(self.tab_movements, text="")
        self.notebook.add(self.tab_balances, text="")

        self._update_tab_buttons(0)
        self.notebook.bind("<<NotebookTabChanged>>", self._on_notebook_tab_changed)

        self._build_products_tab()
        self._build_movements_tab()
        self._build_balances_tab()

        self.refresh_dropdowns()
        self.update_products_table()
        self.update_movements_table()
        self.update_balances_table()

        self.update_hashes()
        self.check_db_updates()

        self.root.deiconify()

    # --- Навигация по вкладкам ------------------------------------------------
    def _make_tab_button(self, parent, text, index, icon):
        btn = Button(parent, text=text,
                     command=lambda: self.notebook.select(index),
                     bg=self.bg_panel, fg=self.fg_light,
                     font=("Segoe UI", 11, "bold"),
                     padx=15, pady=2,
                     relief="solid",                # Рамка вместо flat
                     borderwidth=1,                 # Толщина рамки
                     highlightthickness=2,
                     highlightcolor="#000000",      # Чёрный контур
                     highlightbackground="#000000", # Чёрный контур
                     cursor="hand2",
                     compound="left")
        if icon:
            btn.config(image=icon)
        btn.bind("<Enter>", lambda e, b=btn: self._on_tab_enter(b))
        btn.bind("<Leave>", lambda e, b=btn: self._on_tab_leave(b))
        return btn

    def _on_tab_enter(self, btn):
        if btn['bg'] != self.color_blue:
            btn.config(bg=self.bg_input)

    def _on_tab_leave(self, btn):
        try:
            active_index = self.notebook.index(self.notebook.select())
            active_btn = self.tab_buttons[active_index]
            btn.config(bg=self.color_blue if btn is active_btn else self.bg_panel)
        except Exception:
            btn.config(bg=self.bg_panel)

    def _on_notebook_tab_changed(self, event):
        current = self.notebook.index(self.notebook.select())
        self._update_tab_buttons(current)

    def _update_tab_buttons(self, active_index):
        for i, btn in enumerate(self.tab_buttons):
            if i == active_index:
                btn.config(bg=self.color_blue, fg=self.fg_dark)
            else:
                btn.config(bg=self.bg_panel, fg=self.fg_light)

    # --- О программе (ПЕРЕРАБОТАНО) -------------------------------------------
    def show_about(self):
        about_win = Toplevel(self.root)
        about_win.title(f"О программе — {APP_NAME}")
        about_win.configure(bg=self.bg_panel)
        about_win.resizable(False, False)
        about_win.transient(self.root)
        about_win.grab_set()

        # Размеры окна
        width, height = 600, 640
        screen_width = about_win.winfo_screenwidth()
        screen_height = about_win.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2 - 20
        about_win.geometry(f"{width}x{height}+{x}+{y}")
        
        # Заголовки
        header_frame = Frame(about_win, bg=self.bg_panel)
        header_frame.pack(fill="x", pady=(20, 10))
        
        Label(header_frame, text="Движение материалов цеха розлива",
              bg=self.bg_panel, fg=self.color_blue,
              font=("Segoe UI", 18, "bold")).pack()
              
        Label(header_frame, text=f"{APP_NAME} | Версия {APP_VERSION}",
              bg=self.bg_panel, fg=self.fg_text,
              font=("Segoe UI", 12)).pack(pady=(5, 0))
              
        Label(header_frame, text="© 2026 ОАО «Компания MogNat». Все права защищены.",
              bg=self.bg_panel, fg=self.fg_light,
              font=("Segoe UI", 9)).pack(pady=(2, 0))

        # Основной текст в Text-виджете
        text_frame = Frame(about_win, bg=self.bg_input, bd=2, relief="solid")
        text_frame.pack(fill="both", expand=True, padx=25, pady=10)

        desc = """Программа предназначена для автоматизированного учёта товаров на складе.

Основные возможности:
• Ведение реестра товаров с названиями и штрихкодами (GTIN)
• Регистрация прихода и расхода с указанием количества и даты
• Автоматический расчёт текущих остатков на складе
• Просмотр полной истории операций по каждому товару
• Сортировка товаров для удобного поиска
• Экспорт отчёта по остаткам в Excel на рабочий стол
• Автоматическое сохранение всех данных в локальной базе

Как пользоваться программой:
1. Вкладка «Товары» — добавление и редактирование номенклатуры.
2. Вкладка «Операции» — регистрация прихода или расхода.
3. Вкладка «Остатки» — просмотр текущего количества на складе.
4. Клик по товару в «Остатках» открывает историю его операций.
5. Кнопка «Сохранить в Excel» на вкладке «Остатки» выгружает 
   отчёт на рабочий стол в папку «Учёт остатков».

Техническая поддержка:
E-mail: ismxfactor@gmail.com
Телефон: +375 (29) 547-39-03
"""

        txt = Text(text_frame, bg=self.bg_input, fg=self.fg_text,
                   font=("Segoe UI", 10), relief="flat", bd=0,
                   wrap="word", padx=15, pady=15, cursor="arrow")
        txt.insert("1.0", desc)
        txt.config(state="disabled")
        
        scrollbar = Scrollbar(text_frame, command=txt.yview)
        txt.config(yscrollcommand=scrollbar.set)
        
        txt.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # --- Блок с кнопками ---
        btn_frame = Frame(about_win, bg=self.bg_panel)
        btn_frame.pack(pady=(5, 20))

        def open_github():
            # Замените ссылку на ваш реальный репозиторий
            webbrowser.open_new("https://github.com/Londimain/Accounting-of-goods")

        # Кнопка "Репозиторий на GitHub" (ярко-синяя)
        btn_github = Button(btn_frame, text="Репозиторий на GitHub", command=open_github,
               bg="#4a90d9", fg="#000000",  # <-- ИЗМЕНЕНО: ярко-синий фон
               font=("Segoe UI", 11, "bold"),
               padx=25, pady=10,
               relief="solid", borderwidth=1,
               highlightthickness=2,
               highlightcolor="#000000",
               highlightbackground="#000000",
               cursor="hand2")
        btn_github.pack(side="left", padx=(0, 15))

        # Кнопка "Закрыть"
        btn_close = Button(btn_frame, text="Закрыть", command=about_win.destroy,
               bg=self.color_blue, fg="#000000", # <-- ИЗМЕНЕНО fg
               font=("Segoe UI", 11, "bold"),
               padx=50, pady=10,
               relief="solid", borderwidth=1,
               highlightthickness=2,
               highlightcolor="#000000",
               highlightbackground="#000000",
               cursor="hand2")
        btn_close.pack(side="left")

        # Добавляем эффект наведения для красоты
        def on_enter(btn, bg_color):
            if btn['state'] != 'disabled':
                btn['bg'] = self.lighten_color(bg_color)
                
        def on_leave(btn, bg_color):
            if btn['state'] != 'disabled':
                btn['bg'] = bg_color

        # Для GitHub используем новый синий цвет
        btn_github.bind("<Enter>", lambda e: on_enter(btn_github, "#4a90d9"))
        btn_github.bind("<Leave>", lambda e: on_leave(btn_github, "#4a90d9"))
        
        btn_close.bind("<Enter>", lambda e: on_enter(btn_close, self.color_blue))
        btn_close.bind("<Leave>", lambda e: on_leave(btn_close, self.color_blue))

    # --- Синхронизация с БД ---------------------------------------------------
    def update_hashes(self):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name, gtin, sort_order FROM products ORDER BY id")
        rows = cur.fetchall()
        products_str = "".join(
            f"{r['id']}|{r['name']}|{r['gtin']}|{r['sort_order']}" for r in rows)
        self.last_known_products_hash = hashlib.md5(
            products_str.encode()).hexdigest()

        cur.execute("SELECT id, product_id, mtype, qty, date FROM movements ORDER BY id")
        rows = cur.fetchall()
        movements_str = "".join(
            f"{r['id']}|{r['product_id']}|{r['mtype']}|{r['qty']}|{r['date']}"
            for r in rows)
        self.last_known_movements_hash = hashlib.md5(
            movements_str.encode()).hexdigest()
        conn.close()

    def check_db_updates(self):
        need_update = False
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("SELECT id, name, gtin, sort_order FROM products ORDER BY id")
            rows = cur.fetchall()
            products_str = "".join(
                f"{r['id']}|{r['name']}|{r['gtin']}|{r['sort_order']}" for r in rows)
            current_products_hash = hashlib.md5(
                products_str.encode()).hexdigest()

            cur.execute("SELECT id, product_id, mtype, qty, date FROM movements ORDER BY id")
            rows = cur.fetchall()
            movements_str = "".join(
                f"{r['id']}|{r['product_id']}|{r['mtype']}|{r['qty']}|{r['date']}"
                for r in rows)
            current_movements_hash = hashlib.md5(
                movements_str.encode()).hexdigest()

            conn.close()

            if current_products_hash != self.last_known_products_hash:
                self.last_known_products_hash = current_products_hash
                need_update = True
            if current_movements_hash != self.last_known_movements_hash:
                self.last_known_movements_hash = current_movements_hash
                need_update = True

            if need_update:
                self.refresh_dropdowns()
                self.update_products_table()
                self.update_movements_table()
                self.update_balances_table()
                if hasattr(self, 'pm_status'):
                    self.pm_status.config(
                        text="Данные обновлены автоматически",
                        fg="#ffd700")
        except Exception:
            pass
        finally:
            try:
                self.root.after(3000, self.check_db_updates)
            except Exception:
                pass


def main():
    init_db()
    root = Tk()
    InventoryApp(root)
    root.mainloop()