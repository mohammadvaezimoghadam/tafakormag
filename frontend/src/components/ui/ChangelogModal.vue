<template>
  <Teleport to="body">
    <div class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <!-- Backdrop with blur -->
      <div 
        class="absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity duration-300" 
        @click="$emit('close')" 
      />

      <!-- Floating centered panel -->
      <div 
        dir="rtl"
        class="relative w-full max-w-md bg-white rounded-[2.5rem] shadow-2xl p-6 sm:p-8 animate-scale-up z-10 text-right flex flex-col max-h-[85vh] border border-gray-100"
      >
        <!-- Decorative Header Section -->
        <div class="text-center mb-6">
          <div class="relative w-14 h-14 bg-gradient-to-tr from-indigo-500 to-purple-600 text-white rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg shadow-indigo-200 animate-bounce-slow">
            <svg class="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            <span class="absolute -top-1.5 -right-1.5 flex h-3.5 w-3.5">
              <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-pink-400 opacity-75"></span>
              <span class="relative inline-flex rounded-full h-3.5 w-3.5 bg-pink-500"></span>
            </span>
          </div>

          <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-black bg-indigo-50 text-indigo-600 border border-indigo-100/60 mb-2">
            نسخه جدید منتشر شد 🎉
          </span>
          
          <h3 class="text-xl font-extrabold text-gray-800 tracking-tight mt-1">
            {{ title }}
          </h3>
          <p class="text-sm text-gray-400 mt-2 font-medium">
            {{ description }}
          </p>
        </div>

        <!-- Updates List (Scrollable if too long) -->
        <div class="flex-1 overflow-y-auto pr-1 pl-2 mb-6 space-y-3 custom-scrollbar">
          <div 
            v-for="(update, index) in updates" 
            :key="index"
            class="group border rounded-2xl p-4 transition-all duration-300 cursor-pointer select-none"
            :class="[
              expandedCards[index] 
                ? 'border-indigo-150 bg-indigo-50/20 shadow-md shadow-indigo-100/10' 
                : 'border-gray-100 bg-gray-50/50 hover:bg-gray-50 hover:border-gray-200'
            ]"
            @click="toggleCard(index)"
          >
            <!-- Card Header -->
            <div class="flex items-center justify-between gap-3">
              <div class="flex items-center gap-3">
                <span 
                  class="w-2 h-2 rounded-full transition-all duration-300"
                  :class="expandedCards[index] ? 'bg-indigo-600 scale-125' : 'bg-gray-300 group-hover:bg-gray-400'"
                />
                <h4 
                  class="text-sm font-extrabold transition-colors duration-200"
                  :class="expandedCards[index] ? 'text-indigo-900' : 'text-gray-700'"
                >
                  {{ update.title }}
                </h4>
              </div>
              
              <!-- Chevron Icon -->
              <svg 
                class="w-4 h-4 text-gray-400 transition-transform duration-300 ease-in-out shrink-0"
                :class="{ 'rotate-180 text-indigo-600': expandedCards[index] }"
                fill="none" 
                viewBox="0 0 24 24" 
                stroke="currentColor"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M19 9l-7 7-7-7" />
              </svg>
            </div>

            <!-- Card Body / Details (Animated Collapse) -->
            <div 
              class="transition-all duration-300 ease-in-out overflow-hidden"
              :style="{ maxHeight: expandedCards[index] ? '200px' : '0px', opacity: expandedCards[index] ? '1' : '0' }"
            >
              <div class="pt-3 pr-5 text-xs text-gray-500 leading-relaxed font-medium">
                {{ update.details }}
              </div>
            </div>
          </div>
        </div>

        <!-- Confirm Action Button -->
        <div class="mt-auto">
          <BaseButton
            variant="primary"
            class="shadow-lg shadow-indigo-100 text-base py-3"
            @click="$emit('close')"
          >
            متوجه شدم
          </BaseButton>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref } from 'vue'
import BaseButton from './BaseButton.vue'

defineProps({
  title: {
    type: String,
    required: true
  },
  description: {
    type: String,
    required: true
  },
  updates: {
    type: Array,
    required: true
  }
})

defineEmits(['close'])

// Keep track of which cards are expanded
const expandedCards = ref({
  0: true // Expand the first card by default for better UX
})

const toggleCard = (index) => {
  expandedCards.value[index] = !expandedCards.value[index]
}
</script>

<style scoped>
.animate-scale-up {
  animation: scaleUp 0.35s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
}

@keyframes scaleUp {
  from {
    transform: scale(0.92);
    opacity: 0;
  }
  to {
    transform: scale(1);
    opacity: 1;
  }
}

.animate-bounce-slow {
  animation: bounceSlow 3s cubic-bezier(0.4, 0, 0.2, 1) infinite;
}

@keyframes bounceSlow {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-6px);
  }
}

/* Elegant scrollbar styling */
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #e2e8f0;
  border-radius: 9999px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #cbd5e1;
}
</style>
