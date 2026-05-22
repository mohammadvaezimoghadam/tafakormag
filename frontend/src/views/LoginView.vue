<template>
  <div class="min-h-[80vh] flex flex-col items-center justify-center">
    <div class="w-full max-w-sm">
      <div class="text-center mb-8">
        <h1 class="text-3xl font-bold text-indigo-700 mb-2">تفکر</h1>
        <p class="text-gray-500">یادداشت‌های خود را همگام در تلگرام و بله منتشر کنید</p>
      </div>
      <Transition name="fade" mode="out-in">
        <PhoneForm
          v-if="step === 'phone'"
          @otp-sent="onOtpSent"
        />
        <OtpForm
          v-else
          :phone="phone"
          :channel="sentChannel"
          @back="step = 'phone'"
        />
      </Transition>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import PhoneForm from '../components/auth/PhoneForm.vue'
import OtpForm from '../components/auth/OtpForm.vue'

const step = ref('phone')
const phone = ref('')
const sentChannel = ref('sms')

const onOtpSent = (data) => {
  phone.value = data.phone
  sentChannel.value = data.channel
  step.value = 'otp'
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