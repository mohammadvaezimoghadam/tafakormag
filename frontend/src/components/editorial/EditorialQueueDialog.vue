<script setup lang="ts">
import { computed } from 'vue'
import type { PostEditProposal } from '@/types/editorial'
import EditorialDiffCard from '@/components/editorial/EditorialDiffCard.vue'
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
import { 
  InboxIcon, 
  CheckCircle2Icon, 
  CheckCheckIcon,
  XIcon
} from '@lucide/vue'
import { useLanguageStore } from '@/stores/languageStore'

const languageStore = useLanguageStore()

const props = withDefaults(defineProps<{
  open: boolean
  proposals: PostEditProposal[]
  topicTitle?: string
  canApprove?: boolean
}>(), {
  proposals: () => [],
  canApprove: true,
})

const emit = defineEmits<{
  (e: 'update:open', val: boolean): void
  (e: 'approve', proposal: PostEditProposal): void
  (e: 'reject', proposal: PostEditProposal): void
  (e: 'approve-all'): void
}>()

const pendingProposals = computed(() => {
  return props.proposals.filter(p => p.status === 'pending')
})

const handleApprove = (proposal: PostEditProposal) => {
  emit('approve', proposal)
}

const handleReject = (proposal: PostEditProposal) => {
  emit('reject', proposal)
}
</script>

<template>
  <Dialog :open="open" @update:open="emit('update:open', $event)">
    <DialogContent 
      :show-close-button="false"
      class="max-w-[460px] w-[calc(100%-2rem)] sm:w-full max-h-[88vh] p-0 overflow-hidden flex flex-col text-start font-sans rounded-3xl border border-border/50 bg-background shadow-2xl"
      :dir="languageStore.dir"
    >
      <!-- Header Banner (مطابق الگوی طراحی یکپارچه دیالوگ‌های پلتفرم) -->
      <DialogHeader class="px-5 py-4 bg-gradient-to-br from-primary/15 via-primary/10 to-transparent border-b border-border/40 flex flex-row items-center justify-between space-y-0 shrink-0">
        <div class="flex items-center gap-3 min-w-0">
          <div class="size-9 rounded-2xl bg-primary/20 text-primary flex items-center justify-center shadow-xs shrink-0">
            <InboxIcon class="size-4.5" />
          </div>
          <div class="flex flex-col text-start min-w-0">
            <div class="flex items-center gap-2">
              <DialogTitle class="text-xs sm:text-sm font-black text-foreground font-sans truncate">
                {{ languageStore.t('میز ویراستاری تاپیک', 'Topic Editorial Queue') }}
              </DialogTitle>
              <Badge 
                v-if="pendingProposals.length > 0" 
                variant="secondary" 
                class="rounded-full px-2 py-0 text-[9.5px] font-bold border-0 bg-primary/10 text-primary shrink-0"
              >
                {{ pendingProposals.length }} {{ languageStore.t('در انتظار', 'Pending') }}
              </Badge>
            </div>
            <DialogDescription class="text-[10px] sm:text-[10.5px] text-muted-foreground mt-0.5 truncate max-w-[220px] sm:max-w-xs">
              {{ topicTitle ? topicTitle : languageStore.t('بررسی و تایید پیشنهادهای ویراستاران تاپیک', 'Review suggested edits from topic editors') }}
            </DialogDescription>
          </div>
        </div>

        <!-- دکمه بستن استاندارد هدر -->
        <button 
          @click="emit('update:open', false)"
          class="size-7 rounded-xl flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-muted/80 transition-colors cursor-pointer border-0 outline-none shrink-0"
          :title="languageStore.t('بستن', 'Close')"
        >
          <XIcon class="size-3.5" />
        </button>
      </DialogHeader>

      <!-- Scrollable Queue Body (بهینه‌شده برای اسکرول روان و سایز موبایل) -->
      <div class="flex-1 overflow-y-auto p-3.5 sm:p-4 flex flex-col gap-3.5 max-h-[calc(88vh-130px)]">
        <!-- Empty State -->
        <div 
          v-if="pendingProposals.length === 0" 
          class="flex flex-col items-center justify-center py-10 px-4 text-center my-auto"
        >
          <div class="size-12 rounded-2xl bg-emerald-500/10 text-emerald-500 flex items-center justify-center mb-3 shadow-xs">
            <CheckCircle2Icon class="size-6" />
          </div>
          <h4 class="text-xs sm:text-sm font-bold text-foreground mb-1">
            {{ languageStore.t('صف ویراستاری خالی است', 'Queue is Clean!') }}
          </h4>
          <p class="text-[11px] max-w-xs text-muted-foreground leading-relaxed">
            {{ languageStore.t('همه پیشنهادهای ویرایش بررسی شده‌اند و موردی در انتظار تایید شما نیست.', 'All edit suggestions have been reviewed.') }}
          </p>
        </div>

        <!-- Proposals List -->
        <template v-else>
          <EditorialDiffCard
            v-for="proposal in pendingProposals"
            :key="proposal.id"
            :proposal="proposal"
            :can-approve="canApprove"
            @approve="handleApprove"
            @reject="handleReject"
          />
        </template>
      </div>

      <!-- Footer Actions -->
      <DialogFooter class="px-4 py-3 border-t border-border/40 bg-muted/20 flex flex-row items-center justify-between gap-2 shrink-0">
        <span class="text-[10.5px] sm:text-[11px] text-muted-foreground font-medium">
          {{ pendingProposals.length }} {{ languageStore.t('پیشنهاد باقیمانده', 'proposals remaining') }}
        </span>

        <div class="flex items-center gap-2">
          <Button 
            variant="outline" 
            size="sm" 
            class="rounded-xl text-xs h-8.5 px-3 cursor-pointer border-border/70 text-foreground/80 hover:bg-muted"
            @click="emit('update:open', false)"
          >
            {{ languageStore.t('بستن', 'Close') }}
          </Button>

          <Button 
            v-if="canApprove && pendingProposals.length > 1"
            size="sm" 
            class="bg-primary hover:bg-primary/90 text-primary-foreground rounded-xl text-xs h-8.5 px-3.5 gap-1.5 cursor-pointer font-semibold shadow-none transition-all"
            @click="emit('approve-all')"
          >
            <CheckCheckIcon class="size-3.5" />
            <span>{{ languageStore.t('تایید همه', 'Approve All') }}</span>
          </Button>
        </div>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
