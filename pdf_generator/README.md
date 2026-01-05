# Photobook PDF Generator

Generate print-ready sRGB PDFs from your photobook album.json.

## Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

## Installation

```bash
cd pdf_generator

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate
uv pip install Pillow reportlab
```

## Usage

```bash
python generate_pdf.py /path/to/image/folder
```

The script expects the image folder to contain:
- `album.json` - The photobook layout data
- All image files referenced in album.json

Output:
- `photobook.pdf` - Print-ready PDF in the image folder

## Output Specifications

| Property | Value |
|----------|-------|
| Page size | 356 × 296 mm |
| Margins | 10mm all sides |
| Color space | sRGB |
| Image resampling | Lanczos (high quality) |

## DPI Warnings

The script will warn you if any images have an effective DPI below 200 when printed. Images with low DPI may appear pixelated in print.

To fix low DPI warnings:
- Use higher resolution source images
- Reduce the zoom level on affected cells in the UI
- Use smaller cell sizes for low-resolution images

## How It Works

1. Reads `album.json` from the specified folder
2. For each page, processes rows and cells matching the UI layout
3. Applies the same cropping algorithm as the Vue.js frontend:
   - Uses focal point (0-1 ratios) and zoom (1.0-3.0)
   - Calculates "cover" crop maintaining cell aspect ratio
   - Centers crop on focal point, clamped to image bounds
4. Crops and resizes images using high-quality LANCZOS resampling
5. Converts images to sRGB color space
6. Renders pages with precise mm positioning using ReportLab

