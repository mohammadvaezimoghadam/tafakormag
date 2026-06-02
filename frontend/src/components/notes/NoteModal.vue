<template>
  <Teleport to="body">
    <div class="fixed inset-0 z-50 flex items-end sm:items-center justify-center">
      <!-- Backdrop -->
      <div class="absolute inset-0 bg-black/50" @click="$emit('close')" />
      <!-- Panel -->
      <div class="relative w-full max-w-md bg-white rounded-t-3xl sm:rounded-2xl shadow-2xl p-6 max-h-[90vh] overflow-y-auto animate-slide-up">
        <!-- Header -->
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-base font-extrabold text-gray-800">{{ isEdit ? 'ویرایش یادداشت' : 'یادداشت جدید' }}</h2>
          <button @click="$emit('close')" class="text-gray-400 hover:text-gray-600 p-1">
            <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form @submit.prevent="handleSave" class="space-y-4">
          <BaseInput
            v-model="form.title"
            label="عنوان (اختیاری)"
            placeholder="عنوان یادداشت..."
          />

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">متن یادداشت</label>
            <textarea
              v-model="form.content"
              rows="6"
              placeholder="متن خود را با **Markdown** بنویسید..."
              class="w-full px-4 py-3 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-colors resize-none"
              :class="contentError ? 'border-red-400 bg-red-50' : ''"
            ></textarea>
            <p v-if="contentError" class="mt-1 text-sm text-red-500">{{ contentError }}</p>
          </div>

          <!-- Switches -->
          <div class="space-y-3 pt-2">
            <div class="flex items-center justify-between">
              <span class="text-sm text-gray-700">ارسال به تلگرام</span>
              <button
                type="button"
                @click="form.send_to_telegram = !form.send_to_telegram"
                :class="form.send_to_telegram ? 'bg-indigo-600' : 'bg-gray-200'"
                class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none"
              >
                <span
                  :class="form.send_to_telegram ? 'translate-x-6' : 'translate-x-1'"
                  class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform"
                />
              </button>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-sm text-gray-700">ارسال به بله</span>
              <button
                type="button"
                @click="form.send_to_bale = !form.send_to_bale"
                :class="form.send_to_bale ? 'bg-indigo-600' : 'bg-gray-200'"
                class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none"
              >
                <span
                  :class="form.send_to_bale ? 'translate-x-6' : 'translate-x-1'"
                  class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform"
                />
              </button>
            </div>
          </div>

          <BaseButton
            type="submit"
            variant="primary"
            :disabled="!isFormValid"
            :loading="saving"
            class="mt-2"
          >
            {{ isEdit ? 'ویرایش' : 'ذخیره' }}
          </BaseButton>
        </form>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { reactive, ref, computed } from 'vue'
import BaseInput from '../ui/BaseInput.vue'
import BaseButton from '../ui/BaseButton.vue'
import { createNote, updateNote } from '../../api'
import { useToast } from '../../composables/useToast'

const props = defineProps({
  note: { type: Object, default: null }
})
const emit = defineEmits(['close', 'saved'])

const isEdit = computed(() => !!props.note?.id)

const form = reactive({
  title: props.note?.title || '',
  content: props.note?.content || '',
  send_to_telegram: props.note?.send_to_telegram ?? false,
  send_to_bale: props.note?.send_to_bale ?? false
})

const saving = ref(false)
const contentError = ref('')
const { showToast } = useToast()

const isFormValid = computed(() => form.content.trim().length > 0)

const handleSave = async () => {
  contentError.value = ''
  if (!isFormValid.value) {
    contentError.value = 'متن یادداشت نمی‌تواند خالی باشد'
    return
  }
  saving.value = true
  try {
    const payload = {
      title: form.title || null,
      content: form.content,
      send_to_telegram: form.send_to_telegram,
      send_to_bale: form.send_to_bale
    }
    if (isEdit.value) {
      await updateNote(props.note.id, payload)
      showToast('یادداشت ویرایش شد', 'success')
    } else {
      await createNote(payload)
      showToast('یادداشت جدید ایجاد شد', 'success')
    }
    emit('saved')
  } catch (err) {
    contentError.value = 'خطا در ذخیره‌سازی'
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.animate-slide-up {
  animation: slideUp 0.3s ease-out;
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