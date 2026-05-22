<template>
  <div class="fixed top-16 left-1/2 -translate-x-1/2 z-[100] w-11/12 max-w-md space-y-2">
    <TransitionGroup name="toast" tag="div">
      <div
        v-for="msg in toastState.messages"
        :key="msg.id"
        class="flex items-center gap-3 px-4 py-3 rounded-xl shadow-lg text-white text-sm font-medium"
        :class="typeClasses(msg.type)"
      >
        <span class="flex-1">{{ msg.message }}</span>
        <button @click="toastState.remove(msg.id)" class="text-white/80 hover:text-white text-lg leading-none">&times;</button>
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup>
import { toastState } from '../../store/toastState'

const typeClasses = (type) => {
  switch (type) {
    case 'success': return 'bg-emerald-500'
    case 'error': return 'bg-rose-500'
    case 'warning': return 'bg-amber-500'
    default: return 'bg-gray-800'
  }
}
</script>

<style scoped>
.toast-enter-active {
  transition: all 0.3s ease-out;
}
.toast-leave-active {
  transition: all 0.2s ease-in;
}
.toast-enter-from {
  opacity: 0;
  transform: translateY(-30px);
}
.toast-leave-to {
  opacity: 0;
  transform: translateY(-30px);
}
</style>