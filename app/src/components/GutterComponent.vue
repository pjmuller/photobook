<script setup lang="ts">
import { ref } from 'vue'
import { CONFIG } from '../config'

const props = defineProps<{
  orientation: 'horizontal' | 'vertical'
  index: number
}>()

const emit = defineEmits<{
  resizeStart: []
  resize: [delta: number]
  resizeEnd: [delta: number]
}>()

const isDragging = ref(false)
let startPosition = 0
let totalDelta = 0

function handleMouseDown(e: MouseEvent) {
  e.preventDefault()
  isDragging.value = true
  startPosition = props.orientation === 'horizontal' ? e.clientX : e.clientY
  totalDelta = 0
  
  emit('resizeStart')
  
  document.addEventListener('mousemove', handleMouseMove)
  document.addEventListener('mouseup', handleMouseUp)
}

function handleMouseMove(e: MouseEvent) {
  if (!isDragging.value) return
  
  const currentPosition = props.orientation === 'horizontal' ? e.clientX : e.clientY
  const delta = currentPosition - startPosition
  
  totalDelta = delta
  emit('resize', delta)
}

function handleMouseUp() {
  if (!isDragging.value) return
  
  isDragging.value = false
  emit('resizeEnd', totalDelta)
  
  document.removeEventListener('mousemove', handleMouseMove)
  document.removeEventListener('mouseup', handleMouseUp)
}
</script>

<template>
  <div
    class="gutter"
    :class="[
      `gutter-${orientation}`,
      { dragging: isDragging }
    ]"
    :style="{
      width: orientation === 'horizontal' ? `${CONFIG.PAGE_GUTTER}px` : '100%',
      height: orientation === 'vertical' ? `${CONFIG.PAGE_GUTTER}px` : '100%',
    }"
    @mousedown="handleMouseDown"
  ></div>
</template>

<style scoped>
.gutter {
  flex-shrink: 0;
  background: white;
  transition: background 0.1s;
}

.gutter-horizontal {
  cursor: col-resize;
}

.gutter-vertical {
  cursor: row-resize;
}

.gutter:hover,
.gutter.dragging {
  background: rgba(59, 130, 246, 0.2);
}
</style>

