<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="open" class="fixed inset-0 z-50 bg-black/40" @click="$emit('close')" />
    </Transition>
    <Transition name="slide">
      <aside v-if="open" class="fixed top-0 right-0 bottom-0 z-50 w-72 bg-white shadow-2xl flex flex-col">
        <div class="flex items-center justify-between px-4 h-14 border-b">
          <h2 class="text-lg font-bold text-indigo-700">منو</h2>
          <button @click="$emit('close')" class="p-2 text-gray-500 hover:text-gray-700">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div class="flex-1 p-6 text-center text-gray-400 flex items-center justify-center">
          <p class="text-lg">به زودی...</p>
        </div>
      </aside>
    </Transition>
  </Teleport>
</template>

<script setup>
defineProps({
  open: { type: Boolean, default: false }
})
defineEmits(['close'])
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-enter-active,
.slide-leave-active {
  transition: transform 0.3s ease;
}
.slide-enter-from,
.slide-leave-to {
  transform: translateX(100%);   /* از راست وارد شود */
}
</style>