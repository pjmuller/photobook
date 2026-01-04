# Photobook Creator

A Vue 3 + TypeScript application for creating family photo albums with customizable layouts.

## Features

- **Multiple Page Layouts**: Choose from 4 different layouts per page (1, 2-2, 2-3, 3-2)
- **Drag & Drop**: Easily arrange photos by dragging from the image bank to cells
- **Smart Cropping**: Auto-crop with focal point and zoom controls
- **Gutter Resizing**: Resize rows and cells by dragging the gutters
- **EXIF Sorting**: Images are automatically sorted by capture date
- **Persistent Storage**: Album data is saved to `album.json` in your image folder

## Getting Started

### Prerequisites

- Node.js 18+
- pnpm (`npm install -g pnpm`)
- A modern browser with File System Access API support (Chrome recommended)

### Installation

```bash
cd app
pnpm install
```

### Development

```bash
pnpm dev
```

Open http://localhost:3000 in your browser.

### Build

```bash
pnpm build
```

The built files will be in the `dist` directory.

## Usage

1. Click "Select Image Folder" to choose a folder containing your JPG images
2. The app will load all images and display them in the bottom panel
3. Drag images from the bank to empty cells in the page spread
4. Use the layout switcher (grid icon) to change page layouts
5. Double-click an image to enter crop mode - pan and zoom to adjust
6. Drag gutters to resize rows and cells
7. Use the navigation buttons to move between spreads
8. Add, delete, or reorder spreads using the toolbar buttons

## Album.json Structure

The album data is saved to `album.json` in your selected folder:

```json
{
  "photobook_version": "2.0",
  "pages": [
    {
      "id": "uuid",
      "layout": "3-2",
      "rows": [
        {
          "height": 294,
          "cells": [
            {
              "width": 237,
              "path": "image.jpg",
              "focalPoint": { "x": 0.5, "y": 0.5 },
              "zoom": 1.0,
              "crop_x": 0,
              "crop_y": 0,
              "crop_width": 1200,
              "crop_height": 800
            }
          ]
        }
      ]
    }
  ]
}
```

## Keyboard Shortcuts

- `←` / `→`: Navigate between spreads
- `Esc`: Exit crop mode

## Tech Stack

- Vue 3 (Composition API)
- TypeScript
- Vite
- exifr (EXIF parsing)
- Bootstrap Icons

