<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted, onUnmounted } from 'vue'
import type { Page, ImageInfo, FocalPoint, Album, AlbumState } from './types'
import type { LayoutType } from './config'
import { CONFIG, LAYOUTS, calculateDefaultRowHeights, calculateDefaultCellWidths } from './config'
import {
  createPage,
  createDefaultAlbum,
  validateAlbum,
  ensureEvenPages,
  readAlbumJson,
  writeAlbumJson,
  findImageLocation,
} from './composables/useFileSystem'
import { loadImagesFromDirectory, cleanupImageUrls } from './composables/useImageBank'
import { calculateCrop, getDefaultCrop, clamp } from './composables/useCropCalculation'
import ControlToolbar from './components/ControlToolbar.vue'
import PageSpread from './components/PageSpread.vue'
import ImageBank from './components/ImageBank.vue'

// Application state
const state = reactive<AlbumState>({
  photobook_version: CONFIG.PHOTOBOOK_VERSION,
  pages: [],
  currentSpreadIndex: 0,
  isLoading: false,
  error: null,
  directoryHandle: null,
  images: [],
  cropModeCell: null,
})

// Confirmation dialog state
const showDeleteConfirm = ref(false)

// Computed properties
const totalSpreads = computed(() => Math.floor(state.pages.length / 2))
const isFirstSpread = computed(() => state.currentSpreadIndex === 0)
const isLastSpread = computed(() => state.currentSpreadIndex >= totalSpreads.value - 1)

const leftPageIndex = computed(() => state.currentSpreadIndex * 2)
const rightPageIndex = computed(() => state.currentSpreadIndex * 2 + 1)

const leftPage = computed(() => state.pages[leftPageIndex.value])
const rightPage = computed(() => state.pages[rightPageIndex.value])

const pageLabel = computed(() => `Page ${state.currentSpreadIndex + 1} / ${totalSpreads.value}`)

const usedImagePaths = computed(() => {
  const used = new Set<string>()
  for (const page of state.pages) {
    for (const row of page.rows) {
      for (const cell of row.cells) {
        if (cell.path) used.add(cell.path)
      }
    }
  }
  return used
})

const imageMap = computed(() => {
  const map = new Map<string, ImageInfo>()
  for (const img of state.images) {
    map.set(img.path, img)
  }
  return map
})

const isAlbumLoaded = computed(() => state.pages.length > 0)

// Crop mode computed
const cropModePageId = computed(() => state.cropModeCell?.pageId ?? null)
const cropModeRowIndex = computed(() => state.cropModeCell?.rowIndex ?? null)
const cropModeCellIndex = computed(() => state.cropModeCell?.cellIndex ?? null)

// Debounced save
let saveTimeout: number | null = null

async function saveAlbum() {
  if (!state.directoryHandle) return
  
  const album: Album = {
    photobook_version: state.photobook_version,
    pages: state.pages,
  }
  
  await writeAlbumJson(state.directoryHandle, album)
}

function debouncedSave() {
  if (saveTimeout) clearTimeout(saveTimeout)
  saveTimeout = window.setTimeout(() => {
    saveAlbum()
  }, 500)
}

// Watch for state changes and auto-save
watch(
  () => state.pages,
  () => {
    if (isAlbumLoaded.value) {
      debouncedSave()
    }
  },
  { deep: true }
)

// Select folder
async function selectFolder() {
  try {
    state.isLoading = true
    state.error = null
    
    // Request directory access
    const handle = await (window as any).showDirectoryPicker()
    state.directoryHandle = handle
    
    // Load images with EXIF data
    const images = await loadImagesFromDirectory(handle)
    
    if (images.length === 0) {
      state.error = 'No JPG images found in the selected folder. Please select a folder with images.'
      state.isLoading = false
      return
    }
    
    state.images = images
    
    // Try to load existing album.json
    const existingAlbum = await readAlbumJson(handle)
    
    if (existingAlbum) {
      // Validate album
      const validation = validateAlbum(existingAlbum)
      if (!validation.valid) {
        state.error = validation.error || 'Invalid album.json'
        state.isLoading = false
        return
      }
      
      // Ensure even pages
      const album = ensureEvenPages(existingAlbum)
      state.pages = album.pages
      
      // If pages were removed, save immediately
      if (album.pages.length !== existingAlbum.pages.length) {
        await saveAlbum()
      }
    } else {
      // Create new album
      const album = createDefaultAlbum()
      state.pages = album.pages
      await saveAlbum()
    }
    
    state.currentSpreadIndex = 0
    state.isLoading = false
  } catch (err) {
    if ((err as Error).name === 'AbortError') {
      // User cancelled
      state.isLoading = false
      return
    }
    state.error = `Error accessing folder: ${(err as Error).message}`
    state.isLoading = false
  }
}

// Navigation
function navigate(direction: 'prev' | 'next') {
  if (direction === 'prev' && !isFirstSpread.value) {
    state.currentSpreadIndex--
  } else if (direction === 'next' && !isLastSpread.value) {
    state.currentSpreadIndex++
  }
}

// Add spread
function addSpread() {
  const newLeft = createPage('2-2')
  const newRight = createPage('2-2')
  
  // Insert after current spread
  const insertIndex = (state.currentSpreadIndex + 1) * 2
  state.pages.splice(insertIndex, 0, newLeft, newRight)
  
  // Navigate to new spread
  state.currentSpreadIndex++
}

// Delete spread
function confirmDeleteSpread() {
  showDeleteConfirm.value = true
}

function cancelDelete() {
  showDeleteConfirm.value = false
}

function deleteSpread() {
  if (totalSpreads.value <= 1) return
  
  // Remove current spread pages
  const removeIndex = state.currentSpreadIndex * 2
  state.pages.splice(removeIndex, 2)
  
  // Adjust current index if needed
  if (state.currentSpreadIndex >= totalSpreads.value) {
    state.currentSpreadIndex = totalSpreads.value - 1
  }
  
  showDeleteConfirm.value = false
}

// Move spread
function moveSpread(direction: 'left' | 'right') {
  const currentIndex = state.currentSpreadIndex * 2
  
  if (direction === 'left' && state.currentSpreadIndex > 0) {
    // Swap with previous spread
    const prevIndex = (state.currentSpreadIndex - 1) * 2
    const temp = [state.pages[currentIndex], state.pages[currentIndex + 1]]
    state.pages[currentIndex] = state.pages[prevIndex]
    state.pages[currentIndex + 1] = state.pages[prevIndex + 1]
    state.pages[prevIndex] = temp[0]
    state.pages[prevIndex + 1] = temp[1]
    state.currentSpreadIndex--
  } else if (direction === 'right' && state.currentSpreadIndex < totalSpreads.value - 1) {
    // Swap with next spread
    const nextIndex = (state.currentSpreadIndex + 1) * 2
    const temp = [state.pages[currentIndex], state.pages[currentIndex + 1]]
    state.pages[currentIndex] = state.pages[nextIndex]
    state.pages[currentIndex + 1] = state.pages[nextIndex + 1]
    state.pages[nextIndex] = temp[0]
    state.pages[nextIndex + 1] = temp[1]
    state.currentSpreadIndex++
  }
}

// Find page by ID
function findPage(pageId: string): Page | undefined {
  return state.pages.find(p => p.id === pageId)
}

// Layout change
function handleChangeLayout(pageId: string, newLayout: LayoutType) {
  const page = findPage(pageId)
  if (!page) return
  
  const oldLayout = page.layout
  if (oldLayout === newLayout) return
  
  // Collect existing images
  const existingImages: { path: string; focalPoint: FocalPoint; zoom: number; width?: number; height?: number }[] = []
  for (const row of page.rows) {
    for (const cell of row.cells) {
      if (cell.path) {
        const imgInfo = imageMap.value.get(cell.path)
        existingImages.push({
          path: cell.path,
          focalPoint: cell.focalPoint || { x: 0.5, y: 0.5 },
          zoom: cell.zoom || CONFIG.MIN_ZOOM,
          width: imgInfo?.naturalWidth,
          height: imgInfo?.naturalHeight,
        })
      }
    }
  }
  
  // Create new layout structure
  const newCellsPerRow = LAYOUTS[newLayout]
  const rowCount = newCellsPerRow.length
  const heights = calculateDefaultRowHeights(rowCount)
  
  const newRows = newCellsPerRow.map((cellCount, rowIndex) => {
    const widths = calculateDefaultCellWidths(cellCount)
    return {
      height: heights[rowIndex],
      cells: widths.map(w => ({ width: w } as any)),
    }
  })
  
  // Place images into new cells (top-left to bottom-right)
  let imgIndex = 0
  
  for (let rowIdx = 0; rowIdx < newRows.length && imgIndex < existingImages.length; rowIdx++) {
    for (let cellIdx = 0; cellIdx < newRows[rowIdx].cells.length && imgIndex < existingImages.length; cellIdx++) {
      const img = existingImages[imgIndex]
      const cell = newRows[rowIdx].cells[cellIdx]
      
      cell.path = img.path
      cell.focalPoint = img.focalPoint
      cell.zoom = img.zoom
      
      // Recalculate crop for new cell dimensions
      if (img.width && img.height) {
        const crop = calculateCrop(
          { width: img.width, height: img.height },
          { width: cell.width, height: newRows[rowIdx].height },
          img.focalPoint,
          img.zoom
        )
        Object.assign(cell, crop)
      }
      
      imgIndex++
    }
  }
  
  // Update page
  page.layout = newLayout
  page.rows = newRows
}

// Resize handlers
let resizeStartValues: { heights?: number[]; widths?: number[] } = {}

function handleResizeRowStart(pageId: string, _rowIndex: number) {
  const page = findPage(pageId)
  if (!page) return
  resizeStartValues.heights = page.rows.map(r => r.height)
}

function handleResizeRow(pageId: string, rowIndex: number, delta: number) {
  const page = findPage(pageId)
  if (!page || !resizeStartValues.heights) return
  
  const totalRows = page.rows.length
  if (rowIndex >= totalRows - 1) return
  
  const row1 = page.rows[rowIndex]
  const row2 = page.rows[rowIndex + 1]
  
  const startHeight1 = resizeStartValues.heights[rowIndex]
  const startHeight2 = resizeStartValues.heights[rowIndex + 1]
  
  // Calculate new heights
  let newHeight1 = startHeight1 + delta
  let newHeight2 = startHeight2 - delta
  
  // Enforce minimums
  const maxHeight1 = startHeight1 + startHeight2 - CONFIG.ROW_MIN_HEIGHT
  
  newHeight1 = clamp(newHeight1, CONFIG.ROW_MIN_HEIGHT, maxHeight1)
  newHeight2 = startHeight1 + startHeight2 - newHeight1
  
  row1.height = newHeight1
  row2.height = newHeight2
  
  // Recalculate crops for affected rows
  recalculateCropsForRow(page, rowIndex)
  recalculateCropsForRow(page, rowIndex + 1)
}

function handleResizeRowEnd(_pageId: string, _rowIndex: number, _delta: number) {
  resizeStartValues = {}
}

function handleResizeCellStart(pageId: string, rowIndex: number, _cellIndex: number) {
  const page = findPage(pageId)
  if (!page) return
  resizeStartValues.widths = page.rows[rowIndex].cells.map(c => c.width)
}

function handleResizeCell(pageId: string, rowIndex: number, cellIndex: number, delta: number) {
  const page = findPage(pageId)
  if (!page || !resizeStartValues.widths) return
  
  const row = page.rows[rowIndex]
  const totalCells = row.cells.length
  if (cellIndex >= totalCells - 1) return
  
  const cell1 = row.cells[cellIndex]
  const cell2 = row.cells[cellIndex + 1]
  
  const startWidth1 = resizeStartValues.widths[cellIndex]
  const startWidth2 = resizeStartValues.widths[cellIndex + 1]
  
  // Calculate new widths
  let newWidth1 = startWidth1 + delta
  let newWidth2 = startWidth2 - delta
  
  // Enforce minimums
  const maxWidth1 = startWidth1 + startWidth2 - CONFIG.CELL_MIN_WIDTH
  
  newWidth1 = clamp(newWidth1, CONFIG.CELL_MIN_WIDTH, maxWidth1)
  newWidth2 = startWidth1 + startWidth2 - newWidth1
  
  cell1.width = newWidth1
  cell2.width = newWidth2
  
  // Recalculate crops for affected cells
  recalculateCropForCell(page, rowIndex, cellIndex)
  recalculateCropForCell(page, rowIndex, cellIndex + 1)
}

function handleResizeCellEnd(_pageId: string, _rowIndex: number, _cellIndex: number, _delta: number) {
  resizeStartValues = {}
}

// Recalculate crop for a cell
function recalculateCropForCell(page: Page, rowIndex: number, cellIndex: number) {
  const row = page.rows[rowIndex]
  const cell = row.cells[cellIndex]
  
  if (!cell.path) return
  
  const imgInfo = imageMap.value.get(cell.path)
  if (!imgInfo?.naturalWidth || !imgInfo?.naturalHeight) return
  
  const crop = calculateCrop(
    { width: imgInfo.naturalWidth, height: imgInfo.naturalHeight },
    { width: cell.width, height: row.height },
    cell.focalPoint || { x: 0.5, y: 0.5 },
    cell.zoom || CONFIG.MIN_ZOOM
  )
  
  Object.assign(cell, crop)
}

// Recalculate crops for all cells in a row
function recalculateCropsForRow(page: Page, rowIndex: number) {
  const row = page.rows[rowIndex]
  for (let cellIndex = 0; cellIndex < row.cells.length; cellIndex++) {
    recalculateCropForCell(page, rowIndex, cellIndex)
  }
}

// Crop mode handlers
function handleEnterCropMode(pageId: string, rowIndex: number, cellIndex: number) {
  state.cropModeCell = { pageId, rowIndex, cellIndex }
}

function handleExitCropMode() {
  state.cropModeCell = null
}

function handleUpdateCrop(pageId: string, rowIndex: number, cellIndex: number, focalPoint: FocalPoint, zoom: number) {
  const page = findPage(pageId)
  if (!page) return
  
  const cell = page.rows[rowIndex].cells[cellIndex]
  if (!cell.path) return
  
  cell.focalPoint = focalPoint
  cell.zoom = zoom
  
  // Recalculate crop values
  const imgInfo = imageMap.value.get(cell.path)
  if (imgInfo?.naturalWidth && imgInfo?.naturalHeight) {
    const crop = calculateCrop(
      { width: imgInfo.naturalWidth, height: imgInfo.naturalHeight },
      { width: cell.width, height: page.rows[rowIndex].height },
      focalPoint,
      zoom
    )
    Object.assign(cell, crop)
  }
}

// Image operations
function handleImageDrop(
  pageId: string,
  rowIndex: number,
  cellIndex: number,
  imagePath: string,
  naturalWidth: number,
  naturalHeight: number
) {
  const page = findPage(pageId)
  if (!page) return
  
  const cell = page.rows[rowIndex].cells[cellIndex]
  const row = page.rows[rowIndex]
  
  // If cell already has an image, it will be available in bank again
  // (no need to explicitly remove, just overwrite)
  
  // Set new image with default crop
  const { focalPoint, zoom, crop } = getDefaultCrop(
    { width: naturalWidth, height: naturalHeight },
    { width: cell.width, height: row.height }
  )
  
  cell.path = imagePath
  cell.focalPoint = focalPoint
  cell.zoom = zoom
  Object.assign(cell, crop)
}

function handleImageRemove(pageId: string, rowIndex: number, cellIndex: number) {
  const page = findPage(pageId)
  if (!page) return
  
  const cell = page.rows[rowIndex].cells[cellIndex]
  
  // Clear image data
  delete cell.path
  delete cell.focalPoint
  delete cell.zoom
  delete cell.crop_x
  delete cell.crop_y
  delete cell.crop_width
  delete cell.crop_height
}

function handleImageSwap(
  pageId: string,
  rowIndex: number,
  cellIndex: number,
  fromPageId: string,
  fromRowIndex: number,
  fromCellIndex: number
) {
  const toPage = findPage(pageId)
  const fromPage = findPage(fromPageId)
  if (!toPage || !fromPage) return
  
  const toCell = toPage.rows[rowIndex].cells[cellIndex]
  const fromCell = fromPage.rows[fromRowIndex].cells[fromCellIndex]
  const toRow = toPage.rows[rowIndex]
  const fromRow = fromPage.rows[fromRowIndex]
  
  // Store source image data
  const fromData = {
    path: fromCell.path,
    focalPoint: fromCell.focalPoint,
    zoom: fromCell.zoom,
  }
  
  // Store target image data (if any)
  const toData = toCell.path ? {
    path: toCell.path,
    focalPoint: toCell.focalPoint,
    zoom: toCell.zoom,
  } : null
  
  // Clear source cell
  delete fromCell.path
  delete fromCell.focalPoint
  delete fromCell.zoom
  delete fromCell.crop_x
  delete fromCell.crop_y
  delete fromCell.crop_width
  delete fromCell.crop_height
  
  // Move source to target
  if (fromData.path) {
    const imgInfo = imageMap.value.get(fromData.path)
    if (imgInfo?.naturalWidth && imgInfo?.naturalHeight) {
      const crop = calculateCrop(
        { width: imgInfo.naturalWidth, height: imgInfo.naturalHeight },
        { width: toCell.width, height: toRow.height },
        fromData.focalPoint || { x: 0.5, y: 0.5 },
        fromData.zoom || CONFIG.MIN_ZOOM
      )
      
      toCell.path = fromData.path
      toCell.focalPoint = fromData.focalPoint
      toCell.zoom = fromData.zoom
      Object.assign(toCell, crop)
    }
  }
  
  // Move target to source (if swap)
  if (toData?.path) {
    const imgInfo = imageMap.value.get(toData.path)
    if (imgInfo?.naturalWidth && imgInfo?.naturalHeight) {
      const crop = calculateCrop(
        { width: imgInfo.naturalWidth, height: imgInfo.naturalHeight },
        { width: fromCell.width, height: fromRow.height },
        toData.focalPoint || { x: 0.5, y: 0.5 },
        toData.zoom || CONFIG.MIN_ZOOM
      )
      
      fromCell.path = toData.path
      fromCell.focalPoint = toData.focalPoint
      fromCell.zoom = toData.zoom
      Object.assign(fromCell, crop)
    }
  }
}

// Navigate to image location
function handleNavigateToImage(imagePath: string) {
  const location = findImageLocation({ photobook_version: state.photobook_version, pages: state.pages }, imagePath)
  if (location) {
    state.currentSpreadIndex = Math.floor(location.pageIndex / 2)
  }
}

// Handle dropping image on bank (remove from cell)
function handleBankDrop(e: DragEvent) {
  e.preventDefault()
  
  const dataStr = e.dataTransfer?.getData('application/json')
  if (!dataStr) return
  
  try {
    const data = JSON.parse(dataStr)
    if (data.type === 'cell') {
      handleImageRemove(data.sourcePageId, data.sourceRowIndex, data.sourceCellIndex)
    }
  } catch {
    console.warn('Failed to parse drag data')
  }
}

// Keyboard shortcuts
function handleKeyDown(e: KeyboardEvent) {
  if (e.key === 'Escape' && state.cropModeCell) {
    handleExitCropMode()
  } else if (e.key === 'ArrowLeft' && !state.cropModeCell) {
    navigate('prev')
  } else if (e.key === 'ArrowRight' && !state.cropModeCell) {
    navigate('next')
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeyDown)
  cleanupImageUrls(state.images)
})
</script>

<template>
  <div class="app-container">
    <!-- Welcome screen -->
    <div v-if="!isAlbumLoaded && !state.isLoading" class="welcome-screen">
      <h1>Photobook Creator</h1>
      <p>Create beautiful photo albums by arranging your images in customizable layouts.</p>
      
      <div v-if="state.error" class="error-message">
        {{ state.error }}
      </div>
      
      <button class="btn btn-primary" @click="selectFolder">
        <i class="bi bi-folder2-open"></i>
        Select Image Folder
      </button>
    </div>
    
    <!-- Loading overlay -->
    <div v-if="state.isLoading" class="loading-overlay">
      <div class="spinner"></div>
      <p>Loading images...</p>
    </div>
    
    <!-- Main app layout -->
    <div v-if="isAlbumLoaded && !state.isLoading" class="app-layout">
      <!-- Header with toolbar -->
      <header class="app-header">
        <ControlToolbar
          :current-spread="state.currentSpreadIndex + 1"
          :total-spreads="totalSpreads"
          :is-first-spread="isFirstSpread"
          :is-last-spread="isLastSpread"
          @navigate="navigate"
          @add-spread="addSpread"
          @delete-spread="confirmDeleteSpread"
          @move-spread="moveSpread"
        />
      </header>
      
      <!-- Main content area -->
      <main class="app-main">
        <PageSpread
          v-if="leftPage && rightPage"
          :left-page="leftPage"
          :right-page="rightPage"
          :page-label="pageLabel"
          :images="imageMap"
          :crop-mode-page-id="cropModePageId"
          :crop-mode-row-index="cropModeRowIndex"
          :crop-mode-cell-index="cropModeCellIndex"
          @change-layout="handleChangeLayout"
          @resize-row-start="handleResizeRowStart"
          @resize-row="handleResizeRow"
          @resize-row-end="handleResizeRowEnd"
          @resize-cell-start="handleResizeCellStart"
          @resize-cell="handleResizeCell"
          @resize-cell-end="handleResizeCellEnd"
          @enter-crop-mode="handleEnterCropMode"
          @exit-crop-mode="handleExitCropMode"
          @update-crop="handleUpdateCrop"
          @image-drop="handleImageDrop"
          @image-remove="handleImageRemove"
          @image-swap="handleImageSwap"
        />
      </main>
      
      <!-- Image bank footer -->
      <footer class="app-footer" @drop="handleBankDrop" @dragover.prevent>
        <ImageBank
          :images="state.images"
          :used-paths="usedImagePaths"
          @navigate-to-image="handleNavigateToImage"
        />
      </footer>
    </div>
    
    <!-- Crop mode overlay -->
    <div
      v-if="state.cropModeCell"
      class="crop-overlay"
      @click="handleExitCropMode"
    ></div>
    
    <!-- Delete confirmation dialog -->
    <div v-if="showDeleteConfirm" class="dialog-overlay">
      <div class="dialog">
        <h3>Delete Spread</h3>
        <p>Are you sure you want to delete this spread? This will remove both pages and return any images to the bank.</p>
        <div class="dialog-actions">
          <button class="btn" @click="cancelDelete">Cancel</button>
          <button class="btn btn-danger" @click="deleteSpread">Delete</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.welcome-screen {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 24px;
  padding: 40px;
}

.welcome-screen h1 {
  font-size: 32px;
  font-weight: 600;
  color: var(--color-text);
}

.welcome-screen p {
  font-size: 16px;
  color: var(--color-text-muted);
  text-align: center;
  max-width: 400px;
}

.loading-overlay {
  position: fixed;
  inset: 0;
  background: rgba(255, 255, 255, 0.95);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  z-index: 1000;
}

.loading-overlay p {
  font-size: 14px;
  color: var(--color-text-muted);
}

.error-message {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid var(--color-danger);
  color: var(--color-danger);
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 14px;
  max-width: 400px;
  text-align: center;
}

.app-layout {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.app-header {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding: 12px 20px;
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
}

.app-main {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  overflow: auto;
}

.app-footer {
  flex-shrink: 0;
}

.crop-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.2);
  z-index: 5;
  cursor: not-allowed;
}

.dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog {
  background: var(--color-surface);
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
  padding: 24px;
  max-width: 400px;
  width: 90%;
}

.dialog h3 {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 12px;
}

.dialog p {
  font-size: 14px;
  color: var(--color-text-muted);
  margin-bottom: 20px;
  line-height: 1.5;
}

.dialog-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}
</style>
