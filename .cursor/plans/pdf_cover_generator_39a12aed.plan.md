---
name: PDF Cover Generator
overview: Create a new Python script `generate_cover.py` that produces a print-ready PDF cover with back panel, spine (with year text), and front panel using the first and last page images from album.json.
todos:
  - id: create-script
    content: Create generate_cover.py with spine lookup, dimension calculations, and image placement
    status: completed
  - id: update-docs
    content: Update .cursor/rules/pdf-cover.mdc with high-level summary
    status: completed
---

# PDF Cover Generator

Create a new Python script in [pdf_generator/generate_cover.py](pdf_generator/generate_cover.py) that generates a single-page PDF cover spread for the photobook.

## Dimensions and Layout

```javascript
|<-- 19mm -->|<-- back panel -->|<-- spine -->|<-- front panel -->|<-- 19mm -->|
    bleed         357mm            6-19mm           357mm              bleed
```



- **Height**: 335mm total (including 19mm bleed top + bottom)
- **Base width**: 758mm (for 6mm spine)
- **Panel width**: 357mm each (back and front)
- **Total width formula**: `758 + (spine_width - 6)` mm

## Spine Width Lookup Table

| Paper Pages | Spine (mm) |

|-------------|------------|

| 24-34       | 6          |

| 36-46       | 7          |

| 48-60       | 8          |

| 62-70       | 9          |

| 72-82       | 10         |

| 84-98       | 11         |

| 100-114     | 12         |

| 116-126     | 13         |

| 128-138     | 14         |

| 140-154     | 15         |

| 156-170     | 16         |

| 172-186     | 17         |

| 188-196     | 18         |

| 200         | 19         |**Paper pages formula**: `(album_pages - 2) / 2`

## Image Placement

1. **Back cover** (left side): First cell image from the **last** album page
2. **Front cover + spine** (right side): First cell image from the **first** album page - extends across both the front panel AND spine area
3. **Year text**: White, centered on spine, placed on top of front image

## Implementation

Reuse utilities from [pdf_generator/generate_pdf.py](pdf_generator/generate_pdf.py):

- `load_image()` - EXIF orientation handling
- `convert_to_srgb()` - color space conversion
- `calculate_crop()` - focal point/zoom to pixel crop
- `crop_and_resize_image()` - high-quality resampling

## CLI Usage

```bash
python generate_cover.py <image_folder> <year>
```



- Outputs `cover.pdf` in the image folder
- Exits with error if year is not provided

## Documentation Update