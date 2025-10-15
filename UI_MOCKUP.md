# Preferencje programu - UI Mockup

## New Section: "Wykrywanie stron kolorowych" (Color Page Detection)

The preferences dialog now includes a new section with the following fields:

```
┌─────────────────────────────────────────────────────────────┐
│ Preferencje programu                                     [X] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ ┌─ Ustawienia ogólne ──────────────────────────────────┐  │
│ │ Domyślna ścieżka odczytu:  [__________________] [...] │  │
│ │ Domyślna ścieżka zapisu:   [__________________] [...] │  │
│ │ Jakość miniatur:           [Średnia ▼]                │  │
│ │ Potwierdzenie przed usunięciem: [✓]                   │  │
│ │ DPI eksportowanych obrazów: [300 ▼]                   │  │
│ └───────────────────────────────────────────────────────┘  │
│                                                             │
│ ┌─ Wykrywanie stron kolorowych ────────────────────────┐  │
│ │ Próg różnicy RGB:          [10      ]                 │  │
│ │                            (1-255, domyślnie 10)      │  │
│ │ Liczba próbkowanych pikseli: [100    ]                │  │
│ │                            (10-1000, domyślnie 100)   │  │
│ │ Skala renderowania:        [0.5     ]                 │  │
│ │                            (0.1-2.0, domyślnie 0.5)   │  │
│ └───────────────────────────────────────────────────────┘  │
│                                                             │
│ ┌─ Reset do ustawień domyślnych ───────────────────────┐  │
│ │                    [Resetuj]                          │  │
│ └───────────────────────────────────────────────────────┘  │
│                                                             │
│              [Zapisz]                      [Anuluj]         │
└─────────────────────────────────────────────────────────────┘
```

## Field Descriptions

### Próg różnicy RGB (RGB Difference Threshold)
- **Range:** 1-255
- **Default:** 10
- **Description:** The threshold for RGB color difference. If the difference between R, G, and B values exceeds this threshold, the page is considered colored.
- **Effect:** Lower values = more sensitive to color detection. Higher values = stricter color detection (requires more color difference to be detected as colored).

### Liczba próbkowanych pikseli (Number of Sampled Pixels)
- **Range:** 10-1000
- **Default:** 100
- **Description:** The number of pixels to sample when analyzing a page for color.
- **Effect:** More samples = more accurate but slower. Fewer samples = faster but potentially less accurate.

### Skala renderowania (Render Scale)
- **Range:** 0.1-2.0
- **Default:** 0.5
- **Description:** The scale at which pages are rendered for analysis. 0.5 means 50% of original resolution.
- **Effect:** Lower scale = faster analysis but lower quality sampling. Higher scale = more accurate but slower.

## Validation

The dialog validates all inputs when "Zapisz" (Save) is clicked:

1. **Próg różnicy RGB:** Must be an integer between 1 and 255
2. **Liczba próbkowanych pikseli:** Must be an integer between 10 and 1000
3. **Skala renderowania:** Must be a float between 0.1 and 2.0

Invalid inputs show an error dialog with a clear message about the acceptable range.

## Usage

After saving the preferences:
- The PDF Analysis dialog (accessible via "Narzędzia" → "Analiza PDF") will use these settings
- All color detection operations will use the configured values instead of hardcoded defaults
- Settings are persisted to the `preferences.txt` file and loaded on application startup
