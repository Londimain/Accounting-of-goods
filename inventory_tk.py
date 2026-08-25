import os
import sys
import sqlite3
from datetime import datetime
from tkinter import Tk, Frame, Label, Entry, Button, StringVar, messagebox, Toplevel, Scrollbar, N, S, E, W
import tkinter.ttk as ttk
from PIL import Image, ImageTk

DB_PATH = "inventory.db"

# Путь к папке с иконками
if getattr(sys, 'frozen', False):
    base_path = os.path.dirname(sys.executable)
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

ICON_PATH = os.path.join(base_path, "ico")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            gtin TEXT,
            sort_order INTEGER DEFAULT 0
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            mtype TEXT NOT NULL CHECK(mtype IN ('in','out')),
            qty REAL NOT NULL,
            date TEXT NOT NULL,
            FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
        )
    """)
    try:
        cur.execute("ALTER TABLE products ADD COLUMN sort_order INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    cur.execute("UPDATE products SET sort_order = id WHERE sort_order = 0 OR sort_order IS NULL")
    conn.commit()
    conn.close()

def fmt_date(d):
    if not d:
        return "-"
    try:
        dt = datetime.strptime(d, "%Y-%m-%d")
        return dt.strftime("%d.%m.%Y")
    except Exception:
        return d

class InventoryApp:
    @staticmethod
    def fmt_qty_clean(value):
        if value is None:
            return "0"
        v = float(value)
        if v == int(v):
            return str(int(v))
        return str(v).rstrip('0').rstrip('.') if '.' in str(v) else str(v)

    def __init__(self, root):
        self.root = root
        
        # СКРЫВАЕМ ОКНО, чтобы не было белого квадрата при загрузке
        self.root.withdraw()
        
        self.root.title("Склад: учёт товаров и операций")
        
        # Установка иконки ярлыка программы (app.ico)
        icon_path = os.path.join(ICON_PATH, "app.ico")
        if os.path.exists(icon_path):
            try:
                # 1. Загрузка для окна (Windows)
                self.root.iconbitmap(icon_path)
                
                # 2. Загрузка для панели задач и окна (универсально)
                img = Image.open(icon_path)
                photo = ImageTk.PhotoImage(img)
                self.root.iconphoto(True, photo)
                
            except Exception:
                pass
        
        self.root.geometry("1400x850")
        self.root.minsize(900, 600)
        self.root.configure(bg="#2b2b2b")
        self.root.state('zoomed')

        # Загрузка иконок
        self.icons = self._load_icons()

        self.bg_main = "#2b2b2b"
        self.bg_panel = "#3c3c3c"
        self.bg_input = "#4a4a4a"
        self.fg_text = "#ffffff"
        self.fg_light = "#4070a7"
        self.fg_dark = "#2b2b2b"
        self.color_blue = "#249e80"
        self.color_green = "#5cb85c"
        self.color_red = "#d9534f"
        self.color_yellow = "#f0ad4e"
        self.color_orange = "#f39c12"
        self.color_header = "#2b2b2b"
        self.color_cancel = "#f39c12" 
        
        self.editing_product_id = None
        self.editing_movement_id = None

        # Храним хеш для сравнения изменений
        self.last_known_products_hash = ""
        self.last_known_movements_hash = ""

        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure("Treeview",
            rowheight=30,
            background=self.bg_panel,
            foreground=self.fg_text,
            fieldbackground=self.bg_panel,
            font=("Segoe UI", 10),
            borderwidth=1,
            relief="solid",
            bordercolor="#1A2519",
            lightcolor="#1A2519",
            darkcolor="#1A2519")
        
        style.configure("Treeview.Heading",
            background=self.color_header,
            foreground=self.fg_text,
            font=("Segoe UI", 10, "bold"),
            borderwidth=1,
            relief="solid",
            bordercolor="#923D3D",
            lightcolor="#923D3D",
            darkcolor="#923D3D")
        
        style.map("Treeview.Heading",
            background=[("active", self.color_header)])
        style.map("Treeview",
            background=[("selected", self.color_blue)],
            foreground=[("selected", self.fg_dark)])

        # Настройка стиля Notebook – скрываем вкладки (заголовки)
        style.configure("TNotebook", tabmargins=[0, 0, 0, 0], borderwidth=0)
        style.configure("TNotebook.Tab", padding=[0, 0, 0, 0], borderwidth=0, focuscolor="none")
        style.layout("TNotebook.Tab", [])  # убираем отрисовку вкладок

        style.configure("Custom.TEntry",
            fieldbackground=self.bg_input,
            background=self.bg_input,
            foreground=self.fg_text,
            insertcolor=self.fg_text,
            bordercolor="#ffffff",
            lightcolor="#ffffff",
            darkcolor="#ffffff",
            borderwidth=2,
            relief="solid",
            padding=(8, 6))
        style.map("Custom.TEntry",
            fieldbackground=[("readonly", self.bg_input)],
            foreground=[("readonly", self.fg_text)],
            insertcolor=[("readonly", self.fg_text)],
            bordercolor=[("focus", "#ffffff")],
            lightcolor=[("focus", "#ffffff")],
            darkcolor=[("focus", "#ffffff")])

        style.configure("Qty.TEntry",
            fieldbackground=self.bg_input,
            background=self.bg_input,
            foreground=self.fg_text,
            insertcolor=self.fg_text,
            bordercolor="#ffffff",
            lightcolor="#ffffff",
            darkcolor="#ffffff",
            borderwidth=2,
            relief="solid",
            padding=(8, 6),
            font=("Segoe UI", 13))
        style.map("Qty.TEntry",
            fieldbackground=[("readonly", self.bg_input)],
            foreground=[("readonly", self.fg_text)],
            insertcolor=[("readonly", self.fg_text)],
            bordercolor=[("focus", "#ffffff")],
            lightcolor=[("focus", "#ffffff")],
            darkcolor=[("focus", "#ffffff")])

        style.configure("Custom.TCombobox",
            fieldbackground=self.bg_input,
            background=self.bg_input,
            foreground=self.fg_text,
            arrowcolor=self.fg_text,
            borderwidth=2,
            relief="solid",
            bordercolor="#ffffff",
            padding=(8, 6))
        style.map("Custom.TCombobox",
            fieldbackground=[("readonly", self.bg_input)],
            foreground=[("readonly", self.fg_text)],
            bordercolor=[("focus", "#ffffff")])

        style.configure("Small.TCombobox",
            fieldbackground=self.bg_input,
            background=self.bg_input,
            foreground=self.fg_text,
            arrowcolor=self.fg_text,
            borderwidth=2,
            relief="solid",
            bordercolor="#ffffff")
        style.map("Small.TCombobox",
            fieldbackground=[("readonly", self.bg_input)],
            foreground=[("readonly", self.fg_text)],
            bordercolor=[("focus", "#ffffff")])

        main_container = Frame(root, bg=self.bg_main)
        main_container.pack(fill="both", expand=True)

        # Верхняя панель с кнопками навигации
        top_panel = Frame(main_container, bg=self.bg_main)
        top_panel.pack(fill="x", padx=10, pady=(15, 10))

        # Контейнер для левых кнопок (вкладки)
        left_buttons = Frame(top_panel, bg=self.bg_main)
        left_buttons.pack(side="left")

        # Получаем иконки для кнопок
        img_products = self.icons.get("products")
        img_operations = self.icons.get("operations")
        img_balances = self.icons.get("balances")

        # Создаём кнопки-вкладки
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

        # Кнопка "О программе" справа с иконкой
        about_icon = self.icons.get("about")
        self.about_btn = Button(top_panel, text="О программе", command=self.show_about,
                                bg=self.bg_panel, fg=self.fg_light,
                                font=("Segoe UI", 11, "bold"),
                                padx=15, pady=2,
                                # ИЗМЕНЕНО: Черный контур заменен на яркий оранжевый #FFB300
                                relief="flat",
                                borderwidth=0,
                                highlightthickness=3,
                                highlightcolor="#FFB300",
                                highlightbackground="#FFB300",
                                cursor="hand2",
                                compound="left")
        if about_icon:
            self.about_btn.config(image=about_icon)
        self.about_btn.pack(side="right", padx=(0, 5))

        # Основной Notebook (без видимых вкладок)
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.tab_products = Frame(self.notebook, bg=self.bg_panel)
        self.tab_movements = Frame(self.notebook, bg=self.bg_panel)
        self.tab_balances = Frame(self.notebook, bg=self.bg_panel)

        self.notebook.add(self.tab_products, text="")
        self.notebook.add(self.tab_movements, text="")
        self.notebook.add(self.tab_balances, text="")

        # Устанавливаем начальную активную кнопку
        self._update_tab_buttons(0)

        # Привязываем событие переключения вкладки для обновления кнопок
        self.notebook.bind("<<NotebookTabChanged>>", self._on_notebook_tab_changed)

        # Строим содержимое вкладок
        self._build_products_tab()
        self._build_movements_tab()
        self._build_balances_tab()

        self.refresh_dropdowns()
        self.update_products_table()
        self.update_movements_table()
        self.update_balances_table()

        # Инициализация хешей
        self.update_hashes()
        # Запуск автоматической проверки обновлений
        self.check_db_updates()

        # ПОКАЗЫВАЕМ ОКНО, когда всё готово
        self.root.deiconify()

    def _make_tab_button(self, parent, text, index, icon):
        """Создаёт кнопку, имитирующую вкладку, для навигации"""
        btn = Button(parent, text=text, command=lambda: self.notebook.select(index),
                     bg=self.bg_panel, fg=self.fg_light,
                     font=("Segoe UI", 11, "bold"),
                     padx=15, pady=2,
                     # ИЗМЕНЕНО: Черный контур заменен на яркий оранжевый #FFB300
                     relief="flat",
                     borderwidth=0,
                     highlightthickness=3,
                     highlightcolor="#FFB300",
                     highlightbackground="#FFB300",
                     cursor="hand2",
                     compound="left")
        if icon:
            btn.config(image=icon)
        # Эффект наведения
        btn.bind("<Enter>", lambda e, b=btn: b.config(bg=self.bg_input) if b['bg'] != self.color_blue else None)
        btn.bind("<Leave>", lambda e, b=btn: b.config(bg=self.color_blue if b is self.tab_buttons[self.notebook.index(self.notebook.select())] else self.bg_panel))
        return btn

    def _on_notebook_tab_changed(self, event):
        """Обновляет активную кнопку при переключении вкладки"""
        current = self.notebook.index(self.notebook.select())
        self._update_tab_buttons(current)

    def _update_tab_buttons(self, active_index):
        """Устанавливает активную кнопку и сбрасывает остальные"""
        for i, btn in enumerate(self.tab_buttons):
            if i == active_index:
                btn.config(bg=self.color_blue, fg=self.fg_dark)
            else:
                btn.config(bg=self.bg_panel, fg=self.fg_light)

    def show_about(self):
        """Показывает окно с информацией о программе (по центру экрана)"""
        about_win = Toplevel(self.root)
        about_win.title("О программе")
        about_win.configure(bg=self.bg_panel)
        about_win.resizable(False, False)
        about_win.transient(self.root)
        about_win.grab_set()

        # Размеры окна (УВЕЛИЧЕНЫ)
        width, height = 600, 650
        # Позиционирование по центру экрана
        screen_width = about_win.winfo_screenwidth()
        screen_height = about_win.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        about_win.geometry(f"{width}x{height}+{x}+{y}")

        # Заголовок
        Label(about_win, text="Движение материалов цеха розлива.",
              bg=self.bg_panel, fg=self.color_blue,
              font=("Segoe UI", 16, "bold")).pack(pady=(10, 5))

        Label(about_win, text="Версия 1.0 | Дата выпуска: 2026",
              bg=self.bg_panel, fg=self.fg_light,
              font=("Segoe UI", 10)).pack(pady=(0, 15))

        # Описание (текст со скриншота)
        desc = """
Программа предназначена для автоматизированного учёта товаров на складе.
Позволяет вести базу товаров, фиксировать приход и расход,
контролировать остатки и получать полную историю операций.

Основные возможности:
• Ведение реестра товаров с названиями и штрихкодами (GTIN)
• Регистрация прихода и расхода товаров с указанием количества и даты
• Автоматический расчёт текущих остатков на складе
• Просмотр полной истории операций по каждому товару
• Сортировка товаров и операций для удобного поиска
• Автоматическое сохранение всех данных в локальной базе

Как пользоваться программой:
1. Перейдите на вкладку «Товары», чтобы добавить или отредактировать номенклатуру.
2. На вкладке «Операции» зарегистрируйте приход или расход по выбранному товару.
3. Перейдите на вкладку «Остатки», чтобы увидеть текущее количество на складе.
4. Кликните на любой товар в «Остатках», чтобы увидеть всю историю его операций.
5. Для возврата к полному списку операций нажмите кнопку «Отмена».

Техническая поддержка:
E-mail: ismxfactor@gmail.com
Телефон: +375 (29) 547-39-03


© 2026 ОАО «Компания MogNat». Все права защищены.
        """
        # Добавлен wraplength для переноса текста внутри окна
        lbl = Label(about_win, text=desc, bg=self.bg_panel, fg=self.fg_text,
                    font=("Segoe UI", 10), justify="left", wraplength=650)
        lbl.pack(padx=20, pady=10, fill="both", expand=True)

        # Кнопка закрыть
        btn = Button(about_win, text="Закрыть", command=about_win.destroy,
                     bg=self.color_blue, fg="#ffffff",
                     font=("Segoe UI", 10, "bold"),
                     padx=20, pady=5,
                     relief="solid", borderwidth=2,
                     highlightthickness=2,
                     highlightcolor="#ffffff",
                     highlightbackground="#ffffff")
        btn.pack(pady=15)

    def _load_icons(self):
        """Загружает иконки из папки ico с автоматическим масштабированием"""
        from PIL import Image, ImageTk
        icons = {}
        
        icon_sizes = {
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
            "about": (24, 24),   # иконка для кнопки "О программе"
        }
        
        icon_files = {
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
        }
        
        for key, filename in icon_files.items():
            filepath = os.path.join(ICON_PATH, filename)
            if os.path.exists(filepath):
                try:
                    img = Image.open(filepath)
                    size = icon_sizes.get(key, (24, 24))
                    img.thumbnail(size, Image.Resampling.LANCZOS)
                    icons[key] = ImageTk.PhotoImage(img)
                except Exception as e:
                    print(f"Не удалось загрузить иконку {filename}: {e}")
                    icons[key] = None
            else:
                icons[key] = None
        
        return icons

    def make_icon_button(self, parent, text, icon_key, command=None, bg="#4a90d9", fg="#ffffff", padx=20, pady=6):
        """Создаёт кнопку с иконкой, текстом и белой рамкой"""
        btn = Button(parent, text=text, command=command,
                    bg=bg, fg=fg,
                    disabledforeground=fg, 
                    font=("Segoe UI", 10, "bold"),
                    padx=padx, pady=pady,
                    relief="solid",
                    borderwidth=2,
                    highlightthickness=2,
                    highlightcolor="#ffffff",
                    highlightbackground="#ffffff",
                    cursor="hand2",
                    compound="left")
        
        icon = self.icons.get(icon_key)
        if icon:
            btn.config(image=icon)
        
        def on_enter(e):
            if btn['state'] != 'disabled':
                btn['bg'] = self.lighten_color(bg)
        
        def on_leave(e):
            if btn['state'] != 'disabled':
                btn['bg'] = bg
        
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn

    def update_hashes(self):
        """Обновляет хеши данных для сравнения"""
        import hashlib
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name, gtin, sort_order FROM products ORDER BY id")
        rows = cur.fetchall()
        products_str = "".join(f"{r['id']}|{r['name']}|{r['gtin']}|{r['sort_order']}" for r in rows)
        self.last_known_products_hash = hashlib.md5(products_str.encode()).hexdigest()
        
        cur.execute("SELECT id, product_id, mtype, qty, date FROM movements ORDER BY id")
        rows = cur.fetchall()
        movements_str = "".join(f"{r['id']}|{r['product_id']}|{r['mtype']}|{r['qty']}|{r['date']}" for r in rows)
        self.last_known_movements_hash = hashlib.md5(movements_str.encode()).hexdigest()
        conn.close()

    def check_db_updates(self):
        """Проверяет изменения в базе и обновляет интерфейс"""
        import hashlib
        need_update = False
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            
            cur.execute("SELECT id, name, gtin, sort_order FROM products ORDER BY id")
            rows = cur.fetchall()
            products_str = "".join(f"{r['id']}|{r['name']}|{r['gtin']}|{r['sort_order']}" for r in rows)
            current_products_hash = hashlib.md5(products_str.encode()).hexdigest()
            
            cur.execute("SELECT id, product_id, mtype, qty, date FROM movements ORDER BY id")
            rows = cur.fetchall()
            movements_str = "".join(f"{r['id']}|{r['product_id']}|{r['mtype']}|{r['qty']}|{r['date']}" for r in rows)
            current_movements_hash = hashlib.md5(movements_str.encode()).hexdigest()
            
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
                    self.pm_status.config(text="Данные обновлены автоматически", fg="#ffd700")
        except Exception:
            pass
        
        self.root.after(3000, self.check_db_updates)

    def make_button(self, parent, text, command=None, bg="#4a90d9", fg="#ffffff", padx=20, pady=6):
        btn = Button(parent, text=text, command=command,
                    bg=bg, fg=fg,
                    disabledforeground=fg, 
                    font=("Segoe UI", 10, "bold"),
                    padx=padx, pady=pady,
                    relief="solid",
                    borderwidth=2,
                    highlightthickness=2,
                    highlightcolor="#ffffff",
                    highlightbackground="#ffffff",
                    cursor="hand2")
        
        def on_enter(e):
            if btn['state'] != 'disabled':
                btn['bg'] = self.lighten_color(bg)
        
        def on_leave(e):
            if btn['state'] != 'disabled':
                btn['bg'] = bg
        
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn
    
    def lighten_color(self, color):
        if color == "#4a90d9":
            return "#5ba0e9"
        elif color == "#5cb85c":
            return "#6cc86c"
        elif color == "#d9534f":
            return "#e9635f"
        elif color == "#f0ad4e":
            return "#f0bd5e"
        elif color == "#f39c12":
            return "#f4ac22"
        return color

    # -------------------------------------------------------------------------
    # ТОВАРЫ
    # -------------------------------------------------------------------------
    def _build_products_tab(self):
        frame = self.tab_products
        
        top_frame = Frame(frame, bg=self.bg_panel)
        top_frame.pack(fill="x", padx=20, pady=(15, 10)) 
        
        for col in range(8): 
            top_frame.grid_columnconfigure(col, weight=1)
        
        Label(top_frame, text="Название:", bg=self.bg_panel, fg=self.fg_text, 
              font=("Segoe UI", 11)).grid(row=0, column=1, padx=5, pady=10, sticky="e")
        self.pm_name = ttk.Entry(top_frame, width=50, style="Custom.TEntry")
        self.pm_name.grid(row=0, column=2, padx=5, pady=10, sticky="w")
        
        Label(top_frame, text="GTIN:", bg=self.bg_panel, fg=self.fg_text,
              font=("Segoe UI", 11)).grid(row=0, column=3, padx=15, pady=10, sticky="e")
        self.pm_gtin = ttk.Entry(top_frame, width=25, style="Custom.TEntry")
        self.pm_gtin.grid(row=0, column=4, padx=5, pady=10, sticky="w")
        
        btn_frame = Frame(top_frame, bg=self.bg_panel)
        btn_frame.grid(row=0, column=5, columnspan=2, padx=10, pady=10)
        
        self.pm_add_btn = self.make_icon_button(btn_frame, " Добавить", "add", self.on_product_add, self.color_blue, padx=15, pady=8)
        self.pm_add_btn.pack(side="left", padx=50)
        
        self.pm_cancel_btn = self.make_icon_button(btn_frame, " Отмена", "cancel", self.on_product_cancel, self.color_cancel, self.fg_text, padx=15, pady=8)
        self.pm_cancel_btn.pack(side="left", padx=0)
        self.pm_cancel_btn.config(state="disabled")
        
        self.pm_status = Label(frame, text="", bg=self.bg_panel, fg=self.color_red, font=("Segoe UI", 10))
        self.pm_status.pack(anchor="w", padx=20, pady=(0, 5))
        
        table_frame = Frame(frame, bg=self.bg_panel)
        table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        
        columns = ("name", "gtin")
        self.products_tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        
        self.products_tree.heading("name", text="Товар", anchor="center")
        self.products_tree.heading("gtin", text="GTIN", anchor="center")
        
        self.products_tree.column("name", width=600, anchor="w")
        self.products_tree.column("gtin", width=250, anchor="center")
        
        self.products_tree.tag_configure('odd', background=self.bg_panel)
        self.products_tree.tag_configure('even', background=self.bg_input)
        
        scroll_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.products_tree.yview)
        self.products_tree.configure(yscrollcommand=scroll_y.set)
        
        self.products_tree.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")
        
        action_frame = Frame(frame, bg=self.bg_panel)
        action_frame.pack(fill="x", padx=20, pady=(10, 20))
        
        for col in range(4):
            action_frame.grid_columnconfigure(col, weight=1)
        
        btn_container = Frame(action_frame, bg=self.bg_panel)
        btn_container.grid(row=0, column=1, columnspan=2)
        
        self.make_icon_button(btn_container, " Вверх", "up", lambda: self.on_move_product("up"), self.color_blue, padx=15, pady=8).pack(side="left", padx=(5, 20))
        self.make_icon_button(btn_container, " Вниз", "down", lambda: self.on_move_product("down"), self.color_blue, padx=15, pady=8).pack(side="left", padx=(5, 80))
        
        self.make_icon_button(btn_container, " Изменить", "edit", self.on_product_edit, self.color_yellow, self.fg_dark, padx=15, pady=8).pack(side="left", padx=(80, 25))
        self.make_icon_button(btn_container, " Удалить", "delete", self.on_product_delete, self.color_red, padx=15, pady=8).pack(side="left", padx=(5, 5))

    def update_products_table(self):
        for item in self.products_tree.get_children():
            self.products_tree.delete(item)
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name, gtin FROM products ORDER BY sort_order, id")
        rows = cur.fetchall()
        conn.close()
        
        for idx, row in enumerate(rows):
            tag = 'even' if idx % 2 == 0 else 'odd'
            self.products_tree.insert("", "end", values=(row["name"], row["gtin"] or ""), 
                                     iid=str(row["id"]), tags=(tag,))

    def on_product_add(self):
        name = self.pm_name.get().strip()
        gtin = self.pm_gtin.get().strip()
        
        if not name:
            self.pm_status.config(text="❌ Введите название", fg=self.color_red)
            return
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        try:
            if self.editing_product_id:
                cur.execute("UPDATE products SET name=?, gtin=? WHERE id=?", (name, gtin, self.editing_product_id))
                self.pm_status.config(text="✅ Товар обновлён", fg=self.color_green)
                self.editing_product_id = None
            else:
                cur.execute("SELECT COALESCE(MAX(sort_order), 0) + 1 FROM products")
                next_order = cur.fetchone()[0]
                cur.execute("INSERT INTO products (name, gtin, sort_order) VALUES (?, ?, ?)", (name, gtin, next_order))
                self.pm_status.config(text="✅ Товар добавлен", fg=self.color_green)
            
            conn.commit()
            self.on_product_cancel()
            self.update_products_table()
            self.update_movements_table()
            self.refresh_dropdowns()
            self.update_balances_table()
            self.update_hashes()
            
        except sqlite3.IntegrityError:
            self.pm_status.config(text="❌ Такой товар уже есть", fg=self.color_red)
        finally:
            conn.close()

    def on_product_cancel(self):
        self.editing_product_id = None
        self.pm_name.delete(0, "end")
        self.pm_gtin.delete(0, "end")
        self.pm_add_btn.config(text=" Добавить")
        self.pm_cancel_btn.config(state="disabled")
        self.pm_status.config(text="")

    def on_product_edit(self):
        sel = self.products_tree.selection()
        if not sel:
            messagebox.showwarning("Внимание", "Выберите товар")
            return
        
        pid = int(sel[0])
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT name, gtin FROM products WHERE id=?", (pid,))
        row = cur.fetchone()
        conn.close()
        
        if row:
            self.editing_product_id = pid
            self.pm_name.delete(0, "end")
            self.pm_name.insert(0, row["name"])
            self.pm_gtin.delete(0, "end")
            self.pm_gtin.insert(0, row["gtin"] or "")
            self.pm_add_btn.config(text=" Обновить")
            self.pm_cancel_btn.config(state="normal")
            self.pm_status.config(text="Режим редактирования", fg=self.color_yellow)

    def on_product_delete(self):
        sel = self.products_tree.selection()
        if not sel:
            messagebox.showwarning("Внимание", "Выберите товар")
            return
        
        if messagebox.askyesno("Подтверждение", "Удалить товар и все операции?"):
            pid = int(sel[0])
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM products WHERE id=?", (pid,))
            conn.commit()
            conn.close()
            
            self.update_products_table()
            self.update_movements_table()
            self.update_balances_table()
            self.refresh_dropdowns()
            self.pm_status.config(text="✅ Товар удалён", fg=self.color_green)
            self.update_hashes()

    def on_move_product(self, direction):
        sel = self.products_tree.selection()
        if not sel:
            messagebox.showwarning("Внимание", "Выберите товар")
            return
        
        pid = int(sel[0])
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT sort_order FROM products WHERE id=?", (pid,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return
        
        current_order = row["sort_order"]
        
        if direction == "up":
            cur.execute("SELECT id, sort_order FROM products WHERE sort_order < ? ORDER BY sort_order DESC LIMIT 1", (current_order,))
        else:
            cur.execute("SELECT id, sort_order FROM products WHERE sort_order > ? ORDER BY sort_order ASC LIMIT 1", (current_order,))
        
        other = cur.fetchone()
        if not other:
            conn.close()
            return
        
        cur.execute("UPDATE products SET sort_order = ? WHERE id = ?", (other["sort_order"], pid))
        cur.execute("UPDATE products SET sort_order = ? WHERE id = ?", (current_order, other["id"]))
        conn.commit()
        conn.close()
        
        self.update_products_table()
        self.update_balances_table()
        self.refresh_dropdowns()
        self.update_hashes()

    # -------------------------------------------------------------------------
    # ОПЕРАЦИИ
    # -------------------------------------------------------------------------
    def _build_movements_tab(self):
        frame = self.tab_movements
        
        top_frame = Frame(frame, bg=self.bg_panel)
        top_frame.pack(fill="x", padx=20, pady=(10, 10))
        
        for col in range(10):
            top_frame.grid_columnconfigure(col, weight=1)
        
        Label(top_frame, text="Товар:", bg=self.bg_panel, fg=self.fg_text,
              font=("Segoe UI", 11)).grid(row=0, column=1, padx=5, pady=10, sticky="e")
        self.op_product = ttk.Combobox(top_frame, state="readonly", width=50, font=("Segoe UI", 11), style="Small.TCombobox")
        self.op_product.grid(row=0, column=2, padx=5, pady=10, sticky="w")
        
        Label(top_frame, text="Тип:", bg=self.bg_panel, fg=self.fg_text,
              font=("Segoe UI", 11)).grid(row=0, column=3, padx=15, pady=15, sticky="e")
        self.op_type = ttk.Combobox(top_frame, values=["Приход", "Расход"], state="readonly", width=10, font=("Segoe UI", 11), style="Small.TCombobox")
        self.op_type.current(0)
        self.op_type.grid(row=0, column=4, padx=5, pady=10, sticky="w")
        
        Label(top_frame, text="Кол-во:", bg=self.bg_panel, fg=self.fg_text,
              font=("Segoe UI", 11)).grid(row=0, column=5, padx=15, pady=10, sticky="e")
        self.op_qty = ttk.Entry(top_frame, width=15, style="Qty.TEntry")
        self.op_qty.grid(row=0, column=6, padx=5, pady=10, sticky="w")
        
        Label(top_frame, text="Дата:", bg=self.bg_panel, fg=self.fg_text,
              font=("Segoe UI", 11)).grid(row=0, column=7, padx=15, pady=10, sticky="e")
        
        date_container = Frame(top_frame, bg=self.bg_input, highlightthickness=2, 
                              highlightcolor="#ffffff", highlightbackground="#ffffff")
        date_container.grid(row=0, column=8, padx=5, pady=10)
        
        self.op_date = ttk.Entry(date_container, width=14, font=("Segoe UI", 11), style="Custom.TEntry")
        self.op_date.pack(side="left", fill="both", expand=True, padx=(3, 0), pady=3)
        self.op_date.insert(0, datetime.now().strftime("%d.%m.%Y"))
        self.op_date.configure(state="readonly")
        
        self.cal_btn = Button(date_container, text="", 
                              bg=self.color_blue, fg="#ffffff", 
                              relief="solid",
                              borderwidth=2,
                              highlightthickness=2,
                              highlightcolor="#ffffff",
                              highlightbackground="#ffffff",
                              cursor="hand2", 
                              command=self._open_calendar,
                              compound="center", bd=0)
        
        cal_icon = self.icons.get("calendar")
        if cal_icon:
            self.cal_btn.config(image=cal_icon, width=-cal_icon.width(), height=-cal_icon.height())
        else:
            self.cal_btn.config(text="...", width=3, font=("Segoe UI", 11, "bold"))
        
        self.cal_btn.pack(side="right", padx=(0, 3), pady=3)
        
        btn_frame = Frame(top_frame, bg=self.bg_panel)
        btn_frame.grid(row=1, column=2, columnspan=6, pady=(10, 5))
        
        self.op_save_btn = self.make_icon_button(btn_frame, " Сохранить", "save", self.on_movement_save, self.color_blue, padx=15, pady=8)
        self.op_save_btn.pack(side="left", padx=150)
        
        self.op_cancel_btn = self.make_icon_button(btn_frame, " Отмена", "cancel", self.on_movement_cancel, self.color_cancel, self.fg_text, padx=15, pady=8)
        self.op_cancel_btn.pack(side="left", padx=97)
        
        self.op_status = Label(frame, text="", bg=self.bg_panel, fg=self.color_red, font=("Segoe UI", 10))
        self.op_status.pack(anchor="w", padx=20, pady=(0, 0))
        
        table_frame = Frame(frame, bg=self.bg_panel)
        table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        
        columns = ("product", "gtin", "type", "qty", "date")
        self.movements_tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        
        self.movements_tree.heading("product", text="Товар", anchor="center")
        self.movements_tree.heading("gtin", text="GTIN", anchor="center")
        self.movements_tree.heading("type", text="Тип", anchor="center")
        self.movements_tree.heading("qty", text="Кол-во", anchor="center")
        self.movements_tree.heading("date", text="Дата", anchor="center")
        
        self.movements_tree.column("product", width=450, anchor="w")
        self.movements_tree.column("gtin", width=200, anchor="center")
        self.movements_tree.column("type", width=120, anchor="center")
        self.movements_tree.column("qty", width=120, anchor="center")
        self.movements_tree.column("date", width=140, anchor="center")
        
        self.movements_tree.tag_configure('odd', background=self.bg_panel)
        self.movements_tree.tag_configure('even', background=self.bg_input)
        
        scroll_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.movements_tree.yview)
        self.movements_tree.configure(yscrollcommand=scroll_y.set)
        
        self.movements_tree.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")
        
        action_frame = Frame(frame, bg=self.bg_panel)
        action_frame.pack(fill="x", padx=20, pady=(10, 20))
        
        for col in range(4):
            action_frame.grid_columnconfigure(col, weight=1)
        
        btn_container = Frame(action_frame, bg=self.bg_panel)
        btn_container.grid(row=0, column=1, columnspan=2)
        
        self.make_icon_button(btn_container, " Изменить", "edit", self.on_movement_edit, self.color_yellow, self.fg_dark, padx=20, pady=8).pack(side="left", padx=30)
        self.make_icon_button(btn_container, " Удалить", "delete", self.on_movement_delete, self.color_red, padx=20, pady=8).pack(side="left", padx=35)

    def _open_calendar(self):
        import tkinter as tk
        from tkcalendar import Calendar
        
        def grab_date():
            self.op_date.configure(state="normal")
            self.op_date.delete(0, 'end')
            self.op_date.insert(0, cal.selection_get().strftime("%d.%m.%Y"))
            self.op_date.configure(state="readonly")
            top.destroy()
        
        top = tk.Toplevel(self.root)
        top.title("Выберите дату")
        top.geometry("300x250+700+300")
        top.configure(bg=self.bg_panel)
        
        cal = Calendar(top, selectmode='day', date_pattern='dd.mm.yyyy',
                       background=self.bg_input, foreground="#ffffff",
                       headersbackground=self.bg_input, headersforeground="#ffd700")
        cal.pack(fill="both", expand=True, padx=10, pady=10)
        
        btn = Button(top, text="Выбрать", command=grab_date,
                     bg=self.color_blue, fg="#ffffff", font=("Segoe UI", 10, "bold"), 
                     relief="solid", borderwidth=2,
                     highlightthickness=2,
                     highlightcolor="#ffffff",
                     highlightbackground="#ffffff")
        btn.pack(pady=5)

    def refresh_dropdowns(self):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM products ORDER BY name")
        rows = cur.fetchall()
        conn.close()
        
        names = [row["name"] for row in rows]
        self.products_by_name = {row["name"]: row["id"] for row in rows}
        self.op_product["values"] = names
        
        if self.op_product.get() not in names:
            self.op_product.set("")

    def on_movement_save(self):
        product_name = self.op_product.get()
        op_type = self.op_type.get()
        qty_str = self.op_qty.get().strip()
        
        try:
            date_obj = datetime.strptime(self.op_date.get(), "%d.%m.%Y")
            date_str = date_obj.strftime("%Y-%m-%d")
        except ValueError:
            self.op_status.config(text="❌ Неверный формат даты (дд.мм.гггг)", fg=self.color_red)
            return
        
        if not product_name:
            self.op_status.config(text="❌ Выберите товар", fg=self.color_red)
            return
        
        if not qty_str:
            self.op_status.config(text="❌ Введите количество", fg=self.color_red)
            return
        
        try:
            qty = float(qty_str.replace(",", "."))
            if qty <= 0:
                self.op_status.config(text="❌ Количество > 0", fg=self.color_red)
                return
        except:
            self.op_status.config(text="❌ Неверное количество", fg=self.color_red)
            return
        
        product_id = self.products_by_name.get(product_name)
        if not product_id:
            self.op_status.config(text="❌ Товар не найден", fg=self.color_red)
            return
        
        mtype = "in" if op_type == "Приход" else "out"
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        try:
            if self.editing_movement_id:
                cur.execute("""
                    UPDATE movements SET product_id=?, mtype=?, qty=?, date=?
                    WHERE id=?
                """, (product_id, mtype, qty, date_str, self.editing_movement_id))
                self.op_status.config(text="✅ Операция обновлена", fg=self.color_green)
                self.editing_movement_id = None
            else:
                cur.execute("""
                    INSERT INTO movements (product_id, mtype, qty, date)
                    VALUES (?, ?, ?, ?)
                """, (product_id, mtype, qty, date_str))
                self.op_status.config(text="✅ Операция сохранена", fg=self.color_green)
            
            conn.commit()
            self.on_movement_cancel()
            self.update_movements_table()
            self.update_balances_table()
            self.refresh_dropdowns()
            self.update_hashes()
            
        except Exception as e:
            conn.rollback()
            self.op_status.config(text=f"❌ Ошибка: {e}", fg=self.color_red)
        finally:
            conn.close()

    def on_movement_cancel(self):
        self.editing_movement_id = None
        self.op_product.set("")
        self.op_type.current(0)
        self.op_qty.delete(0, "end")
        self.op_save_btn.config(text=" Сохранить")
        self.op_status.config(text="")
        
        self.op_date.configure(state="normal")
        self.op_date.delete(0, "end")
        self.op_date.insert(0, datetime.now().strftime("%d.%m.%Y"))
        self.op_date.configure(state="readonly")
        
        self.update_movements_table()

    def on_movement_edit(self):
        sel = self.movements_tree.selection()
        if not sel:
            messagebox.showwarning("Внимание", "Выберите операцию")
            return
        
        mid = int(sel[0])
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM movements WHERE id=?", (mid,))
        row = cur.fetchone()
        conn.close()
        
        if row:
            product_name = None
            for name, pid in self.products_by_name.items():
                if pid == row["product_id"]:
                    product_name = name
                    break
            
            if not product_name:
                self.op_status.config(text="❌ Товар не найден", fg=self.color_red)
                return
            
            self.editing_movement_id = mid
            self.op_product.set(product_name)
            self.op_type.current(0 if row["mtype"] == "in" else 1)
            self.op_qty.delete(0, "end")
            self.op_qty.insert(0, self.fmt_qty_clean(row["qty"]))
            
            try:
                dt = datetime.strptime(row["date"], "%Y-%m-%d")
                self.op_date.configure(state="normal")
                self.op_date.delete(0, "end")
                self.op_date.insert(0, dt.strftime("%d.%m.%Y"))
                self.op_date.configure(state="readonly")
            except:
                pass
            
            self.op_save_btn.config(text=" Обновить")
            self.op_status.config(text="Режим редактирования", fg=self.color_yellow)

    def on_movement_delete(self):
        sel = self.movements_tree.selection()
        if not sel:
            messagebox.showwarning("Внимание", "Выберите операцию")
            return
        
        if messagebox.askyesno("Подтверждение", "Удалить операцию?"):
            mid = int(sel[0])
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM movements WHERE id=?", (mid,))
            conn.commit()
            conn.close()
            
            self.update_movements_table()
            self.update_balances_table()
            self.op_status.config(text="✅ Операция удалена", fg=self.color_green)
            self.update_hashes()

    def update_movements_table(self):
        for item in self.movements_tree.get_children():
            self.movements_tree.delete(item)
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT m.id, m.date, m.qty, m.mtype, p.name, p.gtin
            FROM movements m
            JOIN products p ON m.product_id = p.id
            ORDER BY m.date DESC, m.id DESC
        """)
        rows = cur.fetchall()
        conn.close()
        
        for idx, row in enumerate(rows):
            type_text = "Приход" if row["mtype"] == "in" else "Расход"
            tag = 'even' if idx % 2 == 0 else 'odd'
            self.movements_tree.insert("", "end", 
                values=(row["name"], row["gtin"] or "", type_text, 
                       str(self.fmt_qty_clean(row["qty"])), fmt_date(row["date"])),
                iid=str(row["id"]), tags=(tag,))

    # -------------------------------------------------------------------------
    # ОСТАТКИ
    # -------------------------------------------------------------------------
    def _build_balances_tab(self):
        frame = self.tab_balances
        
        info_frame = Frame(frame, bg=self.bg_panel)
        info_frame.pack(fill="x", padx=20, pady=18)
        
        info_frame.grid_columnconfigure(0, weight=1)
        info_frame.grid_columnconfigure(1, weight=1)
        
        Label(info_frame, text="Остатки товаров на складе", bg=self.bg_panel, fg=self.fg_text,
              font=("Segoe UI", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=4)
        Label(info_frame, text="Только товары с проведёнными операциями", bg=self.bg_panel, fg=self.fg_light,
              font=("Segoe UI", 11)).grid(row=1, column=0, columnspan=2, pady=2)
        
        table_frame = Frame(frame, bg=self.bg_panel)
        table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        
        columns = ("product", "gtin", "income", "outcome", "balance", "last_in", "last_out")
        self.balances_tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        
        self.balances_tree.heading("product", text="Товар", anchor="center")
        self.balances_tree.heading("gtin", text="GTIN", anchor="center")
        self.balances_tree.heading("income", text="Приход", anchor="center")
        self.balances_tree.heading("outcome", text="Расход", anchor="center")
        self.balances_tree.heading("balance", text="Остаток", anchor="center")
        self.balances_tree.heading("last_in", text="Посл. приход", anchor="center")
        self.balances_tree.heading("last_out", text="Посл. расход", anchor="center")
        
        self.balances_tree.column("product", width=300, anchor="w")
        self.balances_tree.column("gtin", width=150, anchor="center")
        self.balances_tree.column("income", width=80, anchor="center")
        self.balances_tree.column("outcome", width=80, anchor="center")
        self.balances_tree.column("balance", width=80, anchor="center")
        self.balances_tree.column("last_in", width=120, anchor="center")
        self.balances_tree.column("last_out", width=120, anchor="center")
        
        self.balances_tree.tag_configure('odd', background=self.bg_panel)
        self.balances_tree.tag_configure('even', background=self.bg_input)
        self.balances_tree.tag_configure('positive', foreground=self.color_yellow)
        self.balances_tree.tag_configure('negative', foreground=self.color_red)
        self.balances_tree.tag_configure('zero', foreground=self.fg_light)
        
        scroll_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.balances_tree.yview)
        self.balances_tree.configure(yscrollcommand=scroll_y.set)
        
        self.balances_tree.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")
        
        self.balances_tree.bind("<ButtonRelease-1>", self.show_product_operations)

    def update_balances_table(self):
        for item in self.balances_tree.get_children():
            self.balances_tree.delete(item)
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                p.id,
                p.name,
                p.gtin,
                COALESCE(SUM(CASE WHEN m.mtype='in' THEN m.qty ELSE 0 END), 0) AS total_in,
                COALESCE(SUM(CASE WHEN m.mtype='out' THEN m.qty ELSE 0 END), 0) AS total_out,
                COALESCE(SUM(CASE WHEN m.mtype='in' THEN m.qty ELSE -m.qty END), 0) AS balance,
                MAX(CASE WHEN m.mtype='in' THEN m.date END) AS last_in,
                MAX(CASE WHEN m.mtype='out' THEN m.date END) AS last_out
            FROM products p
            LEFT JOIN movements m ON p.id = m.product_id
            GROUP BY p.id, p.name, p.gtin
            HAVING total_in > 0 OR total_out > 0
            ORDER BY p.sort_order, p.name
        """)
        rows = cur.fetchall()
        conn.close()
        
        for idx, row in enumerate(rows):
            tag = 'even' if idx % 2 == 0 else 'odd'
            
            balance = row["balance"]
            if balance > 0:
                balance_tag = 'positive'
            elif balance < 0:
                balance_tag = 'negative'
            else:
                balance_tag = 'zero'
            
            self.balances_tree.insert("", "end",
                iid=str(row["id"]),
                values=(row["name"], 
                       row["gtin"] or "-",
                       str(self.fmt_qty_clean(row["total_in"])),
                       str(self.fmt_qty_clean(row["total_out"])),
                       str(self.fmt_qty_clean(balance)),
                       fmt_date(row["last_in"]),
                       fmt_date(row["last_out"])),
                tags=(tag, balance_tag))

    # -------------------------------------------------------------------------
    # МЕТОД ДЛЯ ПЕРЕХОДА К ОПЕРАЦИЯМ ТОВАРА
    # -------------------------------------------------------------------------
    def show_product_operations(self, event):
        """При клике на товар в таблице остатков переключает на вкладку Операции и фильтрует по товару"""
        selection = self.balances_tree.selection()
        if not selection:
            return
        
        product_id = int(selection[0])
        
        self.notebook.select(self.tab_movements)
        
        for item in self.movements_tree.get_children():
            self.movements_tree.delete(item)
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT m.id, m.date, m.qty, m.mtype, p.name, p.gtin
            FROM movements m
            JOIN products p ON m.product_id = p.id
            WHERE m.product_id = ?
            ORDER BY m.date DESC, m.id DESC
        """, (product_id,))
        rows = cur.fetchall()
        conn.close()
        
        for idx, row in enumerate(rows):
            type_text = "Приход" if row["mtype"] == "in" else "Расход"
            tag = 'even' if idx % 2 == 0 else 'odd'
            self.movements_tree.insert("", "end", 
                values=(row["name"], row["gtin"] or "", type_text, 
                       str(self.fmt_qty_clean(row["qty"])), fmt_date(row["date"])),
                iid=str(row["id"]), tags=(tag,))
        
        self.op_status.config(text=f"Показаны операции по выбранному товару. Нажмите «Отмена», чтобы сбросить фильтр.", fg=self.color_yellow)

if __name__ == "__main__":
    init_db()
    root = Tk()
    app = InventoryApp(root)
    root.mainloop()