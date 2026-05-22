<template>
  <form @submit.prevent="handleSubmit" class="space-y-4">
    <BaseInput
      v-model="phone"
      type="tel"
      label="شماره موبایل"
      placeholder="۰۹xxxxxxxxx"
      :error="error"
      maxlength="11"
    />
    <BaseButton
      type="submit"
      variant="primary"
      :disabled="!isPhoneValid"
      :loading="loading"
    >
      ارسال کد تأیید
    </BaseButton>
  </form>
</template>

<script setup>
import { ref, computed } from 'vue'
import BaseInput from '../ui/BaseInput.vue'
import BaseButton from '../ui/BaseButton.vue'
import { requestOtp } from '../../api'

const emit = defineEmits(['otp-sent'])

const phone = ref('')
const loading = ref(false)
const error = ref('')

const isPhoneValid = computed(() => phone.value.length === 11 && /^\d+$/.test(phone.value))

const handleSubmit = async () => {
  if (!isPhoneValid.value) return
  error.value = ''
  loading.value = true
  try {
    await requestOtp(phone.value)
    emit('otp-sent', phone.value)
  } catch (err) {
    error.value = 'خطا در ارسال کد'
  } finally {
    loading.value = false
  }
}
</script>