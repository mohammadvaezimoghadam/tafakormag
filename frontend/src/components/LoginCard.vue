<script setup lang="ts">
import { ref, watch } from 'vue'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { InputOTP, InputOTPGroup, InputOTPSlot } from '@/components/ui/input-otp'
import { 
  SmartphoneIcon, 
  SendIcon, 
  ArrowRightIcon, 
  CheckCircle2Icon, 
  AlertTriangleIcon,
  KeyRoundIcon
} from '@lucide/vue'
import { useUserStore } from '@/stores/userStore'

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

const digits = ref(['', '', '', ''])
const inputRefs = ref<HTMLInputElement[]>([])

// Synchronize digits with otp.value
watch(digits, (newVal) => {
  otp.value = newVal.join('')
}, { deep: true })

// Synchronize state prop changes with internal flow
watch(() => props.state, (newVal) => {
  if (newVal === 'loading') {
    isLoading.value = true
    localError.value = ''
  } else if (newVal === 'error') {
    isLoading.value = false
    localError.value = props.errorMessage
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
    localError.value = 'لطفا شماره همراه خود را وارد کنید.'
    return
  }
  if (!validatePhone(phone.value)) {
    localError.value = 'فرمت شماره همراه نادرست است (مثال: ۰۹۱۲۳۴۵۶۷۸۹).'
    return
  }

  isLoading.value = true
  emit('submitPhone', phone.value)

  try {
    await userStore.requestOtp(phone.value)
    step.value = 'otp'
    emit('stateChange', 'otp')
    // Focus first slot
    setTimeout(() => {
      inputRefs.value[0]?.focus()
    }, 150)
  } catch (err: any) {
    localError.value = err.response?.data?.error || 'خطا در ارسال کد تایید. لطفاً بعداً تلاش کنید.'
  } finally {
    isLoading.value = false
  }
}

// Submitting verification code
const handleSubmitOtp = async () => {
  localError.value = ''
  if (otp.value.length < 4) {
    localError.value = 'لطفا کد تایید ۴ رقمی را به طور کامل وارد کنید.'
    return
  }

  isLoading.value = true
  emit('submitOtp', otp.value)

  try {
    await userStore.verifyOtp(phone.value, otp.value)
    emit('stateChange', 'success')
  } catch (err: any) {
    localError.value = err.response?.data?.error || 'کد تایید وارد شده معتبر نیست.'
    digits.value = ['', '', '', '']
    setTimeout(() => {
      inputRefs.value[0]?.focus()
    }, 50)
  } finally {
    isLoading.value = false
  }
}

const handleOtpInput = (e: Event, index: number) => {
  localError.value = ''
  const val = (e.target as HTMLInputElement).value
  const cleanVal = val.replace(/\D/g, '')
  const lastChar = cleanVal.slice(-1)
  
  digits.value[index] = lastChar
  ;(e.target as HTMLInputElement).value = lastChar

  if (lastChar) {
    if (index < 3) {
      setTimeout(() => {
        inputRefs.value[index + 1]?.focus()
        inputRefs.value[index + 1]?.select()
      }, 0)
    } else {
      setTimeout(() => {
        handleSubmitOtp()
      }, 50)
    }
  }
}

const handleOtpKeydown = (e: KeyboardEvent, index: number) => {
  if (e.key === 'Backspace') {
    localError.value = ''
    if (!digits.value[index] && index > 0) {
      digits.value[index - 1] = ''
      setTimeout(() => {
        inputRefs.value[index - 1]?.focus()
        inputRefs.value[index - 1]?.select()
      }, 0)
    }
  }
}

const handleOtpPaste = (e: ClipboardEvent) => {
  localError.value = ''
  const pasteData = e.clipboardData?.getData('text') || ''
  const cleanPaste = pasteData.replace(/\D/g, '').slice(0, 4)
  if (cleanPaste.length === 4) {
    for (let i = 0; i < 4; i++) {
      digits.value[i] = cleanPaste[i] || ''
    }
    setTimeout(() => {
      inputRefs.value[3]?.focus()
      handleSubmitOtp()
    }, 50)
  }
  e.preventDefault()
}

// Resetting the flow
const handleReset = () => {
  phone.value = ''
  otp.value = ''
  digits.value = ['', '', '', '']
  step.value = 'phone'
  localError.value = ''
  isLoading.value = false
  emit('stateChange', 'idle')
}
</script>

<template>
  <div class="w-full bg-card border border-border/80 rounded-lg shadow-sm overflow-hidden transition-all duration-300">
    
    <!-- HEADER -->
    <div class="p-6 bg-gradient-to-br from-secondary/40 to-secondary/10 border-b border-border/40 text-center flex flex-col items-center gap-2">
      <!-- Brand Logo / Icon -->
      <div class="size-12 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center text-primary shadow-xs">
        <SmartphoneIcon v-if="step === 'phone'" class="size-6 animate-pulse" />
        <KeyRoundIcon v-else-if="step === 'otp'" class="size-6" />
        <CheckCircle2Icon v-else class="size-6 text-emerald-500" />
      </div>
      
      <div class="flex flex-col gap-1">
        <h1 class="text-xl font-extrabold tracking-tight text-foreground">تفکر</h1>
        <p v-if="step === 'phone'" class="text-muted-foreground text-xs leading-normal">
          برای ورود شماره همراه خود را وارد کنید
        </p>
        <p v-else-if="step === 'otp'" class="text-muted-foreground text-xs leading-normal">
          کد تایید ارسال شده به شماره <code class="bg-muted px-1 py-0.5 rounded font-sans">{{ phone }}</code> را وارد کنید
        </p>
        <p v-else class="text-muted-foreground text-xs leading-normal">
          ورود شما با موفقیت انجام شد
        </p>
      </div>
    </div>

    <!-- BODY & INTERACTIVE FLOW -->
    <div class="p-6">
      
      <!-- STEP 1: PHONE FORM -->
      <div v-if="step === 'phone'" class="grid gap-4">
        <!-- Error Alert -->
        <div v-if="localError" class="flex items-start gap-2.5 p-3.5 bg-destructive/10 text-destructive rounded-lg border border-destructive/20 text-xs text-right w-full">
          <AlertTriangleIcon class="size-4 shrink-0 mt-0.5" />
          <p class="leading-relaxed font-semibold">{{ localError }}</p>
        </div>

        <div class="flex flex-col gap-1.5">
          <Label for="login-phone" class="text-xs text-muted-foreground font-semibold">شماره همراه:</Label>
          <div class="relative w-full" dir="rtl">
            <Input 
              id="login-phone" 
              type="tel" 
              v-model="phone" 
              placeholder="۰۹۱۲۳۴۵۶۷۸۹" 
              maxlength="11"
              :disabled="isLoading"
              class="h-10 text-center font-sans pr-10 tracking-widest text-sm focus-visible:ring-primary/20"
              @keyup.enter="handleSubmitPhone"
            />
            <span class="absolute inset-y-0 right-3 flex items-center pointer-events-none text-muted-foreground/60">
              <SmartphoneIcon class="size-4" />
            </span>
          </div>
        </div>

        <Button 
          type="submit"
          @click="handleSubmitPhone" 
          :disabled="isLoading" 
          class="w-full flex items-center justify-center gap-2 cursor-pointer"
        >
          <span v-if="isLoading" class="flex items-center gap-1.5">
            <span class="size-3.5 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin" />
            در حال ارسال...
          </span>
          <span v-else class="flex items-center gap-2">
            ارسال کد تایید
            <SendIcon data-icon="inline-end" />
          </span>
        </Button>
      </div>

      <!-- STEP 2: OTP VERIFICATION -->
      <div v-else-if="step === 'otp'" class="grid gap-4">
        <!-- Error Alert -->
        <div v-if="localError" class="flex items-start gap-2.5 p-3.5 bg-destructive/10 text-destructive rounded-lg border border-destructive/20 text-xs text-right w-full">
          <AlertTriangleIcon class="size-4 shrink-0 mt-0.5" />
          <p class="leading-relaxed font-semibold">{{ localError }}</p>
        </div>

        <div class="flex flex-col items-center gap-3">
          <Label class="text-xs text-muted-foreground font-semibold text-center">کد تایید ۴ رقمی:</Label>
          <div dir="ltr" class="flex justify-center gap-3.5 w-full" style="direction: ltr;">
            <input
              v-for="(digit, index) in digits"
              :key="index"
              :ref="el => { if (el) inputRefs[index] = el as HTMLInputElement }"
              :value="digits[index]"
              type="text"
              inputmode="numeric"
              maxlength="1"
              :disabled="isLoading"
              class="w-12 h-12 text-center text-xl font-bold bg-background border border-input rounded-xl focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-all shadow-inner font-sans"
              :class="localError ? 'border-destructive bg-destructive/5 text-destructive focus:ring-destructive focus:border-destructive' : ''"
              @input="handleOtpInput($event, index)"
              @keydown="handleOtpKeydown($event, index)"
              @paste="handleOtpPaste"
              @focus="($event.target as HTMLInputElement).select()"
            />
          </div>
        </div>

        <div class="flex flex-col gap-2">
          <Button 
            type="submit"
            @click="handleSubmitOtp" 
            :disabled="isLoading" 
            class="w-full flex items-center justify-center gap-2 cursor-pointer"
          >
            <span v-if="isLoading" class="flex items-center gap-1.5">
              <span class="size-3.5 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin" />
              در حال بررسی...
            </span>
            <span v-else class="flex items-center gap-2">
              بررسی کد تایید
              <CheckCircle2Icon data-icon="inline-end" />
            </span>
          </Button>

          <button 
            @click="step = 'phone'; localError = ''" 
            :disabled="isLoading" 
            class="text-[11px] text-primary hover:underline font-medium text-center py-2 flex items-center justify-center gap-1 cursor-pointer disabled:opacity-50"
          >
            <ArrowRightIcon class="size-3" />
            تغییر شماره همراه
          </button>
        </div>
      </div>

      <!-- STEP 3: LOGIN SUCCESS -->
      <div v-else class="grid gap-6 text-center py-4">
        <div class="text-emerald-600 dark:text-emerald-400 flex flex-col items-center gap-3">
          <CheckCircle2Icon class="size-16 animate-bounce" />
          <h2 class="text-lg font-extrabold text-foreground">خوش آمدید!</h2>
          <p class="text-xs text-muted-foreground max-w-xs leading-relaxed">
            احراز هویت شما با موفقیت به پایان رسید و شما وارد سامانه تفکر شدید.
          </p>
        </div>

        <Button 
          variant="outline" 
          @click="handleReset" 
          class="w-full flex items-center justify-center gap-2 cursor-pointer"
        >
          خروج از حساب / تست مجدد
        </Button>
      </div>

    </div>

  </div>
</template>
