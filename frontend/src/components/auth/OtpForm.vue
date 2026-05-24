<template>
  <form @submit.prevent="handleSubmit" class="space-y-4">
    <!-- جعبه زیبای نمایش وضعیت و مقصد ارسال کد تایید -->
    <div class="p-3.5 bg-indigo-50 border border-indigo-100 rounded-xl text-sm text-indigo-800 text-center mb-4 flex items-center justify-center gap-2 transition-all duration-300">
      <span class="flex h-2 w-2 relative" v-if="currentChannel === 'sms'">
        <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
        <span class="relative inline-flex rounded-full h-2 w-2 bg-indigo-500"></span>
      </span>
      <span v-if="currentChannel === 'sms'">📱 کد تأیید پیامکی به شماره شما ارسال شد.</span>
      <span v-else-if="currentChannel === 'bale'">💬 کد تأیید در <strong>پیام‌رسان بله</strong> برای شما صادر شد.</span>
      <span v-else-if="currentChannel === 'debug'">🛠️ [توسعه] کد در کنسول سرور چاپ شد.</span>
    </div>

    <!-- فیلد وارد کردن کد تایید -->
    <BaseInput
      v-model="otp"
      type="text"
      label="کد تأیید ورود"
      placeholder="۴ رقم"
      :error="error"
      maxlength="4"
      inputmode="numeric"
      class="text-center font-bold font-mono tracking-widest text-lg"
    />

    <!-- شمارش معکوس و دکمه ارسال مجدد -->
    <div class="flex flex-col items-center justify-center text-sm py-2 space-y-4">
      <div v-if="timer > 0" class="text-gray-500 flex items-center gap-1.5 font-medium">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-indigo-500 animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span>ارسال مجدد کد پس از:</span>
        <span class="font-mono text-indigo-600 text-base font-semibold">{{ formattedTime }}</span>
      </div>
      
      <button
        v-else
        type="button"
        @click="handleResend"
        :disabled="resendLoading"
        class="text-indigo-600 hover:text-indigo-800 font-medium transition-colors duration-200 flex items-center gap-1 focus:outline-none focus:underline"
      >
        <span v-if="resendLoading" class="inline-block w-4 h-4 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin"></span>
        <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 1121.21 8H17" />
        </svg>
        <span>ارسال مجدد کد تأیید (پیامک)</span>
      </button>

      <!-- دکمه کم‌اولویت و فرعی هدایت به بله (Bale OTP Fallback Button) -->
      <div class="w-full border-t border-gray-100 pt-4 flex flex-col items-center gap-2">
        <button
          type="button"
          @click="openBaleBot"
          class="px-4 py-2 text-xs font-semibold text-gray-600 bg-gray-50 border border-gray-200 rounded-xl hover:bg-gray-100 hover:text-gray-800 transition-all duration-200 flex items-center gap-2 shadow-sm active:scale-98 focus:outline-none"
        >
          <span>💬 دریافت کد ورود در ربات بله</span>
        </button>
        <p class="text-[10px] text-gray-400 text-center max-w-[250px] leading-relaxed">
          در صورت عدم دریافت پیامک، ربات بله را استارت کرده و دکمه ارسال شماره را بزنید تا کد برای شما فرستاده شود.
        </p>
      </div>
    </div>

    <!-- دکمه ورود اصلی -->
    <BaseButton
      type="submit"
      variant="primary"
      :disabled="!isOtpValid"
      :loading="loading"
    >
      ورود به تفکر
    </BaseButton>

    <!-- اصلاح شماره -->
    <button type="button" @click="$emit('back')" class="w-full text-center text-xs text-gray-400 hover:text-indigo-600 transition-colors duration-200 mt-2">
      اصلاح شماره موبایل
    </button>
  </form>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import BaseInput from '../ui/BaseInput.vue'
import BaseButton from '../ui/BaseButton.vue'
import { verifyOtp, requestOtp } from '../../api'
import { useAuth } from '../../composables/useAuth'
import { useToast } from '../../composables/useToast'

const props = defineProps({
  phone: { type: String, required: true },
  channel: { type: String, default: 'sms' }
})
const emit = defineEmits(['back'])

const { login } = useAuth()
const { showToast } = useToast()
const otp = ref('')
const loading = ref(false)
const resendLoading = ref(false)
const error = ref('')

const currentChannel = ref(props.channel)
const timer = ref(120)
let timerInterval = null

const startTimer = () => {
  timer.value = 120
  if (timerInterval) clearInterval(timerInterval)
  timerInterval = setInterval(() => {
    if (timer.value > 0) {
      timer.value--
    } else {
      clearInterval(timerInterval)
    }
  }, 1000)
}

const formattedTime = computed(() => {
  const minutes = Math.floor(timer.value / 60)
  const seconds = timer.value % 60
  const pad = (n) => n < 10 ? '0' + n : n
  return `${minutes}:${pad(seconds)}`
})

const notifyChannel = (chan) => {
  if (chan === 'sms') {
    showToast('کد تایید ورود با موفقیت پیامک شد.', 'success')
  } else if (chan === 'bale') {
    showToast('کد تایید با موفقیت در ربات بله شما صادر شد.', 'success')
  } else if (chan === 'debug') {
    showToast('حالت شبیه‌سازی: کد ورود در کنسول سرور چاپ شد.', 'info')
  }
}

onMounted(() => {
  startTimer()
  notifyChannel(currentChannel.value)
})

onUnmounted(() => {
  if (timerInterval) clearInterval(timerInterval)
})

const handleResend = async () => {
  if (timer.value > 0 || resendLoading.value) return
  resendLoading.value = true
  error.value = ''
  try {
    const res = await requestOtp(props.phone)
    currentChannel.value = res.data?.channel || 'sms'
    startTimer()
    notifyChannel(currentChannel.value)
  } catch (err) {
    error.value = 'خطا در ارسال مجدد کد'
    showToast('خطا در ارسال مجدد پیامک. لطفاً از گزینه ربات بله استفاده کنید.', 'error')
  } finally {
    resendLoading.value = false
  }
}

const openBaleBot = () => {
  // باز کردن چت ربات بله OTP تفکر در تب جدید
  // ربات به محض استارت و کلیک روی دکمه، کد را صادر می‌کند
  const baleBotUrl = import.meta.env.VITE_BALE_OTP_BOT_URL || 'https://ble.ir/tafakor_otp_bot'
  window.open(baleBotUrl, '_blank')
  currentChannel.value = 'bale'
  showToast('ربات بله در تب جدید باز شد. شماره خود را به اشتراک بگذارید تا کد را دریافت کنید.', 'info')
}

const isOtpValid = computed(() => otp.value.length === 4)

const handleSubmit = async () => {
  if (!isOtpValid.value) return
  error.value = ''
  loading.value = true
  try {
    const res = await verifyOtp(props.phone, otp.value)
    login(res.data.token)
    window.location.href = '/'
  } catch (err) {
    error.value = 'کد تأیید نامعتبر یا منقضی شده است'
  } finally {
    loading.value = false
  }
}
</script>