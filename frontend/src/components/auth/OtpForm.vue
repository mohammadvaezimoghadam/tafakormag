<template>
  <form @submit.prevent="handleSubmit" class="space-y-5">
    <!-- جعبه زیبای نمایش وضعیت و مقصد ارسال کد تایید -->
    <div class="p-4 bg-indigo-50/70 border border-indigo-100/50 rounded-2xl text-xs text-indigo-900 text-right space-y-1 shadow-sm transition-all duration-300">
      <div class="flex items-center gap-2">
        <span class="flex h-2 w-2 relative" v-if="currentChannel === 'sms'">
          <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
          <span class="relative inline-flex rounded-full h-2 w-2 bg-indigo-500"></span>
        </span>
        <span class="font-extrabold text-indigo-950">
          {{ currentChannel === 'sms' ? '📱 کد تأیید پیامک شد' : currentChannel === 'bale' ? '💬 کد تأیید در بله صادر شد' : '🛠️ حالت شبیه‌سازی فعال است' }}
        </span>
      </div>
      <p class="text-gray-500 leading-relaxed">
        کد ورود ۴ رقمی به شماره <span class="font-black text-indigo-700 font-mono">{{ phone }}</span> ارسال شده است.
      </p>
    </div>

    <!-- فیلد وارد کردن کد تایید -->
    <div class="space-y-2.5">
      <label class="block text-xs font-black text-gray-500 pr-1">کد تأیید ورود</label>
      <div class="flex justify-center gap-3" dir="ltr" style="direction: ltr;">
        <input
          v-for="(digit, index) in digits"
          :key="index"
          :ref="el => { if (el) inputRefs[index] = el }"
          :value="digits[index]"
          type="text"
          inputmode="numeric"
          class="w-14 h-14 text-center text-2xl font-black bg-gray-50 border border-gray-200 rounded-2xl focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 focus:bg-white transition-all shadow-inner font-mono"
          :class="error ? 'border-red-400 bg-red-50/20 text-red-600 focus:ring-red-400 focus:border-red-400' : ''"
          @input="handleInput($event, index)"
          @keydown="handleKeydown($event, index)"
          @paste="handlePaste"
          @focus="$event.target.select()"
        />
      </div>
      <Transition name="fade">
        <p v-if="error" class="text-xs text-red-500 text-center font-bold mt-1.5">{{ error }}</p>
      </Transition>
    </div>

    <!-- شمارش معکوس و دکمه ارسال مجدد -->
    <div class="flex flex-col items-center justify-center text-xs py-2 space-y-4">
      <div v-if="timer > 0" class="text-gray-400 flex items-center gap-1.5 font-medium">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-indigo-500 animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span>ارسال مجدد کد پس از:</span>
        <span class="font-mono text-indigo-600 text-sm font-black">{{ formattedTime }}</span>
      </div>
      
      <button
        v-else
        type="button"
        @click="handleResend"
        :disabled="resendLoading"
        class="text-indigo-600 hover:text-indigo-800 font-extrabold transition-colors duration-200 flex items-center gap-1 focus:outline-none"
      >
        <span v-if="resendLoading" class="inline-block w-4 h-4 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin"></span>
        <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M4 4v5h.582m15.356 2A8.001 8.001 0 1121.21 8H17" />
        </svg>
        <span>ارسال مجدد کد تأیید (پیامک)</span>
      </button>

      <!-- دکمه ربات بله (Bale OTP Fallback Button) -->
      <div class="w-full border-t border-gray-100 pt-4 flex flex-col items-center gap-2.5">
        <button
          type="button"
          @click="openBaleBot"
          class="px-4 py-2.5 text-xs font-black text-emerald-700 bg-emerald-50 border border-emerald-100 hover:bg-emerald-100/70 hover:border-emerald-200 rounded-2xl transition-all duration-200 flex items-center gap-2 shadow-sm active:scale-95 focus:outline-none"
        >
          <span class="text-sm">💬</span>
          <span>دریافت سریع کد ورود در ربات بله</span>
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
      class="shadow-md mt-2"
    >
      ورود به تفکر
    </BaseButton>

    <!-- اصلاح شماره -->
    <button type="button" @click="$emit('back')" class="w-full text-center text-xs text-gray-400 hover:text-indigo-600 transition-colors duration-200 mt-2 font-bold">
      اصلاح شماره موبایل
    </button>
  </form>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
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

const digits = ref(['', '', '', ''])
const inputRefs = []

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

const handleInput = (e, index) => {
  error.value = ''
  const val = e.target.value
  const cleanVal = val.replace(/\D/g, '')
  const lastChar = cleanVal.slice(-1)
  
  digits.value[index] = lastChar
  e.target.value = lastChar // بروزرسانی مستقیم مقدار فیلد در DOM برای اطمینان

  if (lastChar) {
    if (index < 3) {
      // تغییر فوکوس به فیلد بعدی در تیک بعدی مرورگر برای همگام‌سازی با کیبورد مجازی
      setTimeout(() => {
        inputRefs[index + 1]?.focus()
        inputRefs[index + 1]?.select()
      }, 0)
    } else {
      // ارسال خودکار فرم پس از پر شدن آخرین رقم
      setTimeout(() => {
        handleSubmit()
      }, 50)
    }
  }
}

const handleKeydown = (e, index) => {
  if (e.key === 'Backspace') {
    error.value = ''
    if (!digits.value[index] && index > 0) {
      digits.value[index - 1] = ''
      setTimeout(() => {
        inputRefs[index - 1]?.focus()
        inputRefs[index - 1]?.select()
      }, 0)
    }
  }
}

const handlePaste = (e) => {
  error.value = ''
  const pasteData = e.clipboardData.getData('text')
  const cleanPaste = pasteData.replace(/\D/g, '').slice(0, 4)
  if (cleanPaste.length === 4) {
    for (let i = 0; i < 4; i++) {
      digits.value[i] = cleanPaste[i]
    }
    setTimeout(() => {
      inputRefs[3]?.focus()
      handleSubmit()
    }, 50)
  }
  e.preventDefault()
}

const otp = computed(() => digits.value.join(''))
const isOtpValid = computed(() => otp.value.length === 4)

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
  setTimeout(() => {
    inputRefs[0]?.focus()
  }, 150)
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
  const baleBotUrl = import.meta.env.VITE_BALE_OTP_BOT_URL || 'https://ble.ir/tafakor_otp_bot'
  window.open(baleBotUrl, '_blank')
  currentChannel.value = 'bale'
  showToast('ربات بله در تب جدید باز شد. شماره خود را به اشتراک بگذارید تا کد را دریافت کنید.', 'info')
}

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
    // پاک کردن کد نامعتبر و بازگرداندن فوکوس به خانه اول
    digits.value = ['', '', '', '']
    setTimeout(() => {
      inputRefs[0]?.focus()
    }, 50)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>