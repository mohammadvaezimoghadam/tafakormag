<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useLanguageStore } from '@/stores/languageStore'
import { cn } from '@/lib/utils'
import { ChevronLeftIcon, ChevronRightIcon } from '@lucide/vue'

const props = withDefaults(
  defineProps<{
    trackClass?: string
    layout?: 'flex' | 'grid'
  }>(),
  {
    trackClass: 'gap-2.5',
    layout: 'flex',
  }
)

const languageStore = useLanguageStore()

const trackRef = ref<HTMLElement | null>(null)
const canScrollLeft = ref(false)
const canScrollRight = ref(false)

let resizeObserver: ResizeObserver | null = null
let mutationObserver: MutationObserver | null = null

const computedTrackClass = computed(() =>
  cn(
    props.layout === 'grid'
      ? 'grid grid-flow-col items-stretch overflow-x-auto pb-2 snap-x snap-mandatory scroll-smooth [scrollbar-width:none] [&::-webkit-scrollbar]:hidden'
      : 'flex items-stretch overflow-x-auto pb-2 snap-x scroll-smooth [scrollbar-width:none] [&::-webkit-scrollbar]:hidden',
    props.trackClass
  )
)

const updateScrollState = () => {
  const el = trackRef.value
  if (!el) {
    canScrollLeft.value = false
    canScrollRight.value = false
    return
  }

  const maxScroll = el.scrollWidth - el.clientWidth
  if (maxScroll <= 4) {
    canScrollLeft.value = false
    canScrollRight.value = false
    return
  }

  const isRtl = getComputedStyle(el).direction === 'rtl'
  if (isRtl) {
    // Standard CSSOM View in RTL: scrollLeft starts at 0 (right) and decreases to -maxScroll (left)
    const offsetFromStart = Math.abs(el.scrollLeft)
    canScrollRight.value = offsetFromStart > 4
    canScrollLeft.value = offsetFromStart < maxScroll - 4
  } else {
    canScrollLeft.value = el.scrollLeft > 4
    canScrollRight.value = el.scrollLeft < maxScroll - 4
  }
}

const getStepDistance = (el: HTMLElement): number => {
  if (props.layout === 'grid') {
    const firstCard = el.firstElementChild as HTMLElement | null
    if (firstCard) {
      const style = getComputedStyle(el)
      const gap = parseFloat(style.columnGap || style.gap || '0') || 0
      const cardWidth = firstCard.getBoundingClientRect().width
      const stride = cardWidth + gap
      if (stride > 0) {
        const visibleCount = Math.max(1, Math.round((el.clientWidth + gap) / stride))
        return Math.round(visibleCount * stride)
      }
    }
  }
  return Math.max(220, Math.round(el.clientWidth * 0.72))
}

const scrollHorizontal = (direction: -1 | 1) => {
  const el = trackRef.value
  if (!el) return
  const step = getStepDistance(el)
  el.scrollBy({
    left: direction * step,
    behavior: 'smooth',
  })
}

onMounted(async () => {
  await nextTick()
  updateScrollState()

  const el = trackRef.value
  if (!el) return

  if (typeof ResizeObserver !== 'undefined') {
    resizeObserver = new ResizeObserver(() => {
      updateScrollState()
    })
    resizeObserver.observe(el)
  }

  if (typeof MutationObserver !== 'undefined') {
    mutationObserver = new MutationObserver(() => {
      updateScrollState()
    })
    mutationObserver.observe(el, { childList: true })
  }

  window.addEventListener('resize', updateScrollState, { passive: true })
})

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  mutationObserver?.disconnect()
  window.removeEventListener('resize', updateScrollState)
})
</script>

<template>
  <div class="relative group/slider">
    <div
      ref="trackRef"
      @scroll.passive="updateScrollState"
      :class="computedTrackClass"
    >
      <slot />
    </div>

    <button
      v-if="canScrollRight"
      type="button"
      @click="scrollHorizontal(1)"
      :aria-label="languageStore.t('اسکرول به راست', 'Scroll right')"
      class="absolute top-1/2 -translate-y-1/2 right-1.5 z-10 size-8 rounded-full bg-background/90 dark:bg-card/90 backdrop-blur-md border border-border/70 text-foreground shadow-md hover:bg-primary hover:text-primary-foreground hover:border-primary active:scale-95 transition-all flex items-center justify-center cursor-pointer"
    >
      <ChevronRightIcon class="size-4" />
    </button>

    <button
      v-if="canScrollLeft"
      type="button"
      @click="scrollHorizontal(-1)"
      :aria-label="languageStore.t('اسکرول به چپ', 'Scroll left')"
      class="absolute top-1/2 -translate-y-1/2 left-1.5 z-10 size-8 rounded-full bg-background/90 dark:bg-card/90 backdrop-blur-md border border-border/70 text-foreground shadow-md hover:bg-primary hover:text-primary-foreground hover:border-primary active:scale-95 transition-all flex items-center justify-center cursor-pointer"
    >
      <ChevronLeftIcon class="size-4" />
    </button>
  </div>
</template>
