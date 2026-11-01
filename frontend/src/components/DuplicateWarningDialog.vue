<script setup lang="ts">
import { computed } from 'vue'
import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogFooter
} from '@/components/ui/alert-dialog'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  AlertTriangleIcon, 
  CalendarIcon, 
  RepeatIcon, 
  ExternalLinkIcon,
  XIcon,
  LayersIcon
} from '@lucide/vue'
import { useLanguageStore } from '@/stores/languageStore'

const languageStore = useLanguageStore()

interface Props {
  isOpen: boolean
  existingPostId?: string | number | null
  createdAt?: string | null
  publishedPlatforms?: string[]
}

const props = withDefaults(defineProps<Props>(), {
  isOpen: false,
  existingPostId: null,
  createdAt: null,
  publishedPlatforms: () => []
})

const emit = defineEmits<{
  (e: 'update:isOpen', value: boolean): void
  (e: 'cancel'): void
  (e: 'go-to-existing', postId: string | number | null): void
  (e: 'force-submit'): void
}>()

const localIsOpen = computed({
  get: () => props.isOpen,
  set: (val) => emit('update:isOpen', val)
})

const formattedDate = computed(() => {
  if (!props.createdAt) return languageStore.isFa ? 'پیش‌تر ثبت شده' : 'Previously published'
  try {
    const d = new Date(props.createdAt)
    if (isNaN(d.getTime())) return props.createdAt
    return d.toLocaleString(languageStore.isFa ? 'fa-IR' : 'en-US', {
      dateStyle: 'medium',
      timeStyle: 'short'
    })
  } catch (e) {
    return props.createdAt
  }
})

const hasTelegram = computed(() => props.publishedPlatforms.includes('telegram'))
const hasBale = computed(() => props.publishedPlatforms.includes('bale'))

const handleGoToExisting = () => {
  emit('go-to-existing', props.existingPostId)
  emit('cancel')
  localIsOpen.value = false
}

const handleForceSubmit = () => {
  emit('force-submit')
  localIsOpen.value = false
}

const handleCancel = () => {
  emit('cancel')
  localIsOpen.value = false
}
</script>

<template>
  <AlertDialog v-model:open="localIsOpen">
    <AlertDialogContent 
      class="max-w-[420px] p-0 overflow-hidden flex flex-col text-start font-sans rounded-3xl border border-border/80 dark:border-border/60 bg-card/95 backdrop-blur-2xl text-card-foreground shadow-[0_20px_50px_rgba(0,0,0,0.2)]"
      :dir="languageStore.dir"
    >
      <!-- Amber Header Banner -->
      <AlertDialogHeader class="px-5 py-4 bg-gradient-to-br from-amber-500/15 via-amber-500/10 to-transparent flex flex-row items-center justify-between border-b border-border/40">
        <div class="flex items-center gap-3">
          <div class="size-9 rounded-xl bg-amber-500/20 text-amber-600 dark:text-amber-400 flex items-center justify-center shadow-xs shrink-0">
            <AlertTriangleIcon class="size-5" />
          </div>
          <AlertDialogTitle class="text-xs font-black text-amber-700 dark:text-amber-300 font-sans">
            {{ languageStore.isFa ? 'پست تکراری تشخیص داده شد' : 'Duplicate Post Detected' }}
          </AlertDialogTitle>
        </div>

        <button 
          @click="handleCancel"
          class="size-7 rounded-xl flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-amber-500/10 transition-colors cursor-pointer border-0 outline-none shrink-0"
          :title="languageStore.isFa ? 'بستن' : 'Close'"
        >
          <XIcon class="size-4" />
        </button>
      </AlertDialogHeader>

      <!-- Content Body -->
      <div class="px-5 pb-5 pt-3 flex flex-col gap-4">
        <AlertDialogDescription class="text-xs text-muted-foreground leading-relaxed font-normal font-sans block">
          {{ languageStore.isFa 
            ? 'برای جلوگیری از ارسال تکراری، می‌توانید به پست قبلی بروید یا در صورت نیاز، همین متن را دوباره منتشر کنید.'
            : 'To avoid duplicate posts, you can jump to the original post or choose to publish again.'
          }}
        </AlertDialogDescription>

        <!-- Specifications Card for Existing Duplicate Post -->
        <div class="flex flex-col gap-2.5 bg-amber-500/5 dark:bg-amber-500/10 border border-amber-500/20 rounded-xl p-3.5 font-sans">
          <div class="flex items-center gap-1.5 text-xs font-bold text-foreground">
            <LayersIcon class="size-3.5 text-amber-500" />
            <span>{{ languageStore.isFa ? 'اطلاعات پست منتشرشده' : 'Published Post Details' }}</span>
          </div>

          <!-- Date & Time -->
          <div class="flex items-center justify-between text-xs pt-2 border-t border-amber-500/15">
            <div class="flex items-center gap-1.5 text-muted-foreground">
              <CalendarIcon class="size-3.5 text-muted-foreground/70" />
              <span class="text-[11px] font-medium font-sans">{{ languageStore.isFa ? 'تاریخ انتشار:' : 'Published Date:' }}</span>
            </div>
            <span class="text-[11px] font-bold text-foreground font-sans">{{ formattedDate }}</span>
          </div>

          <!-- Published Platforms Badges -->
          <div class="flex items-center justify-between text-xs pt-1">
            <span class="text-[11px] font-medium text-muted-foreground font-sans">{{ languageStore.isFa ? 'پلتفرم‌ها:' : 'Platforms:' }}</span>
            <div class="flex items-center gap-1.5 flex-wrap">
              <!-- Telegram Badge -->
              <Badge 
                v-if="hasTelegram" 
                variant="secondary" 
                class="bg-sky-500/10 border-sky-500/20 text-sky-600 dark:text-sky-400 text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1 font-sans"
              >
                <span class="font-sans font-black text-[9px]">TG</span>
                <span>{{ languageStore.isFa ? 'تلگرام' : 'Telegram' }}</span>
              </Badge>
              
              <!-- Bale Badge -->
              <Badge 
                v-if="hasBale" 
                variant="secondary" 
                class="bg-emerald-500/10 border-emerald-500/20 text-emerald-600 dark:text-emerald-400 text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1 font-sans"
              >
                <span class="font-sans font-black text-[9px]">BL</span>
                <span>{{ languageStore.isFa ? 'بله' : 'Bale' }}</span>
              </Badge>

              <!-- Tafakor Badge -->
              <Badge 
                variant="secondary" 
                class="bg-primary/10 border-primary/20 text-primary text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1 font-sans"
              >
                <span>{{ languageStore.isFa ? 'تفکر' : 'Tafakor' }}</span>
              </Badge>
            </div>
          </div>
        </div>
      </div>

      <!-- Footer Actions with Concise, High-Impact UX Writing -->
      <AlertDialogFooter class="px-5 py-3.5 bg-muted/20 border-t border-border/50 flex flex-row items-center justify-end gap-2">
        <!-- Secondary Option: Force Republish -->
        <Button 
          type="button" 
          variant="outline" 
          size="sm" 
          class="text-xs font-bold rounded-xl h-10 px-4 cursor-pointer hover:bg-amber-500/10 hover:text-amber-600 hover:border-amber-500/30 font-sans active:scale-95 transition-all" 
          @click="handleForceSubmit"
        >
          <RepeatIcon data-icon="inline-start" />
          {{ languageStore.isFa ? 'ارسال مجدد' : 'Publish Again' }}
        </Button>

        <!-- Primary Option: View Original Post -->
        <Button 
          type="button" 
          variant="default" 
          size="sm" 
          class="text-xs font-bold rounded-xl h-10 px-4 cursor-pointer bg-amber-600 hover:bg-amber-700 text-white font-sans active:scale-95 transition-all shadow-md shadow-amber-600/20" 
          @click="handleGoToExisting"
        >
          <ExternalLinkIcon data-icon="inline-start" />
          {{ languageStore.isFa ? 'مشاهده پست قبلی' : 'View Original Post' }}
        </Button>
      </AlertDialogFooter>
    </AlertDialogContent>
  </AlertDialog>
</template>
