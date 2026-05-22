<template>
  <div class="p-4 bg-white rounded-2xl shadow-sm border space-y-3">
    <div class="flex items-center justify-between">
      <span class="font-medium text-gray-800 capitalize">{{ platform }}</span>
      <span v-if="connected" class="text-emerald-500 text-sm flex items-center gap-1">
        <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/></svg>
        متصل
      </span>
      <BaseButton
        v-else
        @click="getToken"
        :loading="loading"
        variant="outline"
        size="sm"
      >
        دریافت توکن
      </BaseButton>
    </div>
    <div v-if="token" class="p-3 bg-gray-50 rounded-xl text-sm text-gray-700 break-all border">
      {{ token }}
      <button @click="copyToken" class="block mt-2 text-indigo-600 text-xs hover:text-indigo-800">
        کپی توکن
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import BaseButton from '../ui/BaseButton.vue'
import { getConnectToken } from '../../api'

const props = defineProps({
  platform: { type: String, required: true },
  connected: { type: Boolean, default: false }
})

const token = ref('')
const loading = ref(false)

const getToken = async () => {
  loading.value = true
  try {
    const res = await getConnectToken(props.platform)
    token.value = res.data.token
  } catch (err) {
    // error handled by interceptor
  } finally {
    loading.value = false
  }
}

const copyToken = () => {
  navigator.clipboard.writeText(token.value)
}
</script>