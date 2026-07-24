<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Checkbox } from '@/components/ui/checkbox'
import { Label } from '@/components/ui/label'
import { AlertTriangleIcon, Trash2Icon, InfoIcon, XIcon } from '@lucide/vue'
import { useLanguageStore } from '@/stores/languageStore'
import { cn } from '@/lib/utils'

const languageStore = useLanguageStore()

export interface SelectiveDeleteOptions {
  delete_from_telegram: boolean
  delete_from_bale: boolean
  delete_from_db: boolean
}

interface Props {
  isOpen: boolean
  title?: string
  description?: string
  confirmText?: string
  cancelText?: string
  variant?: 'destructive' | 'warning' | 'info'
  // Selective deletion props
  isSelectiveDelete?: boolean
  post?: any
  publishedPlatforms?: string[]
  telegramMessageIds?: Record<string, any>
  baleMessageIds?: Record<string, any>
}

const props = withDefaults(defineProps<Props>(), {
  title: '',
  description: '',
  confirmText: '',
  cancelText: '',
  variant: 'destructive',
  isSelectiveDelete: undefined,
  post: null,
  publishedPlatforms: () => [],
  telegramMessageIds: () => ({}),
  baleMessageIds: () => ({})
})

const emit = defineEmits<{
  (e: 'update:isOpen', value: boolean): void
  (e: 'confirm', options?: SelectiveDeleteOptions): void
  (e: 'cancel'): void
}>()

const localIsOpen = computed({
  get: () => props.isOpen,
  set: (val) => emit('update:isOpen', val)
})

// Effective platforms & message IDs evaluation
const effectivePublishedPlatforms = computed<string[]>(() => {
  if (Array.isArray(props.publishedPlatforms) && props.publishedPlatforms.length > 0) return props.publishedPlatforms
  if (props.post?.publishedPlatforms && Array.isArray(props.post.publishedPlatforms)) return props.post.publishedPlatforms
  if (props.post?.published_platforms && Array.isArray(props.post.published_platforms)) return props.post.published_platforms
  return []
})

const effectiveTelegramMessageIds = computed<Record<string, any>>(() => {
  const ids = props.telegramMessageIds || props.post?.telegramMessageIds || props.post?.telegram_message_ids
  if (ids && typeof ids === 'object' && !Array.isArray(ids)) return ids
  return {}
})

const effectiveBaleMessageIds = computed<Record<string, any>>(() => {
  const ids = props.baleMessageIds || props.post?.baleMessageIds || props.post?.bale_message_ids
  if (ids && typeof ids === 'object' && !Array.isArray(ids)) return ids
  return {}
})

const hasTelegram = computed(() => {
  const inPlatforms = (effectivePublishedPlatforms.value || []).includes('telegram')
  const inMsgIds = Boolean(Object.keys(effectiveTelegramMessageIds.value || {}).length)
  return inPlatforms || inMsgIds
})

const hasBale = computed(() => {
  const inPlatforms = (effectivePublishedPlatforms.value || []).includes('bale')
  const inMsgIds = Boolean(Object.keys(effectiveBaleMessageIds.value || {}).length)
  return inPlatforms || inMsgIds
})

const isSelectiveMode = computed(() => {
  if (props.isSelectiveDelete !== undefined) return props.isSelectiveDelete
  return hasTelegram.value || hasBale.value
})

// Checkbox selection states
const deleteFromTelegram = ref(false)
const deleteFromBale = ref(false)
const deleteFromDb = ref(true)

watch(() => [props.isOpen, hasTelegram.value, hasBale.value], () => {
  if (props.isOpen) {
    deleteFromTelegram.value = hasTelegram.value
    deleteFromBale.value = hasBale.value
    deleteFromDb.value = true
  }
}, { immediate: true })

const isConfirmDisabled = computed(() => {
  if (isSelectiveMode.value) {
    const tgSelected = hasTelegram.value && deleteFromTelegram.value
    const baleSelected = hasBale.value && deleteFromBale.value
    const dbSelected = deleteFromDb.value
    return !tgSelected && !baleSelected && !dbSelected
  }
  return false
})

const handleConfirm = () => {
  if (isConfirmDisabled.value) return

  if (isSelectiveMode.value) {
    emit('confirm', {
      delete_from_telegram: hasTelegram.value ? deleteFromTelegram.value : false,
      delete_from_bale: hasBale.value ? deleteFromBale.value : false,
      delete_from_db: deleteFromDb.value
    })
  } else {
    emit('confirm')
  }
  localIsOpen.value = false
}

const handleCancel = () => {
  emit('cancel')
  localIsOpen.value = false
}

// Icon based on variant
const iconComponent = computed(() => {
  if (props.variant === 'warning') return AlertTriangleIcon
  if (props.variant === 'info') return InfoIcon
  return Trash2Icon
})

// Header Icon colors based on variant
const iconBgClass = computed(() => {
  if (props.variant === 'warning') return 'bg-amber-500/10 text-amber-500'
  if (props.variant === 'info') return 'bg-blue-500/10 text-blue-500'
  return 'bg-destructive/10 text-destructive'
})

// Header gradient background based on variant
const headerBgClass = computed(() => {
  if (props.variant === 'warning') return 'bg-gradient-to-br from-amber-500/10 to-amber-500/5'
  if (props.variant === 'info') return 'bg-gradient-to-br from-blue-500/10 to-blue-500/5'
  return 'bg-gradient-to-br from-destructive/10 to-destructive/5'
})

const confirmButtonVariant = computed(() => {
  if (props.variant === 'destructive') return 'destructive'
  return 'default'
})

const defaultConfirmText = computed(() => {
  if (props.confirmText) return props.confirmText
  return languageStore.isFa ? 'تایید و حذف' : 'Confirm & Delete'
})

const defaultCancelText = computed(() => {
  if (props.cancelText) return props.cancelText
  return languageStore.isFa ? 'انصراف' : 'Cancel'
})
</script>

<template>
  <Dialog v-model:open="localIsOpen">
    <DialogContent 
      :show-close-button="false" 
      class="max-w-[420px] p-0 overflow-hidden flex flex-col text-start font-sans" 
      :dir="languageStore.dir"
    >
      <!-- Header -->
      <DialogHeader :class="cn('px-5 py-4 border-b border-border/40 flex flex-row items-center justify-between', headerBgClass)">
        <div class="flex items-center gap-2">
          <div :class="cn('size-8 rounded-full flex items-center justify-center shadow-xs shrink-0', iconBgClass)">
            <component :is="iconComponent" class="size-4" />
          </div>
          <DialogTitle class="text-xs font-black text-foreground">
            {{ title }}
          </DialogTitle>
        </div>
        
        <button 
          @click="handleCancel"
          class="size-6.5 rounded-lg flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-muted/80 transition-colors cursor-pointer border-0 outline-none"
          :title="defaultCancelText"
        >
          <XIcon class="size-3.5" />
        </button>
      </DialogHeader>

      <!-- Body -->
      <div class="p-5 flex flex-col gap-4">
        <DialogDescription class="text-xs text-muted-foreground leading-relaxed font-medium block">
          {{ description }}
        </DialogDescription>

        <!-- Selective Deletion Controls & Status Badges -->
        <div v-if="isSelectiveMode" class="flex flex-col gap-3.5 bg-muted/20 border border-border/40 rounded-2xl p-3.5">
          <!-- Published Platforms Badges -->
          <div class="flex items-center justify-between gap-2">
            <span class="text-[11px] font-extrabold text-foreground">
              {{ languageStore.isFa ? 'پلتفرم‌های انتشار یافته:' : 'Published Platforms:' }}
            </span>
            <div class="flex items-center gap-1.5 flex-wrap">
              <!-- Telegram Badge -->
              <Badge 
                v-if="hasTelegram" 
                variant="secondary" 
                class="bg-sky-500/10 border-sky-500/20 text-sky-600 dark:text-sky-400 text-[10px] font-extrabold px-2 py-0.5 rounded-full flex items-center gap-1"
              >
                <span class="font-sans font-black text-[9px]">TG</span>
                <span>{{ languageStore.isFa ? 'تلگرام' : 'Telegram' }}</span>
              </Badge>
              
              <!-- Bale Badge -->
              <Badge 
                v-if="hasBale" 
                variant="secondary" 
                class="bg-emerald-500/10 border-emerald-500/20 text-emerald-600 dark:text-emerald-400 text-[10px] font-extrabold px-2 py-0.5 rounded-full flex items-center gap-1"
              >
                <span class="font-sans font-black text-[9px]">BL</span>
                <span>{{ languageStore.isFa ? 'بله' : 'Bale' }}</span>
              </Badge>

              <!-- Database/Tafakor Badge -->
              <Badge 
                variant="secondary" 
                class="bg-primary/10 border-primary/20 text-primary text-[10px] font-extrabold px-2 py-0.5 rounded-full flex items-center gap-1"
              >
                <span>{{ languageStore.isFa ? 'پلتفرم تفکر' : 'Tafakor Platform' }}</span>
              </Badge>
            </div>
          </div>

          <!-- Checkboxes for Selective Deletion -->
          <div class="flex flex-col gap-2 pt-2 border-t border-border/30">
            <!-- Telegram Checkbox -->
            <div 
              class="flex items-center justify-between p-2.5 rounded-xl border transition-colors select-none"
              :class="[
                hasTelegram 
                  ? 'border-border/60 bg-background/50 cursor-pointer hover:bg-muted/40' 
                  : 'border-border/20 bg-muted/20 opacity-50 cursor-not-allowed'
              ]"
              @click="hasTelegram && (deleteFromTelegram = !deleteFromTelegram)"
            >
              <div class="flex items-center gap-2.5">
                <Checkbox 
                  id="del-tg" 
                  :checked="deleteFromTelegram" 
                  :disabled="!hasTelegram"
                  @update:checked="(val: boolean | 'indeterminate') => deleteFromTelegram = val === true"
                />
                <Label 
                  for="del-tg" 
                  :class="[
                    'text-xs font-bold select-none cursor-pointer',
                    !hasTelegram ? 'cursor-not-allowed text-muted-foreground' : 'text-foreground'
                  ]"
                  @click.prevent
                >
                  {{ languageStore.isFa ? 'حذف از تلگرام' : 'Delete from Telegram' }}
                </Label>
              </div>
              <Badge v-if="!hasTelegram" variant="outline" class="text-[9px] text-muted-foreground border-border/40">
                {{ languageStore.isFa ? 'غیرفعال (منتشر نشده)' : 'Not published' }}
              </Badge>
            </div>

            <!-- Bale Checkbox -->
            <div 
              class="flex items-center justify-between p-2.5 rounded-xl border transition-colors select-none"
              :class="[
                hasBale 
                  ? 'border-border/60 bg-background/50 cursor-pointer hover:bg-muted/40' 
                  : 'border-border/20 bg-muted/20 opacity-50 cursor-not-allowed'
              ]"
              @click="hasBale && (deleteFromBale = !deleteFromBale)"
            >
              <div class="flex items-center gap-2.5">
                <Checkbox 
                  id="del-bale" 
                  :checked="deleteFromBale" 
                  :disabled="!hasBale"
                  @update:checked="(val: boolean | 'indeterminate') => deleteFromBale = val === true"
                />
                <Label 
                  for="del-bale" 
                  :class="[
                    'text-xs font-bold select-none cursor-pointer',
                    !hasBale ? 'cursor-not-allowed text-muted-foreground' : 'text-foreground'
                  ]"
                  @click.prevent
                >
                  {{ languageStore.isFa ? 'حذف از بله' : 'Delete from Bale' }}
                </Label>
              </div>
              <Badge v-if="!hasBale" variant="outline" class="text-[9px] text-muted-foreground border-border/40">
                {{ languageStore.isFa ? 'غیرفعال (منتشر نشده)' : 'Not published' }}
              </Badge>
            </div>

            <!-- DB Checkbox -->
            <div 
              class="flex items-center justify-between p-2.5 rounded-xl border border-border/60 bg-background/50 cursor-pointer hover:bg-muted/40 transition-colors select-none"
              @click="deleteFromDb = !deleteFromDb"
            >
              <div class="flex items-center gap-2.5">
                <Checkbox 
                  id="del-db" 
                  :checked="deleteFromDb" 
                  @update:checked="(val: boolean | 'indeterminate') => deleteFromDb = val === true"
                />
                <Label 
                  for="del-db" 
                  class="text-xs font-bold text-foreground select-none cursor-pointer"
                  @click.prevent
                >
                  {{ languageStore.isFa ? 'حذف از پلتفرم تفکر (دیتابیس)' : 'Delete from Tafakor Platform (DB)' }}
                </Label>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Footer Actions -->
      <DialogFooter class="px-5 py-3.5 bg-muted/20 border-t border-border/40 flex justify-end gap-2">
        <Button 
          type="button" 
          variant="outline" 
          size="sm" 
          class="text-xs font-bold rounded-2xl cursor-pointer" 
          @click="handleCancel"
        >
          {{ defaultCancelText }}
        </Button>
        <Button 
          type="button" 
          :variant="confirmButtonVariant" 
          size="sm" 
          :disabled="isConfirmDisabled"
          class="text-xs font-bold rounded-2xl cursor-pointer" 
          @click="handleConfirm"
        >
          <component :is="iconComponent" data-icon="inline-start" />
          {{ defaultConfirmText }}
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
