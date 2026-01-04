import exifr from 'exifr'
import type { ImageInfo } from '../types'
import { CONFIG } from '../config'

/**
 * Extract EXIF DateTimeOriginal from a file
 */
async function getExifDateTime(file: File): Promise<Date | undefined> {
  try {
    const exif = await exifr.parse(file, ['DateTimeOriginal'])
    if (exif?.DateTimeOriginal) {
      return new Date(exif.DateTimeOriginal)
    }
  } catch {
    // EXIF parsing failed, ignore
  }
  return undefined
}

/**
 * Get natural dimensions of an image from a blob URL
 */
function getImageNaturalDimensions(url: string): Promise<{ width: number; height: number }> {
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.onload = () => resolve({ width: img.naturalWidth, height: img.naturalHeight })
    img.onerror = reject
    img.src = url
  })
}

/**
 * Calculate thumbnail width for a given aspect ratio
 */
export function calculateThumbnailWidth(naturalWidth: number, naturalHeight: number): number {
  const aspectRatio = naturalWidth / naturalHeight
  return Math.round(CONFIG.THUMBNAIL_HEIGHT * aspectRatio)
}

/**
 * Load all images from a directory with EXIF data for sorting
 */
export async function loadImagesFromDirectory(
  directoryHandle: FileSystemDirectoryHandle
): Promise<ImageInfo[]> {
  const images: ImageInfo[] = []

  for await (const entry of (directoryHandle as any).values()) {
    if (entry.kind !== 'file') continue

    const name = entry.name.toLowerCase()
    if (!name.endsWith('.jpg') && !name.endsWith('.jpeg')) continue

    try {
      const fileHandle = await directoryHandle.getFileHandle(entry.name)
      const file = await fileHandle.getFile()

      // Get EXIF date
      const dateTime = await getExifDateTime(file)

      // Create object URL
      const objectUrl = URL.createObjectURL(file)

      // Get natural dimensions
      let naturalWidth = 0
      let naturalHeight = 0
      try {
        const dims = await getImageNaturalDimensions(objectUrl)
        naturalWidth = dims.width
        naturalHeight = dims.height
      } catch {
        // Failed to get dimensions, will be 0
      }

      images.push({
        path: entry.name,
        name: entry.name,
        dateTime,
        naturalWidth,
        naturalHeight,
        objectUrl,
      })
    } catch {
      console.warn(`Failed to load image: ${entry.name}`)
    }
  }

  // Sort images: those with EXIF date first (by date), then those without (by filename)
  return sortImagesByDate(images)
}

/**
 * Sort images by EXIF DateTimeOriginal, then by filename
 */
export function sortImagesByDate(images: ImageInfo[]): ImageInfo[] {
  const withDate = images.filter((img) => img.dateTime !== undefined)
  const withoutDate = images.filter((img) => img.dateTime === undefined)

  // Sort images with date by date (ascending)
  withDate.sort((a, b) => {
    return (a.dateTime?.getTime() || 0) - (b.dateTime?.getTime() || 0)
  })

  // Sort images without date by filename
  withoutDate.sort((a, b) => a.name.localeCompare(b.name))

  return [...withDate, ...withoutDate]
}

/**
 * Find image info by path
 */
export function findImageByPath(images: ImageInfo[], path: string): ImageInfo | undefined {
  return images.find((img) => img.path === path)
}

/**
 * Clean up object URLs when no longer needed
 */
export function cleanupImageUrls(images: ImageInfo[]): void {
  for (const image of images) {
    if (image.objectUrl) {
      URL.revokeObjectURL(image.objectUrl)
    }
  }
}

/**
 * Refresh object URL for a single image
 */
export async function refreshImageUrl(
  directoryHandle: FileSystemDirectoryHandle,
  imagePath: string
): Promise<string | null> {
  try {
    const fileHandle = await directoryHandle.getFileHandle(imagePath)
    const file = await fileHandle.getFile()
    return URL.createObjectURL(file)
  } catch {
    return null
  }
}

