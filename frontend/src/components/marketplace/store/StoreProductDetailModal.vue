<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { 
  XIcon, 
  MapPinIcon, 
  TruckIcon, 
  FileTextIcon, 
  BookOpenIcon, 
  HeartHandshakeIcon, 
  ShoppingBagIcon, 
  CheckIcon,
  PlusIcon,
  MinusIcon,
  TagIcon,
  ShieldCheckIcon
} from '@lucide/vue'
import {
  Dialog,
  DialogContent,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog'
import type { StoreItem } from '@/types/store'
import { useStoreCatalog } from '@/composables/useStoreCatalog'
import { useLanguageStore } from '@/stores/languageStore'

const props = defineProps<{
  open: boolean
  item: StoreItem | null
}>()

const emit = defineEmits<{
  (e: 'update:open', val: boolean): void
  (e: 'add-to-cart', item: StoreItem, quantity: number): void
}>()

const languageStore = useLanguageStore()
const { formatToman } = useStoreCatalog()

const selectedImage = ref<string>('')
const quantity = ref(1)
const isAdded = ref(false)

watch(() => props.item, (newItem) => {
  if (newItem) {
    selectedImage.value = newItem.cover_image || (newItem.images?.[0]?.image_url || '')
    quantity.value = 1
    isAdded.value = false
  }
}, { immediate: true })

const allImages = computed(() => {
  if (!props.item) return []
  const imgs: string[] = []
  if (props.item.cover_image) imgs.push(props.item.cover_image)
  if (props.item.images) {
    props.item.images.forEach(img => {
      if (img.image_url && !imgs.includes(img.image_url)) {
        imgs.push(img.image_url)
      }
    })
  }
  return imgs
})

const handleAddToCart = () => {
  if (!props.item) return
  emit('add-to-cart', props.item, quantity.value)
  isAdded.value = true
  setTimeout(() => {
    isAdded.value = false
  }, 2000)
}

const conditionLabel = computed(() => {
  switch (props.item?.condition) {
    case 'new': return 'نو و آکبند'
    case 'like_new': return 'در حد نو (بسیار تمیز)'
    case 'used': return 'دست‌دوم سالم'
    case 'damaged': return 'دارای ایراد جزئی'
    default: return null
  }
})
</script>

<template>
  <Dialog :open="open" @update:open="(val) => emit('update:open', val)">
    <DialogContent 
      v-if="item"
      :dir="languageStore.dir"
      class="w-[90vw] max-w-[500px] p-0 overflow-hidden rounded-3xl bg-card border-border/80 shadow-2xl flex flex-col max-h-[85vh]"
    >
      <DialogTitle class="sr-only">{{ item.title }}</DialogTitle>
      <DialogDescription class="sr-only">{{ item.description }}</DialogDescription>

      <!-- Modal Header Bar -->
      <div class="h-14 px-5 border-b border-border/60 flex items-center justify-between bg-muted/20 shrink-0 select-none">
        <div class="flex items-center gap-2">
          <span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-primary/10 text-primary border border-primary/20">
            {{ item.category_name }}
          </span>
          <span 
            v-if="item.deal_type === 'donation'"
            class="px-2 py-0.5 rounded-full text-[10px] font-extrabold bg-muted text-foreground border border-border/80 flex items-center gap-1"
          >
            <HeartHandshakeIcon class="size-3 text-muted-foreground" />
            کالای اهدایی
          </span>
        </div>
      </div>

      <!-- Scrollable Body Content -->
      <div class="p-5 overflow-y-auto flex-1 flex flex-col gap-5 text-start font-sans scrollbar-none no-scrollbar">
        
        <!-- Image & Gallery Viewer -->
        <div class="flex flex-col gap-2.5">
          <div class="w-full aspect-16/10 rounded-2xl bg-muted/40 overflow-hidden border border-border/60 relative">
            <img 
              v-if="selectedImage"
              :src="selectedImage" 
              :alt="item.title"
              class="w-full h-full object-cover object-center"
            />
            <div v-else class="w-full h-full flex items-center justify-center text-muted-foreground/40">
              <BookOpenIcon class="size-16" />
            </div>

            <!-- Discount Badge Overlay -->
            <span 
              v-if="item.has_active_discount"
              class="absolute top-3 right-3 px-2.5 py-1 rounded-xl text-xs font-black bg-rose-500 text-white shadow-md flex items-center gap-1"
            >
              <TagIcon class="size-3" />
              تخفیف ویژه تفکر
            </span>
          </div>

          <!-- Thumbnails Strip -->
          <div v-if="allImages.length > 1" class="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none no-scrollbar">
            <button
              v-for="(img, idx) in allImages"
              :key="idx"
              @click="selectedImage = img"
              :class="[
                'size-14 rounded-xl overflow-hidden border-2 transition-all shrink-0 cursor-pointer',
                selectedImage === img ? 'border-primary shadow-xs scale-95' : 'border-transparent opacity-60 hover:opacity-100'
              ]"
            >
              <img :src="img" :alt="`تصویر ${idx + 1}`" class="w-full h-full object-cover" />
            </button>
          </div>
        </div>

        <!-- Title & Basic Info -->
        <div>
          <h2 class="text-base sm:text-lg font-black text-foreground leading-snug">
            {{ item.title }}
          </h2>

          <!-- Meta tags (City, Condition, Delivery) -->
          <div class="flex flex-wrap items-center gap-2 mt-2.5 text-xs text-muted-foreground">
            <span v-if="item.city_name" class="inline-flex items-center gap-1 bg-muted/60 px-2 py-1 rounded-lg">
              <MapPinIcon class="size-3 text-primary" />
              ارسال از {{ item.city_name }}
            </span>
            <span v-if="conditionLabel" class="inline-flex items-center gap-1 bg-muted/60 px-2 py-1 rounded-lg">
              <ShieldCheckIcon class="size-3 text-muted-foreground" />
              {{ conditionLabel }}
            </span>
            <span class="inline-flex items-center gap-1 bg-muted/60 px-2 py-1 rounded-lg">
              <TruckIcon class="size-3 text-amber-500" />
              {{ item.delivery_type === 'digital' ? 'دانلود آنی پس از سفارش' : 'تحویل پستی سراسر کشور' }}
            </span>
          </div>
        </div>

        <!-- Book Metadata Box (if present) -->
        <div 
          v-if="item.book_detail"
          class="rounded-2xl bg-muted/30 border border-border/60 p-3.5 flex flex-col gap-2 text-xs"
        >
          <span class="font-bold text-foreground flex items-center gap-1.5 mb-1 text-primary">
            <BookOpenIcon class="size-3.5" />
            شناسنامه کتاب و مشخصات نشر
          </span>
          <div class="grid grid-cols-2 gap-2 text-[11px]">
            <div v-if="item.book_detail.author" class="flex flex-col">
              <span class="text-muted-foreground">پدیدآورنده / نویسنده:</span>
              <span class="font-semibold text-foreground mt-0.5">{{ item.book_detail.author }}</span>
            </div>
            <div v-if="item.book_detail.publisher" class="flex flex-col">
              <span class="text-muted-foreground">ناشر:</span>
              <span class="font-semibold text-foreground mt-0.5">{{ item.book_detail.publisher }}</span>
            </div>
            <div v-if="item.book_detail.translator" class="flex flex-col">
              <span class="text-muted-foreground">مترجم:</span>
              <span class="font-semibold text-foreground mt-0.5">{{ item.book_detail.translator }}</span>
            </div>
            <div v-if="item.book_detail.publication_year" class="flex flex-col">
              <span class="text-muted-foreground">سال چاپ:</span>
              <span class="font-semibold text-foreground mt-0.5">{{ item.book_detail.publication_year }}</span>
            </div>
            <div v-if="item.book_detail.pages_count" class="flex flex-col">
              <span class="text-muted-foreground">تعداد صفحات:</span>
              <span class="font-semibold text-foreground mt-0.5">{{ item.book_detail.pages_count }} صفحه</span>
            </div>
            <div v-if="item.book_detail.isbn" class="flex flex-col">
              <span class="text-muted-foreground">شابک (ISBN):</span>
              <span class="font-semibold text-foreground mt-0.5 font-mono">{{ item.book_detail.isbn }}</span>
            </div>
          </div>
        </div>

        <!-- Description -->
        <div class="flex flex-col gap-1.5">
          <span class="text-xs font-bold text-foreground">توضیحات و معرفی کالا:</span>
          <p class="text-xs text-muted-foreground leading-relaxed whitespace-pre-line">
            {{ item.description || 'توضیحات بیشتری برای این کالا ثبت نشده است.' }}
          </p>
        </div>

      </div>

      <!-- Sticky Bottom Action & Price Bar -->
      <div class="p-4 border-t border-border/70 bg-card flex items-center justify-between gap-3 shrink-0">
        <!-- Price Info -->
        <div class="flex flex-col text-start">
          <template v-if="item.deal_type === 'donation'">
            <span class="text-sm font-black text-foreground">
              رایگان (طرح اهدای کتاب)
            </span>
            <span class="text-[10px] text-muted-foreground">فقط هزینه پست هنگام تحویل</span>
          </template>
          <template v-else>
            <div class="flex items-baseline gap-1">
              <span class="text-base font-black text-foreground">
                {{ formatToman(item.effective_price * quantity) }}
              </span>
              <span class="text-xs text-muted-foreground">تومان</span>
            </div>
            <span 
              v-if="item.has_active_discount"
              class="text-[11px] text-muted-foreground/60 line-through"
            >
              {{ formatToman(Number(item.price) * quantity) }}
            </span>
          </template>
        </div>

        <!-- Quantity & Add Actions -->
        <div class="flex items-center gap-2.5">
          <!-- Quantity Stepper (if sale & physical) -->
          <div 
            v-if="item.deal_type === 'sale' && !item.is_unlimited_stock"
            class="flex items-center bg-muted/70 rounded-xl p-1 border border-border/70 shadow-2xs"
          >
            <button 
              @click="quantity++"
              :disabled="quantity >= item.stock"
              class="size-8 rounded-lg flex items-center justify-center hover:bg-background text-foreground disabled:opacity-30 cursor-pointer transition-colors"
            >
              <PlusIcon class="size-4" />
            </button>
            <span class="w-7 text-center text-xs font-black">{{ quantity }}</span>
            <button 
              @click="quantity = Math.max(1, quantity - 1)"
              :disabled="quantity <= 1"
              class="size-8 rounded-lg flex items-center justify-center hover:bg-background text-foreground disabled:opacity-30 cursor-pointer transition-colors"
            >
              <MinusIcon class="size-4" />
            </button>
          </div>

          <!-- Main CTA Button -->
          <button
            @click="handleAddToCart"
            :class="[
              'px-5 py-2.5 rounded-xl text-xs sm:text-sm font-bold flex items-center gap-2 transition-all duration-200 active:scale-95 shadow-xs hover:shadow-md cursor-pointer',
              isAdded 
                ? 'bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900' 
                : 'bg-primary text-primary-foreground hover:bg-primary/90'
            ]"
          >
            <CheckIcon v-if="isAdded" class="size-4.5" />
            <template v-else>
              <HeartHandshakeIcon v-if="item.deal_type === 'donation'" class="size-4.5" />
              <ShoppingBagIcon v-else class="size-4.5" />
              <span>{{ item.deal_type === 'donation' ? 'ثبت درخواست دریافت' : 'افزودن به سبد' }}</span>
            </template>
          </button>
        </div>
      </div>

    </DialogContent>
  </Dialog>
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
