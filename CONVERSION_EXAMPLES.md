# PySide6 Conversion Examples

This document shows side-by-side comparisons of the tkinter original code and the PySide6 converted code to illustrate the conversion patterns.

## Example 1: ShiftContentDialog - Complete Conversion

### Original (tkinter - 86 lines)

```python
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

    def create_widgets(self):
        main_frame = ttk.Frame(self, padding="8")
        main_frame.pack(fill="both", expand=True)

        xy_frame = ttk.LabelFrame(main_frame, text="Kierunek i wartość przesunięcia (mm)", padding=(8, 6))
        xy_frame.pack(fill='x', padx=4, pady=(8, 0))

        ENTRY_WIDTH = 4

        ttk.Label(xy_frame, text="Poziome:").grid(row=0, column=0, sticky="w", padx=(2, 8), pady=(4,2))
        self.x_value = ttk.Entry(xy_frame, width=ENTRY_WIDTH)
        self.x_value.insert(0, "0")
        self.x_value.grid(row=0, column=1, sticky="w", padx=(0,2), pady=(4,2))
        self.x_direction = tk.StringVar(value='P')
        ttk.Radiobutton(xy_frame, text="Lewo", variable=self.x_direction, value='L').grid(row=0, column=2, sticky="w", padx=(8, 4))
        ttk.Radiobutton(xy_frame, text="Prawo", variable=self.x_direction, value='P').grid(row=0, column=3, sticky="w", padx=(0,2))

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', side='bottom', pady=(10, 4))
        ttk.Button(button_frame, text="Przesuń", command=self.ok).pack(side='left', expand=True, padx=5)
        ttk.Button(button_frame, text="Anuluj", command=self.cancel).pack(side='right', expand=True, padx=5)

    def ok(self, event=None):
        try:
            x_mm = float(self.x_value.get().replace(',', '.'))
            # ... validation ...
            self.result = {
                'x_dir': self.x_direction.get(),
                'x_mm': x_mm,
                # ...
            }
            self.destroy()
        except ValueError as e:
            messagebox.showerror("Błąd Wprowadzania", f"Nieprawidłowa wartość: {e}.")

    def cancel(self, event=None):
        self.result = None
        self.destroy()
```

### Converted (PySide6 - 108 lines)

```python
class ShiftContentDialog(QDialog):
    """Okno dialogowe do określania przesunięcia zawartości strony, wyśrodkowane i modalne."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Przesuwanie zawartości stron")
        self.setModal(True)
        self.result = None
        
        self.init_ui()
        self.resize_to_fit()
        
        # Keyboard shortcuts
        self.escape_action = QAction(self)
        self.escape_action.setShortcut(QKeySequence(Qt.Key_Escape))
        self.escape_action.triggered.connect(self.reject)
        self.addAction(self.escape_action)
        
        self.return_action = QAction(self)
        self.return_action.setShortcut(QKeySequence(Qt.Key_Return))
        self.return_action.triggered.connect(self.ok)
        self.addAction(self.return_action)
        
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        
        # XY Frame
        xy_group = QGroupBox("Kierunek i wartość przesunięcia (mm)")
        xy_layout = QGridLayout()
        xy_layout.setSpacing(8)
        
        # Horizontal shift
        xy_layout.addWidget(QLabel("Poziome:"), 0, 0, Qt.AlignRight)
        self.x_value = QLineEdit("0")
        self.x_value.setMaximumWidth(50)
        xy_layout.addWidget(self.x_value, 0, 1)
        
        self.x_direction_group = QButtonGroup(self)
        self.x_left = QRadioButton("Lewo")
        self.x_right = QRadioButton("Prawo")
        self.x_right.setChecked(True)
        self.x_direction_group.addButton(self.x_left, 0)
        self.x_direction_group.addButton(self.x_right, 1)
        xy_layout.addWidget(self.x_left, 0, 2)
        xy_layout.addWidget(self.x_right, 0, 3)
        
        xy_group.setLayout(xy_layout)
        main_layout.addWidget(xy_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)
        ok_button = QPushButton("Przesuń")
        ok_button.clicked.connect(self.ok)
        cancel_button = QPushButton("Anuluj")
        cancel_button.clicked.connect(self.reject)
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)
        
    def ok(self):
        try:
            x_mm = float(self.x_value.text().replace(',', '.'))
            # ... validation ...
            x_dir = 'L' if self.x_left.isChecked() else 'P'
            
            self.result = {
                'x_dir': x_dir,
                'x_mm': x_mm,
                # ...
            }
            self.accept()
        except ValueError as e:
            QMessageBox.critical(self, "Błąd Wprowadzania", 
                               f"Nieprawidłowa wartość: {e}.")
    
    def resize_to_fit(self):
        self.adjustSize()
        if self.parent():
            parent_geo = self.parent().geometry()
            self.move(
                parent_geo.x() + (parent_geo.width() - self.width()) // 2,
                parent_geo.y() + (parent_geo.height() - self.height()) // 2
            )
```

## Key Differences Explained

### 1. Class Inheritance
- **tkinter**: `tk.Toplevel` (separate window)
- **PySide6**: `QDialog` (modal dialog, more appropriate)

### 2. Modal Behavior
- **tkinter**: `self.grab_set()`, `self.wait_window()`
- **PySide6**: `self.setModal(True)`, `exec()` when showing

### 3. Layout System
- **tkinter**: `pack()` and `grid()` methods on widgets
- **PySide6**: Layout objects (`QVBoxLayout`, `QGridLayout`) that contain widgets

### 4. Variable Binding
- **tkinter**: `tk.StringVar()` with `.get()` method
- **PySide6**: Direct widget access with `.text()` or `.isChecked()`

### 5. Radio Buttons
- **tkinter**: Grouped by sharing same variable
- **PySide6**: Explicitly grouped with `QButtonGroup`

### 6. Event Handling
- **tkinter**: `bind('<Escape>', callback)`
- **PySide6**: `QAction` with `setShortcut()` and `triggered` signal

### 7. Dialog Result
- **tkinter**: `self.destroy()` to close
- **PySide6**: `self.accept()` or `self.reject()`

### 8. Message Boxes
- **tkinter**: `messagebox.showerror()`
- **PySide6**: `QMessageBox.critical()`

## Example 2: Layout Comparison

### tkinter Grid Layout
```python
label = ttk.Label(frame, text="Value:")
label.grid(row=0, column=0, sticky="e", padx=4)

entry = ttk.Entry(frame, width=6)
entry.grid(row=0, column=1, sticky="w", padx=2)

button = ttk.Button(frame, text="OK")
button.grid(row=1, column=0, columnspan=2)
```

### PySide6 Grid Layout
```python
layout = QGridLayout()

label = QLabel("Value:")
layout.addWidget(label, 0, 0, Qt.AlignRight)

entry = QLineEdit()
entry.setMaximumWidth(60)
layout.addWidget(entry, 0, 1, Qt.AlignLeft)

button = QPushButton("OK")
layout.addWidget(button, 1, 0, 1, 2)  # row, col, rowspan, colspan

frame.setLayout(layout)
```

## Example 3: Button Connections

### tkinter
```python
button = ttk.Button(frame, text="Save", command=self.save_document)
button.pack(side='left', padx=5)
```

### PySide6
```python
button = QPushButton("Save")
button.clicked.connect(self.save_document)
layout.addWidget(button)
```

## Example 4: Entry Widget Value Access

### tkinter
```python
entry = ttk.Entry(frame)
entry.insert(0, "default")
# Later:
value = entry.get()
```

### PySide6
```python
entry = QLineEdit("default")
# Later:
value = entry.text()
```

## Example 5: Radio Button Groups

### tkinter
```python
var = tk.StringVar(value='option1')
rb1 = ttk.Radiobutton(frame, text="Option 1", variable=var, value='option1')
rb2 = ttk.Radiobutton(frame, text="Option 2", variable=var, value='option2')
# Later:
selected = var.get()
```

### PySide6
```python
group = QButtonGroup()
rb1 = QRadioButton("Option 1")
rb2 = QRadioButton("Option 2")
rb1.setChecked(True)
group.addButton(rb1, 0)
group.addButton(rb2, 1)
# Later:
if rb1.isChecked():
    # option 1 selected
```

## Example 6: File Dialogs

### tkinter
```python
filepath = filedialog.askopenfilename(
    title="Open PDF",
    filetypes=[("PDF files", "*.pdf")]
)
```

### PySide6
```python
filepath, _ = QFileDialog.getOpenFileName(
    self,
    "Open PDF",
    "",
    "PDF files (*.pdf)"
)
```

## Example 7: Message Boxes

### tkinter
```python
result = messagebox.askyesno(
    "Confirm",
    "Are you sure?",
    parent=self
)
```

### PySide6
```python
result = QMessageBox.question(
    self,
    "Confirm",
    "Are you sure?",
    QMessageBox.Yes | QMessageBox.No
)
if result == QMessageBox.Yes:
    # User clicked Yes
```

## Summary of Conversion Rules

1. **Inheritance**: `tk.Toplevel` → `QDialog`, `tk.Frame` → `QWidget`
2. **Layouts**: Create layout objects, add widgets to them, set layout on container
3. **Variables**: Direct widget access instead of `tk.StringVar` etc.
4. **Events**: Signals/slots instead of `bind()`
5. **Grouping**: Explicit `QButtonGroup` for radio buttons
6. **Dialogs**: Use Qt static methods (`QFileDialog`, `QMessageBox`)
7. **Styling**: CSS-like stylesheets instead of individual properties
8. **Result**: `accept()`/`reject()` instead of `destroy()`

## Benefits of These Patterns

1. **Clearer Structure**: Explicit layout objects vs implicit positioning
2. **Type Safety**: Direct widget methods vs string-based variable access
3. **Modern API**: Active development and features in Qt/PySide6
4. **Cross-Platform**: Better native look and feel on all platforms
5. **Performance**: Generally better performance with complex UIs

These patterns, once understood, make the conversion straightforward and systematic.
