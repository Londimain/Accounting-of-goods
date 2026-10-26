import tkinter as tk
from tkinter import Button, messagebox, Frame, Label
import tkinter.ttk as ttk


class WidgetHelpersMixin:
    def make_icon_button(self, parent, text, icon_key, command=None,
                         bg="#4a90d9", fg="#000000", padx=20, pady=6):
        btn = Button(parent, text=text, command=command,
                    bg=bg, fg=fg,
                    disabledforeground=fg,
                    font=("Segoe UI", 10, "bold"),
                    padx=padx, pady=pady,
                    relief="solid",
                    borderwidth=1,
                    highlightthickness=2,
                    highlightcolor="#000000",
                    highlightbackground="#000000",
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

    def make_button(self, parent, text, command=None,
                    bg="#4a90d9", fg="#000000", padx=20, pady=6):
        btn = Button(parent, text=text, command=command,
                    bg=bg, fg=fg,
                    disabledforeground=fg,
                    font=("Segoe UI", 10, "bold"),
                    padx=padx, pady=pady,
                    relief="solid",
                    borderwidth=1,
                    highlightthickness=2,
                    highlightcolor="#000000",
                    highlightbackground="#000000",
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
        mapping = {
            "#4a90d9": "#5ba0e9",
            "#5cb85c": "#6cc86c",
            "#d9534f": "#e9635f",
            "#f0ad4e": "#f0bd5e",
            "#f39c12": "#f4ac22",
            "#24292e": "#3f464d",
        }
        return mapping.get(color, color)

    # --- ИСПРАВЛЕНО: надежное копирование/вставка ---
    def bind_copy_paste(self, widget):
        def _copy(event):
            try:
                widget.clipboard_clear()
                widget.clipboard_append(widget.selection_get())
            except tk.TclError:
                pass
            return "break"

        def _paste(event):
            try:
                text = widget.clipboard_get()
                try:
                    widget.delete("sel.first", "sel.last")
                except tk.TclError:
                    pass
                widget.insert("insert", text)
            except tk.TclError:
                pass
            return "break"

        def _cut(event):
            try:
                widget.clipboard_clear()
                widget.clipboard_append(widget.selection_get())
                widget.delete("sel.first", "sel.last")
            except tk.TclError:
                pass
            return "break"

        def _select_all(event):
            widget.select_range(0, "end")
            widget.icursor("end")
            return "break"

        widget.bind("<Control-c>", _copy)
        widget.bind("<Control-C>", _copy)
        widget.bind("<Control-v>", _paste)
        widget.bind("<Control-V>", _paste)
        widget.bind("<Control-x>", _cut)
        widget.bind("<Control-X>", _cut)
        widget.bind("<Control-a>", _select_all)
        widget.bind("<Control-A>", _select_all)

    # --- ИСПРАВЛЕНО: увеличены кнопки и окно ---
    def ask_admin_password(self, action="удаление"):
        top = tk.Toplevel(self.root)
        top.title("Подтверждение действий")
        top.configure(bg=self.bg_panel)
        top.transient(self.root)
        top.grab_set()
        top.resizable(False, False)

        # Центрируем окно относительно главного окна программы
        self.root.update_idletasks()
        w, h = 420, 190  # Увеличен размер окна
        x = self.root.winfo_rootx() + (self.root.winfo_width() - w) // 2
        y = self.root.winfo_rooty() + (self.root.winfo_height() - h) // 2
        top.geometry(f"{w}x{h}+{x}+{y}")

        Label(top, text=f"Для {action} требуется\nпароль администратора:",
              bg=self.bg_panel, fg=self.fg_text,
              font=("Segoe UI", 11)).pack(pady=(20, 10))

        pwd_var = tk.StringVar()
        entry = ttk.Entry(top, textvariable=pwd_var, show="*", style="Custom.TEntry")
        entry.pack(padx=40, pady=5, fill="x")
        entry.focus_set()

        result = [False]

        def on_ok(event=None):
            if pwd_var.get() == "admins":
                result[0] = True
                top.destroy()
            else:
                messagebox.showerror("Доступ запрещён", "Неверный пароль", parent=top)
                entry.delete(0, "end")
                entry.focus_set()

        def on_cancel(event=None):
            top.destroy()

        btn_frame = Frame(top, bg=self.bg_panel)
        btn_frame.pack(pady=20)

        # Увеличены отступы (padx/pady) и шрифт
        tk.Button(btn_frame, text="OK", command=on_ok, bg=self.color_blue, fg=self.fg_dark,
                  font=("Segoe UI", 11, "bold"), relief="solid", borderwidth=1,
                  highlightthickness=2, highlightcolor="#000000", highlightbackground="#000000",
                  cursor="hand2", padx=40, pady=8).pack(side="left", padx=15)
                  
        tk.Button(btn_frame, text="Отмена", command=on_cancel, bg=self.color_cancel, fg=self.fg_dark,
                  font=("Segoe UI", 11, "bold"), relief="solid", borderwidth=1,
                  highlightthickness=2, highlightcolor="#000000", highlightbackground="#000000",
                  cursor="hand2", padx=30, pady=8).pack(side="left", padx=15)

        entry.bind("<Return>", on_ok)
        top.bind("<Escape>", on_cancel)

        self.root.wait_window(top)
        return result[0]