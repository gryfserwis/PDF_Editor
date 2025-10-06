"""
Moduł custom_dialogs.py - Niestandardowe okna dialogowe.

Zawiera funkcje do wyświetlania niestandardowych okien dialogowych
wyśrodkowanych na oknie aplikacji.
"""

import tkinter as tk
from tkinter import ttk


def custom_messagebox(parent, title, message, typ="info"):
    """Wyświetla niestandardowe okno dialogowe wyśrodkowane na oknie aplikacji.
    
    Args:
        parent: Okno nadrzędne
        title: Tytuł okna
        message: Treść komunikatu
        typ: Typ dialogu ('info', 'error', 'warning', 'question', 'yesnocancel')
        
    Returns:
        bool lub None: 
            - dla 'question': True (Tak) lub False (Nie)
            - dla 'yesnocancel': True (Tak), False (Nie) lub None (Anuluj)
            - dla innych: None
    """
    dialog = tk.Toplevel(parent)
    dialog.title(title)
    dialog.transient(parent)
    dialog.grab_set()
    dialog.resizable(False, False)
    
    colors = {
        "info": "#d1ecf1",
        "error": "#f8d7da",
        "warning": "#fff3cd",
        "question": "#d1ecf1",
        "yesnocancel": "#d1ecf1"
    }
    bg_color = colors.get(typ, "#f0f0f0")
    
    main_frame = ttk.Frame(dialog, padding="12")
    main_frame.pack(fill="both", expand=True)
    content_frame = ttk.Frame(main_frame)
    content_frame.pack(fill="both", expand=True, pady=(0, 12))
    
    msg_label = tk.Label(content_frame, text=message, justify="left", 
                        wraplength=310, font=("Arial", 10))
    msg_label.pack(fill="both", expand=True, pady=6)
    
    result = [None]
    
    def on_yes():
        result[0] = True
        dialog.destroy()
    
    def on_no():
        result[0] = False
        dialog.destroy()
    
    def on_cancel():
        result[0] = None
        dialog.destroy()
    
    def on_ok():
        dialog.destroy()
    
    button_frame = ttk.Frame(main_frame)
    button_frame.pack()
    
    if typ == "question":
        yes_btn = ttk.Button(button_frame, text="Tak", command=on_yes, width=10)
        yes_btn.pack(side="left", padx=4)
        no_btn = ttk.Button(button_frame, text="Nie", command=on_no, width=10)
        no_btn.pack(side="left", padx=4)
        dialog.bind("<Return>", lambda e: on_yes())
        dialog.bind("<Escape>", lambda e: on_no())
        yes_btn.focus_set()
    elif typ == "yesnocancel":
        yes_btn = ttk.Button(button_frame, text="Tak", command=on_yes, width=10)
        yes_btn.pack(side="left", padx=4)
        no_btn = ttk.Button(button_frame, text="Nie", command=on_no, width=10)
        no_btn.pack(side="left", padx=4)
        cancel_btn = ttk.Button(button_frame, text="Anuluj", command=on_cancel, width=10)
        cancel_btn.pack(side="left", padx=4)
        dialog.bind("<Return>", lambda e: on_yes())
        dialog.bind("<Escape>", lambda e: on_cancel())
        dialog.protocol("WM_DELETE_WINDOW", on_cancel)
        yes_btn.focus_set()
    else:
        ok_btn = ttk.Button(button_frame, text="OK", command=on_ok, width=10)
        ok_btn.pack(padx=4)
        dialog.bind("<Return>", lambda e: on_ok())
        dialog.bind("<Escape>", lambda e: on_ok())
        ok_btn.focus_set()
    
    # Wyśrodkuj na rodzicu
    dialog.update_idletasks()
    dialog_w = dialog.winfo_width()
    dialog_h = dialog.winfo_height()
    parent_x = parent.winfo_rootx()
    parent_y = parent.winfo_rooty()
    parent_w = parent.winfo_width()
    parent_h = parent.winfo_height()
    x = parent_x + (parent_w - dialog_w) // 2
    y = parent_y + (parent_h - dialog_h) // 2
    dialog.geometry(f"+{x}+{y}")
    dialog.wait_window()
    return result[0]
