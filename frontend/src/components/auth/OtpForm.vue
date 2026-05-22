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
    <BaseButton
      type="submit"
      variant="primary"
      :disabled="!isOtpValid"
      :loading="loading"
    >
      ورود
    </BaseButton>
    <button type="button" @click="$emit('back')" class="w-full text-center text-sm text-indigo-600 hover:text-indigo-800 mt-2">
      اصلاح شماره موبایل
    </button>
  </form>
</template>

<script setup>
import { ref, computed } from 'vue'
import BaseInput from '../ui/BaseInput.vue'
import BaseButton from '../ui/BaseButton.vue'
import { verifyOtp } from '../../api'
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
const error = ref('')

const isOtpValid = computed(() => otp.value.length === 4)

const handleSubmit = async () => {
  if (!isOtpValid.value) return
  error.value = ''
  loading.value = true
  try {
    const res = await verifyOtp(props.phone, otp.value)
    login(res.data.token)
    // ریدایرکت کامل با reload برای اطمینان از خواندن توکن
    window.location.href = '/'
  } catch (err) {
    error.value = 'کد نامعتبر یا منقضی شده'
  } finally {
    loading.value = false
  }
}
</script>