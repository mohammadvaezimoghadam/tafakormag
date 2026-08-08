<script setup lang="ts">
import { ref, watch, onUnmounted, computed } from 'vue'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { InputOTP, InputOTPGroup, InputOTPSlot } from '@/components/ui/input-otp'
import { 
  SendIcon, 
  ArrowRightIcon, 
  CheckCircle2Icon, 
  AlertTriangleIcon,
  ClockIcon, 
  RotateCcwIcon, 
  Loader2Icon 
} from '@lucide/vue'
import { useUserStore } from '@/stores/userStore'
import { useToastStore } from '@/stores/toastStore'
import { useLanguageStore } from '@/stores/languageStore'

const toastStore = useToastStore()
const languageStore = useLanguageStore()

// Props to control state from the playground
const props = withDefaults(defineProps<{
  state?: 'idle' | 'loading' | 'error' | 'success'
  errorMessage?: string
}>(), {
  state: 'idle',
  errorMessage: 'شماره همراه وارد شده معتبر نیست. لطفا شماره معتبری وارد کنید.'
})

const emit = defineEmits<{
  (e: 'submitPhone', phone: string): void
  (e: 'submitOtp', otp: string): void
  (e: 'stateChange', newState: string): void
}>()

const userStore = useUserStore()

// Internal states for the interactive flow
const phone = ref('')
const otp = ref('')
const step = ref<'phone' | 'otp' | 'success'>('phone')
const isLoading = ref(false)
const localError = ref('')

// Countdown Timer logic
const cooldown = ref(60)
let timerId: any = null

const startTimer = () => {
  cooldown.value = 60
  if (timerId) clearInterval(timerId)
  timerId = setInterval(() => {
    if (cooldown.value > 0) {
      cooldown.value--
    } else {
      clearInterval(timerId)
      timerId = null
    }
  }, 1000)
}

const formattedTime = computed(() => {
  const minutes = Math.floor(cooldown.value / 60)
  const seconds = cooldown.value % 60
  return languageStore.n(`${minutes}:${seconds.toString().padStart(2, '0')}`)
})

const handleResendOtp = async () => {
  if (cooldown.value > 0) return
  isLoading.value = true
  localError.value = ''
  try {
    await userStore.requestOtp(phone.value)
    startTimer()
    toastStore.triggerToast(languageStore.t('کد تایید مجدداً ارسال شد.', 'Verification code resent successfully.'), 'success')
  } catch (err: any) {
    const errorText = err.response?.data?.error || languageStore.t('خطا در ارسال مجدد کد تایید.', 'Failed to resend verification code.')
    localError.value = errorText
    toastStore.triggerToast(errorText, 'error')
  } finally {
    isLoading.value = false
  }
}

const handleResetPhone = () => {
  step.value = 'phone'
  localError.value = ''
  if (timerId) {
    clearInterval(timerId)
    timerId = null
  }
}

// Reset state when the global login modal is opened/closed
watch(() => userStore.isLoginModalOpen, (newVal) => {
  if (newVal) {
    phone.value = ''
    otp.value = ''
    step.value = 'phone'
    localError.value = ''
    isLoading.value = false
    if (timerId) {
      clearInterval(timerId)
      timerId = null
    }
  }
})

// Synchronize state prop changes with internal flow
watch(() => props.state, (newVal) => {
  if (newVal === 'loading') {
    isLoading.value = true
    localError.value = ''
  } else if (newVal === 'error') {
    isLoading.value = false
    localError.value = props.errorMessage === 'شماره همراه وارد شده معتبر نیست. لطفا شماره معتبری وارد کنید.'
      ? languageStore.t('شماره همراه وارد شده معتبر نیست. لطفا شماره معتبری وارد کنید.', 'The entered mobile number is not valid. Please enter a valid number.')
      : props.errorMessage
  } else if (newVal === 'success') {
    isLoading.value = false
    localError.value = ''
    step.value = 'success'
  } else {
    isLoading.value = false
    localError.value = ''
    step.value = 'phone'
  }
})

// Validation helper
const validatePhone = (value: string) => {
  const phoneRegex = /^09\d{9}$/
  return phoneRegex.test(value)
}

// Submitting phone number
const handleSubmitPhone = async () => {
  localError.value = ''
  if (!phone.value) {
    toastStore.triggerToast(languageStore.t('لطفا شماره همراه خود را وارد کنید.', 'Please enter your mobile number.'), 'error')
    return
  }
  if (!validatePhone(phone.value)) {
    toastStore.triggerToast(languageStore.t('فرمت شماره همراه نادرست است (مثال: ۰۹۱۲۳۴۵۶۷۸۹).', 'Invalid phone format (e.g., 09123456789).'), 'error')
    return
  }

  isLoading.value = true
  emit('submitPhone', phone.value)

  try {
    await userStore.requestOtp(phone.value)
    step.value = 'otp'
    startTimer()
    emit('stateChange', 'otp')
  } catch (err: any) {
    const errorText = err.response?.data?.error || languageStore.t('خطا در ارسال کد تایید. لطفاً بعداً تلاش کنید.', 'Failed to send verification code. Please try again later.')
    localError.value = errorText
    toastStore.triggerToast(errorText, 'error')
  } finally {
    isLoading.value = false
  }
}

// Submitting verification code
const handleSubmitOtp = async () => {
  localError.value = ''
  if (otp.value.length < 4) {
    toastStore.triggerToast(languageStore.t('لطفا کد تایید ۴ رقمی را به طور کامل وارد کنید.', 'Please enter the complete 4-digit code.'), 'error')
    return
  }

  isLoading.value = true
  emit('submitOtp', otp.value)

  try {
    await userStore.verifyOtp(phone.value, otp.value)
    emit('stateChange', 'success')
  } catch (err: any) {
    const errorText = err.response?.data?.error || languageStore.t('کد تایید وارد شده معتبر نیست.', 'The entered verification code is not valid.')
    localError.value = errorText
    toastStore.triggerToast(errorText, 'error')
    otp.value = ''
  } finally {
    isLoading.value = false
  }
}

// Resetting the flow
const handleReset = () => {
  phone.value = ''
  otp.value = ''
  step.value = 'phone'
  localError.value = ''
  isLoading.value = false
  if (timerId) {
    clearInterval(timerId)
    timerId = null
  }
  emit('stateChange', 'idle')
}

onUnmounted(() => {
  if (timerId) clearInterval(timerId)
})
</script>

<template>
  <div 
    class="w-full bg-card/80 dark:bg-card/50 border border-border/60 backdrop-blur-xl rounded-2xl sm:rounded-3xl overflow-hidden shadow-sm transition-all duration-300 font-sans"
    :dir="languageStore.dir"
  >
    
    <!-- HEADER -->
    <div class="pt-6 sm:pt-7 pb-2 px-5 sm:px-6 text-center flex flex-col items-center gap-1.5">
      <h1 class="text-lg sm:text-xl font-bold tracking-tight text-foreground">
        {{ languageStore.t('ورود به تفکر', 'Sign in to Tafakor') }}
      </h1>
      <p v-if="step === 'phone'" class="text-muted-foreground text-xs leading-relaxed">
        {{ languageStore.t('برای ورود شماره همراه خود را وارد کنید', 'Enter your mobile number to sign in') }}
      </p>
      <p v-else-if="step === 'otp'" class="text-muted-foreground text-xs leading-relaxed">
        {{ languageStore.t('کد تایید ارسال شده به شماره', 'Enter the code sent to') }} 
        <span class="text-foreground font-mono font-bold bg-muted/60 px-1.5 py-0.5 rounded-md mx-0.5" dir="ltr">{{ languageStore.n(phone) }}</span>
      </p>
      <p v-else class="text-muted-foreground text-xs leading-relaxed">
        {{ languageStore.t('ورود شما با موفقیت انجام شد', 'You have successfully signed in') }}
      </p>
    </div>

    <!-- BODY & INTERACTIVE FLOW -->
    <div class="p-5 sm:p-6 pt-2">
      
      <!-- Inline Error Alert -->
      <transition name="alert-slide">
        <div 
          v-if="localError" 
          class="flex items-start gap-2.5 p-3 bg-destructive/10 text-destructive rounded-xl border border-destructive/20 text-xs font-semibold text-start mb-4 shadow-2xs"
        >
          <AlertTriangleIcon class="size-4 shrink-0 mt-0.5" />
          <p class="leading-relaxed">{{ localError }}</p>
        </div>
      </transition>
      
      <!-- STEP 1: PHONE FORM (Clean input without mobile icon) -->
      <div v-if="step === 'phone'" class="grid gap-4">

        <div class="flex flex-col gap-1.5">
          <Label for="login-phone" class="text-xs text-muted-foreground font-semibold">
            {{ languageStore.t('شماره همراه:', 'Mobile Number:') }}
          </Label>
          
          <!-- Pure, crisp input without mobile icon clutter -->
          <Input 
            id="login-phone" 
            type="tel" 
            v-model="phone" 
            :placeholder="languageStore.t('۰۹۱۲۳۴۵۶۷۸۹', '09123456789')" 
            maxlength="11"
            :disabled="isLoading"
            dir="ltr"
            class="h-10 text-center font-mono font-bold tracking-widest text-sm rounded-xl bg-background/60 border-border/70 focus-visible:ring-primary/20 shadow-2xs"
            @keyup.enter="handleSubmitPhone"
          />
        </div>

        <Button 
          type="submit"
          @click="handleSubmitPhone" 
          :disabled="isLoading" 
          class="w-full h-10 rounded-xl font-bold text-xs flex items-center justify-center gap-2 cursor-pointer shadow-xs hover:scale-101 active:scale-98 transition-all"
        >
          <span v-if="isLoading" class="flex items-center gap-1.5">
            <Loader2Icon class="size-4 animate-spin" />
            {{ languageStore.t('در حال ارسال...', 'Sending...') }}
          </span>
          <span v-else class="flex items-center gap-2" :class="[languageStore.isFa ? 'flex-row' : 'flex-row-reverse']">
            <span>{{ languageStore.t('ارسال کد تایید', 'Send Verification Code') }}</span>
            <SendIcon class="size-3.5" :class="[languageStore.isFa ? '' : 'rotate-180']" />
          </span>
        </Button>
      </div>

      <!-- STEP 2: OTP VERIFICATION -->
      <div v-else-if="step === 'otp'" class="grid gap-4">

        <div class="flex flex-col items-center gap-3">
          <Label class="text-xs text-muted-foreground font-semibold text-center">
            {{ languageStore.t('کد تایید ۴ رقمی:', '4-Digit Verification Code:') }}
          </Label>
          
          <div dir="ltr" class="flex justify-center w-full">
            <InputOTP v-model="otp" :maxlength="4" :disabled="isLoading" @complete="handleSubmitOtp">
              <InputOTPGroup class="gap-1.5">
                <InputOTPSlot :index="0" class="rounded-lg! border shadow-2xs" />
                <InputOTPSlot :index="1" class="rounded-lg! border shadow-2xs" />
                <InputOTPSlot :index="2" class="rounded-lg! border shadow-2xs" />
                <InputOTPSlot :index="3" class="rounded-lg! border shadow-2xs" />
              </InputOTPGroup>
            </InputOTP>
          </div>

          <!-- Countdown Timer Badge or Resend Button -->
          <div class="flex items-center justify-center min-h-[32px] mt-1 transition-all duration-300">
            <transition name="timer-fade" mode="out-in">
              <div 
                v-if="cooldown > 0" 
                class="inline-flex items-center gap-1.5 px-3 py-1 bg-muted/40 text-muted-foreground border border-border/50 rounded-full text-[10px] font-semibold tracking-normal shadow-2xs"
              >
                <ClockIcon class="size-3 text-primary/70" />
                <span>{{ languageStore.t('ارسال مجدد پس از', 'Resend in') }} {{ formattedTime }}</span>
              </div>
              <button 
                v-else 
                type="button"
                @click="handleResendOtp" 
                :disabled="isLoading"
                class="inline-flex items-center gap-1.5 px-3 py-1 bg-secondary text-secondary-foreground hover:bg-secondary/80 hover:text-foreground border border-border/40 rounded-full text-[10px] font-bold transition-all duration-200 shadow-2xs cursor-pointer disabled:opacity-50"
              >
                <RotateCcwIcon class="size-3 text-muted-foreground" />
                <span>{{ languageStore.t('ارسال مجدد کد تایید', 'Resend Verification Code') }}</span>
              </button>
            </transition>
          </div>
        </div>

        <div class="flex flex-col gap-2">
          <Button 
            type="submit"
            @click="handleSubmitOtp" 
            :disabled="isLoading" 
            class="w-full h-10 rounded-xl font-bold text-xs flex items-center justify-center gap-2 cursor-pointer shadow-xs hover:scale-101 active:scale-98 transition-all"
          >
            <span v-if="isLoading" class="flex items-center gap-1.5">
              <Loader2Icon class="size-4 animate-spin" />
              {{ languageStore.t('در حال بررسی...', 'Verifying...') }}
            </span>
            <span v-else class="flex items-center gap-2">
              <span>{{ languageStore.t('بررسی کد تایید', 'Verify Code') }}</span>
              <CheckCircle2Icon class="size-3.5" />
            </span>
          </Button>

          <button 
            @click="handleResetPhone" 
            :disabled="isLoading" 
            class="text-[11px] text-muted-foreground hover:text-primary font-medium text-center py-1.5 flex items-center justify-center gap-1 cursor-pointer transition-colors disabled:opacity-50"
            :class="[languageStore.isFa ? 'flex-row' : 'flex-row-reverse']"
          >
            <ArrowRightIcon class="size-3" :class="[languageStore.isFa ? '' : 'rotate-180']" />
            <span>{{ languageStore.t('تغییر شماره همراه', 'Change Phone Number') }}</span>
          </button>
        </div>
      </div>

      <!-- STEP 3: LOGIN SUCCESS -->
      <div v-else class="grid gap-5 text-center py-3">
        <div class="flex flex-col items-center gap-2.5">
          <div class="size-14 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-500 shadow-xs mb-1">
            <CheckCircle2Icon class="size-8" />
          </div>
          <h2 class="text-base sm:text-lg font-bold text-foreground">
            {{ languageStore.t('خوش آمدید!', 'Welcome!') }}
          </h2>
          <p class="text-xs text-muted-foreground max-w-xs leading-relaxed">
            {{ languageStore.t('احراز هویت شما با موفقیت انجام شد و وارد سامانه تفکر شدید.', 'Your authentication was successful and you are now signed in to Tafakor.') }}
          </p>
        </div>

        <Button 
          variant="outline" 
          @click="handleReset" 
          class="w-full h-9 rounded-xl text-xs font-semibold flex items-center justify-center gap-2 cursor-pointer border-border/60 hover:bg-muted/50"
        >
          {{ languageStore.t('خروج از حساب / تست مجدد', 'Sign Out / Test Again') }}
        </Button>
      </div>

    </div>

  </div>
</template>

<style scoped>
.alert-slide-enter-active,
.alert-slide-leave-active {
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}
.alert-slide-enter-from,
.alert-slide-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

.timer-fade-enter-active,
.timer-fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.timer-fade-enter-from,
.timer-fade-leave-to {
  opacity: 0;
  transform: scale(0.96);
}
</style>
