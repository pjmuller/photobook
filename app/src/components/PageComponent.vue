<script setup lang="ts">
import { ref, computed } from 'vue'
import type { Page, ImageInfo, FocalPoint } from '../types'
import type { LayoutType } from '../config'
import { CONFIG, ROW_LAYOUTS, COLUMN_LAYOUTS, isColumnLayout } from '../config'
import RowComponent from './RowComponent.vue'
import ColumnComponent from './ColumnComponent.vue'
import GutterComponent from './GutterComponent.vue'

const props = defineProps<{
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
  resizeColumnStart: [columnIndex: number]
  resizeColumn: [columnIndex: number, delta: number]
  resizeColumnEnd: [columnIndex: number, delta: number]
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
const rowLayouts: LayoutType[] = ['1', '2-2', '2-3', '3-2']
const columnLayouts: LayoutType[] = ['1-1', '1-2', '2-1']

// Check if current page uses column layout
const isColumnPage = computed(() => isColumnLayout(props.page.layout))

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

// Column events forwarding
function handleResizeColumnStart(columnIndex: number) {
  emit('resizeColumnStart', columnIndex)
}

function handleResizeColumn(columnIndex: number, delta: number) {
  emit('resizeColumn', columnIndex, delta)
}

function handleResizeColumnEnd(columnIndex: number, delta: number) {
  emit('resizeColumnEnd', columnIndex, delta)
}

// Cell events forwarding (rowIndex is columnIndex for column layouts)
function handleResizeCellStart(containerIndex: number, cellIndex: number) {
  emit('resizeCellStart', containerIndex, cellIndex)
}

function handleResizeCell(containerIndex: number, cellIndex: number, delta: number) {
  emit('resizeCell', containerIndex, cellIndex, delta)
}

function handleResizeCellEnd(containerIndex: number, cellIndex: number, delta: number) {
  emit('resizeCellEnd', containerIndex, cellIndex, delta)
}

// Crop events forwarding
function handleEnterCropMode(containerIndex: number, cellIndex: number) {
  emit('enterCropMode', containerIndex, cellIndex)
}

function handleExitCropMode() {
  emit('exitCropMode')
}

function handleUpdateCrop(containerIndex: number, cellIndex: number, focalPoint: FocalPoint, zoom: number) {
  emit('updateCrop', containerIndex, cellIndex, focalPoint, zoom)
}

// Image events forwarding
function handleImageDrop(containerIndex: number, cellIndex: number, imagePath: string, naturalWidth: number, naturalHeight: number) {
  emit('imageDrop', containerIndex, cellIndex, imagePath, naturalWidth, naturalHeight)
}

function handleImageRemove(containerIndex: number, cellIndex: number) {
  emit('imageRemove', containerIndex, cellIndex)
}

function handleImageSwap(containerIndex: number, cellIndex: number, fromPageId: string, fromContainerIndex: number, fromCellIndex: number) {
  emit('imageSwap', containerIndex, cellIndex, fromPageId, fromContainerIndex, fromCellIndex)
}

// Get layout preview cells - returns array of arrays representing the layout structure
function getLayoutCells(layout: LayoutType): { cells: number[]; isColumn: boolean }[] {
  const isCol = isColumnLayout(layout)
  const layoutDef = isCol ? COLUMN_LAYOUTS[layout] : ROW_LAYOUTS[layout]
  return layoutDef.map(count => ({ cells: Array(count).fill(1), isColumn: isCol }))
}
</script>

<template>
  <div
    class="page"
    :class="{ 'page-columns': isColumnPage }"
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
        <!-- Row-based layouts -->
        <div class="layout-section-label">Rows</div>
        <div
          v-for="layout in rowLayouts"
          :key="layout"
          class="layout-option"
          :class="{ active: page.layout === layout }"
          @click="selectLayout(layout)"
        >
          <div
            v-for="(item, idx) in getLayoutCells(layout)"
            :key="idx"
            class="layout-option-row"
          >
            <div
              v-for="(_, cellIdx) in item.cells"
              :key="cellIdx"
              class="layout-option-cell"
            ></div>
          </div>
        </div>
        
        <!-- Column-based layouts -->
        <div class="layout-section-label">Columns</div>
        <div
          v-for="layout in columnLayouts"
          :key="layout"
          class="layout-option layout-option-columns"
          :class="{ active: page.layout === layout }"
          @click="selectLayout(layout)"
        >
          <div
            v-for="(item, idx) in getLayoutCells(layout)"
            :key="idx"
            class="layout-option-column"
          >
            <div
              v-for="(_, cellIdx) in item.cells"
              :key="cellIdx"
              class="layout-option-cell"
            ></div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Row-based layout -->
    <template v-if="page.rows">
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
    </template>
    
    <!-- Column-based layout -->
    <template v-if="page.columns">
      <template v-for="(column, columnIndex) in page.columns" :key="columnIndex">
        <!-- Gutter between columns (not before first) -->
        <GutterComponent
          v-if="columnIndex > 0"
          orientation="horizontal"
          :index="columnIndex - 1"
          @resize-start="handleResizeColumnStart(columnIndex - 1)"
          @resize="(delta) => handleResizeColumn(columnIndex - 1, delta)"
          @resize-end="(delta) => handleResizeColumnEnd(columnIndex - 1, delta)"
        />
        
        <ColumnComponent
          :column="column"
          :page-id="page.id"
          :column-index="columnIndex"
          :images="images"
          :crop-mode-page-id="cropModePageId"
          :crop-mode-column-index="cropModeRowIndex"
          :crop-mode-cell-index="cropModeCellIndex"
          @resize-cell-start="(cI) => handleResizeCellStart(columnIndex, cI)"
          @resize-cell="(cI, d) => handleResizeCell(columnIndex, cI, d)"
          @resize-cell-end="(cI, d) => handleResizeCellEnd(columnIndex, cI, d)"
          @enter-crop-mode="(cI) => handleEnterCropMode(columnIndex, cI)"
          @exit-crop-mode="handleExitCropMode"
          @update-crop="(cI, fp, z) => handleUpdateCrop(columnIndex, cI, fp, z)"
          @image-drop="(cI, p, w, h) => handleImageDrop(columnIndex, cI, p, w, h)"
          @image-remove="(cI) => handleImageRemove(columnIndex, cI)"
          @image-swap="(cI, pId, colI, srcCI) => handleImageSwap(columnIndex, cI, pId, colI, srcCI)"
        />
      </template>
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

.page.page-columns {
  flex-direction: row;
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
  min-width: 160px;
}

.layout-switcher.left .layout-menu {
  left: 0;
}

.layout-switcher.right .layout-menu {
  right: 0;
}

.layout-section-label {
  grid-column: 1 / -1;
  font-size: 10px;
  font-weight: 600;
  color: #888;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 4px 0 2px;
}

.layout-section-label:not(:first-child) {
  margin-top: 4px;
  border-top: 1px solid #eee;
  padding-top: 8px;
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

/* Row-based layout preview */
.layout-option-row {
  flex: 1;
  display: flex;
  gap: 2px;
}

/* Column-based layout preview */
.layout-option.layout-option-columns {
  flex-direction: row;
}

.layout-option-column {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.layout-option-cell {
  flex: 1;
  background: #dee2e6;
  border-radius: 2px;
}
</style>

