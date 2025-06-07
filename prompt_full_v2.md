# Goal
Create a family album photobook creator as a single-page application.
The user assigns local images to predefined page layouts. The final deliverable of this tool is an `album.json` file that a separate process (out of scope of this project) can use to generate a PDF.

Prioritize simple, effective code, a clean UI, and a smooth user experience.

# Specification
- we only support JPG images
- we work with fixed pixel dimensions, no need to scale to the viewport
  - PAGE_OUTER_MARGIN = 20
  - PAGE_WIDTH = 730
  - PAGE_HEIGHT = 598
  - ROW_MIN_HEIGHT = 100, // MAX depends on the number of rows: `PAGE_HEIGHT - ((ROW_COUNT - 1) * (ROW_MIN_HEIGHT + PAGE_GUTTER))`
  - CELL_MIN_WIDTH = 100, // MAX depends on the number of cells in a row: `PAGE_WIDTH - ((CELL_COUNT - 1) * (CELL_MIN_WIDTH + PAGE_GUTTER))`
  - PAGE_GUTTER = 10, used in between of rows and columns
    - e.g. if a row is divided into 3 cells, each cell will have width of `(PAGE_WIDTH - (2 * PAGE_GUTTER)) / 3`
- the first page is a single page, displayed on the right.
- All subsequent pages are displayed as double-page spreads (e.g., 2-3, 4-5).
  - each spread is 2 pages wide and each has it's own layout
  - total screen real estate used is `2 * (PAGE_WIDTH + (2 * PAGE_OUTER_MARGIN))` and `PAGE_HEIGHT + (2 * PAGE_OUTER_MARGIN)`
  - show a vertical line between the 2 pages in the spread, add shadows so it looks like a spread
- The last page (e.g. page 6) is a single page, displayed on the left.
- an image can only be used once in the album


# Grid Calculation Strategy
- All page, row, cell, and gutter dimensions must be calculated in **JavaScript** to final **pixel** values, which are then applied via inline styles. This ensures the resizing logic is perfectly synchronized with the rendered output.
- Gutters must be implemented as separate `div` elements, not as CSS `margin` or `gap`.
- Avoid using CSS `calc()`, `flex-basis` percentages, or the `gap` property for the core layout, as the JavaScript needs full, explicit control over dimensions.
- The JS logic must calculate the "net" available space 
  - given N is the number of rows, the row height is `(PAGE_HEIGHT - (N - 1) * PAGE_GUTTER) / N`
  - given N is the number of cells, the cell width is `(PAGE_WIDTH - (N - 1) * PAGE_GUTTER) / N`

# Layouts
- A Layout consists of rows, and each row is divided into 1, 2 or 3 cells. 
  - the height of images within a row is always the same
- layouts contain placeholder cells, these show as dotted lines with "Drop image" in it
- Predefined Layouts
  - "1": 
    - 1 row, 1 cell (full picture page)
    - symbol: '██'
    - cell height: `(PAGE_HEIGHT - (0 * PAGE_GUTTER))/1`, width: `(PAGE_WIDTH - (0 * PAGE_GUTTER))/1`
  - "2-2":
    - row 1: 2 cells
    - row 2: 2 cells
    - symbol: '██▌██▌\n██▌██▌'
    - cell height: `(PAGE_HEIGHT - (1 * PAGE_GUTTER)) / 2`, width: `(PAGE_WIDTH - (1 * PAGE_GUTTER)) / 2`
  - "2-3":
    - row 1: 2 cells, cell height: `(PAGE_HEIGHT - (1 * PAGE_GUTTER)) / 2`, width: `(PAGE_WIDTH - (1 * PAGE_GUTTER)) / 2`
    - row 2: 3 cells, cell height: `(PAGE_HEIGHT - (1 * PAGE_GUTTER)) / 2`, width: `(PAGE_WIDTH - (2 * PAGE_GUTTER)) / 3`
    - symbol: '██▌██▌\n█▌█▌█▌'
  - "3-2":
    - row 1: 3 cells, cell height: `(PAGE_HEIGHT - (1 * PAGE_GUTTER)) / 2`, width: `(PAGE_WIDTH - (2 * PAGE_GUTTER)) / 3`
    - row 2: 2 cells, cell height: `(PAGE_HEIGHT - (1 * PAGE_GUTTER)) / 2`, width: `(PAGE_WIDTH - (1 * PAGE_GUTTER)) / 2`
    - symbol: '█▌█▌█▌\n██▌██▌'


# Change layout of a page
- A layout change icon (`bi-grid-fill`) should be visible on the top-left of a left page and top-right of a right page.
- It should not be active on the first and last single pages of the album. (these always have layout "1")
- Clicking the icon opens a submenu showing the 4 available layouts. Visualize the layouts using the unicode symbols block characters, not their codenames ("1", "2-2", "2-3", "3-2").
  - on click of a layout, change the current page layout and close the menu
- you can change from any layout to any other layout
- rule of thumb: keep as much as possible of the row/cell attributes the same so that the user doesn't have to re-crop the images (`height`, `width`, `crop_x`, `crop_y`, `crop_width`, `crop_height`, `path`, ...)
- only recrop the images to fill the cells where we changed row `height` or cell `width` for that cell
- when we change to a layout that can hold less images, returned the unused images to the image bank
- specific switch strategies:
  - from "2-3" to "2-2". Drop the 3rd image in the bottom row. Reset the cell `width` of the bottom row cells
  - from "3-2" to "2-2". Drop the 3rd image in the top row. Reset the cell `width` of the top row cells
  - from "3-2" to "2-3" (or vice versa). just swap the rows (and keep all attributes the same)
  - from any to "1". Keep the first image you find (top to bottom, left to right) and drop all the others (reactivate them in the bottom bar), reset the `height` to MAX, `width` to MAX
  - from "1" to any, set the image in the top left cell. Reset the row `height` of the 2 rows, and use default cell `width`
  - from "2-2" to "2-3", keep top row exactly as is, add one extra cell in the bottom row and reset cell `width` in that row to 1/3,1/3,1/3
  - from "2-2" to "3-2", keep bottom row exactly as is, add one extra cell in the top row and reset `width` in that row to 1/3,1/3,1/3
  - update the album.json file in the selected folder


# Resizing
- The user can resize rows and cells by dragging the gutters between them. The gutters separate divs show a `row-resize` or `col-resize` cursor on hover.
- **Implementation Logic**:
  - On `mousedown` on a gutter, capture initial mouse coordinates and the initial row `height` or cell `width` of the adjacent elements. Add `mousemove` and `mouseup` event listeners to the `document`.
  - No need for scaling, we work with fixed pixel dimensions, moving the gutter with x pixels changes the `height` or `width` attribute value with the same amount of pixels
  - Enforce a minimum size to prevent cells from collapsing, see `ROW_MIN_HEIGHT` and `CELL_MIN_WIDTH`
  - Update the `height` or `width` values in the Alpine.js data model, letting the UI update reactively. Ensure the sum of the resized properties remains either `PAGE_WIDTH` or `PAGE_HEIGHT`.
  - On `mouseup`, remove the event listeners and immediately trigger the auto-crop function for all images within the resized cells.

# UI
## top right Floating buttons
- Use a Bootstrap button group with icon-only buttons (`bi-*`). All buttons must have a tooltip on hover explaining their function or why they are disabled.
- **Navigation** btn-group: `bi-arrow-left` (Previous) and `bi-arrow-right` (Next).
- **Page Actions**:
  - `bi-plus`: 
    - Adds a new, empty double-page spread (with "2-2" & "2-2" layout)
    - after the current page (spread) except when on the last page, then add it before it.
    - After add, switches to the new spread.
  - `bi-trash`: 
    - Deletes the current page spread after a confirmation dialog. 
    - Disabled for single pages.
  - `bi-arrow-left-right`: 
    - A dropdown button to move the current double-page spread left `bi-arrow-bar-left` or right `bi-arrow-bar-right`. 
    - Disabled for single pages, left disabled if it's the first spread, right disabled if it's the last spread.


## bottom panel (image bank)
- A 170px high, 100% width horizontally-scrolling panel with a dark background.
- Displays all images from the selected folder sorted based on the EXIF data (DateTimeOriginal)
  - if the EXIF data is not available put at the end and then sort these by filename
- thumbs of all pictures of the selected folder
  - All thumbnails must have a fixed height of 150px. Their width **must be calculated dynamically in JavaScript** based on the image's original aspect ratio to prevent any distortion.
  - slightly rounded corners and subtle shadow
- not used images
  - show a `cursor: grab` to drag the image to the main area
- used images:
  - cursor `pointer`
  - gray out
  - when clicked, move to the page where it is used
- image hover
  - animation that makes it slightly bigger
  - no tooltip needed with filename, in general filenames are not important anywhere

## Main area
- The central area displays the current single page or spread.
- The page/spread always has a fixed size, and should NOT be scaled to fit the main area's viewport.
- for first and last page, we show single page
- for all next pages, show the page spreads, e.g. page 2 & 3, 4 & 5 along side each other
- Display the page numbers in a single, unobtrusive element (e.g., bottom-center). Format: "Page 1 / 6", "Pages 2-3 / 6", "Pages 4-5 / 6", "Pages 6 / 6".

# Persistence & Data
Store all album data in `album.json` in the user's selected folder.
Do this after any CRUD operation (add/move/remove image, resize, crop, change layout, move page, delete page, ...).

```json
{
  "photobook_version": "2.0", // fixed version number, so we can change the format without breaking backwards compatibility
  "pages": [ // page spreads have 2 separate entries in this array, one for the left page and one for the right page
    {
      "id": "UUID", // for easy reference
      "layout": "3-2", // (top row 3 cells, bottom row 2 cells)
      "rows": [
        { // first row
          "height": 294, // min: ROW_MIN_HEIGHT, max: PAGE_HEIGHT - ROW_MIN_HEIGHT - PAGE_GUTTER
          "cells": [
            {
              "width": 237, // min: CELL_MIN_WIDTH, max: PAGE_WIDTH - (2 * (PAGE_GUTTER + CELL_MIN_WIDTH)).
              "path": "image1.jpg", // inside of the selected folder
              "crop_x": 15, // x on original image (in pixels)
              "crop_y": 90, // original image y position
              "crop_width": 1265, // original image width
              "crop_height": 834 // original image height
            },
            { "width": 237}, // 2nd cell, waiting for an image to be dropped in
            { "width": 236}, // 3rd cell, total width = 237 + 10 (gutter) + 237 + 10 (gutter) + 236 = 730 (= PAGE_WIDTH)
          ]
        },
        { // 2nd row
          "height": 294, // total height will be 294 (row 1) + 294 (row 2) + 10 (gutter) = 598 (= PAGE_HEIGHT)
          "cells": [
            { "width": 360}, // 1st cell
            { "width": 360}, // 2nd cell, total width = 360 + 360 + 10 (gutter) = 730 (= PAGE_WIDTH)
          ]
        },
      ]
    }
  ]
}
```

Validation
- sum of rows height + gutters must be equal to PAGE_HEIGHT
- sum of cells width + gutters must be equal to PAGE_WIDTH
  - when adding a default cell widths, calculate using Math.floor() for the first N-1 cells. The last cell's width should be the remaining space to ensure the total always sums exactly to PAGE_WIDTH

# Interactions
- **Initial State**: Show a single "Select Image Folder" button to trigger the file system access API
- **Folder Selection**: Use the `window.showDirectoryPicker()` API to allow the user to select a folder. Store the `directoryHandle` for later use (reading images, writing `album.json`).
  - if selected folder has no JPG files inside it show an error to select another folder
- **Loading**: If `album.json` exists in the folder, load it. Otherwise, create a new default album (First Page, one 2-page sprea (layout "2-3" and "3-2"), Last Page) and save it.
  - if the album.json has a different `photobook_version` than the current version, show a breaking error that it is not compatible and they should remove the file before reloading the page
  - show a spinner while loading
- **Saving**: Automatically save any changes to `album.json`.
- **Drag and Drop**:
  - Use the native HTML5 Drag and Drop API. Give visual feedback during drag operations
  - Drag images from the bank to any cell, if the cell had an image move it to image bank
  - Drag an image from one cell to another to swap them
  - Drag an image from a cell to the image bank to remove it and make it available in the image bank
- **Image Cropping**:
  - **Auto-Crop**: When an image is first dropped, automatically calculate the crop_x, crop_y, crop_width, crop_height attributes to fill (center-crop, fill cell completely cut off image parts if needed) the cell's aspect ratio, the goal is to show as much as possible of the image without showing any white space.
  - **Manual Crop**: On double-click, open a modal with `Croppie.js` to allow the user to refine the crop. Preset x, y, width, height and zoom to what we had in the `album.json` file. Converted to what Croppie.js expects.
  - **Displaying Crop**: The cropped image should be displayed within its cell using a container `div` with `overflow: hidden`. The `<img>` tag inside should be styled by a JavaScript function that calculates the required CSS `transform: scale(...) translate(...)` and explicit `width`/`height` in pixels. This function should receive the cell's rendered pixel dimensions as an argument to ensure accuracy; avoid having it query the DOM for dimensions itself.


# Technical details
- we will only use this on Chrome, no need for cross-browser support.
- this project is ran locally on the same macbook with a fixed screen resolution
- **HTML/CSS/JS**: A single `index.html` file.
- **JS Structure**: Structure the application's logic within a single Alpine.js factory function (e.g., `function photobookApp() { return { ... } }`). This promotes better code encapsulation and follows modern Alpine.js patterns.
- **UI Rendering**: Use Alpine.js's `x-for` templates to render the album pages, rows, and cells. Avoid generating large HTML strings in JavaScript to inject with `x-html`, as this complicates reactive styling and event handling.
- import libraries using cdn
  - bootstrap 5 & bootstrap icons
    - https://cdn.jsdelivr.net/npm/bootstrap@5.3.6/dist/css/bootstrap.min.css
    - https://cdn.jsdelivr.net/npm/bootstrap@5.3.6/dist/js/bootstrap.bundle.min.js
    - https://cdn.jsdelivr.net/npm/bootstrap-icons@1.13.1/font/bootstrap-icons.min.css
  - https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js for the UI logic
  - https://cdnjs.cloudflare.com/ajax/libs/croppie/2.6.5/croppie.min.js for crop on double click
  - https://cdn.jsdelivr.net/npm/exif-js@2.3.0/exif.js for date sorting
- **Forbidden Libraries**: Do not use `jQuery` 

Write the full code (A-Z) for the album builder in the index.html file, don't omit anything