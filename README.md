# GRYF PDF Editor

Professional PDF editing tool with comprehensive features for page manipulation, numbering, cropping, and more.

## Versions Available

### Tkinter Version (Original)
- **File:** `PDFEditor.py`
- **Launch:** `python3 PDFEditor.py`
- Classic Tkinter-based interface

### PySide6 Version (Qt)
- **File:** `PDFEditor_qt.py`
- **Launch:** `python3 PDFEditor_qt.py`
- Modern Qt-based interface with enhanced UI/UX
- 100% feature parity with original version

## Requirements

```bash
pip install PySide6 PyMuPDF pypdf pillow
```

For Tkinter version (original):
```bash
pip install tkinterdnd2  # For drag & drop support
```

## Features

- ✅ Open, edit, and save PDF files
- ✅ Page selection (all, odd, even, portrait, landscape)
- ✅ Clipboard operations (cut, copy, paste)
- ✅ Undo/Redo support
- ✅ Page numbering (add with multiple formats, remove with smart detection)
- ✅ Page cropping and resizing
- ✅ Content shifting
- ✅ Page rotation
- ✅ Merge multiple pages into grid layout
- ✅ Import/Export PDF pages
- ✅ Import images as pages
- ✅ Export pages as PNG images
- ✅ Drag & drop support for files and page reordering
- ✅ Thumbnail view with zoom
- ✅ Comprehensive keyboard shortcuts

## Quick Start

### Qt Version (Recommended)
```bash
python3 PDFEditor_qt.py
```

### Tkinter Version
```bash
python3 PDFEditor.py
```

## Keyboard Shortcuts

### File Operations
- `Ctrl+O` - Open PDF
- `Ctrl+S` - Save as
- `Ctrl+I` - Import PDF
- `Ctrl+E` - Export selected pages
- `Ctrl+Shift+I` - Import image
- `Ctrl+Shift+E` - Export as images

### Edit Operations
- `Ctrl+Z` - Undo
- `Ctrl+Y` - Redo
- `Ctrl+X` - Cut pages
- `Ctrl+C` - Copy pages
- `Ctrl+V` - Paste after
- `Ctrl+Shift+V` - Paste before
- `Delete` - Delete selected pages
- `Ctrl+D` - Duplicate page

### Selection
- `Ctrl+A` or `F4` - Select all
- `F1` - Select odd pages
- `F2` - Select even pages
- `Ctrl+F1` - Select portrait pages
- `Ctrl+F2` - Select landscape pages

### Modifications
- `Ctrl+Shift+-` - Rotate left
- `Ctrl+Shift++` - Rotate right
- `F5` - Shift content
- `F6` - Remove page numbers
- `F7` - Add page numbers
- `F8` - Crop/Resize dialog
- `Ctrl+N` - Insert blank page after
- `Ctrl+Shift+N` - Insert blank page before

### View
- `Ctrl++` or `Ctrl+Wheel Up` - Zoom in
- `Ctrl+-` or `Ctrl+Wheel Down` - Zoom out

## License

Copyright © Centrum Graficzne Gryf sp. z o.o.

All rights reserved. Copying, modifying, and distributing this program without written permission is prohibited.

## Version History

### v5.0.0 (Qt Version)
- Complete PySide6 port with modern UI
- Enhanced drag & drop support
- Improved visual feedback
- Native Qt dialogs and widgets

### v4.1.1 (Tkinter Version)
- Stable Tkinter-based version
- All core PDF editing features
