<script setup lang="ts">
import { ref, computed } from 'vue'
import { 
  MenuIcon, 
  XIcon, 
  ChevronLeftIcon, 
  ChevronDownIcon,
  BookOpenIcon, 
  GraduationCapIcon, 
  LandmarkIcon, 
  HeadphonesIcon, 
  FeatherIcon, 
  SmileIcon,
  HeartHandshakeIcon,
  DownloadIcon,
  PackageCheckIcon,
  RotateCcwIcon,
  CheckIcon
} from '@lucide/vue'
import type { StoreCategory } from '@/types/store'
import { useLanguageStore } from '@/stores/languageStore'

const props = defineProps<{
  open: boolean
  categories: StoreCategory[]
  selectedCategoryId: number | null
  selectedDealType: 'all' | 'sale' | 'donation'
  selectedDeliveryType: 'all' | 'physical' | 'digital'
  inStockOnly: boolean
  activeFiltersCount: number
  totalItemsCount: number
}>()

const emit = defineEmits<{
  (e: 'update:open', val: boolean): void
  (e: 'select-category', categoryId: number | null): void
  (e: 'update:selectedDealType', val: 'all' | 'sale' | 'donation'): void
  (e: 'update:selectedDeliveryType', val: 'all' | 'physical' | 'digital'): void
  (e: 'update:inStockOnly', val: boolean): void
  (e: 'clear-all'): void
}>()

const languageStore = useLanguageStore()

// Active highlighted category in the right sidebar (defaults to selected or first category)
const activeHoverCategoryId = ref<number | null>(null)
const expandedMobileCatId = ref<number | null>(null)

// Computed active category object for the right sidebar
const currentParentCategory = computed(() => {
  if (props.categories.length === 0) return null
  if (activeHoverCategoryId.value !== null) {
    const found = props.categories.find(c => c.id === activeHoverCategoryId.value)
    if (found) return found
  }
  if (props.selectedCategoryId !== null) {
    // Check if it's a top parent
    const foundParent = props.categories.find(c => c.id === props.selectedCategoryId)
    if (foundParent) return foundParent
    // Check if it's a child
    for (const cat of props.categories) {
      if (cat.children?.some(ch => ch.id === props.selectedCategoryId)) {
        return cat
      }
    }
  }
  return props.categories[0] || null
})

// Clean, gentle icon mapper for categories (minimal, zero aggressive graphics)
const getCategoryIcon = (slug: string) => {
  switch (slug) {
    case 'religious-books': return BookOpenIcon
    case 'literature-poetry': return FeatherIcon
    case 'academic-books': return GraduationCapIcon
    case 'history-philosophy': return LandmarkIcon
    case 'multimedia-software': return HeadphonesIcon
    case 'children-books': return SmileIcon
    default: return BookOpenIcon
  }
}

const handleSelectCategory = (catId: number | null) => {
  emit('select-category', catId)
  emit('update:open', false)
}

const handleClose = () => {
  emit('update:open', false)
}

const toggleMobileCategory = (cat: StoreCategory) => {
  if (cat.children && cat.children.length > 0) {
    expandedMobileCatId.value = expandedMobileCatId.value === cat.id ? null : cat.id
  } else {
    handleSelectCategory(cat.id)
  }
}
</script>

<template>
  <!-- Responsive Category Menu: Mobile Slide-Out Drawer & Desktop Pop-up Modal -->
  <Teleport to="body">
    <div 
      v-if="open" 
      class="fixed inset-0 z-50 select-none font-sans overflow-hidden sm:flex sm:items-start sm:justify-center sm:pt-20 sm:px-6"
      :dir="languageStore.dir"
    >
      <!-- Soft Dimmed Backdrop -->
      <transition name="fade">
        <div 
          @click="handleClose" 
          class="fixed inset-0 bg-black/45 backdrop-blur-xs transition-opacity duration-200 z-40"
        />
      </transition>

      <!-- Main Panel: Mobile Right-Side Slider Drawer (Square Corners) vs Desktop Pop-up Modal -->
      <transition name="slide-corner">
        <div 
          class="fixed inset-y-0 right-0 z-50 flex flex-col bg-card text-card-foreground overflow-hidden w-[70vw] max-w-[275px] min-w-[240px] h-full shadow-2xl border-l border-border/70 rounded-none sm:static sm:w-full sm:max-w-4xl sm:max-h-[82vh] sm:h-auto sm:rounded-3xl sm:border sm:border-border/70 sm:shadow-2xl"
        >
          <!-- Top Bar inside Modal / Drawer -->
          <div class="h-13 px-4 sm:px-5 border-b border-border/60 flex items-center justify-between bg-muted/20 shrink-0">
            <div class="flex items-center gap-2">
              <MenuIcon class="size-4 text-foreground" />
              <span class="text-xs sm:text-sm font-extrabold text-foreground">
                دسته‌بندی کالاها
              </span>
            </div>

            <div class="flex items-center gap-2">
              <button
                v-if="activeFiltersCount > 0"
                @click="emit('clear-all')"
                type="button"
                class="text-xs text-muted-foreground hover:text-foreground px-2 py-1 rounded-lg transition-all cursor-pointer flex items-center gap-1 font-semibold"
              >
                <RotateCcwIcon class="size-3" />
                <span>حذف فیلترها</span>
              </button>

              <button 
                @click="handleClose"
                class="size-8 rounded-full bg-secondary flex items-center justify-center hover:opacity-80 transition-opacity text-foreground cursor-pointer"
                title="بستن"
              >
                <XIcon class="size-4" />
              </button>
            </div>
          </div>

          <!-- ================= MOBILE VIEW (Accordion Drawer) ================= -->
          <div class="flex sm:hidden flex-col flex-1 overflow-y-auto p-3 scrollbar-none no-scrollbar divide-y divide-border/40">
            <!-- All Items Option -->
            <button
              @click="handleSelectCategory(null)"
              type="button"
              :class="[
                'w-full py-3 px-3 text-xs font-bold flex items-center justify-between cursor-pointer rounded-xl transition-colors text-start',
                selectedCategoryId === null ? 'bg-muted text-foreground' : 'text-muted-foreground hover:text-foreground'
              ]"
            >
              <div class="flex items-center gap-2.5">
                <MenuIcon class="size-4 text-muted-foreground" />
                <span>همه کالاها</span>
              </div>
              <CheckIcon v-if="selectedCategoryId === null" class="size-4 text-foreground" />
            </button>

            <!-- Parent Categories Loop -->
            <div 
              v-for="cat in categories" 
              :key="cat.id" 
              class="py-1 flex flex-col"
            >
              <button
                @click="toggleMobileCategory(cat)"
                type="button"
                class="w-full py-2.5 px-3 text-xs font-bold flex items-center justify-between cursor-pointer text-start hover:bg-muted/40 rounded-xl transition-colors"
                :class="selectedCategoryId === cat.id ? 'text-foreground font-black' : 'text-foreground/90'"
              >
                <div class="flex items-center gap-2.5 truncate">
                  <component 
                    :is="getCategoryIcon(cat.slug)" 
                    class="size-4 text-muted-foreground shrink-0" 
                  />
                  <span class="truncate">{{ cat.name }}</span>
                </div>
                <template v-if="cat.children && cat.children.length > 0">
                  <ChevronDownIcon 
                    class="size-3.5 text-muted-foreground/70 transition-transform duration-200"
                    :class="expandedMobileCatId === cat.id ? 'rotate-180' : ''" 
                  />
                </template>
                <template v-else>
                  <ChevronLeftIcon class="size-3 text-muted-foreground/50" />
                </template>
              </button>

              <!-- Mobile Accordion Subcategories -->
              <div 
                v-if="cat.children && cat.children.length > 0 && expandedMobileCatId === cat.id"
                class="pe-2 ps-8 py-1.5 flex flex-col gap-1.5 bg-muted/20 rounded-xl mt-1"
              >
                <!-- Direct link to whole category -->
                <button
                  @click="handleSelectCategory(cat.id)"
                  type="button"
                  class="text-xs font-bold text-start py-1.5 px-2 text-foreground/80 hover:text-foreground cursor-pointer flex items-center gap-1.5"
                >
                  <span class="h-2.5 w-0.5 rounded-full bg-foreground/60 shrink-0" />
                  <span>همه محصولات {{ cat.name }}</span>
                </button>

                <!-- Children links -->
                <button
                  v-for="sub in cat.children"
                  :key="sub.id"
                  @click="handleSelectCategory(sub.id)"
                  type="button"
                  :class="[
                    'text-xs text-start py-1.5 px-2 rounded-lg transition-colors cursor-pointer flex items-center justify-between',
                    selectedCategoryId === sub.id 
                      ? 'bg-muted text-foreground font-black' 
                      : 'text-muted-foreground hover:text-foreground'
                  ]"
                >
                  <span>{{ sub.name }}</span>
                  <CheckIcon v-if="selectedCategoryId === sub.id" class="size-3 text-foreground" />
                </button>
              </div>
            </div>
          </div>

          <!-- ================= DESKTOP VIEW (Two-Column Digikala Mega-Menu) ================= -->
          <div class="hidden sm:flex flex-1 overflow-hidden divide-x divide-x-reverse divide-border/60">
            
            <!-- Right Column: Main Category List -->
            <div class="w-60 bg-muted/15 p-2 overflow-y-auto shrink-0 scrollbar-none no-scrollbar flex flex-col gap-1">
              <!-- Option: All Categories -->
              <button
                @click="handleSelectCategory(null)"
                @mouseenter="activeHoverCategoryId = null"
                type="button"
                :class="[
                  'w-full px-3 py-2.5 rounded-xl text-xs font-semibold flex items-center justify-between transition-all cursor-pointer text-start',
                  selectedCategoryId === null
                    ? 'bg-muted text-foreground font-bold shadow-xs'
                    : 'text-muted-foreground hover:text-foreground hover:bg-muted/40'
                ]"
              >
                <div class="flex items-center gap-2">
                  <MenuIcon class="size-4 shrink-0 text-muted-foreground" />
                  <span>همه کالاها</span>
                </div>
                <CheckIcon v-if="selectedCategoryId === null" class="size-3.5 text-foreground" />
              </button>

              <!-- Main Categories -->
              <button
                v-for="cat in categories"
                :key="cat.id"
                @click="handleSelectCategory(cat.id)"
                @mouseenter="activeHoverCategoryId = cat.id"
                type="button"
                :class="[
                  'w-full px-3 py-2.5 rounded-xl text-xs font-semibold flex items-center justify-between transition-all cursor-pointer text-start',
                  currentParentCategory?.id === cat.id
                    ? 'bg-card text-foreground font-bold shadow-xs border border-border/70 border-r-2 border-r-foreground'
                    : 'text-muted-foreground hover:text-foreground hover:bg-muted/30 border border-transparent'
                ]"
              >
                <div class="flex items-center gap-2.5 truncate">
                  <component 
                    :is="getCategoryIcon(cat.slug)" 
                    class="size-4 shrink-0"
                    :class="currentParentCategory?.id === cat.id ? 'text-foreground' : 'text-muted-foreground/70'"
                  />
                  <span class="truncate">{{ cat.name }}</span>
                </div>
                <ChevronLeftIcon class="size-3 text-muted-foreground/50 shrink-0" />
              </button>
            </div>

            <!-- Left Panel: Subcategories & Detailed Filter Options -->
            <div class="flex-1 p-5 overflow-y-auto flex flex-col justify-between gap-5 text-start scrollbar-none no-scrollbar bg-card">
              <div v-if="currentParentCategory" class="flex flex-col gap-4">
                <!-- Top Header: "مشاهده همه کتب [نام دسته] >" -->
                <button
                  @click="handleSelectCategory(currentParentCategory.id)"
                  type="button"
                  class="self-start text-xs font-extrabold text-foreground hover:underline flex items-center gap-1 cursor-pointer"
                >
                  <span>همه محصولات {{ currentParentCategory.name }}</span>
                  <ChevronLeftIcon class="size-3.5" />
                </button>

                <!-- Subcategories Grid (Digikala Style with subtle vertical pipe indicator) -->
                <div 
                  v-if="currentParentCategory.children && currentParentCategory.children.length > 0"
                  class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-5 pt-1"
                >
                  <div 
                    v-for="sub in currentParentCategory.children" 
                    :key="sub.id"
                    class="flex flex-col gap-2"
                  >
                    <button
                      @click="handleSelectCategory(sub.id)"
                      type="button"
                      :class="[
                        'text-xs font-bold flex items-center gap-1.5 text-start cursor-pointer hover:text-foreground transition-colors',
                        selectedCategoryId === sub.id ? 'text-foreground font-black' : 'text-foreground/80'
                      ]"
                    >
                      <span class="h-3 w-0.5 rounded-full bg-border shrink-0" />
                      <span>{{ sub.name }}</span>
                      <ChevronLeftIcon class="size-3 text-muted-foreground/60" />
                    </button>
                  </div>
                </div>

                <div v-else class="text-xs text-muted-foreground py-4">
                  محصولات این دسته‌بندی به‌صورت یکپارچه در دسترس هستند.
                </div>
              </div>

              <!-- Desktop Bottom Filter Quick Toggles -->
              <div class="pt-4 border-t border-border/50 flex flex-wrap items-center justify-between gap-3 text-xs text-muted-foreground">
                <div class="flex flex-wrap items-center gap-3">
                  <label class="flex items-center gap-2 cursor-pointer select-none text-foreground hover:text-foreground transition-colors">
                    <input 
                      type="checkbox" 
                      :checked="selectedDealType === 'donation'"
                      @change="(e: any) => emit('update:selectedDealType', e.target.checked ? 'donation' : 'all')"
                      class="rounded border-border accent-foreground size-4"
                    />
                    <span class="text-xs font-semibold">فقط کالاهای اهدایی</span>
                  </label>

                  <label class="flex items-center gap-2 cursor-pointer select-none text-foreground hover:text-foreground transition-colors">
                    <input 
                      type="checkbox" 
                      :checked="selectedDeliveryType === 'digital'"
                      @change="(e: any) => emit('update:selectedDeliveryType', e.target.checked ? 'digital' : 'all')"
                      class="rounded border-border accent-foreground size-4"
                    />
                    <span class="text-xs font-semibold">فقط دانلودی</span>
                  </label>

                  <label class="flex items-center gap-2 cursor-pointer select-none text-foreground hover:text-foreground transition-colors">
                    <input 
                      type="checkbox" 
                      :checked="inStockOnly"
                      @change="(e: any) => emit('update:inStockOnly', e.target.checked)"
                      class="rounded border-border accent-foreground size-4"
                    />
                    <span class="text-xs font-semibold">فقط کالاهای موجود</span>
                  </label>
                </div>

                <button
                  @click="handleClose"
                  type="button"
                  class="px-4 py-2 rounded-xl bg-foreground text-background text-xs font-bold cursor-pointer hover:opacity-90 transition-all shadow-xs"
                >
                  مشاهده نتایج ({{ totalItemsCount }} کالا)
                </button>
              </div>

            </div>

          </div>

          <!-- Bottom Footer for Mobile View -->
          <div class="sm:hidden p-3 border-t border-border/60 bg-muted/20 flex flex-col gap-2 shrink-0">
            <div class="flex items-center justify-between gap-2 text-xs">
              <label class="flex items-center gap-1.5 cursor-pointer select-none text-foreground text-[11px]">
                <input 
                  type="checkbox" 
                  :checked="selectedDealType === 'donation'"
                  @change="(e: any) => emit('update:selectedDealType', e.target.checked ? 'donation' : 'all')"
                  class="rounded border-border accent-foreground size-3.5"
                />
                <span>اهدایی</span>
              </label>

              <label class="flex items-center gap-1.5 cursor-pointer select-none text-foreground text-[11px]">
                <input 
                  type="checkbox" 
                  :checked="selectedDeliveryType === 'digital'"
                  @change="(e: any) => emit('update:selectedDeliveryType', e.target.checked ? 'digital' : 'all')"
                  class="rounded border-border accent-foreground size-3.5"
                />
                <span>دانلودی</span>
              </label>

              <label class="flex items-center gap-1.5 cursor-pointer select-none text-foreground text-[11px]">
                <input 
                  type="checkbox" 
                  :checked="inStockOnly"
                  @change="(e: any) => emit('update:inStockOnly', e.target.checked)"
                  class="rounded border-border accent-foreground size-3.5"
                />
                <span>موجود</span>
              </label>
            </div>

            <button
              @click="handleClose"
              type="button"
              class="w-full py-2.5 rounded-xl bg-foreground text-background text-xs font-bold cursor-pointer hover:opacity-90 transition-all text-center"
            >
              مشاهده نتایج ({{ totalItemsCount }} کالا)
            </button>
          </div>

        </div>
      </transition>
    </div>
  </Teleport>
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

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Mobile Slide-out from Corner (< 640px) */
@media (max-width: 639px) {
  .slide-corner-enter-active,
  .slide-corner-leave-active {
    transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  }
  .slide-corner-enter-from,
  .slide-corner-leave-to {
    transform: translateX(100%);
  }
}

/* Desktop Centered Modal Pop-up (>= 640px) */
@media (min-width: 640px) {
  .slide-corner-enter-active,
  .slide-corner-leave-active {
    transition: opacity 0.2s ease, transform 0.2s ease;
  }
  .slide-corner-enter-from,
  .slide-corner-leave-to {
    opacity: 0;
    transform: scale(0.96);
  }
}
</style>
