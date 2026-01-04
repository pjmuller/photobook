# Goal

Start from grid/00_gpt_52.html and create me a new .html file that adds cropping functionality.

# Specifications

## Already implemented

**Layout:**
  *   Display a two-page spread, with a left page and a right page appearing side-by-side (aspect ratio 35:29 per page)
  *   Together, the two pages should fluidly scale to fill the width of the browser window.
  *   Each page must contain a 2x3 grid (2 rows, with 3 cells in each row), 6 cells per page for a total of 12 cells across the entire spread.
  *   Each cell should display a unique placeholder image via `https://picsum.photos/`

**Gutters:**
  *   The key feature is resizable gutters handled by split.js
  *   The user must be able to drag the **horizontal space** between the two rows on each page to adjust their relative heights.
  *   The user must be able to drag the **vertical space** between the two cells within each row to adjust their relative widths.
  *   When resizing, the total page height and width must remain constant; dragging a gutter should only redistribute the space between the adjacent elements.

## TODO: Cropping
*   The user must be able to crop the image, double check enter crop mode
    *   click outside the cell to exit crop mode
*   Provide a zoom slider, should never see whitespace (close to or within the cell)
    *   max zoom should be 5x
    *   default zoom should be 1x to fit to cover.
*   Be able to move (pan) the image within the cell (when zoomed in)
    *  constrained so the image always covers the cell (no whitespace),
*   Care for a great user experience
    *   make it clear which cell is in crop mode

# Technical Requirements
*   Produce a single `index.html` file containing all necessary HTML, CSS, and JavaScript.
*   This project is only ran on a macbook, never on touchscreens.
*   Use the [Bootstrap 5 CDN](https://getbootstrap.com/docs/5.3/getting-started/introduction/#cdn-links) for basic styling.
*   use https://unpkg.com/split.js/dist/split.min.js
*   You can use any helper library you want for cropping or use vanilla JS
*   No need to persist any state, just have a temporary state for the current loaded page cells.