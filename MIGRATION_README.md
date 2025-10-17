# GRYF PDF Editor - Tkinter to PySide6 Migration

## Migration Status

**Date**: 2025-10-17  
**Version**: 5.6.0  
**Status**: ⚠️ **Automated Migration Created - Manual Completion Required**

## Files

- `PDFEditor.py` - Original Tkinter version (PRESERVED)
- `PDFEditor_pyside6.py` - Automated PySide6 migration (NEEDS MANUAL FIXES)
- `PDFEditor_tkinter_backup.py` - Backup of original

## What Was Migrated

### ✅ Completed (Automated)
1. **Import statements** - All Tkinter imports replaced with PySide6
2. **Widget class names** - tk.* and ttk.* replaced with Q* equivalents  
3. **File dialogs** - filedialog.* replaced with QFileDialog.*
4. **Message boxes** - messagebox.* replaced with QMessageBox.*
5. **Basic widget replacements**:
   - tk.Frame/ttk.Frame → QFrame
   - tk.Label/ttk.Label → QLabel
   - tk.Button/ttk.Button → QPushButton
   - tk.Entry/ttk.Entry → QLineEdit
   - tk.Checkbutton/ttk.Checkbutton → QCheckBox
   - tk.Radiobutton/ttk.Radiobutton → QRadioButton
   - ttk.Combobox → QComboBox
   - ttk.LabelFrame → QGroupBox
   - tk.Listbox → QListWidget
6. **Business Logic** - ALL PDF manipulation, macro system, preferences PRESERVED

### ⚠️ Requires Manual Completion

#### Critical (Application Won't Run Without These)
1. **Layout Management** (HIGHEST PRIORITY)
   - All `.pack()`, `.grid()`, `.place()` calls need conversion to Qt layouts
   - Use QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout
   - Approximately 1000+ layout calls to fix
   
2. **Variable Bindings** 
   - StringVar/IntVar/BooleanVar need conversion to:
     - Direct properties (for simple cases)
     - Qt Signals/Slots (for reactive updates)
   - Approximately 200+ variable instances to fix

3. **Event Handling**
   - All `.bind()` calls need conversion to signal/slot connections
   - Example: `widget.bind('<Return>', handler)` → `widget.returnPressed.connect(handler)`
   - Approximately 150+ event bindings to convert

4. **custom_messagebox Function**
   - Needs complete rewrite for Qt
   - Used extensively throughout application
   - See original lines 126-213 for reference

#### Important (Application Will Run But Features Won't Work)
5. **Dialog Geometry and Positioning**
   - `.geometry()`, `.winfo_*()` calls need Qt equivalents
   - Dialog centering logic needs update
   - All 13 dialogs affected

6. **Drag & Drop Implementation**
   - Completely different API between Tkinter and Qt
   - See ThumbnailFrame class and SelectablePDFViewer
   - Requires reimplementation with Qt's drag-drop API

7. **Tooltip System**
   - Current Tooltip class won't work in Qt
   - Use QToolTip or reimplement with QWidget

#### Low Priority (Nice to Have)
8. **Widget Styling**
   - Qt uses QSS (similar to CSS) instead of configure()
   - Colors, fonts should use Qt style system
   
9. **Icon Loading**
   - Adapt resource_path() function for Qt if needed
   - Test icon loading from icons/ folder

## Component Breakdown

### Dialogs to Fix (13 total)
Each requires layout management + event handling fixes:

1. PreferencesDialog
2. PageCropResizeDialog
3. PageNumberingDialog
4. PageNumberMarginDialog
5. ShiftContentDialog
6. ImageImportSettingsDialog
7. EnhancedPageRangeDialog
8. MergePageGridDialog
9. MacroEditDialog
10. MacroRecordingDialog
11. MacrosListDialog
12. MergePDFDialog
13. PDFAnalysisDialog

### Main Classes
- SelectablePDFViewer (main application) - ~2000 lines
- ThumbnailFrame - drag-drop widget
- PreferencesManager - ✅ works as-is (pure Python)

## How to Complete the Migration

### Phase 1: Get Basic Application Running (8-12 hours)
1. Fix `custom_messagebox` function for Qt
2. Fix layouts in main SelectablePDFViewer class
3. Fix main window initialization and menu bar
4. Test that application starts and displays

### Phase 2: Fix Simple Dialogs (6-8 hours)
1. Start with simplest dialog (e.g., PageNumberMarginDialog)
2. Convert layout (pack/grid → Qt layouts)
3. Convert variables (StringVar → properties)
4. Convert events (bind → signals)
5. Test dialog
6. Repeat for each dialog

### Phase 3: Fix Complex Features (10-15 hours)
1. Implement Qt drag-and-drop in ThumbnailFrame
2. Fix all event bindings in main application
3. Test macro system
4. Test preferences system
5. Test all PDF operations

### Phase 4: Polish & Testing (5-10 hours)
1. Fix styling and appearance
2. Test all features thoroughly
3. Fix edge cases
4. Update documentation

**Total Estimated Time: 30-45 hours**

## Quick Start for Manual Fixing

### Example: Converting a Simple Dialog

**Before (Tkinter)**:
```python
class SimpleDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Dialog")
        
        frame = ttk.Frame(self, padding="12")
        frame.pack(fill="both", expand=True)
        
        label = ttk.Label(frame, text="Enter value:")
        label.grid(row=0, column=0)
        
        self.value_var = tk.StringVar()
        entry = ttk.Entry(frame, textvariable=self.value_var)
        entry.grid(row=0, column=1)
        
        btn = ttk.Button(frame, text="OK", command=self.ok)
        btn.grid(row=1, column=0, columnspan=2)
    
    def ok(self):
        print(self.value_var.get())
        self.destroy()
```

**After (PySide6)**:
```python
class SimpleDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Dialog")
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Add widgets to layout
        form_layout = QFormLayout()
        self.value_edit = QLineEdit()
        form_layout.addRow("Enter value:", self.value_edit)
        layout.addLayout(form_layout)
        
        # Add button
        btn = QPushButton("OK")
        btn.clicked.connect(self.ok)
        layout.addWidget(btn)
    
    def ok(self):
        print(self.value_edit.text())
        self.accept()
```

### Key Differences

1. **Layouts**: Explicit layout objects (QVBoxLayout, etc.)
2. **Variables**: Direct widget properties (`.text()`, `.isChecked()`)
3. **Events**: Signal/slot connections (`.clicked.connect()`)
4. **Dialog closing**: `.accept()` or `.reject()` instead of `.destroy()`

## Testing Strategy

1. Test each dialog independently first
2. Create simple test script for each dialog:
   ```python
   if __name__ == '__main__':
       app = QApplication(sys.argv)
       dialog = MyDialog(None)
       result = dialog.exec()
       print(f"Result: {result}")
   ```
3. Fix issues before integrating into main application

## Dependencies

The migrated version requires:
```
PySide6>=6.5.0
PyMuPDF (fitz)
Pillow
pypdf
```

Install with:
```bash
pip install PySide6 PyMuPDF Pillow pypdf
```

## Migration Tools

For finding areas needing fixes:
```bash
# Find all pack() calls
grep -n "\.pack(" PDFEditor_pyside6.py

# Find all StringVar references  
grep -n "StringVar" PDFEditor_pyside6.py

# Find all bind() calls
grep -n "\.bind(" PDFEditor_pyside6.py

# Find all TODO/FIXME comments
grep -n "FIXME\|TODO" PDFEditor_pyside6.py
```

## Support

This migration represents converting a 8000+ line application from one UI framework to another.
If you encounter issues:

1. Check this README
2. Refer to Qt documentation: https://doc.qt.io/qtforpython/
3. Compare with original Tkinter version for business logic
4. Test incrementally - don't try to run the whole app at once

## License

Same as original GRYF PDF Editor - Proprietary to Centrum Graficzne Gryf sp. z o.o.
