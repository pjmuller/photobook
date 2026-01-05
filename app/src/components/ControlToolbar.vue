<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'

const props = defineProps<{
  currentSpread: number
  totalSpreads: number
  isFirstSpread: boolean
  isLastSpread: boolean
}>()

const emit = defineEmits<{
  navigate: [direction: 'prev' | 'next']
  addSpread: []
  deleteSpread: []
  moveSpread: [direction: 'left' | 'right']
}>()

const moveDropdownOpen = ref(false)
const dropdownRef = ref<HTMLElement | null>(null)

const canMoveLeft = computed(() => props.currentSpread > 1)
const canMoveRight = computed(() => props.currentSpread < props.totalSpreads)

function toggleMoveDropdown() {
  moveDropdownOpen.value = !moveDropdownOpen.value
}

function closeMoveDropdown() {
  moveDropdownOpen.value = false
}

function handleMoveLeft() {
  emit('moveSpread', 'left')
  closeMoveDropdown()
}

function handleMoveRight() {
  emit('moveSpread', 'right')
  closeMoveDropdown()
}

function handleClickOutside(event: MouseEvent) {
  if (dropdownRef.value && !dropdownRef.value.contains(event.target as Node)) {
    closeMoveDropdown()
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<template>
  <div class="control-toolbar">
    <!-- Navigation -->
    <div class="btn-group">
      <button
        class="btn btn-icon"
        :disabled="isFirstSpread"
        data-tooltip="Previous spread"
        @click="emit('navigate', 'prev')"
      >
        <i class="bi bi-arrow-left"></i>
      </button>
      <button
        class="btn btn-icon"
        :disabled="isLastSpread"
        data-tooltip="Next spread"
        @click="emit('navigate', 'next')"
      >
        <i class="bi bi-arrow-right"></i>
      </button>
    </div>

    <!-- Page Actions -->
    <div class="btn-group">
      <button
        class="btn btn-icon"
        data-tooltip="Add new spread"
        @click="emit('addSpread')"
      >
        <i class="bi bi-plus"></i>
      </button>
      <button
        class="btn btn-icon btn-danger"
        :disabled="totalSpreads <= 1"
        data-tooltip="Delete current spread"
        @click="emit('deleteSpread')"
      >
        <i class="bi bi-trash"></i>
      </button>
      <div ref="dropdownRef" class="dropdown" :class="{ open: moveDropdownOpen }">
        <button
          class="btn btn-icon"
          :disabled="totalSpreads <= 1"
          data-tooltip="Move spread"
          @click="toggleMoveDropdown"
        >
          <i class="bi bi-arrow-left-right"></i>
        </button>
        <div class="dropdown-menu">
          <div
            class="dropdown-item"
            :class="{ disabled: !canMoveLeft }"
            @click="canMoveLeft && handleMoveLeft()"
          >
            <i class="bi bi-arrow-bar-left"></i>
            Move left
          </div>
          <div
            class="dropdown-item"
            :class="{ disabled: !canMoveRight }"
            @click="canMoveRight && handleMoveRight()"
          >
            <i class="bi bi-arrow-bar-right"></i>
            Move right
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.control-toolbar {
  display: flex;
  gap: 12px;
}

.dropdown-item.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>

