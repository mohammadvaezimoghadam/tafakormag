<script setup lang="ts">
import { computed } from 'vue'
import type { PostEditHistoryItem } from '@/types/editorial'
import FormattedText from '@/components/common/FormattedText.vue'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter
} from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar'
import { 
  HistoryIcon, 
  ClockIcon, 
  UserCheckIcon,
  SparklesIcon,
  FileTextIcon,
  XIcon,
  LayersIcon,
  ArrowRightIcon
} from '@lucide/vue'
import { useLanguageStore } from '@/stores/languageStore'

const languageStore = useLanguageStore()

const props = withDefaults(defineProps<{
  open: boolean
  history: PostEditHistoryItem[]
  postId?: string | number
  loading?: boolean
}>(), {
  history: () => [],
  loading: false
})

const emit = defineEmits<{
  (e: 'update:open', val: boolean): void
}>()

const getItemContent = (item: PostEditHistoryItem): string => {
  return item.newContent || item.content || item.previousContent || ''
}

const getItemPreviousContent = (item: PostEditHistoryItem): string => {
  return item.previousContent || ''
}

const getItemApprover = (item: PostEditHistoryItem) => {
  return item.approvedBy || item.approver || null
}

const getItemNote = (item: PostEditHistoryItem): string => {
  return item.note || item.summaryOfChanges || ''
}

const formatHistoryTime = (rawTime?: string): string => {
  if (!rawTime) return ''
  if (rawTime.includes('امروز') || rawTime.includes('دیروز') || rawTime.includes('پیش') || rawTime.includes('ago')) {
    return languageStore.n(rawTime)
  }
  try {
    const date = new Date(rawTime)
    if (isNaN(date.getTime())) return languageStore.n(rawTime)
    return date.toLocaleDateString(languageStore.currentLanguage === 'fa' ? 'fa-IR' : 'en-US', {
      hour: '2-digit',
      minute: '2-digit',
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      numberingSystem: languageStore.currentLanguage === 'fa' ? 'arabext' : 'latn'
    })
  } catch (e) {
    return languageStore.n(rawTime)
  }
}
</script>

<template>
  <Dialog :open="open" @update:open="emit('update:open', $event)">
    <DialogContent 
      :show-close-button="false"
      class="max-w-[460px] p-0 overflow-hidden flex flex-col text-start font-sans rounded-3xl border border-border/50 bg-background shadow-2xl"
      :dir="languageStore.dir"
    >
      <!-- Header Banner (مطابق استایل استانداردهای دیالوگ پلتفرم) -->
      <DialogHeader class="px-5 py-4 bg-gradient-to-br from-primary/15 via-primary/10 to-transparent border-b border-border/40 flex flex-row items-center justify-between space-y-0">
        <div class="flex items-center gap-3">
          <div class="size-9 rounded-2xl bg-primary/20 text-primary flex items-center justify-center shadow-xs shrink-0">
            <HistoryIcon class="size-4.5" />
          </div>
          <div class="flex flex-col text-start">
            <div class="flex items-center gap-2">
              <DialogTitle class="text-xs sm:text-sm font-black text-foreground font-sans">
                {{ languageStore.t('تاریخچه ویرایش‌های پست', 'Post Edit History') }}
              </DialogTitle>
              <Badge 
                v-if="!loading && history.length > 0" 
                variant="secondary" 
                class="rounded-full px-2 py-0 text-[9.5px] font-bold border-0 bg-primary/10 text-primary"
              >
                {{ history.length }} {{ languageStore.t('نسخه', 'versions') }}
              </Badge>
            </div>
            <DialogDescription class="text-[10px] sm:text-[10.5px] text-muted-foreground mt-0.5">
              {{ languageStore.t('مشاهده نسخه‌ها و تغییرات ثبت‌شده در این پیام', 'View revision versions and changes for this post') }}
            </DialogDescription>
          </div>
        </div>

        <button 
          @click="emit('update:open', false)"
          class="size-7 rounded-xl flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-muted/80 transition-colors cursor-pointer border-0 outline-none shrink-0"
          :title="languageStore.t('بستن', 'Close')"
        >
          <XIcon class="size-4" />
        </button>
      </DialogHeader>

      <!-- History Timeline / States Body -->
      <div class="p-4 sm:p-5 flex flex-col gap-3.5 max-h-[70vh] overflow-y-auto">
        <!-- 1. LOADING STATE (لودینگ شیک همگام با دیالوگ‌های پروژه) -->
        <template v-if="loading">
          <div class="flex flex-col gap-3 w-full animate-pulse">
            <div 
              v-for="i in 2" 
              :key="'hist-skel-' + i"
              class="w-full rounded-2xl border border-border/40 bg-muted/15 p-3.5 flex flex-col gap-2.5"
            >
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <Skeleton class="size-7 rounded-full" />
                  <div class="flex flex-col gap-1">
                    <Skeleton class="h-3 w-20 rounded-md" />
                    <Skeleton class="h-2.5 w-14 rounded-md" />
                  </div>
                </div>
                <Skeleton class="h-4.5 w-16 rounded-full" />
              </div>
              <Skeleton class="h-12 w-full rounded-xl" />
            </div>
          </div>
        </template>

        <!-- 2. EMPTY STATE (طراحی بازطراحی شده و یکپارچه) -->
        <div 
          v-else-if="history.length === 0" 
          class="py-8 px-4 flex flex-col items-center justify-center text-center rounded-2xl bg-muted/20 border border-border/40 my-2"
        >
          <div class="size-12 rounded-2xl bg-muted/60 text-muted-foreground flex items-center justify-center mb-3 shadow-inner">
            <HistoryIcon class="size-6 text-muted-foreground/70" />
          </div>
          <h4 class="text-xs sm:text-sm font-bold text-foreground mb-1">
            {{ languageStore.t('هیچ ویرایشی برای این پیام ثبت نشده است', 'No Edit History Recorded') }}
          </h4>
          <p class="text-[10.5px] sm:text-[11px] text-muted-foreground max-w-[280px] leading-relaxed mb-4">
            {{ languageStore.t('این یادداشت از زمان انتشار تاکنون ویرایش نشده یا نسخه‌ قبلی برای آن در سامانه موجود نیست.', 'This post has not been modified since publication, or no previous versions are recorded.') }}
          </p>
          <Button 
            variant="outline" 
            size="sm" 
            class="rounded-xl text-xs h-8 px-4 cursor-pointer border-border/70 hover:bg-muted"
            @click="emit('update:open', false)"
          >
            {{ languageStore.t('متوجه شدم', 'Got it') }}
          </Button>
        </div>

        <!-- 3. TIMELINE STATE (طراحی با سایزهای دقیق هماهنگ با دیالوگ‌های دیگر) -->
        <div v-else class="relative ps-4 sm:ps-5 border-s-2 border-primary/25 dark:border-primary/20 space-y-4 ms-2 sm:ms-2.5 my-1">
          <div 
            v-for="(item, idx) in history" 
            :key="item.id || idx"
            class="relative group"
          >
            <!-- Timeline dot -->
            <div class="absolute -start-[21px] sm:-start-[25px] top-3.5 size-3 rounded-full border-2 border-background bg-primary shadow-xs" />

            <!-- History Item Card -->
            <div class="w-full rounded-2xl border border-border/40 bg-card p-3.5 shadow-none flex flex-col gap-2.5 text-start transition-all hover:border-border/70">
              <!-- Meta Info: Editor, Badge, Timestamp & Approver -->
              <div class="flex flex-wrap items-center justify-between gap-2 border-b border-border/30 pb-2">
                <div class="flex items-center gap-2">
                  <Avatar class="size-7 border border-border/40">
                    <AvatarImage :src="item.editor?.avatar || ''" :alt="item.editor?.name" />
                    <AvatarFallback class="bg-primary/10 text-primary text-[10px] font-bold">
                      {{ item.editor?.name?.charAt(0) || 'U' }}
                    </AvatarFallback>
                  </Avatar>

                  <div class="flex flex-col text-start">
                    <div class="flex items-center gap-1.5 flex-wrap">
                      <span class="text-xs font-bold text-foreground">{{ item.editor?.name || languageStore.t('ویراستار', 'Editor') }}</span>
                      <Badge variant="secondary" class="text-[9px] px-1.5 py-0 h-4 font-medium border-0 bg-muted/60">
                        {{ item.editor?.role || languageStore.t('ویراستار تاپیک', 'Topic Editor') }}
                      </Badge>
                    </div>
                    <div class="flex items-center gap-1 text-[9.5px] text-muted-foreground mt-0.5">
                      <ClockIcon class="size-2.5 text-primary" />
                      <span>{{ formatHistoryTime(item.appliedAt || item.createdAt) }}</span>
                    </div>
                  </div>
                </div>

                <!-- Approver Badge (if available) -->
                <div v-if="getItemApprover(item)" class="flex items-center gap-1 text-[10px] text-muted-foreground bg-muted/30 px-2 py-0.5 rounded-lg border border-border/30">
                  <UserCheckIcon class="size-3 text-emerald-500 shrink-0" />
                  <span>{{ languageStore.t('تاییدکننده:', 'Approved by:') }}</span>
                  <span class="font-bold text-foreground">{{ getItemApprover(item)?.name }}</span>
                </div>
              </div>

              <!-- Optional Change Note / Reason -->
              <div 
                v-if="getItemNote(item)" 
                class="flex items-start gap-1.5 text-[10.5px] text-muted-foreground bg-primary/[0.025] border border-primary/10 rounded-xl p-2"
              >
                <SparklesIcon class="size-3 text-primary shrink-0 mt-0.5" />
                <span class="leading-relaxed">{{ getItemNote(item) }}</span>
              </div>

              <!-- Content Comparison or Preview -->
              <div class="flex flex-col gap-2 w-full">
                <!-- If both previous and new content exist: Show comparison -->
                <template v-if="getItemPreviousContent(item) && getItemContent(item)">
                  <!-- 1. Previous Content -->
                  <div class="w-full rounded-xl bg-destructive/[0.03] dark:bg-destructive/[0.05] border border-destructive/15 p-2.5 flex flex-col gap-1">
                    <div class="flex items-center justify-between">
                      <span class="text-[9.5px] font-bold text-destructive bg-destructive/10 px-1.5 py-0.2 rounded-md">
                        {{ languageStore.t('متن قبلی', 'Previous Content') }}
                      </span>
                    </div>
                    <div class="text-xs text-foreground/80 leading-relaxed whitespace-pre-wrap">
                      <FormattedText :content="getItemPreviousContent(item)" />
                    </div>
                  </div>

                  <!-- 2. New Content -->
                  <div class="w-full rounded-xl bg-primary/[0.03] dark:bg-primary/[0.05] border border-primary/15 p-2.5 flex flex-col gap-1">
                    <div class="flex items-center justify-between">
                      <span class="text-[9.5px] font-bold text-primary bg-primary/10 px-1.5 py-0.2 rounded-md">
                        {{ languageStore.t('متن ویرایش‌شده', 'Revised Content') }}
                      </span>
                    </div>
                    <div class="text-xs sm:text-[12.5px] font-medium text-foreground/95 leading-relaxed whitespace-pre-wrap">
                      <FormattedText :content="getItemContent(item)" />
                    </div>
                  </div>
                </template>

                <!-- Otherwise show single revision content -->
                <div 
                  v-else 
                  class="text-xs sm:text-[12.5px] text-foreground/90 bg-muted/20 border border-border/30 p-3 rounded-xl leading-relaxed whitespace-pre-wrap"
                >
                  <FormattedText :content="getItemContent(item)" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Footer (طراحی فشرده و متناسب با ابعاد پروژه) -->
      <DialogFooter class="px-5 py-3 border-t border-border/40 bg-muted/20 flex flex-row justify-between items-center gap-2">
        <span class="text-[10px] sm:text-[10.5px] text-muted-foreground font-medium">
          {{ history.length > 0 ? languageStore.t('ثبت شده در زنجیره تغییرات تاپیک', 'Recorded in topic audit log') : '' }}
        </span>
        <Button 
          variant="outline" 
          size="sm" 
          class="rounded-xl text-xs h-8 px-4 cursor-pointer border-border/70"
          @click="emit('update:open', false)"
        >
          {{ languageStore.t('بستن', 'Close') }}
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
