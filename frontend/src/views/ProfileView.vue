<template>
  <div class="space-y-6 pt-4 max-w-md mx-auto">
    <!-- نمایش مشخصات کاربر شامل شماره تلفن پویا -->
    <UserInfo :phone="profile.phone || phoneFallback" />

    <!-- بخش اتصالات ربات اختصاصی -->
    <div class="space-y-4">
      <h2 class="text-sm font-bold text-gray-400 px-1">تنظیمات ربات‌های انتشار اختصاصی شما</h2>
      
      <PlatformConnect 
        platform="telegram" 
        :connected="profile.is_telegram_bot_connected" 
        :bot-username="profile.telegram_bot_username"
        @updated="loadProfile"
      />
      
      <PlatformConnect 
        platform="bale" 
        :connected="profile.is_bale_bot_connected" 
        :bot-username="profile.bale_bot_username"
        @updated="loadProfile"
      />
    </div>

    <!-- دکمه خروج -->
    <BaseButton variant="danger" @click="handleLogout" class="mt-6 w-full">خروج از حساب</BaseButton>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../composables/useAuth'
import UserInfo from '../components/profile/UserInfo.vue'
import PlatformConnect from '../components/profile/PlatformConnect.vue'
import BaseButton from '../components/ui/BaseButton.vue'
import { fetchProfile } from '../api'

const router = useRouter()
const { logout } = useAuth()

const phoneFallback = ref(localStorage.getItem('user_phone') || '۰۹xxxxxxxxx')
const profile = ref({
  phone: '',
  is_telegram_bot_connected: false,
  telegram_bot_username: '',
  is_bale_bot_connected: false,
  bale_bot_username: '',
  is_telegram_otp_connected: false,
  is_bale_otp_connected: false
})

const loadProfile = async () => {
  try {
    const res = await fetchProfile()
    profile.value = res.data
    if (res.data?.phone) {
      localStorage.setItem('user_phone', res.data.phone)
    }
  } catch (err) {
    // خطا توسط اینترسپتور مدیریت می‌شود
  }
}

const handleLogout = () => {
  logout()
  router.push({ name: 'login' })
}

onMounted(() => {
  loadProfile()
})
</script>