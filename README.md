# Goal
Create a family album photobook creator as a single-page application.
The user assigns local images to predefined page layouts. The final deliverable of this tool is an `album.json` file that a separate process (out of scope of this project) can use to generate a PDF.

Prioritize simple, effective code, a clean UI, and a smooth user experience.

# Specification
- each page is 35cm wide and 29cm high
- 1cm margin from the outer edges
- 0.5cm gutter separates all rows and columns within the page content area
- Page Spreads:
  - The first page is a single page, displayed on the right.
  - All subsequent pages are displayed as double-page spreads (e.g., 2-3, 4-5).
  - The last page (e.g. page 6) is a single page, displayed on the left.
- an image can only be used once in the album


# Layouts
- Define base page dimensions (width, height, margin) using `cm` units in the CSS, ideally with CSS variables.
- For dynamic calculations in JavaScript, create helper functions to determine the precise pixel dimensions of the page content area, rows, and columns. These helpers are essential for accurate resize and crop calculations.
- Gutters between rows and columns should have a fixed pixel size within the JavaScript model to simplify the resizing logic.
- Use CSS Flexbox for the high-level structure of rows and columns.
- A Layout consists of rows, and each row is divided into columns (that consist of 1-12 bootstrap columns). 
  - the height of images within a row is always the same
- layouts contain placeholder cells, these show as dotted lines with "Drop image" in it
- Predefined Layouts
  - "1": 
    - 1 row, 1 column (full picture page)
    - symbol: '██'
  - "2-2": 50% height_percent each row
    - row 1: 2 columns, 6, 6 width_grid
    - row 2: 2 columns, 6, 6 width_grid
    - symbol: '██▌██▌\n██▌██▌'
  - "2-3": 50% height_percent each row
    - row 1: 2 columns, 4, 8 width_grid
    - row 2: 3 columns, 4, 4, 4 width_grid
    - symbol: '██▌██▌\n█▌█▌█▌'
  - "3-2": 50% height_percent each row
    - row 1: 3 columns, 4, 4, 4 width_grid
    - row 2: 2 columns, 6, 6 width_grid
    - symbol: '█▌█▌█▌\n██▌██▌'

# Change layout of a page
- A layout change icon (`bi-grid-fill`) should be visible on the top-left of a left page and top-right of a right page.
- It should not be active on the first and last single pages of the album. (these always have layout "1")
- Clicking the icon opens a small menu showing the 4 available layouts. Visualize the layouts using the unicode symbols block characters, not their codenames ("1", "2-2", "2-3", "3-2").
  - on click of a layout,make the change and close the menu
- you can change from any layout to any other layout
- rule of thumb: keep as much as possible of the attributes the same so that the user doesn't have to re-crop the images (`height_percent` or `width_grid`, `x`, `y`, `width`, `height`, `path`, ...)
- only recrop the images to fill the cells where we changed `height_percent` or `width_grid` for that cell
- when we change to a layout that can hold less images (e.g from 5 images to 4, 5 or 4 images to 1), returned the unused images to the image bank
- specific switch strategies:
  - from "2-3" to "2-2". Drop the 3rd image in the top row. Reset the `width_grid` of the top row to 6, 6
  - from "3-2" to "2-2". Drop the 3rd image in the bottom row. Reset the `width_grid` of the bottom row to 6, 6
  - from "3-2" to "2-3" (or vice versa). just swap the rows (and keep all attributes the same)
  - from any to "1". Keep the first image you find (top to bottom, left to right) and drop all the others (reactivate them in the bottom bar), reset the `height_percent` to 100%, `width_grid` to 12
  - from "1" to any, set the image in the top left cell. Reset the `height_percent` of the 2 rows to 50% and use default `width_grid` (6,6 or 4,4,4)
  - from "2-2" to "2-3" or "3-2". keep existing images, just add one extra column and reset `width_grid` in that row to 4, 4, 4
  - update the album.json file in the selected folder


# Resizing
- The user can resize rows and columns by dragging the gutters between them. The gutters should be invisible overlay elements that show a `row-resize` or `col-resize` cursor on hover.
- **Implementation Logic**:
  - On `mousedown` on a gutter, capture initial mouse coordinates and the initial `height_percent` or `width_grid` of the adjacent elements. Add `mousemove` and `mouseup` event listeners to the `document`.
  - **Coordinate Scaling**: The main album preview is scaled to fit the viewport. **This is critical:** All mouse movement deltas (e.g., `event.clientX - startX`) MUST be divided by the current album scale factor to get the real, unscaled pixel delta.
  - The unscaled pixel delta must be converted into a change in `%` or `grid units`. For example: `delta_percent = (unscaled_pixel_delta / container_pixel_height) * 100`.
  - Update the `height_percent` or `width_grid` values in the Alpine.js data model, letting the UI update reactively.
  - When resizing columns in a 3-column row, only the two columns adjacent to the dragged gutter should change their width; their combined width remains constant.
  - On `mouseup`, remove the event listeners and immediately trigger the auto-crop function for all images within the resized cells.

# UI
## top right Floating buttons
- Use a Bootstrap button group with icon-only buttons (`bi-*`). All buttons must have a tooltip on hover explaining their function or why they are disabled.
- **Navigation** btn-group: `bi-arrow-left` (Previous) and `bi-arrow-right` (Next).
- **Page Actions**:
  - `bi-plus`: Adds a new, empty double-page spread (with "2-2" layout) after the current view. Disabled button if viewing the last page. After add, switches to the new spread.
  - `bi-trash`: Deletes the current page spread after a confirmation dialog. Disabled for single pages.
  - `bi-arrow-left-right`: A dropdown button to move the current double-page spread left `bi-arrow-bar-left` or right `bi-arrow-bar-right`. Disabled for single pages, left disabled if it's the first spread, right disabled if it's the last spread.


## bottom panel (image bank)
- A 170px high, 100% width horizontally-scrolling panel with a dark background.
- Displays all images from the selected folder sorted based on the EXIF data
  - if the EXIF data is not available put at the end and then sort these by filename
- thumbs of all pictures of the selected folder
  - in their original aspect ratio
  - height of each image is 150px, width variable to keep aspect ratio
- not used images: show a `cursor: grab` to drag the image to the main area
- used images:
  - cursor `pointer`
  - gray out
  - when clicked, move to the page where it is used
- image hover
  - animation that makes it slightly bigger
  - no tooltip needed with filename, in general filenames are not important anywhere

## Main area
- The central area displays the current single page or spread.
- The page/spread should be scaled down proportionally to fit entirely within the main area's viewport.
- for first and last page, we show single page
- for all next pages, show the page spreads, e.g. page 2 & 3, 4 & 5 along side each other
- Display the page numbers in a single, unobtrusive element (e.g., bottom-center). Format: "Page 1 / 6", "Pages 2-3 / 6", "Pages 4-5 / 6", "Pages 6 / 6".

# Persistence & Data
Store all album data in `album.json` in the user's selected folder.
Do this after any CRUD operation.

```json
{
  "photobook_version": "0.1", // fixed version number, so we can change the format without breaking backwards compatibility
  "pages": [
    {
      "id": "UUID", // for easy reference
      "layout": "3-2", // (top row 3 columns, bottom row 2 columns) semi redundant as we can derive it from the rows and columns, though makes it easier for change layout logic
      "rows": [
        { // first row
          "height_percent": 30, // in % of the total height (29cm - 2cm edge margin - 0.5cm gutter)
          "columns": [
            {
              "width_grid": 4, // 1-10 (12 bootstrap columns total and we need at least 2 more images on this row)
              "path": "image1.jpg", // inside of the selected folder
              "x": 15, // for cropping: x on original image (in pixels)
              "y": 90,
              "width": 1265,
              "height": 834
            },
            { "width_grid": 4}, // 2nd column, waiting for an image to be dropped in
            { "width_grid": 4}, // 3rd column
          ]
        },
        { // 2nd row
          "height_percent": 70,
          "columns": [
            { "width_grid": 6}, // 1st column
            { "width_grid": 6}, // 2nd column
          ]
        },
      ]
    }
  ]
}
```

# Interactions
- **Initial State**: Show a single "Select Image Folder" button to trigger the file system access API
- **Folder Selection**: Use the `window.showDirectoryPicker()` API to allow the user to select a folder. Store the `directoryHandle` for later use (reading images, writing `album.json`).
  - if selected folder has no JPG files inside it show an error to select another folder
- **Loading**: If `album.json` exists in the folder, load it. Otherwise, create a new default album (First Page, one 2-page sprea (layout "2-3" and "3-2"), Last Page) and save it.
  - if the album.json has a different `photobook_version` than the current version, show a breaking error that it is not compatible and they should remove the file before reloading the page
  - show a spinner while loading
- **Saving**: Automatically save any changes (adding/moving images, resizing, layout changes) to `album.json`.
- **Drag and Drop**:
  - Use the native HTML5 Drag and Drop API.
  - Drag images from the bank to any cell, if the cell had an image move it to image bank
  - Drag an image from one cell to another to swap them
  - Drag an image from a cell to the image bank (or the gray area around the pages) to remove it and make it available in the image bank
- **Image Cropping**:
  - **Auto-Crop**: When an image is first dropped, automatically calculate the x, y, width, height attributes to fill (center-crop) the cell's aspect ratio, the goal is to show as much as possible of the image without showing any white space.
  - **Manual Crop**: On double-click, open a modal with `Croppie.js` to allow the user to refine the crop.
  - **Displaying Crop**: The cropped image should be displayed within its cell using a container `div` with `overflow: hidden`. The `<img>` tag inside should be styled by a JavaScript function that calculates the required CSS `transform: scale(...) translate(...)` and explicit `width`/`height` in pixels. This function should receive the cell's rendered pixel dimensions as an argument to ensure accuracy; avoid having it query the DOM for dimensions itself.


# Technical details
- we will only use this on Chrome, no need for cross-browser support
- this project is ran locally on a macbook
- **HTML/CSS/JS**: A single `index.html` file.
- **UI Rendering**: Use Alpine.js's `x-for` templates to render the album pages, rows, and columns. Avoid generating large HTML strings in JavaScript to inject with `x-html`, as this complicates reactive styling and event handling.
- import libraries using cdn
  - bootstrap 5 & bootstrap icons
  - alpinejs for the UI logic
  - https://cdnjs.cloudflare.com/ajax/libs/croppie/2.6.5/croppie.min.js for crop on double click
- https://cdn.jsdelivr.net/npm/exif-js@2.3.0/exif.js for date sorting
- **Forbidden Libraries**: Do not use `jQuery` 

Write the full code (A-Z) for the album builder in the index.html file, don't omit anything