<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { 
  SearchIcon, 
  XIcon, 
  ShoppingBagIcon, 
  StoreIcon, 
  MenuIcon,
  BookOpenIcon,
  Loader2Icon,
  ArrowUpDownIcon,
  RotateCcwIcon,
  CheckIcon,
  SparklesIcon,
  HeartHandshakeIcon,
  DownloadIcon,
  FlameIcon,
  PackageCheckIcon,
  ChevronLeftIcon
} from '@lucide/vue'
import type { StoreItem } from '@/types/store'
import { useStoreCatalog } from '@/composables/useStoreCatalog'
import StoreProductCard from './StoreProductCard.vue'
import StoreProductDetailModal from './StoreProductDetailModal.vue'
import StoreCartModal from './StoreCartModal.vue'
import StoreCategoryMegaMenu from './StoreCategoryMegaMenu.vue'

const {
  items,
  categories,
  loading,
  error,
  searchQuery,
  selectedCategoryId,
  selectedDealType,
  selectedDeliveryType,
  inStockOnly,
  hasDiscountOnly,
  minPrice,
  maxPrice,
  sortBy,
  activeFiltersCount,
  hasActiveFilters,
  selectedCategoryObj,
  clearAllFilters,
  cartCount,
  fetchItems,
  fetchCategories,
  addToCart,
  formatToman,
} = useStoreCatalog()

const selectedItemForDetail = ref<StoreItem | null>(null)
const isDetailOpen = ref(false)
const isCartOpen = ref(false)
const isMegaMenuOpen = ref(false)
const addedItemIds = ref<number[]>([])

const sortOptions = [
  { label: 'جدیدترین', value: 'newest' },
  { label: 'ارزان‌ترین', value: 'cheapest' },
  { label: 'گران‌ترین', value: 'most_expensive' },
  { label: 'پربازدیدترین', value: 'popular' },
]

onMounted(async () => {
  await Promise.all([
    fetchCategories(),
    fetchItems()
  ])
})

// Debounced search watcher
let searchTimeout: any = null
watch(searchQuery, () => {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    fetchItems()
  }, 300)
})

// Reactive watcher on all filters and sorting
watch([
  selectedCategoryId, 
  selectedDealType, 
  selectedDeliveryType, 
  inStockOnly, 
  hasDiscountOnly, 
  minPrice, 
  maxPrice, 
  sortBy
], () => {
  fetchItems()
})

const handleViewDetails = (item: StoreItem) => {
  selectedItemForDetail.value = item
  isDetailOpen.value = true
}

const handleAddToCart = (item: StoreItem, qty: number = 1) => {
  addToCart(item, qty)
  if (!addedItemIds.value.includes(item.id)) {
    addedItemIds.value.push(item.id)
    setTimeout(() => {
      addedItemIds.value = addedItemIds.value.filter(id => id !== item.id)
    }, 1800)
  }
}

const handleSelectCategory = (catId: number | null) => {
  selectedCategoryId.value = catId
}

const toggleDonation = () => {
  selectedDealType.value = selectedDealType.value === 'donation' ? 'all' : 'donation'
}

const toggleDigital = () => {
  selectedDeliveryType.value = selectedDeliveryType.value === 'digital' ? 'all' : 'digital'
}

const toggleDiscount = () => {
  hasDiscountOnly.value = !hasDiscountOnly.value
}

const togglePopular = () => {
  sortBy.value = sortBy.value === 'popular' ? 'newest' : 'popular'
}

const selectedCategoryParent = computed(() => {
  if (!selectedCategoryObj.value) return null
  for (const parent of categories.value) {
    if (parent.children?.some(ch => ch.id === selectedCategoryObj.value?.id)) {
      return parent
    }
  }
  return null
})
</script>

<template>
  <div class="w-full flex flex-col gap-4 font-sans select-none pb-24 text-start">
    
    <!-- Clean, Minimalist Digikala-Style Top Bar (Zero bulky banners) -->
    <div class="w-full flex flex-col gap-3">
      
      <!-- Row 1: Search Input & Shopping Cart Button -->
      <div class="w-full flex items-center gap-2.5">
        
        <!-- Search Input -->
        <div class="relative flex-1 flex items-center">
          <SearchIcon class="absolute right-3.5 size-4 text-muted-foreground pointer-events-none" />
          <input 
            v-model="searchQuery"
            type="text"
            placeholder="جستجو در قرآن، کتب، نویسنده، ناشر یا شابک..."
            class="w-full h-11 pr-10 pl-9 rounded-2xl bg-card border border-border/70 text-xs font-medium text-foreground placeholder:text-muted-foreground/60 focus:outline-none focus:ring-1 focus:ring-primary/40 focus:border-primary transition-all text-start"
          />
          <button 
            v-if="searchQuery"
            @click="searchQuery = ''"
            class="absolute left-3 size-6 rounded-lg flex items-center justify-center text-muted-foreground hover:text-foreground cursor-pointer"
          >
            <XIcon class="size-3.5" />
          </button>
        </div>

        <!-- Sleek Shopping Cart Button -->
        <button
          @click="isCartOpen = true"
          type="button"
          class="h-11 px-3.5 rounded-2xl bg-card border border-border/70 hover:border-primary/50 text-foreground text-xs font-bold flex items-center gap-2 transition-all shadow-xs hover:shadow-sm cursor-pointer shrink-0"
        >
          <ShoppingBagIcon class="size-4 text-primary" />
          <span class="hidden sm:inline">سبد خرید</span>
          <span 
            v-if="cartCount > 0"
            class="px-1.5 py-0.2 rounded-full text-[10px] font-black bg-primary text-primary-foreground leading-tight"
          >
            {{ cartCount }}
          </span>
        </button>
      </div>

      <!-- Digikala-Style Sub-Navbar (Pure monochrome, flat inline links, zero button boxes, zero green/blue) -->
      <div class="w-full border-b border-border/70 pb-2 flex flex-wrap items-center justify-between gap-x-4 gap-y-2 text-xs select-none">
        
        <!-- Right / Start: Menu Trigger & Flat Inline Navigation Links -->
        <div class="flex items-center gap-x-3 sm:gap-x-4 flex-wrap">
          
          <!-- Digikala «دسته‌بندی کالاها ☰» Trigger (Flat Link) -->
          <button
            @click="isMegaMenuOpen = true"
            type="button"
            class="flex items-center gap-1.5 py-1 text-xs font-bold text-foreground hover:text-foreground/75 transition-colors cursor-pointer shrink-0"
            title="مشاهده دسته‌بندی‌ها"
          >
            <MenuIcon class="size-4 shrink-0 text-foreground" />
            <span>{{ selectedCategoryObj ? selectedCategoryObj.name : 'دسته‌بندی کالاها' }}</span>
          </button>

          <!-- Divider -->
          <div class="h-3.5 w-px bg-border/80 shrink-0" />

          <!-- شگفت‌انگیزها (تخفیف‌دارها) -->
          <button
            @click="toggleDiscount"
            type="button"
            :class="[
              'flex items-center gap-1.5 py-1 text-xs transition-colors cursor-pointer shrink-0',
              hasDiscountOnly
                ? 'font-bold text-foreground'
                : 'font-normal text-muted-foreground hover:text-foreground'
            ]"
          >
            <SparklesIcon class="size-3.5 shrink-0" :class="hasDiscountOnly ? 'text-foreground' : 'text-muted-foreground/70'" />
            <span>شگفت‌انگیزها</span>
          </button>

          <!-- کالاهای اهدایی -->
          <button
            @click="toggleDonation"
            type="button"
            :class="[
              'flex items-center gap-1.5 py-1 text-xs transition-colors cursor-pointer shrink-0',
              selectedDealType === 'donation'
                ? 'font-bold text-foreground'
                : 'font-normal text-muted-foreground hover:text-foreground'
            ]"
          >
            <HeartHandshakeIcon class="size-3.5 shrink-0" :class="selectedDealType === 'donation' ? 'text-foreground' : 'text-muted-foreground/70'" />
            <span>کالاهای اهدایی</span>
          </button>

          <!-- فایل‌های دانلودی -->
          <button
            @click="toggleDigital"
            type="button"
            :class="[
              'flex items-center gap-1.5 py-1 text-xs transition-colors cursor-pointer shrink-0',
              selectedDeliveryType === 'digital'
                ? 'font-bold text-foreground'
                : 'font-normal text-muted-foreground hover:text-foreground'
            ]"
          >
            <DownloadIcon class="size-3.5 shrink-0" :class="selectedDeliveryType === 'digital' ? 'text-foreground' : 'text-muted-foreground/70'" />
            <span>فایل‌های دانلودی</span>
          </button>

          <!-- پرفروش‌ترین‌ها -->
          <button
            @click="togglePopular"
            type="button"
            :class="[
              'flex items-center gap-1.5 py-1 text-xs transition-colors cursor-pointer shrink-0',
              sortBy === 'popular'
                ? 'font-bold text-foreground'
                : 'font-normal text-muted-foreground hover:text-foreground'
            ]"
          >
            <FlameIcon class="size-3.5 shrink-0" :class="sortBy === 'popular' ? 'text-foreground' : 'text-muted-foreground/70'" />
            <span>پرفروش‌ترین‌ها</span>
          </button>

          <!-- فقط کالاهای موجود -->
          <button
            @click="inStockOnly = !inStockOnly"
            type="button"
            :class="[
              'flex items-center gap-1.5 py-1 text-xs transition-colors cursor-pointer shrink-0 hidden md:flex',
              inStockOnly
                ? 'font-bold text-foreground'
                : 'font-normal text-muted-foreground hover:text-foreground'
            ]"
          >
            <PackageCheckIcon class="size-3.5 shrink-0" :class="inStockOnly ? 'text-foreground' : 'text-muted-foreground/70'" />
            <span>فقط کالاهای موجود</span>
          </button>

          <!-- Divider -->
          <div class="h-3.5 w-px bg-border/80 shrink-0" />

        </div>

        <!-- Left / End: Sorting & Count -->
        <div class="flex items-center gap-3 ms-auto sm:ms-0">
          <div class="flex items-center gap-2 text-xs">
            <span class="text-[11px] text-muted-foreground/60 hidden sm:inline">مرتب‌سازی:</span>
            <div class="flex items-center gap-1.5">
              <button
                v-for="opt in sortOptions.filter(o => o.value !== 'popular')"
                :key="opt.value"
                @click="sortBy = opt.value"
                type="button"
                :class="[
                  'px-1.5 py-0.5 text-xs transition-colors cursor-pointer shrink-0 select-none whitespace-nowrap',
                  sortBy === opt.value
                    ? 'font-bold text-foreground'
                    : 'text-muted-foreground hover:text-foreground'
                ]"
              >
                {{ opt.label }}
              </button>
            </div>
          </div>

          <span class="text-xs text-muted-foreground/60 font-medium hidden sm:inline font-mono">
            {{ items.length }} کالا
          </span>
        </div>

      </div>

      <!-- Digikala-Style Breadcrumbs (Directly beneath sub-navbar, NO delete chips!) -->
      <div class="w-full flex items-center gap-1.5 text-xs text-muted-foreground/75 py-0.5 flex-wrap">
        <button 
          @click="clearAllFilters" 
          class="hover:text-foreground transition-colors cursor-pointer font-medium"
        >
          فروشگاه اینترنتی تفکر
        </button>
        <span class="text-muted-foreground/40 text-[10px]">/</span>
        
        <template v-if="selectedCategoryObj">
          <button 
            v-if="selectedCategoryParent"
            @click="selectedCategoryId = selectedCategoryParent.id"
            class="hover:text-foreground transition-colors cursor-pointer"
          >
            {{ selectedCategoryParent.name }}
          </button>
          <span v-if="selectedCategoryParent" class="text-muted-foreground/40 text-[10px]">/</span>
          <span class="text-foreground font-bold">{{ selectedCategoryObj.name }}</span>
        </template>
        <template v-else>
          <span class="text-foreground font-medium">همه کتب و محصولات فرهنگی</span>
        </template>
      </div>

    </div>

    <!-- Products Grid Section (2 items per row on mobile, 3 items per row on desktop/tablet) -->
    <div class="w-full">
      <!-- Loading State -->
      <div v-if="loading" class="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-6">
        <div 
          v-for="i in 6" 
          :key="i"
          class="rounded-2xl border border-border/60 bg-card/60 p-3 sm:p-4 flex flex-col gap-3 animate-pulse"
        >
          <div class="w-full aspect-[16/11] rounded-xl bg-muted/60" />
          <div class="h-3.5 w-3/4 rounded-md bg-muted/60" />
          <div class="h-3 w-1/2 rounded-md bg-muted/50" />
          <div class="h-5 w-1/3 rounded-md bg-muted/70 mt-2" />
        </div>
      </div>

      <!-- Empty State -->
      <div 
        v-else-if="items.length === 0" 
        class="w-full rounded-3xl border border-dashed border-border/80 p-10 flex flex-col items-center justify-center text-center gap-3 bg-muted/10 my-6"
      >
        <div class="size-16 rounded-2xl bg-muted/50 flex items-center justify-center text-muted-foreground">
          <BookOpenIcon class="size-8 stroke-[1.5]" />
        </div>
        <span class="text-sm font-bold text-foreground">کالایی با فیلترهای انتخابی یافت نشد</span>
        <span class="text-xs text-muted-foreground max-w-sm">
          می‌توانید کلمه جستجو را تغییر دهید یا فیلترهای انتخابی را پاک کنید.
        </span>
        <button
          @click="clearAllFilters"
          class="px-5 py-2.5 rounded-xl bg-primary text-primary-foreground text-xs font-bold transition-all cursor-pointer mt-2 shadow-xs hover:shadow-md"
        >
          پاک کردن تمام فیلترها
        </button>
      </div>

      <!-- Products Grid: 2 columns on mobile, 3 columns on tablet/desktop -->
      <div v-else class="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-6">
        <StoreProductCard
          v-for="item in items"
          :key="item.id"
          :item="item"
          :is-added-to-cart="addedItemIds.includes(item.id)"
          @view-details="handleViewDetails"
          @add-to-cart="handleAddToCart"
        />
      </div>
    </div>

    <!-- Digikala-Style Category Mega-Menu Pop-up -->
    <StoreCategoryMegaMenu
      v-model:open="isMegaMenuOpen"
      :categories="categories"
      :selected-category-id="selectedCategoryId"
      v-model:selected-deal-type="selectedDealType"
      v-model:selected-delivery-type="selectedDeliveryType"
      v-model:in-stock-only="inStockOnly"
      :active-filters-count="activeFiltersCount"
      :total-items-count="items.length"
      @select-category="handleSelectCategory"
      @clear-all="clearAllFilters"
    />

    <!-- Product Detail Modal -->
    <StoreProductDetailModal
      v-model:open="isDetailOpen"
      :item="selectedItemForDetail"
      @add-to-cart="handleAddToCart"
    />

    <!-- Cart Modal -->
    <StoreCartModal
      v-model:open="isCartOpen"
    />

  </div>
</template>
