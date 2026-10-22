import sqlite3
from tkinter import Frame, Label, messagebox
import tkinter.ttk as ttk

from .db import get_db_connection


class ProductsTabMixin:

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

        self.pm_add_btn = self.make_icon_button(
            btn_frame, " Добавить", "add", self.on_product_add, self.color_blue,
            padx=15, pady=8)
        self.pm_add_btn.pack(side="left", padx=50)

        self.pm_cancel_btn = self.make_icon_button(
            btn_frame, " Отмена", "cancel", self.on_product_cancel,
            self.color_cancel, fg=self.fg_dark, padx=15, pady=8) # <-- ИЗМЕНЕНО fg
        self.pm_cancel_btn.pack(side="left", padx=0)
        self.pm_cancel_btn.config(state="disabled")

        self.pm_status = Label(frame, text="", bg=self.bg_panel,
                               fg=self.color_red, font=("Segoe UI", 10))
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

        scroll_y = ttk.Scrollbar(table_frame, orient="vertical",
                                 command=self.products_tree.yview)
        self.products_tree.configure(yscrollcommand=scroll_y.set)

        self.products_tree.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")

        action_frame = Frame(frame, bg=self.bg_panel)
        action_frame.pack(fill="x", padx=20, pady=(10, 20))

        for col in range(4):
            action_frame.grid_columnconfigure(col, weight=1)

        btn_container = Frame(action_frame, bg=self.bg_panel)
        btn_container.grid(row=0, column=1, columnspan=2)

        self.make_icon_button(btn_container, " Вверх", "up",
                              lambda: self.on_move_product("up"),
                              self.color_blue, padx=15, pady=8).pack(
            side="left", padx=(5, 20))
        self.make_icon_button(btn_container, " Вниз", "down",
                              lambda: self.on_move_product("down"),
                              self.color_blue, padx=15, pady=8).pack(
            side="left", padx=(5, 80))

        self.make_icon_button(btn_container, " Изменить", "edit",
                              self.on_product_edit,
                              self.color_yellow, self.fg_dark,
                              padx=15, pady=8).pack(side="left", padx=(80, 25))
        self.make_icon_button(btn_container, " Удалить", "delete",
                              self.on_product_delete,
                              self.color_red, padx=15, pady=8).pack(
            side="left", padx=(5, 5))

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
            self.products_tree.insert(
                "", "end",
                values=(row["name"], row["gtin"] or ""),
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
            was_editing = self.editing_product_id is not None
            if was_editing:
                cur.execute(
                    "UPDATE products SET name=?, gtin=? WHERE id=?",
                    (name, gtin, self.editing_product_id))
            else:
                cur.execute("SELECT COALESCE(MAX(sort_order), 0) + 1 FROM products")
                next_order = cur.fetchone()[0]
                cur.execute(
                    "INSERT INTO products (name, gtin, sort_order) VALUES (?, ?, ?)",
                    (name, gtin, next_order))

            conn.commit()

            msg = "✅ Товар обновлён" if was_editing else "✅ Товар добавлен"
            # ВАЖНО: сначала сбрасываем форму (это очистит статус),
            # затем ставим сообщение об успехе.
            self.on_product_cancel()
            self.pm_status.config(text=msg, fg=self.color_green)

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
            cur.execute(
                "SELECT id, sort_order FROM products WHERE sort_order < ? "
                "ORDER BY sort_order DESC LIMIT 1", (current_order,))
        else:
            cur.execute(
                "SELECT id, sort_order FROM products WHERE sort_order > ? "
                "ORDER BY sort_order ASC LIMIT 1", (current_order,))

        other = cur.fetchone()
        if not other:
            conn.close()
            return

        cur.execute("UPDATE products SET sort_order = ? WHERE id = ?",
                    (other["sort_order"], pid))
        cur.execute("UPDATE products SET sort_order = ? WHERE id = ?",
                    (current_order, other["id"]))
        conn.commit()
        conn.close()

        self.update_products_table()
        self.update_balances_table()
        self.refresh_dropdowns()
        self.update_hashes()