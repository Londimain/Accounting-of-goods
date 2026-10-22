from datetime import datetime
from tkinter import Frame, Label, Button, messagebox
import tkinter as tk
import tkinter.ttk as ttk

from .db import get_db_connection
from .utils import fmt_date, fmt_qty_clean


class MovementsTabMixin:

    def _build_movements_tab(self):
        frame = self.tab_movements

        top_frame = Frame(frame, bg=self.bg_panel)
        top_frame.pack(fill="x", padx=20, pady=(10, 10))

        for col in range(10):
            top_frame.grid_columnconfigure(col, weight=1)

        Label(top_frame, text="Товар:", bg=self.bg_panel, fg=self.fg_text,
              font=("Segoe UI", 11)).grid(row=0, column=1, padx=5, pady=10, sticky="e")
        self.op_product = ttk.Combobox(
            top_frame, state="readonly", width=50,
            font=("Segoe UI", 11), style="Small.TCombobox")
        self.op_product.grid(row=0, column=2, padx=5, pady=10, sticky="w")

        Label(top_frame, text="Тип:", bg=self.bg_panel, fg=self.fg_text,
              font=("Segoe UI", 11)).grid(row=0, column=3, padx=15, pady=15, sticky="e")
        self.op_type = ttk.Combobox(
            top_frame, values=["Приход", "Расход"], state="readonly", width=10,
            font=("Segoe UI", 11), style="Small.TCombobox")
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

        self.op_date = ttk.Entry(date_container, width=14,
                                 font=("Segoe UI", 11), style="Custom.TEntry")
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
            self.cal_btn.config(image=cal_icon,
                                width=-cal_icon.width(),
                                height=-cal_icon.height())
        else:
            self.cal_btn.config(text="...", width=3, font=("Segoe UI", 11, "bold"))

        self.cal_btn.pack(side="right", padx=(0, 3), pady=3)

        btn_frame = Frame(top_frame, bg=self.bg_panel)
        btn_frame.grid(row=1, column=2, columnspan=6, pady=(10, 5))

        self.op_save_btn = self.make_icon_button(
            btn_frame, " Сохранить", "save", self.on_movement_save,
            self.color_blue, padx=15, pady=8)
        self.op_save_btn.pack(side="left", padx=150)

        self.op_cancel_btn = self.make_icon_button(
            btn_frame, " Отмена", "cancel", self.on_movement_cancel,
            self.color_cancel, fg=self.fg_dark, padx=15, pady=8) # <-- ИЗМЕНЕНО fg
        self.op_cancel_btn.pack(side="left", padx=97)

        self.op_status = Label(frame, text="", bg=self.bg_panel,
                               fg=self.color_red, font=("Segoe UI", 10))
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

        scroll_y = ttk.Scrollbar(table_frame, orient="vertical",
                                 command=self.movements_tree.yview)
        self.movements_tree.configure(yscrollcommand=scroll_y.set)

        self.movements_tree.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")

        action_frame = Frame(frame, bg=self.bg_panel)
        action_frame.pack(fill="x", padx=20, pady=(10, 20))

        for col in range(4):
            action_frame.grid_columnconfigure(col, weight=1)

        btn_container = Frame(action_frame, bg=self.bg_panel)
        btn_container.grid(row=0, column=1, columnspan=2)

        self.make_icon_button(btn_container, " Изменить", "edit",
                              self.on_movement_edit,
                              self.color_yellow, self.fg_dark,
                              padx=20, pady=8).pack(side="left", padx=30)
        self.make_icon_button(btn_container, " Удалить", "delete",
                              self.on_movement_delete,
                              self.color_red, padx=20, pady=8).pack(
            side="left", padx=35)

    def _open_calendar(self):
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
                       headersbackground=self.bg_input,
                       headersforeground="#ffd700")
        cal.pack(fill="both", expand=True, padx=10, pady=10)

        Button(top, text="Выбрать", command=grab_date,
               bg=self.color_blue, fg="#000000", # <-- ИЗМЕНЕНО fg
               font=("Segoe UI", 10, "bold"),
               relief="solid", borderwidth=2,
               highlightthickness=2,
               highlightcolor="#ffffff",
               highlightbackground="#ffffff").pack(pady=5)

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
            self.op_status.config(text="❌ Неверный формат даты (дд.мм.гггг)",
                                  fg=self.color_red)
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
        except Exception:
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
            was_editing = self.editing_movement_id is not None
            if was_editing:
                cur.execute("""
                    UPDATE movements SET product_id=?, mtype=?, qty=?, date=?
                    WHERE id=?
                """, (product_id, mtype, qty, date_str, self.editing_movement_id))
            else:
                cur.execute("""
                    INSERT INTO movements (product_id, mtype, qty, date)
                    VALUES (?, ?, ?, ?)
                """, (product_id, mtype, qty, date_str))

            conn.commit()

            msg = ("✅ Операция обновлена" if was_editing
                   else "✅ Операция сохранена")
            # ВАЖНО: сначала сброс формы (очистит статус), потом сообщение.
            self.on_movement_cancel()
            self.op_status.config(text=msg, fg=self.color_green)

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
            self.op_qty.insert(0, fmt_qty_clean(row["qty"]))

            try:
                dt = datetime.strptime(row["date"], "%Y-%m-%d")
                self.op_date.configure(state="normal")
                self.op_date.delete(0, "end")
                self.op_date.insert(0, dt.strftime("%d.%m.%Y"))
                self.op_date.configure(state="readonly")
            except Exception:
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
            self.movements_tree.insert(
                "", "end",
                values=(row["name"], row["gtin"] or "", type_text,
                       fmt_qty_clean(row["qty"]), fmt_date(row["date"])),
                iid=str(row["id"]), tags=(tag,))