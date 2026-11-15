<script setup lang="ts">
import { ref, computed } from 'vue'
import type { BookDonationPostData } from '@/types/shelf'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar'
import { 
  BookOpenIcon, 
  QrCodeIcon, 
  PackageIcon, 
  MapPinIcon, 
  HandHeartIcon, 
  Share2Icon, 
  UserCheckIcon,
  SparklesIcon,
  MoreVerticalIcon,
  CopyIcon,
  CheckIcon,
  InfoIcon
} from '@lucide/vue'
import { useToastStore } from '@/stores/toastStore'
import { useLanguageStore } from '@/stores/languageStore'

const toastStore = useToastStore()
const languageStore = useLanguageStore()

export interface BookChatCardProps {
  book: BookDonationPostData
  topicName?: string
  authorName?: string
  authorAvatar?: string
  canEdit?: boolean
  isPreview?: boolean
}

const props = withDefaults(defineProps<BookChatCardProps>(), {
  topicName: undefined,
  authorName: 'همراه تفاخر',
  authorAvatar: undefined,
  canEdit: false,
  isPreview: false
})

const emit = defineEmits<{
  (e: 'claim-click', book: BookDonationPostData): void
  (e: 'inspect-click', shortCode: string): void
  (e: 'share-click', book: BookDonationPostData): void
}>()

const isCopied = ref(false)

const hasInPerson = computed(() => props.book.donation_methods?.includes('in_person') || Boolean(props.book.short_code))
const hasPostal = computed(() => props.book.donation_methods?.includes('postal'))
const hasStation = computed(() => props.book.donation_methods?.includes('station'))

const conditionLabel = computed(() => {
  if (props.book.condition_display) return props.book.condition_display
  const map: Record<string, string> = {
    new: 'نو و آکبند',
    like_new: 'در حد نو',
    good: 'دست دوم سالم',
    fair: 'خوانده‌شده',
    worn: 'کهنه'
  }
  return map[props.book.condition || ''] || 'دست دوم'
})

const copyShortCode = async () => {
  if (!props.book.short_code) return
  try {
    await navigator.clipboard.writeText(props.book.short_code)
    isCopied.value = true
    toastStore.triggerToast(languageStore.t('کد شناسنامه کتاب کپی شد.', 'Book short code copied.'), 'success')
    setTimeout(() => {
      isCopied.value = false
    }, 2000)
  } catch {
    toastStore.triggerToast('خطا در کپی', 'error')
  }
}

const handleShare = () => {
  emit('share-click', props.book)
}
</script>

<template>
  <div class="relative w-full max-w-md mx-auto my-2 group transition-all duration-300">
    <!-- Ambient glow container matching Tafakor book aesthetic -->
    <div 
      class="absolute -inset-0.5 rounded-3xl opacity-30 group-hover:opacity-75 blur-md transition duration-500 bg-linear-to-r from-amber-500/20 via-emerald-500/25 to-teal-500/20 pointer-events-none" 
    />

    <Card class="relative overflow-hidden rounded-3xl border border-amber-500/30 dark:border-amber-500/20 bg-card/95 backdrop-blur-xl shadow-lg hover:shadow-xl transition-all duration-300 p-0 gap-0">
      <!-- Top Decorative Banner -->
      <div class="h-1.5 w-full bg-linear-to-r from-amber-500 via-emerald-500 to-teal-500" />

      <!-- Header: Topic, Badge & Donor info -->
      <CardHeader class="p-3.5 pb-2.5 flex flex-col gap-2">
        <div class="flex items-center justify-between gap-2">
          <div class="flex items-center gap-2 min-w-0">
            <div class="size-8 rounded-xl bg-amber-500/10 text-amber-600 dark:text-amber-400 flex items-center justify-center shrink-0 border border-amber-500/20">
              <BookOpenIcon class="size-4" />
            </div>
            <div class="flex flex-col min-w-0">
              <div class="flex items-center gap-1.5">
                <span class="text-xs font-extrabold text-foreground truncate">
                  {{ languageStore.t('کتاب اهدایی', 'Book Donation') }}
                </span>
                <Badge variant="outline" class="text-[9px] px-1.5 py-0 h-4 font-bold rounded-md bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30">
                  {{ languageStore.t('رایگان', 'Free') }}
                </Badge>
              </div>
              <span v-if="topicName" class="text-[10px] text-muted-foreground truncate">
                {{ topicName }}
              </span>
            </div>
          </div>

          <!-- QR Short code badge if in-person circulation is active -->
          <button
            v-if="book.short_code"
            type="button"
            class="inline-flex items-center gap-1 px-2 py-0.5 rounded-lg text-[10px] font-mono font-bold bg-muted/60 hover:bg-muted border border-border/60 text-foreground transition-colors cursor-pointer"
            :title="languageStore.t('کپی کد یکتای گردش کتاب', 'Copy circulation code')"
            @click.stop="copyShortCode"
          >
            <QrCodeIcon class="size-3 text-primary shrink-0" />
            <span>{{ book.short_code }}</span>
            <CheckIcon v-if="isCopied" class="size-2.5 text-emerald-500" />
            <CopyIcon v-else class="size-2.5 text-muted-foreground" />
          </button>
        </div>
      </CardHeader>

      <!-- Content: Book Cover + Meta + Notes -->
      <CardContent class="p-3.5 pt-1 pb-3 flex flex-col gap-3">
        <div class="flex gap-3 items-start">
          <!-- Book Cover image or stylized fallback -->
          <div class="relative w-20 h-28 sm:w-24 sm:h-32 shrink-0 rounded-xl overflow-hidden border border-border/60 bg-muted/40 shadow-xs flex flex-col items-center justify-center text-center p-1.5 group-hover:scale-[1.02] transition-transform">
            <img 
              v-if="book.cover_image"
              :src="book.cover_image" 
              :alt="book.title"
              class="w-full h-full object-cover rounded-lg"
              loading="lazy"
            />
            <div v-else class="flex flex-col items-center justify-center gap-1 text-muted-foreground">
              <BookOpenIcon class="size-8 text-amber-500/70" />
              <span class="text-[9px] font-bold line-clamp-2 leading-tight text-foreground/80">
                {{ book.title }}
              </span>
            </div>
          </div>

          <!-- Book Details -->
          <div class="flex flex-col flex-1 min-w-0 gap-1.5">
            <h4 class="text-sm font-extrabold text-foreground leading-snug line-clamp-2">
              {{ book.title }}
            </h4>

            <div v-if="book.author" class="text-xs text-muted-foreground line-clamp-1">
              <span class="text-[11px]">{{ languageStore.t('پدیدآور:', 'Author:') }}</span>
              <span class="font-medium text-foreground/90 mr-1">{{ book.author }}</span>
            </div>

            <div v-if="book.publisher" class="text-[11px] text-muted-foreground line-clamp-1">
              <span>{{ languageStore.t('ناشر:', 'Publisher:') }}</span>
              <span class="font-medium text-foreground/80 mr-1">{{ book.publisher }}</span>
            </div>

            <!-- Condition & Delivery Badges -->
            <div class="flex flex-wrap items-center gap-1.5 pt-1">
              <Badge variant="secondary" class="text-[10px] px-1.5 py-0 h-5 font-semibold rounded-md border border-border/40">
                {{ conditionLabel }}
              </Badge>

              <Badge 
                v-if="hasInPerson" 
                variant="outline" 
                class="text-[10px] px-1.5 py-0 h-5 font-semibold rounded-md gap-1 bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/30"
              >
                <QrCodeIcon class="size-2.5" />
                <span>{{ languageStore.t('تحویل حضوری', 'In-Person') }}</span>
              </Badge>

              <Badge 
                v-if="hasPostal" 
                variant="outline" 
                class="text-[10px] px-1.5 py-0 h-5 font-semibold rounded-md gap-1 bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/30"
              >
                <PackageIcon class="size-2.5" />
                <span>{{ languageStore.t('ارسال پستی', 'Postal') }}</span>
              </Badge>

              <Badge 
                v-if="hasStation" 
                variant="outline" 
                class="text-[10px] px-1.5 py-0 h-5 font-semibold rounded-md gap-1 bg-purple-500/10 text-purple-600 dark:text-purple-400 border-purple-500/30"
              >
                <MapPinIcon class="size-2.5" />
                <span>{{ languageStore.t('قفسه تفاخر', 'Kiosk') }}</span>
              </Badge>
            </div>
          </div>
        </div>

        <!-- Book description / Donor note -->
        <p v-if="book.description" class="text-xs text-muted-foreground leading-relaxed line-clamp-3 bg-muted/20 p-2.5 rounded-xl border border-border/30">
          {{ book.description }}
        </p>

        <!-- Donor info bar -->
        <div class="flex items-center justify-between text-[11px] text-muted-foreground pt-1 border-t border-border/30">
          <div class="flex items-center gap-1.5">
            <span class="text-[10px] text-muted-foreground">{{ languageStore.t('اهداکننده:', 'Donor:') }}</span>
            <span class="font-semibold text-foreground">{{ book.seller_name || authorName || 'همراه تفاخر' }}</span>
          </div>
          <span v-if="book.shipping_payer === 'donor'" class="text-[10px] text-emerald-600 dark:text-emerald-400 font-bold">
            {{ languageStore.t('هزینه ارسال با اهداکننده', 'Free shipping') }}
          </span>
        </div>
      </CardContent>

      <!-- Footer: Interactive Action Buttons -->
      <CardFooter class="p-3.5 pt-0 flex items-center justify-between gap-2">
        <!-- Main Primary Call-to-Action: Claim / Request Book -->
        <Button
          type="button"
          size="sm"
          class="flex-1 h-9 rounded-xl text-xs font-bold gap-1.5 bg-linear-to-r from-amber-500 to-emerald-600 hover:from-amber-600 hover:to-emerald-700 text-white shadow-xs cursor-pointer active:scale-95 transition-all"
          @click="emit('claim-click', book)"
        >
          <HandHeartIcon class="size-3.5" />
          <span>{{ languageStore.t('دریافت این کتاب', 'Claim this Book') }}</span>
        </Button>

        <!-- Journey / QR Inspect Button -->
        <Button
          v-if="book.short_code"
          type="button"
          variant="outline"
          size="sm"
          class="h-9 px-2.5 rounded-xl text-xs font-bold gap-1.5 border-border/60 hover:bg-muted cursor-pointer"
          :title="languageStore.t('مشاهده سفرنامه و سرگذشت کتاب', 'Book Journey')"
          @click="emit('inspect-click', book.short_code)"
        >
          <QrCodeIcon class="size-3.5 text-primary" />
          <span class="hidden sm:inline">{{ languageStore.t('سفرنامه', 'Journey') }}</span>
        </Button>

        <!-- Share Button -->
        <Button
          type="button"
          variant="ghost"
          size="icon"
          class="size-9 rounded-xl text-muted-foreground hover:text-foreground cursor-pointer shrink-0"
          :title="languageStore.t('اشتراک‌گذاری', 'Share')"
          @click="handleShare"
        >
          <Share2Icon class="size-3.5" />
        </Button>
      </CardFooter>
    </Card>
  </div>
</template>

