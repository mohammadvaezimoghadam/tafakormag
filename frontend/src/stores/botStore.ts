import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { useUserStore } from './userStore'
import * as api from '../api'

export const useBotStore = defineStore('bot', () => {
  const userStore = useUserStore()

  const telegramConnecting = ref(false)
  const baleConnecting = ref(false)

  const telegramBotStatus = computed<'disconnected' | 'connecting' | 'connected' | 'conflict'>(() => {
    if (telegramConnecting.value) return 'connecting'
    if (!userStore.userProfile) return 'disconnected'
    if (userStore.userProfile.is_telegram_bot_connected) return 'connected'
    if (
      userStore.userProfile.telegram_bot_disconnect_reason === 'claimed_by_another_user' ||
      userStore.userProfile.telegram_bot_disconnect_reason === 'conflict'
    )
      return 'conflict'
    return 'disconnected'
  })

  // Dummy token to trigger masked display in the UI if connected
  const telegramBotToken = ref('')

  const baleBotStatus = computed<'disconnected' | 'connecting' | 'connected' | 'conflict'>(() => {
    if (baleConnecting.value) return 'connecting'
    if (!userStore.userProfile) return 'disconnected'
    if (userStore.userProfile.is_bale_bot_connected) return 'connected'
    if (
      userStore.userProfile.bale_bot_disconnect_reason === 'claimed_by_another_user' ||
      userStore.userProfile.bale_bot_disconnect_reason === 'conflict'
    )
      return 'conflict'
    return 'disconnected'
  })

  const baleBotToken = ref('')

  const connectTelegram = async (token: string, onConnect?: () => void) => {
    telegramConnecting.value = true
    try {
      const res = await api.updateCustomBot('telegram', token)
      if (res.data?.success) {
        await userStore.loadProfile()
        telegramBotToken.value = token
        if (onConnect) onConnect()
      }
    } catch (err: any) {
      console.error('Error connecting Telegram bot:', err)
      const errorData = err.response?.data
      if (errorData?.code === 'claimed_by_another_user') {
        const otherPhone = errorData.other_phone || 'دیگری'
        const msg = `این ربات در حال حاضر به حساب کاربری با شماره تلفن ${otherPhone} متصل است. آیا مطمئن هستید که می‌خواهید مالکیت آن را به این حساب انتقال دهید؟`
        if (window.confirm(msg)) {
          const resForce = await api.updateCustomBot('telegram', token, true)
          if (resForce.data?.success) {
            await userStore.loadProfile()
            telegramBotToken.value = token
            if (onConnect) onConnect()
          }
        }
      }
      throw err
    } finally {
      telegramConnecting.value = false
    }
  }

  const disconnectTelegram = async (onDisconnect?: () => void) => {
    try {
      const res = await api.updateCustomBot('telegram', '')
      if (res.data?.success) {
        await userStore.loadProfile()
        telegramBotToken.value = ''
        if (onDisconnect) onDisconnect()
      }
    } catch (err) {
      console.error('Error disconnecting Telegram bot:', err)
      throw err
    }
  }

  const connectBale = async (token: string, onConnect?: () => void) => {
    baleConnecting.value = true
    try {
      const res = await api.updateCustomBot('bale', token)
      if (res.data?.success) {
        await userStore.loadProfile()
        baleBotToken.value = token
        if (onConnect) onConnect()
      }
    } catch (err: any) {
      console.error('Error connecting Bale bot:', err)
      const errorData = err.response?.data
      if (errorData?.code === 'claimed_by_another_user') {
        const otherPhone = errorData.other_phone || 'دیگری'
        const msg = `این ربات در حال حاضر به حساب کاربری با شماره تلفن ${otherPhone} متصل است. آیا مطمئن هستید که می‌خواهید مالکیت آن را به این حساب انتقال دهید؟`
        if (window.confirm(msg)) {
          const resForce = await api.updateCustomBot('bale', token, true)
          if (resForce.data?.success) {
            await userStore.loadProfile()
            baleBotToken.value = token
            if (onConnect) onConnect()
          }
        }
      }
      throw err
    } finally {
      baleConnecting.value = false
    }
  }

  const disconnectBale = async (onDisconnect?: () => void) => {
    try {
      const res = await api.updateCustomBot('bale', '')
      if (res.data?.success) {
        await userStore.loadProfile()
        baleBotToken.value = ''
        if (onDisconnect) onDisconnect()
      }
    } catch (err) {
      console.error('Error disconnecting Bale bot:', err)
      throw err
    }
  }

  return {
    telegramBotStatus,
    telegramBotToken,
    baleBotStatus,
    baleBotToken,
    connectTelegram,
    disconnectTelegram,
    connectBale,
    disconnectBale
  }
})
