<template>
  <div class="space-y-6 pt-4">
    <UserInfo :phone="phone" />
    <div class="space-y-4">
      <PlatformConnect platform="telegram" :connected="false" />
      <PlatformConnect platform="bale" :connected="false" />
    </div>
    <BaseButton variant="danger" @click="handleLogout" class="mt-6">خروج</BaseButton>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../composables/useAuth'
import UserInfo from '../components/profile/UserInfo.vue'
import PlatformConnect from '../components/profile/PlatformConnect.vue'
import BaseButton from '../components/ui/BaseButton.vue'

const router = useRouter()
const { logout } = useAuth()

const phone = ref(localStorage.getItem('user_phone') || '۰۹xxxxxxxxx')

const handleLogout = () => {
  logout()
  router.push({ name: 'login' })
}
</script>