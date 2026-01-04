<script setup lang="ts">
import type { Row, ImageInfo, FocalPoint } from '../types'
import PhotoCell from './PhotoCell.vue'
import GutterComponent from './GutterComponent.vue'

const props = defineProps<{
  row: Row
  pageId: string
  rowIndex: number
  images: Map<string, ImageInfo>
  cropModePageId: string | null
  cropModeRowIndex: number | null
  cropModeCellIndex: number | null
}>()

const emit = defineEmits<{
  resizeCellStart: [cellIndex: number]
  resizeCell: [cellIndex: number, delta: number]
  resizeCellEnd: [cellIndex: number, delta: number]
  enterCropMode: [cellIndex: number]
  exitCropMode: []
  updateCrop: [cellIndex: number, focalPoint: FocalPoint, zoom: number]
  imageDrop: [cellIndex: number, imagePath: string, naturalWidth: number, naturalHeight: number]
  imageRemove: [cellIndex: number]
  imageSwap: [cellIndex: number, fromPageId: string, fromRowIndex: number, fromCellIndex: number]
}>()

// Get image info for a cell
function getImageInfo(path?: string): ImageInfo | undefined {
  if (!path) return undefined
  return props.images.get(path)
}

// Check if a cell is in crop mode
function isCellInCropMode(cellIndex: number): boolean {
  return (
    props.cropModePageId === props.pageId &&
    props.cropModeRowIndex === props.rowIndex &&
    props.cropModeCellIndex === cellIndex
  )
}

// Handle cell resize
function handleResizeStart(cellIndex: number) {
  emit('resizeCellStart', cellIndex)
}

function handleResize(cellIndex: number, delta: number) {
  emit('resizeCell', cellIndex, delta)
}

function handleResizeEnd(cellIndex: number, delta: number) {
  emit('resizeCellEnd', cellIndex, delta)
}

// Handle crop mode
function handleEnterCropMode(cellIndex: number) {
  emit('enterCropMode', cellIndex)
}

function handleExitCropMode() {
  emit('exitCropMode')
}

function handleUpdateCrop(cellIndex: number, focalPoint: FocalPoint, zoom: number) {
  emit('updateCrop', cellIndex, focalPoint, zoom)
}

// Handle image operations
function handleImageDrop(cellIndex: number, imagePath: string, naturalWidth: number, naturalHeight: number) {
  emit('imageDrop', cellIndex, imagePath, naturalWidth, naturalHeight)
}

function handleImageRemove(cellIndex: number) {
  emit('imageRemove', cellIndex)
}

function handleImageSwap(cellIndex: number, fromPageId: string, fromRowIndex: number, fromCellIndex: number) {
  emit('imageSwap', cellIndex, fromPageId, fromRowIndex, fromCellIndex)
}
</script>

<template>
  <div
    class="page-row"
    :style="{ height: `${row.height}px` }"
  >
    <template v-for="(cell, cellIndex) in row.cells" :key="cellIndex">
      <!-- Gutter between cells (not before first) -->
      <GutterComponent
        v-if="cellIndex > 0"
        orientation="horizontal"
        :index="cellIndex - 1"
        @resize-start="handleResizeStart(cellIndex - 1)"
        @resize="(delta) => handleResize(cellIndex - 1, delta)"
        @resize-end="(delta) => handleResizeEnd(cellIndex - 1, delta)"
      />
      
      <PhotoCell
        :cell="cell"
        :row-height="row.height"
        :page-id="pageId"
        :row-index="rowIndex"
        :cell-index="cellIndex"
        :image-info="getImageInfo(cell.path)"
        :is-crop-mode="isCellInCropMode(cellIndex)"
        @enter-crop-mode="handleEnterCropMode(cellIndex)"
        @exit-crop-mode="handleExitCropMode"
        @update-crop="(fp, z) => handleUpdateCrop(cellIndex, fp, z)"
        @image-drop="(path, w, h) => handleImageDrop(cellIndex, path, w, h)"
        @image-remove="handleImageRemove(cellIndex)"
        @image-swap="(pId, rI, cI) => handleImageSwap(cellIndex, pId, rI, cI)"
      />
    </template>
  </div>
</template>

<style scoped>
.page-row {
  display: flex;
  width: 100%;
  flex-shrink: 0;
}
</style>

