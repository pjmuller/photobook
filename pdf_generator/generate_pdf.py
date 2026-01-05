#!/usr/bin/env python3
"""
Photobook PDF Generator

Generates print-ready sRGB PDFs from album.json and source images.
Uses the same cropping and layout logic as the Vue.js frontend.
"""

import json
import sys
from pathlib import Path
from typing import TypedDict, NotRequired

from PIL import Image
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

# =============================================================================
# Constants - matching the Vue app's config.ts
# =============================================================================

# UI dimensions (in pixels)
UI_PAGE_WIDTH = 730
UI_PAGE_HEIGHT = 598
UI_GUTTER = 7

# Print dimensions (in mm)
PRINT_PAGE_WIDTH = 356
PRINT_PAGE_HEIGHT = 296
PRINT_MARGIN = 2  # 2mm margin for bleed (printer cuts 3mm, so 1mm bleeds past cut line)

# Printable area (mm)
PRINT_AREA_WIDTH = PRINT_PAGE_WIDTH - (2 * PRINT_MARGIN)   # 352mm
PRINT_AREA_HEIGHT = PRINT_PAGE_HEIGHT - (2 * PRINT_MARGIN)  # 292mm

# Scale factor: mm per UI pixel
SCALE_FACTOR = PRINT_AREA_WIDTH / UI_PAGE_WIDTH  # ~0.4822 mm/px

# Gutter in mm
PRINT_GUTTER = UI_GUTTER * SCALE_FACTOR  # ~4.8mm

# DPI warning threshold
MIN_DPI_WARNING = 200

# =============================================================================
# Type definitions matching types.ts
# =============================================================================


class FocalPoint(TypedDict):
    x: float
    y: float


class Cell(TypedDict):
    width: NotRequired[int]   # used in row-based layouts
    height: NotRequired[int]  # used in column-based layouts
    path: NotRequired[str]
    focalPoint: NotRequired[FocalPoint]
    zoom: NotRequired[float]
    crop_x: NotRequired[float]
    crop_y: NotRequired[float]
    crop_width: NotRequired[float]
    crop_height: NotRequired[float]


class Row(TypedDict):
    height: int
    cells: list[Cell]


class Column(TypedDict):
    width: int
    cells: list[Cell]  # cells stacked vertically within the column


class Page(TypedDict):
    id: str
    layout: str
    rows: NotRequired[list[Row]]      # for row-based layouts
    columns: NotRequired[list[Column]]  # for column-based layouts


class Album(TypedDict):
    photobook_version: str
    pages: list[Page]


# Column-based layouts
COLUMN_LAYOUTS = {"1-1", "1-2", "2-1"}


def is_column_layout(layout: str) -> bool:
    """Check if a layout is column-based."""
    return layout in COLUMN_LAYOUTS


# =============================================================================
# Cropping Logic - exact port from useCropCalculation.ts
# =============================================================================


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp a value between min and max."""
    return min(max_val, max(min_val, value))


def calculate_crop(
    img_w: float,
    img_h: float,
    cell_w: float,
    cell_h: float,
    focal_x: float,
    focal_y: float,
    zoom: float,
) -> tuple[float, float, float, float]:
    """
    Calculate the crop rectangle from user intent (focalPoint, zoom) to pixel values.

    This is a direct port of calculateCrop() from useCropCalculation.ts.

    Args:
        img_w: Image width in pixels
        img_h: Image height in pixels
        cell_w: Cell width in UI pixels
        cell_h: Cell height in UI pixels
        focal_x: Focal point X (0.0 to 1.0)
        focal_y: Focal point Y (0.0 to 1.0)
        zoom: Zoom level (1.0 = cover, max 3.0)

    Returns:
        Tuple of (crop_x, crop_y, crop_width, crop_height) in image pixels
    """
    # Calculate aspect ratios
    img_ar = img_w / img_h
    cell_ar = cell_w / cell_h

    # Determine "cover" crop box at zoom=1.0
    # This is the largest rectangle with cell's aspect ratio that fits in the image
    if img_ar > cell_ar:
        # Image is wider than cell - height is the constraint
        base_crop_h = img_h
        base_crop_w = img_h * cell_ar
    else:
        # Image is narrower or same AR as cell - width is the constraint
        base_crop_w = img_w
        base_crop_h = img_w / cell_ar

    # Apply zoom: higher zoom = smaller crop rectangle (more magnified)
    final_crop_w = base_crop_w / zoom
    final_crop_h = base_crop_h / zoom

    # Calculate focal point in pixels on original image
    focal_px_x = focal_x * img_w
    focal_px_y = focal_y * img_h

    # Center the crop box over the focal point
    crop_x = focal_px_x - final_crop_w / 2
    crop_y = focal_px_y - final_crop_h / 2

    # Clamp to ensure crop box stays within image bounds
    crop_x = clamp(crop_x, 0, img_w - final_crop_w)
    crop_y = clamp(crop_y, 0, img_h - final_crop_h)

    return crop_x, crop_y, final_crop_w, final_crop_h


# =============================================================================
# Image Processing
# =============================================================================


def load_image(image_path: Path) -> Image.Image:
    """Load an image and apply EXIF orientation."""
    img = Image.open(image_path)

    # Apply EXIF orientation (handles rotated phone photos)
    from PIL import ImageOps

    img = ImageOps.exif_transpose(img)

    return img


def convert_to_srgb(img: Image.Image) -> Image.Image:
    """Convert an image to sRGB color space."""
    if img.mode == "RGB":
        return img

    # Handle transparency by compositing on white background
    if img.mode in ("RGBA", "LA", "PA"):
        background = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode == "RGBA":
            background.paste(img, mask=img.split()[3])
        else:
            background.paste(img)
        return background

    # Convert any other mode to RGB
    return img.convert("RGB")


def crop_and_resize_image(
    img: Image.Image,
    crop_x: float,
    crop_y: float,
    crop_w: float,
    crop_h: float,
    target_w_mm: float,
    target_h_mm: float,
    target_dpi: float = 300,
) -> Image.Image:
    """
    Crop an image and resize it for the target print dimensions.

    Uses high-quality LANCZOS resampling for smooth results.
    """
    # Crop the image (Pillow uses integer coordinates)
    crop_box = (
        int(round(crop_x)),
        int(round(crop_y)),
        int(round(crop_x + crop_w)),
        int(round(crop_y + crop_h)),
    )
    cropped = img.crop(crop_box)

    # Calculate target size in pixels at target DPI
    # DPI = pixels / inch, and 1 inch = 25.4mm
    target_w_px = int(round(target_w_mm / 25.4 * target_dpi))
    target_h_px = int(round(target_h_mm / 25.4 * target_dpi))

    # Resize using high-quality LANCZOS resampling
    resized = cropped.resize((target_w_px, target_h_px), Image.Resampling.LANCZOS)

    return resized


def calculate_effective_dpi(crop_width: float, print_width_mm: float) -> float:
    """Calculate the effective DPI of a cropped image at print size."""
    # DPI = (source pixels / print size in inches)
    # print size in inches = print_width_mm / 25.4
    print_width_inches = print_width_mm / 25.4
    return crop_width / print_width_inches


# =============================================================================
# PDF Generation
# =============================================================================


def render_cell(
    c: canvas.Canvas,
    cell: Cell,
    cell_width_ui: int,
    cell_height_ui: int,
    cell_width_mm: float,
    cell_height_mm: float,
    pdf_x: float,
    pdf_y: float,
    image_folder: Path,
    low_dpi_warnings: list[str],
) -> None:
    """Render a single cell to the PDF canvas."""
    # Skip empty cells
    if "path" not in cell or not cell["path"]:
        return

    image_path = image_folder / cell["path"]

    if not image_path.exists():
        print(f"  Warning: Image not found: {cell['path']}")
        return

    # Load image
    img = load_image(image_path)
    img_w, img_h = img.size

    # Get crop parameters
    focal_point = cell.get("focalPoint", {"x": 0.5, "y": 0.5})
    zoom = cell.get("zoom", 1.0)

    # Calculate crop (using UI pixel dimensions for aspect ratio)
    crop_x, crop_y, crop_w, crop_h = calculate_crop(
        img_w,
        img_h,
        cell_width_ui,
        cell_height_ui,
        focal_point["x"],
        focal_point["y"],
        zoom,
    )

    # Check DPI
    effective_dpi = calculate_effective_dpi(crop_w, cell_width_mm)
    if effective_dpi < MIN_DPI_WARNING:
        warning = f"  Low DPI warning: {cell['path']} at {effective_dpi:.0f} DPI (min recommended: {MIN_DPI_WARNING})"
        low_dpi_warnings.append(warning)
        print(warning)

    # Crop and resize image
    processed_img = crop_and_resize_image(
        img,
        crop_x,
        crop_y,
        crop_w,
        crop_h,
        cell_width_mm,
        cell_height_mm,
        target_dpi=300,  # Internal processing at 300 DPI
    )

    # Convert to sRGB
    srgb_img = convert_to_srgb(processed_img)

    # Draw image on PDF
    img_reader = ImageReader(srgb_img)
    c.drawImage(
        img_reader,
        pdf_x,
        pdf_y,
        width=cell_width_mm * mm,
        height=cell_height_mm * mm,
        preserveAspectRatio=False,
    )

    # Close images to free memory
    img.close()
    processed_img.close()
    srgb_img.close()


def generate_pdf(album: Album, image_folder: Path, output_path: Path) -> None:
    """Generate a print-ready PDF from the album data.
    
    Note: First and last pages are skipped as they are used for the cover
    (rendered separately by generate_cover.py).
    """
    # Skip first and last pages (used for cover)
    interior_pages = album["pages"][1:-1] if len(album["pages"]) > 2 else []
    
    if not interior_pages:
        print("Error: Album has no interior pages (only cover pages)")
        return

    print(f"Generating PDF: {output_path}")
    print(f"Page size: {PRINT_PAGE_WIDTH}x{PRINT_PAGE_HEIGHT}mm")
    print(f"Margins: {PRINT_MARGIN}mm")
    print(f"Scale factor: {SCALE_FACTOR:.4f} mm/px")
    print(f"Skipping first and last pages (used for cover)")
    print()

    # Create PDF canvas
    c = canvas.Canvas(
        str(output_path),
        pagesize=(PRINT_PAGE_WIDTH * mm, PRINT_PAGE_HEIGHT * mm),
    )

    low_dpi_warnings: list[str] = []

    for page_idx, page in enumerate(interior_pages):
        print(f"Processing page {page_idx + 1}/{len(interior_pages)} (layout: {page['layout']})")

        if "columns" in page and page["columns"]:
            # Column-based layout: iterate columns left-to-right, cells top-to-bottom
            current_x = 0.0

            for col_idx, column in enumerate(page["columns"]):
                col_width_ui = column["width"]
                col_width_mm = col_width_ui * SCALE_FACTOR

                # Track Y position from top of printable area
                current_y_from_top = 0.0

                for cell_idx, cell in enumerate(column["cells"]):
                    cell_height_ui = cell.get("height", UI_PAGE_HEIGHT)
                    cell_height_mm = cell_height_ui * SCALE_FACTOR
                    cell_width_mm = col_width_mm

                    # Calculate position in PDF coordinates
                    # ReportLab uses bottom-left origin, so flip Y
                    pdf_x = (PRINT_MARGIN + current_x) * mm
                    pdf_y = (PRINT_PAGE_HEIGHT - PRINT_MARGIN - current_y_from_top - cell_height_mm) * mm

                    render_cell(
                        c,
                        cell,
                        col_width_ui,
                        cell_height_ui,
                        cell_width_mm,
                        cell_height_mm,
                        pdf_x,
                        pdf_y,
                        image_folder,
                        low_dpi_warnings,
                    )

                    # Move to next cell position (vertically)
                    current_y_from_top += cell_height_mm
                    if cell_idx < len(column["cells"]) - 1:
                        current_y_from_top += PRINT_GUTTER

                # Move to next column position (horizontally)
                current_x += col_width_mm
                if col_idx < len(page["columns"]) - 1:
                    current_x += PRINT_GUTTER

        else:
            # Row-based layout (existing behavior)
            # Track Y position from top of printable area
            # ReportLab uses bottom-left origin, so we need to flip Y coordinates
            current_y_from_top = 0.0

            rows = page.get("rows", [])
            for row_idx, row in enumerate(rows):
                row_height_ui = row["height"]
                row_height_mm = row_height_ui * SCALE_FACTOR

                # Track X position from left of printable area
                current_x = 0.0

                for cell_idx, cell in enumerate(row["cells"]):
                    cell_width_ui = cell.get("width", UI_PAGE_WIDTH)
                    cell_width_mm = cell_width_ui * SCALE_FACTOR
                    cell_height_mm = row_height_mm

                    # Calculate position in PDF coordinates
                    # ReportLab uses bottom-left origin, so flip Y
                    pdf_x = (PRINT_MARGIN + current_x) * mm
                    pdf_y = (PRINT_PAGE_HEIGHT - PRINT_MARGIN - current_y_from_top - cell_height_mm) * mm

                    render_cell(
                        c,
                        cell,
                        cell_width_ui,
                        row_height_ui,
                        cell_width_mm,
                        cell_height_mm,
                        pdf_x,
                        pdf_y,
                        image_folder,
                        low_dpi_warnings,
                    )

                    # Move to next cell position
                    current_x += cell_width_mm
                    if cell_idx < len(row["cells"]) - 1:
                        current_x += PRINT_GUTTER

                # Move to next row position
                current_y_from_top += row_height_mm
                if row_idx < len(rows) - 1:
                    current_y_from_top += PRINT_GUTTER

        # Add page break (except for last page)
        if page_idx < len(interior_pages) - 1:
            c.showPage()

    # Save PDF
    c.save()

    print()
    print(f"PDF generated successfully: {output_path}")
    print(f"Interior pages rendered: {len(interior_pages)}")
    print(f"(First and last album pages skipped - used for cover)")

    if low_dpi_warnings:
        print()
        print(f"Warning: {len(low_dpi_warnings)} image(s) have DPI below {MIN_DPI_WARNING}")
        print("These images may appear pixelated when printed.")


# =============================================================================
# CLI Entry Point
# =============================================================================


def main() -> None:
    """Main entry point for the PDF generator."""
    if len(sys.argv) < 2:
        print("Usage: python generate_pdf.py <image_folder>")
        print()
        print("Arguments:")
        print("  image_folder  Path to folder containing album.json and images")
        print()
        print("Output:")
        print("  Creates photobook.pdf in the image folder")
        sys.exit(1)

    image_folder = Path(sys.argv[1]).resolve()

    if not image_folder.is_dir():
        print(f"Error: Not a directory: {image_folder}")
        sys.exit(1)

    album_path = image_folder / "album.json"
    if not album_path.exists():
        print(f"Error: album.json not found in {image_folder}")
        sys.exit(1)

    # Load album data
    print(f"Loading album from: {album_path}")
    with open(album_path, "r", encoding="utf-8") as f:
        album: Album = json.load(f)

    print(f"Album version: {album.get('photobook_version', 'unknown')}")
    print(f"Pages: {len(album['pages'])}")
    print()

    # Generate PDF
    output_path = image_folder / "photobook.pdf"
    generate_pdf(album, image_folder, output_path)


if __name__ == "__main__":
    main()

