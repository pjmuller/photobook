# Goal
Create a single `index.html` that displays a resizable, two-page photo album layout.

# Specifications

**Layout:**
  *   Display a two-page spread, with a left page and a right page appearing side-by-side (aspect ratio 35:29 per page)
  *   Together, the two pages should fluidly scale to fill the width of the browser window.
  *   Each page must contain a 2x3 grid (2 rows, with 3 cells in each row), 6 cells per page for a total of 12 cells across the entire spread.
  *   Each cell should display a unique placeholder image. You can use a service like `https://picsum.photos/` or `https://via.placeholder.com/`.

**Functionality:**
  *   The key feature is resizable gutters (shown as white space between cells, same size horizontal as vertical)
  *   The user must be able to drag the **horizontal space** between the two rows on each page to adjust their relative heights.
  *   The user must be able to drag the **vertical space** between the two cells within each row to adjust their relative widths.
  *   When resizing, the total page height and width must remain constant; dragging a gutter should only redistribute the space between the adjacent elements.

# Technical Requirements

*   Produce a single `index.html` file containing all necessary HTML, CSS, and JavaScript.
*   Use the [Bootstrap 5 CDN](https://getbootstrap.com/docs/5.3/getting-started/introduction/#cdn-links) for basic styling.
*   You can use any helper library you want, but keep it simple.
*   No need to remember any state

# Implementation Guide

**Recommended approach:** Use [Split.js](https://split.js.org/) for gutter resizing — it handles drag logic, cursor states, and size constraints automatically.

**Structure (nested containers):**
```
.spread (flex, gap for spine)
  └── .page (flex-column)
        ├── .row-top (flex)
        │     └── .cell × 3
        └── .row-bottom (flex)
              └── .cell × 3
```

**Key CSS:**
- Spread: `display: flex; gap: 10px` for spine between pages
- Pages: `flex: 1` to share width equally
- Cells: `overflow: hidden` with `img { object-fit: cover; width/height: 100% }`
- Maintain aspect ratio with `aspect-ratio: 70/29` on spread or calculate dimensions in JS

**Split.js setup:**
```js
// Vertical split (rows) per page
Split(['#row-top', '#row-bottom'], { direction: 'vertical', sizes: [50, 50] });

// Horizontal split (cells) per row
Split(document.querySelectorAll('.row .cell'), { direction: 'horizontal', sizes: [33, 34, 33] });
```

**Alternative:** Pure CSS Grid with manual drag — use `grid-template-columns: 1fr var(--gutter) 1fr var(--gutter) 1fr` and rebuild template on drag using `fr` units for fluid scaling.