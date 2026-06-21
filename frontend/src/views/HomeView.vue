<script setup lang="ts">
import { useRouter } from 'vue-router'
import LoginCard from '@/components/LoginCard.vue'

const router = useRouter()

const handleStateChange = (state: string) => {
  if (state === 'success') {
    // Automatically redirect to / immediately
    router.push('/')
  }
}
</script>

<template>
  <div class="w-full min-h-[80vh] flex justify-center items-center py-6 px-4" dir="rtl">
    <!-- Centered, width-restricted Login Container (mobile & tablet layout) -->
    <div class="w-full max-w-[420px] transition-all duration-500 animate-in fade-in slide-in-from-bottom-5">
      <LoginCard @state-change="handleStateChange" />
    </div>
  </div>
</template>

