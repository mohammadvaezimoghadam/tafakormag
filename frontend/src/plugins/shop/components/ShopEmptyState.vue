<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    type?: 'search' | 'books' | 'stations' | 'transfers'
    title?: string
    description?: string
    actionText?: string
  }>(),
  {
    type: 'search',
    title: '',
    description: '',
    actionText: '',
  }
)

const emit = defineEmits<{
  (e: 'action'): void
}>()

const defaultTitle = computed(() => {
  switch (props.type) {
    case 'search':
      return 'کتاب یا کالایی با این مشخصات یافت نشد'
    case 'books':
      return 'کتابی در این بخش وجود ندارد'
    case 'stations':
      return 'ایستگاهی در این موقعیت ثبت نشده است'
    case 'transfers':
      return 'هنوز سفری برای این کتاب ثبت نشده'
    default:
      return 'موردی یافت نشد'
  }
})

const defaultDescription = computed(() => {
  switch (props.type) {
    case 'search':
      return 'می‌توانید عنوان، نام نویسنده یا شابک را دوباره بررسی فرمایید.'
    case 'books':
      return 'شما می‌توانید اولین جلد کتاب را در چرخه تفاخر به اشتراک بگذارید.'
    case 'stations':
      return 'به‌زودی قفسه‌های جدید تفاخر در این منطقه افزوده خواهد شد.'
    case 'transfers':
      return 'با انتقال این کتاب به فرد دیگر، اولین برگ از سفرنامه آن ورق خواهد خورد.'
    default:
      return ''
  }
})
</script>

<template>
  <div class="flex flex-col items-center justify-center py-12 px-4 text-center select-none">
    <!-- Handcrafted Minimalist SVG Vector Line Art -->
    <div class="relative w-28 h-28 mb-4 flex items-center justify-center text-zinc-400 dark:text-zinc-600">
      
      <!-- 1. Search Empty State (Minimal Open Book & Fine Orbit Lens) -->
      <svg
        v-if="type === 'search'"
        viewBox="0 0 100 100"
        class="w-24 h-24 stroke-current fill-none stroke-[1.25] stroke-linecap-round stroke-linejoin-round"
      >
        <!-- Open book spine and pages -->
        <path d="M 50 32 L 50 72" />
        <path d="M 50 72 C 38 68 22 68 14 74 L 14 36 C 22 30 38 30 50 34 C 62 30 78 30 86 36 L 86 74 C 78 68 62 68 50 72 Z" />
        <!-- Page lines (subtle) -->
        <path d="M 22 44 C 30 42 40 42 46 45" stroke-dasharray="2 3" class="opacity-50" />
        <path d="M 22 53 C 30 51 40 51 46 54" stroke-dasharray="2 3" class="opacity-50" />
        <path d="M 54 45 C 60 42 70 42 78 44" stroke-dasharray="2 3" class="opacity-50" />
        <path d="M 54 54 C 60 51 70 51 78 53" stroke-dasharray="2 3" class="opacity-50" />
        <!-- Elegant subtle search lens ring overlapping corner -->
        <circle cx="72" cy="30" r="11" class="text-zinc-600 dark:text-zinc-400 stroke-[1.5]" />
        <line x1="80" y1="38" x2="89" y2="47" class="text-zinc-600 dark:text-zinc-400 stroke-[1.5]" />
      </svg>

      <!-- 2. Books Empty State (Two Clean Stacked Volumes) -->
      <svg
        v-else-if="type === 'books'"
        viewBox="0 0 100 100"
        class="w-24 h-24 stroke-current fill-none stroke-[1.25] stroke-linecap-round stroke-linejoin-round"
      >
        <!-- Bottom Book -->
        <rect x="22" y="56" width="56" height="14" rx="2" />
        <line x1="28" y1="56" x2="28" y2="70" class="opacity-40" />
        <path d="M 36 63 L 68 63" stroke-dasharray="3 3" class="opacity-50" />

        <!-- Top Book (Slightly narrower, centered) -->
        <rect x="26" y="38" width="48" height="14" rx="2" />
        <line x1="32" y1="38" x2="32" y2="52" class="opacity-40" />
        <path d="M 40 45 L 64 45" stroke-dasharray="3 3" class="opacity-50" />

        <!-- Small bookmark ribbon hanging out -->
        <path d="M 46 38 L 46 48 L 50 45 L 54 48 L 54 38" class="text-zinc-500 dark:text-zinc-400 fill-zinc-100 dark:fill-zinc-800 stroke-[1.2]" />
      </svg>

      <!-- 3. Stations Empty State (Public Kiosk / Architectural Shelf) -->
      <svg
        v-else-if="type === 'stations'"
        viewBox="0 0 100 100"
        class="w-24 h-24 stroke-current fill-none stroke-[1.25] stroke-linecap-round stroke-linejoin-round"
      >
        <!-- Canopy / Roof -->
        <path d="M 24 38 L 50 24 L 76 38 Z" />
        <!-- Base pillars -->
        <line x1="28" y1="38" x2="28" y2="76" />
        <line x1="72" y1="38" x2="72" y2="76" />
        <!-- Foundation -->
        <line x1="20" y1="76" x2="80" y2="76" stroke-width="2" />
        <!-- Shelf tiers -->
        <line x1="28" y1="52" x2="72" y2="52" />
        <line x1="28" y1="64" x2="72" y2="64" />
        <!-- Tiny standing books on shelf -->
        <rect x="34" y="44" width="4" height="8" rx="0.5" class="opacity-40" />
        <rect x="39" y="42" width="4" height="10" rx="0.5" class="opacity-40" />
        <rect x="58" y="56" width="4" height="8" rx="0.5" class="opacity-40" />
        <rect x="63" y="55" width="4" height="9" rx="0.5" class="opacity-40" />
      </svg>

      <!-- 4. Transfers / Handover Empty State (Dual Curved Flow Arrows) -->
      <svg
        v-else
        viewBox="0 0 100 100"
        class="w-24 h-24 stroke-current fill-none stroke-[1.25] stroke-linecap-round stroke-linejoin-round"
      >
        <!-- Central circular journey path -->
        <path d="M 32 40 A 22 22 0 0 1 68 40" stroke-dasharray="3 3" />
        <path d="M 68 60 A 22 22 0 0 1 32 60" stroke-dasharray="3 3" />
        <!-- Hand / Exchange nodes -->
        <circle cx="28" cy="50" r="5" class="text-zinc-600 dark:text-zinc-400 stroke-[1.5]" />
        <circle cx="72" cy="50" r="5" class="text-zinc-600 dark:text-zinc-400 stroke-[1.5]" />
        <!-- Subtle arrowheads -->
        <path d="M 66 36 L 72 40 L 66 44" />
        <path d="M 34 56 L 28 60 L 34 64" />
      </svg>
    </div>

    <!-- Clean Typography without Clutter -->
    <h3 class="text-sm font-semibold text-zinc-800 dark:text-zinc-200 mb-1">
      {{ title || defaultTitle }}
    </h3>
    <p v-if="description || defaultDescription" class="text-xs text-zinc-500 dark:text-zinc-400 max-w-sm mb-4 leading-relaxed">
      {{ description || defaultDescription }}
    </p>

    <!-- Optional Minimal Action Button -->
    <button
      v-if="actionText"
      @click="emit('action')"
      type="button"
      class="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-medium border border-zinc-300 dark:border-zinc-700 hover:bg-zinc-100 dark:hover:bg-zinc-800 text-zinc-800 dark:text-zinc-200 transition-colors cursor-pointer"
    >
      <span>{{ actionText }}</span>
    </button>
  </div>
</template>

