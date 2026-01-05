// All dimension values are in pixels
export const CONFIG = {
  PAGE_OUTER_MARGIN: 20,
  PAGE_WIDTH: 730,
  PAGE_HEIGHT: 598,
  ROW_MIN_HEIGHT: 100,
  CELL_MIN_WIDTH: 100,
  PAGE_GUTTER: 10,
  PHOTOBOOK_VERSION: '2.0',
  MAX_ZOOM: 3.0,
  MIN_ZOOM: 1.0,
  THUMBNAIL_HEIGHT: 150,
} as const

// Row-based layout definitions: key is layout name, value is array of cell counts per row
export const ROW_LAYOUTS: Record<string, number[]> = {
  '1': [1],
  '2-2': [2, 2],
  '2-3': [2, 3],
  '3-2': [3, 2],
}

// Column-based layout definitions: key is layout name, value is array of cell counts per column
export const COLUMN_LAYOUTS: Record<string, number[]> = {
  '1-1': [1, 1],   // 2 columns, 1 cell each (full height)
  '1-2': [1, 2],   // 2 columns: left=1 full height, right=2 half height
  '2-1': [2, 1],   // 2 columns: left=2 half height, right=1 full height
}

// Combined layouts for backward compatibility
export const LAYOUTS: Record<LayoutType, number[]> = {
  ...ROW_LAYOUTS,
  ...COLUMN_LAYOUTS,
} as Record<LayoutType, number[]>

export type LayoutType = '1' | '2-2' | '2-3' | '3-2' | '1-1' | '1-2' | '2-1'

/**
 * Check if a layout is column-based
 */
export function isColumnLayout(layout: LayoutType): boolean {
  return layout in COLUMN_LAYOUTS
}

/**
 * Calculate default row heights for a given number of rows
 * Uses Math.floor for all but the last row to avoid rounding errors
 */
export function calculateDefaultRowHeights(rowCount: number): number[] {
  if (rowCount === 0) return []
  
  const totalGutterHeight = (rowCount - 1) * CONFIG.PAGE_GUTTER
  const availableHeight = CONFIG.PAGE_HEIGHT - totalGutterHeight
  const baseHeight = Math.floor(availableHeight / rowCount)
  
  const heights: number[] = []
  let remaining = availableHeight
  
  for (let i = 0; i < rowCount - 1; i++) {
    heights.push(baseHeight)
    remaining -= baseHeight
  }
  heights.push(remaining) // Last row gets remaining space
  
  return heights
}

/**
 * Calculate default cell widths for a given number of cells in a row
 * Uses Math.floor for all but the last cell to avoid rounding errors
 */
export function calculateDefaultCellWidths(cellCount: number): number[] {
  if (cellCount === 0) return []
  
  const totalGutterWidth = (cellCount - 1) * CONFIG.PAGE_GUTTER
  const availableWidth = CONFIG.PAGE_WIDTH - totalGutterWidth
  const baseWidth = Math.floor(availableWidth / cellCount)
  
  const widths: number[] = []
  let remaining = availableWidth
  
  for (let i = 0; i < cellCount - 1; i++) {
    widths.push(baseWidth)
    remaining -= baseWidth
  }
  widths.push(remaining) // Last cell gets remaining space
  
  return widths
}

/**
 * Get the maximum row height given other rows and gutter constraints
 */
export function getMaxRowHeight(rowCount: number): number {
  if (rowCount <= 1) return CONFIG.PAGE_HEIGHT
  return CONFIG.PAGE_HEIGHT - (rowCount - 1) * (CONFIG.ROW_MIN_HEIGHT + CONFIG.PAGE_GUTTER)
}

/**
 * Get the maximum cell width given other cells and gutter constraints
 */
export function getMaxCellWidth(cellCount: number): number {
  if (cellCount <= 1) return CONFIG.PAGE_WIDTH
  return CONFIG.PAGE_WIDTH - (cellCount - 1) * (CONFIG.CELL_MIN_WIDTH + CONFIG.PAGE_GUTTER)
}

/**
 * Calculate default column widths for a given number of columns
 * Uses Math.floor for all but the last column to avoid rounding errors
 */
export function calculateDefaultColumnWidths(columnCount: number): number[] {
  if (columnCount === 0) return []
  
  const totalGutterWidth = (columnCount - 1) * CONFIG.PAGE_GUTTER
  const availableWidth = CONFIG.PAGE_WIDTH - totalGutterWidth
  const baseWidth = Math.floor(availableWidth / columnCount)
  
  const widths: number[] = []
  let remaining = availableWidth
  
  for (let i = 0; i < columnCount - 1; i++) {
    widths.push(baseWidth)
    remaining -= baseWidth
  }
  widths.push(remaining) // Last column gets remaining space
  
  return widths
}

/**
 * Calculate default cell heights for a given number of cells in a column
 * Uses Math.floor for all but the last cell to avoid rounding errors
 */
export function calculateDefaultCellHeights(cellCount: number): number[] {
  if (cellCount === 0) return []
  
  const totalGutterHeight = (cellCount - 1) * CONFIG.PAGE_GUTTER
  const availableHeight = CONFIG.PAGE_HEIGHT - totalGutterHeight
  const baseHeight = Math.floor(availableHeight / cellCount)
  
  const heights: number[] = []
  let remaining = availableHeight
  
  for (let i = 0; i < cellCount - 1; i++) {
    heights.push(baseHeight)
    remaining -= baseHeight
  }
  heights.push(remaining) // Last cell gets remaining space
  
  return heights
}

/**
 * Get the maximum column width given other columns and gutter constraints
 */
export function getMaxColumnWidth(columnCount: number): number {
  if (columnCount <= 1) return CONFIG.PAGE_WIDTH
  return CONFIG.PAGE_WIDTH - (columnCount - 1) * (CONFIG.CELL_MIN_WIDTH + CONFIG.PAGE_GUTTER)
}

/**
 * Get the maximum cell height given other cells and gutter constraints
 */
export function getMaxCellHeight(cellCount: number): number {
  if (cellCount <= 1) return CONFIG.PAGE_HEIGHT
  return CONFIG.PAGE_HEIGHT - (cellCount - 1) * (CONFIG.ROW_MIN_HEIGHT + CONFIG.PAGE_GUTTER)
}

