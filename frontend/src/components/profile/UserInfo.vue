<template>
  <div class="flex items-center gap-4 p-4 bg-white rounded-2xl shadow-sm border">
    <div class="w-12 h-12 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600 font-bold text-lg">
      {{ phone.charAt(0) }}
    </div>
    <div>
      <p class="text-sm text-gray-500">شماره موبایل</p>
      <p class="font-medium text-gray-800">{{ phone }}</p>
    </div>
  </div>
</template>

<script setup>
defineProps({
  phone: { type: String, default: '' }
})
</script>