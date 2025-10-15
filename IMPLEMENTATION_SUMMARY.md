# Implementation Summary: Color Detection Preferences

## Overview

This implementation adds user-configurable settings for color page detection to the PDF Editor application. Previously, the color detection algorithm used hardcoded values. Now users can adjust these parameters through the Preferences dialog.

## Changes Made

### 1. PreferencesManager Class (lines 216-358)

Added three new default preferences:

```python
'color_detect_threshold': '10',    # RGB difference threshold (1-255)
'color_detect_samples': '100',     # Number of pixels to sample (10-1000)
'color_detect_scale': '0.5',       # Render scale for analysis (0.1-2.0)
```

These are stored in the `preferences.txt` file and persist between sessions.

### 2. PreferencesDialog Class (lines 360-506)

#### UI Changes (build_ui method, ~line 385)

Added a new section "Wykrywanie stron kolorowych" (Color Page Detection) with three fields:

1. **Próg różnicy RGB** (RGB Difference Threshold)
   - Entry field with hint text: "(1-255, domyślnie 10)"
   - Bound to `self.color_threshold_var`

2. **Liczba próbkowanych pikseli** (Number of Sampled Pixels)
   - Entry field with hint text: "(10-1000, domyślnie 100)"
   - Bound to `self.color_samples_var`

3. **Skala renderowania** (Render Scale)
   - Entry field with hint text: "(0.1-2.0, domyślnie 0.5)"
   - Bound to `self.color_scale_var`

#### Loading Values (load_current_values method, ~line 459)

Added code to load the three new preferences when the dialog opens:

```python
self.color_threshold_var.set(self.prefs_manager.get('color_detect_threshold'))
self.color_samples_var.set(self.prefs_manager.get('color_detect_samples'))
self.color_scale_var.set(self.prefs_manager.get('color_detect_scale'))
```

#### Validation and Saving (ok method, ~line 492)

Added comprehensive validation before saving:

- **Threshold**: Must be integer in range 1-255
- **Samples**: Must be integer in range 10-1000
- **Scale**: Must be float in range 0.1-2.0

Each validation failure shows a user-friendly error dialog with the acceptable range.

After validation, values are saved to the preferences file:

```python
self.prefs_manager.set('color_detect_threshold', str(threshold))
self.prefs_manager.set('color_detect_samples', str(samples))
self.prefs_manager.set('color_detect_scale', str(scale))
```

### 3. PDFAnalysisDialog Class (lines 3175-3492)

#### Initialization (line 3191)

Added access to preferences manager:

```python
self.prefs_manager = viewer.prefs_manager
```

#### Color Detection Algorithm (_detect_color method, line 3331)

Replaced hardcoded values with preferences:

**Before:**
```python
mat = fitz.Matrix(0.5, 0.5)  # Hardcoded
samples = min(100, pix.width * pix.height)  # Hardcoded
if abs(r - g) > 10 or abs(g - b) > 10 or abs(r - b) > 10:  # Hardcoded
```

**After:**
```python
render_scale = float(self.prefs_manager.get('color_detect_scale', '0.5'))
max_samples = int(self.prefs_manager.get('color_detect_samples', '100'))
threshold = int(self.prefs_manager.get('color_detect_threshold', '10'))

mat = fitz.Matrix(render_scale, render_scale)
samples = min(max_samples, pix.width * pix.height)
if abs(r - g) > threshold or abs(g - b) > threshold or abs(r - b) > threshold:
```

Default values are provided as fallbacks to ensure backward compatibility.

## Testing

### Unit Tests

1. **PreferencesManager Test**: Verified default values, saving, loading, and persistence
2. **Validation Test**: Verified range checking for all three parameters
3. **Integration Test**: End-to-end workflow testing including:
   - Default value loading
   - Modification and persistence
   - Edge case handling (min/max values)
   - Backward compatibility with old preference files

All tests passed successfully. ✓

### Code Structure Verification

Verified that:
- All UI elements are present in the dialog
- Validation logic is implemented
- Settings are properly saved
- PDFAnalysisDialog uses the preferences

## User Impact

### Benefits

1. **Customization**: Users can now adjust color detection sensitivity to their needs
2. **Performance**: Users can trade accuracy for speed by adjusting sample count and render scale
3. **Flexibility**: Different document types may require different thresholds
4. **Persistence**: Settings are saved and remembered between sessions

### Usage

1. Open **Ustawienia** → **Preferencje**
2. Scroll to **Wykrywanie stron kolorowych** section
3. Adjust the three parameters:
   - **Próg różnicy RGB**: Higher = stricter color detection
   - **Liczba próbkowanych pikseli**: Higher = more accurate but slower
   - **Skala renderowania**: Higher = more accurate but slower
4. Click **Zapisz** to save changes
5. The PDF Analysis dialog will now use these settings

### Example Scenarios

**Fast, approximate detection:**
- Threshold: 15
- Samples: 50
- Scale: 0.3

**Accurate, detailed detection:**
- Threshold: 5
- Samples: 500
- Scale: 1.0

**Default (balanced):**
- Threshold: 10
- Samples: 100
- Scale: 0.5

## Backward Compatibility

The implementation maintains full backward compatibility:
- Old preference files without these fields will use defaults
- The `PreferencesManager` automatically adds missing fields
- Default values are provided in all `get()` calls

## File Changes

**Single file modified:** `PDFEditor.py`

**Lines of code:**
- Added: ~120 lines
- Modified: ~10 lines
- Total changes: ~130 lines

## Technical Details

### Parameter Descriptions

1. **RGB Threshold (color_detect_threshold)**
   - Purpose: Determines how different RGB values must be to consider a pixel "colored"
   - Implementation: `abs(r - g) > threshold`
   - Range: 1-255 (byte values)
   - Impact: Lower = more sensitive (detects subtle colors), Higher = less sensitive

2. **Sample Count (color_detect_samples)**
   - Purpose: Number of pixels to check in the page
   - Implementation: Samples are spread evenly across the page
   - Range: 10-1000 pixels
   - Impact: More samples = better accuracy but slower analysis

3. **Render Scale (color_detect_scale)**
   - Purpose: Resolution at which to render the page for analysis
   - Implementation: `fitz.Matrix(scale, scale)`
   - Range: 0.1-2.0 (10% to 200% of original)
   - Impact: Higher scale = better sampling quality but slower rendering

## Conclusion

The implementation successfully adds configurable color detection settings to the PDF Editor while maintaining code quality, backward compatibility, and user-friendliness. All tests pass and the feature is ready for use.
