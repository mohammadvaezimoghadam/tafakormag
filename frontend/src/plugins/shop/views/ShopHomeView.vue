<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  fetchCatalogItems,
  fetchBookStations,
  fetchMyHeldBooks,
  registerBookTitle,
  registerPhysicalCopy,
} from '../api'
import type { CatalogItem, BookStationItem, PhysicalCopyItem } from '../types'
import ShopItemCard from '../components/ShopItemCard.vue'
import ShopEmptyState from '../components/ShopEmptyState.vue'
import HandoverDialog from '../components/HandoverDialog.vue'
import { useLanguageStore } from '@/stores/languageStore'
import { useToastStore } from '@/stores/toastStore'

const router = useRouter()
const languageStore = useLanguageStore()
const toastStore = useToastStore()

// State
const searchQuery = ref('')
const activeFilter = ref<'all' | 'donation' | 'sale' | 'stations'>('all')
const items = ref<CatalogItem[]>([])
const stations = ref<BookStationItem[]>([])
const heldBooks = ref<PhysicalCopyItem[]>([])
const isLoading = ref(false)

// Modals
const isHandoverOpen = ref(false)
const isRegisterOpen = ref(false)
const registerForm = ref({
  title: '',
  author: '',
  publisher: '',
  condition: 'good',
  privacy: 'first_name_only',
})
const isRegistering = ref(false)

let debounceTimer: any = null

const loadData = async () => {
  isLoading.value = true
  try {
    if (activeFilter.value === 'stations') {
      stations.value = await fetchBookStations()
    } else {
      const dealTypeParam = activeFilter.value === 'all' ? undefined : activeFilter.value
      items.value = await fetchCatalogItems({
        search: searchQuery.value.trim() || undefined,
        deal_type: dealTypeParam as any,
      })
    }
  } catch (err) {
    console.error('Failed to load shop items:', err)
  } finally {
    isLoading.value = false
  }
}

watch(activeFilter, () => {
  loadData()
})

watch(searchQuery, () => {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    loadData()
  }, 300)
})

onMounted(() => {
  loadData()
})

const handleItemSelect = (item: CatalogItem) => {
  // If user clicks, could open detail or trigger action
}

const handleViewJourney = (code: string) => {
  router.push(`/apps/shop/copy/${code}`)
}

const submitNewBook = async () => {
  if (!registerForm.value.title.trim() || !registerForm.value.author.trim()) {
    toastStore.showToast('عنوان و نام نویسنده الزامی است.', 'error')
    return
  }
  isRegistering.value = true
  try {
    const bookTitle = await registerBookTitle({
      title: registerForm.value.title.trim(),
      author: registerForm.value.author.trim(),
      publisher: registerForm.value.publisher.trim(),
    })
    const copy = await registerPhysicalCopy({
      book_title_id: bookTitle.id,
      condition: registerForm.value.condition,
      privacy: registerForm.value.privacy,
    })
    toastStore.showToast(`کتاب با شناسه ${copy.short_code} در چرخه گردش ثبت شد.`, 'success')
    isRegisterOpen.value = false
    registerForm.value = { title: '', author: '', publisher: '', condition: 'good', privacy: 'first_name_only' }
    loadData()
  } catch (err: any) {
    const msg = err.response?.data?.detail || 'خطا در ثبت کتاب.'
    toastStore.showToast(msg, 'error')
  } finally {
    isRegistering.value = false
  }
}
</script>

<template>
  <div class="max-w-4xl mx-auto px-4 py-6 space-y-5" dir="rtl">
    
    <!-- Sophisticated Dark / Charcoal Hero Banner -->
    <div class="bg-zinc-950 text-white border border-zinc-800 rounded-2xl p-5 sm:p-6 shadow-xl flex flex-col sm:flex-row sm:items-center justify-between gap-4 select-none">
      <div class="space-y-1">
        <div class="inline-flex items-center gap-1.5 px-2.5 py-0.5 bg-zinc-800/80 rounded-md text-[11px] font-medium text-zinc-300">
          <span>🛍️</span>
          <span>فروشگاه و گردش کتاب تفاخر</span>
        </div>
        <h1 class="text-xl sm:text-2xl font-bold tracking-tight text-zinc-100">
          بازارچه کتاب و اندیشه
        </h1>
        <p class="text-xs text-zinc-400 max-w-md">
          اهدای رایگان، خرید و فروش کتاب دست دوم و انتقال حضوری با بارکد اختصاصی
        </p>
      </div>

      <!-- Quick Action Buttons -->
      <div class="flex items-center gap-2 shrink-0">
        <button
          @click="isHandoverOpen = true"
          type="button"
          class="px-3.5 py-2 rounded-xl bg-zinc-100 hover:bg-white text-zinc-900 text-xs font-bold transition-all shadow-xs cursor-pointer flex items-center gap-1.5"
        >
          <span>📷</span>
          <span>اسکن / دریافت کتاب</span>
        </button>

        <button
          @click="isRegisterOpen = true"
          type="button"
          class="px-3.5 py-2 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs font-semibold border border-zinc-700 transition-all cursor-pointer flex items-center gap-1.5"
        >
          <span>+</span>
          <span>ثبت کتاب</span>
        </button>
      </div>
    </div>

    <!-- Search and Filter Bar -->
    <div class="space-y-3">
      <!-- Search Input -->
      <div class="relative">
        <input
          v-model="searchQuery"
          type="search"
          placeholder="جستجوی عنوان کتاب، نویسنده یا ناشر (مثال: گلشن راز)..."
          class="w-full px-4 py-2.5 text-xs sm:text-sm rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 focus:outline-hidden focus:border-zinc-500 dark:focus:border-zinc-600 transition-colors shadow-2xs"
        />
      </div>

      <!-- Filter Tabs -->
      <div class="flex items-center gap-1.5 p-1 bg-zinc-100/80 dark:bg-zinc-900/80 border border-zinc-200/60 dark:border-zinc-800 rounded-xl overflow-x-auto select-none">
        <button
          @click="activeFilter = 'all'"
          type="button"
          :class="[
            'px-3 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer shrink-0',
            activeFilter === 'all'
              ? 'bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 font-bold shadow-xs'
              : 'text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-200'
          ]"
        >
          همه کتب و اقلام
        </button>

        <button
          @click="activeFilter = 'donation'"
          type="button"
          :class="[
            'px-3 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer shrink-0 flex items-center gap-1',
            activeFilter === 'donation'
              ? 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-400 font-bold shadow-xs'
              : 'text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-200'
          ]"
        >
          <span class="size-1.5 rounded-full bg-emerald-500 inline-block"></span>
          <span>اهدای رایگان</span>
        </button>

        <button
          @click="activeFilter = 'sale'"
          type="button"
          :class="[
            'px-3 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer shrink-0',
            activeFilter === 'sale'
              ? 'bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 font-bold shadow-xs'
              : 'text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-200'
          ]"
        >
          فروشی
        </button>

        <button
          @click="activeFilter = 'stations'"
          type="button"
          :class="[
            'px-3 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer shrink-0 flex items-center gap-1',
            activeFilter === 'stations'
              ? 'bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 font-bold shadow-xs'
              : 'text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-200'
          ]"
        >
          <span>🏛️</span>
          <span>قفسه‌های تفاخر</span>
        </button>
      </div>
    </div>

    <!-- Feed Content -->
    <!-- Loading State -->
    <div v-if="isLoading" class="py-16 text-center text-xs text-zinc-400">
      در حال دریافت اطلاعات...
    </div>

    <!-- Case A: Catalog Items Grid (Side-by-side feed) -->
    <div v-else-if="activeFilter !== 'stations'">
      <div v-if="items.length > 0" class="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <ShopItemCard
          v-for="item in items"
          :key="item.id"
          :item="item"
          @select="handleItemSelect"
        />
      </div>

      <!-- Empty State -->
      <ShopEmptyState
        v-else
        :type="searchQuery ? 'search' : 'books'"
        :title="searchQuery ? 'کتابی با این نام یا مشخصات یافت نشد' : 'هنوز کتابی در این بخش ثبت نشده است'"
        action-text="ثبت کتاب جدید"
        @action="isRegisterOpen = true"
      />
    </div>

    <!-- Case B: Stations / Kiosks List -->
    <div v-else class="space-y-3">
      <div v-if="stations.length > 0" class="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div
          v-for="st in stations"
          :key="st.id"
          class="p-4 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 flex flex-col justify-between gap-3 shadow-xs"
        >
          <div>
            <div class="flex items-center justify-between mb-1">
              <span class="text-xs font-bold text-zinc-900 dark:text-zinc-100">
                {{ st.name }}
              </span>
              <span class="text-[10px] px-2 py-0.5 rounded-md bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 font-mono">
                {{ st.current_books_count }} / {{ st.capacity }} جلد
              </span>
            </div>
            <p class="text-[11px] text-zinc-500 leading-relaxed">
              {{ st.address_text }} <span v-if="st.city_name">({{ st.city_name }})</span>
            </p>
          </div>

          <div class="pt-2 border-t border-zinc-100 dark:border-zinc-800 flex items-center justify-between text-[11px]">
            <span class="text-emerald-600 dark:text-emerald-400 font-medium">
              آماده پذیرش و امانت
            </span>
            <button
              @click="isHandoverOpen = true"
              type="button"
              class="text-zinc-700 dark:text-zinc-300 hover:underline cursor-pointer"
            >
              ثبت تحویل یا برداشت
            </button>
          </div>
        </div>
      </div>

      <ShopEmptyState
        v-else
        type="stations"
        title="ایستگاهی ثبت نشده است"
        description="به‌زودی قفسه‌های جدید تفاخر در این منطقه افزوده خواهد شد."
      />
    </div>

    <!-- Handover Dialog Modal -->
    <HandoverDialog
      v-model:open="isHandoverOpen"
      @view-journey="handleViewJourney"
      @success="loadData"
    />

    <!-- Register Book Modal -->
    <div v-if="isRegisterOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs select-none">
      <div class="w-full max-w-md bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-5 shadow-2xl flex flex-col gap-4 text-zinc-900 dark:text-zinc-100">
        <div class="flex items-center justify-between pb-3 border-b border-zinc-100 dark:border-zinc-800">
          <h3 class="text-sm font-bold">معرفی و ثبت کتاب در شبکه گردش</h3>
          <button @click="isRegisterOpen = false" class="text-zinc-400 hover:text-zinc-600 text-sm cursor-pointer">✕</button>
        </div>

        <div class="space-y-3 text-xs">
          <div>
            <label class="block font-medium mb-1 text-zinc-700 dark:text-zinc-300">عنوان کتاب *</label>
            <input v-model="registerForm.title" placeholder="مثال: گلشن راز" class="w-full px-3 py-2 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800/50" />
          </div>

          <div>
            <label class="block font-medium mb-1 text-zinc-700 dark:text-zinc-300">نویسنده / پدیدآور *</label>
            <input v-model="registerForm.author" placeholder="مثال: شیخ محمود شبستری" class="w-full px-3 py-2 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800/50" />
          </div>

          <div>
            <label class="block font-medium mb-1 text-zinc-700 dark:text-zinc-300">ناشر (اختیاری)</label>
            <input v-model="registerForm.publisher" placeholder="مثال: انتشارات زوار" class="w-full px-3 py-2 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800/50" />
          </div>

          <div>
            <label class="block font-medium mb-1 text-zinc-700 dark:text-zinc-300">کیفیت ظاهری نسخه</label>
            <select v-model="registerForm.condition" class="w-full px-3 py-2 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800/50">
              <option value="like_new">در حد نو</option>
              <option value="good">دست دوم سالم</option>
              <option value="fair">خوانده‌شده با حاشیه‌نویسی</option>
            </select>
          </div>
        </div>

        <div class="pt-2 flex items-center justify-end gap-2">
          <button @click="isRegisterOpen = false" type="button" class="px-3 py-2 text-xs text-zinc-500 hover:text-zinc-700 cursor-pointer">انصراف</button>
          <button @click="submitNewBook" :disabled="isRegistering" type="button" class="px-4 py-2 rounded-lg bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 text-xs font-bold hover:bg-zinc-800 transition-colors cursor-pointer">
            {{ isRegistering ? 'در حال ثبت...' : 'ثبت و دریافت شناسه' }}
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

