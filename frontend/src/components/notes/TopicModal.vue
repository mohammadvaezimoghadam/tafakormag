<template>
  <Teleport to="body">
    <div class="fixed inset-0 z-50 flex items-end sm:items-center justify-center">
      <!-- Backdrop -->
      <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" @click="$emit('close')" />
      
      <!-- Panel -->
      <div class="relative w-full max-w-md bg-white rounded-t-3xl sm:rounded-3xl shadow-2xl p-6 max-h-[90vh] overflow-y-auto animate-slide-up z-10 text-right">
        <!-- Header -->
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-base font-extrabold text-gray-800">{{ isEdit ? 'ویرایش تاپیک' : 'ساخت تاپیک جدید' }}</h2>
          <button @click="$emit('close')" class="text-gray-400 hover:text-gray-600 p-1 hover:bg-gray-50 rounded-full transition-colors">
            <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form @submit.prevent="handleSave" class="space-y-5">
          <!-- نام تاپیک -->
          <BaseInput
            v-model="form.name"
            label="نام تاپیک"
            placeholder="نام تاپیک خود را بنویسید..."
            class="text-right"
            required
            :class="nameError ? 'border-red-400' : ''"
          />
          <p v-if="nameError" class="text-xs text-red-500 mt-1">{{ nameError }}</p>

          <!-- دیسکریپشن / خلاصه -->
          <div>
            <label class="block text-sm font-extrabold text-gray-700 mb-1.5">توضیحات کوتاه</label>
            <textarea
              v-model="form.description"
              rows="3"
              placeholder="توضیح کوتاهی درباره موضوع این تاپیک بنویسید..."
              class="w-full px-4 py-3 border border-gray-200 rounded-2xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-right transition-all resize-none shadow-inner"
            ></textarea>
          </div>

          <!-- آپلود تصویر کاور -->
          <div>
            <label class="block text-sm font-extrabold text-gray-700 mb-1.5">تصویر کاور تاپیک</label>
            <div class="flex items-center space-x-3 space-x-reverse">
              <div
                v-if="imagePreview || currentImageUrl"
                class="w-16 h-16 rounded-2xl border border-gray-200 overflow-hidden shrink-0 shadow-sm"
              >
                <img :src="imagePreview || currentImageUrl" class="w-full h-full object-cover" />
              </div>
              <div
                v-else
                class="w-16 h-16 rounded-2xl bg-indigo-50 text-indigo-500 flex items-center justify-center shrink-0 font-black text-xl shadow-inner border border-indigo-100"
              >
                T
              </div>
              <label
                class="flex-1 border-2 border-dashed border-gray-200 rounded-2xl p-4 flex flex-col items-center justify-center cursor-pointer hover:border-indigo-500 hover:bg-indigo-50/10 transition-all text-xs text-gray-500"
              >
                <svg class="w-6 h-6 text-gray-400 mb-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                <span>انتخاب تصویر کاور</span>
                <input type="file" ref="fileInput" @change="handleFileChange" accept="image/*" class="hidden" />
              </label>
            </div>
          </div>

          <!-- دکمه ثبت -->
          <BaseButton
            type="submit"
            variant="primary"
            :disabled="!isFormValid"
            :loading="saving"
            class="mt-2 shadow-md"
          >
            {{ isEdit ? 'ذخیره تغییرات' : 'ایجاد تاپیک' }}
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
import { createTopic, updateTopic } from '../../api'
import { useToast } from '../../composables/useToast'

const props = defineProps({
  topic: { type: Object, default: null }
})
const emit = defineEmits(['close', 'saved'])

const isEdit = computed(() => !!props.topic?.id)

const form = reactive({
  name: props.topic?.name || '',
  description: props.topic?.description || ''
})

const fileInput = ref(null)
const selectedFile = ref(null)
const imagePreview = ref('')
const saving = ref(false)
const nameError = ref('')

const { showToast } = useToast()

const currentImageUrl = computed(() => {
  if (!props.topic?.image) return ''
  const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
  if (props.topic.image.startsWith('http://') || props.topic.image.startsWith('https://')) {
    return props.topic.image
  }
  return `${apiBase}${props.topic.image}`
})

const isFormValid = computed(() => form.name.trim().length > 0)

const handleFileChange = (e) => {
  const file = e.target.files[0]
  if (!file) return
  selectedFile.value = file
  
  // ساخت پیش‌نمایش تصویر
  const reader = new FileReader()
  reader.onload = (event) => {
    imagePreview.value = event.target.result
  }
  reader.readAsDataURL(file)
}

const handleSave = async () => {
  nameError.value = ''
  if (!isFormValid.value) {
    nameError.value = 'نام تاپیک نمی‌تواند خالی باشد'
    return
  }
  saving.value = true
  
  try {
    const formData = new FormData()
    formData.append('name', form.name)
    if (form.description) {
      formData.append('description', form.description)
    }
    if (selectedFile.value) {
      formData.append('image', selectedFile.value)
    }

    if (isEdit.value) {
      await updateTopic(props.topic.id, formData)
      showToast('تاپیک با موفقیت به‌روزرسانی شد', 'success')
    } else {
      await createTopic(formData)
      showToast('تاپیک جدید با موفقیت ایجاد شد', 'success')
    }
    emit('saved')
  } catch (err) {
    nameError.value = 'خطا در ذخیره‌سازی تاپیک'
  } finally {
    saving.value = false
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
