<template>
  <header class="fixed top-0 left-0 right-0 z-40 bg-white/80 backdrop-blur-md border-b border-gray-200 max-w-md mx-auto">
    <div class="relative flex items-center justify-center px-4 h-14">
      <!-- دکمه همبرگر (سمت راست) -->
      <button @click="$emit('toggle-sidebar')" class="absolute right-4 p-2 rounded-lg text-gray-600 hover:bg-gray-100">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>

      <!-- عنوان (وسط) -->
      <h1 class="text-lg font-bold text-indigo-700">تفکر</h1>
    </div>
  </header>
</template>

<script setup>
defineEmits(['toggle-sidebar'])
</script>