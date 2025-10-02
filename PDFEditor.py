import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import fitz
from PIL import Image, ImageTk
import io
import math 
import os
import sys 
import re 
from typing import Optional, List, Set, Dict, Union
from datetime import date 
import pypdf
from pypdf import PdfReader, PdfWriter, Transformation
from pypdf.generic import RectangleObject, FloatObject, ArrayObject
# ArrayObject jest nadal potrzebne, jeśli użyjesz add_transformation, choć FloatObject 
# wystarczyłoby, jeśli pypdf je konwertuje. Zostawiam dla pełnej kompatybilności.
from pypdf.generic import NameObject # Dodaj import dla NameObject

# Definicja BASE_DIR i inne stałe
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ICON_FOLDER = os.path.join(BASE_DIR, "icons")
FOCUS_HIGHLIGHT_COLOR = "#000000" # Czarny (Black)
FOCUS_HIGHLIGHT_WIDTH = 2        # Szerokość ramki fokusu (stała)

# DANE PROGRAMU
PROGRAM_TITLE = "GRYF PDF Editor" 
PROGRAM_VERSION = "3.6.0"
PROGRAM_DATE = date.today().strftime("%Y-%m-%d")

# === STAŁE DLA A4 (w punktach PDF i mm) ===
A4_WIDTH_POINTS = 595.276 
A4_HEIGHT_POINTS = 841.89
MM_TO_POINTS = 72 / 25.4 # ~2.8346

def mm2pt(mm):
    return float(mm) * MM_TO_POINTS


# === STAŁE KOLORY NARZĘDZIOWE (jeśli ich nie masz) ===
# Musisz zdefiniować te kolory, jeśli ich nie masz, dla przycisku importu
BG_IMPORT = "#F0AD4E" # np. Jakiś pomarańczowy dla importu
GRAY_FG = "#555555" # Jeśli używasz tego dla ikon

COPYRIGHT_INFO = (
    "Program stanowi wyłączną własność intelektualną Centrum Graficznego Gryf sp. z o.o.\n\n"
    "Wszelkie prawa zastrzeżone. Kopiowanie, modyfikowanie oraz rozpowszechnianie "
    "programu bez pisemnej zgody autora jest zabronione."
)

# === STAŁE KOLORYSTYKA DLA SPOJNOSCI ===
BG_PRIMARY = '#F0F0F0'  # Główne tło okien i dialogów
BG_SECONDARY = '#E0E0E0' # Tło paneli kontrolnych/przycisków
BG_BUTTON_DEFAULT = "#D0D0D0" # Domyślny kolor przycisków
FG_TEXT = "#444444" # Kolor tekstu na przyciskach

# === STAŁE DLA A4 (w punktach PDF) ===
A4_WIDTH_POINTS = 595.276 
A4_HEIGHT_POINTS = 841.89


def resource_path(relative_path):
    """
    Tworzy poprawną ścieżkę do zasobów (logo, ikony itp.).
    Działa w trybie deweloperskim i po spakowaniu PyInstallerem.
    """
    try:
        # Aplikacja spakowana (PyInstaller --onefile)
        base_path = sys._MEIPASS
    except AttributeError:
        # Tryb deweloperski (po prostu katalog skryptu)
        base_path = os.path.dirname(os.path.abspath(__file__))
        
    return os.path.join(base_path, relative_path)
  
import tkinter as tk
from tkinter import ttk, messagebox


class PageCropResizeDialog(tk.Toplevel):
    PAPER_FORMATS = {
        'A0': (841, 1189),
        'A1': (594, 841),
        'A2': (420, 594),
        'A3': (297, 420),
        'A4': (210, 297),
        'A5': (148, 210),
        'A6': (105, 148),
        'Niestandardowy': (0, 0)
    }

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Kadrowanie i zmiana rozmiaru stron")
        self.transient(parent)
        self.result = None

        self.crop_mode = tk.StringVar(value="nocrop")
        self.margin_top = tk.StringVar(value="10")
        self.margin_bottom = tk.StringVar(value="10")
        self.margin_left = tk.StringVar(value="10")
        self.margin_right = tk.StringVar(value="10")

        self.resize_mode = tk.StringVar(value="noresize")
        self.target_format = tk.StringVar(value="A4")
        self.custom_width = tk.StringVar(value="")
        self.custom_height = tk.StringVar(value="")
        self.position_mode = tk.StringVar(value="center")
        self.offset_x = tk.StringVar(value="0")
        self.offset_y = tk.StringVar(value="0")

        self.build_ui()
        self.update_field_states()
        self.center_dialog(parent)
        self.grab_set()
        self.focus_force()
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.resizable(False, False)

        # --- Obsługa Enter i Esc jak w innych dialogach ---
        self.bind("<Return>", lambda e: self.ok())
        self.bind("<KP_Enter>", lambda e: self.ok())
        self.bind("<Escape>", lambda e: self.cancel())

        self.wait_window(self)

    def build_ui(self):
        pad = {'padx': 8, 'pady': 4}
        pady_row1 = (0, 6)
        pady_row2 = (0, 0)

        # --- CROP SECTION ---
        crop_frame = ttk.LabelFrame(self, text="Przycinanie strony")
        crop_frame.pack(fill="x", padx=12, pady=(12, 4))

        crop_modes = [
            ("Nie przycinaj", "nocrop"),
            ("Przytnij obraz bez zmiany rozmiaru arkusza", "crop_only"),
            ("Przytnij obraz i dostosuj rozmiar arkusza", "crop_resize"),
        ]
        self.crop_radiobuttons = []
        for txt, val in crop_modes:
            rb = ttk.Radiobutton(crop_frame, text=txt, variable=self.crop_mode, value=val, command=self.update_field_states)
            rb.pack(anchor="w", **pad)
            self.crop_radiobuttons.append(rb)

        margin_frame = ttk.Frame(crop_frame)
        margin_frame.pack(fill="x", padx=12, pady=(4, 6))
        ttk.Label(margin_frame, text="Góra [mm]:").grid(row=0, column=0, sticky="w", padx=(0,6), pady=pady_row1)
        self.e_margin_top = ttk.Entry(margin_frame, textvariable=self.margin_top, width=6)
        self.e_margin_top.grid(row=0, column=1, sticky="w", padx=(0,16), pady=pady_row1)
        ttk.Label(margin_frame, text="Dół [mm]:").grid(row=0, column=2, sticky="w", padx=(0,6), pady=pady_row1)
        self.e_margin_bottom = ttk.Entry(margin_frame, textvariable=self.margin_bottom, width=6)
        self.e_margin_bottom.grid(row=0, column=3, sticky="w", padx=(0,0), pady=pady_row1)

        ttk.Label(margin_frame, text="Lewo [mm]:").grid(row=1, column=0, sticky="w", padx=(0,6), pady=pady_row2)
        self.e_margin_left = ttk.Entry(margin_frame, textvariable=self.margin_left, width=6)
        self.e_margin_left.grid(row=1, column=1, sticky="w", padx=(0,16), pady=pady_row2)
        ttk.Label(margin_frame, text="Prawo [mm]:").grid(row=1, column=2, sticky="w", padx=(0,6), pady=pady_row2)
        self.e_margin_right = ttk.Entry(margin_frame, textvariable=self.margin_right, width=6)
        self.e_margin_right.grid(row=1, column=3, sticky="w", padx=(0,0), pady=pady_row2)
        self.margin_entries = [self.e_margin_top, self.e_margin_bottom, self.e_margin_left, self.e_margin_right]

        # --- RESIZE SECTION ---
        resize_frame = ttk.LabelFrame(self, text="Zmiana rozmiaru arkusza")
        resize_frame.pack(fill="x", padx=12, pady=8)

        resize_modes = [
            ("Nie zmieniaj rozmiaru", "noresize"),
            ("Zmień rozmiar i skaluj obraz", "resize_scale"),
            ("Zmień rozmiar i nie skaluj obrazu", "resize_noscale"),
        ]
        self.resize_radiobuttons = []
        for txt, val in resize_modes:
            rb = ttk.Radiobutton(resize_frame, text=txt, variable=self.resize_mode, value=val, command=self.update_field_states)
            rb.pack(anchor="w", **pad)
            self.resize_radiobuttons.append(rb)

        format_frame = ttk.Frame(resize_frame)
        format_frame.pack(fill="x", padx=12, pady=(4, 0))
        ttk.Label(format_frame, text="Format:").grid(row=0, column=0, sticky="w")
        self.format_combo = ttk.Combobox(format_frame, textvariable=self.target_format, values=list(self.PAPER_FORMATS.keys()), state="readonly", width=16)
        self.format_combo.grid(row=0, column=1, sticky="w", padx=(0,12))
        self.format_combo.bind("<<ComboboxSelected>>", lambda e: self.update_field_states())

        self.custom_size_frame = ttk.Frame(format_frame)
        self.custom_size_frame.grid(row=1, column=0, columnspan=2, sticky="w", pady=(8,0))
        ttk.Label(self.custom_size_frame, text="Szerokość [mm]:").grid(row=0, column=0, sticky="w", padx=(0,6), pady=pady_row1)
        self.e_custom_width = ttk.Entry(self.custom_size_frame, textvariable=self.custom_width, width=8)
        self.e_custom_width.grid(row=0, column=1, sticky="w", padx=(0,12), pady=pady_row1)
        ttk.Label(self.custom_size_frame, text="Wysokość [mm]:").grid(row=0, column=2, sticky="w", padx=(0,6), pady=pady_row1)
        self.e_custom_height = ttk.Entry(self.custom_size_frame, textvariable=self.custom_height, width=8)
        self.e_custom_height.grid(row=0, column=3, sticky="w", padx=(0,0), pady=pady_row1)
        self.custom_entries = [self.e_custom_width, self.e_custom_height]

        # --- POSITION SECTION (osobna ramka) ---
        self.position_frame = ttk.LabelFrame(self, text="Położenie obrazu")
        self.position_frame.pack(fill="x", padx=12, pady=(8, 0))
        position_modes = [
            ("Wyśrodkuj", "center"),
            ("Niestandardowe położenie", "custom")
        ]
        self.position_radiobuttons = []
        for txt, val in position_modes:
            rb = ttk.Radiobutton(self.position_frame, text=txt, variable=self.position_mode, value=val, command=self.update_field_states)
            rb.pack(anchor="w", **pad)
            self.position_radiobuttons.append(rb)

        self.offset_frame = ttk.Frame(self.position_frame)
        self.offset_frame.pack(fill="x", padx=18, pady=(0,0))
        ttk.Label(self.offset_frame, text="Od lewej [mm]:").grid(row=0, column=0, sticky="w", padx=(0,6), pady=pady_row1)
        self.e_offset_x = ttk.Entry(self.offset_frame, textvariable=self.offset_x, width=8)
        self.e_offset_x.grid(row=0, column=1, sticky="w", padx=(0,16), pady=pady_row1)
        ttk.Label(self.offset_frame, text="Od dołu [mm]:").grid(row=0, column=2, sticky="w", padx=(0,6), pady=pady_row1)
        self.e_offset_y = ttk.Entry(self.offset_frame, textvariable=self.offset_y, width=8)
        self.e_offset_y.grid(row=0, column=3, sticky="w", padx=(0,0), pady=pady_row1)
        self.offset_entries = [self.e_offset_x, self.e_offset_y]

        # --- BUTTONS ---
        button_frame = ttk.Frame(self)
        button_frame.pack(fill="x", padx=12, pady=(12,10))
        ttk.Button(button_frame, text="Zastosuj", command=self.ok).pack(side="left", expand=True, padx=5)
        ttk.Button(button_frame, text="Anuluj", command=self.cancel).pack(side="right", expand=True, padx=5)

    def update_field_states(self):
        crop_selected = self.crop_mode.get() != "nocrop"
        resize_selected = self.resize_mode.get() != "noresize"

        # Ekskluzywność crop <-> resize
        for rb in self.resize_radiobuttons:
            rb["state"] = tk.DISABLED if crop_selected else tk.NORMAL
        for rb in self.crop_radiobuttons:
            rb["state"] = tk.DISABLED if resize_selected else tk.NORMAL

        # Pola crop (marginesy)
        enable_crop = self.crop_mode.get() != "nocrop" and not resize_selected
        for entry in self.margin_entries:
            entry["state"] = tk.NORMAL if enable_crop else tk.DISABLED

        # Pole wyboru formatu i niestandardowe rozmiary tylko dla resize_xxx
        enable_format = self.resize_mode.get() != "noresize" and not crop_selected
        self.format_combo["state"] = "readonly" if enable_format else tk.DISABLED
        enable_custom = enable_format and self.target_format.get() == "Niestandardowy"
        for entry in self.custom_entries:
            entry["state"] = tk.NORMAL if enable_custom else tk.DISABLED

        # Pozycjonowanie i offsety:
        # Aktywne dla (crop_only) lub (resize_noscale), ale tylko jeśli odpowiednie sekcje nie są zablokowane
        enable_position = (
           # (self.crop_mode.get() == "crop_only" and not resize_selected) or
            (self.resize_mode.get() == "resize_noscale" and not crop_selected)
        )
        state_radio = tk.NORMAL if enable_position else tk.DISABLED
        for rb in self.position_radiobuttons:
            rb["state"] = state_radio

        enable_offsets = enable_position and self.position_mode.get() == "custom"
        for entry in self.offset_entries:
            entry["state"] = tk.NORMAL if enable_offsets else tk.DISABLED

    def center_dialog(self, parent):
        self.update_idletasks()
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_w = parent.winfo_width()
        parent_h = parent.winfo_height()
        dialog_w = self.winfo_width()
        dialog_h = self.winfo_height()
        x = parent_x + (parent_w - dialog_w) // 2
        y = parent_y + (parent_h - dialog_h) // 2
        self.geometry(f"+{x}+{y}")

    def ok(self, event=None):
        try:
            crop_mode = self.crop_mode.get()
            resize_mode = self.resize_mode.get()

            # Marginesy
            if crop_mode == "nocrop":
                top = bottom = left = right = 0.0
            else:
                top = float(self.margin_top.get().replace(",", "."))
                bottom = float(self.margin_bottom.get().replace(",", "."))
                left = float(self.margin_left.get().replace(",", "."))
                right = float(self.margin_right.get().replace(",", "."))
                for v in [top, bottom, left, right]:
                    if v < 0:
                        raise ValueError("Marginesy muszą być nieujemne.")

            # Format i wymiary docelowe
            if resize_mode != "noresize":
                format_name = self.target_format.get()
                if format_name == "Niestandardowy":
                    w = float(self.custom_width.get().replace(",", "."))
                    h = float(self.custom_height.get().replace(",", "."))
                    if w <= 0 or h <= 0:
                        raise ValueError("Rozmiar niestandardowy musi być większy od zera.")
                    target_dims = (w, h)
                else:
                    target_dims = self.PAPER_FORMATS[format_name]
            else:
                format_name = None
                target_dims = (None, None)

            # Pozycjonowanie
            enable_position = (
                (self.crop_mode.get() == "crop_only" and not (self.resize_mode.get() != "noresize")) or
                (self.resize_mode.get() == "resize_noscale" and not (self.crop_mode.get() != "nocrop"))
            )
            if enable_position:
                position_mode = self.position_mode.get()
                offset_x = offset_y = 0.0
                if position_mode == "custom":
                    offset_x = float(self.offset_x.get().replace(",", "."))
                    offset_y = float(self.offset_y.get().replace(",", "."))
                    if offset_x < 0 or offset_y < 0:
                        raise ValueError("Offset musi być nieujemny.")
            else:
                position_mode = None
                offset_x = offset_y = None

            self.result = {
                "crop_mode": crop_mode,
                "crop_top_mm": top,
                "crop_bottom_mm": bottom,
                "crop_left_mm": left,
                "crop_right_mm": right,
                "resize_mode": resize_mode,
                "target_format": format_name,
                "target_width_mm": target_dims[0],
                "target_height_mm": target_dims[1],
                "position_mode": position_mode if enable_position else None,
                "offset_x_mm": offset_x if enable_position else None,
                "offset_y_mm": offset_y if enable_position else None,
            }
            self.destroy()
        except Exception as e:
            messagebox.showerror("Błąd", f"Nieprawidłowe dane: {e}", parent=self)

    def cancel(self, event=None):
        self.result = None
        self.destroy()

class Tooltip:
    """
    Tworzy prosty, wielokrotnie używalny dymek pomocy (tooltip) 
    dla widgetów Tkinter (przycisków, etykiet, itp.).
    """
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.id = None
        self.x = 0
        self.y = 0
        
        # Oczekuje na najechanie kursorem: po 500 ms wywołuje show()
        self.widget.bind("<Enter>", self.schedule)
        # Po opuszczeniu kursora: wywołuje hide()
        self.widget.bind("<Leave>", self.hide)

    def schedule(self, event=None):
        # Anuluje poprzednie oczekiwanie, jeśli nastąpiło ponowne wejście
        self.cancel()
        # Ustawia nowe oczekiwanie na 500 ms (0.5 sekundy)
        self.id = self.widget.after(500, self.show)

    def cancel(self):
        # Anuluje zaplanowane wyświetlenie dymka (jeśli istnieje)
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None

    def show(self, event=None):
        """Wyświetla dymek pomocy."""
        if self.tip_window or not self.text:
            return

        # 1. Tworzenie okna Toplevel
        x = self.widget.winfo_rootx() + 20 # Przesunięcie o 20px w prawo
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 1 # Pod widgetem
        
        self.tip_window = tk.Toplevel(self.widget)
        self.tip_window.wm_overrideredirect(True) # Usuwa ramkę okna
        self.tip_window.wm_geometry(f"+{x}+{y}")

        # 2. Dodanie etykiety z tekstem
        label = tk.Label(self.tip_window, text=self.text, justify=tk.LEFT,
                         background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                         font=("tahoma", "8", "normal"))
        label.pack(ipadx=1) # Minimalny padding wewnętrzny

    def hide(self, event=None):
        """Ukrywa i niszczy dymek pomocy."""
        self.cancel()
        if self.tip_window:
            self.tip_window.destroy()
        self.tip_window = None

# Przykład użycia tej klasy na przycisku:
# Tooltip(przycisk_numeracja, "Wstawia numerację na zaznaczonych stronach.")
  
import tkinter as tk
from tkinter import ttk, messagebox

class PageNumberingDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.transient(parent)
        self.title("Dodawanie numeracji stron")
        self.result = None

        self.create_variables()
        self.build_ui()

        self.resizable(False, False)
        self.grab_set()
        self.focus_force()
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.bind('<Escape>', lambda e: self.cancel())
        self.bind('<Return>', lambda e: self.ok())
        self.center_window()
        self.wait_window(self)

    def create_variables(self):
        self.v_margin_left = tk.StringVar(value="35")
        self.v_margin_right = tk.StringVar(value="25")
        self.v_margin_vertical_mm = tk.StringVar(value="15")
        self.v_vertical_pos = tk.StringVar(value='dol')
        self.v_alignment = tk.StringVar(value='prawa')
        self.v_mode = tk.StringVar(value='normalna')
        self.v_start_page = tk.StringVar(value="1")
        self.v_start_number = tk.StringVar(value="1")
        self.font_options = ["Helvetica", "Times-Roman", "Courier", "Arial"]
        self.size_options = ["6", "8", "10", "11", "12", "13", "14"]
        self.v_font_name = tk.StringVar(value=self.font_options[1])
        self.v_font_size = tk.StringVar(value="12")
        self.v_mirror_margins = tk.BooleanVar(value=False)
        self.v_format_type = tk.StringVar(value='simple')

    def center_window(self):
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        x = self.parent.winfo_x() + (self.parent.winfo_width() - w) // 2
        y = self.parent.winfo_y() + (self.parent.winfo_height() - h) // 2
        self.geometry(f'+{x}+{y}')

    def build_ui(self):
        main_frame = ttk.Frame(self, padding="6")
        main_frame.pack(fill="both", expand=True)

        PADX_GROUP = 8
        PADY_GROUP = (8, 0)
        ENTRY_WIDTH = 4

        # 1. Marginesy poziome i lustrzane
        config_frame = ttk.LabelFrame(main_frame, text="Marginesy poziome (mm)")
        config_frame.pack(fill="x", padx=PADX_GROUP, pady=PADY_GROUP)
        config_inner = ttk.Frame(config_frame)
        config_inner.pack(anchor='w', padx=2, pady=(8, 2))
        ttk.Label(config_inner, text="Lewy:").pack(side='left', padx=(0,4))
        ttk.Entry(config_inner, textvariable=self.v_margin_left, width=ENTRY_WIDTH).pack(side='left', padx=(0,10))
        ttk.Label(config_inner, text="Prawy:").pack(side='left', padx=(0,4))
        ttk.Entry(config_inner, textvariable=self.v_margin_right, width=ENTRY_WIDTH).pack(side='left', padx=(0,0))
        ttk.Checkbutton(config_frame, text="Plik ma marginesy lustrzane", variable=self.v_mirror_margins).pack(anchor='w', padx=2, pady=(6,6))

        # 2. Położenie
        pos_frame = ttk.LabelFrame(main_frame, text="Położenie numeru strony")
        pos_frame.pack(fill="x", padx=PADX_GROUP, pady=PADY_GROUP)

        row_idx = 0
        ttk.Label(pos_frame, text="Od krawędzi:").grid(row=row_idx, column=0, sticky="w", padx=(2,4), pady=(2,2))
        ttk.Entry(pos_frame, textvariable=self.v_margin_vertical_mm, width=ENTRY_WIDTH).grid(row=row_idx, column=1, sticky="w", padx=(0,2), pady=(2,2))
        row_idx += 1

        # Radiobuttony PION
        ttk.Label(pos_frame, text="Pion:").grid(row=row_idx, column=0, sticky="w", padx=(2,4), pady=(2,2))
        ttk.Radiobutton(pos_frame, text="Nagłówek", variable=self.v_vertical_pos, value='gora').grid(row=row_idx, column=1, sticky="w", padx=(0,4))
        ttk.Radiobutton(pos_frame, text="Stopka", variable=self.v_vertical_pos, value='dol').grid(row=row_idx, column=2, sticky="w", padx=(0,2))
        row_idx += 1

        # Radiobuttony POZIOM
        ttk.Label(pos_frame, text="Poziom:").grid(row=row_idx, column=0, sticky="w", padx=(2,4), pady=(2,2))
        ttk.Radiobutton(pos_frame, text="Lewo", variable=self.v_alignment, value='lewa').grid(row=row_idx, column=1, sticky="w", padx=(0,4))
        ttk.Radiobutton(pos_frame, text="Środek", variable=self.v_alignment, value='srodek').grid(row=row_idx, column=2, sticky="w", padx=(0,4))
        ttk.Radiobutton(pos_frame, text="Prawo", variable=self.v_alignment, value='prawa').grid(row=row_idx, column=3, sticky="w", padx=(0,2))
        row_idx += 1

        # Radiobuttony TRYP
        ttk.Label(pos_frame, text="Tryb:").grid(row=row_idx, column=0, sticky="w", padx=(2,4), pady=(2,2))
        ttk.Radiobutton(pos_frame, text="Normalna", variable=self.v_mode, value='normalna').grid(row=row_idx, column=1, sticky="w", padx=(0,4))
        ttk.Radiobutton(pos_frame, text="Lustrzana", variable=self.v_mode, value='lustrzana').grid(row=row_idx, column=2, sticky="w", padx=(0,2))
        row_idx += 1

        # 3. Liczniki startowe
        counter_frame = ttk.LabelFrame(main_frame, text="Wartość numeracji")
        counter_frame.pack(fill="x", padx=PADX_GROUP, pady=(8,0))
        counter_inner = ttk.Frame(counter_frame)
        counter_inner.pack(fill="x", padx=2, pady=(0,0))
        ttk.Label(counter_inner, text="Licznik numeracji zacznij od numeru:").grid(row=0, column=0, sticky="w", padx=(2,4), pady=(0,10))
        ttk.Entry(counter_inner, textvariable=self.v_start_number, width=ENTRY_WIDTH).grid(row=0, column=1, sticky="w", padx=(0,2), pady=(0,10))

        # 4. Czcionka i format
        style_frame = ttk.LabelFrame(main_frame, text="Czcionka i format numeracji")
        style_frame.pack(fill="x", padx=PADX_GROUP, pady=PADY_GROUP)
        font_row = ttk.Frame(style_frame)
        font_row.pack(anchor='w', padx=2, pady=(8, 2))
        ttk.Label(font_row, text="Czcionka:").pack(side='left', padx=(0,6))
        font_combo = ttk.Combobox(font_row, textvariable=self.v_font_name, values=self.font_options, state='readonly', width=16)
        font_combo.pack(side='left', padx=(0,10))
        ttk.Label(font_row, text="Rozmiar [pt]:").pack(side='left', padx=(0,6))
        size_combo = ttk.Combobox(font_row, textvariable=self.v_font_size, values=self.size_options, state='readonly', width=ENTRY_WIDTH)
        size_combo.pack(side='left', padx=(0,0))

        f_frame = ttk.Frame(style_frame)
        f_frame.pack(anchor='w', padx=2, pady=(8, 6))
        ttk.Label(f_frame, text="Format:").pack(side='left', padx=(0,6))
        ttk.Radiobutton(f_frame, text="Standardowy (1, 2...)", variable=self.v_format_type, value='simple').pack(side='left', padx=(0,6))
        ttk.Radiobutton(f_frame, text="Strona 1 z 99", variable=self.v_format_type, value='full').pack(side='left', padx=(0,0))

        # 5. Przyciski
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=(8,6))
        ttk.Button(button_frame, text="Wstaw", command=self.ok).pack(side='left', expand=True, padx=5)
        ttk.Button(button_frame, text="Anuluj", command=self.cancel).pack(side='right', expand=True, padx=5)

    def ok(self, event=None):
        try:
            start_page_val = int(self.v_start_page.get())
            result = {
                'margin_left_mm': float(self.v_margin_left.get().replace(',', '.')),
                'margin_right_mm': float(self.v_margin_right.get().replace(',', '.')),
                'margin_vertical_mm': float(self.v_margin_vertical_mm.get().replace(',', '.')),
                'vertical_pos': self.v_vertical_pos.get(),
                'alignment': self.v_alignment.get(),
                'mode': self.v_mode.get(),
                'start_num': int(self.v_start_number.get()),
                'start_page_idx': start_page_val - 1,
                'font_name': self.v_font_name.get().strip(),
                'font_size': float(self.v_font_size.get().replace(',', '.')),
                'mirror_margins': self.v_mirror_margins.get(),
                'format_type': self.v_format_type.get()
            }
            if result['start_num'] < 1 or start_page_val < 1:
                raise ValueError("Numery startowe i strony muszą być >= 1.")
            self.result = result
            self.destroy()
        except Exception as e:
            messagebox.showerror("Błąd wprowadzania", f"Sprawdź wprowadzone wartości: {e}", parent=self)

    def cancel(self, event=None):
        self.result = None
        self.destroy()
        
import tkinter as tk
from tkinter import ttk, messagebox

class PageNumberMarginDialog(tk.Toplevel):
    """Okno dialogowe do określania wysokości marginesów (górnego i dolnego) do skanowania."""
    def __init__(self, parent, initial_margin_mm=20):
        super().__init__(parent)
        self.parent = parent
        self.transient(parent)
        self.title("Usuwanie numeracji stron")
        self.result = None

        self.create_widgets(initial_margin_mm)
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.cancel)

        # Ustawienia modalności
        self.grab_set()
        self.focus_force()
        self.bind('<Escape>', lambda e: self.cancel())
        self.bind('<Return>', lambda e: self.ok())

        self.center_window()
        self.wait_window(self)

    def center_window(self):
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        x = self.parent.winfo_x() + (self.parent.winfo_width() - w) // 2
        y = self.parent.winfo_y() + (self.parent.winfo_height() - h) // 2
        self.geometry(f'+{x}+{y}')

    def create_widgets(self, initial_margin_mm):
        main_frame = ttk.Frame(self, padding="6")
        main_frame.pack(fill="both", expand=True)

        margin_frame = ttk.LabelFrame(
            main_frame, text="Wysokość pola z numerem (mm)", padding=(8, 4)
        )
        margin_frame.pack(fill="x", padx=4, pady=(6, 2))

        ENTRY_WIDTH = 4

        # Marginesy w jednej kolumnie grid
        for idx, (label_text, var_name) in enumerate([
            ("Od góry (nagłówek):", "top_margin_entry"),
            ("Od dołu (stopka):", "bottom_margin_entry")
        ]):
            ttk.Label(margin_frame, text=label_text).grid(
                row=idx, column=0, sticky="e", padx=(2, 6), pady=(2, 2)
            )
            entry = ttk.Entry(margin_frame, width=ENTRY_WIDTH)
            entry.insert(0, str(initial_margin_mm))
            entry.grid(row=idx, column=1, sticky="w", padx=(0, 2), pady=(2, 2))
            setattr(self, var_name, entry)

        # Przyciski
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', side='bottom', pady=(8, 4))
        ttk.Button(button_frame, text="Usuń", command=self.ok).pack(side='left', expand=True, padx=5)
        ttk.Button(button_frame, text="Anuluj", command=self.cancel).pack(side='right', expand=True, padx=5)

    def ok(self, event=None):
        try:
            top_mm = float(self.top_margin_entry.get().replace(',', '.'))
            bottom_mm = float(self.bottom_margin_entry.get().replace(',', '.'))

            if top_mm < 0 or bottom_mm < 0:
                raise ValueError("Wartości marginesów muszą być nieujemne.")

            self.result = {'top_mm': top_mm, 'bottom_mm': bottom_mm}
            self.destroy()
        except ValueError:
            messagebox.showerror("Błąd Wprowadzania", "Wprowadź prawidłowe, nieujemne liczby (w mm).")

    def cancel(self, event=None):
        self.result = None
        self.destroy()

class ShiftContentDialog(tk.Toplevel):
    """Okno dialogowe do określania przesunięcia zawartości strony, wyśrodkowane i modalne."""
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.transient(parent)
        self.title("Przesuwanie zawartości stron")
        self.result = None

        self.create_widgets()
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.cancel)

        self.grab_set()
        self.focus_force()
        self.bind('<Escape>', lambda event: self.cancel())
        self.bind('<Return>', lambda event: self.ok())

        self.center_window()
        self.wait_window(self)

    def center_window(self):
        self.update_idletasks()
        dialog_width = self.winfo_width()
        dialog_height = self.winfo_height()
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        position_x = parent_x + (parent_width // 2) - (dialog_width // 2)
        position_y = parent_y + (parent_height // 2) - (dialog_height // 2)
        self.geometry(f'+{position_x}+{position_y}')

    def create_widgets(self):
        main_frame = ttk.Frame(self, padding="8")
        main_frame.pack(fill="both", expand=True)

        # Ramka sekcji X i Y razem, jak w innych dialogach
        xy_frame = ttk.LabelFrame(main_frame, text="Kierunek i wartość przesunięcia (mm)", padding=(8, 6))
        xy_frame.pack(fill='x', padx=4, pady=(8, 0))

        ENTRY_WIDTH = 4

        # Przesunięcie X - grid, zwarty układ
        ttk.Label(xy_frame, text="Poziome:").grid(row=0, column=0, sticky="w", padx=(2, 8), pady=(4,2))
        self.x_value = ttk.Entry(xy_frame, width=ENTRY_WIDTH)
        self.x_value.insert(0, "0")
        self.x_value.grid(row=0, column=1, sticky="w", padx=(0,2), pady=(4,2))
        self.x_direction = tk.StringVar(value='P')
        ttk.Radiobutton(xy_frame, text="Lewo", variable=self.x_direction, value='L').grid(row=0, column=2, sticky="w", padx=(8, 4))
        ttk.Radiobutton(xy_frame, text="Prawo", variable=self.x_direction, value='P').grid(row=0, column=3, sticky="w", padx=(0,2))

        # Przesunięcie Y
        ttk.Label(xy_frame, text="Pionowe:").grid(row=1, column=0, sticky="w", padx=(2, 8), pady=(8,2))
        self.y_value = ttk.Entry(xy_frame, width=ENTRY_WIDTH)
        self.y_value.insert(0, "0")
        self.y_value.grid(row=1, column=1, sticky="w", padx=(0,2), pady=(8,2))
        self.y_direction = tk.StringVar(value='G')
        ttk.Radiobutton(xy_frame, text="Dół", variable=self.y_direction, value='D').grid(row=1, column=2, sticky="w", padx=(8, 4))
        ttk.Radiobutton(xy_frame, text="Góra", variable=self.y_direction, value='G').grid(row=1, column=3, sticky="w", padx=(0,2))

        # Przyciski
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', side='bottom', pady=(10, 4))
        ttk.Button(button_frame, text="Przesuń", command=self.ok).pack(side='left', expand=True, padx=5)
        ttk.Button(button_frame, text="Anuluj", command=self.cancel).pack(side='right', expand=True, padx=5)

    def ok(self, event=None):
        try:
            x_mm = float(self.x_value.get().replace(',', '.'))
            y_mm = float(self.y_value.get().replace(',', '.'))
            if x_mm < 0 or y_mm < 0:
                 raise ValueError("Wartości przesunięcia muszą być nieujemne.")
            self.result = {
                'x_dir': self.x_direction.get(),
                'y_dir': self.y_direction.get(),
                'x_mm': x_mm,
                'y_mm': y_mm
            }
            self.destroy()
        except ValueError as e:
            messagebox.showerror("Błąd Wprowadzania", f"Nieprawidłowa wartość: {e}. Użyj cyfr, kropki lub przecinka.")

    def cancel(self, event=None):
        self.result = None
        self.destroy()

import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image

class ImageImportSettingsDialog(tk.Toplevel):
    def __init__(self, parent, title, image_path):
        super().__init__(parent)
        self.transient(parent)
        self.title(title)
        self.image_path = image_path
        self.result = None

        self.image_pixel_width, self.image_pixel_height = 0, 0
        self.image_dpi = 96

        try:
            img = Image.open(image_path)
            self.image_pixel_width, self.image_pixel_height = img.size
            dpi_info = img.info.get('dpi', (96, 96))
            self.image_dpi = dpi_info[0] if isinstance(dpi_info, tuple) else 96
            img.close()
        except Exception:
            pass

        self.scaling_mode = tk.StringVar(value="DOPASUJ")
        self.alignment_mode = tk.StringVar(value="SRODEK")
        self.scale_factor = tk.DoubleVar(value=100.0)
        self.page_orientation = tk.StringVar(value="PIONOWO")

        self.initial_focus = self.body()
        self.buttonbox()
        self.update_scale_controls()

        self.update_idletasks()

        dialog_width = 360
        dialog_height = self.winfo_height()
        parent_x, parent_y = parent.winfo_rootx(), parent.winfo_rooty()
        parent_width, parent_height = parent.winfo_width(), parent.winfo_height()
        x = parent_x + parent_width // 2 - dialog_width // 2
        y = parent_y + parent_height // 2 - dialog_height // 2
        self.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        self.resizable(False, False)
        self.grab_set()

        if self.initial_focus:
            self.initial_focus.focus_set()
        self.wait_window(self)

    def body(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill="both", expand=True)

        # Sekcja 1: Informacje o obrazie
        info_frame = ttk.LabelFrame(main_frame, text="Informacje o obrazie źródłowym", padding=(8, 4))
        info_frame.pack(fill='x', pady=(0, 8))
        ttk.Label(info_frame, text=f"Wymiary: {self.image_pixel_width} x {self.image_pixel_height} px", anchor="w").pack(fill='x')
        ttk.Label(info_frame, text=f"DPI: {self.image_dpi}", anchor="w").pack(fill='x')

        # Sekcja 2: Orientacja strony A4
        orient_frame = ttk.LabelFrame(main_frame, text="Orientacja strony docelowej (A4)", padding=(8, 4))
        orient_frame.pack(fill='x', pady=(0, 8))
        ttk.Radiobutton(orient_frame, text="Pionowo", variable=self.page_orientation, value="PIONOWO").pack(anchor="w", pady=2)
        ttk.Radiobutton(orient_frame, text="Poziomo", variable=self.page_orientation, value="POZIOMO").pack(anchor="w", pady=2)

        # Sekcja 3: Skalowanie
        scale_frame = ttk.LabelFrame(main_frame, text="Ustawienia skalowania", padding=(8, 4))
        scale_frame.pack(fill='x', pady=(0, 8))
        options = [
            ("Dopasuj do strony A4", "DOPASUJ"),
            ("Oryginalny rozmiar (100%)", "ORYGINALNY"),
            ("Skala niestandardowa", "SKALA")
        ]
        for text, value in options:
            rb = ttk.Radiobutton(
                scale_frame, text=text, variable=self.scaling_mode, value=value,
                command=self.update_scale_controls
            )
            rb.pack(anchor="w", pady=2)

        self.scale_entry_frame = ttk.Frame(scale_frame)
        self.scale_entry_frame.pack(fill='x', pady=4, padx=12)
        ttk.Label(self.scale_entry_frame, text="Skala [%]:").pack(side=tk.LEFT)
        self.scale_entry = ttk.Entry(self.scale_entry_frame, textvariable=self.scale_factor, width=6)
        self.scale_entry.pack(side=tk.LEFT, padx=5)

        # Sekcja 4: Wyrównanie
        align_frame = ttk.LabelFrame(main_frame, text="Wyrównanie na stronie", padding=(8, 4))
        align_frame.pack(fill='x')
        align_options = [
            ("Środek strony", "SRODEK"),
            ("Góra", "GORA"),
            ("Dół", "DOL")
        ]
        for text, value in align_options:
            ttk.Radiobutton(align_frame, text=text, variable=self.alignment_mode, value=value).pack(anchor="w", pady=2)

        return self.scale_entry

    def update_scale_controls(self):
        if self.scaling_mode.get() == "SKALA":
            self.scale_entry.config(state=tk.NORMAL)
        else:
            self.scale_entry.config(state=tk.DISABLED)

    def buttonbox(self):
        # Wyśrodkowane przyciski z większym odstępem między nimi i mniejszym od góry
        box = ttk.Frame(self)
        box.pack(fill=tk.X, pady=(8, 10))
        center = ttk.Frame(box)
        center.pack(anchor="center")
        ttk.Button(center, text="Importuj", width=12, command=self.ok).pack(side=tk.LEFT, padx=20)
        ttk.Button(center, text="Anuluj", width=12, command=self.cancel).pack(side=tk.LEFT, padx=20)
        self.bind("<Return>", self.ok)
        self.bind("<Escape>", lambda e: self.cancel())

    def ok(self, event=None):
        if self.scaling_mode.get() == "SKALA":
            try:
                scale_val = self.scale_factor.get()
                if not (0.1 <= scale_val <= 1000):
                    messagebox.showerror(
                        "Błąd", "Skala musi być wartością liczbową od 0.1 do 1000%.", parent=self
                    )
                    self.scale_entry.focus_set()
                    return
            except tk.TclError:
                messagebox.showerror(
                    "Błąd", "Wprowadź poprawną wartość liczbową skali.", parent=self
                )
                self.scale_entry.focus_set()
                return

        self.result = {
            'scaling_mode': self.scaling_mode.get(),
            'scale_factor': self.scale_factor.get() / 100,
            'alignment': self.alignment_mode.get(),
            'page_orientation': self.page_orientation.get(),
            'image_dpi': self.image_dpi
        }
        self.destroy()

    def cancel(self, event=None):
        self.result = None
        self.destroy()
# ====================================================================
# KLASA: OKNO DIALOGOWE WYBORU ZAKRESU STRON (Bez zmian)
# ====================================================================

import tkinter as tk
from tkinter import ttk, messagebox
import re
from typing import Optional, List

class EnhancedPageRangeDialog(tk.Toplevel):
    def __init__(self, parent, title, imported_doc):
        super().__init__(parent)
        self.transient(parent)
        self.title(title)
        self.imported_doc = imported_doc

        try:
            self.max_pages = len(imported_doc)
        except ValueError:
            self.max_pages = 0
            messagebox.showerror("Błąd", "Dokument PDF został zamknięty przed otwarciem dialogu.")
            self.destroy()
            self.result = None
            return

        self.result = None

        dialog_width, dialog_height = 300, 155
        parent_x, parent_y = parent.winfo_rootx(), parent.winfo_rooty()
        parent_width, parent_height = parent.winfo_width(), parent.winfo_height()
        x = parent_x + parent_width // 2 - dialog_width // 2
        y = parent_y + parent_height // 2 - dialog_height // 2
        self.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        self.resizable(False, False)
        self.grab_set()

        self.initial_focus = self.body()
        self.buttonbox()

        if self.initial_focus:
            self.initial_focus.focus_set()

        self.wait_window(self)

    def body(self):
        main_frame = ttk.Frame(self, padding=(10, 10))
        main_frame.pack(fill="both")

        range_frame = ttk.LabelFrame(main_frame, text="Zakres stron do importu", padding=(10, 8))
        range_frame.pack(fill='x', pady=(0, 2))

        label = ttk.Label(
            range_frame,
            text=f"Podaj strony z zakresu [1 - {self.max_pages}]:",
            anchor="w"
        )
        label.grid(row=0, column=0, sticky="w", pady=(0, 2))

        self.entry = ttk.Entry(range_frame, width=18)
        self.entry.insert(0, f"1-{self.max_pages}")
        self.entry.grid(row=1, column=0, sticky="we", pady=(0, 0))

        helper = ttk.Label(
            range_frame,
            text="Format: 1, 3-5, 7",
            foreground="gray"
        )
        helper.grid(row=2, column=0, sticky="w", pady=(2, 0))

        range_frame.columnconfigure(0, weight=1)

        return self.entry

    def buttonbox(self):
        # Przycisk importuj/anuluj – tuż pod ramką, bez odstępu od dołu
        box = ttk.Frame(self)
        box.pack(fill=tk.X, pady=(4, 0))
        center = ttk.Frame(box)
        center.pack(anchor="center")
        ttk.Button(center, text="Importuj", width=12, command=self.ok).pack(side=tk.LEFT, padx=14)
        ttk.Button(center, text="Anuluj", width=12, command=self.cancel).pack(side=tk.LEFT, padx=14)
        self.bind("<Return>", self.ok)
        self.bind("<Escape>", lambda e: self.cancel())

    def ok(self, event=None):
        raw_range = self.entry.get().strip()
        if not raw_range:
            messagebox.showerror("Błąd", "Wprowadź zakres stron.", parent=self)
            self.entry.focus_set()
            return

        page_indices = self._parse_range(raw_range)
        if page_indices is None:
            messagebox.showerror("Błąd formatu", "Niepoprawny format zakresu. Użyj np. 1, 3-5, 7.", parent=self)
            self.entry.focus_set()
            return

        self.result = page_indices
        self.destroy()

    def cancel(self, event=None):
        self.result = None
        self.destroy()

    def _parse_range(self, raw_range: str) -> Optional[List[int]]:
        selected_pages = set()
        if not re.fullmatch(r'[\d,\-\s]+', raw_range):
            return None
        parts = raw_range.split(',')
        for part in parts:
            part = part.strip()
            if not part:
                continue
            if '-' in part:
                try:
                    start, end = map(int, part.split('-'))
                    start = max(1, start)
                    end = min(self.max_pages, end)
                    if start > end:
                        continue
                    for page_num in range(start, end + 1):
                        selected_pages.add(page_num - 1)
                except ValueError:
                    return None
            else:
                try:
                    page_num = int(part)
                    if 1 <= page_num <= self.max_pages:
                        selected_pages.add(page_num - 1)
                except ValueError:
                    return None
        return sorted(list(selected_pages))

# ====================================================================
# KLASA: RAMKA MINIATURY (Bez zmian)
# ====================================================================

class ThumbnailFrame(tk.Frame):
    def __init__(self, parent, viewer_app, page_index, column_width):
        super().__init__(parent, bg="#F5F5F5") 
        self.page_index = page_index
        self.viewer_app = viewer_app
        self.column_width = column_width
        self.bg_normal = "#F5F5F5"
        self.bg_selected = "#B3E5FC"
        self.outer_frame = tk.Frame(
            self, 
            bg=self.bg_normal, 
            borderwidth=0, 
            relief=tk.FLAT,
            highlightthickness=FOCUS_HIGHLIGHT_WIDTH, 
            highlightbackground=self.bg_normal 
        )
        self.outer_frame.pack(fill="both", expand=True, padx=0, pady=0)
        self.img_label = None 
        self.setup_ui(self.outer_frame)

    def _bind_all_children(self, sequence, func):
        self.bind(sequence, func)
        self.outer_frame.bind(sequence, func)
        for child in self.outer_frame.winfo_children():
            child.bind(sequence, func)
            if child.winfo_class() == 'Frame':
                 for grandchild in child.winfo_children():
                     grandchild.bind(sequence, func)

    def setup_ui(self, parent_frame):
        img_tk = self.viewer_app._render_and_scale(self.page_index, self.column_width)
        self.viewer_app.tk_images[self.page_index] = img_tk
        
        image_container = tk.Frame(parent_frame, bg="white") 
        image_container.pack(padx=5, pady=(5, 0))
        
        self.img_label = tk.Label(image_container, image=img_tk, bg="white")
        self.img_label.pack() 
        
        tk.Label(parent_frame, text=f"Strona {self.page_index + 1}", bg=self.bg_normal, font=("Helvetica", 10, "bold")).pack(pady=(5, 0))
        
        format_label = self.viewer_app._get_page_size_label(self.page_index)
        tk.Label(parent_frame, text=format_label, fg="gray", bg=self.bg_normal, font=("Helvetica", 9)).pack(pady=(0, 5))

        self._bind_all_children("<Button-1>", lambda event, idx=self.page_index: self.viewer_app._handle_lpm_click(idx, event))

        self._bind_all_children("<Button-3>", lambda event, idx=self.page_index: self._handle_ppm_click(event, idx))

    def _handle_ppm_click(self, event, page_index):
        self.viewer_app.active_page_index = page_index
        
        if page_index not in self.viewer_app.selected_pages:
             self.viewer_app.selected_pages.clear()
             self.viewer_app.selected_pages.add(page_index)
             self.viewer_app.update_selection_display()
        
        self.viewer_app.update_focus_display(hide_mouse_focus=True) 
        self.viewer_app.context_menu.tk_popup(event.x_root, event.y_root)

# ====================================================================
# GŁÓWNA KLASA PROGRAMU: SELECTABLEPDFVIEWER
# ====================================================================

class SelectablePDFViewer:
    MM_TO_POINTS = 72 / 25.4 # ~2.8346
    # === NOWE STAŁE DLA MARGINESU ===
    # Określamy wysokość marginesu do skanowania w milimetrach (np. 20 mm)
    MARGIN_HEIGHT_MM = 20
    # Obliczamy wysokość w punktach, używając Twojej stałej konwersji
    MARGIN_HEIGHT_PT = MARGIN_HEIGHT_MM * MM_TO_POINTS 
    import io
    import fitz
    from pypdf import PdfReader, PdfWriter, Transformation
    from pypdf.generic import RectangleObject, FloatObject

    MM_TO_POINTS = 72 / 25.4

    def _crop_pages(self, pdf_bytes, selected_indices, top_mm, bottom_mm, left_mm, right_mm, reposition=False, pos_mode="center", offset_x_mm=0, offset_y_mm=0):
        reader = PdfReader(io.BytesIO(pdf_bytes))
        writer = PdfWriter()
        for i, page in enumerate(reader.pages):
            if i not in selected_indices:
                writer.add_page(page)
                continue
            orig_mediabox = RectangleObject([float(v) for v in page.mediabox])
            x0, y0, x1, y1 = [float(v) for v in orig_mediabox]
            new_x0 = x0 + mm2pt(left_mm)
            new_y0 = y0 + mm2pt(bottom_mm)
            new_x1 = x1 - mm2pt(right_mm)
            new_y1 = y1 - mm2pt(top_mm)
            if new_x0 >= new_x1 or new_y0 >= new_y1:
                writer.add_page(page)
                continue
            new_rect = RectangleObject([new_x0, new_y0, new_x1, new_y1])

            # Ustaw tylko cropbox, trimbox, artbox - mediabox zostaje oryginalny!
            page.cropbox = new_rect
            page.trimbox = new_rect
            page.artbox = new_rect
            # Przywracamy mediabox (nie zmieniamy!)
            page.mediabox = orig_mediabox

            # opcjonalnie: przesuwanie zawartości strony (zostawiam bez zmian)
            if reposition:
                dx = mm2pt(offset_x_mm) if pos_mode == "custom" else 0
                dy = mm2pt(offset_y_mm) if pos_mode == "custom" else 0
                if dx != 0 or dy != 0:
                    transform = Transformation().translate(tx=dx, ty=dy)
                    page.add_transformation(transform)

            writer.add_page(page)
        out = io.BytesIO()
        writer.write(out)
        out.seek(0)
        return out.read()
        
    import fitz  # PyMuPDF

    def _mask_crop_pages(self, pdf_bytes, selected_indices, top_mm, bottom_mm, left_mm, right_mm):
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        MM_TO_PT = 72 / 25.4
        for i in selected_indices:
            page = doc[i]
            rect = page.rect

            # Wylicz marginesy w punktach
            left_pt   = left_mm * MM_TO_PT
            right_pt  = right_mm * MM_TO_PT
            top_pt    = top_mm * MM_TO_PT
            bottom_pt = bottom_mm * MM_TO_PT

            # Lewy margines
            if left_pt > 0:
                mask_rect = fitz.Rect(rect.x0, rect.y0, rect.x0 + left_pt, rect.y1)
                page.draw_rect(mask_rect, color=(1,1,1), fill=(1,1,1), overlay=True)
            # Prawy margines
            if right_pt > 0:
                mask_rect = fitz.Rect(rect.x1 - right_pt, rect.y0, rect.x1, rect.y1)
                page.draw_rect(mask_rect, color=(1,1,1), fill=(1,1,1), overlay=True)
            # Górny margines
            if top_pt > 0:
                mask_rect = fitz.Rect(rect.x0, rect.y1 - top_pt, rect.x1, rect.y1)
                page.draw_rect(mask_rect, color=(1,1,1), fill=(1,1,1), overlay=True)
            # Dolny margines
            if bottom_pt > 0:
                mask_rect = fitz.Rect(rect.x0, rect.y0, rect.x1, rect.y0 + bottom_pt)
                page.draw_rect(mask_rect, color=(1,1,1), fill=(1,1,1), overlay=True)

        output_bytes = doc.write()
        doc.close()
        return output_bytes

    def _resize_scale(self, pdf_bytes, selected_indices, width_mm, height_mm):
        reader = PdfReader(io.BytesIO(pdf_bytes))
        writer = PdfWriter()
        target_width = mm2pt(width_mm)
        target_height = mm2pt(height_mm)
        for i, page in enumerate(reader.pages):
            if i not in selected_indices:
                writer.add_page(page)
                continue
            orig_w = float(page.mediabox.width)
            orig_h = float(page.mediabox.height)
            scale = min(target_width / orig_w, target_height / orig_h)
            dx = (target_width - orig_w * scale) / 2
            dy = (target_height - orig_h * scale) / 2
            transform = Transformation().scale(sx=scale, sy=scale).translate(tx=dx, ty=dy)
            page.add_transformation(transform)
            page.mediabox = RectangleObject([0, 0, target_width, target_height])
            page.cropbox = RectangleObject([0, 0, target_width, target_height])
            writer.add_page(page)
        out = io.BytesIO()
        writer.write(out)
        out.seek(0)
        return out.read()

    def _resize_noscale(self, pdf_bytes, selected_indices, width_mm, height_mm, pos_mode="center", offset_x_mm=0, offset_y_mm=0):
        reader = PdfReader(io.BytesIO(pdf_bytes))
        writer = PdfWriter()
        target_width = mm2pt(width_mm)
        target_height = mm2pt(height_mm)
        for i, page in enumerate(reader.pages):
            if i not in selected_indices:
                writer.add_page(page)
                continue
            orig_w = float(page.mediabox.width)
            orig_h = float(page.mediabox.height)
            if pos_mode == "center":
                dx = (target_width - orig_w) / 2
                dy = (target_height - orig_h) / 2
            else:
                dx = mm2pt(offset_x_mm)
                dy = mm2pt(offset_y_mm)
            transform = Transformation().translate(tx=dx, ty=dy)
            page.add_transformation(transform)
            page.mediabox = RectangleObject([0, 0, target_width, target_height])
            page.cropbox = RectangleObject([0, 0, target_width, target_height])
            writer.add_page(page)
        out = io.BytesIO()
        writer.write(out)
        out.seek(0)
        return out.read()

    def apply_page_crop_resize_dialog(self):
        """
        Wywołaj ten kod np. w obsłudze przycisku „Kadruj/Zmień rozmiar”.
        """
        if not self.pdf_document or not self.selected_pages:
            self._update_status("Musisz zaznaczyć przynajmniej jedną stronę PDF.")
            return

        dialog = PageCropResizeDialog(self.master)
        result = dialog.result
        if not result:
            self._update_status("Anulowano operację.")
            return

        pdf_bytes_export = io.BytesIO()
        self.pdf_document.save(pdf_bytes_export)
        pdf_bytes_export.seek(0)
        pdf_bytes_val = pdf_bytes_export.read()
        indices = sorted(list(self.selected_pages))

        crop_mode = result["crop_mode"]
        resize_mode = result["resize_mode"]

        try:
            if crop_mode == "crop_only" and resize_mode == "noresize":
                new_pdf_bytes = self._mask_crop_pages(
                    pdf_bytes_val, indices,
                    result["crop_top_mm"], result["crop_bottom_mm"],
                    result["crop_left_mm"], result["crop_right_mm"],
                )
                msg = "Dodano białe maski zamiast przycinania stron."
            elif crop_mode == "crop_resize" and resize_mode == "noresize":
                new_pdf_bytes = self._crop_pages(
                    pdf_bytes_val, indices,
                    result["crop_top_mm"], result["crop_bottom_mm"],
                    result["crop_left_mm"], result["crop_right_mm"],
                    reposition=False
                )
                msg = "Zastosowano przycięcie i zmianę rozmiaru arkusza."
            elif resize_mode == "resize_scale":
                new_pdf_bytes = self._resize_scale(
                    pdf_bytes_val, indices,
                    result["target_width_mm"], result["target_height_mm"]
                )
                msg = "Zmieniono rozmiar i skalowano zawartość."
            elif resize_mode == "resize_noscale":
                new_pdf_bytes = self._resize_noscale(
                    pdf_bytes_val, indices,
                    result["target_width_mm"], result["target_height_mm"],
                    pos_mode=result.get("position_mode") or "center",
                    offset_x_mm=result.get("offset_x_mm") or 0,
                    offset_y_mm=result.get("offset_y_mm") or 0,
                )
                msg = "Zmieniono rozmiar strony (bez skalowania zawartości)."
            else:
                self._update_status("Nie wybrano żadnej operacji do wykonania.")
                return
            self._save_state_to_undo() 
            self.pdf_document.close()
            self.pdf_document = fitz.open("pdf", new_pdf_bytes)
            self._update_status(msg)
            # Odśwież widok/miniatury:
            if hasattr(self, "_reconfigure_grid"):
                self._reconfigure_grid()
            if hasattr(self, "update_selection_display"):
                self.update_selection_display()
            if hasattr(self, "update_focus_display"):
                self.update_focus_display()

        except Exception as e:
            self._update_status(f"Błąd podczas przetwarzania PDF: {e}")
            import traceback; traceback.print_exc()
                
# Zakładamy, że ta funkcja jest metodą klasy PdfToolApp, 
# która ma atrybuty self.pdf_document, self.master, self.MM_TO_POINTS, 
# _save_state, _update_status i _reconfigure_grid.

    def insert_page_numbers(self):
        """
        Wstawia numerację stron, z uwzględnieniem tylko zaznaczonych stron 
        (self.selected_pages) oraz poprawnej logiki centrowania ('srodek').
        """
        if not self.pdf_document:
            self._update_status("Błąd: Musisz najpierw załadować plik PDF.")
            return

        # POPRAWKA: Sprawdzamy i używamy atrybutu self.selected_pages
        if not hasattr(self, 'selected_pages') or not self.selected_pages:
             messagebox.showwarning("Brak wyboru", "Najpierw zaznacz strony, które mają być numerowane.")
             return
        
        # 1. Wywołanie dialogu i pobranie ustawień
        dialog = PageNumberingDialog(self.master)
        settings = dialog.result

        if settings is None:
            self._update_status("Wstawianie numeracji anulowane przez użytkownika.")
            return

        doc = self.pdf_document
        self._update_status("Wstawianie numeracji stron...")
        
        MM_PT = self.MM_TO_POINTS 

        try:
            self._save_state_to_undo() 
            
            # 2. Pobieranie parametrów
            start_number = settings['start_num']
            mode = settings['mode']                 
            direction = settings['alignment']        
            position = settings['vertical_pos']      
            mirror_margins = settings['mirror_margins']
            format_mode = settings['format_type']    
            
            left_mm = settings['margin_left_mm']
            right_mm = settings['margin_right_mm']

            left_pt_base = left_mm * MM_PT
            right_pt_base = right_mm * MM_PT
            margin_v_mm = settings['margin_vertical_mm']
            margin_v = margin_v_mm * MM_PT
            font_size = settings['font_size']
            font = settings['font_name']
            
            # Pobieramy listę indeksów stron do przetworzenia
            selected_indices = sorted(self.selected_pages)
            
            current_number = start_number
            # Całkowita liczba stron, które zostaną PONUMEROWANE (dla formatu 'full')
            total_counted_pages = len(selected_indices) + start_number - 1 
            
            # 3. Główna pętla przez ZAZNACZONE strony
            # i = indeks strony w dokumencie
            for i in selected_indices:
                
                # Używamy load_page(i) tak jak w Twojej funkcji usuwania
                page = doc.load_page(i) 
                rect = page.rect
                rotation = page.rotation
                
                # Tworzenie tekstu numeracji
                if format_mode == 'full':
                    # current_number rośnie od start_number do total_counted_pages
                    text = f"Strona {current_number} z {total_counted_pages}"
                else:
                    text = str(current_number)
                
                text_width = fitz.get_text_length(text, fontname=font, fontsize=font_size)

                # A. Ustal ostateczne wyrównanie (align)
                is_even_counted_page = (current_number - start_number) % 2 == 0 

                if mode == "lustrzana":
                    if direction == "srodek":
                        align = "srodek"
                    elif direction == "lewa":
                        # Lewa (ustawienie) = Wewnętrzna (zmiana na zewnątrz/do wewnątrz w zależności od parzystości licznika)
                        align = "lewa" if is_even_counted_page else "prawa"
                    else: # direction == "prawa"
                        # Prawa (ustawienie) = Zewnętrzna
                        align = "prawa" if is_even_counted_page else "lewa"
                else:
                    align = direction

                # B. Korekta marginesów bazowych (left_pt, right_pt) na podstawie 'mirror_margins'
                is_physical_odd = (i + 1) % 2 == 1 # Indeks strony fizycznej (i)
                
                if mirror_margins:
                    # Zamiana marginesów dla stron parzystych dokumentu
                    if is_physical_odd:
                        left_pt, right_pt = left_pt_base, right_pt_base
                    else:
                        left_pt, right_pt = right_pt_base, left_pt_base
                else:
                    left_pt, right_pt = left_pt_base, right_pt_base

                # C. Obliczanie pozycji (x, y) z uwzględnieniem rotacji
                
                if rotation == 0:
                    if align == "lewa":
                        x = rect.x0 + left_pt
                    elif align == "prawa":
                        x = rect.x1 - right_pt - text_width
                    elif align == "srodek":
                        # Skorygowana formuła centrowania
                        total_width = rect.width
                        margin_diff = left_pt - right_pt
                        x = rect.x0 + (total_width / 2) - (text_width / 2) + (margin_diff / 2)
                        
                    y = rect.y0 + margin_v + font_size if position == "gora" else rect.y1 - margin_v 
                    angle = 0
                    
                elif rotation == 90:
                    if align == "lewa":
                        y = rect.y0 + left_pt
                    elif align == "prawa":
                        y = rect.y1 - right_pt - text_width
                    elif align == "srodek":
                        total_height = rect.height 
                        margin_diff = left_pt - right_pt
                        y = rect.y0 + (total_height / 2) - (text_width / 2) + (margin_diff / 2)
                        
                    x = rect.x0 + margin_v + font_size if position == "gora" else rect.x1 - margin_v
                    angle = 90
                    
                elif rotation == 180:
                    if align == "lewa":
                        x = rect.x1 - right_pt - text_width 
                    elif align == "prawa":
                        x = rect.x0 + left_pt
                    elif align == "srodek":
                        total_width = rect.width
                        margin_diff = left_pt - right_pt
                        x = rect.x0 + (total_width / 2) - (text_width / 2) + (margin_diff / 2)

                    y = rect.y1 - margin_v - font_size if position == "gora" else rect.y0 + margin_v
                    angle = 180
                    
                elif rotation == 270:
                    if align == "lewa":
                        y = rect.y1 - right_pt - text_width
                    elif align == "prawa":
                        y = rect.y0 + left_pt
                    elif align == "srodek":
                        total_height = rect.height 
                        margin_diff = left_pt - right_pt
                        y = rect.y0 + (total_height / 2) - (text_width / 2) + (margin_diff / 2)
                        
                    x = rect.x1 - margin_v - font_size if position == "gora" else rect.x0 + margin_v
                    angle = 270
                else:
                    x = rect.x0 + left_pt
                    y = rect.y1 - margin_v
                    angle = 0

                # D. Wstawienie numeru
                page.insert_text(
                    fitz.Point(x, y),
                    text,
                    fontsize=font_size,
                    fontname=font,
                    color=(0, 0, 0),
                    rotate=angle
                )

                # WZROST LICZNIKA TYLKO DLA PRZETWORZONEJ STRONY
                current_number += 1

            # 4. Finalizacja GUI
            self._reconfigure_grid() 
            self._update_status(f"Numeracja wstawiona na {len(selected_indices)} stronach. Plik gotowy do zapisu.")

        except Exception as e:
            self._update_status(f"BŁĄD przy dodawaniu numeracji: {e}")
            messagebox.showerror("Błąd Numeracji", str(e))
    def remove_page_numbers(self):
        """
        Usuwa numery stron z marginesów określonych przez użytkownika.
        """
        if not self.pdf_document or not self.selected_pages:
            self._update_status("Musisz załadować dokument i zaznaczyć strony.")
            return

        # 1. Otwarcie dialogu i pobranie wartości od użytkownika
        dialog = PageNumberMarginDialog(self.master, initial_margin_mm=20) # Zakładam, że root to główne okno
        margins = dialog.result

        if margins is None:
            self._update_status("Usuwanie numerów stron anulowane.")
            return

        top_mm = margins['top_mm']
        bottom_mm = margins['bottom_mm']
        
        # Przeliczanie milimetrów na punkty
        mm_to_points = self.MM_TO_POINTS # Używamy stałej klasy
        top_pt = top_mm * mm_to_points
        bottom_pt = bottom_mm * mm_to_points

        # ... (resztę kodu ustawiającą wzorce zostawiamy bez zmian) ...
        page_number_patterns = [
            r'^\s*[-–]?\s*\d+\s*[-–]?\s*$',  # 1, -1-, - 1 -
            r'^\s*(?:Strona|Page)\s+\d+\s+(?:z|of)\s+\d+\s*$', 
            r'^\s*\d+\s*(?:/|-|\s+)\s*\d+\s*$',
            r'^\s*\(\s*\d+\s*\)\s*$' 
        ]
        compiled_patterns = [re.compile(p, re.IGNORECASE) for p in page_number_patterns]

        try:
            pages_to_process = sorted(list(self.selected_pages))
            modified_count = 0
            
            for page_index in pages_to_process:
                page = self.pdf_document.load_page(page_index)
                rect = page.rect
                
                # 2. Definicja obszarów skanowania na podstawie wartości użytkownika
                
                # Margines Górny (od 0 do top_pt)
                top_margin_rect = fitz.Rect(rect.x0, rect.y0, rect.x1, rect.y0 + top_pt)
                
                # Margines Dolny (od rect.y1 - bottom_pt do rect.y1)
                bottom_margin_rect = fitz.Rect(rect.x0, rect.y1 - bottom_pt, rect.x1, rect.y1)
                
                scan_rects = [top_margin_rect, bottom_margin_rect]
                
                found_and_removed = False
                
                # ... (resztę logiki ekstrakcji i usuwania tekstu zostawiamy bez zmian) ...
                
                for scan_rect in scan_rects:
                    text_blocks = page.get_text("blocks", clip=scan_rect)
                    
                    for block in text_blocks:
                        block_text = block[4]
                        lines = block_text.strip().split('\n')
                        
                        for line in lines:
                            cleaned_line = line.strip()
                            for pattern in compiled_patterns:
                                if pattern.fullmatch(cleaned_line):
                                    text_instances = page.search_for(cleaned_line, clip=scan_rect)
                                    
                                    for inst in text_instances:
                                        page.add_redact_annot(inst)
                                        found_and_removed = True
                                        
                if found_and_removed:
                    page.apply_redactions()
                    modified_count += 1
                    
            # 3. Finalizacja
            if modified_count > 0:
                self._save_state_to_undo()
                self._reconfigure_grid() 
                self._update_status(f"Usunięto numery stron na {modified_count} stronach, używając marginesów: G={top_mm:.1f}mm, D={bottom_mm:.1f}mm.")
            else:
                self._update_status(f"Nie znaleziono numerów stron w marginesach: G={top_mm:.1f}mm, D={bottom_mm:.1f}mm.")
                
        except Exception as e:
            self._update_status(f"BŁĄD: Nie udało się usunąć numerów stron: {e}")

    def shift_page_content(self):
        """
        Otwiera okno dialogowe i przesuwa zawartość zaznaczonych stron,
        używając PyPDF do transformacji macierzowej.
        """
        if not self.pdf_document or not self.selected_pages:
            self._update_status("Musisz załadować dokument i zaznaczyć strony do przesunięcia.")
            return

        # 1. Uruchomienie okna dialogowego i pobranie wyników
        dialog = ShiftContentDialog(self.master)
        result = dialog.result

        if not result or (result['x_mm'] == 0 and result['y_mm'] == 0):
            self._update_status("Anulowano lub zerowe przesunięcie.")
            return

        # 2. Konwersja i określenie transformacji
        dx_pt = result['x_mm'] * self.MM_TO_POINTS
        dy_pt = result['y_mm'] * self.MM_TO_POINTS
        
        # Określenie znaku przesunięcia
        x_sign = 1 if result['x_dir'] == 'P' else -1 # Prawo (+), Lewo (-)
        y_sign = 1 if result['y_dir'] == 'G' else -1 # Góra (+), Dół (-)
        
        final_dx = dx_pt * x_sign
        final_dy = dy_pt * y_sign # Pamiętaj, że w PDF Y rośnie w górę

        try:
            pages_to_shift = sorted(list(self.selected_pages))
            
            # === Przygotowanie do transformacji za pomocą PyPDF ===
            
            # Krok 1: Zapisz aktualny dokument PyMuPDF do bufora PyPDF może go wczytać
            pdf_bytes = self.pdf_document.tobytes()
            pdf_reader = PdfReader(io.BytesIO(pdf_bytes))
            pdf_writer = PdfWriter()
            
            # Krok 2: Tworzenie macierzy transformacji (przesunięcie)
            # [1, 0, 0, 1, x, y]
            # Używamy ujemnego Y, aby przesunąć w górę (G), co jest zgodne z PDF
            
            transform = Transformation().translate(tx=final_dx, ty=final_dy)
            
            # Krok 3: Iteracja przez strony i stosowanie macierzy
            for i, page in enumerate(pdf_reader.pages):
                if i in pages_to_shift:
                    # Stosowanie transformacji do strony
                    page.add_transformation(transform)
                    
                # Dodaj stronę do nowego writera
                pdf_writer.add_page(page)

            # Krok 4: Zapisanie nowego dokumentu do bufora
            new_pdf_stream = io.BytesIO()
            pdf_writer.write(new_pdf_stream)
            new_pdf_bytes = new_pdf_stream.getvalue()
            
            # Krok 5: Aktualizacja stanu aplikacji za pomocą PyMuPDF
            if self.pdf_document: self.pdf_document.close()
            self.pdf_document = fitz.open("pdf", new_pdf_bytes)
            
            # 3. Zapisanie stanu i odświeżenie GUI
            self._save_state_to_undo() # Zapisuje nowy stan do historii
            self._reconfigure_grid() 
            self._update_status(f"Przesunięto zawartość na {len(pages_to_shift)} stronach o {result['x_mm']} mm (X) i {result['y_mm']} mm (Y) za pomocą PyPDF.")
            
        except Exception as e:
            self._update_status(f"BŁĄD PyPDF: Nie udało się przesunąć zawartości: {e}")
            
    def _reverse_pages(self):
        """Odwraca kolejność wszystkich stron w bieżącym dokumencie PDF."""
        if not self.pdf_document:
            messagebox.showinfo("Informacja", "Najpierw otwórz plik PDF.")
            return

        # 1. Zapisz obecny stan do historii przed zmianą
        self._save_state_to_undo() 
        
        try:
            doc = self.pdf_document
            page_count = len(doc)
            
            # Tworzenie nowego, pustego dokumentu z odwróconą kolejnością
            new_doc = fitz.open() 
            for i in range(page_count - 1, -1, -1):
                new_doc.insert_pdf(doc, from_page=i, to_page=i)
                
            # Zastąpienie starego dokumentu nowym
            self.pdf_document.close()
            self.pdf_document = new_doc
            
            # 2. Resetowanie stanu (wyzerowanie zaznaczenia)
            self.active_page_index = 0
            self.selected_pages.clear()
            
            # 3. RĘCZNE CZYSZCZENIE I ODŚWIEŻENIE WIDOKU
            # Używamy zestawu metod zidentyfikowanych w Twoim kodzie:
            self.tk_images.clear()
            for widget in list(self.scrollable_frame.winfo_children()): 
                widget.destroy()
            self.thumb_frames.clear()

            self._reconfigure_grid()
            self.update_tool_button_states()
            self.update_focus_display()
            # -----------------------------------------------
            
            self._update_status(f"Pomyślnie odwrócono kolejność {page_count} stron.")
            
        except Exception as e:
            messagebox.showerror("Błąd", f"Wystąpił błąd podczas odwracania stron: {e}")
            # W przypadku błędu użytkownik może użyć przycisku Cofnij aby przywrócić stan
    
    def _apply_selection_by_indices(self, indices_to_select):
        """Ogólna metoda do zaznaczania stron na podstawie listy indeksów."""
        if not self.pdf_document:
            return

        current_selection = self.selected_pages.copy()
        
        # Tworzenie nowej, czystej selekcji
        new_selection = set(indices_to_select)
        
        # Zastąpienie dotychczasowej selekcji
        self.selected_pages = new_selection
        
        # Przerenderowanie, jeśli selekcja się zmieniła
        if current_selection != self.selected_pages:
            
            # === POPRAWKA ===
            # Właściwa metoda do odświeżania widoku po zmianie zaznaczenia:
            self.update_selection_display()
            # ================
            self.update_tool_button_states()
            
    def _select_odd_pages(self):
        """Zaznacza strony nieparzyste (indeksy 0, 2, 4...)."""
        if not self.pdf_document: return
        
        # W Pythonie indeksy są od 0, więc strony nieparzyste mają indeksy parzyste (0, 2, 4...)
        indices = [i for i in range(len(self.pdf_document)) if i % 2 == 0]
        self._apply_selection_by_indices(indices)

    def _select_even_pages(self):
        """Zaznacza strony parzyste (indeksy 1, 3, 5...)."""
        if not self.pdf_document: return

        # Strony parzyste mają indeksy nieparzyste (1, 3, 5...)
        indices = [i for i in range(len(self.pdf_document)) if i % 2 != 0]
        self._apply_selection_by_indices(indices)

    def _select_portrait_pages(self):
        """Zaznacza strony pionowe (wysokość > szerokość)."""
        if not self.pdf_document: return
        
        indices = []
        for i in range(len(self.pdf_document)):
            page = self.pdf_document.load_page(i)
            # Sprawdzenie, czy wysokość bounding boxu jest większa niż szerokość
            if page.rect.height > page.rect.width:
                indices.append(i)
        self._apply_selection_by_indices(indices)
        
    def _select_landscape_pages(self):
        """Zaznacza strony poziome (szerokość >= wysokość)."""
        if not self.pdf_document: return
        
        indices = []
        for i in range(len(self.pdf_document)):
            page = self.pdf_document.load_page(i)
            # Sprawdzenie, czy szerokość bounding boxu jest większa lub równa wysokości
            if page.rect.width >= page.rect.height:
                indices.append(i)
        self._apply_selection_by_indices(indices)
    
    def export_selected_pages_to_image(self):
        """Eksportuje wybrane strony do plików PNG o wysokiej rozdzielczości."""
        
        selected_indices = sorted(list(self.selected_pages))
        
        if not selected_indices:
            messagebox.showinfo("Informacja", "Wybierz strony do eksportu.")
            return

        output_dir = filedialog.askdirectory(
            title="Wybierz folder do zapisu wyeksportowanych obrazów"
        )
        
        if not output_dir:
            return

        try:
            # Ustawienia eksportu
            zoom = 300 / 72.0 
            matrix = fitz.Matrix(zoom, zoom)
            
            # POPRAWKA BŁĘDU: Bezpieczne pobieranie nazwy bazowej
            # Jeśli self.file_path istnieje, użyj jego nazwy. W przeciwnym razie, użyj "export".
            if hasattr(self, 'file_path') and self.file_path:
                base_filename = os.path.splitext(os.path.basename(self.file_path))[0]
            else:
                base_filename = "export"
            
            exported_count = 0
            
            self.master.config(cursor="wait")
            self.master.update()
            
            for index in selected_indices:
                if index < len(self.pdf_document):
                    page = self.pdf_document.load_page(index)
                    
                    pix = page.get_pixmap(matrix=matrix, alpha=False)
                    
                    # Budowanie nazwy pliku: "nazwa_dokumentu_strona_X.png"
                    output_filename = f"{base_filename}_strona_{index + 1}.png"
                    output_path = os.path.join(output_dir, output_filename)
                    
                    pix.save(output_path)
                    exported_count += 1
            
            self.master.config(cursor="")
            
        #    messagebox.showinfo(
        #        "Sukces Eksportu", 
        #        f"Pomyślnie wyeksportowano {exported_count} stron do folderu:\n{output_dir}"
        #    )
            self._update_status(f"Pomyślnie wyeksportowano {exported_count} stron do folderu: {output_dir}")   
        except Exception as e:
            self.master.config(cursor="")
            messagebox.showerror("Błąd Eksportu", f"Wystąpił błąd podczas eksportowania stron:\n{e}")
            
            
    
    
    def __init__(self, master):
        self.master = master
        master.title(PROGRAM_TITLE) 
        
        master.protocol("WM_DELETE_WINDOW", self.on_close_window) 

        self.pdf_document = None
        self.selected_pages: Set[int] = set()
        self.tk_images: Dict[int, ImageTk.PhotoImage] = {}
        self.icons: Dict[str, Union[ImageTk.PhotoImage, str]] = {} 
        
        self.thumb_frames: Dict[int, 'ThumbnailFrame'] = {}
        self.active_page_index = 0 

        self.clipboard: Optional[bytes] = None 
        self.pages_in_clipboard_count: int = 0 
        
        self.fixed_thumb_width = 250  
        self.min_zoom_width = 150    
        self.THUMB_PADDING = 8       
        self.ZOOM_FACTOR = 0.9       
        self.target_num_cols = 4     
        self.min_cols = 2            
        self.max_cols = 10           
        self.MIN_WINDOW_WIDTH = 1000    
        self.render_dpi_factor = 0.833 
        
        self.undo_stack: List[bytes] = []
        self.redo_stack: List[bytes] = []
        self.max_stack_size = 50
        
        self._set_initial_geometry() 
        self._load_icons_or_fallback(size=28) 
        self._create_menu() 
        self._setup_context_menu() 
        self._setup_key_bindings() 
        
        GRAY_BG = BG_BUTTON_DEFAULT    
        GRAY_FG = FG_TEXT
        
        self.BG_OPEN = GRAY_BG     
        self.BG_SAVE = GRAY_BG     
        self.BG_UNDO = GRAY_BG     
        self.BG_DELETE = GRAY_BG   
        self.BG_INSERT = GRAY_BG   
        self.BG_ROTATE = GRAY_BG
        self.BG_SHIFT = GRAY_BG
        self.BG_CLIPBOARD = GRAY_BG 
        
        self.BG_IMPORT = GRAY_BG
        self.BG_EXPORT = GRAY_BG

        main_control_panel = tk.Frame(master, bg=BG_SECONDARY, padx=10, pady=5) 
        main_control_panel.pack(side=tk.TOP, fill=tk.X)
        
        tools_frame = tk.Frame(main_control_panel, bg=BG_SECONDARY)
        tools_frame.pack(side=tk.LEFT, fill=tk.Y)

        ICON_WIDTH = 3
        ICON_FONT = ("Arial", 14)
        PADX_SMALL = 5
        PADX_LARGE = 15
        
        def create_tool_button(parent, key, command, bg_color, fg_color="#333", state=tk.NORMAL, padx=(0, PADX_SMALL)):
            icon = self.icons[key]
            
            # NOWA LOGIKA: Zwiększenie czytelności przycisku
            btn_text = ""
                        
            common_config = {
                'command': command,
                'state': state,
                'bg': bg_color,
                'relief': tk.RAISED,
                'bd': 1,
            }

            if isinstance(icon, ImageTk.PhotoImage):
                 # Jeśli używamy ikon graficznych, używamy ich
                 btn = tk.Button(parent, image=icon, **common_config)
                 btn.image = icon 
            else:
                 # Jeśli używamy emoji/tekstu zastępczego, używamy dłuższej formy dla czytelności
                 if btn_text:
                     btn = tk.Button(parent, text=btn_text, font=("Arial", 9, "bold"), fg=fg_color, **common_config)
                 else:
                     btn = tk.Button(parent, text=icon, width=ICON_WIDTH, font=ICON_FONT, fg=fg_color, **common_config)
            
            btn.pack(side=tk.LEFT, padx=padx)
            return btn

        # 1. PRZYCISKI PLIK/ZAPISZ/IMPORT/EKSPORT/COFNIJ
        self.open_button = create_tool_button(tools_frame, 'open', self.open_pdf, self.BG_OPEN, GRAY_FG, padx=(5, PADX_SMALL)) 
        
        self.save_button_icon = create_tool_button(tools_frame, 'save', self.save_document, self.BG_SAVE, GRAY_FG, state=tk.DISABLED, padx=(0, PADX_LARGE)) 
        
        # PRZYCISK IMPORTU PDF 
        self.import_button = create_tool_button(tools_frame, 'import', self.import_pdf_after_active_page, self.BG_IMPORT, GRAY_FG, state=tk.DISABLED, padx=(0, PADX_SMALL)) 
        self.extract_button = create_tool_button(tools_frame, 'export', self.extract_selected_pages, self.BG_EXPORT, GRAY_FG, state=tk.DISABLED, padx=(0, PADX_LARGE)) 
        
        # PRZYCISK IMPORTU OBRAZU 
        self.image_import_button = create_tool_button(tools_frame, 'image_import', self.import_image_to_new_page, self.BG_IMPORT, GRAY_FG, state=tk.DISABLED, padx=(0, PADX_SMALL)) 
        self.export_image_button = create_tool_button(tools_frame, 'export_image', self.export_selected_pages_to_image, self.BG_EXPORT, GRAY_FG, state=tk.DISABLED, padx=(0, PADX_LARGE))
        
        self.undo_button = create_tool_button(tools_frame, 'undo', self.undo, self.BG_UNDO, GRAY_FG, state=tk.DISABLED, padx=(0, PADX_SMALL))
        self.redo_button = create_tool_button(tools_frame, 'redo', self.redo, self.BG_UNDO, GRAY_FG, state=tk.DISABLED, padx=(0, PADX_LARGE))
        
        # 2. PRZYCISKI EDYCJI STRON
        self.delete_button = create_tool_button(tools_frame, 'delete', self.delete_selected_pages, self.BG_DELETE, GRAY_FG, state=tk.DISABLED, padx=(0, PADX_SMALL)) 
        
        # 3. PRZYCISKI WYCINAJ/KOPIUJ/WKLEJ
        self.cut_button = create_tool_button(tools_frame, 'cut', self.cut_selected_pages, self.BG_CLIPBOARD, GRAY_FG, state=tk.DISABLED, padx=(0, PADX_SMALL)) 
        self.copy_button = create_tool_button(tools_frame, 'copy', self.copy_selected_pages, self.BG_CLIPBOARD, GRAY_FG, state=tk.DISABLED, padx=(0, PADX_SMALL)) 
        
        self.paste_before_button = create_tool_button(tools_frame, 'paste_b', self.paste_pages_before, self.BG_CLIPBOARD, GRAY_FG, state=tk.DISABLED, padx=(0, PADX_SMALL)) 
        self.paste_after_button = create_tool_button(tools_frame, 'paste_a', self.paste_pages_after, self.BG_CLIPBOARD, GRAY_FG, state=tk.DISABLED, padx=(0, PADX_LARGE)) 
        
        self.insert_before_button = create_tool_button(tools_frame, 'insert_b', self.insert_blank_page_before, self.BG_INSERT, GRAY_FG, state=tk.DISABLED, padx=(0, PADX_SMALL)) 
        self.insert_after_button = create_tool_button(tools_frame, 'insert_a', self.insert_blank_page_after, self.BG_INSERT, GRAY_FG, state=tk.DISABLED, padx=(0, PADX_LARGE)) 
        
        self.rotate_left_button = create_tool_button(tools_frame, 'rotate_l', lambda: self.rotate_selected_page(-90), self.BG_ROTATE, GRAY_FG, state=tk.DISABLED, padx=(0, PADX_SMALL)) 
        self.rotate_right_button = create_tool_button(tools_frame, 'rotate_r', lambda: self.rotate_selected_page(90), self.BG_ROTATE, GRAY_FG, state=tk.DISABLED, padx=(0, 20)) 

        self.shift_content_btn = create_tool_button(tools_frame, 'shift', self.shift_page_content, self.BG_SHIFT, GRAY_FG, state=tk.DISABLED, padx=(0, PADX_LARGE))
        self.remove_nums_btn = create_tool_button(tools_frame, 'page_num_del', self.remove_page_numbers, self.BG_DELETE, GRAY_FG, state=tk.DISABLED, padx=(0, PADX_SMALL))
        self.add_nums_btn = create_tool_button(tools_frame, 'add_nums', self.insert_page_numbers, self.BG_INSERT, GRAY_FG, state=tk.DISABLED, padx=(0, PADX_LARGE))
        
        
        Tooltip(self.open_button, "Otwórz plik PDF.")
        Tooltip(self.save_button_icon, "Zapisz całość do nowego pliku PDF.")
        
        Tooltip(self.import_button, "Importuj strony z pliku PDF.\n" "Strony zostaną wstawione po bieżącej, a przy braku zazanczenia - na końcu pliku.")
        Tooltip(self.extract_button, "Eksportuj strony do pliku PDF.\n" "Wymaga zaznaczenia przynajniej jednej strony.")
        
        Tooltip(self.image_import_button, "Importuj strony z pliku obrazu.\n" "Strony zostaną wstawione po bieżącej, a przy braku zazanczenia - na końcu pliku.")
        Tooltip(self.export_image_button, "Eksportuj strony do plików PNG.\n" "Wymaga zaznaczenia przynajniej jednej strony.")
        
        Tooltip(self.undo_button, "Cofnij ostatnią zmianę.\n" "Obsługuje do 50 kroków wstecz.")
        Tooltip(self.redo_button, "Ponów cofniętą zmianę.\n" "Obsługuje do 50 kroków do przodu.")
        
        Tooltip(self.delete_button, "Usuń zaznaczone strony.\n" "Wymaga zaznaczenia przynajniej jednej strony.")
        Tooltip(self.cut_button, "Wytnij zaznaczone strony.\n" "Wymaga zaznaczenia przynajniej jednej strony.")
        Tooltip(self.copy_button, "Skopiuj zaznaczone strony.\n" "Wymaga zaznaczenia przynajniej jednej strony.")
        
        Tooltip(self.paste_before_button, "Wklej stronę przed bieżącą.\n" "Wymaga wcześniejszego skopiowania/wycięcia prznajmniej jednej strony.")
        Tooltip(self.paste_after_button, "Wklej stronę po bieżącej.\n" "Wymaga wcześniejszego skopiowania/wycięcia prznajmniej jednej strony.")
        
        Tooltip(self.insert_before_button, "Wstaw pustą stronę przed bieżącą.\n" "Wymaga zaznaczenia jednej strony.")
        Tooltip(self.insert_after_button, "Wstaw pustą stronę po bieżącej.\n" "Wymaga zaznaczenia jednej strony.")

        Tooltip(self.rotate_left_button, "Obróć w lewo - prawidłowy obrót dla druku stron poziomych.\n" "Wymaga zaznaczenia przynajniej jednej strony.")
        Tooltip(self.rotate_right_button, "Obróć w prawo.\n" "Wymaga zaznaczenia przynajniej jednej strony.")
        Tooltip(self.shift_content_btn, "Zmiana marginesów (przesuwanie obrazu).\n" "Wymaga zaznaczenia przynajniej jednej strony.")
        Tooltip(self.remove_nums_btn, "Usuwanie numeracji. \n" "Wymaga zaznaczenia przynajniej jednej strony.")
        Tooltip(self.add_nums_btn, "Wstawianie numeracji. \n" "Wymaga zaznaczenia przynajniej jednej strony.")

        # ZOOM 
        zoom_frame = tk.Frame(main_control_panel, bg=BG_SECONDARY)
        zoom_frame.pack(side=tk.RIGHT, padx=10)
        
        ZOOM_BG = GRAY_BG 
        ZOOM_FONT = ("Arial", 14, "bold") 
        ZOOM_WIDTH = 2
        
        self.zoom_in_button = create_tool_button(zoom_frame, 'zoom_in', self.zoom_in, ZOOM_BG, fg_color=GRAY_FG, padx=(2, 2), state=tk.DISABLED) 
        if not isinstance(self.icons['zoom_in'], ImageTk.PhotoImage):
             self.zoom_in_button.config(width=ZOOM_WIDTH, height=1, font=ZOOM_FONT)

        self.zoom_out_button = create_tool_button(zoom_frame, 'zoom_out', self.zoom_out, ZOOM_BG, fg_color=GRAY_FG, padx=(2, 5), state=tk.DISABLED) 
        if not isinstance(self.icons['zoom_out'], ImageTk.PhotoImage):
             self.zoom_out_button.config(width=ZOOM_WIDTH, height=1, font=ZOOM_FONT)
        
        
        # Pasek statusu 
        self.status_bar = tk.Label(master, text="Gotowy. Otwórz plik PDF.", bd=1, relief=tk.SUNKEN, anchor=tk.W, bg="#f0f0f0", fg="black")
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)


        self.canvas = tk.Canvas(master, bg="#F5F5F5") 
        self.scrollbar = tk.Scrollbar(master, orient="vertical", command=self.canvas.yview)
        
        self.scrollable_frame = tk.Frame(self.canvas, bg="#F5F5F5") 
        
        self.canvas_window_id = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        self.canvas.bind("<Configure>", self._reconfigure_grid) 
        
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True) 

        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel) 
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)
        
        self.update_tool_button_states() 
        self._setup_drag_and_drop_file()

    # --- Metody obsługi GUI i zdarzeń (Bez zmian) ---
    def on_close_window(self):
        # Sprawdź czy są niezapisane zmiany (niepusty stos undo)
        if self.pdf_document is not None and len(self.undo_stack) > 0:
            response = messagebox.askyesnocancel(
                "Niezapisane zmiany",
                "Czy chcesz zapisać zmiany w dokumencie przed zamknięciem programu?"
            )
            if response is None: 
                return
            elif response is True: 
                self.save_document() 
                if len(self.undo_stack) > 0:
                    return 
                self.master.quit() 
            else: 
                self.master.quit()
        else:
            self.master.quit()

    def _set_initial_geometry(self):
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        initial_width = self.MIN_WINDOW_WIDTH
        initial_height = int(screen_height * 0.50)  
        self.master.minsize(self.MIN_WINDOW_WIDTH, initial_height)
        x_cordinate = int((screen_width / 2) - (initial_width / 2))
        y_cordinate = int((screen_height / 2) - (initial_height / 2))
        self.master.geometry(f"{initial_width}x{initial_height}+{x_cordinate}+{y_cordinate}")

    def _load_icons_or_fallback(self, size=28):
        icon_map = {
            'open': ('📂', "open.png"),
            'save': ('💾', "save.png"),
            'undo': ('↩️', "undo.png"),
            'redo': ('↪️', "redo.png"),
            'delete': ('🗑️', "delete.png"),
            'cut': ('✂️', "cut.png"),  
            'copy': ('📋', "copy.png"),  
            'paste_b': ('⬆️📄', "paste_before.png"),  
            'paste_a': ('⬇️📄', "paste_after.png"),  
            'insert_b': ('⬆️➕', "insert_before.png"),  
            'insert_a': ('⬇️➕', "insert_after.png"),  
            'rotate_l': ('↺', "rotate_left.png"),
            'rotate_r': ('↻', "rotate_right.png"),
            'zoom_in': ('➖', "zoom_in.png"),  
            'zoom_out': ('➕', "zoom_out.png"),
            'export': ('📤', "export.png"), 
            'export_image': ('🖼️', "export_image.png"),
            'import': ('📥', "import.png"), # Import PDF
            'image_import': ('🖼️', "import_image.png"), # Import Obrazu
            'shift': ('↔️', "shift.png"), 
            'page_num_del': ('#️⃣❌', "del_nums.png"), 
            'add_nums': ('#️⃣➕', "add_nums.png"), 

        }
        for key, (emoji, filename) in icon_map.items():
            try:
                path = os.path.join(ICON_FOLDER, filename)
                img = Image.open(path).convert("RGBA")
                self.icons[key] = ImageTk.PhotoImage(img.resize((size, size), Image.LANCZOS))
            except Exception:
                self.icons[key] = emoji

    def _create_menu(self):
        menu_bar = tk.Menu(self.master)
        self.master.config(menu=menu_bar)

        self.file_menu = tk.Menu(menu_bar, tearoff=0)  
        menu_bar.add_cascade(label="Plik", menu=self.file_menu)
        self.file_menu.add_command(label="Otwórz PDF...", command=self.open_pdf, accelerator="Ctrl+O")
        self.file_menu.add_command(label="Zapisz jako...", command=self.save_document, state=tk.DISABLED, accelerator="Ctrl+S")
        self.file_menu.add_separator() 
        self.file_menu.add_command(label="Importuj strony z PDF...", command=self.import_pdf_after_active_page, state=tk.DISABLED, accelerator="Ctrl+I") 
        self.file_menu.add_command(label="Eksportuj strony do PDF...", command=self.extract_selected_pages, state=tk.DISABLED,accelerator="Ctrl+E") 
        self.file_menu.add_separator() 
        self.file_menu.add_command(label="Importuj obraz na nową stronę...", command=self.import_image_to_new_page, state=tk.DISABLED, accelerator="Ctrl+Shift+I") 
        self.file_menu.add_command(label="Eksportuj strony jako obrazy PNG...", command=self.export_selected_pages_to_image, state=tk.DISABLED, accelerator="Ctrl+Shift+E")
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Zamknij program", command=self.on_close_window)  

        select_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Zaznacz", menu=select_menu)
        select_menu.add_command(label="Wszystkie strony", command=self._select_all, accelerator="Ctrl+A, F4")
        select_menu.add_separator()
        select_menu.add_command(label="Strony nieparzyste", command=self._select_odd_pages, state=tk.DISABLED, accelerator="F1")
        select_menu.add_command(label="Strony parzyste", command=self._select_even_pages, state=tk.DISABLED, accelerator="F2")
        select_menu.add_separator()
        select_menu.add_command(label="Strony pionowe", command=self._select_portrait_pages, state=tk.DISABLED, accelerator="Ctrl+F1")
        select_menu.add_command(label="Strony poziome", command=self._select_landscape_pages, state=tk.DISABLED, accelerator="Ctrl+F2")
        self.select_menu = select_menu
        
        self.edit_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Edycja", menu=self.edit_menu)
        self._populate_edit_menu(self.edit_menu)
        
        self.modifications_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Modyfikacje", menu=self.modifications_menu)
        self._populate_modifications_menu(self.modifications_menu) # Wypełniamy nową metodą
        
        self.help_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Pomoc", menu=self.help_menu)
        self.help_menu.add_command(label="O programie", command=self.show_about_dialog)
        
        

    def show_about_dialog(self):
        PROGRAM_LOGO_PATH = resource_path(os.path.join('icons', 'logo.png'))
        # STAŁE WYMIARY OKNA
        DIALOG_WIDTH = 280
        DIALOG_HEIGHT = 260

        # 1. Inicjalizacja i Ustawienia Okna
        dialog = tk.Toplevel(self.master)
        dialog.title("O programie")
        dialog.geometry(f"{DIALOG_WIDTH}x{DIALOG_HEIGHT}") # Ustawienie stałego rozmiaru
        dialog.resizable(False, False) # Zablokowanie zmiany rozmiaru
        
        # Ustawienia modalne
        dialog.transient(self.master)
        dialog.grab_set()
        dialog.focus_set()
        
        # 2. Centralizacja Okna (Matematyczna, używając stałych)
        dialog.update_idletasks() # Wymuś odświeżenie dla bezpieczeństwa
        
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        
        # Obliczenia bazujące na stałych
        position_top = int(screen_height / 2 - DIALOG_HEIGHT / 2)
        position_right = int(screen_width / 2 - DIALOG_WIDTH / 2)
        
        # Zastosowanie pozycji (nie zmieniamy rozmiaru w tym wywołaniu)
        dialog.geometry(f'+{position_right}+{position_top}')
        
        # --- Ramka Centrująca Treść ---
        main_frame = ttk.Frame(dialog)
        # Pack bez expand/fill sprawia, że treść jest mała i wyśrodkowana w stałym oknie
        main_frame.pack(padx=10, pady=10) 

        # 3. Dodanie Grafiki
        logo_path = PROGRAM_LOGO_PATH 
        self.tk_image = None 

        if logo_path:
            try:
                pil_image = Image.open(logo_path)
                pil_image = pil_image.resize((60, 60), Image.Resampling.LANCZOS)
                
                self.tk_image = ImageTk.PhotoImage(pil_image)
                
                logo_label = ttk.Label(main_frame, image=self.tk_image)
                logo_label.pack(pady=(0, 5))
            except Exception as e:
                print(f"Błąd ładowania logo: {e}") 

        # 4. Dodanie Treści
        
        # Tytuł
        title_label = ttk.Label(main_frame, text=PROGRAM_TITLE, font=("Helvetica", 12, "bold"))
        title_label.pack(pady=(2, 1))
        
        # Wersja
        version_label = ttk.Label(main_frame, text=f"Wersja: {PROGRAM_VERSION} (Data: {PROGRAM_DATE})", font=("Helvetica", 8))
        version_label.pack(pady=1)

        separator_frame = tk.Frame(main_frame, height=1, bg='lightgray')
        separator_frame.pack(fill='x', padx=15, pady=15)
        # Prawa Autorskie (Zmodyfikowano: czcionka 10, bez pogrubienia, dodano zawijanie)
        copy_label = ttk.Label(
        main_frame, 
        text=COPYRIGHT_INFO, 
        font=("Helvetica", 8),              # Czcionka 10, bez pogrubienia
        foreground="black",
        wraplength=250                       # Zawijanie tekstu po osiągnięciu 300 pikseli szerokości
        )
        copy_label.pack(pady=(5, 0))
        
        # 5. Blokowanie
        dialog.wait_window()
    
    def _setup_context_menu(self):
        self.context_menu = tk.Menu(self.master, tearoff=0)
        self._populate_edit_menu(self.context_menu)
    
    def _populate_edit_menu(self, menu_obj):
        menu_obj.add_command(label="Cofnij", command=self.undo, accelerator="Ctrl+Z")
        menu_obj.add_command(label="Ponów", command=self.redo, accelerator="Ctrl+Y")
        menu_obj.add_separator()
        menu_obj.add_command(label="Usuń zaznaczone", command=self.delete_selected_pages, accelerator="Delete/Backspace")
        menu_obj.add_command(label="Wytnij zaznaczone", command=self.cut_selected_pages, accelerator="Ctrl+X")
        menu_obj.add_command(label="Kopiuj zaznaczone", command=self.copy_selected_pages, accelerator="Ctrl+C")
        menu_obj.add_command(label="Wklej przed", command=self.paste_pages_before, accelerator="Ctrl+Shift+V")
        menu_obj.add_command(label="Wklej po", command=self.paste_pages_after, accelerator="Ctrl+V")
        menu_obj.add_separator()
        menu_obj.add_command(label="Duplikuj stronę", command=self.duplicate_selected_page, accelerator="Ctrl+D")
        menu_obj.add_separator()
        menu_obj.add_command(label="Wstaw nową stronę przed", command=self.insert_blank_page_before, accelerator="Ctrl+Shift+N")
        menu_obj.add_command(label="Wstaw nową stronę po", command=self.insert_blank_page_after, accelerator="Ctrl+N")
        #menu_obj.add_separator()
        #menu_obj.add_command(label="Obróć w lewo (-90°)", command=lambda: self.rotate_selected_page(-90))
        #menu_obj.add_command(label="Obróć w prawo (+90°)", command=lambda: self.rotate_selected_page(90))

    def _populate_modifications_menu(self, menu_obj):
        
        # OBRACANIE
        menu_obj.add_command(label="Obróć w lewo (-90°)", command=lambda: self.rotate_selected_page(-90), state=tk.DISABLED, accelerator="Ctrl+Shift+(-)")
        menu_obj.add_command(label="Obróć w prawo (+90°)", command=lambda: self.rotate_selected_page(90), state=tk.DISABLED, accelerator="Ctrl+Shift+(+)")
        menu_obj.add_separator()
    
        # === NOWA OPCJA: USUWANIE NUMERÓW STRON ===
        menu_obj.add_command(label="Przesuń zawartość zaznaczonych stron...",command=self.shift_page_content, state=tk.DISABLED, accelerator="F5")
        menu_obj.add_command(label="Usuń numery stron...", command=self.remove_page_numbers, state=tk.DISABLED, accelerator="F6")
        menu_obj.add_command(label="Wstaw numery stron...", command=self.insert_page_numbers, state=tk.DISABLED, accelerator="F7")
     
    # ... (resztę modyfikacji) ...
    
        # ODRACANIE KOLEJNOŚCI
        menu_obj.add_separator()
        menu_obj.add_command(label="Przytnij zaznaczone strony...", command=self.apply_page_crop_resize_dialog, state=tk.DISABLED, accelerator="F8")
        menu_obj.add_command(label="Odwróć kolejność wszystkich stron", command=self._reverse_pages, state=tk.DISABLED)
    
    def _setup_key_bindings(self):
        self.master.bind('<Control-x>', lambda e: self.cut_selected_pages())
        self.master.bind('<Control-c>', lambda e: self.copy_selected_pages())
        self.master.bind('<Control-d>', lambda e: self.duplicate_selected_page())
        self.master.bind('<Control-z>', lambda e: self.undo())
        self.master.bind('<Control-y>', lambda e: self.redo())
        self.master.bind('<Delete>', lambda e: self.delete_selected_pages())
        self.master.bind('<BackSpace>', lambda e: self.delete_selected_pages())
        self.master.bind('<Control-a>', lambda e: self._select_all())
        self.master.bind('<F4>', lambda e: self._select_all())
        self.master.bind('<F1>', lambda e: self._select_odd_pages())
        self.master.bind('<F2>', lambda e: self._select_even_pages())
        self.master.bind('<Control-Shift-minus>', lambda e: self.rotate_selected_page(-90))
        self.master.bind('<Control-Shift-plus>', lambda e: self.rotate_selected_page(+90))
        self.master.bind('<F5>', lambda e: self.shift_page_content())
        self.master.bind('<F6>', lambda e: self.remove_page_numbers())
        self.master.bind('<F7>', lambda e: self.insert_page_numbers())
        self.master.bind('<F8>', lambda e: self.apply_page_crop_resize_dialog())
        
        self.master.bind('<Control-F1>', lambda e: self._select_portrait_pages())
        self.master.bind('<Control-F2>', lambda e: self._select_landscape_pages())
        self.master.bind('<Control-v>', lambda e: self.paste_pages_after())
        self.master.bind('<Control-Shift-V>', lambda e: self.paste_pages_before())
        self.master.bind('<Control-n>', lambda e: self.insert_blank_page_after())
        self.master.bind('<Control-Shift-N>', lambda e: self.insert_blank_page_before())
        # === SKRÓTY DLA EKSPORTU ===
        # Ctrl+E dla Eksportu stron do nowego PDF
        self.master.bind('<Control-e>', lambda e: self.extract_selected_pages())
        # Ctrl+Shift+E dla Eksportu stron jako obrazów PNG
        self.master.bind('<Control-Shift-E>', lambda e: self.export_selected_pages_to_image())
        # ===========================
        self._setup_focus_logic()
        self.master.bind('<Control-o>', lambda e: self.open_pdf())
        self.master.bind('<Control-s>', lambda e: self.save_document())
        # Zmienione skróty
        self.master.bind('<Control-Shift-I>', lambda e: self.import_image_to_new_page()) # Ctrl+K dla obrazu
        self.master.bind('<Control-i>', lambda e: self.import_pdf_after_active_page()) # Ctrl+I dla PDF
        
    def _setup_focus_logic(self):
        self.master.bind('<Escape>', lambda e: self._clear_all_selection())
        self.master.bind('<space>', lambda e: self._toggle_selection_space())
        self.master.bind('<Left>', lambda e: self._move_focus_and_scroll(-1))
        self.master.bind('<Right>', lambda e: self._move_focus_and_scroll(1))
        self.master.bind('<Up>', lambda e: self._move_focus_and_scroll(-self.target_num_cols))
        self.master.bind('<Down>', lambda e: self._move_focus_and_scroll(self.target_num_cols))

    def _select_all(self):
        if self.pdf_document:
            all_pages = set(range(len(self.pdf_document)))
            if self.selected_pages == all_pages:
                self.selected_pages.clear()
                self._update_status("Anulowano zaznaczenie wszystkich stron (Ctrl+A).")
            else:
                self.selected_pages = all_pages
                self._update_status(f"Zaznaczono wszystkie strony ({len(self.pdf_document)}).")
            if self.pdf_document.page_count > 0:
                self.active_page_index = 0
            self.update_selection_display()
            self.update_focus_display()
            
    def _select_range(self, start_index, end_index):
        if not self.pdf_document: return
        if start_index > end_index:
            start_index, end_index = end_index, start_index
        self.selected_pages.clear() 
        for i in range(start_index, end_index + 1):
            if i < len(self.pdf_document):
                self.selected_pages.add(i)
        self.update_selection_display()
        self.active_page_index = end_index 
        
    def _clear_all_selection(self):
        if self.pdf_document:
            self.active_page_index = 0
        if self.selected_pages:
            self.selected_pages.clear()
            self.update_selection_display()
            self.update_focus_display()
            self._update_status("Anulowano zaznaczenie wszystkich stron (ESC).")
            
    def _toggle_selection_space(self):
        if self.pdf_document and self.pdf_document.page_count > 0:
            if self.active_page_index in self.selected_pages:
                self.selected_pages.remove(self.active_page_index)
            else:
                self.selected_pages.add(self.active_page_index)
            self.update_selection_display()

    def _get_page_frame(self, index) -> Optional['ThumbnailFrame']:
        return self.thumb_frames.get(index)

    def _move_focus_and_scroll(self, delta: int):
        if not self.pdf_document: return
        new_index = self.active_page_index + delta
        max_index = len(self.pdf_document) - 1
        if 0 <= new_index <= max_index:
            self.active_page_index = new_index
            self.update_focus_display(hide_mouse_focus=False)  
            frame = self._get_page_frame(self.active_page_index)
            if frame:
                self.canvas.update_idletasks()
                y1 = frame.winfo_y()
                y2 = frame.winfo_y() + frame.winfo_height()
                bbox = self.canvas.bbox("all")
                total_height = bbox[3] if bbox is not None else 1
                norm_top = y1 / total_height
                norm_bottom = y2 / total_height
                current_top, current_bottom = self.canvas.yview()
                if norm_top < current_top:
                    self.canvas.yview_moveto(norm_top)
                elif norm_bottom > current_bottom:
                    scroll_pos = norm_bottom - (current_bottom - current_top)
                    self.canvas.yview_moveto(scroll_pos)
                        
    def _handle_lpm_click(self, page_index, event):
        is_shift_pressed = (event.state & 0x1) != 0 
        if is_shift_pressed and self.selected_pages:
            last_active = self.active_page_index
            self._select_range(last_active, page_index)
        else:
            self._toggle_selection_lpm(page_index)
        self.active_page_index = page_index
        self.update_focus_display(hide_mouse_focus=True)

    def _toggle_selection_lpm(self, page_index):
        if page_index in self.selected_pages:
            self.selected_pages.remove(page_index)
        else:
            self.selected_pages.add(page_index)
        self.update_selection_display()

    def update_tool_button_states(self):
        doc_loaded = self.pdf_document is not None
        has_selection = len(self.selected_pages) > 0
        has_single_selection = len(self.selected_pages) == 1
        has_undo = len(self.undo_stack) > 0
        has_redo = len(self.redo_stack) > 0
        has_clipboard_content = self.clipboard is not None
        
        delete_state = tk.NORMAL if doc_loaded and has_selection else tk.DISABLED
        insert_state = tk.NORMAL if doc_loaded and has_single_selection else tk.DISABLED
        paste_enable_state = tk.NORMAL if has_clipboard_content and doc_loaded and (len(self.selected_pages) <= 1) else tk.DISABLED 
        rotate_state = tk.NORMAL if doc_loaded and has_selection else tk.DISABLED
        undo_state = tk.NORMAL if has_undo else tk.DISABLED
        redo_state = tk.NORMAL if has_redo else tk.DISABLED
        import_state = tk.NORMAL if doc_loaded else tk.DISABLED 
        select_state = tk.NORMAL if doc_loaded else tk.DISABLED
        reverse_state = tk.NORMAL if doc_loaded else tk.DISABLED
         
        # 1. Aktualizacja przycisków w panelu głównym
        self.undo_button.config(state=undo_state)
        self.redo_button.config(state=redo_state)
        self.delete_button.config(state=delete_state)
        self.cut_button.config(state=delete_state)
        self.copy_button.config(state=delete_state)
        self.import_button.config(state=import_state) 
        self.image_import_button.config(state=import_state) 
        self.extract_button.config(state=delete_state) 
        self.export_image_button.config(state=delete_state) 
        self.insert_before_button.config(state=insert_state)
        self.insert_after_button.config(state=insert_state)
        self.paste_before_button.config(state=paste_enable_state)
        self.paste_after_button.config(state=paste_enable_state)
        self.rotate_left_button.config(state=rotate_state)
        self.rotate_right_button.config(state=rotate_state)
        self.shift_content_btn.config(state=delete_state)
        self.remove_nums_btn.config(state=delete_state)
        self.add_nums_btn.config(state=delete_state)
        
        if doc_loaded:
             zoom_in_state = tk.NORMAL if self.target_num_cols > self.min_cols else tk.DISABLED
             zoom_out_state = tk.NORMAL if self.target_num_cols < self.max_cols else tk.DISABLED
        else:
             zoom_in_state = tk.DISABLED
             zoom_out_state = tk.DISABLED
             
        self.zoom_in_button.config(state=zoom_in_state)
        self.zoom_out_button.config(state=zoom_out_state)

        # 2. Aktualizacja pozycji w menu
        menus_to_update = [self.file_menu, self.edit_menu, self.select_menu]
        if hasattr(self, 'context_menu'):
            menus_to_update.append(self.context_menu)
        if hasattr(self, 'modifications_menu'):
            menus_to_update.append(self.modifications_menu)
        
        menu_state_map = {
            "Importuj strony z PDF...": import_state, 
            "Importuj obraz na nową stronę...": import_state,
            "Eksportuj strony do PDF...": delete_state,
            "Eksportuj strony jako obrazy PNG...": delete_state,            
            "Cofnij": undo_state,
            "Ponów": redo_state,
            "Wszystkie strony": select_state,
            "Strony nieparzyste": select_state,
            "Strony parzyste": select_state,
            "Strony pionowe": select_state,
            "Strony poziome": select_state,
            "Wytnij zaznaczone": delete_state,
            "Kopiuj zaznaczone": delete_state,
            "Usuń zaznaczone": delete_state,
            "Wklej przed": paste_enable_state,
            "Wklej po": paste_enable_state,
            "Duplikuj stronę": insert_state,
            "Wstaw nową stronę przed": insert_state,
            "Wstaw nową stronę po": insert_state,
            "Obróć w lewo (-90°)": rotate_state,
            "Obróć w prawo (+90°)": rotate_state,
            "Odwróć kolejność wszystkich stron": reverse_state,
            "Usuń numery stron...": delete_state, 
            "Wstaw numery stron...": delete_state, 
            "Przesuń zawartość zaznaczonych stron...": delete_state,
            "Przytnij zaznaczone strony...": delete_state
        }
        
        for menu in menus_to_update:
            for label, state in menu_state_map.items():
                try:
                    menu.entryconfig(label, state=state)
                except tk.TclError:
                    continue
    
    def _setup_drag_and_drop_file(self):
        pass

    # --- Metody obsługi plików i edycji (Ze zmianami w import_image_to_new_page) ---
    def open_pdf(self, event=None, filepath=None):
        if not filepath:
            filepath = filedialog.askopenfilename(filetypes=[("Pliki PDF", "*.pdf")])
            if not filepath:  
                self._update_status("Anulowano otwieranie pliku.")
                return

        try:
            if self.pdf_document: self.pdf_document.close()
            self.pdf_document = fitz.open(filepath)
            self.selected_pages = set()
            self.tk_images = {}
            self.undo_stack.clear()
            self.redo_stack.clear()
            self.clipboard = None
            self.pages_in_clipboard_count = 0
            self.active_page_index = 0
            self.thumb_frames.clear()
            self._save_state_to_undo()
            for widget in list(self.scrollable_frame.winfo_children()):
                widget.destroy()
            self.target_num_cols = 4  
            self._reconfigure_grid()  
            self._update_status(f"Wczytano {len(self.pdf_document)} stron. Gotowy do edycji.")
            self.save_button_icon.config(state=tk.NORMAL)
            self.file_menu.entryconfig("Zapisz jako...", state=tk.NORMAL)
            self.update_tool_button_states()
            self.update_focus_display()
            
        except Exception as e:
            self._update_status(f"BŁĄD: Nie udało się wczytać pliku PDF: {e}")
            self.pdf_document = None
            self.save_button_icon.config(state=tk.DISABLED)
            self.file_menu.entryconfig("Zapisz jako...", state=tk.DISABLED)
            self.update_tool_button_states()

    def import_pdf_after_active_page(self, event=None): # Dodano event=None dla skrótu
        if not self.pdf_document:
            self._update_status("BŁĄD: Otwórz najpierw dokument PDF.")
            return
        import_path = filedialog.askopenfilename(
            title="Wybierz plik PDF do zaimportowania",
            filetypes=[("Pliki PDF", "*.pdf")]
        )
        if not import_path:
            self._update_status("Anulowano importowanie pliku.")
            return
            
        imported_doc = None
        selected_indices = None 
        try:
            imported_doc = fitz.open(import_path)
            max_pages = len(imported_doc)
            self.master.update_idletasks() 
            dialog = EnhancedPageRangeDialog(self.master, "Ustawienia importu PDF", imported_doc)
            selected_indices = dialog.result 
            if selected_indices is None or not selected_indices:
                self._update_status("Anulowano importowanie lub nie wybrano stron.")
                return
            insert_index = len(self.pdf_document)
            if len(self.selected_pages) == 1:
                page_index = list(self.selected_pages)[0]
                insert_index = page_index + 1 
            elif len(self.selected_pages) > 1:
                 insert_index = max(self.selected_pages) + 1
            else:
                 insert_index = len(self.pdf_document)
                 
            self._save_state_to_undo()
            num_inserted = len(selected_indices)
            temp_doc_for_insert = fitz.open()
            for page_index_to_import in selected_indices:
                 temp_doc_for_insert.insert_pdf(imported_doc, from_page=page_index_to_import, to_page=page_index_to_import)
            self.pdf_document.insert_pdf(temp_doc_for_insert, start_at=insert_index)
            temp_doc_for_insert.close()

            self.selected_pages.clear()
            self.tk_images.clear()
            for widget in list(self.scrollable_frame.winfo_children()): widget.destroy()
            self.thumb_frames.clear()

            self._reconfigure_grid()
            self.update_tool_button_states()
            self.update_focus_display()
            self._update_status(f"Zaimportowano {num_inserted} wybranych stron i wstawiono w pozycji {insert_index}.")

        except Exception as e:
            self._update_status(f"BŁĄD Importowania: Nie udało się wczytać lub wstawić pliku: {e}")
            
        finally:
             if imported_doc and not imported_doc.is_closed:
                  imported_doc.close()

    def import_image_to_new_page(self):
        if not self.pdf_document:
            messagebox.showerror("Błąd", "Najpierw otwórz dokument PDF.")
            return

        image_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.tif;*.tiff")],
            title="Wybierz plik obrazu do importu"
        )
        
        if not image_path:
            return

        # 1. Otwarcie dialogu i pobranie ustawień
        dialog = ImageImportSettingsDialog(self.master, "Ustawienia importu obrazu", image_path)
        settings = dialog.result
        
        if not settings:
            return
            
        scaling_mode = settings['scaling_mode']
        alignment = settings['alignment']
        scale_factor = settings['scale_factor']
        page_orientation = settings['page_orientation']
        
        try:
            # Wczytanie obrazu za pomocą PIL dla wymiarów
            img = Image.open(image_path)
            image_width_px, image_height_px = img.size
            image_dpi = settings.get('image_dpi', 96)
            
            # Konwersja wymiarów obrazu z pikseli na punkty PDF
            image_width_points = (image_width_px / image_dpi) * 72
            image_height_points = (image_height_px / image_dpi) * 72
            
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można wczytać obrazu: {e}")
            return
        
        # 2. Ustalanie wymiarów nowej strony docelowej (A4) i Tworzenie tymczasowego dokumentu fitz
        if page_orientation == "PIONOWO":
            page_w, page_h = A4_WIDTH_POINTS, A4_HEIGHT_POINTS
        else:
            page_w, page_h = A4_HEIGHT_POINTS, A4_WIDTH_POINTS
            
        # Tworzymy NOWY, TYMCZASOWY dokument fitz, w którym umieścimy obraz (wzorzec z Twojego działającego kodu)
        imported_doc = fitz.open()
        try:
            imported_page = imported_doc.new_page(
                -1, 
                width=page_w, 
                height=page_h
            )
        except Exception as e:
            messagebox.showerror("Błąd inicjalizacji fitz", f"Nie udało się utworzyć tymczasowej strony PDF: {e}")
            return

        # 3. Obliczanie Skalowania
        if scaling_mode == "ORYGINALNY":
            # Używa scale_factor jako końcowego współczynnika (np. 1.0 dla 100%, 0.5 dla 50%)
            scale = scale_factor
            
        elif scaling_mode == "SKALA":
            # W tym trybie również używamy scale_factor jako końcowego współczynnika
            scale = scale_factor
            
        elif scaling_mode == "DOPASUJ":
            scale_margin_points = MM_TO_POINTS * 50 # 50mm marginesu (25mm z każdej strony)
            scale_w = (page_w - scale_margin_points) / image_width_points
            scale_h = (page_h - scale_margin_points) / image_height_points
            scale = min(scale_w, scale_h)
        else:
            # Domyślnie 100% oryginalnego rozmiaru (jeśli DPI jest poprawne)
            scale = 1.0

        # ZAWSZE używaj obliczonego współczynnika 'scale' do określenia ostatecznych wymiarów
        final_w = image_width_points * scale
        final_h = image_height_points * scale
        # 4. Obliczanie Pozycji (Wyrównanie)
        offset_mm = 25.0
        offset_points = offset_mm * MM_TO_POINTS # ~70.87 punktów (25 mm)
        
        if alignment == "SRODEK":
            x_start = (page_w - final_w) / 2
            y_start = (page_h - final_h) / 2
            
        elif alignment == "GORA":
            # !!! ZAMIANA: Wstawiamy przy dolnej krawędzi (bo Twoja aplikacja interpretuje to odwrotnie)
            x_start = (page_w - final_w) / 2
            y_start = offset_points  # Wstawia obraz 25 mm od dolnej krawędzi
            
        elif alignment == "DOL":
            # !!! ZAMIANA: Wstawiamy przy górnej krawędzi (bo Twoja aplikacja interpretuje to odwrotnie)
            x_start = (page_w - final_w) / 2
            y_start = page_h - final_h - offset_points  # Wstawia obraz 25 mm od górnej krawędzi
            
        else: # Domyślnie Lewy Górny (lub jakakolwiek inna domyślna logika)
            x_start = offset_points 
            y_start = page_h - final_h - offset_points 
        
        # Określenie prostokąta docelowego dla fitz: Rect(x0, y0, x1, y1)
        rect = fitz.Rect(x_start, y_start, x_start + final_w, y_start + final_h)

        # 5. Wklejenie obrazu do tymczasowej strony fitz
        try:
            imported_page.insert_image(rect, filename=image_path)
            
            # 6. Określenie pozycji wstawienia w głównym dokumencie
            
            # Wzorzec przejęty z Twojego import_pdf_after_active_page:
            insert_index = len(self.pdf_document)
            if len(self.selected_pages) == 1:
                page_index = list(self.selected_pages)[0]
                insert_index = page_index + 1
            elif len(self.selected_pages) > 1:
                insert_index = max(self.selected_pages) + 1
            else:
                insert_index = len(self.pdf_document)
            
            # Zapis stanu przed modyfikacją głównego dokumentu
            self._save_state_to_undo()
            
            # *** KLUCZOWA ZMIANA: Wstawienie tymczasowego dokumentu do głównego ***
            # Wykorzystujemy fitz.Document.insert_pdf() w taki sam sposób jak w Twojej działającej funkcji:
            self.pdf_document.insert_pdf(
                imported_doc, 
                from_page=0, 
                to_page=0,  # Wstawiamy tylko pierwszą stronę (z indeksem 0) z naszego tymczasowego dokumentu
                start_at=insert_index # Wstawiamy na docelową pozycję w głównym dokumencie
            )
            # --------------------------------------------------------------------
            
            # Aktualizacja aktywnej strony po wstawieniu
            self.active_page_index = insert_index
            
            # 7. Odświeżenie widoku i statusu
            self.selected_pages.clear()
            self.tk_images.clear()
            for widget in list(self.scrollable_frame.winfo_children()): widget.destroy()
            self.thumb_frames.clear()
            
            self._reconfigure_grid()
            self.update_tool_button_states()
            self.update_focus_display()
            
            self.status_bar.config(text=f"Zaimportowano obraz jako stronę na pozycji {insert_index + 1}. Aktualna liczba stron: {len(self.pdf_document)}.")
            
        except Exception as e:
            messagebox.showerror("Błąd Wklejania", f"Nie udało się wkleić obrazu: {e}")
            
        finally:
            # Zamknięcie tymczasowego dokumentu (ważne dla uniknięcia wycieków pamięci)
            if imported_doc and not imported_doc.is_closed:
                imported_doc.close()
            
    def _update_status(self, message):
        self.status_bar.config(text=message, fg="black")
            
    def _save_state_to_undo(self):
        """Zapisuje bieżący stan dokumentu na stosie undo i czyści stos redo."""
        if self.pdf_document:
            buffer = self.pdf_document.write()
            self.undo_stack.append(buffer)
            if len(self.undo_stack) > self.max_stack_size:
                self.undo_stack.pop(0)
            # Każda nowa modyfikacja czyści stos redo
            self.redo_stack.clear()
            self.update_tool_button_states()
        else:
            self.undo_stack.clear()
            self.redo_stack.clear()
            self.update_tool_button_states()
            
    def _get_page_bytes(self, page_indices: Set[int]) -> bytes:
        temp_doc = fitz.open()
        sorted_indices = sorted(list(page_indices))
        for index in sorted_indices:
            temp_doc.insert_pdf(self.pdf_document, from_page=index, to_page=index)
        page_bytes = temp_doc.write()
        temp_doc.close()
        return page_bytes
    
    def copy_selected_pages(self):
        if not self.pdf_document or not self.selected_pages:
            self._update_status("BŁĄD: Zaznacz strony do skopiowania.")
            return
        try:
            self.clipboard = self._get_page_bytes(self.selected_pages)
            self.pages_in_clipboard_count = len(self.selected_pages)
            self.selected_pages.clear()
            self.update_selection_display()
            self._update_status(f"Skopiowano {self.pages_in_clipboard_count} stron do schowka.")
        except Exception as e:
            self._update_status(f"BŁĄD Kopiowania: {e}")
            
    def cut_selected_pages(self):
        if not self.pdf_document or not self.selected_pages:
            self._update_status("BŁĄD: Zaznacz strony do wycięcia.")
            return
        try:
            self._save_state_to_undo()
            self.clipboard = self._get_page_bytes(self.selected_pages)
            self.pages_in_clipboard_count = len(self.selected_pages)
            pages_to_delete = sorted(list(self.selected_pages), reverse=True)
            for page_index in pages_to_delete:
                self.pdf_document.delete_page(page_index)
            deleted_count = len(self.selected_pages)
            self.selected_pages.clear()
            self.tk_images.clear()
            for widget in list(self.scrollable_frame.winfo_children()): widget.destroy()
            self.thumb_frames.clear()  
            self._reconfigure_grid()
            self.update_tool_button_states()
            self._update_status(f"Wycięto {deleted_count} stron i skopiowano do schowka.")
        except Exception as e:
            self._update_status(f"BŁĄD Wycinania: {e}")
            
    def paste_pages_before(self):
        self._handle_paste_operation(before=True)

    def paste_pages_after(self):
        self._handle_paste_operation(before=False)
        
    def _handle_paste_operation(self, before: bool):
        if not self.pdf_document or not self.clipboard:
            self._update_status("BŁĄD: Schowek jest pusty.")
            return
            
        if len(self.selected_pages) > 1:
             self._update_status("BŁĄD: Do wklejenia po/przed, zaznacz dokładnie jedną stronę, lub w ogóle by wkleić na końcu.")
             return
            
        target_index = len(self.pdf_document)
        if len(self.selected_pages) == 1:
            page_index = list(self.selected_pages)[0]
            if before:
                target_index = page_index  
            else:
                target_index = page_index + 1  
            
        self._perform_paste(target_index)

    def _perform_paste(self, target_index: int):
        try:
            self._save_state_to_undo()
            temp_doc = fitz.open("pdf", self.clipboard)
            self.pdf_document.insert_pdf(temp_doc, start_at=target_index)
            num_inserted = len(temp_doc)
            temp_doc.close()
            self.clipboard = None
            self.pages_in_clipboard_count = 0
            self.selected_pages.clear()
            self.tk_images.clear()
            for widget in list(self.scrollable_frame.winfo_children()): widget.destroy()
            self.thumb_frames.clear()  
            self._reconfigure_grid()
            self.update_tool_button_states()
            self._update_status(f"Wklejono {num_inserted} stron w pozycji {target_index}.")
        except Exception as e:
            self._update_status(f"BŁĄD Wklejania: {e}")
            
    def delete_selected_pages(self, event=None, save_state: bool = True): 
        if not self.pdf_document or not self.selected_pages:  
            self._update_status("BŁĄD: Brak zaznaczonych stron do usunięcia.")
            return
        pages_to_delete = sorted(list(self.selected_pages), reverse=True)
        deleted_count = 0
        try:
            if save_state:
                self._save_state_to_undo()
            for page_index in pages_to_delete:
                self.pdf_document.delete_page(page_index)
                deleted_count += 1
            self.selected_pages.clear()
            self.tk_images.clear()
            for widget in list(self.scrollable_frame.winfo_children()): widget.destroy()
            self.thumb_frames.clear()  
            self.total_pages = len(self.pdf_document)
            self.active_page_index = min(self.active_page_index, self.total_pages - 1)
            self.active_page_index = max(0, self.active_page_index)
            self._reconfigure_grid()  
            self.update_tool_button_states()
            self.update_focus_display()  
            if save_state:
                 self._update_status(f"Usunięto {deleted_count} stron. Aktualna liczba stron: {self.total_pages}.")
        except Exception as e:
            self._update_status(f"BŁĄD: Wystąpił błąd podczas usuwania: {e}")

    def extract_selected_pages(self):
        if not self.pdf_document or not self.selected_pages:
            self._update_status("BŁĄD: Zaznacz strony, które chcesz wyodrębnić do nowego pliku.")
            return
        filepath = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("Pliki PDF", "*.pdf")],
            title="Zapisz wyodrębnione strony jako nowy PDF..."
        )
        if not filepath:
            self._update_status("Anulowano ekstrakcję stron.")
            return
        try:
            page_bytes = self._get_page_bytes(self.selected_pages)
            num_extracted = len(self.selected_pages)
            with open(filepath, "wb") as f:
                f.write(page_bytes)
            self._update_status(f"Pomyślnie wyodrębniono {num_extracted} stron do: {filepath}")
        except Exception as e:
            self._update_status(f"BŁĄD Eksportu: Nie udało się zapisać nowego pliku: {e}")

    def undo(self):
        """Cofnij ostatnią operację - przywraca stan ze stosu undo."""
        if len(self.undo_stack) == 0:
            self._update_status("Brak operacji do cofnięcia!")
            return

        # Zapisz bieżący stan na stos redo
        if self.pdf_document:
            current_state = self.pdf_document.write()
            self.redo_stack.append(current_state)
            if len(self.redo_stack) > self.max_stack_size:
                self.redo_stack.pop(0)

        # Pobierz poprzedni stan ze stosu undo
        previous_state_bytes = self.undo_stack.pop()
        
        try:
            if self.pdf_document: 
                self.pdf_document.close()
            self.pdf_document = fitz.open("pdf", previous_state_bytes)
            self.selected_pages.clear()
            self.tk_images.clear()
            self.thumb_frames.clear()
            for widget in list(self.scrollable_frame.winfo_children()):  
                widget.destroy()

            self.active_page_index = min(self.active_page_index, len(self.pdf_document) - 1)
            self._reconfigure_grid()  
            self.update_tool_button_states()
            self.update_focus_display()
            self._update_status("Cofnięto ostatnią operację.")
        except Exception as e:
            self._update_status(f"BŁĄD: Nie udało się cofnąć operacji: {e}")
            self.pdf_document = None
            self.update_tool_button_states()
            
    def redo(self):
        """Ponów cofniętą operację - przywraca stan ze stosu redo."""
        if len(self.redo_stack) == 0:
            self._update_status("Brak operacji do ponowienia!")
            return

        # Zapisz bieżący stan na stos undo
        if self.pdf_document:
            current_state = self.pdf_document.write()
            self.undo_stack.append(current_state)
            if len(self.undo_stack) > self.max_stack_size:
                self.undo_stack.pop(0)

        # Pobierz następny stan ze stosu redo
        next_state_bytes = self.redo_stack.pop()
        
        try:
            if self.pdf_document:
                self.pdf_document.close()
            self.pdf_document = fitz.open("pdf", next_state_bytes)
            self.selected_pages.clear()
            self.tk_images.clear()
            self.thumb_frames.clear()
            for widget in list(self.scrollable_frame.winfo_children()):
                widget.destroy()

            self.active_page_index = min(self.active_page_index, len(self.pdf_document) - 1)
            self._reconfigure_grid()
            self.update_tool_button_states()
            self.update_focus_display()
            self._update_status("Ponowiono operację.")
        except Exception as e:
            self._update_status(f"BŁĄD: Nie udało się ponowić operacji: {e}")
            self.pdf_document = None
            self.update_tool_button_states()
            
    def save_document(self):
        if not self.pdf_document: return
        filepath = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("Pliki PDF", "*.pdf")],
            title="Zapisz zmodyfikowany PDF jako..."
        )
        if not filepath:  
            self._update_status("Anulowano zapisywanie.")
            return
        try:
            self.pdf_document.save(filepath, garbage=4, clean=True, pretty=True)  
            self._update_status(f"Dokument pomyślnie zapisany jako: {filepath}")
            # Po zapisaniu czyścimy stosy undo/redo
            self.undo_stack.clear()
            self.redo_stack.clear()
            self.update_tool_button_states() 
        except Exception as e:
            self._update_status(f"BŁĄD: Nie udało się zapisać pliku: {e}")
            
    def rotate_selected_page(self, angle):
        if not self.pdf_document or not self.selected_pages: 
            self._update_status("BŁĄD: Zaznacz strony do obrotu.")
            return
        pages_to_rotate = sorted(list(self.selected_pages))
        try:
            self._save_state_to_undo()
            rotated_count = 0
            for page_index in pages_to_rotate:
                page = self.pdf_document.load_page(page_index)
                current_rotation = page.rotation
                new_rotation = (current_rotation + angle) % 360
                page.set_rotation(new_rotation)
                rotated_count += 1
            self.tk_images.clear()
            for widget in list(self.scrollable_frame.winfo_children()): widget.destroy()
            self.thumb_frames.clear()
            self._reconfigure_grid()  
            self.update_tool_button_states()
            self.update_focus_display()
            self._update_status(f"Obrócono {rotated_count} stron o {angle} stopni.")
        except Exception as e:
            self._update_status(f"BŁĄD: Wystąpił błąd podczas obracania: {e}")

    def insert_blank_page_before(self):
           self._handle_insert_operation(before=True)

    def insert_blank_page_after(self):
        self._handle_insert_operation(before=False)
        
    def _handle_insert_operation(self, before: bool):
        if not self.pdf_document or len(self.selected_pages) != 1:  
             self._update_status("BŁĄD: Zaznacz dokładnie jedną stronę, aby wstawić obok niej nową.")
             return
        width, height = (595.276, 841.89)
        page_index = list(self.selected_pages)[0]
        try:
            # Użycie wymiarów istniejącej strony
            rect = self.pdf_document[page_index].rect
            width = rect.width
            height = rect.height  
        except Exception:
            pass # Pozostawienie domyślnych A4
        
        if before:
              target_page = page_index
        else:
              target_page = page_index + 1
              
        try:
            self._save_state_to_undo()
            self.pdf_document.insert_page(
                pno=target_page,  
                width=width,  
                height=height
            )
            self.selected_pages.clear()
            self.tk_images.clear()
            for widget in list(self.scrollable_frame.winfo_children()): widget.destroy()
            self.thumb_frames.clear()
            self._reconfigure_grid()  
            self.update_tool_button_states()
            self.update_focus_display()
            self._update_status(f"Wstawiono nową, pustą stronę. Aktualna liczba stron: {len(self.pdf_document)}.")
        except Exception as e:
            self._update_status(f"BŁĄD: Wystąpił błąd podczas wstawiania: {e}")
    
    def duplicate_selected_page(self):
        """Duplikuje aktualnie zaznaczoną stronę i wstawia ją zaraz po oryginale."""
        if not self.pdf_document or len(self.selected_pages) != 1:
            self._update_status("BŁĄD: Zaznacz dokładnie jedną stronę, aby ją zduplikować.")
            return
        
        page_index = list(self.selected_pages)[0]
        
        try:
            self._save_state_to_undo()
            
            # Wstawienie kopii strony zaraz po oryginale
            self.pdf_document.insert_pdf(
                self.pdf_document,
                from_page=page_index,
                to_page=page_index,
                start_at=page_index + 1
            )
            
            # Odświeżenie GUI
            self.selected_pages.clear()
            self.tk_images.clear()
            for widget in list(self.scrollable_frame.winfo_children()): 
                widget.destroy()
            self.thumb_frames.clear()
            self._reconfigure_grid()
            self.update_tool_button_states()
            self.update_focus_display()
            
            self._update_status(f"Zduplikowano stronę {page_index + 1}. Aktualna liczba stron: {len(self.pdf_document)}.")
        except Exception as e:
            self._update_status(f"BŁĄD: Wystąpił błąd podczas duplikowania strony: {e}")
            
    # --- Metody obsługi widoku/GUI (Bez zmian) ---
    def _on_mousewheel(self, event):
        current_y = self.canvas.yview()[0]
        if event.num == 4 or event.delta > 0:  
            if current_y <= 0.001:  
                return  
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:  
            self.canvas.yview_scroll(1, "units")
            
    def zoom_in(self):
        if self.pdf_document:
            self.target_num_cols = max(self.min_cols, self.target_num_cols - 1)
            self._reconfigure_grid()
            self.update_tool_button_states()  

    def zoom_out(self):
        if self.pdf_document:
            self.target_num_cols = min(self.max_cols, self.target_num_cols + 1)
            self._reconfigure_grid()
            self.update_tool_button_states()  

    def _reconfigure_grid(self, event=None):
        if not self.pdf_document:  
             self.canvas.config(scrollregion=self.canvas.bbox("all"))
             return

        self.master.update_idletasks()
        actual_canvas_width = self.canvas.winfo_width()
        scrollbar_safety = 25  
        available_width = max(100, actual_canvas_width - scrollbar_safety)  
        internal_padding = self.THUMB_PADDING  
        min_thumb_size = self.min_zoom_width
        min_required_col_size = min_thumb_size + internal_padding  
        calculated_num_cols = int((available_width - internal_padding) / min_required_col_size)
        num_cols = self.target_num_cols  
        if num_cols > calculated_num_cols:
            num_cols = calculated_num_cols
            self.target_num_cols = max(self.min_cols, num_cols)
        num_cols = max(self.min_cols, min(self.max_cols, num_cols))
        total_padding_width = (num_cols + 1) * internal_padding
        space_for_thumbs = available_width - total_padding_width
        theoretical_width = space_for_thumbs / num_cols
        final_column_width = theoretical_width * self.ZOOM_FACTOR
        column_width = max(1, math.floor(final_column_width))  
        self.fixed_thumb_width = column_width  
        
        for widget in list(self.scrollable_frame.grid_slaves()):
             if not isinstance(widget, ThumbnailFrame):
                 widget.destroy()

        for col in range(self.max_cols):  
             if col < num_cols:
                 self.scrollable_frame.grid_columnconfigure(col, weight=1)  
             else:
                 self.scrollable_frame.grid_columnconfigure(col, weight=0)  

        if not self.thumb_frames:
             self._create_widgets(num_cols, column_width)
        else:
             self._update_widgets(num_cols, column_width)
            
        self.scrollable_frame.update_idletasks()  
        bbox = self.canvas.bbox("all")
        if bbox is not None:
              self.canvas.config(scrollregion=(bbox[0], 0, bbox[2], bbox[3]))
              self.canvas.yview_moveto(0.0)  
              self.canvas.coords(self.canvas_window_id, 0, 0)
              self.canvas.yview_moveto(0.0)
        else:
              self.canvas.config(scrollregion=(0, 0, actual_canvas_width, 10))

    def _get_page_size_label(self, page_index):
        if not self.pdf_document: return ""
        page = self.pdf_document.load_page(page_index)
        page_width = page.rect.width
        page_height = page.rect.height
        width_mm = round(page_width / 72 * 25.4)
        page_height_mm = round(page_height / 72 * 25.4)
        
        if 205 <= width_mm <= 215 and 292 <= page_height_mm <= 302: return "A4"
        if 292 <= width_mm <= 302 and 205 <= page_height_mm <= 215: return "A4 (Poziom)"
        if 292 <= width_mm <= 302 and 415 <= page_height_mm <= 425: return "A3"
        return f"{width_mm} x {page_height_mm} mm"


    def _create_widgets(self, num_cols, column_width):
        for i in range(len(self.pdf_document)):
            page_frame = ThumbnailFrame(
                parent=self.scrollable_frame,  
                viewer_app=self,  
                page_index=i,  
                column_width=column_width
            )
            page_frame.grid(row=i // num_cols, column=i % num_cols, padx=self.THUMB_PADDING, pady=self.THUMB_PADDING, sticky="n")  
            self.thumb_frames[i] = page_frame  
            
        self.update_selection_display()
        self.update_focus_display()

    def _update_widgets(self, num_cols, column_width):
        page_frames = [c for c in self.scrollable_frame.grid_slaves() if isinstance(c, ThumbnailFrame)]
        page_frames.sort(key=lambda x: x.page_index)
        frame_bg = "#F5F5F5"  
        for i, page_frame in enumerate(page_frames):
            page_frame.grid(row=i // num_cols, column=i % num_cols, padx=self.THUMB_PADDING, pady=self.THUMB_PADDING, sticky="n")  
            idx = page_frame.page_index
            img_tk = self._render_and_scale(idx, column_width)
            self.tk_images[idx] = img_tk
            page_frame.img_label.config(image=img_tk)
            page_frame.img_label.image = img_tk
            outer_frame_children = page_frame.outer_frame.winfo_children()
            if len(outer_frame_children) > 2:
                  outer_frame_children[1].config(text=f"Strona {idx + 1}", bg=frame_bg)
                  outer_frame_children[2].config(text=self._get_page_size_label(idx), bg=frame_bg)
            
        self.update_selection_display()
        self.update_focus_display()

    
    def _render_and_scale(self, page_index, column_width):
        page = self.pdf_document.load_page(page_index)
        page_width = page.rect.width
        page_height = page.rect.height
        aspect_ratio = page_height / page_width if page_width != 0 else 1
        final_thumb_width = column_width  
        final_thumb_height = int(final_thumb_width * aspect_ratio)
        if final_thumb_width <= 0: final_thumb_width = 1
        if final_thumb_height <= 0: final_thumb_height = 1

        mat = fitz.Matrix(self.render_dpi_factor, self.render_dpi_factor)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        
        img_data = pix.tobytes("ppm")
        image = Image.open(io.BytesIO(img_data))
        
        resized_image = image.resize((final_thumb_width, final_thumb_height), Image.LANCZOS)  
        
        return ImageTk.PhotoImage(resized_image)

    def update_selection_display(self):
        num_selected = len(self.selected_pages)
        
        for frame_index, frame in self.thumb_frames.items():
            inner_frame = frame.outer_frame
            if frame_index in self.selected_pages:
                frame.config(bg=frame.bg_selected)  
                for widget in inner_frame.winfo_children():
                    if isinstance(widget, tk.Label) and widget.cget('bg') != 'white':
                         widget.config(bg=frame.bg_selected)
                inner_frame.config(bg=frame.bg_selected)
            else:
                frame.config(bg=frame.bg_normal)
                for widget in inner_frame.winfo_children():
                    if isinstance(widget, tk.Label) and widget.cget('bg') != 'white':
                         widget.config(bg=frame.bg_normal)
                inner_frame.config(bg=frame.bg_normal)

        self.update_tool_button_states()
        
        if self.pdf_document:
             if num_selected > 0:
                 msg = f"Zaznaczono {num_selected} stron. Użyj przycisków w panelu do edycji."
                 if num_selected == 1:
                      page_num = list(self.selected_pages)[0] + 1
                      msg = f"Zaznaczono 1 stronę (Strona {page_num}). Użyj przycisków w panelu do edycji."
                 self._update_status(msg)
             else:
                 self._update_status(f"Dokument wczytany. Liczba stron: {len(self.pdf_document)}. Zaznacz strony (LPM lub Spacja) do edycji.")
        else:
             self._update_status("Gotowy. Otwórz plik PDF.")

    def update_focus_display(self, hide_mouse_focus: bool = False):
        if not self.pdf_document: return
        for index, frame in self.thumb_frames.items():
            inner_frame = frame.outer_frame
            if index == self.active_page_index and not hide_mouse_focus:
                inner_frame.config(highlightbackground=FOCUS_HIGHLIGHT_COLOR, highlightcolor=FOCUS_HIGHLIGHT_COLOR)
            else:
                inner_frame.config(highlightbackground=frame.bg_normal, highlightcolor=frame.bg_normal)

if __name__ == '__main__':
    try:
        root = tk.Tk()
        app = SelectablePDFViewer(root)
        root.mainloop()
    except ImportError as e:
        print(f"BŁĄD: Wymagane biblioteki nie są zainstalowane. Upewnij się, że masz PyMuPDF (pip install PyMuPDF) i Pillow (pip install Pillow). Szczegóły: {e}")
        sys.exit(1)