<template>
  <Teleport to="body">
    <div class="fixed inset-0 z-50 flex items-end sm:items-center justify-center">
      <!-- Backdrop -->
      <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" @click="$emit('close')" />

      <!-- Panel -->
      <div class="relative w-full max-w-sm bg-white rounded-t-3xl sm:rounded-3xl shadow-2xl p-6 animate-slide-up z-10 text-right">
        <!-- Close Button -->
        <button @click="$emit('close')" class="absolute top-4 left-4 text-gray-400 hover:text-gray-600 hover:bg-gray-50 p-1.5 rounded-full transition-all">
          <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        <div class="text-center mt-3 mb-6">
          <div class="w-12 h-12 bg-indigo-50 text-indigo-600 rounded-2xl flex items-center justify-center mx-auto mb-3">
            <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
          <h3 class="text-base font-black text-gray-800">ورود به حساب تفکر</h3>
          <p class="text-xs text-gray-400 mt-1.5 px-2">برای انجام کنش‌ها (ثبت نظر یا واکنش) ابتدا باید شماره موبایل خود را وارد کنید.</p>
        </div>

        <form @submit.prevent="handleRequestOtp" class="space-y-4">
          <div>
            <label class="block text-xs font-bold text-gray-500 mb-1.5 pr-1">شماره موبایل</label>
            <input
              v-model="phone"
              type="tel"
              placeholder="مثال: 09123456789"
              class="w-full bg-gray-50 text-center px-4 py-3 rounded-2xl border border-gray-200 text-sm font-bold focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 focus:bg-white transition-all dir-ltr"
              :class="phoneError ? 'border-red-400' : ''"
              required
            />
            <p v-if="phoneError" class="text-[10px] text-red-500 mt-1 pr-1">{{ phoneError }}</p>
          </div>

          <BaseButton
            type="submit"
            variant="primary"
            :loading="loading"
            class="w-full rounded-2xl py-3 font-extrabold shadow-lg"
          >
            دریافت کد تأیید
          </BaseButton>
        </form>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import BaseButton from '../ui/BaseButton.vue'
import { requestOtp } from '../../api'
import { useToast } from '../../composables/useToast'

const emit = defineEmits(['close'])

const router = useRouter()
const { showToast } = useToast()

const phone = ref('')
const loading = ref(false)
const phoneError = ref('')

const validatePhone = (p) => {
  const regex = /^09\d{9}$/
  return regex.test(p)
}

const handleRequestOtp = async () => {
  phoneError.value = ''
  const cleanPhone = phone.value.trim()
  
  if (!validatePhone(cleanPhone)) {
    phoneError.value = 'شماره موبایل نامعتبر است (مانند: 09123456789)'
    return
  }

  loading.value = true
  try {
    const res = await requestOtp(cleanPhone)
    showToast(res.data?.message || 'کد ورود ارسال شد', 'success')
    emit('close')
    
    // ریدایرکت به صفحه لاگین با پر کردن شماره تلفن و مرحله ورود کد تایید
    router.push({
      name: 'login',
      query: {
        phone: cleanPhone,
        channel: res.data?.channel || 'sms'
      }
    })
  } catch (err) {
    phoneError.value = err.response?.data?.error || 'خطا در ارسال کد تایید'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.animate-slide-up {
  animation: slideUp 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}
@keyframes slideUp {
  from {
    transform: translateY(100%);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}
</style>
