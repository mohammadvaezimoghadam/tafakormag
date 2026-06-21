import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import * as api from '../api'

export interface UserProfile {
  id?: number | string
  phone: string
  first_name?: string
  last_name?: string
  name: string
  avatar?: string
  statusText?: string
  statusVariant?: 'success' | 'warning' | 'info' | 'muted'
  
  // Custom bot states
  is_telegram_bot_connected?: boolean
  telegram_bot_username?: string
  telegram_bot_disconnect_reason?: string | null
  is_bale_bot_connected?: boolean
  bale_bot_username?: string
  bale_bot_disconnect_reason?: string | null
}

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('auth_token') || '')
  const userProfile = ref<UserProfile | null>(null)
  const loading = ref(false)

  const isAuthenticated = computed(() => !!token.value)

  const getImageUrl = (url?: string) => {
    if (!url) return ''
    const mediaIdx = url.indexOf('/media/')
    if (mediaIdx !== -1) {
      url = url.slice(mediaIdx)
    }
    const staticIdx = url.indexOf('/static/')
    if (staticIdx !== -1) {
      url = url.slice(staticIdx)
    }
    if (url.startsWith('http://') || url.startsWith('https://')) {
      return url
    }
    if (url.startsWith('//')) {
      url = url.slice(1)
    }
    const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
    if (apiBase === '/') {
      return url
    }
    const base = apiBase.endsWith('/') ? apiBase.slice(0, -1) : apiBase
    const path = url.startsWith('/') ? url : '/' + url
    return `${base}${path}`
  }

  const mapProfile = (data: any): UserProfile => {
    const firstName = data.first_name || ''
    const lastName = data.last_name || ''
    const fullName = [firstName, lastName].filter(Boolean).join(' ') || data.phone || 'کاربر تفکر'
    
    return {
      id: data.id,
      phone: data.phone,
      first_name: data.first_name,
      last_name: data.last_name,
      name: fullName,
      avatar: getImageUrl(data.profile_image),
      statusText: data.is_telegram_bot_connected || data.is_bale_bot_connected ? 'متصل' : 'فعال',
      statusVariant: 'success',
      is_telegram_bot_connected: data.is_telegram_bot_connected,
      telegram_bot_username: data.telegram_bot_username,
      telegram_bot_disconnect_reason: data.telegram_bot_disconnect_reason,
      is_bale_bot_connected: data.is_bale_bot_connected,
      bale_bot_username: data.bale_bot_username,
      bale_bot_disconnect_reason: data.bale_bot_disconnect_reason
    }
  }

  const loadProfile = async () => {
    if (!token.value) return
    loading.value = true
    try {
      const res = await api.fetchProfile()
      userProfile.value = mapProfile(res.data)
      if (res.data?.phone) {
        localStorage.setItem('user_phone', res.data.phone)
      }
      return userProfile.value
    } catch (err) {
      console.error('Error fetching profile:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  const requestOtp = async (phone: string, forceSms = false) => {
    loading.value = true
    try {
      const res = await api.requestOtp(phone, forceSms)
      return res.data
    } catch (err) {
      console.error('Error requesting OTP:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  const verifyOtp = async (phone: string, code: string) => {
    loading.value = true
    try {
      const res = await api.verifyOtp(phone, code)
      const tokenVal = res.data.token
      token.value = tokenVal
      localStorage.setItem('auth_token', tokenVal)
      await loadProfile()
      return res.data
    } catch (err) {
      console.error('Error verifying OTP:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  const updateProfile = async (formData: FormData) => {
    loading.value = true
    try {
      const res = await api.updateProfile(formData)
      userProfile.value = mapProfile(res.data)
      return userProfile.value
    } catch (err) {
      console.error('Error updating profile:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  const logout = () => {
    token.value = ''
    userProfile.value = null
    localStorage.removeItem('auth_token')
    localStorage.removeItem('user_phone')
  }

  return {
    token,
    userProfile,
    loading,
    isAuthenticated,
    loadProfile,
    requestOtp,
    verifyOtp,
    updateProfile,
    logout
  }
})
