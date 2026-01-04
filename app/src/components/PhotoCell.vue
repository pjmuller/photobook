<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { Cell, ImageInfo, FocalPoint } from '../types'
import { CONFIG } from '../config'
import {
  intentToDisplayState,
  displayStateToIntent,
  zoomAboutPoint,
  panImage,
  zoomToSlider,
  sliderToZoom,
  clamp,
} from '../composables/useCropCalculation'

const props = defineProps<{
  cell: Cell
  rowHeight: number
  pageId: string
  rowIndex: number
  cellIndex: number
  imageInfo?: ImageInfo
  isCropMode: boolean
}>()

const emit = defineEmits<{
  enterCropMode: []
  exitCropMode: []
  updateCrop: [focalPoint: FocalPoint, zoom: number]
  imageDrop: [imagePath: string, naturalWidth: number, naturalHeight: number]
  imageRemove: []
  imageSwap: [fromPageId: string, fromRowIndex: number, fromCellIndex: number]
}>()

// Display state
const scale = ref(1)
const tx = ref(0)
const ty = ref(0)
const minScale = ref(1)

// UI state
const isDragging = ref(false)
const isDropTarget = ref(false)
const cellRef = ref<HTMLDivElement | null>(null)

// Drag state
let dragStartX = 0
let dragStartY = 0
let dragStartTx = 0
let dragStartTy = 0

// Image dimensions
const imgDimensions = computed(() => {
  if (!props.imageInfo) return { width: 0, height: 0 }
  return {
    width: props.imageInfo.naturalWidth || 0,
    height: props.imageInfo.naturalHeight || 0,
  }
})

const cellDimensions = computed(() => ({
  width: props.cell.width,
  height: props.rowHeight,
}))

const hasImage = computed(() => !!props.cell.path && !!props.imageInfo)
const isMissing = computed(() => !!props.cell.path && !props.imageInfo)

// Slider value
const sliderValue = computed(() => {
  const zoom = props.cell.zoom || CONFIG.MIN_ZOOM
  return zoomToSlider(zoom)
})

// Transform style for the image
const imageStyle = computed(() => {
  if (!hasImage.value) return {}
  return {
    transform: `translate(${tx.value}px, ${ty.value}px) scale(${scale.value})`,
    transformOrigin: '0 0',
  }
})

// Update display state from props
function updateDisplayState() {
  if (!hasImage.value || imgDimensions.value.width === 0) return

  const focalPoint = props.cell.focalPoint || { x: 0.5, y: 0.5 }
  const zoom = props.cell.zoom || CONFIG.MIN_ZOOM

  const state = intentToDisplayState(
    imgDimensions.value,
    cellDimensions.value,
    focalPoint,
    zoom
  )

  scale.value = state.scale
  tx.value = state.tx
  ty.value = state.ty
  minScale.value = state.minScale
}

// Watch for changes and update display
watch(
  () => [props.cell, props.rowHeight, props.imageInfo],
  () => updateDisplayState(),
  { deep: true, immediate: true }
)

// Double click to enter/exit crop mode
function handleDoubleClick() {
  if (!hasImage.value) return
  
  if (props.isCropMode) {
    emit('exitCropMode')
  } else {
    emit('enterCropMode')
  }
}

// Mouse down for panning
function handleMouseDown(e: MouseEvent) {
  if (!props.isCropMode || e.button !== 0) return
  
  e.preventDefault()
  isDragging.value = true
  dragStartX = e.clientX
  dragStartY = e.clientY
  dragStartTx = tx.value
  dragStartTy = ty.value
  
  document.addEventListener('mousemove', handleMouseMove)
  document.addEventListener('mouseup', handleMouseUp)
}

function handleMouseMove(e: MouseEvent) {
  if (!isDragging.value) return
  
  const deltaX = e.clientX - dragStartX
  const deltaY = e.clientY - dragStartY
  
  const newPos = panImage(
    imgDimensions.value,
    cellDimensions.value,
    scale.value,
    dragStartTx,
    dragStartTy,
    deltaX,
    deltaY
  )
  
  tx.value = newPos.tx
  ty.value = newPos.ty
}

function handleMouseUp() {
  if (!isDragging.value) return
  
  isDragging.value = false
  document.removeEventListener('mousemove', handleMouseMove)
  document.removeEventListener('mouseup', handleMouseUp)
  
  // Emit crop update
  emitCropUpdate()
}

// Wheel zoom
function handleWheel(e: WheelEvent) {
  if (!props.isCropMode || !hasImage.value) return
  
  e.preventDefault()
  
  const rect = cellRef.value?.getBoundingClientRect()
  if (!rect) return
  
  const pointX = e.clientX - rect.left
  const pointY = e.clientY - rect.top
  
  const zoomStep = Math.exp(-e.deltaY * 0.001)
  const maxScale = minScale.value * CONFIG.MAX_ZOOM
  const newScale = clamp(scale.value * zoomStep, minScale.value, maxScale)
  
  const result = zoomAboutPoint(
    imgDimensions.value,
    cellDimensions.value,
    scale.value,
    tx.value,
    ty.value,
    newScale,
    pointX,
    pointY
  )
  
  scale.value = result.scale
  tx.value = result.tx
  ty.value = result.ty
  
  emitCropUpdate()
}

// Slider change
function handleSliderInput(e: Event) {
  const target = e.target as HTMLInputElement
  const value = parseInt(target.value, 10)
  const zoom = sliderToZoom(value)
  
  // Zoom around cell center
  const maxScale = minScale.value * CONFIG.MAX_ZOOM
  const newScale = clamp(minScale.value * zoom, minScale.value, maxScale)
  
  const centerX = cellDimensions.value.width / 2
  const centerY = cellDimensions.value.height / 2
  
  const result = zoomAboutPoint(
    imgDimensions.value,
    cellDimensions.value,
    scale.value,
    tx.value,
    ty.value,
    newScale,
    centerX,
    centerY
  )
  
  scale.value = result.scale
  tx.value = result.tx
  ty.value = result.ty
  
  emitCropUpdate()
}

// Reset crop to default
function handleReset() {
  const focalPoint = { x: 0.5, y: 0.5 }
  const zoom = CONFIG.MIN_ZOOM
  emit('updateCrop', focalPoint, zoom)
}

// Emit crop update to parent
function emitCropUpdate() {
  const intent = displayStateToIntent(
    imgDimensions.value,
    cellDimensions.value,
    scale.value,
    tx.value,
    ty.value
  )
  emit('updateCrop', intent.focalPoint, intent.zoom)
}

// Drag and drop handlers
function handleDragOver(e: DragEvent) {
  e.preventDefault()
  e.dataTransfer!.dropEffect = 'move'
  isDropTarget.value = true
}

function handleDragLeave() {
  isDropTarget.value = false
}

function handleDrop(e: DragEvent) {
  e.preventDefault()
  isDropTarget.value = false
  
  const dataStr = e.dataTransfer?.getData('application/json')
  if (!dataStr) return
  
  try {
    const data = JSON.parse(dataStr)
    
    if (data.type === 'bank') {
      // Dropping from bank
      emit('imageDrop', data.imagePath, data.naturalWidth, data.naturalHeight)
    } else if (data.type === 'cell') {
      // Swapping from another cell
      emit('imageSwap', data.sourcePageId, data.sourceRowIndex, data.sourceCellIndex)
    }
  } catch {
    console.warn('Failed to parse drag data')
  }
}

function handleDragStart(e: DragEvent) {
  if (!hasImage.value || props.isCropMode) {
    e.preventDefault()
    return
  }
  
  const data = {
    type: 'cell',
    imagePath: props.cell.path,
    sourcePageId: props.pageId,
    sourceRowIndex: props.rowIndex,
    sourceCellIndex: props.cellIndex,
  }
  
  e.dataTransfer!.setData('application/json', JSON.stringify(data))
  e.dataTransfer!.effectAllowed = 'move'
}

// Zoom display value
const zoomDisplay = computed(() => {
  const zoom = props.cell.zoom || CONFIG.MIN_ZOOM
  return `${zoom.toFixed(1)}×`
})
</script>

<template>
  <div
    ref="cellRef"
    class="cell"
    :class="{
      'crop-active': isCropMode,
      'is-dragging': isDragging,
      'drop-target': isDropTarget,
    }"
    :style="{
      width: `${cell.width}px`,
      height: `${rowHeight}px`,
    }"
    :draggable="hasImage && !isCropMode"
    @dblclick="handleDoubleClick"
    @mousedown="handleMouseDown"
    @wheel="handleWheel"
    @dragover="handleDragOver"
    @dragleave="handleDragLeave"
    @drop="handleDrop"
    @dragstart="handleDragStart"
  >
    <!-- Empty placeholder -->
    <div v-if="!cell.path" class="cell-placeholder">
      <i class="bi bi-image"></i>
      <span>Drop image</span>
    </div>
    
    <!-- Missing image -->
    <div v-else-if="isMissing" class="cell-missing">
      <i class="bi bi-exclamation-triangle"></i>
      <span>Missing image</span>
    </div>
    
    <!-- Image -->
    <img
      v-else-if="imageInfo?.objectUrl"
      :src="imageInfo.objectUrl"
      :style="imageStyle"
      class="cell-image"
      draggable="false"
    />
    
    <!-- Crop mode toolbar (positioned below cell) -->
    <Teleport to="body">
      <div v-if="isCropMode" class="crop-toolbar">
        <span class="label">Zoom</span>
        <input
          type="range"
          class="zoom-slider"
          min="0"
          max="100"
          :value="sliderValue"
          @input="handleSliderInput"
        />
        <span class="zoom-value">{{ zoomDisplay }}</span>
        <button class="btn" @click="handleReset">Reset</button>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.cell {
  position: relative;
  overflow: hidden;
  background: #f8f9fa;
  cursor: pointer;
  transition: box-shadow 0.15s ease;
  flex-shrink: 0;
}

.cell:hover:not(.crop-active) {
  box-shadow: inset 0 0 0 2px rgba(59, 130, 246, 0.2);
}

.cell.crop-active {
  box-shadow: inset 0 0 0 3px var(--color-accent);
  z-index: 10;
  cursor: grab;
}

.cell.crop-active.is-dragging {
  cursor: grabbing;
}

.cell.drop-target {
  box-shadow: inset 0 0 0 3px var(--color-accent);
  background: rgba(59, 130, 246, 0.1);
}

.cell-placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border: 2px dashed #dee2e6;
  border-radius: 4px;
  margin: 4px;
  color: #adb5bd;
  font-size: 13px;
}

.cell-placeholder i {
  font-size: 24px;
  opacity: 0.5;
}

.cell-missing {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: rgba(239, 68, 68, 0.1);
  color: var(--color-danger);
  font-size: 12px;
}

.cell-image {
  position: absolute;
  top: 0;
  left: 0;
  width: auto;
  height: auto;
  max-width: none;
  max-height: none;
  display: block;
  user-select: none;
  -webkit-user-drag: none;
  will-change: transform;
  pointer-events: none;
}
</style>

