<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { fetchBookJourney } from '../api'
import type { BookJourneyResponse } from '../types'
import ShopEmptyState from '../components/ShopEmptyState.vue'

const route = useRoute()
const router = useRouter()
const code = ref(String(route.params.code || ''))
const journeyData = ref<BookJourneyResponse | null>(null)
const isLoading = ref(true)

onMounted(async () => {
  if (!code.value) {
    isLoading.value = false
    return
  }
  try {
    journeyData.value = await fetchBookJourney(code.value)
  } catch (err) {
    console.error('Failed to load book journey:', err)
  } finally {
    isLoading.value = false
  }
})
</script>

<template>
  <div class="max-w-2xl mx-auto px-4 py-6 space-y-5" dir="rtl">
    <!-- Back Header -->
    <div class="flex items-center justify-between">
      <button
        @click="router.back()"
        type="button"
        class="inline-flex items-center gap-1.5 text-xs text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-200 transition-colors cursor-pointer"
      >
        <span>←</span>
        <span>بازگشت به فروشگاه</span>
      </button>

      <span class="text-xs font-mono px-2 py-0.5 rounded bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 font-bold">
        {{ code }}
      </span>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="py-16 text-center text-xs text-zinc-400">
      در حال دریافت سفرنامه کتاب...
    </div>

    <!-- Content -->
    <div v-else-if="journeyData" class="space-y-6">
      <!-- Book Identity Header -->
      <div class="p-4 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 flex items-center justify-between gap-4">
        <div>
          <h2 class="text-base font-bold text-zinc-900 dark:text-zinc-100">
            {{ journeyData.book_title.title }}
          </h2>
          <p class="text-xs text-zinc-500 mt-0.5">
            اثر {{ journeyData.book_title.author }}
          </p>
        </div>

        <div class="text-center px-3 py-1.5 rounded-lg bg-zinc-50 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700">
          <span class="block text-sm font-bold text-zinc-900 dark:text-zinc-100">
            {{ journeyData.total_transfers }}
          </span>
          <span class="text-[10px] text-zinc-400">گردش ثبت‌شده</span>
        </div>
      </div>

      <!-- Timeline Stream -->
      <div v-if="journeyData.journey && journeyData.journey.length > 0" class="relative pr-6 border-r-2 border-zinc-200 dark:border-zinc-800 space-y-6">
        <div
          v-for="(event, idx) in journeyData.journey"
          :key="event.id"
          class="relative group"
        >
          <!-- Timeline Bullet -->
          <div class="absolute -right-[31px] top-1 size-3.5 rounded-full bg-white dark:bg-zinc-900 border-2 border-zinc-800 dark:border-zinc-200 group-hover:scale-125 transition-transform"></div>

          <!-- Event Card -->
          <div class="p-3.5 rounded-xl border border-zinc-100 dark:border-zinc-800 bg-zinc-50/80 dark:bg-zinc-900/40 space-y-2">
            <div class="flex items-center justify-between text-xs">
              <span class="font-bold text-zinc-800 dark:text-zinc-200">
                {{ event.from_display_name }} ← {{ event.to_display_name }}
              </span>
              <span class="text-[10px] text-zinc-400 font-mono">
                {{ new Date(event.date).toLocaleDateString('fa-IR') }}
              </span>
            </div>

            <!-- Notes or feedback -->
            <p v-if="event.donor_note" class="text-[11px] text-zinc-600 dark:text-zinc-400 italic bg-white dark:bg-zinc-800/60 p-2 rounded-lg border border-zinc-200/50 dark:border-zinc-700/50">
              «{{ event.donor_note }}»
            </p>

            <p v-if="event.recipient_note" class="text-[11px] text-zinc-600 dark:text-zinc-400 italic bg-white dark:bg-zinc-800/60 p-2 rounded-lg border border-zinc-200/50 dark:border-zinc-700/50">
              «{{ event.recipient_note }}»
            </p>

            <!-- Station note if applicable -->
            <div v-if="event.station_name" class="text-[10px] text-zinc-400 flex items-center gap-1">
              <span>🏛️</span>
              <span>تحویل در قفسه {{ event.station_name }} <span v-if="event.city_name">({{ event.city_name }})</span></span>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <ShopEmptyState
        v-else
        type="transfers"
        title="هنوز سفری برای این جلد ثبت نشده است"
        description="این کتاب به زودی اولین دست‌به‌دست شدن خود را تجربه خواهد کرد."
      />
    </div>

    <ShopEmptyState
      v-else
      type="books"
      title="کتاب مورد نظر یافت نشد"
      description="شناسه کتاب را مجدداً بررسی فرمایید."
    />
  </div>
</template>

