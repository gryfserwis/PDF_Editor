# PDF Editor - PySide6 Migration

## Overview

This document describes the migration of the PDF Editor from tkinter to PySide6.

## Original Application

- **File**: `PDFEditor.py`
- **Size**: 3774 lines, 172KB
- **Framework**: tkinter with tkinterdnd2
- **Classes**: 10 classes (7 dialogs, 2 helpers, 1 main application)
- **Methods**: 119 methods in main SelectablePDFViewer class

## Migration Status

### Completed ✓

1. **Project Structure**
   - Complete PySide6 imports
   - All constants and configuration preserved
   - Resource path handling maintained

2. **Complete Dialog Implementations**
   - `ShiftContentDialog` - Fully converted to PySide6
   - `PageNumberMarginDialog` - Fully converted to PySide6

3. **Framework Classes**
   - `SelectablePDFViewer` - Main application framework created
   - Menu system foundation
   - Toolbar foundation
   - Status bar implemented
   - Window structure with scroll area

4. **Helper Classes**
   - `Tooltip` - Simple adapter created

### Requires Implementation ⚠

The following components have template structures but need full implementation:

1. **Dialog Classes** (following the pattern of completed dialogs):
   - `PageNumberingDialog` - 8KB, complex parameters
   - `EnhancedPageRangeDialog` - 4.5KB, page range selection
   - `ImageImportSettingsDialog` - 6KB, image import options
   - `PageCropResizeDialog` - 13KB, most complex dialog
   - `MergePageGridDialog` - 13.5KB, grid merge with preview

2. **Main Application Methods** (119 methods total):
   - PDF operations (open, save, import, export)
   - Page manipulation (rotate, delete, insert, cut, copy, paste)
   - Thumbnail grid management
   - Selection handling
   - Undo/redo system
   - Drag & drop support
   - Context menus
   - Keyboard shortcuts
   - Zoom controls
   - All toolbar button implementations

3. **Helper Classes**:
   - `ThumbnailFrame` - Complete thumbnail display widget

## Conversion Patterns

### tkinter → PySide6 Mappings

| tkinter | PySide6 | Notes |
|---------|---------|-------|
| `tk.Toplevel` | `QDialog` | Set modal with `setModal(True)` |
| `tk.Frame` | `QWidget` or `QFrame` | Depending on styling needs |
| `tk.Label` | `QLabel` | Direct replacement |
| `tk.Button` | `QPushButton` | Use `clicked.connect()` signal |
| `tk.Entry` | `QLineEdit` | Use `text()` to get value |
| `tk.Radiobutton` | `QRadioButton` | Group with `QButtonGroup` |
| `tk.Checkbutton` | `QCheckBox` | Use `isChecked()` |
| `ttk.Combobox` | `QComboBox` | Use `currentText()` |
| `ttk.LabelFrame` | `QGroupBox` | Set title with constructor |
| `tk.Canvas` | `QScrollArea` or custom widget | Depends on use case |
| `tk.StringVar` | Python `str` | No need for special variable class |
| `pack()` | `QVBoxLayout` | Vertical layout |
| `grid()` | `QGridLayout` | Grid layout |
| `bind('<Key>')` | `QAction` + `setShortcut()` | Keyboard shortcuts |
| `messagebox.*` | `QMessageBox.*` | Similar static methods |
| `filedialog.*` | `QFileDialog.*` | Similar static methods |

### Layout Conversion

**tkinter pack:**
```python
frame.pack(side=tk.TOP, fill=tk.X)
```

**PySide6 equivalent:**
```python
layout = QVBoxLayout()
layout.addWidget(widget)
```

**tkinter grid:**
```python
widget.grid(row=0, column=1, sticky="w")
```

**PySide6 equivalent:**
```python
layout = QGridLayout()
layout.addWidget(widget, 0, 1, Qt.AlignLeft)
```

### Event Handling

**tkinter:**
```python
button.bind('<Button-1>', callback)
self.bind('<Escape>', self.cancel)
```

**PySide6:**
```python
button.clicked.connect(callback)
escape_action = QAction(self)
escape_action.setShortcut(QKeySequence(Qt.Key_Escape))
escape_action.triggered.connect(self.cancel)
self.addAction(escape_action)
```

## Estimated Work Remaining

- **Dialog Implementations**: 15-20 hours
  - Each dialog requires careful conversion of layout and logic
  - PageCropResizeDialog and MergePageGridDialog are most complex
  
- **Main Application Methods**: 20-30 hours
  - 119 methods need adaptation
  - PDF processing logic largely unchanged
  - UI interactions need PySide6 adaptation

- **Testing and Refinement**: 5-10 hours
  - Test each dialog thoroughly
  - Verify all functionality preserved
  - UI/UX adjustments

**Total Estimated**: 40-60 hours

## Running the Application

### Requirements

```bash
pip install PySide6 PyMuPDF Pillow pypdf
```

### Launch

```bash
python PDFEditor_PySide6.py
```

**Note**: The application will show a status dialog indicating which features are implemented.

## Development Guidelines

1. **Preserve All Functionality**: Every parameter and option from the tkinter version must be maintained

2. **Follow Patterns**: Use the completed dialogs (ShiftContentDialog, PageNumberMarginDialog) as templates

3. **Test Incrementally**: Test each dialog and feature as it's implemented

4. **PDF Processing**: The PDF processing logic (pypdf, fitz) remains unchanged - only GUI needs adaptation

5. **Layout Managers**: Use appropriate Qt layouts (QVBoxLayout, QHBoxLayout, QGridLayout) to match original appearance

## File Structure

```
PDF_Editor/
├── PDFEditor.py                    # Original tkinter version (3774 lines)
├── PDFEditor_PySide6.py            # PySide6 version (679 lines, framework + 2 complete dialogs)
├── README_PySide6_Migration.md     # This file
├── requirements_pyside6.txt         # Python dependencies
└── icons/                          # Icon resources (unchanged)
```

## Migration Benefits

Once complete, the PySide6 version will provide:

- Modern, native-looking UI on all platforms
- Better performance and stability
- Active framework support (Qt is actively maintained)
- Enhanced features and widgets
- Better high-DPI display support
- Improved accessibility

## Original Functionality (All Must Be Preserved)

- PDF file operations (open, save, import, export)
- Page manipulation (rotate, delete, insert, move, duplicate)
- Clipboard operations (cut, copy, paste)
- Page numbering with extensive options
- Content shifting and margin adjustment
- Page cropping and resizing
- Image import with scaling options
- PDF merging
- Page grid merging
- Thumbnail preview grid
- Undo/redo (50 levels)
- Drag and drop support
- Keyboard shortcuts
- Context menus
- Status bar updates
- Zoom controls

## Contact

For questions about this migration, refer to the original `PDFEditor.py` for implementation details.
