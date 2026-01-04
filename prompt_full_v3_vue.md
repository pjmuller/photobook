# Goal
Create a family album photobook creator as a single-page application.
The user assigns local images to predefined page layouts. The final deliverable of this tool is an `album.json` file that a separate process (out of scope of this project) can use to generate a PDF.

Prioritize simple, effective code, a clean UI, and a smooth user experience.

# Specification
- we only support JPG images
- we work with fixed pixel dimensions, no need to scale to the viewport. Grouped into a single configuration object at the top of the script for easy reference and modification.
  ```js
  const CONFIG = { // all values are in pixels
    PAGE_OUTER_MARGIN: 20,
    PAGE_WIDTH: 730,
    PAGE_HEIGHT: 598,
    ROW_MIN_HEIGHT: 100, // MAX depends on the number of rows: `PAGE_HEIGHT - ((ROW_COUNT - 1) * (ROW_MIN_HEIGHT + PAGE_GUTTER))`
    CELL_MIN_WIDTH: 100, // MAX depends on the number of cells in a row: `PAGE_WIDTH - ((CELL_COUNT - 1) * (CELL_MIN_WIDTH + PAGE_GUTTER))`
    PAGE_GUTTER: 10, // used in between of rows and columns, e.g. if a row is divided into 3 cells, each cell will have width of `(PAGE_WIDTH - (2 * PAGE_GUTTER)) / 3`
    PHOTOBOOK_VERSION: "2.0"
  };
  ```
- The photobook should be displayed as a series of two-page spreads.
  - Each spread consists of a left page and a right page.
  - The first spread displays `album.json[0]` on the left and `album.json[1]` on the right.
  - Subsequent spreads continue this pattern: the second spread shows `album.json[2]` and `album.json[3]`, and so on.
  - If the album should always have an even number of pages. If not, omit the last entry.
- This album generator doesn't handle the book cover, it only cares about the inner spread pages.
- Display a page counter in the format `Page X / Y`, where `X` is the current spread number and `Y` is the total number of spreads. For example: `Page 1 / 15`. The total number of spreads is `album.length / 2`.

# Grid Calculation Strategy
- All page, row, cell, and gutter dimensions must be calculated in **JavaScript** to final **pixel** values, which are then applied via inline styles. This ensures the resizing logic is perfectly synchronized with the rendered output.
- Gutters must be implemented as separate `div` elements, not as CSS `margin` or `gap`.
- Avoid using CSS `calc()`, `flex-basis` percentages, or the `gap` property for the core layout, as the JavaScript needs full, explicit control over dimensions.
- The JS logic must calculate the "net" available space for rows and cells.
  - **Row Height Calculation:** For a page with `N` rows, the height of each row is `(CONFIG.PAGE_HEIGHT - (N - 1) * CONFIG.PAGE_GUTTER) / N`.
  - **Cell Width Calculation:** For a row with `M` cells, the width of each cell is `(CONFIG.PAGE_WIDTH - (M - 1) * CONFIG.PAGE_GUTTER) / M`.
  - **Important for Distribution:** When calculating default widths/heights, use `Math.floor()` for all but the last element. The last element's size must be calculated as the remaining space to ensure the total perfectly matches `PAGE_WIDTH` or `PAGE_HEIGHT`, avoiding rounding errors.



# Layouts
- A Layout consists of rows, and each row is divided into 1, 2 or 3 cells. 
  - the height of images within a row is always the same
- layouts contain placeholder cells, these show as dotted lines with "Drop image" in it
- Predefined Layouts
  - "1": 
    - 1 row, 1 cell (full picture page)
    - cell height: `(PAGE_HEIGHT - (0 * PAGE_GUTTER))/1`, width: `(PAGE_WIDTH - (0 * PAGE_GUTTER))/1`
  - "2-2":
    - row 1: 2 cells
    - row 2: 2 cells
    - cell height: `(PAGE_HEIGHT - (1 * PAGE_GUTTER)) / 2`, width: `(PAGE_WIDTH - (1 * PAGE_GUTTER)) / 2`
  - "2-3":
    - row 1: 2 cells, cell height: `(PAGE_HEIGHT - (1 * PAGE_GUTTER)) / 2`, width: `(PAGE_WIDTH - (1 * PAGE_GUTTER)) / 2`
    - row 2: 3 cells, cell height: `(PAGE_HEIGHT - (1 * PAGE_GUTTER)) / 2`, width: `(PAGE_WIDTH - (2 * PAGE_GUTTER)) / 3`
  - "3-2":
    - row 1: 3 cells, cell height: `(PAGE_HEIGHT - (1 * PAGE_GUTTER)) / 2`, width: `(PAGE_WIDTH - (2 * PAGE_GUTTER)) / 3`
    - row 2: 2 cells, cell height: `(PAGE_HEIGHT - (1 * PAGE_GUTTER)) / 2`, width: `(PAGE_WIDTH - (1 * PAGE_GUTTER)) / 2`


# Change layout of a page
- A layout change icon (`bi-grid-fill`) should be visible on the top-left of a left page and top-right of a right page.
- Clicking the icon opens a submenu showing the 4 available layouts ("1", "2-2", "2-3", "3-2").
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
  - Update the `height` or `width` values in the Vue data model, letting the UI update reactively. Ensure the sum of the resized properties remains either `PAGE_WIDTH` or `PAGE_HEIGHT`.
  - continiously resize the cells (don't wait until the `mouseup` event), adjusting their crop to the new cell aspect ratio while preserving the user's custom `focalPoint` and `zoom` settings.
  - On `mouseup`, remove the event listeners.

# Image Intelligence: Cropping, Panning, and Zooming

To provide a seamless and professional experience, image handling is managed through a sophisticated "focal point" model. This separates user intent (what to look at, how close to be) from the final rendered output. The system will intelligently auto-crop images upon placement and provide intuitive tools for manual refinement.

**Data Model (in `album.json`):**
For each image placed in a cell, we store a core set of user-driven properties. All other display values are *derived* from these.
- `path`: The image filename.
- **User Intent Model (The Source of Truth)**:
  - `focalPoint`: An object `{x, y}` where `x` and `y` are ratios from `0.0` to `1.0`. This marks the most important spot in the image, as defined by the user. It acts as the anchor for all panning and zooming operations. Example: `{x: 0.5, y: 0.5}` is the exact center.
  - `zoom`: A float `>= 1.0`. This is a **magnification factor**. `zoom: 1.0` represents the base level where the image is scaled just large enough to "cover" the cell's area without leaving whitespace. `zoom: 2.0` means the image is magnified to be twice as large as that base "cover" state, effectively zooming in on the `focalPoint`.
- **Computed Output for PDF Generator**:
  - These values are calculated by the JS logic and stored so the PDF generator doesn't need to re-compute anything.
  - `crop_x`, `crop_y`, `crop_width`, `crop_height`: The precise pixel-based rectangle to be cropped from the original image. All these values **must always be non-negative pixel numbers (integers or floats), not `null` or `undefined`**.

**Auto-Crop on Drop:**
When an image is first dropped into a cell, the system **must** automatically calculate the optimal crop. The cell's image data should be fully initialized: `focalPoint` set to the center `{x: 0.5, y: 0.5}`, `zoom` set to the minimum value of `1.0`, and all `crop_x`, `crop_y`, `crop_width`, `crop_height` values immediately computed by calling the `calculateCrop` function.

**Manual Panning and Zooming:**
- **Panning:** When a user pans the image, the application is modifying the `focalPoint`. The `zoom` level remains unchanged. The `crop_*` values are recalculated in real-time.
- **Zooming:** When a user zooms, the application is modifying the `zoom` value. The `focalPoint` remains unchanged, ensuring the view stays centered on the point of interest. The `crop_*` values are recalculated in real-time.

**Core Calculation Logic (Model to Pixels):**
This must be implemented as a **pure function**, e.g., `calculateCrop(imageDimensions, cellDimensions, focalPoint, zoom)`. This function takes all necessary data as arguments and returns an object with the final `{ crop_x, crop_y, crop_width, crop_height }`. It must not have any side effects.

It must be executed whenever an image is dropped, a cell is resized, or the user manually pans or zooms.

*Calculation Steps:*
1.  **Inputs**: Original image dimensions (`imgW`, `imgH`), cell dimensions (`cellW`, `cellH`), `focalPoint`, and `zoom`.
2.  **Calculate Aspect Ratios**: `imgAR = imgW / imgH`, `cellAR = cellW / cellH`.
3.  **Determine "Cover" Crop Box at `zoom: 1.0`**: Find the dimensions of a rectangle that has the same aspect ratio as the cell but is scaled to fit within the original image. This represents the maximum possible view of the image within the cell's constraints.
    - If `imgAR > cellAR` (image is wider than cell), the base crop dimensions are `width = imgH * cellAR`, `height = imgH`.
    - If `imgAR <= cellAR` (image is narrower or same AR as cell), the base crop dimensions are `width = imgW`, `height = imgW / cellAR`.
    - Let's call these `baseCropW` and `baseCropH`.
4.  **Apply Zoom**: Scale the base crop box down by the `zoom` factor to create the final crop dimensions. A higher zoom value results in a smaller cropping rectangle (i.e., a "zoomed-in" view).
    - `finalCropW = baseCropW / zoom`
    - `finalCropH = baseCropH / zoom`
5.  **Position with Focal Point**: Determine the pixel coordinates of the focal point on the original image:
    - `focalX = focalPoint.x * imgW`
    - `focalY = focalPoint.y * imgH`
6.  **Calculate Top-Left Corner**: Center the final crop box over the focal point's pixel location.
    - `crop_x = focalX - (finalCropW / 2)`
    - `crop_y = focalY - (finalCropH / 2)`
7.  **Clamp to Bounds**: Crucially, ensure the crop box lies entirely within the original image. The calculated `crop_x` and `crop_y` must be adjusted to prevent any part of the crop area from being outside the image dimensions (`0, 0, imgW, imgH`).
    - `final_crop_x = Math.max(0, Math.min(crop_x, imgW - finalCropW))`
    - `final_crop_y = Math.max(0, Math.min(crop_y, imgH - finalCropH))`
8.  **Output**: The final, clamped values are stored in `album.json`:
    - `crop_x`: `final_crop_x`
    - `crop_y`: `final_crop_y`
    - `crop_width`: `finalCropW`
    - `crop_height`: `finalCropH`

**Displaying the Cropped Image in the UI:**
To display the cropped area within the cell `div` (which must have `overflow: hidden`), the inner `<img>` tag is not actually cropped, but rather scaled and shifted using CSS `transform`. This is highly efficient. A JavaScript function calculates the transform values based on the `album.json` crop data:
1.  **Inputs**: Cell dimensions (`cellW`, `cellH`) and the image's stored crop data (`crop_x`, `crop_y`, `crop_width`, `crop_height`).
2.  **Calculate Scale**: The image must be scaled so that the cropped area's width matches the cell's width.
    -   `scale = cellW / crop_width`
3.  **Calculate Translation**: The image must be shifted so that the top-left corner of the crop area aligns with the top-left corner of the cell.
    -   `translateX = -crop_x * scale`
    -   `translateY = -crop_y * scale`
4.  **Apply CSS**: The resulting inline style for the `<img>` tag would be:
    -   `transform: scale(${scale}) translate(${translateX}px, ${translateY}px);`
    -   `transform-origin: top left;`

# UI
## top right Floating buttons
- Use a Bootstrap button group with icon-only buttons (`bi-*`). All buttons must have a tooltip on hover explaining their function or why they are disabled.
- **Navigation** btn-group: `bi-arrow-left` (Previous) and `bi-arrow-right` (Next).
- **Page Actions**:
  - `bi-plus`: 
    - Adds a 2 new pages (each with "2-2" layout) indexed after the current spread
    - After add, change the pagination to view the new (empty) spread.
  - `bi-trash`: 
    - Deletes the current page spread after a confirmation dialog. both left and right page are deleted.
  - `bi-arrow-left-right`: 
    - A dropdown button to move the current double-page spread left `bi-arrow-bar-left` or right `bi-arrow-bar-right`. 


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
- Performance: It's ok that the whole UI is blocked by a spinner until we read all EXIF data. No need to batch process the images.

## Main area
- The central area displays the page spread.
- The spread always has a fixed size, and should NOT be scaled to fit the main area's viewport.
- One page spread shows 2 pages side by side
- Display the page spread number in a single, unobtrusive element (e.g., bottom-center). Format: "Page 1 / 6"

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
              "path": "image1.jpg", // Path to the image file within the selected folder. (don't store blob:null/... but the actual filename within the selected folder)
              "focalPoint": {"x": 0.5, "y": 0.5}, // The user-defined point of interest (0.0-1.0 ratio).
              "zoom": 1.0, // The user-defined zoom level, min 1.0 (base level where the image is scaled just large enough to "cover" the cell's area without leaving whitespace), max 3.0.
              // computed fields based on focalPoint and zoom
              "crop_x": 15, // x on original image (in pixels)
              "crop_y": 90, // original image y position
              "crop_width": 1265, // original image width
              "crop_height": 834, // original image height
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

## State Management
- All application state must be stored in a single, top-level reactive object created with `Vue.reactive()`. This object, named `albumState`, will be a direct representation of the `album.json` structure, plus any transient UI state (e.g., `currentSpreadIndex`).
- This `albumState` object will be managed exclusively within the root `AlbumApp` component.
- Child components must **not** directly modify the state. They receive data via `props` and communicate changes back to `AlbumApp` by emitting events with payloads (e.g., `@image-dropped="{ pageId, cellId, imagePath }"`). This enforces a strict one-way data flow.


# Interactions
- **Initial State**: Show a single "Select Image Folder" button to trigger the file system access API
- **Folder Selection**: Use the `window.showDirectoryPicker()` API to allow the user to select a folder. Store the `directoryHandle` for later use (reading images, writing `album.json`).
  - if selected folder has no JPG files inside it show an error to select another folder
- **Loading**: If `album.json` exists in the folder, load it. Otherwise, create a new album containing a single two-page spread. The left page will have the "3-2" layout and the right page will have the "2-3" layout. Both pages will be empty. Save this structure as album.json and then load it.
  - if the album.json has a different `photobook_version` than the current version, show a breaking error that it is not compatible and they should remove the file before reloading the page
  - if the album.json has an odd number of pages, the last page entry is discarded and the file is immediately re-saved. This ensures data integrity from the start. The page counter Y is always album.pages.length / 2.
  - show a spinner while loading
  - **Handling Missing Images:** If `album.json` is loaded and contains a reference to an image `path` that is no longer present in the directory, the application must not crash. It should render a "Missing Image" placeholder in that cell and log a warning to the developer console. The user should be able to drop a new image into that cell to replace the missing one.
- **Saving**: Automatically save any changes to `album.json`.
- **Drag and Drop**:
  - Use the native HTML5 Drag and Drop API. Give visual feedback during drag operations
  - Drag images from the bank to any cell, if the cell had an image move it to image bank
  - Drag an image from one cell to another to swap them
  - Drag an image from a cell to the image bank to remove it and make it available in the image bank
  - Crucially, dragging an image to or from a cell, or swapping images between cells, **must not alter the intrinsic dimensions (width or height) of any affected cells or rows**. Cell and row dimensions are fixed layout properties, determined solely by JavaScript calculations for the chosen layout or by user resizing through gutters, and are not content-dependent.
- **Image Cropping**:
  - **Auto-Crop**: When an image is first dropped, automatically calculate the crop to fill the cell (center-crop), covering the entire cell without showing white space.
  - **Manual Crop**: On double-click, The user can pan and zoom the image within the cell's aspect ratio. 
    - do not open a modal, show a Bootstrap range slider below the image. Make the cursor styled as not-allowed everywhere outside of the cell, or the slider.
    - when zooming in & out, keep the focal point in the same spot.
    - Be able to move the image within the cell (both horizontally and vertically). But always within bounds, never allow whitespaces to show.
    - double click to exit crop mode and reactivate the cell
      - when exiting crop mode, the user should be able to drag the image to another cell / image bank.
  - **Displaying Crop**: The cropped image is displayed within its cell using a container `div` with `overflow: hidden`. The `<img>` tag inside is positioned and scaled using CSS transforms calculated by a JavaScript function. This function receives the cell's dimensions and the image's crop data as arguments.
- **Performance:** To ensure the UI remains responsive even with hundreds of images, apply the `loading="lazy"` attribute to all `<img>` tags within the image bank.

# Technical details
- we will only use this on Chrome, no need for cross-browser support.
- this project is ran locally on the same macbook with a fixed screen resolution
- **HTML/CSS/JS**: A single `index.html` file.
- **JS Structure**: Structure the vue 3 (composition api) app 
  - multiple templates in a single file.
    ```html
    <template>
    <body>
      <div id="app">
        <foo-bar name="John" email="john@example.com"></foo-bar>
      </div>

      <template id="foo-bar-template">...</template>
    </body>
    </template>
    <script>
          const { createApp, ref, reactive, computed, onMounted, watch } = Vue;
          const FooBarComponent = {
            template: '#foo-bar-template',
            props: [],
            emits: [],
            setup(props) {
              // ...
            }
          };
    </script>
    ```
- import libraries using cdn
  - bootstrap 5 & bootstrap icons
    - https://cdn.jsdelivr.net/npm/bootstrap@5.3.6/dist/css/bootstrap.min.css
    - https://cdn.jsdelivr.net/npm/bootstrap@5.3.6/dist/js/bootstrap.bundle.min.js
    - https://cdn.jsdelivr.net/npm/bootstrap-icons@1.13.1/font/bootstrap-icons.min.css
  - https://unpkg.com/vue@3/dist/vue.global.js for the UI logic
  - https://cdn.jsdelivr.net/npm/exif-js@2.3.0/exif.js for date sorting
- **Forbidden Libraries**: Do not use `jQuery` 

Write the full code (A-Z) for the album builder in the index.html file, don't omit anything

## Vue.js Component Architecture

To create a clean, maintainable, and scalable application, the architecture will be broken down into small, focused components. This approach follows the **Single Responsibility Principle**, where each component does one thing well. It ensures that complex logic, like resizing, is encapsulated and reusable.

All state is managed in the root `AlbumApp` component and flows down to children via `props`. Children communicate changes back up to the root via `emits`, ensuring a predictable one-way data flow.

### Component Hierarchy and Data Flow

```
AlbumApp (Manages all state `albumState`)
├── ControlToolbar (Emits user actions like 'add-page')
│
├── PageSpread (Container for the two visible pages)
│   ├── PageComponent (Left Page)
│   │   ├── RowComponent (for each row in the page)
│   │   │   ├── PhotoCell (for each cell in the row)
│   │   │   ├── GutterComponent (vertical, between cells)
│   │   │   └── PhotoCell
│   │   ├── GutterComponent (horizontal, between rows)
│   │   └── RowComponent
│   │       └── ...
│   └── PageComponent (Right Page)
│       └── ...
│
└── ImageBank (Displays all available photos)
```


### Component Breakdown

-   **`AlbumApp` (Root Component)**
    -   **Responsibility:** The heart of the application.
        -   Owns the single reactive state object (`albumState`).
        -   Handles all data mutations (changing layouts, resizing, dropping images, etc.) in response to events from child components.
        -   Manages file system interactions (selecting folder, loading/saving `album.json`).
        -   Renders the main layout, including `ControlToolbar`, `PageSpread`, and `ImageBank`.

-   **`ControlToolbar`**
    -   **Responsibility:** Renders the main action buttons (navigation, add/delete spread, etc.). It is a "dumb" component that only displays data and reports user intent.
    -   **Props:** `isFirstSpread`, `isLastSpread` (to disable navigation buttons).
    -   **Emits:** `@navigate`, `@add-spread`, `@delete-spread`, `@move-spread`.

-   **`PageSpread`**
    -   **Responsibility:** A simple container that displays the current two-page spread (left and right pages) side-by-side. It also displays the page counter.
    -   **Props:** `leftPageData`, `rightPageData`, `pageNumberLabel`.
    -   **Emits:** Passes through all events from its `PageComponent` children up to `AlbumApp`.

-   **`PageComponent`**
    -   **Responsibility:** Renders a single page. It orchestrates the vertical layout by rendering `RowComponent`s and the horizontal `GutterComponent`s that separate them. It also manages the "Change Layout" UI for that page.
    -   **Props:** `pageData` (the full object for one page), `isLeftPage` (boolean, for positioning the layout icon).
    -   **Emits:** `@change-layout`, `@resize-row`, and passes through events from its children.

-   **`RowComponent` (New)**
    -   **Responsibility:** Renders a single row within a page. It orchestrates the horizontal layout by rendering `PhotoCell` components and the vertical `GutterComponent`s that separate them.
    -   **Props:** `rowData`, `pageId`, `rowIndex`.
    -   **Emits:** `@resize-cell`, and passes through events from its `PhotoCell` children.

-   **`PhotoCell`**
    -   **Responsibility:** The most granular view component. Renders a single photo slot. It displays either an image placeholder or the cropped image. It is the drop target for images and handles the UI for entering crop-editing mode.
    -   **Props:** `cellData`, `pageId`, `rowIndex`, `cellIndex` (these IDs are crucial for emitting precise events).
    -   **Emits:** `@image-dropped`, `@image-swapped`, `@image-removed`, `@edit-crop-start`.

-   **`GutterComponent` (New & Reusable)**
    -   **Responsibility:** A self-contained, reusable component that renders a single draggable gutter. It encapsulates all the `mousedown`/`mousemove`/`mouseup` logic for resizing. This isolates complex DOM event handling from layout components.
    -   **Props:** `orientation` ('vertical' or 'horizontal'), `index` (the index of the row/cell it follows).
    -   **Emits:** `@resize-start`, `@resize-end` with a payload containing the final pixel `delta`. The parent (`PageComponent` or `RowComponent`) is responsible for translating this delta into a state change.

-   **`ImageBank`**
    -   **Responsibility:** Renders the bottom panel of available images. Manages the display state of thumbnails (e.g., used vs. unused, hover effects).
    -   **Props:** `images` (array of all image objects, each with `path`, `isUsed`, etc.).
    -   **Emits:** `@image-drag-start`, `@navigate-to-image` (when a used image is clicked).