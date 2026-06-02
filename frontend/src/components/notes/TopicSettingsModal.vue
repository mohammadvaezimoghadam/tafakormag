<template>
  <Teleport to="body">
    <div class="fixed inset-0 z-50 flex items-end sm:items-center justify-center">
      <!-- Backdrop -->
      <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" @click="$emit('close')" />

      <!-- Panel -->
      <div class="relative w-full max-w-md bg-white rounded-t-3xl sm:rounded-3xl shadow-2xl p-6 max-h-[90vh] overflow-y-auto animate-slide-up z-10 text-right">
        <!-- Header -->
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-xl font-black text-gray-800">⚙️ تنظیمات اتصال پیام‌رسان‌ها</h2>
          <button @click="$emit('close')" class="text-gray-400 hover:text-gray-600 p-1 hover:bg-gray-50 rounded-full transition-colors">
            <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div class="space-y-6">
          <!-- هدر توضیحات -->
          <div class="bg-indigo-50/50 rounded-2xl p-4 border border-indigo-50 text-xs text-indigo-700 leading-relaxed">
            💡 با فعال‌سازی همگام‌سازی، پست‌های ارسالی شما در این تاپیک به صورت خودکار از طریق ربات‌های اختصاصی در گروه‌ها و کانال‌های انتخاب شده منتشر خواهند شد.
          </div>

          <!-- بخش تلگرام -->
          <div class="border-b border-gray-100 pb-5 space-y-4">
            <div class="flex items-center justify-between">
              <div class="flex items-center space-x-2 space-x-reverse">
                <span class="text-lg">🔹</span>
                <span class="text-sm font-extrabold text-gray-800">همگام‌سازی با تلگرام</span>
              </div>
              <!-- سوییچ تلگرام -->
              <button
                type="button"
                @click="toggleTelegram"
                :class="telegramActive ? 'bg-indigo-600' : 'bg-gray-200'"
                class="relative inline-flex h-6 w-11 shrink-0 items-center rounded-full transition-colors focus:outline-none shadow-sm"
              >
                <span
                  :class="telegramActive ? 'translate-x-6' : 'translate-x-1'"
                  class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform shadow"
                />
              </button>
            </div>

            <!-- لیست مقاصد تلگرام -->
            <Transition name="fade-height">
              <div v-if="telegramActive" class="space-y-2 pr-3 pt-2">
                <div v-if="loadingTg" class="text-xs text-gray-400 py-2">در حال بارگذاری کانال‌ها...</div>
                <div v-else-if="tgDestinations.length === 0" class="text-xs text-amber-600 bg-amber-50 rounded-xl p-3 border border-amber-50">
                  ⚠️ هیچ مقصد متصلی در تلگرام یافت نشد. ابتدا ربات خود را در تلگرام به گروه یا کانال عضو و مدیر کنید.
                </div>
                <div v-else class="space-y-2 max-h-40 overflow-y-auto pl-1">
                  <label
                    v-for="dest in tgDestinations"
                    :key="dest.id"
                    class="flex items-center space-x-3 space-x-reverse bg-gray-50/70 p-3 rounded-xl border border-gray-100 hover:bg-gray-50 cursor-pointer text-xs transition-colors"
                  >
                    <input
                      type="checkbox"
                      :value="dest.id"
                      v-model="selectedTgConnections"
                      class="w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                    />
                    <div class="flex-1 truncate">
                      <span class="font-bold text-gray-700 block">{{ dest.label }}</span>
                      <span class="text-[10px] text-gray-400 block mt-0.5 dir-ltr text-right">{{ dest.chat_id }}</span>
                    </div>
                  </label>
                </div>
              </div>
            </Transition>
          </div>

          <!-- بخش بله -->
          <div class="pb-2 space-y-4">
            <div class="flex items-center justify-between">
              <div class="flex items-center space-x-2 space-x-reverse">
                <span class="text-lg">🟢</span>
                <span class="text-sm font-extrabold text-gray-800">همگام‌سازی با بله</span>
              </div>
              <!-- سوییچ بله -->
              <button
                type="button"
                @click="toggleBale"
                :class="baleActive ? 'bg-indigo-600' : 'bg-gray-200'"
                class="relative inline-flex h-6 w-11 shrink-0 items-center rounded-full transition-colors focus:outline-none shadow-sm"
              >
                <span
                  :class="baleActive ? 'translate-x-6' : 'translate-x-1'"
                  class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform shadow"
                />
              </button>
            </div>

            <!-- لیست مقاصد بله -->
            <Transition name="fade-height">
              <div v-if="baleActive" class="space-y-2 pr-3 pt-2">
                <div v-if="loadingBale" class="text-xs text-gray-400 py-2">در حال بارگذاری کانال‌ها...</div>
                <div v-else-if="baleDestinations.length === 0" class="text-xs text-amber-600 bg-amber-50 rounded-xl p-3 border border-amber-50">
                  ⚠️ هیچ مقصد متصلی در بله یافت نشد. ابتدا ربات خود را در بله به گروه یا کانال عضو و مدیر کنید.
                </div>
                <div v-else class="space-y-2 max-h-40 overflow-y-auto pl-1">
                  <label
                    v-for="dest in baleDestinations"
                    :key="dest.id"
                    class="flex items-center space-x-3 space-x-reverse bg-gray-50/70 p-3 rounded-xl border border-gray-100 hover:bg-gray-50 cursor-pointer text-xs transition-colors"
                  >
                    <input
                      type="checkbox"
                      :value="dest.id"
                      v-model="selectedBaleConnections"
                      class="w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                    />
                    <div class="flex-1 truncate">
                      <span class="font-bold text-gray-700 block">{{ dest.label }}</span>
                      <span class="text-[10px] text-gray-400 block mt-0.5 dir-ltr text-right">{{ dest.chat_id }}</span>
                    </div>
                  </label>
                </div>
              </div>
            </Transition>
          </div>

          <!-- دکمه ذخیره -->
          <BaseButton
            @click="handleSave"
            variant="primary"
            :loading="saving"
            class="w-full rounded-2xl py-3 font-extrabold shadow-lg"
          >
            ذخیره تنظیمات اتصالات
          </BaseButton>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import BaseButton from '../ui/BaseButton.vue'
import { fetchDestinations, updateTopic } from '../../api'
import { useToast } from '../../composables/useToast'

const props = defineProps({
  topic: { type: Object, required: true }
})
const emit = defineEmits(['close', 'updated'])

const telegramActive = ref(props.topic.telegram_bot_active)
const baleActive = ref(props.topic.bale_bot_active)

const getIds = (connections) => {
  if (!connections) return []
  return connections.map(c => typeof c === 'object' && c !== null ? c.id : c)
}
const selectedTgConnections = ref(getIds(props.topic.telegram_connections))
const selectedBaleConnections = ref(getIds(props.topic.bale_connections))

const tgDestinations = ref([])
const baleDestinations = ref([])

const loadingTg = ref(false)
const loadingBale = ref(false)
const saving = ref(false)

const { showToast } = useToast()

const toggleTelegram = () => {
  telegramActive.value = !telegramActive.value
  if (telegramActive.value && tgDestinations.value.length === 0) {
    loadTgDestinations()
  }
}

const toggleBale = () => {
  baleActive.value = !baleActive.value
  if (baleActive.value && baleDestinations.value.length === 0) {
    loadBaleDestinations()
  }
}

const loadTgDestinations = async () => {
  loadingTg.value = true
  try {
    const res = await fetchDestinations('telegram')
    tgDestinations.value = res.data ?? []
  } catch (err) {
    // خطا توسط اینترسپتور مدیریت می‌شود
  } finally {
    loadingTg.value = false
  }
}

const loadBaleDestinations = async () => {
  loadingBale.value = true
  try {
    const res = await fetchDestinations('bale')
    baleDestinations.value = res.data ?? []
  } catch (err) {
    // خطا توسط اینترسپتور مدیریت می‌شود
  } finally {
    loadingBale.value = false
  }
}

const handleSave = async () => {
  saving.value = true
  try {
    const payload = {
      telegram_bot_active: telegramActive.value,
      bale_bot_active: baleActive.value,
      telegram_connections: selectedTgConnections.value,
      bale_connections: selectedBaleConnections.value
    }
    
    await updateTopic(props.topic.id, payload)
    showToast('تنظیمات اتصالات پیام‌رسان با موفقیت ذخیره شد', 'success')
    emit('updated')
  } catch (err) {
    showToast('خطا در ذخیره‌سازی اتصالات', 'error')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  if (telegramActive.value) {
    loadTgDestinations()
  }
  if (baleActive.value) {
    loadBaleDestinations()
  }
})
</script>

<style scoped>
.animate-slide-up {
  animation: slideUp 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}

.fade-height-enter-active,
.fade-height-leave-active {
  transition: all 0.25s ease-out;
  max-height: 200px;
  opacity: 1;
}

.fade-height-enter-from,
.fade-height-leave-to {
  max-height: 0;
  opacity: 0;
  overflow: hidden;
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
