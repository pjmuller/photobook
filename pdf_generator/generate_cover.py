#!/usr/bin/env python3
"""
Photobook Cover PDF Generator

Generates a print-ready cover PDF with back panel, spine, and front panel.
The front image extends across the spine area, with year text centered on the spine.
"""

import json
import sys
from pathlib import Path
from typing import TypedDict, NotRequired

from PIL import Image, ImageOps
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# =============================================================================
# Constants - Cover dimensions
# =============================================================================

# Bleed on all sides (mm)
BLEED = 19

# Total height including bleed (mm)
TOTAL_HEIGHT = 335

# Base total width for 6mm spine (mm)
BASE_TOTAL_WIDTH = 758

# Base spine width (mm)
BASE_SPINE_WIDTH = 6

# UI dimensions for crop calculation (matching Vue app)
UI_PAGE_WIDTH = 730
UI_PAGE_HEIGHT = 598

# DPI for output
OUTPUT_DPI = 300

# Spine width lookup table: (min_pages, max_pages, spine_mm)
SPINE_TABLE = [
    (24, 34, 6),
    (36, 46, 7),
    (48, 60, 8),
    (62, 70, 9),
    (72, 82, 10),
    (84, 98, 11),
    (100, 114, 12),
    (116, 126, 13),
    (128, 138, 14),
    (140, 154, 15),
    (156, 170, 16),
    (172, 186, 17),
    (188, 196, 18),
    (200, 200, 19),
]


# =============================================================================
# Type definitions
# =============================================================================


class FocalPoint(TypedDict):
    x: float
    y: float


class Cell(TypedDict):
    width: NotRequired[int]
    height: NotRequired[int]
    path: NotRequired[str]
    focalPoint: NotRequired[FocalPoint]
    zoom: NotRequired[float]


class Row(TypedDict):
    height: int
    cells: list[Cell]


class Column(TypedDict):
    width: int
    cells: list[Cell]


class Page(TypedDict):
    id: str
    layout: str
    rows: NotRequired[list[Row]]
    columns: NotRequired[list[Column]]


class Album(TypedDict):
    photobook_version: str
    pages: list[Page]


# =============================================================================
# Spine calculation
# =============================================================================


def calculate_paper_pages(album_pages: int) -> int:
    """
    Calculate the number of paper pages from album pages.
    
    Formula: (album_pages - 2 covers) / 2 (recto-verso printing)
    """
    return (album_pages - 2) // 2


def get_spine_width(paper_pages: int) -> int:
    """
    Get spine width in mm based on paper page count.
    
    Returns the spine width from the lookup table, or raises an error
    if the page count is out of range.
    """
    for min_pages, max_pages, spine_mm in SPINE_TABLE:
        if min_pages <= paper_pages <= max_pages:
            return spine_mm
    
    # Handle edge cases
    if paper_pages < 24:
        print(f"Warning: {paper_pages} paper pages is below minimum (24). Using 6mm spine.")
        return 6
    if paper_pages > 200:
        print(f"Warning: {paper_pages} paper pages exceeds maximum (200). Using 19mm spine.")
        return 19
    
    # Shouldn't reach here, but fallback
    raise ValueError(f"Cannot determine spine width for {paper_pages} paper pages")


def calculate_total_width(spine_width: int) -> float:
    """Calculate total cover width including bleed for a given spine width."""
    return BASE_TOTAL_WIDTH + (spine_width - BASE_SPINE_WIDTH)


# =============================================================================
# Image utilities (reused from generate_pdf.py)
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
    """
    img_ar = img_w / img_h
    cell_ar = cell_w / cell_h

    if img_ar > cell_ar:
        base_crop_h = img_h
        base_crop_w = img_h * cell_ar
    else:
        base_crop_w = img_w
        base_crop_h = img_w / cell_ar

    final_crop_w = base_crop_w / zoom
    final_crop_h = base_crop_h / zoom

    focal_px_x = focal_x * img_w
    focal_px_y = focal_y * img_h

    crop_x = focal_px_x - final_crop_w / 2
    crop_y = focal_px_y - final_crop_h / 2

    crop_x = clamp(crop_x, 0, img_w - final_crop_w)
    crop_y = clamp(crop_y, 0, img_h - final_crop_h)

    return crop_x, crop_y, final_crop_w, final_crop_h


def load_image(image_path: Path) -> Image.Image:
    """Load an image and apply EXIF orientation."""
    img = Image.open(image_path)
    img = ImageOps.exif_transpose(img)
    return img


def convert_to_srgb(img: Image.Image) -> Image.Image:
    """Convert an image to sRGB color space."""
    if img.mode == "RGB":
        return img

    if img.mode in ("RGBA", "LA", "PA"):
        background = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode == "RGBA":
            background.paste(img, mask=img.split()[3])
        else:
            background.paste(img)
        return background

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
    """Crop an image and resize it for the target print dimensions."""
    crop_box = (
        int(round(crop_x)),
        int(round(crop_y)),
        int(round(crop_x + crop_w)),
        int(round(crop_y + crop_h)),
    )
    cropped = img.crop(crop_box)

    target_w_px = int(round(target_w_mm / 25.4 * target_dpi))
    target_h_px = int(round(target_h_mm / 25.4 * target_dpi))

    resized = cropped.resize((target_w_px, target_h_px), Image.Resampling.LANCZOS)
    return resized


# =============================================================================
# Page validation
# =============================================================================


def count_cells_in_page(page: Page) -> int:
    """Count the total number of cells in a page."""
    count = 0
    
    if "rows" in page and page["rows"]:
        for row in page["rows"]:
            count += len(row["cells"])
    
    if "columns" in page and page["columns"]:
        for column in page["columns"]:
            count += len(column["cells"])
    
    return count


def validate_single_cell_page(page: Page, page_name: str) -> None:
    """
    Validate that a page has exactly one cell.
    
    Exits with error if the page has multiple cells.
    """
    cell_count = count_cells_in_page(page)
    if cell_count != 1:
        print(f"Error: {page_name} must have exactly 1 cell (layout '1'), but has {cell_count} cells.")
        print(f"       Current layout: {page['layout']}")
        print("       Cover pages must use a single full-page image.")
        sys.exit(1)


def get_first_cell_with_image(page: Page) -> Cell | None:
    """
    Get the first cell that has an image from a page.
    
    Works with both row-based and column-based layouts.
    """
    # Try row-based layout first
    if "rows" in page and page["rows"]:
        for row in page["rows"]:
            for cell in row["cells"]:
                if cell.get("path"):
                    return cell
    
    # Try column-based layout
    if "columns" in page and page["columns"]:
        for column in page["columns"]:
            for cell in column["cells"]:
                if cell.get("path"):
                    return cell
    
    return None


# =============================================================================
# Cover PDF Generation
# =============================================================================


def generate_cover(
    album: Album,
    image_folder: Path,
    output_path: Path,
    year: str,
) -> None:
    """Generate a print-ready cover PDF from the album data."""
    
    pages = album["pages"]
    album_page_count = len(pages)
    
    # Calculate spine dimensions
    paper_pages = calculate_paper_pages(album_page_count)
    spine_width = get_spine_width(paper_pages)
    total_width = calculate_total_width(spine_width)
    
    # Image widths: spine belongs to front, so front is spine_width larger
    # Back = (W - S) / 2, Front = (W + S) / 2
    back_image_width = (total_width - spine_width) / 2
    front_image_width = (total_width + spine_width) / 2
    image_height = TOTAL_HEIGHT  # Full height including bleed
    
    print(f"Album pages: {album_page_count}")
    print(f"Paper pages: {paper_pages}")
    print(f"Spine width: {spine_width}mm")
    print(f"Total cover dimensions: {total_width}mm x {TOTAL_HEIGHT}mm")
    print(f"Back image: {back_image_width}mm | Front image: {front_image_width}mm")
    print()
    
    # Get cover pages
    front_page = pages[0]  # First page = front cover
    back_page = pages[-1]  # Last page = back cover
    
    # Validate that cover pages have exactly one cell
    validate_single_cell_page(front_page, "Front cover page (first page)")
    validate_single_cell_page(back_page, "Back cover page (last page)")
    
    front_cell = get_first_cell_with_image(front_page)
    back_cell = get_first_cell_with_image(back_page)
    
    if not front_cell or not front_cell.get("path"):
        print("Error: No image found on front cover page (first page)")
        sys.exit(1)
    
    if not back_cell or not back_cell.get("path"):
        print("Error: No image found on back cover page (last page)")
        sys.exit(1)
    
    print(f"Front cover image: {front_cell['path']}")
    print(f"Back cover image: {back_cell['path']}")
    print()
    
    # Create PDF canvas
    c = canvas.Canvas(
        str(output_path),
        pagesize=(total_width * mm, TOTAL_HEIGHT * mm),
    )
    
    # Calculate positions
    # Layout: | back image | front image (includes spine) |
    # Back image starts at x=0, front image starts where back ends
    spine_x = back_image_width  # Spine starts where back image ends
    
    # Process and draw back cover image (left side)
    print("Processing back cover image...")
    back_image_path = image_folder / back_cell["path"]
    if not back_image_path.exists():
        print(f"Error: Back cover image not found: {back_cell['path']}")
        sys.exit(1)
    
    back_img = load_image(back_image_path)
    back_img_w, back_img_h = back_img.size
    
    back_focal = back_cell.get("focalPoint", {"x": 0.5, "y": 0.5})
    back_zoom = back_cell.get("zoom", 1.0)
    
    # Calculate crop for back image (using full height aspect ratio)
    back_crop_x, back_crop_y, back_crop_w, back_crop_h = calculate_crop(
        back_img_w, back_img_h,
        back_image_width, image_height,  # Target aspect ratio
        back_focal["x"], back_focal["y"],
        back_zoom,
    )
    
    back_processed = crop_and_resize_image(
        back_img,
        back_crop_x, back_crop_y, back_crop_w, back_crop_h,
        back_image_width, image_height,
        OUTPUT_DPI,
    )
    back_srgb = convert_to_srgb(back_processed)
    
    # Draw back image (starts at x=0 to include left bleed)
    back_reader = ImageReader(back_srgb)
    c.drawImage(
        back_reader,
        0,  # Start at left edge (includes bleed)
        0,  # Start at bottom (includes bleed)
        width=back_image_width * mm,
        height=image_height * mm,
        preserveAspectRatio=False,
    )
    
    back_img.close()
    back_processed.close()
    back_srgb.close()
    
    # Process and draw front cover image (right side, extends into spine)
    print("Processing front cover image...")
    front_image_path = image_folder / front_cell["path"]
    if not front_image_path.exists():
        print(f"Error: Front cover image not found: {front_cell['path']}")
        sys.exit(1)
    
    front_img = load_image(front_image_path)
    front_img_w, front_img_h = front_img.size
    
    front_focal = front_cell.get("focalPoint", {"x": 0.5, "y": 0.5})
    front_zoom = front_cell.get("zoom", 1.0)
    
    # Calculate crop for front image
    front_crop_x, front_crop_y, front_crop_w, front_crop_h = calculate_crop(
        front_img_w, front_img_h,
        front_image_width, image_height,
        front_focal["x"], front_focal["y"],
        front_zoom,
    )
    
    front_processed = crop_and_resize_image(
        front_img,
        front_crop_x, front_crop_y, front_crop_w, front_crop_h,
        front_image_width, image_height,
        OUTPUT_DPI,
    )
    front_srgb = convert_to_srgb(front_processed)
    
    # Draw front image (starts at spine position, extends to right edge including bleed)
    front_reader = ImageReader(front_srgb)
    c.drawImage(
        front_reader,
        spine_x * mm,  # Start at spine
        0,  # Start at bottom (includes bleed)
        width=front_image_width * mm,
        height=image_height * mm,
        preserveAspectRatio=False,
    )
    
    front_img.close()
    front_processed.close()
    front_srgb.close()
    
    # Draw year text on spine
    print(f"Adding year text: {year}")
    
    # Calculate spine center
    spine_center_x = spine_x + spine_width / 2
    spine_center_y = TOTAL_HEIGHT / 2
    
    # Set up text style
    c.setFillColorRGB(1, 1, 1)  # White
    
    # Font size for ~10mm text height
    # 1 point = 1/72 inch, 1 inch = 25.4mm
    # 10mm = 10/25.4 * 72 ≈ 28pt
    font_size = 28
    
    # Use Helvetica Bold (built-in font)
    c.setFont("Helvetica-Bold", font_size)
    
    # Rotate and draw text vertically (bottom to top)
    c.saveState()
    c.translate(spine_center_x * mm, spine_center_y * mm)
    c.rotate(90)  # Rotate 90 degrees counter-clockwise
    
    # Calculate text width for centering
    text_width = c.stringWidth(year, "Helvetica-Bold", font_size)
    c.drawString(-text_width / 2, -font_size / 3, year)
    
    c.restoreState()
    
    # Save PDF
    c.save()
    
    print()
    print(f"Cover PDF generated successfully: {output_path}")


# =============================================================================
# CLI Entry Point
# =============================================================================


def main() -> None:
    """Main entry point for the cover PDF generator."""
    if len(sys.argv) < 3:
        print("Usage: python generate_cover.py <image_folder> <year>")
        print()
        print("Arguments:")
        print("  image_folder  Path to folder containing album.json and images")
        print("  year          Year to display on the spine (e.g., 2024)")
        print()
        print("Output:")
        print("  Creates cover.pdf in the image folder")
        sys.exit(1)
    
    image_folder = Path(sys.argv[1]).resolve()
    year = sys.argv[2]
    
    if not image_folder.is_dir():
        print(f"Error: Not a directory: {image_folder}")
        sys.exit(1)
    
    album_path = image_folder / "album.json"
    if not album_path.exists():
        print(f"Error: album.json not found in {image_folder}")
        sys.exit(1)
    
    # Validate year
    if not year.strip():
        print("Error: Year cannot be empty")
        sys.exit(1)
    
    # Load album data
    print(f"Loading album from: {album_path}")
    with open(album_path, "r", encoding="utf-8") as f:
        album: Album = json.load(f)
    
    print(f"Album version: {album.get('photobook_version', 'unknown')}")
    print()
    
    # Generate cover PDF
    output_path = image_folder / "cover.pdf"
    generate_cover(album, image_folder, output_path, year)


if __name__ == "__main__":
    main()

