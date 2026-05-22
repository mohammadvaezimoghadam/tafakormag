<template>
  <form @submit.prevent="handleSubmit" class="space-y-4">
    <BaseInput
      v-model="otp"
      type="text"
      label="کد تأیید"
      placeholder="۴ رقم"
      :error="error"
      maxlength="4"
      inputmode="numeric"
    />

    <div class="flex flex-col items-center justify-center text-sm py-1">
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
import { useRouter } from 'vue-router'

const props = defineProps({
  phone: { type: String, required: true }
})
const emit = defineEmits(['back'])

const { login } = useAuth()
const router = useRouter()
const otp = ref('')
const loading = ref(false)
const resendLoading = ref(false)
const error = ref('')

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

onMounted(() => {
  startTimer()
})

onUnmounted(() => {
  if (timerInterval) clearInterval(timerInterval)
})

const handleResend = async () => {
  if (timer.value > 0 || resendLoading.value) return
  resendLoading.value = true
  error.value = ''
  try {
    await requestOtp(props.phone)
    startTimer()
  } catch (err) {
    error.value = 'خطا در ارسال مجدد کد'
  } finally {
    resendLoading.value = false
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