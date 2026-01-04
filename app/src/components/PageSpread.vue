<script setup lang="ts">
import type { Page, ImageInfo, FocalPoint } from '../types'
import type { LayoutType } from '../config'
import PageComponent from './PageComponent.vue'

const props = defineProps<{
  leftPage: Page
  rightPage: Page
  pageLabel: string
  images: Map<string, ImageInfo>
  cropModePageId: string | null
  cropModeRowIndex: number | null
  cropModeCellIndex: number | null
}>()

const emit = defineEmits<{
  changeLayout: [pageId: string, newLayout: LayoutType]
  resizeRowStart: [pageId: string, rowIndex: number]
  resizeRow: [pageId: string, rowIndex: number, delta: number]
  resizeRowEnd: [pageId: string, rowIndex: number, delta: number]
  resizeCellStart: [pageId: string, rowIndex: number, cellIndex: number]
  resizeCell: [pageId: string, rowIndex: number, cellIndex: number, delta: number]
  resizeCellEnd: [pageId: string, rowIndex: number, cellIndex: number, delta: number]
  enterCropMode: [pageId: string, rowIndex: number, cellIndex: number]
  exitCropMode: []
  updateCrop: [pageId: string, rowIndex: number, cellIndex: number, focalPoint: FocalPoint, zoom: number]
  imageDrop: [pageId: string, rowIndex: number, cellIndex: number, imagePath: string, naturalWidth: number, naturalHeight: number]
  imageRemove: [pageId: string, rowIndex: number, cellIndex: number]
  imageSwap: [pageId: string, rowIndex: number, cellIndex: number, fromPageId: string, fromRowIndex: number, fromCellIndex: number]
}>()

// Left page events
function handleLeftChangeLayout(layout: LayoutType) {
  emit('changeLayout', props.leftPage.id, layout)
}

function handleLeftResizeRowStart(rowIndex: number) {
  emit('resizeRowStart', props.leftPage.id, rowIndex)
}

function handleLeftResizeRow(rowIndex: number, delta: number) {
  emit('resizeRow', props.leftPage.id, rowIndex, delta)
}

function handleLeftResizeRowEnd(rowIndex: number, delta: number) {
  emit('resizeRowEnd', props.leftPage.id, rowIndex, delta)
}

function handleLeftResizeCellStart(rowIndex: number, cellIndex: number) {
  emit('resizeCellStart', props.leftPage.id, rowIndex, cellIndex)
}

function handleLeftResizeCell(rowIndex: number, cellIndex: number, delta: number) {
  emit('resizeCell', props.leftPage.id, rowIndex, cellIndex, delta)
}

function handleLeftResizeCellEnd(rowIndex: number, cellIndex: number, delta: number) {
  emit('resizeCellEnd', props.leftPage.id, rowIndex, cellIndex, delta)
}

function handleLeftEnterCropMode(rowIndex: number, cellIndex: number) {
  emit('enterCropMode', props.leftPage.id, rowIndex, cellIndex)
}

function handleLeftUpdateCrop(rowIndex: number, cellIndex: number, focalPoint: FocalPoint, zoom: number) {
  emit('updateCrop', props.leftPage.id, rowIndex, cellIndex, focalPoint, zoom)
}

function handleLeftImageDrop(rowIndex: number, cellIndex: number, imagePath: string, naturalWidth: number, naturalHeight: number) {
  emit('imageDrop', props.leftPage.id, rowIndex, cellIndex, imagePath, naturalWidth, naturalHeight)
}

function handleLeftImageRemove(rowIndex: number, cellIndex: number) {
  emit('imageRemove', props.leftPage.id, rowIndex, cellIndex)
}

function handleLeftImageSwap(rowIndex: number, cellIndex: number, fromPageId: string, fromRowIndex: number, fromCellIndex: number) {
  emit('imageSwap', props.leftPage.id, rowIndex, cellIndex, fromPageId, fromRowIndex, fromCellIndex)
}

// Right page events
function handleRightChangeLayout(layout: LayoutType) {
  emit('changeLayout', props.rightPage.id, layout)
}

function handleRightResizeRowStart(rowIndex: number) {
  emit('resizeRowStart', props.rightPage.id, rowIndex)
}

function handleRightResizeRow(rowIndex: number, delta: number) {
  emit('resizeRow', props.rightPage.id, rowIndex, delta)
}

function handleRightResizeRowEnd(rowIndex: number, delta: number) {
  emit('resizeRowEnd', props.rightPage.id, rowIndex, delta)
}

function handleRightResizeCellStart(rowIndex: number, cellIndex: number) {
  emit('resizeCellStart', props.rightPage.id, rowIndex, cellIndex)
}

function handleRightResizeCell(rowIndex: number, cellIndex: number, delta: number) {
  emit('resizeCell', props.rightPage.id, rowIndex, cellIndex, delta)
}

function handleRightResizeCellEnd(rowIndex: number, cellIndex: number, delta: number) {
  emit('resizeCellEnd', props.rightPage.id, rowIndex, cellIndex, delta)
}

function handleRightEnterCropMode(rowIndex: number, cellIndex: number) {
  emit('enterCropMode', props.rightPage.id, rowIndex, cellIndex)
}

function handleRightUpdateCrop(rowIndex: number, cellIndex: number, focalPoint: FocalPoint, zoom: number) {
  emit('updateCrop', props.rightPage.id, rowIndex, cellIndex, focalPoint, zoom)
}

function handleRightImageDrop(rowIndex: number, cellIndex: number, imagePath: string, naturalWidth: number, naturalHeight: number) {
  emit('imageDrop', props.rightPage.id, rowIndex, cellIndex, imagePath, naturalWidth, naturalHeight)
}

function handleRightImageRemove(rowIndex: number, cellIndex: number) {
  emit('imageRemove', props.rightPage.id, rowIndex, cellIndex)
}

function handleRightImageSwap(rowIndex: number, cellIndex: number, fromPageId: string, fromRowIndex: number, fromCellIndex: number) {
  emit('imageSwap', props.rightPage.id, rowIndex, cellIndex, fromPageId, fromRowIndex, fromCellIndex)
}
</script>

<template>
  <div class="spread-container">
    <div class="spread">
      <PageComponent
        :page="leftPage"
        :is-left-page="true"
        :images="images"
        :crop-mode-page-id="cropModePageId"
        :crop-mode-row-index="cropModeRowIndex"
        :crop-mode-cell-index="cropModeCellIndex"
        @change-layout="handleLeftChangeLayout"
        @resize-row-start="handleLeftResizeRowStart"
        @resize-row="handleLeftResizeRow"
        @resize-row-end="handleLeftResizeRowEnd"
        @resize-cell-start="handleLeftResizeCellStart"
        @resize-cell="handleLeftResizeCell"
        @resize-cell-end="handleLeftResizeCellEnd"
        @enter-crop-mode="handleLeftEnterCropMode"
        @exit-crop-mode="emit('exitCropMode')"
        @update-crop="handleLeftUpdateCrop"
        @image-drop="handleLeftImageDrop"
        @image-remove="handleLeftImageRemove"
        @image-swap="handleLeftImageSwap"
      />
      
      <PageComponent
        :page="rightPage"
        :is-left-page="false"
        :images="images"
        :crop-mode-page-id="cropModePageId"
        :crop-mode-row-index="cropModeRowIndex"
        :crop-mode-cell-index="cropModeCellIndex"
        @change-layout="handleRightChangeLayout"
        @resize-row-start="handleRightResizeRowStart"
        @resize-row="handleRightResizeRow"
        @resize-row-end="handleRightResizeRowEnd"
        @resize-cell-start="handleRightResizeCellStart"
        @resize-cell="handleRightResizeCell"
        @resize-cell-end="handleRightResizeCellEnd"
        @enter-crop-mode="handleRightEnterCropMode"
        @exit-crop-mode="emit('exitCropMode')"
        @update-crop="handleRightUpdateCrop"
        @image-drop="handleRightImageDrop"
        @image-remove="handleRightImageRemove"
        @image-swap="handleRightImageSwap"
      />
    </div>
    
    <div class="page-counter">{{ pageLabel }}</div>
  </div>
</template>

<style scoped>
.spread-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.spread {
  display: flex;
  gap: 4px;
  background: linear-gradient(90deg, #e8e8e8 0%, #f0f0f0 50%, #e8e8e8 100%);
  padding: 12px;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.page-counter {
  font-size: 14px;
  color: #6b6b6b;
  font-weight: 500;
}
</style>

