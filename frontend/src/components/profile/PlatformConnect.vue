<template>
  <div class="p-5 bg-white rounded-2xl shadow-sm border border-gray-100 space-y-4 transition-all duration-300 hover:shadow-md">
    <!-- بخش سربرگ کامپوننت -->
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-2">
        <span v-if="platform === 'telegram'" class="text-2xl">✈️</span>
        <span v-else class="text-2xl">💬</span>
        <span class="font-bold text-gray-800 capitalize text-lg">
          ربات اختصاصی {{ platform === 'telegram' ? 'تلگرام' : 'بله' }}
        </span>
      </div>

      <!-- چیپس تلویند نمایش وضعیت اتصال زنده -->
      <span
        v-if="connected && !isEditing"
        class="px-3 py-1 bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs font-semibold rounded-full flex items-center gap-1.5 animate-fade-in"
      >
        <span class="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
        {{ botUsername || 'متصل' }}
      </span>
      <span
        v-else-if="!connected"
        class="px-3 py-1 bg-amber-50 text-amber-700 border border-amber-200 text-xs font-semibold rounded-full flex items-center gap-1.5"
      >
        <span class="h-2 w-2 rounded-full bg-amber-400"></span>
        نامتصل
      </span>
    </div>

    <!-- راهنمای ساخت ربات اختصاصی -->
    <p class="text-sm text-gray-500 leading-relaxed" v-if="!connected || isEditing">
      برای انتشار خودکار یادداشت‌ها، ابتدا در BotFather پیام‌رسان {{ platform === 'telegram' ? 'تلگرام' : 'بله' }} یک ربات اختصاصی بسازید و توکن API آن را در کادر زیر وارد کنید.
    </p>

    <!-- لایه فرم اتصال یا ویرایش توکن -->
    <Transition name="fade" mode="out-in">
      <div v-if="!connected || isEditing" class="space-y-3" :key="'form'">
        <div class="flex flex-col gap-1.5">
          <label class="text-xs font-semibold text-gray-500">توکن API ربات اختصاصی:</label>
          <input
            v-model="token"
            type="text"
            placeholder="مثال: 123456:ABC-DEF1234ghIkl-zyx"
            class="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all duration-200"
            :disabled="loading"
          />
        </div>
        
        <div class="flex items-center gap-2">
          <BaseButton
            @click="handleSave"
            :loading="loading"
            variant="primary"
            size="sm"
            class="flex-1"
            :disabled="!token.trim()"
          >
            {{ isEditing ? 'ذخیره تغییرات' : 'ثبت و اتصال ربات' }}
          </BaseButton>
          
          <BaseButton
            v-if="isEditing"
            @click="cancelEdit"
            variant="outline"
            size="sm"
            :disabled="loading"
          >
            انصراف
          </BaseButton>
        </div>
      </div>

      <!-- لایه نمایش وضعیت متصل -->
      <div v-else class="space-y-3" :key="'status'">
        <div class="p-3 bg-gray-50 rounded-xl text-sm border border-gray-100 flex flex-col gap-1">
          <div class="flex justify-between items-center text-xs text-gray-400">
            <span>آدرس ربات شما:</span>
            <a 
              :href="platform === 'telegram' ? `https://t.me/${botUsername?.replace('@','')}` : `https://ble.ir/${botUsername?.replace('@','')}`" 
              target="_blank" 
              class="text-indigo-600 hover:underline font-semibold"
            >
              باز کردن چت ربات ↗
            </a>
          </div>
          <span class="font-mono text-gray-700 font-semibold break-all text-center py-1.5">
            {{ botUsername }}
          </span>
        </div>

        <div class="flex items-center gap-2">
          <!-- دکمه ویرایش مستقیم توکن -->
          <BaseButton
            @click="isEditing = true"
            variant="outline"
            size="sm"
            class="flex-1 text-indigo-600 border-indigo-200 hover:bg-indigo-50"
          >
            🔧 ویرایش توکن
          </BaseButton>

          <!-- دکمه قطع اتصال ربات -->
          <BaseButton
            @click="handleDisconnect"
            :loading="disconnectLoading"
            variant="danger"
            size="sm"
            class="flex-1"
          >
            🔌 قطع اتصال
          </BaseButton>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import BaseButton from '../ui/BaseButton.vue'
import { updateCustomBot } from '../../api'
import { useToast } from '../../composables/useToast'

const props = defineProps({
  platform: { type: String, required: true },
  connected: { type: Boolean, default: false },
  botUsername: { type: String, default: '' }
})

const emit = defineEmits(['updated'])

const { showToast } = useToast()
const token = ref('')
const loading = ref(false)
const disconnectLoading = ref(false)
const isEditing = ref(false)

const handleSave = async () => {
  if (!token.value.trim()) return
  loading.value = true
  try {
    const res = await updateCustomBot(props.platform, token.value.trim())
    if (res.data?.success) {
      showToast(res.data.message || 'ربات اختصاصی با موفقیت متصل شد.', 'success')
      token.value = ''
      isEditing.value = false
      emit('updated')
    }
  } catch (err) {
    // خطا توسط اینترسپتور نمایش داده می‌شود
  } finally {
    loading.value = false
  }
}

const handleDisconnect = async () => {
  if (!window.confirm(`آیا مطمئن هستید که می‌خواهید ربات اختصاصی ${props.platform === 'telegram' ? 'تلگرام' : 'بله'} را قطع اتصال کنید؟`)) return
  disconnectLoading.value = true
  try {
    const res = await updateCustomBot(props.platform, '')
    if (res.data?.success) {
      showToast('ربات اختصاصی با موفقیت قطع اتصال شد.', 'success')
      isEditing.value = false
      emit('updated')
    }
  } catch (err) {
    // خطا توسط اینترسپتور مدیریت می‌شود
  } finally {
    disconnectLoading.value = false
  }
}

const cancelEdit = () => {
  token.value = ''
  isEditing.value = false
}
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: all 0.25s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(4px);
}
</style>