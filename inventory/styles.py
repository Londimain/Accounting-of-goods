import tkinter.ttk as ttk


def apply_styles(*, bg_panel, bg_input, fg_text, fg_dark, color_blue, color_header):
    style = ttk.Style()
    style.theme_use('clam')

    style.configure("Treeview",
        rowheight=30,
        background=bg_panel,
        foreground=fg_text,
        fieldbackground=bg_panel,
        font=("Segoe UI", 10),
        borderwidth=1,
        relief="solid",
        bordercolor="#1A2519",
        lightcolor="#1A2519",
        darkcolor="#1A2519")

    style.configure("Treeview.Heading",
        background=color_header,
        foreground=fg_text,
        font=("Segoe UI", 10, "bold"),
        borderwidth=1,
        relief="solid",
        bordercolor="#923D3D",
        lightcolor="#923D3D",
        darkcolor="#923D3D")

    style.map("Treeview.Heading",
        background=[("active", color_header)])
    style.map("Treeview",
        background=[("selected", color_blue)],
        foreground=[("selected", fg_dark)])

    style.configure("TNotebook", tabmargins=[0, 0, 0, 0], borderwidth=0)
    style.configure("TNotebook.Tab", padding=[0, 0, 0, 0], borderwidth=0, focuscolor="none")
    style.layout("TNotebook.Tab", [])

    style.configure("Custom.TEntry",
        fieldbackground=bg_input,
        background=bg_input,
        foreground=fg_text,
        insertcolor=fg_text,
        bordercolor="#ffffff",
        lightcolor="#ffffff",
        darkcolor="#ffffff",
        borderwidth=2,
        relief="solid",
        padding=(8, 6))
    style.map("Custom.TEntry",
        fieldbackground=[("readonly", bg_input)],
        foreground=[("readonly", fg_text)],
        insertcolor=[("readonly", fg_text)],
        bordercolor=[("focus", "#ffffff")],
        lightcolor=[("focus", "#ffffff")],
        darkcolor=[("focus", "#ffffff")])

    style.configure("Qty.TEntry",
        fieldbackground=bg_input,
        background=bg_input,
        foreground=fg_text,
        insertcolor=fg_text,
        bordercolor="#ffffff",
        lightcolor="#ffffff",
        darkcolor="#ffffff",
        borderwidth=2,
        relief="solid",
        padding=(8, 6),
        font=("Segoe UI", 13))
    style.map("Qty.TEntry",
        fieldbackground=[("readonly", bg_input)],
        foreground=[("readonly", fg_text)],
        insertcolor=[("readonly", fg_text)],
        bordercolor=[("focus", "#ffffff")],
        lightcolor=[("focus", "#ffffff")],
        darkcolor=[("focus", "#ffffff")])

    style.configure("Custom.TCombobox",
        fieldbackground=bg_input,
        background=bg_input,
        foreground=fg_text,
        arrowcolor=fg_text,
        borderwidth=2,
        relief="solid",
        bordercolor="#ffffff",
        padding=(8, 6))
    style.map("Custom.TCombobox",
        fieldbackground=[("readonly", bg_input)],
        foreground=[("readonly", fg_text)],
        bordercolor=[("focus", "#ffffff")])

    style.configure("Small.TCombobox",
        fieldbackground=bg_input,
        background=bg_input,
        foreground=fg_text,
        arrowcolor=fg_text,
        borderwidth=2,
        relief="solid",
        bordercolor="#ffffff")
    style.map("Small.TCombobox",
        fieldbackground=[("readonly", bg_input)],
        foreground=[("readonly", fg_text)],
        bordercolor=[("focus", "#ffffff")])