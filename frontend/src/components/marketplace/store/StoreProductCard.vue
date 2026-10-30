<script setup lang="ts">
import { computed } from 'vue'
import { 
  HeartHandshakeIcon, 
  DownloadIcon, 
  StarIcon, 
  ShoppingBagIcon, 
  CheckIcon,
  BookOpenIcon,
  EyeIcon
} from '@lucide/vue'
import type { StoreItem } from '@/types/store'
import { useStoreCatalog } from '@/composables/useStoreCatalog'

const props = defineProps<{
  item: StoreItem
  isAddedToCart?: boolean
}>()

const emit = defineEmits<{
  (e: 'view-details', item: StoreItem): void
  (e: 'add-to-cart', item: StoreItem): void
}>()

const { formatToman } = useStoreCatalog()

// Calculate discount percentage
const discountPercentage = computed(() => {
  if (!props.item.has_active_discount || !props.item.discount_price) return 0
  const original = Number(props.item.price)
  const discount = Number(props.item.discount_price)
  if (original <= 0 || discount >= original) return 0
  return Math.round(((original - discount) / original) * 100)
})
</script>

<template>
  <div 
    @click="emit('view-details', item)"
    class="group relative flex flex-col justify-between rounded-2xl bg-card border border-border/70 hover:border-primary/40 shadow-xs hover:shadow-lg transition-all duration-300 overflow-hidden cursor-pointer select-none"
  >
    <!-- Top Image Container -->
    <div class="relative w-full aspect-[16/11] bg-muted/40 overflow-hidden">
      <img 
        v-if="item.cover_image"
        :src="item.cover_image" 
        :alt="item.title"
        class="w-full h-full object-cover object-center group-hover:scale-105 transition-transform duration-500 ease-out"
        loading="lazy"
      />
      <!-- Fallback illustration if image is missing -->
      <div 
        v-else 
        class="w-full h-full flex flex-col items-center justify-center bg-gradient-to-br from-primary/10 to-primary/5 text-primary/60 gap-2 p-4"
      >
        <BookOpenIcon class="size-10 stroke-[1.5]" />
        <span class="text-xs font-medium text-center line-clamp-1">{{ item.category_name }}</span>
      </div>

      <!-- Subtle Top Gradient Overlay for Badge Contrast -->
      <div class="absolute inset-x-0 top-0 h-16 bg-gradient-to-b from-black/40 via-black/15 to-transparent pointer-events-none" />

      <!-- Top-Right: Deal / Delivery Status Badges (Stacked vertically to never overlap) -->
      <div class="absolute top-2.5 right-2.5 z-10 flex flex-col items-start gap-1 pointer-events-none">
        <!-- Donation Badge -->
        <span 
          v-if="item.deal_type === 'donation'"
          class="px-2.5 py-0.5 rounded-lg text-[10px] font-extrabold bg-zinc-800 text-zinc-100 dark:bg-zinc-200 dark:text-zinc-900 shadow-xs flex items-center gap-1 shrink-0 whitespace-nowrap"
        >
          <HeartHandshakeIcon class="size-3" />
          <span>کالای اهدایی</span>
        </span>

        <!-- Digital Badge -->
        <span 
          v-if="item.delivery_type === 'digital'"
          class="px-2 py-0.5 rounded-lg text-[10px] font-bold bg-zinc-700 text-zinc-100 dark:bg-zinc-300 dark:text-zinc-900 shadow-xs flex items-center gap-1 shrink-0 whitespace-nowrap"
        >
          <DownloadIcon class="size-3" />
          <span>دانلودی</span>
        </span>
      </div>

      <!-- Top-Left: Discount Tag or Featured Star -->
      <div class="absolute top-2.5 left-2.5 z-10 pointer-events-none">
        <span 
          v-if="item.has_active_discount && discountPercentage > 0"
          class="px-2 py-0.5 rounded-lg text-[11px] font-black bg-rose-600 text-white shadow-xs flex items-center gap-0.5 shrink-0 whitespace-nowrap"
        >
          <span>{{ discountPercentage }}٪</span>
          <span class="text-[9px] font-medium opacity-90">تخفیف</span>
        </span>

        <span 
          v-else-if="item.is_featured && item.deal_type !== 'donation'"
          class="size-6 rounded-lg bg-zinc-800 text-zinc-200 shadow-xs flex items-center justify-center shrink-0"
          title="کالای منتخب"
        >
          <StarIcon class="size-3.5 fill-current" />
        </span>
      </div>
    </div>

    <!-- Content Body -->
    <div class="p-2.5 sm:p-4 flex flex-col flex-1 justify-between gap-2 sm:gap-3 text-start">
      <div>
        <!-- Category & Location / Delivery -->
        <div class="flex items-center justify-between text-[10px] sm:text-[11px] text-muted-foreground mb-1">
          <span class="truncate font-semibold text-foreground/80">{{ item.category_name }}</span>
          <span v-if="item.city_name" class="text-[9px] sm:text-[10px] shrink-0 text-muted-foreground/80">
            {{ item.city_name }}
          </span>
        </div>

        <!-- Title -->
        <h3 class="text-xs sm:text-sm font-bold text-foreground line-clamp-2 leading-snug group-hover:text-primary transition-colors min-h-[2rem] sm:min-h-[2.5rem]">
          {{ item.title }}
        </h3>

        <!-- Author / Publisher (if book) -->
        <p v-if="item.book_detail?.author" class="text-[10px] sm:text-xs text-muted-foreground mt-0.5 sm:mt-1 line-clamp-1">
          {{ item.book_detail.author }}
        </p>
      </div>

      <!-- Price & CTA Section -->
      <div class="pt-2 sm:pt-3 border-t border-border/50 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1.5 sm:gap-2.5 mt-auto">
        <!-- Price Display -->
        <div class="flex flex-col text-start min-w-0">
          <template v-if="item.deal_type === 'donation'">
            <span class="text-xs sm:text-sm font-black text-foreground whitespace-nowrap">
              رایگان (اهدایی)
            </span>
            <span class="text-[9px] text-muted-foreground truncate hidden sm:inline">ارسال به سراسر کشور</span>
          </template>
          
          <template v-else>
            <div class="flex items-baseline gap-1">
              <span class="text-xs sm:text-base font-black text-foreground tracking-tight">
                {{ formatToman(item.effective_price) }}
              </span>
              <span class="text-[9px] sm:text-[10px] text-muted-foreground font-semibold">تومان</span>
            </div>
            <span 
              v-if="item.has_active_discount"
              class="text-[9px] sm:text-[11px] text-muted-foreground/60 line-through"
            >
              {{ formatToman(item.price) }}
            </span>
          </template>
        </div>

        <!-- Action Button -->
        <button 
          @click.stop="emit('add-to-cart', item)"
          type="button"
          :class="[
            'h-7 sm:h-9 px-2 sm:px-3.5 rounded-lg sm:rounded-xl flex items-center justify-center gap-1 sm:gap-1.5 transition-all duration-200 active:scale-95 shadow-xs cursor-pointer font-bold text-[11px] sm:text-xs shrink-0 self-end sm:self-auto w-full sm:w-auto',
            isAddedToCart 
              ? 'bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900' 
              : 'bg-primary hover:bg-primary/90 text-primary-foreground shadow-xs hover:shadow-md'
          ]"
          :title="item.deal_type === 'donation' ? 'درخواست دریافت اهدایی' : 'افزودن به سبد خرید'"
        >
          <template v-if="isAddedToCart">
            <CheckIcon class="size-3 sm:size-3.5 shrink-0" />
            <span>افزوده شد</span>
          </template>
          <template v-else>
            <HeartHandshakeIcon v-if="item.deal_type === 'donation'" class="size-3 sm:size-3.5 shrink-0" />
            <ShoppingBagIcon v-else class="size-3 sm:size-3.5 shrink-0" />
            <span>{{ item.deal_type === 'donation' ? 'درخواست اهدا' : 'خرید' }}</span>
          </template>
        </button>
      </div>
    </div>
  </div>
</template>
