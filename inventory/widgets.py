from tkinter import Button


class WidgetHelpersMixin:
    def make_icon_button(self, parent, text, icon_key, command=None,
                         bg="#4a90d9", fg="#000000", padx=20, pady=6): # <-- ИЗМЕНЕНО fg
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
                    bg="#4a90d9", fg="#000000", padx=20, pady=6): # <-- ИЗМЕНЕНО fg
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