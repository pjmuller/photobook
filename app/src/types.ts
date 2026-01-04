import type { LayoutType } from './config'

// Focal point for image cropping (0.0 to 1.0 ratios)
export interface FocalPoint {
  x: number
  y: number
}

// A cell within a row - can be empty or contain an image
export interface Cell {
  width: number
  path?: string
  focalPoint?: FocalPoint
  zoom?: number
  // Computed crop values (in original image pixels)
  crop_x?: number
  crop_y?: number
  crop_width?: number
  crop_height?: number
}

// A row within a page
export interface Row {
  height: number
  cells: Cell[]
}

// A single page in the album
export interface Page {
  id: string
  layout: LayoutType
  rows: Row[]
}

// The complete album.json structure
export interface Album {
  photobook_version: string
  pages: Page[]
}

// Image metadata from the file system
export interface ImageInfo {
  path: string
  name: string
  dateTime?: Date
  naturalWidth?: number
  naturalHeight?: number
  objectUrl?: string
}

// Image dimensions
export interface ImageDimensions {
  width: number
  height: number
}

// Cell dimensions
export interface CellDimensions {
  width: number
  height: number
}

// Crop calculation result
export interface CropResult {
  crop_x: number
  crop_y: number
  crop_width: number
  crop_height: number
}

// CSS transform for displaying cropped image
export interface ImageTransform {
  scale: number
  translateX: number
  translateY: number
}

// Application state (extends Album with UI state)
export interface AlbumState {
  // Album data
  photobook_version: string
  pages: Page[]
  
  // UI state
  currentSpreadIndex: number
  isLoading: boolean
  error: string | null
  
  // File system state
  directoryHandle: FileSystemDirectoryHandle | null
  images: ImageInfo[]
  
  // Crop mode state
  cropModeCell: CropModeCellInfo | null
}

// Info about which cell is in crop mode
export interface CropModeCellInfo {
  pageId: string
  rowIndex: number
  cellIndex: number
}

// Drag data for image transfers
export interface DragData {
  type: 'bank' | 'cell'
  imagePath: string
  sourcePageId?: string
  sourceRowIndex?: number
  sourceCellIndex?: number
}

// Event payloads for component communication
export interface ImageDroppedPayload {
  pageId: string
  rowIndex: number
  cellIndex: number
  imagePath: string
  naturalWidth: number
  naturalHeight: number
}

export interface ImageSwappedPayload {
  fromPageId: string
  fromRowIndex: number
  fromCellIndex: number
  toPageId: string
  toRowIndex: number
  toCellIndex: number
}

export interface ImageRemovedPayload {
  pageId: string
  rowIndex: number
  cellIndex: number
}

export interface ResizePayload {
  pageId: string
  type: 'row' | 'cell'
  index: number
  rowIndex?: number // Only for cell resize
  delta: number
}

export interface CropUpdatePayload {
  pageId: string
  rowIndex: number
  cellIndex: number
  focalPoint?: FocalPoint
  zoom?: number
}

export interface LayoutChangePayload {
  pageId: string
  newLayout: LayoutType
}

