<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from 'vue'
import { 
  ArrowRightIcon, 
  SearchIcon,
  MoreVerticalIcon,
  XIcon
} from '@lucide/vue'
import TopicSettingsMenu from './TopicSettingsMenu.vue'
import { Button } from '@/components/ui/button'

// Props configuration
const props = withDefaults(defineProps<{
  isInnerPage?: boolean
  title?: string
  innerTitle?: string
  loading?: boolean
  error?: boolean
  showOptionsButton?: boolean
  showSearchButton?: boolean
  searchQuery?: string
}>(), {
  isInnerPage: false,
  title: 'تفکر',
  innerTitle: 'پشتیبانی',
  loading: false,
  error: false,
  showOptionsButton: true,
  showSearchButton: false,
  searchQuery: ''
})

const emit = defineEmits<{
  (e: 'back'): void
  (e: 'actionClick', actionName: string): void
  (e: 'edit-topic'): void
  (e: 'delete-topic'): void
  (e: 'topic-connections'): void
  (e: 'update:searchQuery', val: string): void
}>()

// Timer logic to fade out 'اتصال برقرار است' after 4 seconds
const showStatus = ref(true)
let statusTimer: any = null

const startStatusTimer = () => {
  if (statusTimer) clearTimeout(statusTimer)
  showStatus.value = true
  statusTimer = setTimeout(() => {
    showStatus.value = false
  }, 4000)
}

onMounted(() => {
  startStatusTimer()
})

watch(() => props.isInnerPage, (newVal) => {
  if (!newVal) {
    // Navigated back to Home - restart status fade timer
    startStatusTimer()
  } else {
    // Navigated to Inner page - show status instantly, clear timer
    showStatus.value = true
    if (statusTimer) clearTimeout(statusTimer)
  }
})

// Options Menu Dropdown State and Handlers
const triggerRect = ref<DOMRect | null>(null)
const isMenuOpen = ref(false)

const handleOptionsClick = (event: MouseEvent) => {
  const target = event.currentTarget as HTMLElement
  if (target) {
    triggerRect.value = target.getBoundingClientRect()
    isMenuOpen.value = true
  }
}

// Search Interaction States & Methods
const isSearchActive = ref(false)
const searchInputRef = ref<HTMLInputElement | null>(null)

const activateSearch = async () => {
  isSearchActive.value = true
  await nextTick()
  if (searchInputRef.value) {
    searchInputRef.value.focus()
  }
  emit('actionClick', 'search')
}

const deactivateSearch = () => {
  isSearchActive.value = false
  emit('update:searchQuery', '')
}

const clearSearch = async () => {
  emit('update:searchQuery', '')
  await nextTick()
  if (searchInputRef.value) {
    searchInputRef.value.focus()
  }
}

const onSearchInput = (event: Event) => {
  const target = event.target as HTMLInputElement
  emit('update:searchQuery', target.value)
}

// Watchers
watch(() => props.showSearchButton, (newVal) => {
  if (!newVal && isSearchActive.value) {
    deactivateSearch()
  }
})
</script>

<template>
  <div class="w-full flex items-center text-right select-none font-sans" dir="rtl">
    
    <!-- Detachable Back Button (RTL, right-aligned) -->
    <button
      @click="emit('back')"
      :class="[
        'h-11 rounded-2xl bg-background/60 backdrop-blur-md flex items-center justify-center text-foreground hover:bg-muted/80 active:scale-95 transition-all duration-300 ease-out shrink-0 cursor-pointer shadow-xs p-0 border outline-none',
        props.isInnerPage 
          ? 'w-11 opacity-100 ml-1 border-border/60' 
          : 'w-0 opacity-0 ml-0 border-transparent overflow-hidden pointer-events-none'
      ]"
      title="بازگشت"
    >
      <ArrowRightIcon class="size-4 text-foreground/80 transition-transform group-hover:-translate-x-0.5" />
    </button>

    <!-- Main Header Card Bar -->
    <div
      :class="[
        'flex-1 rounded-2xl border bg-background/60 backdrop-blur-md flex items-center justify-between px-3.5 transition-all duration-300 relative overflow-hidden shadow-xs',
        isInnerPage ? 'border-border/60' : 'border-border/80',
        isSearchActive ? 'h-[50px]' : 'h-11'
      ]"
    >
      <!-- Subtle Loading Bar Progress at the bottom -->
      <div
        v-if="loading"
        class="absolute bottom-0 left-0 right-0 h-0.5 bg-primary/20 overflow-hidden"
      >
        <div class="absolute inset-y-0 bg-primary w-1/3 animate-infinite-loading" />
      </div>

      <transition name="header-content-fade" mode="out-in">
        <!-- Normal Mode Header Content -->
        <div v-if="!isSearchActive" class="w-full flex items-center justify-between" key="normal">
          <!-- Title & Status Section (RTL: right side) -->
          <div class="flex items-center gap-2">
            <!-- Dynamic Error Glow Indicator -->
            <span 
              v-if="error" 
              class="size-2 rounded-full bg-destructive animate-pulse shrink-0" 
              title="خطای ارتباطی"
            />
            
            <div class="flex flex-col text-right">
              <span class="text-xs font-extrabold text-foreground transition-all duration-300">
                {{ isInnerPage ? innerTitle : title }}
              </span>
              <transition name="status-fade">
                <span 
                  v-if="loading"
                  class="text-[8.5px] font-medium transition-all duration-300 mt-0.5 text-muted-foreground block overflow-hidden"
                >
                  در حال اتصال...
                </span>
              </transition>
            </div>
          </div>

          <!-- Actions Section (RTL: left side) -->
          <div v-if="!isInnerPage && showSearchButton" class="flex items-center gap-1">
            <slot name="actions">
              <Button 
                @click="activateSearch"
                variant="ghost"
                class="size-7.5 rounded-md hover:bg-muted/80 flex items-center justify-center text-muted-foreground hover:text-foreground transition-colors cursor-pointer p-0"
                title="جستجو"
              >
                <SearchIcon class="size-4" />
              </Button>
            </slot>
          </div>
        </div>

        <!-- Search Mode Header Content -->
        <div v-else class="w-full flex items-center gap-2" key="search" dir="rtl">
          <SearchIcon class="size-4 text-primary shrink-0 transition-colors" />
          
          <input
            ref="searchInputRef"
            :value="searchQuery"
            @input="onSearchInput"
            type="text"
            placeholder="جستجو در تاپیک‌ها..."
            class="flex-1 bg-transparent border-none outline-none text-xs font-bold text-foreground placeholder:text-muted-foreground/60 w-full font-sans py-1 focus:outline-none focus:ring-0 focus:border-none focus-visible:outline-none focus-visible:ring-0 focus-visible:ring-offset-0 focus-visible:border-none"
            @keydown.esc="deactivateSearch"
          />

          <div class="flex items-center gap-1 shrink-0">
            <!-- Clear input button (only if searchQuery is not empty) -->
            <button
              v-if="searchQuery"
              @click.stop="clearSearch"
              class="size-6 rounded-md flex items-center justify-center hover:bg-muted/80 text-muted-foreground hover:text-foreground active:scale-95 transition-all cursor-pointer border-0"
              title="پاک کردن متن"
            >
              <XIcon class="size-3 shrink-0" />
            </button>
            
            <!-- Separator line -->
            <div v-if="searchQuery" class="w-px h-4 bg-border/80" />

            <!-- Close / Cancel search button -->
            <button
              @click.stop="deactivateSearch"
              class="size-7.5 rounded-md hover:bg-muted/80 flex items-center justify-center text-muted-foreground hover:text-foreground active:scale-95 transition-colors cursor-pointer border-0"
              title="بستن جستجو"
            >
              <XIcon class="size-4 shrink-0" />
            </button>
          </div>
        </div>
      </transition>

    </div>

    <!-- Detachable Options Button (RTL, left-aligned) -->
    <button
      @click="handleOptionsClick"
      :class="[
        'h-11 rounded-2xl bg-background/60 backdrop-blur-md flex items-center justify-center text-foreground hover:bg-muted/80 active:scale-95 transition-all duration-300 ease-out shrink-0 cursor-pointer shadow-xs p-0 border outline-none',
        props.isInnerPage && props.showOptionsButton
          ? 'w-11 opacity-100 mr-1 border-border/60' 
          : 'w-0 opacity-0 mr-0 border-transparent overflow-hidden pointer-events-none'
      ]"
      title="تنظیمات تاپیک"
    >
      <MoreVerticalIcon class="size-4 text-foreground/80" />
    </button>
  </div>

  <!-- Teleported Options Dropdown Menu -->
  <Teleport to="body">
    <TopicSettingsMenu
      :isOpen="isMenuOpen"
      :triggerRect="triggerRect"
      @close="isMenuOpen = false"
      @edit="emit('edit-topic')"
      @connections="emit('topic-connections')"
      @delete="emit('delete-topic')"
    />
  </Teleport>
</template>

<style scoped>
@keyframes loading-progress {
  0% { transform: translateX(250%); }
  100% { transform: translateX(-250%); }
}

.animate-infinite-loading {
  animation: loading-progress 1.6s infinite linear;
}

/* Status text fade transitions */
.status-fade-enter-active,
.status-fade-leave-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  max-height: 15px;
}

.status-fade-enter-from,
.status-fade-leave-to {
  opacity: 0;
  max-height: 0px;
  transform: translateY(-2px);
  margin-top: 0px;
}

.status-fade-enter-to,
.status-fade-leave-from {
  opacity: 1;
  max-height: 15px;
  transform: translateY(0);
  margin-top: 2px;
}

/* Header search transition */
.header-content-fade-enter-active,
.header-content-fade-leave-active {
  transition: all 0.2s ease-in-out;
}

.header-content-fade-enter-from,
.header-content-fade-leave-to {
  opacity: 0;
  transform: translateY(2px);
}

.header-content-fade-enter-to,
.header-content-fade-leave-from {
  opacity: 1;
  transform: translateY(0);
}
</style>
