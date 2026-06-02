<template>
  <div class="font-sans antialiased text-gray-900 bg-gray-50 min-h-screen relative max-w-md w-full mx-auto shadow-xl">
    <template v-if="showLayout">
      <AppHeader @toggle-sidebar="sidebarOpen = !sidebarOpen" />
      <SidebarDrawer :open="sidebarOpen" @close="sidebarOpen = false" />
    </template>
    
    <!-- محتوای صفحات -->
    <main :class="[
      showLayout ? 'pt-14' : 'px-4',
      showBottomNav ? 'pb-20' : 'pb-0'
    ]">
      <router-view />
    </main>
    
    <!-- نویگیشن بار پایین -->
    <BottomNav v-if="showBottomNav" />
    
    <BaseToast />

    <!-- مودال ورود سریع سراسری -->
    <QuickLoginModal
      v-if="showGlobalLoginModal"
      @close="showGlobalLoginModal = false"
    />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import AppHeader from './components/layout/AppHeader.vue'
import SidebarDrawer from './components/layout/SidebarDrawer.vue'
import BaseToast from './components/ui/BaseToast.vue'
import BottomNav from './components/layout/BottomNav.vue'
import QuickLoginModal from './components/auth/QuickLoginModal.vue'
import { useAuth } from './composables/useAuth'

const route = useRoute()
const showLayout = computed(() => route.name !== 'login')
const showBottomNav = computed(() => showLayout.value && !route.meta.hideBottomNav)
const sidebarOpen = ref(false)

const { showGlobalLoginModal } = useAuth()
</script>
