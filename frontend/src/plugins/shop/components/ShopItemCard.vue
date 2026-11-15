<script setup lang="ts">
import { computed } from 'vue'
import type { CatalogItem } from '../types'

const props = defineProps<{
  item: CatalogItem
}>()

const emit = defineEmits<{
  (e: 'select', item: CatalogItem): void
  (e: 'request-donation', item: CatalogItem): void
}>()

const isDonation = computed(() => props.item.deal_type === 'donation')

const formattedPrice = computed(() => {
  if (isDonation.value) {
    return 'اهدای رایگان'
  }
  const price = Number(props.item.effective_price || props.item.price || 0)
  return `${price.toLocaleString('fa-IR')} تومان`
})
</script>

<template>
  <div
    @click="emit('select', item)"
    class="group relative flex flex-col justify-between p-3.5 rounded-xl border border-zinc-200/80 dark:border-zinc-800/80 bg-white dark:bg-zinc-900/60 hover:border-zinc-400 dark:hover:border-zinc-700 transition-all duration-200 cursor-pointer shadow-xs"
  >
    <div class="flex gap-3">
      <!-- Thumbnail / Cover Image -->
      <div class="relative w-18 h-24 shrink-0 rounded-lg overflow-hidden bg-zinc-100 dark:bg-zinc-800/80 border border-zinc-200/60 dark:border-zinc-800 flex items-center justify-center text-zinc-400">
        <img
          v-if="item.cover_image"
          :src="item.cover_image"
          :alt="item.title"
          class="w-full h-full object-cover group-hover:scale-102 transition-transform duration-300"
          loading="lazy"
        />
        <!-- Clean Book Spine SVG Fallback -->
        <svg
          v-else
          viewBox="0 0 32 40"
          class="w-8 h-8 stroke-current fill-none stroke-[1.25] stroke-linecap-round stroke-linejoin-round"
        >
          <rect x="6" y="4" width="20" height="32" rx="2" />
          <line x1="11" y1="4" x2="11" y2="36" />
          <line x1="15" y1="12" x2="22" y2="12" class="opacity-60" />
          <line x1="15" y1="18" x2="20" y2="18" class="opacity-40" />
        </svg>
      </div>

      <!-- Info Column -->
      <div class="flex flex-col justify-between flex-1 min-w-0">
        <div>
          <!-- Badge Row: Distinct colored badge (Green for donation, Dark slate for sale) -->
          <div class="flex items-center gap-1.5 mb-1.5">
            <span
              v-if="isDonation"
              class="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-semibold bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-500/20"
            >
              اهدای رایگان
            </span>
            <span
              v-else
              class="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-semibold bg-zinc-100 dark:bg-zinc-800 text-zinc-900 dark:text-zinc-200 border border-zinc-300 dark:border-zinc-700"
            >
              فروشی
            </span>

            <span
              v-if="item.delivery_type === 'digital'"
              class="inline-flex items-center px-1.5 py-0.5 rounded-md text-[10px] font-medium text-zinc-500 bg-zinc-100 dark:bg-zinc-800/50"
            >
              الکترونیکی
            </span>
          </div>

          <!-- Title -->
          <h4 class="text-xs sm:text-sm font-semibold text-zinc-900 dark:text-zinc-100 line-clamp-2 leading-snug group-hover:text-zinc-600 dark:group-hover:text-zinc-300 transition-colors">
            {{ item.title }}
          </h4>
        </div>

        <!-- Meta row: Seller and Price -->
        <div class="mt-2 flex items-center justify-between text-[11px] pt-2 border-t border-zinc-100 dark:border-zinc-800/60">
          <span class="text-zinc-500 dark:text-zinc-400 truncate max-w-[120px]">
            {{ item.seller_name || 'کاربر تفاخر' }}
          </span>

          <span
            :class="[
              'font-semibold text-xs',
              isDonation
                ? 'text-emerald-600 dark:text-emerald-400 font-bold'
                : 'text-zinc-900 dark:text-zinc-100'
            ]"
          >
            {{ formattedPrice }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

