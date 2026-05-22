<template>
  <form @submit.prevent="handleSubmit" class="space-y-4">
    <!-- نمایش مقصد ارسال کد تایید با طراحی پریمیوم -->
    <div class="p-3 bg-indigo-50 border border-indigo-100 rounded-lg text-sm text-indigo-800 text-center mb-4 flex items-center justify-center gap-2 transition-all duration-300">
      <span class="flex h-2 w-2 relative" v-if="currentChannel !== 'sms' && currentChannel !== 'debug'">
        <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
        <span class="relative inline-flex rounded-full h-2 w-2 bg-indigo-500"></span>
      </span>
      <span v-if="currentChannel === 'bale'">💬 کد تأیید به <strong>پیام‌رسان بله</strong> شما ارسال شد.</span>
      <span v-else-if="currentChannel === 'telegram'">✈️ کد تأیید به <strong>ربات تلگرام</strong> شما ارسال شد.</span>
      <span v-else-if="currentChannel === 'sms'">📱 کد تأیید به صورت <strong>پیامک (SMS)</strong> ارسال شد.</span>
      <span v-else-if="currentChannel === 'debug'">🛠️ [توسعه] کد در کنسول چاپ شد.</span>
    </div>

    <BaseInput
      v-model="otp"
      type="text"
      label="کد تأیید"
      placeholder="۴ رقم"
      :error="error"
      maxlength="4"
      inputmode="numeric"
    />

    <div class="flex flex-col items-center justify-center text-sm py-1 space-y-3">
      <!-- بخش تایمر و ارسال مجدد عمومی -->
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
        <span>ارسال مجدد کد تأیید</span>
      </button>

      <!-- دکمه درخواست ارسال مجدد از طریق پیامک عادی در صورت متصل بودن به بات -->
      <div v-if="currentChannel !== 'sms' && currentChannel !== 'debug'" class="w-full border-t border-gray-100 pt-3 flex justify-center">
        <button
          type="button"
          @click="handleRequestSMS"
          :disabled="smsLoading"
          class="text-amber-600 hover:text-amber-800 font-medium transition-colors duration-200 flex items-center gap-1.5 focus:outline-none"
        >
          <span v-if="smsLoading" class="inline-block w-4 h-4 border-2 border-amber-600 border-t-transparent rounded-full animate-spin"></span>
          <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
          </svg>
          <span>کد را به صورت پیامک (SMS) ارسال کن</span>
        </button>
      </div>
    </div>

    <BaseButton
      type="submit"
      variant="primary"
      :disabled="!isOtpValid"
      :loading="loading"
    >
      ورود
    </BaseButton>

    <button type="button" @click="$emit('back')" class="w-full text-center text-sm text-gray-500 hover:text-indigo-600 transition-colors duration-200 mt-2">
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
import { useRouter } from 'vue-router'

const props = defineProps({
  phone: { type: String, required: true },
  channel: { type: String, default: 'sms' }
})
const emit = defineEmits(['back'])

const { login } = useAuth()
const { showToast } = useToast()
const router = useRouter()
const otp = ref('')
const loading = ref(false)
const resendLoading = ref(false)
const smsLoading = ref(false)
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
  if (chan === 'bale') {
    showToast('کد ورود با موفقیت به ربات بله شما ارسال شد.', 'success')
  } else if (chan === 'telegram') {
    showToast('کد ورود با موفقیت به ربات تلگرام شما ارسال شد.', 'success')
  } else if (chan === 'sms') {
    showToast('کد ورود با موفقیت به صورت پیامک ارسال شد.', 'success')
  } else if (chan === 'debug') {
    showToast('حالت آزمایشی: کد ورود در کنسول سرور چاپ شد.', 'info')
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
  } finally {
    resendLoading.value = false
  }
}

const handleRequestSMS = async () => {
  if (smsLoading.value) return
  smsLoading.value = true
  error.value = ''
  try {
    // فراخوانی با فورس اس‌ام‌اس
    const res = await requestOtp(props.phone, true)
    currentChannel.value = res.data?.channel || 'sms'
    startTimer()
    notifyChannel(currentChannel.value)
  } catch (err) {
    error.value = 'سامانه پیامکی در دسترس نیست؛ لطفاً از ربات استفاده کنید.'
  } finally {
    smsLoading.value = false
  }
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
    error.value = 'کد نامعتبر یا منقضی شده'
  } finally {
    loading.value = false
  }
}
</script>