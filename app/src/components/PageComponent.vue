<script setup lang="ts">
import { ref } from 'vue'
import type { Page, ImageInfo, FocalPoint } from '../types'
import type { LayoutType } from '../config'
import { CONFIG, LAYOUTS } from '../config'
import RowComponent from './RowComponent.vue'
import GutterComponent from './GutterComponent.vue'

defineProps<{
  page: Page
  isLeftPage: boolean
  images: Map<string, ImageInfo>
  cropModePageId: string | null
  cropModeRowIndex: number | null
  cropModeCellIndex: number | null
}>()

const emit = defineEmits<{
  changeLayout: [newLayout: LayoutType]
  resizeRowStart: [rowIndex: number]
  resizeRow: [rowIndex: number, delta: number]
  resizeRowEnd: [rowIndex: number, delta: number]
  resizeCellStart: [rowIndex: number, cellIndex: number]
  resizeCell: [rowIndex: number, cellIndex: number, delta: number]
  resizeCellEnd: [rowIndex: number, cellIndex: number, delta: number]
  enterCropMode: [rowIndex: number, cellIndex: number]
  exitCropMode: []
  updateCrop: [rowIndex: number, cellIndex: number, focalPoint: FocalPoint, zoom: number]
  imageDrop: [rowIndex: number, cellIndex: number, imagePath: string, naturalWidth: number, naturalHeight: number]
  imageRemove: [rowIndex: number, cellIndex: number]
  imageSwap: [rowIndex: number, cellIndex: number, fromPageId: string, fromRowIndex: number, fromCellIndex: number]
}>()

const layoutMenuOpen = ref(false)
const availableLayouts: LayoutType[] = ['1', '2-2', '2-3', '3-2']

function toggleLayoutMenu() {
  layoutMenuOpen.value = !layoutMenuOpen.value
}

function selectLayout(layout: LayoutType) {
  emit('changeLayout', layout)
  layoutMenuOpen.value = false
}

// Close menu when clicking outside
function handleClickOutside(e: Event) {
  const target = e.target as HTMLElement
  if (!target.closest('.layout-switcher')) {
    layoutMenuOpen.value = false
  }
}

// Row events forwarding
function handleResizeRowStart(rowIndex: number) {
  emit('resizeRowStart', rowIndex)
}

function handleResizeRow(rowIndex: number, delta: number) {
  emit('resizeRow', rowIndex, delta)
}

function handleResizeRowEnd(rowIndex: number, delta: number) {
  emit('resizeRowEnd', rowIndex, delta)
}

// Cell events forwarding
function handleResizeCellStart(rowIndex: number, cellIndex: number) {
  emit('resizeCellStart', rowIndex, cellIndex)
}

function handleResizeCell(rowIndex: number, cellIndex: number, delta: number) {
  emit('resizeCell', rowIndex, cellIndex, delta)
}

function handleResizeCellEnd(rowIndex: number, cellIndex: number, delta: number) {
  emit('resizeCellEnd', rowIndex, cellIndex, delta)
}

// Crop events forwarding
function handleEnterCropMode(rowIndex: number, cellIndex: number) {
  emit('enterCropMode', rowIndex, cellIndex)
}

function handleExitCropMode() {
  emit('exitCropMode')
}

function handleUpdateCrop(rowIndex: number, cellIndex: number, focalPoint: FocalPoint, zoom: number) {
  emit('updateCrop', rowIndex, cellIndex, focalPoint, zoom)
}

// Image events forwarding
function handleImageDrop(rowIndex: number, cellIndex: number, imagePath: string, naturalWidth: number, naturalHeight: number) {
  emit('imageDrop', rowIndex, cellIndex, imagePath, naturalWidth, naturalHeight)
}

function handleImageRemove(rowIndex: number, cellIndex: number) {
  emit('imageRemove', rowIndex, cellIndex)
}

function handleImageSwap(rowIndex: number, cellIndex: number, fromPageId: string, fromRowIndex: number, fromCellIndex: number) {
  emit('imageSwap', rowIndex, cellIndex, fromPageId, fromRowIndex, fromCellIndex)
}

// Get layout preview cells
function getLayoutCells(layout: LayoutType): number[][] {
  return LAYOUTS[layout].map(count => Array(count).fill(1))
}
</script>

<template>
  <div
    class="page"
    :style="{
      width: `${CONFIG.PAGE_WIDTH}px`,
      height: `${CONFIG.PAGE_HEIGHT}px`,
    }"
    @click="handleClickOutside"
  >
    <!-- Layout switcher -->
    <div
      class="layout-switcher"
      :class="isLeftPage ? 'left' : 'right'"
    >
      <button
        class="btn btn-icon"
        data-tooltip="Change layout"
        @click.stop="toggleLayoutMenu"
      >
        <i class="bi bi-grid-fill"></i>
      </button>
      
      <div v-if="layoutMenuOpen" class="layout-menu" @click.stop>
        <div
          v-for="layout in availableLayouts"
          :key="layout"
          class="layout-option"
          :class="{ active: page.layout === layout }"
          @click="selectLayout(layout)"
        >
          <div
            v-for="(row, rowIdx) in getLayoutCells(layout)"
            :key="rowIdx"
            class="layout-option-row"
          >
            <div
              v-for="(_, cellIdx) in row"
              :key="cellIdx"
              class="layout-option-cell"
            ></div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Rows -->
    <template v-for="(row, rowIndex) in page.rows" :key="rowIndex">
      <!-- Gutter between rows (not before first) -->
      <GutterComponent
        v-if="rowIndex > 0"
        orientation="vertical"
        :index="rowIndex - 1"
        @resize-start="handleResizeRowStart(rowIndex - 1)"
        @resize="(delta) => handleResizeRow(rowIndex - 1, delta)"
        @resize-end="(delta) => handleResizeRowEnd(rowIndex - 1, delta)"
      />
      
      <RowComponent
        :row="row"
        :page-id="page.id"
        :row-index="rowIndex"
        :images="images"
        :crop-mode-page-id="cropModePageId"
        :crop-mode-row-index="cropModeRowIndex"
        :crop-mode-cell-index="cropModeCellIndex"
        @resize-cell-start="(cI) => handleResizeCellStart(rowIndex, cI)"
        @resize-cell="(cI, d) => handleResizeCell(rowIndex, cI, d)"
        @resize-cell-end="(cI, d) => handleResizeCellEnd(rowIndex, cI, d)"
        @enter-crop-mode="(cI) => handleEnterCropMode(rowIndex, cI)"
        @exit-crop-mode="handleExitCropMode"
        @update-crop="(cI, fp, z) => handleUpdateCrop(rowIndex, cI, fp, z)"
        @image-drop="(cI, p, w, h) => handleImageDrop(rowIndex, cI, p, w, h)"
        @image-remove="(cI) => handleImageRemove(rowIndex, cI)"
        @image-swap="(cI, pId, rI, srcCI) => handleImageSwap(rowIndex, cI, pId, rI, srcCI)"
      />
    </template>
  </div>
</template>

<style scoped>
.page {
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06), 0 0 1px rgba(0, 0, 0, 0.08);
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.layout-switcher {
  position: absolute;
  top: 8px;
  z-index: 20;
  opacity: 0;
  transition: opacity 0.15s;
}

.page:hover .layout-switcher {
  opacity: 1;
}

.layout-switcher.left {
  left: 8px;
}

.layout-switcher.right {
  right: 8px;
}

.layout-menu {
  position: absolute;
  top: 100%;
  margin-top: 4px;
  background: white;
  border: 1px solid #e5e5e5;
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  padding: 8px;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
  z-index: 30;
}

.layout-switcher.left .layout-menu {
  left: 0;
}

.layout-switcher.right .layout-menu {
  right: 0;
}

.layout-option {
  width: 60px;
  height: 50px;
  background: #fafafa;
  border: 2px solid #e5e5e5;
  border-radius: 4px;
  cursor: pointer;
  padding: 4px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  transition: all 0.1s;
}

.layout-option:hover {
  border-color: var(--color-accent);
}

.layout-option.active {
  border-color: var(--color-accent);
  background: rgba(59, 130, 246, 0.1);
}

.layout-option-row {
  flex: 1;
  display: flex;
  gap: 2px;
}

.layout-option-cell {
  flex: 1;
  background: #dee2e6;
  border-radius: 2px;
}
</style>

