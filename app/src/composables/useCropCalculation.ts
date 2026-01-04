import { CONFIG } from '../config'
import type { CropResult, ImageDimensions, CellDimensions, FocalPoint, ImageTransform } from '../types'

/**
 * Clamp a value between min and max
 */
export function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value))
}

/**
 * Calculate the crop rectangle from user intent (focalPoint, zoom) to pixel values
 * 
 * This is a pure function that converts the user's intent (where to look, how close)
 * into the exact pixel rectangle to crop from the original image.
 */
export function calculateCrop(
  imageDimensions: ImageDimensions,
  cellDimensions: CellDimensions,
  focalPoint: FocalPoint,
  zoom: number
): CropResult {
  const imgW = imageDimensions.width
  const imgH = imageDimensions.height
  const cellW = cellDimensions.width
  const cellH = cellDimensions.height

  // Calculate aspect ratios
  const imgAR = imgW / imgH
  const cellAR = cellW / cellH

  // Determine "cover" crop box at zoom: 1.0
  // This is the largest rectangle with cell's aspect ratio that fits in the image
  let baseCropW: number
  let baseCropH: number

  if (imgAR > cellAR) {
    // Image is wider than cell - height is the constraint
    baseCropH = imgH
    baseCropW = imgH * cellAR
  } else {
    // Image is narrower or same AR as cell - width is the constraint
    baseCropW = imgW
    baseCropH = imgW / cellAR
  }

  // Apply zoom: higher zoom = smaller crop rectangle (more magnified)
  const finalCropW = baseCropW / zoom
  const finalCropH = baseCropH / zoom

  // Calculate focal point in pixels on original image
  const focalX = focalPoint.x * imgW
  const focalY = focalPoint.y * imgH

  // Center the crop box over the focal point
  let crop_x = focalX - finalCropW / 2
  let crop_y = focalY - finalCropH / 2

  // Clamp to ensure crop box stays within image bounds
  crop_x = clamp(crop_x, 0, imgW - finalCropW)
  crop_y = clamp(crop_y, 0, imgH - finalCropH)

  return {
    crop_x,
    crop_y,
    crop_width: finalCropW,
    crop_height: finalCropH,
  }
}

/**
 * Calculate CSS transform for displaying cropped image in a cell
 * 
 * The image is not actually cropped - it's scaled and positioned so that
 * the crop area aligns with the cell boundaries.
 */
export function calculateImageTransform(
  cellDimensions: CellDimensions,
  cropResult: CropResult
): ImageTransform {
  const { width: cellW } = cellDimensions
  const { crop_x, crop_y, crop_width } = cropResult

  // Scale so crop area width matches cell width
  const scale = cellW / crop_width

  // Translate so crop area's top-left aligns with cell's top-left
  const translateX = -crop_x * scale
  const translateY = -crop_y * scale

  return { scale, translateX, translateY }
}

/**
 * Get CSS transform string from transform values
 */
export function getTransformStyle(transform: ImageTransform): string {
  return `scale(${transform.scale}) translate(${transform.translateX / transform.scale}px, ${transform.translateY / transform.scale}px)`
}

/**
 * Calculate the minimum scale needed to cover a cell (object-fit: cover)
 */
export function computeMinScale(
  imageDimensions: ImageDimensions,
  cellDimensions: CellDimensions
): number {
  const imgW = Math.max(1, imageDimensions.width)
  const imgH = Math.max(1, imageDimensions.height)
  const cellW = Math.max(1, cellDimensions.width)
  const cellH = Math.max(1, cellDimensions.height)

  return Math.max(cellW / imgW, cellH / imgH)
}

/**
 * Convert display state (scale, tx, ty) to user intent model (focalPoint, zoom)
 * Used when user pans/zooms via UI
 */
export function displayStateToIntent(
  imageDimensions: ImageDimensions,
  cellDimensions: CellDimensions,
  scale: number,
  tx: number,
  ty: number
): { focalPoint: FocalPoint; zoom: number } {
  const imgW = imageDimensions.width
  const imgH = imageDimensions.height
  const cellW = cellDimensions.width
  const cellH = cellDimensions.height

  // Calculate what point on the image is at the cell center
  const cellCenterX = cellW / 2
  const cellCenterY = cellH / 2

  // The image point at cell center
  const imgX = (cellCenterX - tx) / scale
  const imgY = (cellCenterY - ty) / scale

  // Convert to focal point (0-1 ratio)
  const focalPoint: FocalPoint = {
    x: clamp(imgX / imgW, 0, 1),
    y: clamp(imgY / imgH, 0, 1),
  }

  // Calculate zoom relative to minScale
  const minScale = computeMinScale(imageDimensions, cellDimensions)
  const zoom = clamp(scale / minScale, CONFIG.MIN_ZOOM, CONFIG.MAX_ZOOM)

  return { focalPoint, zoom }
}

/**
 * Convert user intent (focalPoint, zoom) to display state (scale, tx, ty)
 * Used when rendering the image
 */
export function intentToDisplayState(
  imageDimensions: ImageDimensions,
  cellDimensions: CellDimensions,
  focalPoint: FocalPoint,
  zoom: number
): { scale: number; tx: number; ty: number; minScale: number } {
  const imgW = imageDimensions.width
  const imgH = imageDimensions.height
  const cellW = cellDimensions.width
  const cellH = cellDimensions.height

  const minScale = computeMinScale(imageDimensions, cellDimensions)
  const scale = minScale * zoom

  // Calculate where the focal point is in image pixels
  const focalX = focalPoint.x * imgW
  const focalY = focalPoint.y * imgH

  // Position image so focal point is at cell center
  const cellCenterX = cellW / 2
  const cellCenterY = cellH / 2

  let tx = cellCenterX - focalX * scale
  let ty = cellCenterY - focalY * scale

  // Clamp translation to prevent whitespace
  const scaledImgW = imgW * scale
  const scaledImgH = imgH * scale
  const minTx = cellW - scaledImgW
  const minTy = cellH - scaledImgH

  tx = clamp(tx, minTx, 0)
  ty = clamp(ty, minTy, 0)

  return { scale, tx, ty, minScale }
}

/**
 * Zoom about a specific point (for wheel zoom)
 */
export function zoomAboutPoint(
  imageDimensions: ImageDimensions,
  cellDimensions: CellDimensions,
  currentScale: number,
  currentTx: number,
  currentTy: number,
  newScale: number,
  pointX: number, // relative to cell
  pointY: number  // relative to cell
): { scale: number; tx: number; ty: number } {
  const imgW = imageDimensions.width
  const imgH = imageDimensions.height
  const cellW = cellDimensions.width
  const cellH = cellDimensions.height

  // Clamp point to cell bounds
  const px = clamp(pointX, 0, cellW)
  const py = clamp(pointY, 0, cellH)

  // Calculate anchor point on image (what's under the cursor)
  const anchorX = (px - currentTx) / currentScale
  const anchorY = (py - currentTy) / currentScale

  // Apply new scale
  const minScale = computeMinScale(imageDimensions, cellDimensions)
  const clampedScale = Math.max(minScale, newScale)

  // Calculate new translation to keep anchor point stationary
  let tx = px - anchorX * clampedScale
  let ty = py - anchorY * clampedScale

  // Clamp translation to prevent whitespace
  const scaledImgW = imgW * clampedScale
  const scaledImgH = imgH * clampedScale
  const minTx = cellW - scaledImgW
  const minTy = cellH - scaledImgH

  tx = clamp(tx, minTx, 0)
  ty = clamp(ty, minTy, 0)

  return { scale: clampedScale, tx, ty }
}

/**
 * Pan the image (for drag)
 */
export function panImage(
  imageDimensions: ImageDimensions,
  cellDimensions: CellDimensions,
  scale: number,
  currentTx: number,
  currentTy: number,
  deltaX: number,
  deltaY: number
): { tx: number; ty: number } {
  const imgW = imageDimensions.width
  const imgH = imageDimensions.height
  const cellW = cellDimensions.width
  const cellH = cellDimensions.height

  let tx = currentTx + deltaX
  let ty = currentTy + deltaY

  // Clamp translation to prevent whitespace
  const scaledImgW = imgW * scale
  const scaledImgH = imgH * scale
  const minTx = cellW - scaledImgW
  const minTy = cellH - scaledImgH

  tx = clamp(tx, minTx, 0)
  ty = clamp(ty, minTy, 0)

  return { tx, ty }
}

/**
 * Update crop on cell resize while preserving focal point
 */
export function recalculateCropOnResize(
  imageDimensions: ImageDimensions,
  _oldCellDimensions: CellDimensions,
  newCellDimensions: CellDimensions,
  focalPoint: FocalPoint,
  zoom: number
): CropResult {
  // Simply recalculate crop with new cell dimensions
  // The focal point and zoom are preserved
  return calculateCrop(imageDimensions, newCellDimensions, focalPoint, zoom)
}

/**
 * Get default crop for a newly dropped image (centered, zoom 1.0)
 */
export function getDefaultCrop(
  imageDimensions: ImageDimensions,
  cellDimensions: CellDimensions
): { focalPoint: FocalPoint; zoom: number; crop: CropResult } {
  const focalPoint: FocalPoint = { x: 0.5, y: 0.5 }
  const zoom = CONFIG.MIN_ZOOM
  const crop = calculateCrop(imageDimensions, cellDimensions, focalPoint, zoom)
  return { focalPoint, zoom, crop }
}

/**
 * Convert slider value (0-100) to zoom (1.0 to MAX_ZOOM)
 */
export function sliderToZoom(sliderValue: number): number {
  const t = clamp(sliderValue, 0, 100) / 100
  return CONFIG.MIN_ZOOM + (CONFIG.MAX_ZOOM - CONFIG.MIN_ZOOM) * t
}

/**
 * Convert zoom (1.0 to MAX_ZOOM) to slider value (0-100)
 */
export function zoomToSlider(zoom: number): number {
  const t = (clamp(zoom, CONFIG.MIN_ZOOM, CONFIG.MAX_ZOOM) - CONFIG.MIN_ZOOM) / (CONFIG.MAX_ZOOM - CONFIG.MIN_ZOOM)
  return Math.round(t * 100)
}

