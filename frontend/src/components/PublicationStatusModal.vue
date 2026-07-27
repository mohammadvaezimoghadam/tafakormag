<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  SendIcon, 
  CalendarIcon, 
  CheckCircle2Icon, 
  XCircleIcon, 
  XIcon,
  LayersIcon
} from '@lucide/vue'
import { useLanguageStore } from '@/stores/languageStore'
import * as api from '@/api'

const languageStore = useLanguageStore()

interface Props {
  isOpen: boolean
  postId?: number | string
  post?: any
  publishedPlatforms?: string[]
  telegramMessageIds?: Record<string, any>
  baleMessageIds?: Record<string, any>
  createdAt?: string | null
}

const props = withDefaults(defineProps<Props>(), {
  isOpen: false,
  postId: undefined,
  post: null,
  publishedPlatforms: () => [],
  telegramMessageIds: () => ({}),
  baleMessageIds: () => ({}),
  createdAt: null
})

const emit = defineEmits<{
  (e: 'update:isOpen', value: boolean): void
  (e: 'close'): void
}>()

const localIsOpen = computed({
  get: () => props.isOpen,
  set: (val) => emit('update:isOpen', val)
})

const fetchedPostDetails = ref<any>(null)

const fetchFreshStatus = async () => {
  const targetId = props.postId || props.post?.id
  if (!targetId) return
  try {
    const res = await api.fetchPostDetails(targetId)
    if (res.data) {
      fetchedPostDetails.value = res.data
    }
  } catch (e) {
    // Fallback to local props if fetch fails
  }
}

watch(() => props.isOpen, (newVal) => {
  if (newVal) {
    fetchFreshStatus()
  }
}, { immediate: true })

// Ultra-safe platform list extraction with array & string checks
const effectivePlatforms = computed<string[]>(() => {
  if (fetchedPostDetails.value?.published_platforms && Array.isArray(fetchedPostDetails.value.published_platforms)) {
    return fetchedPostDetails.value.published_platforms
  }
  let platforms: any = props.publishedPlatforms || props.post?.publishedPlatforms || props.post?.published_platforms
  if (typeof platforms === 'string') {
    try { platforms = JSON.parse(platforms) } catch (e) { platforms = [platforms] }
  }
  if (Array.isArray(platforms)) return platforms as string[]
  return []
})

// Safe null/undefined object extraction for telegram_message_ids
const effectiveTelegramMessageIds = computed<Record<string, any>>(() => {
  let ids = fetchedPostDetails.value?.telegram_message_ids || props.telegramMessageIds || props.post?.telegramMessageIds || props.post?.telegram_message_ids
  if (typeof ids === 'string') {
    try { ids = JSON.parse(ids) } catch (e) {}
  }
  if (ids && typeof ids === 'object' && !Array.isArray(ids)) return ids
  return {}
})

// Safe null/undefined object extraction for bale_message_ids
const effectiveBaleMessageIds = computed<Record<string, any>>(() => {
  let ids = fetchedPostDetails.value?.bale_message_ids || props.baleMessageIds || props.post?.baleMessageIds || props.post?.bale_message_ids
  if (typeof ids === 'string') {
    try { ids = JSON.parse(ids) } catch (e) {}
  }
  if (ids && typeof ids === 'object' && !Array.isArray(ids)) return ids
  return {}
})

const effectiveCreatedAt = computed(() => {
  if (props.createdAt) return props.createdAt
  if (props.post?.timestamp) return props.post.timestamp
  if (props.post?.created_at) return props.post.created_at
  return ''
})

// Robust boolean checks with fallbacks
const hasTelegram = computed(() => {
  const inPlatforms = (effectivePlatforms.value || []).includes('telegram')
  const inMsgIds = Boolean(Object.keys(effectiveTelegramMessageIds.value || {}).length)
  return inPlatforms || inMsgIds
})

const hasBale = computed(() => {
  const inPlatforms = (effectivePlatforms.value || []).includes('bale')
  const inMsgIds = Boolean(Object.keys(effectiveBaleMessageIds.value || {}).length)
  return inPlatforms || inMsgIds
})

const formattedDate = computed(() => {
  const dt = effectiveCreatedAt.value
  if (!dt) return languageStore.t('ثبت شده در دیتابیس', 'Recorded in DB')
  try {
    const d = new Date(dt)
    if (isNaN(d.getTime())) return dt
    return d.toLocaleString(languageStore.isFa ? 'fa-IR' : 'en-US', {
      dateStyle: 'medium',
      timeStyle: 'short'
    })
  } catch (e) {
    return dt
  }
})

const handleClose = () => {
  emit('close')
  localIsOpen.value = false
}
</script>

<template>
  <Dialog v-model:open="localIsOpen">
    <DialogContent 
      :show-close-button="false" 
      class="max-w-[420px] p-0 overflow-hidden flex flex-col text-start font-sans border-0 shadow-2xl" 
      :dir="languageStore.dir"
    >
      <!-- Header Banner -->
      <DialogHeader class="px-5 py-4 bg-gradient-to-br from-primary/15 via-primary/10 to-transparent flex flex-row items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="size-9 rounded-2xl bg-primary/20 text-primary flex items-center justify-center shadow-xs shrink-0">
            <SendIcon class="size-4.5" />
          </div>
          <DialogTitle class="text-xs font-black text-foreground font-sans">
            {{ languageStore.t('وضعیت انتشار پست', 'Publication Status') }}
          </DialogTitle>
        </div>
        
        <button 
          @click="handleClose"
          class="size-7 rounded-xl flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-muted/80 transition-colors cursor-pointer border-0 outline-none shrink-0"
          :title="languageStore.t('بستن', 'Close')"
        >
          <XIcon class="size-4" />
        </button>
      </DialogHeader>

      <!-- Content Body -->
      <div class="p-5 flex flex-col gap-4">
        <!-- Date Info Card -->
        <div class="flex items-center justify-between p-3 rounded-2xl bg-muted/20 border border-border/40 font-sans">
          <div class="flex items-center gap-2 text-muted-foreground">
            <CalendarIcon class="size-4 text-primary" />
            <span class="text-xs font-medium">{{ languageStore.t('تاریخ ثبت اولیه:', 'Created Date:') }}</span>
          </div>
          <span class="text-xs font-bold text-foreground">{{ formattedDate }}</span>
        </div>

        <!-- Platforms Publication Status List -->
        <div class="flex flex-col gap-2.5 font-sans">
          <span class="text-[11px] font-extrabold text-foreground flex items-center gap-1.5">
            <LayersIcon class="size-3.5 text-primary" />
            <span>{{ languageStore.t('پلتفرم‌های هدف:', 'Target Platforms:') }}</span>
          </span>

          <!-- 1. Tafakor Database Status -->
          <div class="flex items-center justify-between p-3 rounded-2xl border border-primary/20 bg-primary/5">
            <div class="flex items-center gap-2.5">
              <div class="size-7 rounded-lg bg-primary/10 text-primary flex items-center justify-center font-bold text-xs">
                {{ languageStore.t('تفکر', 'Tafakor') }}
              </div>
              <div class="flex flex-col text-start">
                <span class="text-xs font-bold text-foreground">
                  {{ languageStore.t('پلتفرم تفکر (دیتابیس)', 'Tafakor Platform (DB)') }}
                </span>
                <span class="text-[10px] text-muted-foreground">
                  {{ languageStore.t('پست اصلی در خط زمانی', 'Original post in timeline') }}
                </span>
              </div>
            </div>
            <Badge class="bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20 text-[10px] font-bold px-2.5 py-0.5 rounded-full flex items-center gap-1 font-sans">
              <CheckCircle2Icon class="size-3" />
              <span>{{ languageStore.t('منتشر شده', 'Published') }}</span>
            </Badge>
          </div>

          <!-- 2. Telegram Status -->
          <div 
            class="flex items-center justify-between p-3 rounded-2xl border transition-colors"
            :class="[
              hasTelegram 
                ? 'border-sky-500/30 bg-sky-500/5' 
                : 'border-border/30 bg-muted/10'
            ]"
          >
            <div class="flex items-center gap-2.5">
              <div class="size-7 rounded-lg bg-sky-500/10 text-sky-600 dark:text-sky-400 flex items-center justify-center font-black text-[10px]">
                TG
              </div>
              <div class="flex flex-col text-start">
                <span class="text-xs font-bold text-foreground">
                  {{ languageStore.t('پیام‌رسان تلگرام', 'Telegram Messenger') }}
                </span>
                <span class="text-[10px] text-muted-foreground">
                  {{ hasTelegram 
                    ? languageStore.t('سینک شده با چت تلگرام', 'Synced with Telegram chat')
                    : languageStore.t('عدم ارسال به تلگرام', 'Not sent to Telegram')
                  }}
                </span>
              </div>
            </div>
            <Badge 
              v-if="hasTelegram"
              class="bg-sky-500/10 text-sky-600 dark:text-sky-400 border-sky-500/20 text-[10px] font-bold px-2.5 py-0.5 rounded-full flex items-center gap-1 font-sans"
            >
              <CheckCircle2Icon class="size-3" />
              <span>{{ languageStore.t('منتشر شده', 'Published') }}</span>
            </Badge>
            <Badge 
              v-else
              variant="outline"
              class="text-muted-foreground border-border/40 text-[10px] font-medium px-2 py-0.5 rounded-full flex items-center gap-1 font-sans"
            >
              <XCircleIcon class="size-3 text-muted-foreground/60" />
              <span>{{ languageStore.t('منتشر نشده', 'Not Published') }}</span>
            </Badge>
          </div>

          <!-- 3. Bale Status -->
          <div 
            class="flex items-center justify-between p-3 rounded-2xl border transition-colors"
            :class="[
              hasBale 
                ? 'border-emerald-500/30 bg-emerald-500/5' 
                : 'border-border/30 bg-muted/10'
            ]"
          >
            <div class="flex items-center gap-2.5">
              <div class="size-7 rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 flex items-center justify-center font-black text-[10px]">
                BL
              </div>
              <div class="flex flex-col text-start">
                <span class="text-xs font-bold text-foreground">
                  {{ languageStore.t('پیام‌رسان بله', 'Bale Messenger') }}
                </span>
                <span class="text-[10px] text-muted-foreground">
                  {{ hasBale 
                    ? languageStore.t('سینک شده با چت بله', 'Synced with Bale chat')
                    : languageStore.t('عدم ارسال به بله', 'Not sent to Bale')
                  }}
                </span>
              </div>
            </div>
            <Badge 
              v-if="hasBale"
              class="bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20 text-[10px] font-bold px-2.5 py-0.5 rounded-full flex items-center gap-1 font-sans"
            >
              <CheckCircle2Icon class="size-3" />
              <span>{{ languageStore.t('منتشر شده', 'Published') }}</span>
            </Badge>
            <Badge 
              v-else
              variant="outline"
              class="text-muted-foreground border-border/40 text-[10px] font-medium px-2 py-0.5 rounded-full flex items-center gap-1 font-sans"
            >
              <XCircleIcon class="size-3 text-muted-foreground/60" />
              <span>{{ languageStore.t('منتشر نشده', 'Not Published') }}</span>
            </Badge>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <DialogFooter class="px-5 py-3 bg-muted/30 border-t border-border/40 flex justify-end">
        <Button 
          type="button" 
          variant="outline" 
          size="sm" 
          class="text-xs font-bold rounded-2xl cursor-pointer font-sans" 
          @click="handleClose"
        >
          {{ languageStore.t('بستن', 'Close') }}
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
