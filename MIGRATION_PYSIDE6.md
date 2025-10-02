# Migracja PDFEditor z Tkinter do PySide6

## Przegląd
Ten dokument opisuje migrację aplikacji GRYF PDF Editor z frameworka Tkinter do PySide6 (Qt for Python).

## Status Migracji
- **Plik źródłowy**: PDFEditor.py (3737 linii)
- **Plik docelowy**: PDFEditor_qt.py
- **Branch**: feature/pyside6-migration

## Główne Zmiany

### 1. Importy
**Tkinter → PySide6**
```python
# PRZED:
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# PO:
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QDialog, QMessageBox, QFileDialog,
    QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QLabel, etc.
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QPixmap, QImage, QAction
```

### 2. Klasy Dialogowe

#### PageCropResizeDialog
- `tk.Toplevel` → `QDialog`
- `tk.StringVar` → zwykłe atrybuty string
- `ttk.Radiobutton` → `QRadioButton` + `QButtonGroup`
- `ttk.Entry` → `QLineEdit`
- `pack()` → `QVBoxLayout.addWidget()`
- `grid()` → `QGridLayout.addWidget(row, col)`

#### PageNumberingDialog  
- Dialog modalny z QDialog
- Wszystkie `tk.StringVar`, `tk.BooleanVar` → zwykłe atrybuty Python
- `ttk.Combobox` → `QComboBox`
- `ttk.Checkbutton` → `QCheckBox`

#### PageNumberMarginDialog
- Prosty dialog z pojedynczym polem

#### ShiftContentDialog
- Radio buttons dla kierunków
- LineEdit dla wartości

#### ImageImportSettingsDialog
- Dialog z wyborem orientacji i trybu dopasowania

#### EnhancedPageRangeDialog
- Dialog wyboru zakresu stron

#### MergePageGridDialog
- Bardziej złożony dialog z podglądem
- QHBoxLayout dla układu lewy panel + prawy podgląd

### 3. ThumbnailFrame
- `tk.Frame` → `QFrame`
- Layout pionowy z QVBoxLayout
- `bind()` → `mousePressEvent()` override
- Etykiety (`tk.Label` → `QLabel`)

### 4. SelectablePDFViewer (Główna Klasa)
- `__init__(master)` → `QMainWindow`
- Menu: tworzymy QMenuBar z QMenu i QAction
- Toolbar: QHBoxLayout z przyciskami QPushButton
- Canvas + Scrollbar → QScrollArea
- `tk.Frame` → `QWidget` dla scrollable_frame
- `tk.Button` → `QPushButton`
- Event handling: `bind()` → `connect()` lub override eventów

### 5. System Eventów

**Bind → Connect / Override**
```python
# PRZED (Tkinter):
widget.bind("<Button-1>", handler)
widget.bind("<MouseWheel>", handler)
widget.bind("<Return>", handler)

# PO (Qt):
widget.mousePressEvent = handler  # override
widget.keyPressEvent = handler    # override
# lub
widget.clicked.connect(handler)   # sygnał
```

**Klawisze Skrótów**
```python
# PRZED:
master.bind("<Control-s>", self.save_document)

# PO:
shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
shortcut.activated.connect(self.save_document)
```

### 6. Layouty

**pack() → Layouty Qt**
```python
# PRZED:
frame.pack(side=tk.TOP, fill=tk.X)

# PO:
layout = QVBoxLayout()
layout.addWidget(frame)
```

**grid() → QGridLayout**
```python
# PRZED:
widget.grid(row=0, column=1, sticky="w")

# PO:
layout = QGridLayout()
layout.addWidget(widget, 0, 1)
```

### 7. MessageBox i FileDialog

```python
# PRZED:
messagebox.showinfo("Tytuł", "Treść")
messagebox.showwarning("Tytuł", "Treść")
messagebox.showerror("Tytuł", "Treść")
result = messagebox.askyesno("Tytuł", "Pytanie")
file = filedialog.askopenfilename(...)

# PO:
QMessageBox.information(parent, "Tytuł", "Treść")
QMessageBox.warning(parent, "Tytuł", "Treść")
QMessageBox.critical(parent, "Tytuł", "Treść")
result = QMessageBox.question(parent, "Tytuł", "Pytanie")
file, _ = QFileDialog.getOpenFileName(...)
```

### 8. Canvas i Obrazy

```python
# PRZED (Tkinter):
from PIL import ImageTk
img_tk = ImageTk.PhotoImage(pil_image)
label = tk.Label(image=img_tk)

# PO (Qt):
from PySide6.QtGui import QPixmap
pil_image.save(buffer, 'PNG')
pixmap = QPixmap()
pixmap.loadFromData(buffer.getvalue())
label = QLabel()
label.setPixmap(pixmap)
```

### 9. Tooltips

```python
# PRZED (Custom Tooltip class):
Tooltip(widget, "Text")

# PO (Built-in Qt):
widget.setToolTip("Text")
```

### 10. Menu Context (PPM)

```python
# PRZED:
menu = tk.Menu(self.master, tearoff=0)
menu.add_command(label="...", command=...)
menu.post(event.x_root, event.y_root)

# PO:
menu = QMenu(self)
menu.addAction("...", handler)
menu.exec(global_pos)
```

## Struktura Pliku PDFEditor_qt.py

```
1. Importy PySide6
2. Stałe (bez zmian z PDFEditor.py)
3. Funkcje pomocnicze (mm2pt, resource_path)
4. Klasy dialogowe:
   - PageCropResizeDialog(QDialog)
   - PageNumberingDialog(QDialog)
   - PageNumberMarginDialog(QDialog)
   - ShiftContentDialog(QDialog)
   - ImageImportSettingsDialog(QDialog)
   - EnhancedPageRangeDialog(QDialog)
   - MergePageGridDialog(QDialog)
5. ThumbnailFrame(QFrame)
6. SelectablePDFViewer(QMainWindow) - główna klasa aplikacji
7. main() - uruchomienie QApplication
```

## Kluczowe Punkty Migracji

### Geometry Management
- Tkinter: pack/grid/place
- Qt: QVBoxLayout, QHBoxLayout, QGridLayout

### Event Loop
- Tkinter: `root.mainloop()`
- Qt: `app.exec()`

### Modal Dialogs
- Tkinter: `dialog.wait_window()`
- Qt: `dialog.exec()` lub `dialog.setModal(True); dialog.show()`

### Widget State
- Tkinter: `state=tk.DISABLED` / `state=tk.NORMAL`
- Qt: `setEnabled(False)` / `setEnabled(True)`

### Colors
- Tkinter: `bg="color"`, `fg="color"`
- Qt: `setStyleSheet("background-color: color; color: textcolor;")`

## Testowanie

Po migracji należy przetestować:
1. Otwieranie PDF
2. Wszystkie operacje edycji (crop, resize, rotate, delete, insert)
3. Import/Export PDF i obrazów
4. Undo/Redo
5. Numeracja stron
6. Scalanie stron
7. Menu i skróty klawiszowe
8. Drag & drop (jeśli zaimplementowane)
9. Wszystkie dialogi

## Uruchomienie

```bash
# Zainstaluj zależności
pip install PySide6 PyMuPDF Pillow pypdf

# Uruchom program
python PDFEditor_qt.py
```

## Uwagi

- Wszystkie metody zachowują tę samą logikę biznesową
- Zmienia się tylko warstwa prezentacji (UI)
- Biblioteki PDF (PyMuPDF, pypdf) pozostają bez zmian
- PIL/Pillow do przetwarzania obrazów
