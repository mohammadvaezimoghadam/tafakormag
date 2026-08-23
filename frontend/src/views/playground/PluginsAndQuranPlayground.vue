<template>
  <div class="min-h-screen bg-zinc-50 dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100 p-4 sm:p-8 space-y-8 font-sans">
    
    <!-- Top Header -->
    <div class="max-w-6xl mx-auto flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-zinc-200 dark:border-zinc-800 pb-6">
      <div class="space-y-1">
        <div class="inline-flex items-center gap-2 px-3 py-1 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 rounded-full text-xs font-bold">
          <span>🧪 محیط آزمایشی (Playground)</span>
        </div>
        <h1 class="text-2xl sm:text-3xl font-black">پلی‌گراند سیستم افزونه‌ها و مینی‌اپلیکیشن قرآن</h1>
        <p class="text-xs sm:text-sm text-zinc-500">تست بلادرنگ رابط‌های کاربری مارکت‌پلیس، ریدر قرآن، سرچ هوشمند و ادغام کامپوزر</p>
      </div>

      <div class="flex items-center gap-2">
        <router-link
          to="/playground"
          class="px-4 py-2 bg-zinc-200 dark:bg-zinc-800 hover:bg-zinc-300 dark:hover:bg-zinc-700 rounded-xl text-xs font-bold transition-colors"
        >
          ← بازگشت به پلی‌گراند اصلی
        </router-link>
      </div>
    </div>

    <!-- Playground Tabs -->
    <div class="max-w-6xl mx-auto space-y-6">
      <div class="flex flex-wrap items-center gap-2 p-1.5 bg-zinc-200/70 dark:bg-zinc-900 rounded-2xl">
        <button
          v-for="t in tabs"
          :key="t.id"
          @click="activeTab = t.id"
          :class="[
            'px-4 py-2.5 rounded-xl text-xs font-bold transition-all flex items-center gap-2',
            activeTab === t.id
              ? 'bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 shadow-sm'
              : 'text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-200'
          ]"
        >
          <span>{{ t.icon }}</span>
          <span>{{ t.label }}</span>
        </button>
      </div>

      <!-- Tab 1: Composer & Verse Picker Integration -->
      <div v-if="activeTab === 'composer'" class="space-y-6 animate-in fade-in duration-200">
        <div class="p-6 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-3xl space-y-4">
          <div>
            <h3 class="font-bold text-base">تست درج آیه در ویرایشگر پیام (Composer Integration)</h3>
            <p class="text-xs text-zinc-500 mt-1">
              روی دکمه «+» در نوار پیام کلیک کنید و گزینه «📖 درج آیه قرآن» را انتخاب نمایید تا نحوه تولید و درج خودکار مارک‌داون را مشاهده کنید.
            </p>
          </div>

          <div class="max-w-xl mx-auto pt-4">
            <TopicMessageInput
              placeholder="پیام خود را بنویسید یا آیه قرآن درج کنید..."
              @send="handleMessageSend"
            />
          </div>

          <div v-if="sentMessages.length > 0" class="pt-6 border-t border-zinc-100 dark:border-zinc-800 space-y-3">
            <h4 class="text-xs font-bold text-zinc-500">پیام‌های ارسال‌شده در محیط آزمایشی:</h4>
            <div
              v-for="(msg, idx) in sentMessages"
              :key="idx"
              class="p-4 bg-zinc-50 dark:bg-zinc-800/50 border border-zinc-200 dark:border-zinc-700/50 rounded-2xl space-y-2"
            >
              <pre class="text-xs font-mono text-emerald-600 dark:text-emerald-400 whitespace-pre-wrap">{{ msg }}</pre>
            </div>
          </div>
        </div>
      </div>

      <!-- Tab 2: Standalone Quran Verse Picker Modal -->
      <div v-if="activeTab === 'picker'" class="space-y-6 animate-in fade-in duration-200">
        <div class="p-6 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-3xl space-y-4">
          <div class="flex items-center justify-between">
            <div>
              <h3 class="font-bold text-base">دیالوگ مستقیم انتخاب آیه (Verse Picker Modal)</h3>
              <p class="text-xs text-zinc-500 mt-1">باز کردن مستقیم دیالوگ و تست فرمت‌دهی خروجی</p>
            </div>
            <button
              @click="showPickerModal = true"
              class="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold shadow-lg shadow-emerald-600/20 transition-all flex items-center gap-2"
            >
              <span>📖</span>
              <span>باز کردن دیالوگ انتخاب آیه</span>
            </button>
          </div>

          <div v-if="pickedMarkdown" class="p-4 bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-500/20 rounded-2xl space-y-2">
            <span class="text-xs font-bold text-emerald-700 dark:text-emerald-400">آخرین مارک‌داون تولید شده:</span>
            <pre class="text-xs font-mono text-zinc-800 dark:text-zinc-200 whitespace-pre-wrap">{{ pickedMarkdown }}</pre>
          </div>

          <QuranVersePickerDialog
            v-if="showPickerModal"
            @insert="handlePickerInsert"
            @close="showPickerModal = false"
          />
        </div>
      </div>

      <!-- Tab 3: Marketplace UI -->
      <div v-if="activeTab === 'marketplace'" class="space-y-6 animate-in fade-in duration-200">
        <div class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-3xl p-6 overflow-hidden">
          <MarketplaceView />
        </div>
      </div>

      <!-- Tab 4: Quran Reader Mini-App -->
      <div v-if="activeTab === 'quran'" class="space-y-6 animate-in fade-in duration-200">
        <div class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-3xl p-6 overflow-hidden">
          <QuranSurahListView />
        </div>
      </div>

      <!-- Tab 5: Quran Smart Search Engine -->
      <div v-if="activeTab === 'search'" class="space-y-6 animate-in fade-in duration-200">
        <div class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-3xl p-6 overflow-hidden">
          <QuranSearchView />
        </div>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import TopicMessageInput from '@/components/TopicMessageInput.vue'
import QuranVersePickerDialog from '@/plugins/quran/components/QuranVersePickerDialog.vue'
import MarketplaceView from '@/views/MarketplaceView.vue'
import QuranSurahListView from '@/plugins/quran/views/QuranSurahListView.vue'
import QuranSearchView from '@/plugins/quran/views/QuranSearchView.vue'

const activeTab = ref('composer')
const showPickerModal = ref(false)
const pickedMarkdown = ref('')
const sentMessages = ref<string[]>([])

const tabs = [
  { id: 'composer', label: 'تست درج در کامپوزر', icon: '✍️' },
  { id: 'picker', label: 'دیالوگ انتخاب آیه', icon: '📖' },
  { id: 'marketplace', label: 'مارکت‌پلیس افزونه‌ها', icon: '🧩' },
  { id: 'quran', label: 'مینی‌اپ و ریدر قرآن', icon: '🕌' },
  { id: 'search', label: 'موتور جستجوی قرآن', icon: '🔍' },
]

const handlePickerInsert = (markdown: string) => {
  pickedMarkdown.value = markdown
  showPickerModal.value = false
}

const handleMessageSend = (msg: { text: string }) => {
  sentMessages.value.unshift(msg.text)
}
</script>
