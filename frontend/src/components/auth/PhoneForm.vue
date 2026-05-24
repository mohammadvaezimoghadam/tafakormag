<template>
  <form @submit.prevent="handleSubmit" class="space-y-4">
    <BaseInput
      v-model="phone"
      type="tel"
      label="شماره موبایل"
      placeholder="۰۹xxxxxxxxx"
      :error="error"
      maxlength="11"
      inputmode="numeric"
      class="text-center font-semibold tracking-wider text-base"
      :disabled="loading"
    />
    <BaseButton
      type="submit"
      variant="primary"
      :disabled="!isPhoneValid"
      :loading="loading"
    >
      ارسال کد تأیید ورود
    </BaseButton>
  </form>
</template>

<script setup>
import { ref, computed } from 'vue'
import BaseInput from '../ui/BaseInput.vue'
import BaseButton from '../ui/BaseButton.vue'
import { requestOtp } from '../../api'
import { useToast } from '../../composables/useToast'

const emit = defineEmits(['otp-sent'])
const { showToast } = useToast()

const phone = ref('')
const loading = ref(false)
const error = ref('')

const isPhoneValid = computed(() => phone.value.length === 11 && /^09\d{9}$/.test(phone.value))

const handleSubmit = async () => {
  if (!isPhoneValid.value) return
  error.value = ''
  loading.value = true
  try {
    const res = await requestOtp(phone.value)
    const channel = res.data?.channel || 'sms'
    emit('otp-sent', { phone: phone.value, channel })
  } catch (err) {
    // خطا در ارسال پیامک: کاربر را باز هم به فرم بعد می‌بریم تا بتواند از بله استفاده کند
    showToast('سامانه پیامکی با اختلال مواجه شد. در مرحله بعد می‌توانید کد را از ربات بله دریافت کنید.', 'error')
    emit('otp-sent', { phone: phone.value, channel: 'sms' })
  } finally {
    loading.value = false
  }
}
</script>