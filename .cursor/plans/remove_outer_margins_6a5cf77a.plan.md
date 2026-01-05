---
name: Remove Outer Margins
overview: Remove the unused PAGE_OUTER_MARGIN from Vue config and reduce PDF print margin from 10mm to 2mm for proper bleed with 3mm printer cutoff.
todos:
  - id: vue-config-cleanup
    content: Remove unused PAGE_OUTER_MARGIN from config.ts
    status: pending
  - id: pdf-margin-update
    content: Update PRINT_MARGIN to 2mm and recalculate derived constants
    status: pending
  - id: mdc-to-pdf
    content: Update to-pdf.mdc with new dimension mapping
    status: pending
  - id: mdc-project-context
    content: Update project-context.mdc if needed
    status: pending
---

# Remove Outer Margins from Vue and PDF Generator

## Summary

The Vue app already has edge-to-edge photos (the `PAGE_OUTER_MARGIN: 20` in config is unused). The PDF generator has a 10mm margin that needs to be reduced to 2mm for proper print bleed.

## Changes

### 1. Vue App Config Cleanup

**File:** [`app/src/config.ts`](app/src/config.ts)

- Remove unused `PAGE_OUTER_MARGIN: 20` constant (line 3)
- No functional changes needed - gutters are already only between images

### 2. PDF Generator Margin Update

**File:** [`pdf_generator/generate_pdf.py`](pdf_generator/generate_pdf.py)

Update print constants (lines 29-38):

| Constant | Old Value | New Value |
|----------|-----------|-----------|
| `PRINT_MARGIN` | 10mm | 2mm |
| `PRINT_AREA_WIDTH` | 336mm | 352mm |
| `PRINT_AREA_HEIGHT` | 276mm | 292mm |
| `SCALE_FACTOR` | ~0.4603 | ~0.4822 mm/px |

This positions photos 2mm from the paper edge. With 3mm printer cutoff, 1mm of photo bleeds past the cut line, ensuring no white edges.

### 3. Update Documentation Rules

**File:** [`.cursor/rules/to-pdf.mdc`](.cursor/rules/to-pdf.mdc)

Update the dimension mapping table:

| UI (px) | Print (mm) | Notes |
|---------|------------|-------|
| 730×598 | 352×292 | Printable area (page minus 2mm margins) |
| 10px gutter | ~4.8mm | Scale factor: 0.4822 mm/px |
| - | 356×296 | Full page size |
| - | 2mm | Margins (bleed for 3mm cutoff) |

**File:** [`.cursor/rules/project-context.mdc`](.cursor/rules/project-context.mdc)

- Remove mention of `PAGE_OUTER_MARGIN` if present
- No changes needed (doesn't mention margins)

## Print Bleed Explanation

```
Paper edge (before cut): 0mm
Photo starts at: 2mm
Printer cuts at: 3mm
Result: Photo bleeds 1mm past cut line → no white edges
```
