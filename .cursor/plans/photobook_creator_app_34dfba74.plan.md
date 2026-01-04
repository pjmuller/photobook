---
name: Photobook Creator App
overview: Build a Vue 3 + TypeScript photobook creator using Vite, migrating the working crop/resize logic from the prototype while adding full album management features (file system access, persistence, multi-spread navigation, layout switching, and image bank).
todos:
  - id: setup
    content: Initialize Vite + Vue 3 + TS project with dependencies
    status: completed
  - id: types-config
    content: Create config.ts and types.ts with all constants and interfaces
    status: completed
    dependencies:
      - setup
  - id: crop-logic
    content: Port crop calculation functions from prototype to useCropCalculation.ts
    status: completed
    dependencies:
      - types-config
  - id: filesystem
    content: Implement useFileSystem.ts for directory picker and album.json persistence
    status: completed
    dependencies:
      - types-config
  - id: image-bank-logic
    content: Implement useImageBank.ts with EXIF sorting
    status: completed
    dependencies:
      - types-config
  - id: base-components
    content: Build PhotoCell, GutterComponent, RowComponent with Split.js
    status: completed
    dependencies:
      - crop-logic
  - id: page-components
    content: Build PageComponent, PageSpread with layout rendering
    status: completed
    dependencies:
      - base-components
  - id: toolbar
    content: Build ControlToolbar with navigation and page actions
    status: completed
    dependencies:
      - setup
  - id: image-bank-ui
    content: Build ImageBank component with thumbnails
    status: completed
    dependencies:
      - image-bank-logic
  - id: root-app
    content: Build AlbumApp root component integrating all pieces
    status: completed
    dependencies:
      - page-components
      - toolbar
      - image-bank-ui
      - filesystem
  - id: drag-drop
    content: Implement drag & drop between bank and cells
    status: completed
    dependencies:
      - root-app
  - id: layout-switch
    content: Implement layout switching with smart image preservation
    status: completed
    dependencies:
      - root-app
  - id: styling
    content: Apply clean minimal light theme styling
    status: completed
    dependencies:
      - root-app
---

# Photobook Creator Application

## Architecture Overview

```mermaid
graph TD
    subgraph root [AlbumApp - Root State Owner]
        State[albumState reactive object]
    end
    
    root --> Toolbar[ControlToolbar]
    root --> Spread[PageSpread]
    root --> Bank[ImageBank]
    
    Spread --> LeftPage[PageComponent - Left]
    Spread --> RightPage[PageComponent - Right]
    
    LeftPage --> Row1L[RowComponent]
    LeftPage --> GutterH1[GutterComponent - horizontal]
    LeftPage --> Row2L[RowComponent]
    
    Row1L --> Cell1[PhotoCell]
    Row1L --> GutterV1[GutterComponent - vertical]
    Row1L --> Cell2[PhotoCell]
```

## Tech Stack

- **Build**: Vite with TypeScript
- **Framework**: Vue 3 Composition API
- **Styling**: CSS with Bootstrap 5 (icons only, minimal utility use)
- **Dependencies**: Split.js (resizing), exifr (EXIF parsing)
- **Theme**: Clean & minimal light theme (white/gray, subtle shadows)

## Project Structure

```
photobook/
├── index.html
├── package.json
├── vite.config.ts
├── tsconfig.json
└── src/
    ├── main.ts
    ├── App.vue
    ├── config.ts                 # CONFIG constants
    ├── types.ts                  # TypeScript interfaces
    ├── composables/
    │   ├── useFileSystem.ts      # showDirectoryPicker, read/write album.json
    │   ├── useImageBank.ts       # EXIF sorting, image state management
    │   └── useCropCalculation.ts # Pure functions from prototype
    ├── components/
    │   ├── ControlToolbar.vue
    │   ├── PageSpread.vue
    │   ├── PageComponent.vue
    │   ├── RowComponent.vue
    │   ├── PhotoCell.vue
    │   ├── GutterComponent.vue
    │   └── ImageBank.vue
    └── styles/
        └── main.css
```

## Implementation Plan

### Phase 1: Project Setup

- Initialize Vite + Vue 3 + TypeScript project
- Install dependencies: `split.js`, `exifr`, `bootstrap-icons`
- Create `config.ts` with all dimension constants from spec
- Create `types.ts` with TypeScript interfaces for album.json structure

### Phase 2: Core Logic Migration

Port the working logic from [`grid_crop/00_opus_45.html`](grid_crop/00_opus_45.html):

- **`useCropCalculation.ts`**: Extract `calculateCrop()`, `computeMinScale()`, `zoomAboutPoint()`, `clampTranslate()`, `applyTransform()` as pure functions
- **Split.js integration**: Keep the proven resize approach, adapt for Vue's reactive system

### Phase 3: File System & Persistence

- **`useFileSystem.ts`**: Implement `showDirectoryPicker()` workflow
  - Scan for JPG files
  - Load existing `album.json` or create default (left: "3-2", right: "2-3")
  - Auto-save on mutations
  - Handle missing images gracefully

### Phase 4: Vue Components

Build components following the spec's hierarchy:

1. **AlbumApp** (root): Owns `albumState`, handles all mutations
2. **ControlToolbar**: Navigation arrows, add/delete/move spread buttons
3. **PageSpread**: Container for left/right pages + page counter
4. **PageComponent**: Single page with layout switcher icon, renders rows
5. **RowComponent**: Renders cells with vertical gutters between them
6. **PhotoCell**: Drop target, displays cropped image or placeholder, crop mode UI
7. **GutterComponent**: Reusable horizontal/vertical resize handle using Split.js
8. **ImageBank**: Bottom panel with EXIF-sorted thumbnails, drag source

### Phase 5: Image Bank & EXIF Sorting

- **`useImageBank.ts`**: 
  - Read all JPGs from directory
  - Extract EXIF DateTimeOriginal using `exifr`
  - Sort: images with EXIF by date, then images without by filename
  - Track used/unused state
  - Calculate thumbnail widths maintaining aspect ratio at 150px height

### Phase 6: Drag & Drop

Implement native HTML5 drag/drop:
- Drag from bank to cell (auto-crop on drop)
- Drag between cells (swap)
- Drag from cell to bank (remove)
- Visual feedback during drag operations

### Phase 7: Layout Switching

Implement the layout change logic from spec:
- Layouts: "1", "2-2", "2-3", "3-2"
- Layout switcher icon (top-left for left page, top-right for right page)
- Smart image preservation when switching layouts
- Return excess images to bank

### Phase 8: Styling

Clean & minimal light theme:
- White page backgrounds with subtle shadows
- Light gray app background
- Subtle borders and shadows
- Blue accent for active states (crop mode, hover)

## Key Files Reference

- **Crop logic to port**: [`grid_crop/00_opus_45.html`](grid_crop/00_opus_45.html) lines 448-534 (transform functions)
- **Split.js setup**: [`grid_crop/00_opus_45.html`](grid_crop/00_opus_45.html) lines 786-819
- **Spec layouts**: [`prompt_full_v3_vue.md`](prompt_full_v3_vue.md) lines 44-57
- **album.json structure**: [`prompt_full_v3_vue.md`](prompt_full_v3_vue.md) lines 194-231