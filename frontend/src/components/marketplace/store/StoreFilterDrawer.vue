<script setup lang="ts">
import { computed } from 'vue'
import { 
  SlidersHorizontalIcon, 
  RotateCcwIcon, 
  HeartHandshakeIcon, 
  DownloadIcon, 
  CheckIcon, 
  TagIcon, 
  PackageCheckIcon,
  BookOpenIcon
} from '@lucide/vue'
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from '@/components/ui/sheet'
import { Switch } from '@/components/ui/switch'
import { Button } from '@/components/ui/button'
import type { StoreCategory } from '@/types/store'
import { useLanguageStore } from '@/stores/languageStore'

const props = defineProps<{
  open: boolean
  categories: StoreCategory[]
  selectedCategoryId: number | null
  selectedDealType: 'all' | 'sale' | 'donation'
  selectedDeliveryType: 'all' | 'physical' | 'digital'
  inStockOnly: boolean
  hasDiscountOnly: boolean
  minPrice: number | null
  maxPrice: number | null
  activeFiltersCount: number
  totalItemsCount: number
}>()

const emit = defineEmits<{
  (e: 'update:open', val: boolean): void
  (e: 'update:selectedCategoryId', val: number | null): void
  (e: 'update:selectedDealType', val: 'all' | 'sale' | 'donation'): void
  (e: 'update:selectedDeliveryType', val: 'all' | 'physical' | 'digital'): void
  (e: 'update:inStockOnly', val: boolean): void
  (e: 'update:hasDiscountOnly', val: boolean): void
  (e: 'update:minPrice', val: number | null): void
  (e: 'update:maxPrice', val: number | null): void
  (e: 'clear-all'): void
  (e: 'apply'): void
}>()

const languageStore = useLanguageStore()

const isDonationOnly = computed({
  get: () => props.selectedDealType === 'donation',
  set: (val: boolean) => {
    emit('update:selectedDealType', val ? 'donation' : 'all')
  }
})

const isDigitalOnly = computed({
  get: () => props.selectedDeliveryType === 'digital',
  set: (val: boolean) => {
    emit('update:selectedDeliveryType', val ? 'digital' : 'all')
  }
})

const formatToman = (val: number | null): string => {
  if (!val) return ''
  return new Intl.NumberFormat('fa-IR').format(val)
}

const handleClear = () => {
  emit('clear-all')
}

const handleApply = () => {
  emit('apply')
  emit('update:open', false)
}
</script>

<template>
  <Sheet :open="open" @update:open="(val: boolean) => emit('update:open', val)">
    <SheetContent 
      side="right" 
      :dir="languageStore.dir"
      class="w-full sm:max-w-md p-0 flex flex-col font-sans select-none bg-card text-card-foreground border-border/80 shadow-2xl"
    >
      <!-- Header -->
      <div class="h-14 px-5 border-b border-border/60 flex items-center justify-between bg-muted/20 shrink-0">
        <div class="flex items-center gap-2 text-foreground">
          <div class="size-8 rounded-xl bg-primary/10 text-primary flex items-center justify-center">
            <SlidersHorizontalIcon class="size-4" />
          </div>
          <div class="flex items-center gap-1.5">
            <span class="text-sm font-black">فیلترها</span>
            <span 
              v-if="activeFiltersCount > 0"
              class="px-1.5 py-0.2 rounded-full text-[10px] font-black bg-primary text-primary-foreground leading-tight"
            >
              {{ activeFiltersCount }}
            </span>
          </div>
        </div>

        <button
          v-if="activeFiltersCount > 0"
          @click="handleClear"
          type="button"
          class="text-xs font-semibold text-destructive hover:bg-destructive/10 px-2.5 py-1 rounded-xl transition-all cursor-pointer flex items-center gap-1 ms-auto me-8"
        >
          <RotateCcwIcon class="size-3" />
          <span>حذف فیلترها</span>
        </button>
      </div>

      <!-- Scrollable Filter Accordions / Sections -->
      <div class="p-5 flex-1 overflow-y-auto flex flex-col gap-6 text-start scrollbar-none no-scrollbar">

        <!-- 1. Categories Hierarchy -->
        <div class="flex flex-col gap-2.5">
          <span class="text-xs font-bold text-foreground flex items-center gap-1.5">
            <BookOpenIcon class="size-3.5 text-primary" />
            دسته‌بندی موضوعی کالا
          </span>

          <div class="flex flex-col gap-1 p-1 rounded-2xl bg-muted/25 border border-border/60">
            <!-- All Categories Option -->
            <button
              @click="emit('update:selectedCategoryId', null)"
              type="button"
              :class="[
                'w-full px-3 py-2 rounded-xl text-xs font-semibold flex items-center justify-between transition-all cursor-pointer text-start',
                selectedCategoryId === null
                  ? 'bg-primary text-primary-foreground font-bold shadow-xs'
                  : 'text-foreground hover:bg-muted/50'
              ]"
            >
              <span>همه موضوعات</span>
              <CheckIcon v-if="selectedCategoryId === null" class="size-3.5" />
            </button>

            <!-- Category Items -->
            <button
              v-for="cat in categories"
              :key="cat.id"
              @click="emit('update:selectedCategoryId', cat.id)"
              type="button"
              :class="[
                'w-full px-3 py-2 rounded-xl text-xs font-semibold flex items-center justify-between transition-all cursor-pointer text-start',
                selectedCategoryId === cat.id
                  ? 'bg-primary text-primary-foreground font-bold shadow-xs'
                  : 'text-foreground hover:bg-muted/50'
              ]"
            >
              <div class="flex items-center gap-2">
                <span>{{ cat.name }}</span>
              </div>
              <CheckIcon v-if="selectedCategoryId === cat.id" class="size-3.5" />
            </button>
          </div>
        </div>

        <!-- 2. Fast Toggle Switches (Digikala Style) -->
        <div class="flex flex-col gap-2">
          <span class="text-xs font-bold text-foreground">وضعیت و شرایط ویژه</span>
          
          <div class="flex flex-col rounded-2xl border border-border/60 divide-y divide-border/40 bg-card overflow-hidden">
            
            <!-- Only Donation Goods Switch -->
            <div class="p-3.5 flex items-center justify-between gap-3">
              <div class="flex items-center gap-2.5">
                <div class="size-7 rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 flex items-center justify-center shrink-0">
                  <HeartHandshakeIcon class="size-4" />
                </div>
                <div class="flex flex-col">
                  <span class="text-xs font-bold text-foreground">فقط کالاهای اهدایی</span>
                  <span class="text-[10px] text-muted-foreground">کتب و محصولات وقفی بدون هزینه خرید</span>
                </div>
              </div>
              <Switch 
                :checked="isDonationOnly"
                @update:checked="(val: boolean) => isDonationOnly = val"
              />
            </div>

            <!-- Only Digital Goods Switch -->
            <div class="p-3.5 flex items-center justify-between gap-3">
              <div class="flex items-center gap-2.5">
                <div class="size-7 rounded-lg bg-sky-500/10 text-sky-600 dark:text-sky-400 flex items-center justify-center shrink-0">
                  <DownloadIcon class="size-4" />
                </div>
                <div class="flex flex-col">
                  <span class="text-xs font-bold text-foreground">فقط فایل‌های دانلودی</span>
                  <span class="text-[10px] text-muted-foreground">دسترسی آنی به فایل پی‌دی‌اف و صوتی</span>
                </div>
              </div>
              <Switch 
                :checked="isDigitalOnly"
                @update:checked="(val: boolean) => isDigitalOnly = val"
              />
            </div>

            <!-- Only In-Stock Items Switch -->
            <div class="p-3.5 flex items-center justify-between gap-3">
              <div class="flex items-center gap-2.5">
                <div class="size-7 rounded-lg bg-amber-500/10 text-amber-600 dark:text-amber-400 flex items-center justify-center shrink-0">
                  <PackageCheckIcon class="size-4" />
                </div>
                <div class="flex flex-col">
                  <span class="text-xs font-bold text-foreground">فقط کالاهای موجود</span>
                  <span class="text-[10px] text-muted-foreground">مواردی که موجودی انبار دارند</span>
                </div>
              </div>
              <Switch 
                :checked="inStockOnly"
                @update:checked="(val: boolean) => emit('update:inStockOnly', val)"
              />
            </div>

            <!-- Only Discounted Items Switch -->
            <div class="p-3.5 flex items-center justify-between gap-3">
              <div class="flex items-center gap-2.5">
                <div class="size-7 rounded-lg bg-rose-500/10 text-rose-600 dark:text-rose-400 flex items-center justify-center shrink-0">
                  <TagIcon class="size-4" />
                </div>
                <div class="flex flex-col">
                  <span class="text-xs font-bold text-foreground">فقط تخفیف‌دارها</span>
                  <span class="text-[10px] text-muted-foreground">محصولات دارای تخفیف شگفت‌انگیز</span>
                </div>
              </div>
              <Switch 
                :checked="hasDiscountOnly"
                @update:checked="(val: boolean) => emit('update:hasDiscountOnly', val)"
              />
            </div>

          </div>
        </div>

        <!-- 3. Price Range (Min & Max Tomans) -->
        <div class="flex flex-col gap-2.5">
          <span class="text-xs font-bold text-foreground">محدوده قیمت (تومان)</span>
          
          <div class="grid grid-cols-2 gap-2.5">
            <!-- Min Price -->
            <div class="flex flex-col gap-1">
              <label class="text-[10px] text-muted-foreground font-medium">از قیمت:</label>
              <input
                :value="minPrice || ''"
                @input="(e: any) => emit('update:minPrice', e.target.value ? Number(e.target.value) : null)"
                type="number"
                placeholder="حداقل (تومان)"
                class="w-full h-10 px-3 rounded-xl bg-card border border-border/70 text-xs font-medium text-foreground focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary text-start"
              />
              <span v-if="minPrice" class="text-[10px] text-primary font-semibold text-start">
                {{ formatToman(minPrice) }} تومان
              </span>
            </div>

            <!-- Max Price -->
            <div class="flex flex-col gap-1">
              <label class="text-[10px] text-muted-foreground font-medium">تا قیمت:</label>
              <input
                :value="maxPrice || ''"
                @input="(e: any) => emit('update:maxPrice', e.target.value ? Number(e.target.value) : null)"
                type="number"
                placeholder="حداکثر (تومان)"
                class="w-full h-10 px-3 rounded-xl bg-card border border-border/70 text-xs font-medium text-foreground focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary text-start"
              />
              <span v-if="maxPrice" class="text-[10px] text-primary font-semibold text-start">
                {{ formatToman(maxPrice) }} تومان
              </span>
            </div>
          </div>
        </div>

      </div>

      <!-- Sticky Bottom Action Button -->
      <div class="p-4 border-t border-border/70 bg-card shrink-0 flex items-center gap-2">
        <Button
          @click="handleApply"
          class="flex-1 h-11 rounded-2xl bg-primary text-primary-foreground text-xs font-bold shadow-md cursor-pointer hover:bg-primary/95 active:scale-[0.99] transition-all"
        >
          <span>مشاهده کالاها</span>
          <span v-if="totalItemsCount > 0" class="opacity-90 font-mono">({{ totalItemsCount }})</span>
        </Button>
      </div>

    </SheetContent>
  </Sheet>
</template>

<style scoped>
.scrollbar-none,
.no-scrollbar {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
.scrollbar-none::-webkit-scrollbar,
.no-scrollbar::-webkit-scrollbar {
  display: none;
}
</style>
