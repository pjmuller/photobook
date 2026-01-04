import { CONFIG, LAYOUTS, calculateDefaultRowHeights, calculateDefaultCellWidths } from '../config'
import type { LayoutType } from '../config'
import type { Album, Page, Row, Cell } from '../types'

/**
 * Generate a UUID for page IDs
 */
function generateId(): string {
  return crypto.randomUUID()
}

/**
 * Create a default cell with specified width
 */
function createEmptyCell(width: number): Cell {
  return { width }
}

/**
 * Create a row with the given height and cell count
 */
function createRow(height: number, cellCount: number): Row {
  const widths = calculateDefaultCellWidths(cellCount)
  return {
    height,
    cells: widths.map(w => createEmptyCell(w)),
  }
}

/**
 * Create a page with the given layout
 */
export function createPage(layout: LayoutType): Page {
  const cellsPerRow = LAYOUTS[layout]
  const rowCount = cellsPerRow.length
  const heights = calculateDefaultRowHeights(rowCount)

  return {
    id: generateId(),
    layout,
    rows: cellsPerRow.map((cellCount, index) => createRow(heights[index], cellCount)),
  }
}

/**
 * Create a default album with one spread (left: 3-2, right: 2-3)
 */
export function createDefaultAlbum(): Album {
  return {
    photobook_version: CONFIG.PHOTOBOOK_VERSION,
    pages: [createPage('3-2'), createPage('2-3')],
  }
}

/**
 * Validate album.json structure
 */
export function validateAlbum(data: unknown): { valid: boolean; error?: string } {
  if (!data || typeof data !== 'object') {
    return { valid: false, error: 'Invalid album data' }
  }

  const album = data as Record<string, unknown>

  // Check version
  if (album.photobook_version !== CONFIG.PHOTOBOOK_VERSION) {
    return {
      valid: false,
      error: `Incompatible album version: ${album.photobook_version}. Expected ${CONFIG.PHOTOBOOK_VERSION}. Please remove album.json and reload.`,
    }
  }

  // Check pages array
  if (!Array.isArray(album.pages)) {
    return { valid: false, error: 'Invalid pages array' }
  }

  return { valid: true }
}

/**
 * Ensure album has even number of pages
 */
export function ensureEvenPages(album: Album): Album {
  if (album.pages.length % 2 !== 0) {
    // Remove last page if odd
    album.pages = album.pages.slice(0, -1)
  }
  return album
}

/**
 * Scan directory for JPG files
 */
export async function scanForImages(
  directoryHandle: FileSystemDirectoryHandle
): Promise<string[]> {
  const jpgFiles: string[] = []

  for await (const entry of (directoryHandle as any).values()) {
    if (entry.kind === 'file') {
      const name = entry.name.toLowerCase()
      if (name.endsWith('.jpg') || name.endsWith('.jpeg')) {
        jpgFiles.push(entry.name)
      }
    }
  }

  return jpgFiles.sort()
}

/**
 * Read album.json from directory
 */
export async function readAlbumJson(
  directoryHandle: FileSystemDirectoryHandle
): Promise<Album | null> {
  try {
    const fileHandle = await directoryHandle.getFileHandle('album.json')
    const file = await fileHandle.getFile()
    const text = await file.text()
    const data = JSON.parse(text)
    return data as Album
  } catch {
    // File doesn't exist or can't be read
    return null
  }
}

/**
 * Write album.json to directory
 */
export async function writeAlbumJson(
  directoryHandle: FileSystemDirectoryHandle,
  album: Album
): Promise<void> {
  const fileHandle = await directoryHandle.getFileHandle('album.json', { create: true })
  const writable = await fileHandle.createWritable()
  await writable.write(JSON.stringify(album, null, 2))
  await writable.close()
}

/**
 * Get file from directory
 */
export async function getImageFile(
  directoryHandle: FileSystemDirectoryHandle,
  filename: string
): Promise<File | null> {
  try {
    const fileHandle = await directoryHandle.getFileHandle(filename)
    return await fileHandle.getFile()
  } catch {
    return null
  }
}

/**
 * Create object URL for an image file
 */
export async function createImageUrl(
  directoryHandle: FileSystemDirectoryHandle,
  filename: string
): Promise<string | null> {
  const file = await getImageFile(directoryHandle, filename)
  if (!file) return null
  return URL.createObjectURL(file)
}

/**
 * Revoke object URL to free memory
 */
export function revokeImageUrl(url: string): void {
  if (url && url.startsWith('blob:')) {
    URL.revokeObjectURL(url)
  }
}

/**
 * Get natural dimensions of an image file
 */
export async function getImageDimensions(
  directoryHandle: FileSystemDirectoryHandle,
  filename: string
): Promise<{ width: number; height: number } | null> {
  const url = await createImageUrl(directoryHandle, filename)
  if (!url) return null

  return new Promise((resolve) => {
    const img = new Image()
    img.onload = () => {
      resolve({ width: img.naturalWidth, height: img.naturalHeight })
      revokeImageUrl(url)
    }
    img.onerror = () => {
      resolve(null)
      revokeImageUrl(url)
    }
    img.src = url
  })
}

/**
 * Check if a file exists in the directory
 */
export async function fileExists(
  directoryHandle: FileSystemDirectoryHandle,
  filename: string
): Promise<boolean> {
  try {
    await directoryHandle.getFileHandle(filename)
    return true
  } catch {
    return false
  }
}

/**
 * Get all image paths used in the album
 */
export function getUsedImages(album: Album): Set<string> {
  const used = new Set<string>()
  for (const page of album.pages) {
    for (const row of page.rows) {
      for (const cell of row.cells) {
        if (cell.path) {
          used.add(cell.path)
        }
      }
    }
  }
  return used
}

/**
 * Find which page/row/cell an image is in
 */
export function findImageLocation(
  album: Album,
  imagePath: string
): { pageIndex: number; rowIndex: number; cellIndex: number } | null {
  for (let pageIndex = 0; pageIndex < album.pages.length; pageIndex++) {
    const page = album.pages[pageIndex]
    for (let rowIndex = 0; rowIndex < page.rows.length; rowIndex++) {
      const row = page.rows[rowIndex]
      for (let cellIndex = 0; cellIndex < row.cells.length; cellIndex++) {
        if (row.cells[cellIndex].path === imagePath) {
          return { pageIndex, rowIndex, cellIndex }
        }
      }
    }
  }
  return null
}

