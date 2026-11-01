<script setup lang="ts">
import { ref, computed } from 'vue'
import type { CampaignCategory } from '@/types/kindness'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar'
import { formatCurrencyTomans } from '@/utils/persianNumbers'
import { cn } from '@/lib/utils'
import { 
  HeartIcon, 
  PinIcon, 
  CalendarIcon, 
  ActivityIcon, 
  UserIcon,
  ImageIcon,
  VideoIcon,
  MoreVerticalIcon,
  PencilIcon,
  CopyIcon,
  Share2Icon,
  Trash2Icon,
  BanIcon
} from '@lucide/vue'
import { useToastStore } from '@/stores/toastStore'
import type { CampaignStatus } from '@/types/kindness'

const toastStore = useToastStore()

export interface DonationChatCardProps {
  id?: string | number
  title: string
  category: CampaignCategory
  status?: CampaignStatus
  targetAmount: number | null
  collectedAmount?: number
  description: string
  mediaUrl?: string
  mediaType?: 'image' | 'video'
  mediaCount?: number
  autoPin?: boolean
  deadline?: string | null
  authorName?: string
  authorAvatar?: string
  authorRole?: string
  topicName?: string
  canEdit?: boolean
  isPreview?: boolean
}

const props = withDefaults(defineProps<DonationChatCardProps>(), {
  id: undefined,
  status: 'active',
  collectedAmount: 0,
  mediaUrl: undefined,
  mediaType: 'image',
  mediaCount: 0,
  autoPin: false,
  deadline: null,
  authorName: 'مدیر تاپیک',
  authorAvatar: undefined,
  authorRole: undefined,
  topicName: undefined,
  canEdit: false,
  isPreview: false
})

const emit = defineEmits<{
  (e: 'donate-click'): void
  (e: 'card-click'): void
  (e: 'edit-click', campaign: DonationChatCardProps): void
  (e: 'delete-click', campaign: DonationChatCardProps): void
}>()

const isMenuOpen = ref(false)
const menuTouchPos = ref<{ x: number; y: number }>({ x: 0, y: 0 })

const handleThreeDotsClick = (e: MouseEvent) => {
  e.stopPropagation()
  menuTouchPos.value = { x: e.clientX, y: e.clientY }
  isMenuOpen.value = true
}

const handleEditAction = (e: Event) => {
  e.stopPropagation()
  isMenuOpen.value = false
  emit('edit-click', {
    id: props.id,
    title: props.title,
    category: props.category,
    status: props.status,
    targetAmount: props.targetAmount,
    collectedAmount: props.collectedAmount,
    description: props.description,
    mediaUrl: props.mediaUrl,
    mediaType: props.mediaType,
    mediaCount: props.mediaCount,
    autoPin: props.autoPin,
    deadline: props.deadline,
    authorName: props.authorName,
    authorAvatar: props.authorAvatar,
    authorRole: props.authorRole,
    topicName: props.topicName
  })
}

const handleDeleteAction = (e: Event) => {
  e.stopPropagation()
  isMenuOpen.value = false
  emit('delete-click', {
    id: props.id,
    title: props.title,
    category: props.category,
    status: props.status,
    targetAmount: props.targetAmount,
    collectedAmount: props.collectedAmount,
    description: props.description,
    mediaUrl: props.mediaUrl,
    mediaType: props.mediaType,
    mediaCount: props.mediaCount,
    autoPin: props.autoPin,
    deadline: props.deadline,
    authorName: props.authorName,
    authorAvatar: props.authorAvatar,
    authorRole: props.authorRole,
    topicName: props.topicName
  })
}

const handleCopyAction = async (e: Event) => {
  e.stopPropagation()
  isMenuOpen.value = false
  const textToCopy = `${props.title}\n\n${props.description}\n\nمبلغ هدف: ${formattedTarget.value} تومان`
  if (navigator.clipboard) {
    try {
      await navigator.clipboard.writeText(textToCopy)
      toastStore.triggerToast('متن پویش با موفقیت کپی شد.', 'success')
    } catch {
      // ignore
    }
  }
}

const handleShareAction = async (e: Event) => {
  e.stopPropagation()
  isMenuOpen.value = false
  const shareUrl = `${window.location.origin}/donate#campaign-${props.id || ''}`
  if (navigator.clipboard) {
    try {
      await navigator.clipboard.writeText(shareUrl)
      toastStore.triggerToast('لینک پویش با موفقیت در حافظه موقت کپی شد.', 'success')
    } catch {
      toastStore.triggerToast('لینک اشتراک‌گذاری کپی شد.', 'info')
    }
  }
}

const CATEGORY_NAMES: Record<CampaignCategory, string> = {
  mosque: 'مسجد',
  school: 'مدرسه و آموزش',
  health: 'درمانی و سلامت',
  livelihood: 'نیازمندان و معیشت',
  construction: 'عمرانی و تجهیزات',
  other: 'متفرقه'
}

const categoryLabel = computed(() => CATEGORY_NAMES[props.category] || 'پویش مهربانی')

const percentage = computed(() => {
  if (!props.targetAmount || props.targetAmount <= 0) return 0
  const pct = Math.round(((props.collectedAmount || 0) / props.targetAmount) * 100)
  return Math.min(100, Math.max(0, pct))
})

const formattedTarget = computed(() => formatCurrencyTomans(props.targetAmount || 0))
const formattedCollected = computed(() => formatCurrencyTomans(props.collectedAmount || 0))
</script>

<template>
  <Card 
    :class="cn(
      'w-full overflow-hidden rounded-2xl border border-border/70 dark:border-border/60 bg-card/95 backdrop-blur-md text-card-foreground shadow-[0_2px_8px_rgba(0,0,0,0.03)] hover:shadow-[0_4px_16px_rgba(0,0,0,0.06)] transition-all duration-300 dir-rtl text-right font-sans hover:border-primary/40 cursor-pointer py-0 gap-0 relative',
      isPreview && 'ring-2 ring-primary/20'
    )"
    @click="emit('card-click')"
  >
    <!-- Header: Creator/Author Profile & Actions -->
    <CardHeader class="px-4 py-3 border-b border-border/60 bg-muted/20 flex flex-row items-center justify-between gap-2 space-y-0">
      <div class="flex items-center gap-2.5 min-w-0">
        <Avatar class="size-9 rounded-xl border border-border/60 shrink-0 overflow-hidden">
          <AvatarImage v-if="authorAvatar" :src="authorAvatar" :alt="authorName" class="w-full h-full object-cover" />
          <AvatarFallback class="bg-primary/10 text-primary text-xs font-bold rounded-xl">
            {{ authorName ? authorName.charAt(0) : 'پ' }}
          </AvatarFallback>
        </Avatar>

        <div class="flex flex-col min-w-0 text-start">
          <span class="text-xs font-bold text-foreground truncate">
            {{ authorName }}
          </span>
          <span class="text-[10px] text-muted-foreground truncate">
            {{ authorRole || (topicName ? `در تاپیک ${topicName}` : 'ایجادکننده پویش') }}
          </span>
        </div>
      </div>

      <div class="flex items-center gap-1.5 shrink-0">
        <Badge 
          v-if="autoPin" 
          variant="secondary" 
          class="text-[10px] px-2 py-0.5 rounded-full font-medium"
          title="پین شده در تاپیک"
        >
          <PinIcon class="rotate-45" data-icon="inline-start" />
          <span>پین‌شده</span>
        </Badge>

        <Badge 
          v-if="isPreview" 
          variant="outline" 
          class="text-[10px] px-2 py-0.5 rounded-full font-medium"
        >
          پیش‌نمایش
        </Badge>

        <!-- Three Dots Options Button (Edit / More) -->
        <Button 
          v-if="canEdit || !isPreview"
          variant="ghost" 
          size="icon" 
          class="size-7 rounded-full text-muted-foreground hover:text-foreground cursor-pointer shrink-0"
          title="گزینه‌ها"
          @click="handleThreeDotsClick"
        >
          <MoreVerticalIcon class="size-4" />
        </Button>
      </div>
    </CardHeader>

    <!-- Optional Media Thumbnail -->
    <div v-if="mediaUrl" class="relative w-full aspect-[2.3/1] bg-muted/40 overflow-hidden border-b border-border/30">
      <img 
        v-if="mediaType === 'image'" 
        :src="mediaUrl" 
        :alt="title" 
        class="w-full h-full object-cover transition-transform duration-500 hover:scale-105"
      />
      <div v-else class="w-full h-full flex items-center justify-center bg-black/80 text-white">
        <VideoIcon class="size-7 text-primary" />
      </div>

      <!-- Multiple Media Indicator -->
      <div 
        v-if="mediaCount > 1" 
        class="absolute bottom-2 left-2 bg-background/85 backdrop-blur-xs text-foreground text-[10px] font-bold px-2 py-0.5 rounded-md flex items-center gap-1 border border-border/40"
      >
        <ImageIcon class="size-3.5" />
        <span>{{ mediaCount }} فایل</span>
      </div>
    </div>

    <!-- Main Content -->
    <CardContent class="p-4 flex flex-col gap-3">
      <!-- Title, Category Badge & Description -->
      <div class="flex flex-col gap-1.5">
        <div class="flex items-start justify-between gap-2">
          <CardTitle class="cn-font-heading text-sm font-bold leading-snug text-foreground line-clamp-2 text-start flex-1">
            {{ title || 'عنوان پویش مهربانی' }}
          </CardTitle>
          <Badge variant="outline" class="text-[10px] px-2 py-0.5 rounded-md font-medium shrink-0 bg-muted/30 border-border/60">
            {{ categoryLabel }}
          </Badge>
        </div>

        <CardDescription class="text-xs text-muted-foreground leading-relaxed line-clamp-2 text-start">
          {{ description || 'توضیحات و شرح نیاز این پویش در این قسمت قرار می‌گیرد.' }}
        </CardDescription>
      </div>

      <!-- Target & Progress Section -->
      <div class="flex flex-col gap-2.5 p-3 rounded-2xl bg-muted/30 border border-border/40">
        <div class="flex items-center justify-between text-xs">
          <span class="text-muted-foreground font-medium">مبلغ هدف:</span>
          <span class="font-bold text-foreground">{{ formattedTarget }}</span>
        </div>

        <!-- Progress Bar -->
        <Progress :model-value="percentage" class="h-2 bg-muted rounded-full" />

        <div class="flex items-center justify-between text-xs text-muted-foreground">
          <span class="font-semibold text-primary">
            جمع‌آوری شده: {{ formattedCollected }}
          </span>
          <span class="font-bold text-foreground">
            {{ percentage }}٪
          </span>
        </div>
      </div>
    </CardContent>

    <!-- Footer: Deadline info and participate action button -->
    <CardFooter class="px-4 pb-3.5 pt-0 flex items-center justify-between gap-2">
      <div v-if="status === 'inactive'" class="flex items-center gap-1.5 text-xs text-destructive font-medium">
        <BanIcon class="size-3.5 text-destructive" />
        <span>پویش متوقف و غیرفعال شد</span>
      </div>
      <div v-else-if="deadline" class="flex items-center gap-1.5 text-xs text-muted-foreground font-medium">
        <CalendarIcon class="size-3.5 text-muted-foreground/80" />
        <span>مهلت: {{ deadline }}</span>
      </div>
      <div v-else class="flex items-center gap-1.5 text-xs text-muted-foreground font-medium">
        <ActivityIcon class="size-3.5 text-primary" />
        <span>پویش فعال</span>
      </div>

      <Button 
        v-if="status === 'active'"
        size="sm" 
        class="rounded-xl font-bold text-xs h-9 px-3.5 cursor-pointer shadow-md shadow-primary/20 active:scale-95 transition-all"
        @click.stop="emit('donate-click')"
      >
        <HeartIcon class="fill-current size-3.5" data-icon="inline-start" />
        <span>مشارکت در پویش</span>
      </Button>
      <Button 
        v-else-if="status === 'inactive'"
        size="sm" 
        variant="secondary"
        disabled
        class="rounded-xl font-bold text-xs h-9 px-3.5 opacity-70 bg-muted text-muted-foreground"
      >
        <BanIcon class="size-3.5" data-icon="inline-start" />
        <span>متوقف شده</span>
      </Button>
      <Button 
        v-else
        size="sm" 
        variant="secondary"
        disabled
        class="rounded-xl font-bold text-xs h-9 px-3.5 opacity-90"
      >
        <span>تکمیل شده</span>
      </Button>
    </CardFooter>
  </Card>

  <!-- Options Context Menu Overlay Teleported to Body -->
  <Teleport to="body">
    <Transition name="fade">
      <div 
        v-if="isMenuOpen" 
        class="fixed inset-0 z-50 bg-black/30 dark:bg-black/50 backdrop-blur-xs flex items-center justify-center pointer-events-auto"
        @click="isMenuOpen = false"
        @contextmenu.prevent="isMenuOpen = false"
      >
        <div 
          class="bg-card/95 backdrop-blur-2xl border border-border/80 dark:border-border/60 rounded-2xl p-1.5 shadow-[0_12px_40px_rgba(0,0,0,0.12)] flex flex-col gap-0.5 w-52 text-start pointer-events-auto select-none animate-in zoom-in-95 duration-150"
          dir="rtl"
          @click.stop
        >
          <!-- Share Campaign Link -->
          <button 
            @click="handleShareAction" 
            class="w-full text-start px-3 py-2 text-xs font-semibold rounded-xl text-foreground hover:bg-muted/80 flex items-center justify-between cursor-pointer transition-all active:scale-[0.98]"
          >
            <span>اشتراک‌گذاری و کپی لینک</span>
            <Share2Icon class="size-3.5 text-muted-foreground" />
          </button>

          <!-- Copy Info -->
          <button 
            @click="handleCopyAction" 
            class="w-full text-start px-3 py-2 text-xs font-semibold rounded-xl text-foreground hover:bg-muted/80 flex items-center justify-between cursor-pointer transition-all active:scale-[0.98]"
          >
            <span>کپی متن پویش</span>
            <CopyIcon class="size-3.5 text-muted-foreground" />
          </button>

          <!-- Edit & Delete Campaign (Strictly For Creator) -->
          <template v-if="canEdit">
            <div class="h-[0.8px] bg-border/60 my-0.5 mx-1" />

            <button 
              v-if="status !== 'inactive'"
              @click="handleEditAction" 
              class="w-full text-start px-3 py-2 text-xs font-semibold rounded-xl text-primary hover:bg-primary/10 flex items-center justify-between cursor-pointer transition-all active:scale-[0.98]"
            >
              <span>ویرایش پویش</span>
              <PencilIcon class="size-3.5 text-primary" />
            </button>

            <button 
              v-if="status !== 'inactive'"
              @click="handleDeleteAction" 
              class="w-full text-start px-3 py-2 text-xs font-semibold rounded-xl text-destructive hover:bg-destructive/10 flex items-center justify-between cursor-pointer transition-all active:scale-[0.98]"
            >
              <span>پاکسازی و حذف پویش</span>
              <Trash2Icon class="size-3.5 text-destructive" />
            </button>
          </template>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
