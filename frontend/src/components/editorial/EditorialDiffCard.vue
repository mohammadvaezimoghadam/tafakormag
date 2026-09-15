<script setup lang="ts">
import { ref, watch } from 'vue'
import type { PostEditProposal } from '@/types/editorial'
import FormattedText from '@/components/common/FormattedText.vue'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { 
  CheckIcon, 
  XIcon, 
  ClockIcon, 
  FileTextIcon, 
  CheckCircle2Icon,
  XCircleIcon,
  EyeIcon,
  PencilIcon
} from '@lucide/vue'
import { useLanguageStore } from '@/stores/languageStore'

const languageStore = useLanguageStore()

const props = withDefaults(defineProps<{
  proposal: PostEditProposal
  isCompact?: boolean
  canApprove?: boolean
  canEdit?: boolean
}>(), {
  canApprove: true,
  canEdit: true,
})

const emit = defineEmits<{
  (e: 'approve', proposal: PostEditProposal): void
  (e: 'reject', proposal: PostEditProposal): void
  (e: 'edit', proposal: PostEditProposal): void
  (e: 'update', proposal: PostEditProposal, newContent: string): void
}>()
</script>

<template>
  <div 
    class="w-full rounded-3xl border border-border/35 bg-card p-3.5 sm:p-5 transition-all duration-200 hover:border-border/50 flex flex-col gap-3.5 sm:gap-4 text-start shadow-none"
    :dir="languageStore.dir"
  >
    <!-- Header: Author/Editor Info & Status -->
    <div class="flex flex-wrap items-center justify-between gap-3 pb-1">
      <div class="flex items-center gap-3">
        <!-- Avatar -->
        <Avatar class="size-10 shadow-none border border-border/40">
          <AvatarImage :src="proposal.editor.avatar || ''" :alt="proposal.editor.name" />
          <AvatarFallback class="bg-primary/10 text-primary font-bold text-xs">
            {{ proposal.editor.name?.charAt(0) || 'U' }}
          </AvatarFallback>
        </Avatar>

        <!-- Editor Name & Timestamp -->
        <div class="flex flex-col text-start">
          <div class="flex items-center gap-1.5 flex-wrap">
            <span class="text-xs sm:text-sm font-bold text-foreground">{{ proposal.editor.name }}</span>
            <Badge variant="secondary" class="text-[10px] px-1.5 py-0 h-4 font-medium border-0">
              {{ languageStore.t('ویراستار تاپیک', 'Topic Editor') }}
            </Badge>
            <span v-if="proposal.postId" class="text-[10px] text-muted-foreground/80 font-mono">
              #{{ proposal.postId }}
            </span>
          </div>
          <div class="flex items-center gap-1.5 text-[10px] text-muted-foreground mt-0.5 font-medium">
            <ClockIcon class="size-3 text-primary" />
            <span>{{ proposal.createdAt }}</span>
          </div>
        </div>
      </div>

      <!-- Status Badge (دایره نارنجی برداشته شده) -->
      <div class="flex items-center gap-2">
        <Badge 
          :variant="proposal.status === 'rejected' ? 'destructive' : 'secondary'"
          class="capitalize text-xs font-medium px-2.5 py-0.5 gap-1 border-0"
        >
          <template v-if="proposal.status === 'pending'">
            <span>{{ languageStore.t('در انتظار بررسی', 'Pending Review') }}</span>
          </template>
          <template v-else-if="proposal.status === 'approved'">
            <CheckCircle2Icon class="size-3.5 text-emerald-500 inline-block" />
            <span>{{ languageStore.t('تایید شده', 'Approved') }}</span>
          </template>
          <template v-else>
            <XCircleIcon class="size-3.5 text-destructive inline-block" />
            <span>{{ languageStore.t('رد شده', 'Rejected') }}</span>
          </template>
        </Badge>
      </div>
    </div>

    <!-- Stacked Comparison Cards (زیر هم، بدون بوردرهای اضافه) -->
    <div class="flex flex-col gap-3 w-full">
      
      <!-- 1. Original / Current Version (نسخه کنونی / فعلی - بدون بوردر) -->
      <div class="w-full rounded-2xl bg-destructive/[0.025] dark:bg-destructive/[0.04] p-4 sm:p-4.5 flex flex-col gap-2.5 transition-all">
        <!-- Sub-card Header -->
        <div class="flex items-center justify-between gap-2 pb-1">
          <Badge variant="outline" class="border-0 bg-destructive/10 text-destructive text-[11px] font-medium px-2 py-0.5">
            {{ languageStore.t('نسخه کنونی (فعلی)', 'Current Version') }}
          </Badge>
          <span class="text-[10px] text-destructive/80 font-medium">
            {{ languageStore.t('جایگزین خواهد شد', 'Will be replaced') }}
          </span>
        </div>

        <!-- Content with FormattedText -->
        <div class="text-foreground/80 text-sm leading-relaxed whitespace-pre-wrap">
          <FormattedText 
            :content="proposal.originalContent" 
            class-name="text-sm font-medium leading-relaxed text-foreground/85 text-start"
            dir="auto"
          />
        </div>
      </div>

      <!-- 2. Proposed Version (نسخه ویراستاری شده - بدون بوردر و سایه، بدون ستاره) -->
      <div class="w-full rounded-2xl bg-emerald-500/[0.035] dark:bg-emerald-500/[0.07] p-4 sm:p-4.5 flex flex-col gap-2.5 transition-all">
        <!-- Sub-card Header (متن شده: نسخه ویراستاری شده، بدون آیکون ستاره) -->
        <div class="flex items-center justify-between gap-2 pb-1">
          <div class="flex items-center gap-2">
            <Badge variant="outline" class="border-0 bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 text-[11px] font-semibold px-2 py-0.5">
              {{ languageStore.t('نسخه ویراستاری شده', 'Edited Version') }}
            </Badge>
            <span class="text-[10px] text-emerald-600 dark:text-emerald-400 font-semibold">
              {{ languageStore.t('متن پس از تایید', 'After approval') }}
            </span>
          </div>

          <!-- Edit button for pending proposal -->
          <Button
            v-if="proposal.status === 'pending' && canEdit"
            variant="ghost"
            size="xs"
            class="h-6 px-2 text-[11px] font-medium text-emerald-700 dark:text-emerald-400 hover:bg-emerald-500/15 gap-1 rounded-lg cursor-pointer transition-all"
            @click="emit('edit', proposal)"
            :title="languageStore.t('ویرایش این پیشنهاد در ورودی پیام', 'Edit this proposal in message input')"
          >
            <PencilIcon class="size-3" />
            <span>{{ languageStore.t('ویرایش پیشنهاد', 'Edit proposal') }}</span>
          </Button>
        </div>

        <!-- Content with FormattedText -->
        <div class="text-foreground text-sm leading-relaxed whitespace-pre-wrap">
          <FormattedText 
            :content="proposal.proposedContent" 
            class-name="text-sm font-medium leading-relaxed text-foreground/95 text-start"
            dir="auto"
          />
        </div>
      </div>

    </div>

    <!-- Actions Footer -->
    <div 
      v-if="proposal.status === 'pending'" 
      class="mt-1 pt-1 flex flex-wrap items-center justify-between gap-3"
    >
      <div class="text-xs text-muted-foreground flex items-center gap-1.5">
        <FileTextIcon class="size-3.5 text-primary" />
        <span>{{ languageStore.t('تغییرات بعد از تایید فوراً در تاپیک و پیام‌رسان‌ها اعمال می‌شوند.', 'Changes apply to topic and channels immediately upon approval.') }}</span>
      </div>

      <!-- دکمه‌ها در سمت چپ برای ادمین اصلی تاپیک -->
      <div v-if="canApprove" class="flex items-center gap-2 mr-auto">
        <Button 
          variant="outline" 
          size="sm"
          class="border-border/70 text-foreground/80 hover:bg-muted hover:text-foreground h-9 px-3.5 rounded-xl gap-1.5 text-xs font-medium cursor-pointer transition-all"
          @click="emit('reject', proposal)"
        >
          <XIcon class="size-4" />
          <span>{{ languageStore.t('رد پیشنهاد', 'Reject') }}</span>
        </Button>
        <Button 
          size="sm"
          class="bg-primary hover:bg-primary/90 text-primary-foreground h-9 px-4 rounded-xl gap-1.5 text-xs font-semibold shadow-none cursor-pointer transition-all"
          @click="emit('approve', proposal)"
        >
          <CheckIcon class="size-4" />
          <span>{{ languageStore.t('تایید و اعمال تغییرات', 'Approve Changes') }}</span>
        </Button>
      </div>

      <!-- برچسب فقط مشاهده برای سایر ادمین‌ها -->
      <div 
        v-else 
        class="flex items-center gap-1.5 text-xs text-muted-foreground bg-muted/50 px-3 py-1.5 rounded-xl border border-border/40 mr-auto font-medium"
      >
        <EyeIcon class="size-3.5 text-muted-foreground" />
        <span>{{ languageStore.t('فقط ادمین اصلی تاپیک امکان تایید یا رد دارد (فقط مشاهده)', 'Only topic creator can approve/reject (view only)') }}</span>
      </div>
    </div>
  </div>
</template>
