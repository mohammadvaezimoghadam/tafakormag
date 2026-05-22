<!-- src/components/BottomNav.vue -->
<template>
  <div class="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 flex justify-around items-center py-2 shadow-lg z-40">
    <router-link
      to="/"
      class="flex flex-col items-center p-2 rounded-lg transition-colors"
      active-class="text-indigo-600"
      exact-active-class="text-indigo-600"
    >
      <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
      </svg>
      <span class="text-xs mt-1">خانه</span>
    </router-link>

    <router-link
      to="/profile"
      class="flex flex-col items-center p-2 rounded-lg transition-colors"
      active-class="text-indigo-600"
    >
      <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
      </svg>
      <span class="text-xs mt-1">پروفایل</span>
    </router-link>
  </div>
</template>