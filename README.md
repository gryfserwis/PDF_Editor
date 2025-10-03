# GRYF PDF Editor (Qt Version)

## Overview

GRYF PDF Editor is a comprehensive PDF manipulation application built with PySide6 (Qt for Python). This is the complete Qt implementation providing modern UI with full drag & drop support for both files and page thumbnails.

## Features

### Core Functionality
- **Open/Save PDF documents** - Load and save PDF files with full format support
- **Thumbnail view** - Visual page explorer with drag & drop reordering
- **Undo/Redo** - 50-level history stack for all operations
- **Clipboard operations** - Cut, copy, paste pages with full multi-page support

### Page Operations
- **Rotate pages** - Left/Right rotation (90° increments)
- **Delete pages** - Remove selected pages with undo support
- **Duplicate pages** - Create copies of selected pages
- **Insert blank pages** - Add new pages before/after current selection
- **Reverse order** - Reverse the order of all pages in document
- **Import/Export** - Import pages from other PDFs, export selected pages

### Advanced Features
- **Crop/Resize pages** - Comprehensive cropping and resizing dialog
  - Three crop modes: none, crop only, crop and resize
  - Three resize modes: none, scale proportionally, resize without scaling
  - Custom or standard paper formats (A0-A6)
  - Custom positioning with offset controls
  
- **Page numbering** - Add or remove page numbers
  - Multiple position options (header/footer, left/center/right)
  - Normal and mirror modes for double-sided printing
  - Custom font and size selection
  - Multiple format options (simple, "Page X of Y")
  - Smart number removal with pattern detection

- **Shift content** - Move page content in any direction
  - X and Y axis shifting with millimeter precision
  - Applies to selected pages only

- **Merge to grid** - Combine multiple pages into grid layout
  - Automatic optimal grid calculation
  - Support for all standard paper formats
  - Configurable margins and spacing
  - Live preview of grid layout

- **Import images** - Convert images to PDF pages
  - Support for PNG, JPG, JPEG, TIF, TIFF
  - Multiple scaling modes (fit, original, custom)
  - Alignment options (center, corners)
  - Orientation toggle (portrait/landscape)

### Selection Features
- **Multi-select** - Click, Ctrl+Click, Shift+Click for range selection
- **Select all** (Ctrl+A) - Select all pages
- **Select odd/even** (F1/F2) - Quick selection helpers
- **Select by orientation** - Portrait or landscape pages
- **Context menu** - Right-click for quick operations

### Drag & Drop
- **File drag & drop** - Drag PDF or image files onto window
  - Opens PDF if no document loaded
  - Imports pages if document already open
  - Converts images to PDF pages
  
- **Thumbnail drag & drop** - Reorder pages by dragging thumbnails
  - Move operation: Left-click drag
  - Copy operation: Ctrl + Left-click drag
  - Multi-page support: Drag multiple selected pages

## Installation

### Requirements
- Python 3.8 or higher
- PySide6 (Qt 6)
- PyMuPDF (fitz)
- Pillow (PIL)
- pypdf

### Install Dependencies

```bash
pip install PySide6 PyMuPDF Pillow pypdf
```

Or using a requirements file:

```bash
pip install -r requirements.txt
```

## Running the Application

```bash
python PDFEditor_qt.py
```

Or on Unix-like systems:

```bash
./PDFEditor_qt.py
```

## Keyboard Shortcuts

### File Operations
- `Ctrl+O` - Open PDF
- `Ctrl+S` - Save as
- `Ctrl+I` - Import PDF
- `Ctrl+E` - Export selected pages
- `Ctrl+Shift+I` - Import image
- `Ctrl+Shift+E` - Export pages as images

### Edit Operations
- `Ctrl+Z` - Undo
- `Ctrl+Y` - Redo
- `Ctrl+X` - Cut selected pages
- `Ctrl+C` - Copy selected pages
- `Ctrl+V` - Paste pages after active
- `Ctrl+Shift+V` - Paste pages before active
- `Delete` - Delete selected pages
- `Ctrl+D` - Duplicate page

### Selection
- `Ctrl+A` - Select all pages
- `F1` - Select odd pages
- `F2` - Select even pages
- `F4` - Select all (alternative)
- `Ctrl+F1` - Select portrait pages
- `Ctrl+F2` - Select landscape pages

### Page Modifications
- `F5` - Shift page content
- `F6` - Remove page numbers
- `F7` - Add page numbers
- `F8` - Crop/resize pages
- `Ctrl+N` - Insert blank page after
- `Ctrl+Shift+N` - Insert blank page before
- `Ctrl+Left` - Rotate page left
- `Ctrl+Right` - Rotate page right

### View
- `Ctrl+Plus` - Zoom in (increase thumbnails)
- `Ctrl+Minus` - Zoom out (decrease thumbnails)
- `Ctrl+Mouse Wheel` - Zoom in/out

## Architecture

### Main Components

1. **PDFEditorMainWindow** - Main application window
   - Manages menus, toolbar, and status bar
   - Handles file operations and document state
   - Coordinates all operations

2. **Dialog Classes** (7 total)
   - `PageCropResizeDialog` - Crop and resize configuration
   - `PageNumberingDialog` - Page numbering options
   - `PageNumberMarginDialog` - Margin settings for number removal
   - `ShiftContentDialog` - Content shifting parameters
   - `ImageImportSettingsDialog` - Image import options
   - `EnhancedPageRangeDialog` - Page range selection
   - `MergePageGridDialog` - Grid merge configuration with preview

3. **ThumbnailWidget** - Individual page thumbnail
   - Displays page preview
   - Handles selection state
   - Supports drag & drop

4. **Custom Widgets**
   - `ThumbnailListWidget` - Scrollable thumbnail container with drag support
   - Selection and focus management
   - Grid layout with dynamic columns

### PDF Processing
- Uses PyMuPDF (fitz) for rendering and basic operations
- Uses pypdf for advanced transformations (shift, crop, resize)
- Maintains undo/redo stacks using byte-level document serialization

## Technical Details

### Dependencies
```python
PySide6>=6.0      # Qt 6 Python bindings
PyMuPDF>=1.18     # PDF rendering and manipulation
Pillow>=8.0       # Image processing
pypdf>=3.0        # PDF transformations
```

### Code Statistics
- **Total lines**: 3,361
- **Classes**: 10 (1 main + 7 dialogs + 2 custom widgets)
- **Methods**: 70+ in main class
- **Dialogs**: 7 complete implementations
- **Keyboard shortcuts**: 30+

### Features vs Original Tkinter Version
This Qt version provides 100% feature parity with the original Tkinter version (PDFEditor.py) while adding:
- Better drag & drop support
- More responsive UI
- Native platform look and feel
- Improved HiDPI support
- Better keyboard navigation
- More intuitive dialogs

## Future Enhancements

Potential improvements for future versions:
- **Thumbnail caching** - Cache rendered thumbnails for better performance
- **Configurable export DPI** - Allow users to set DPI for image exports
- **Dark theme** - Add dark mode option
- **Advanced image import** - More import options and format support
- **Batch operations** - Process multiple files at once
- **PDF forms** - Support for filling PDF forms
- **Annotations** - Add text annotations and highlights
- **Bookmarks** - Manage PDF bookmarks/outline
- **Metadata editing** - Edit PDF metadata (author, title, etc.)

## License

Program stanowi wyłączną własność intelektualną Centrum Graficznego Gryf sp. z o.o.

Wszelkie prawa zastrzeżone. Kopiowanie, modyfikowanie oraz rozpowszechnianie programu bez pisemnej zgody autora jest zabronione.

## Version History

### Version 5.0.0 (Current)
- Complete Qt/PySide6 implementation
- Full feature parity with Tkinter version
- Enhanced drag & drop support
- Improved dialogs with live previews
- 50-level undo/redo stack
- Comprehensive keyboard shortcuts

## Support

For issues, questions, or feature requests, please contact Centrum Graficzne Gryf sp. z o.o.

---

**Note**: This is the Qt (PySide6) version. The original Tkinter version (PDFEditor.py) is maintained separately for reference and backward compatibility.
