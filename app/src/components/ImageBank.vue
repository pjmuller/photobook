<script setup lang="ts">
import type { ImageInfo } from '../types'
import { CONFIG } from '../config'
import { calculateThumbnailWidth } from '../composables/useImageBank'

const props = defineProps<{
  images: ImageInfo[]
  usedPaths: Set<string>
}>()

const emit = defineEmits<{
  navigateToImage: [imagePath: string]
}>()

function isUsed(path: string): boolean {
  return props.usedPaths.has(path)
}

function getThumbnailWidth(image: ImageInfo): number {
  if (!image.naturalWidth || !image.naturalHeight) {
    return CONFIG.THUMBNAIL_HEIGHT // fallback to square
  }
  return calculateThumbnailWidth(image.naturalWidth, image.naturalHeight)
}

function handleDragStart(e: DragEvent, image: ImageInfo) {
  if (isUsed(image.path)) {
    e.preventDefault()
    return
  }
  
  const data = {
    type: 'bank',
    imagePath: image.path,
    naturalWidth: image.naturalWidth,
    naturalHeight: image.naturalHeight,
  }
  
  e.dataTransfer!.setData('application/json', JSON.stringify(data))
  e.dataTransfer!.effectAllowed = 'move'
}

function handleClick(image: ImageInfo) {
  if (isUsed(image.path)) {
    emit('navigateToImage', image.path)
  }
}

function handleDragOver(e: DragEvent) {
  e.preventDefault()
  e.dataTransfer!.dropEffect = 'move'
}

function handleDrop(e: DragEvent) {
  e.preventDefault()
  // Dropping an image back to the bank removes it from its cell
  // This is handled by the parent component
}
</script>

<template>
  <div 
    class="image-bank"
    @dragover="handleDragOver"
    @drop="handleDrop"
  >
    <img
      v-for="image in images"
      :key="image.path"
      :src="image.objectUrl"
      :style="{
        width: `${getThumbnailWidth(image)}px`,
        height: `${CONFIG.THUMBNAIL_HEIGHT}px`,
      }"
      class="bank-thumbnail"
      :class="{ used: isUsed(image.path) }"
      :draggable="!isUsed(image.path)"
      loading="lazy"
      @dragstart="(e) => handleDragStart(e, image)"
      @click="handleClick(image)"
    />
    
    <div v-if="images.length === 0" class="bank-empty">
      <i class="bi bi-images"></i>
      <span>No images in folder</span>
    </div>
  </div>
</template>

<style scoped>
.image-bank {
  height: 170px;
  background: #2b2f36;
  padding: 10px 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  overflow-x: auto;
  overflow-y: hidden;
}

.image-bank::-webkit-scrollbar {
  height: 8px;
}

.image-bank::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
}

.image-bank::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.3);
  border-radius: 4px;
}

.image-bank::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.4);
}

.bank-thumbnail {
  flex-shrink: 0;
  border-radius: 4px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  cursor: grab;
  transition: transform 0.15s, opacity 0.15s, box-shadow 0.15s;
  object-fit: cover;
}

.bank-thumbnail:hover {
  transform: scale(1.05);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
}

.bank-thumbnail.used {
  opacity: 0.4;
  cursor: pointer;
}

.bank-thumbnail.used:hover {
  opacity: 0.6;
  transform: scale(1.02);
}

.bank-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: rgba(255, 255, 255, 0.5);
  font-size: 14px;
}

.bank-empty i {
  font-size: 32px;
}
</style>

