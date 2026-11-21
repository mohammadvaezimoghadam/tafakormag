<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { 
  InboxIcon, 
  CheckCheckIcon, 
  RefreshCwIcon, 
  CheckCircle2Icon,
  ArrowRightIcon,
  SparklesIcon,
  FileCheck2Icon,
  HistoryIcon,
  EyeIcon
} from '@lucide/vue'
import PlatformHeader from './PlatformHeader.vue'
import TopicMessageInput from './TopicMessageInput.vue'
import EditorialDiffCard from '@/components/editorial/EditorialDiffCard.vue'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useLanguageStore } from '@/stores/languageStore'
import { useToastStore } from '@/stores/toastStore'
import { 
  fetchEditProposals, 
  updateEditProposal,
  approveEditProposal, 
  rejectEditProposal, 
  approveAllEditProposals
} from '@/api'
import type { PostEditProposal } from '@/types/editorial'

const languageStore = useLanguageStore()
const toastStore = useToastStore()

const props = withDefaults(defineProps<{
  topicId?: string | number | null
  topicTitle?: string
  isOwner?: boolean
  initialProposals?: PostEditProposal[]
}>(), {
  topicId: null,
  topicTitle: '',
  isOwner: false,
})

const emit = defineEmits<{
  (e: 'back'): void
  (e: 'proposals-updated'): void
}>()

// State
const loading = ref(true)
const isBulkApproving = ref(false)
const proposals = ref<PostEditProposal[]>([])
const activeTab = ref<'pending' | 'all'>('pending')
const processingIds = ref<Record<string, boolean>>({})

// Header Title
const pageHeaderTitle = computed(() => {
  if (props.topicTitle) {
    return languageStore.t(`میز ویراستاری ${props.topicTitle}`, `${props.topicTitle} Editorial Desk`)
  }
  return languageStore.t('میز ویراستاری تاپیک', 'Topic Editorial Desk')
})

const pendingProposals = computed(() => {
  return proposals.value.filter(p => p.status === 'pending')
})

const filteredProposals = computed(() => {
  if (activeTab.value === 'pending') {
    return pendingProposals.value
  }
  return proposals.value
})

const loadProposals = async () => {
  if (props.initialProposals && props.initialProposals.length > 0 && !props.topicId) {
    proposals.value = [...props.initialProposals]
    loading.value = false
    return
  }

  if (!props.topicId) {
    loading.value = false
    return
  }

  loading.value = true
  try {
    const res = await fetchEditProposals({
      topic_id: props.topicId,
      status: activeTab.value === 'pending' ? 'pending' : undefined
    })
    proposals.value = res.data || []
  } catch (err: any) {
    console.error('Failed to load editorial proposals:', err)
  } finally {
    loading.value = false
  }
}

const handleApprove = async (proposal: PostEditProposal) => {
  if (!props.isOwner) {
    toastStore.triggerToast(
      languageStore.t('تنها سازنده و ادمین اصلی تاپیک مجاز به تایید پیشنهادات است.', 'Only the topic owner can approve proposals.'),
      'warning'
    )
    return
  }
  processingIds.value[proposal.id] = true
  try {
    await approveEditProposal(proposal.id)
    proposal.status = 'approved'
    toastStore.triggerToast(
      languageStore.t('پیشنهاد ویرایش با موفقیت تایید و منتشر شد.', 'Edit proposal approved and published successfully.'),
      'success'
    )
    emit('proposals-updated')
  } catch (err: any) {
    toastStore.triggerToast(
      err.response?.data?.error || languageStore.t('خطا در تایید پیشنهاد', 'Failed to approve proposal.'),
      'error'
    )
  } finally {
    processingIds.value[proposal.id] = false
  }
}

const handleReject = async (proposal: PostEditProposal) => {
  if (!props.isOwner) {
    toastStore.triggerToast(
      languageStore.t('تنها سازنده و ادمین اصلی تاپیک مجاز به رد پیشنهادات است.', 'Only the topic owner can reject proposals.'),
      'warning'
    )
    return
  }
  processingIds.value[proposal.id] = true
  try {
    await rejectEditProposal(proposal.id)
    proposal.status = 'rejected'
    toastStore.triggerToast(
      languageStore.t('پیشنهاد ویرایش رد شد.', 'Edit proposal rejected.'),
      'info'
    )
    emit('proposals-updated')
  } catch (err: any) {
    toastStore.triggerToast(
      err.response?.data?.error || languageStore.t('خطا در رد پیشنهاد', 'Failed to reject proposal.'),
      'error'
    )
  } finally {
    processingIds.value[proposal.id] = false
  }
}

const handleApproveAll = async () => {
  if (!props.isOwner || !props.topicId || pendingProposals.value.length === 0) return
  isBulkApproving.value = true
  try {
    await approveAllEditProposals(props.topicId)
    proposals.value.forEach(p => {
      if (p.status === 'pending') p.status = 'approved'
    })
    toastStore.triggerToast(
      languageStore.t('تمامی پیشنهادهای ویرایش تایید و اعمال شدند.', 'All edit proposals approved and applied.'),
      'success'
    )
    emit('proposals-updated')
  } catch (err: any) {
    toastStore.triggerToast(
      err.response?.data?.error || languageStore.t('خطا در تایید گروهی', 'Failed to bulk approve.'),
      'error'
    )
  } finally {
    isBulkApproving.value = false
  }
}

const handleUpdateProposal = async (proposal: PostEditProposal, newContent: string) => {
  try {
    await updateEditProposal(proposal.id, { proposed_content: newContent })
    proposal.proposedContent = newContent
    proposal.proposed_content = newContent
    toastStore.triggerToast(
      languageStore.t('پیشنهاد ویرایش با موفقیت اصلاح شد.', 'Edit proposal updated successfully.'),
      'success'
    )
    emit('proposals-updated')
  } catch (err: any) {
    toastStore.triggerToast(
      err.response?.data?.detail || err.response?.data?.error || languageStore.t('خطا در به‌روزرسانی پیشنهاد', 'Failed to update proposal.'),
      'error'
    )
  }
}

const editingProposal = ref<PostEditProposal | null>(null)

const handleStartEdit = (proposal: PostEditProposal) => {
  editingProposal.value = proposal
}

const handleCancelEditProposal = () => {
  editingProposal.value = null
}

const handleSaveProposalEdit = async (payload: { text: string }) => {
  if (!editingProposal.value) return
  const proposal = editingProposal.value
  try {
    await updateEditProposal(proposal.id, { proposed_content: payload.text })
    proposal.proposedContent = payload.text
    proposal.proposed_content = payload.text
    toastStore.triggerToast(
      languageStore.t('پیشنهاد ویرایش با موفقیت اصلاح شد.', 'Edit proposal updated successfully.'),
      'success'
    )
    editingProposal.value = null
    emit('proposals-updated')
  } catch (err: any) {
    toastStore.triggerToast(
      err.response?.data?.detail || err.response?.data?.error || languageStore.t('خطا در به‌روزرسانی پیشنهاد', 'Failed to update proposal.'),
      'error'
    )
  }
}

const handleTabChange = (val: string | number) => {
  activeTab.value = val as 'pending' | 'all'
  loadProposals()
}

onMounted(() => {
  loadProposals()
})
</script>

<template>
  <div 
    class="w-full flex flex-col gap-4 text-start font-sans select-none pb-24" 
    :dir="languageStore.dir"
  >
    <!-- Subview Header -->
    <PlatformHeader 
      is-inner-page
      :inner-title="pageHeaderTitle"
      :show-options-button="false"
      @back="emit('back')"
    />

    <!-- View-only notice banner for non-owner admins -->
    <div 
      v-if="!isOwner" 
      class="w-full bg-muted/60 border border-border/50 text-foreground/80 px-4 py-3 rounded-2xl flex items-center gap-3 text-xs leading-relaxed font-medium"
    >
      <div class="size-8 rounded-xl bg-amber-500/10 text-amber-600 dark:text-amber-400 flex items-center justify-center shrink-0">
        <EyeIcon class="size-4" />
      </div>
      <div class="flex flex-col gap-0.5 text-start">
        <span class="font-bold text-foreground">{{ languageStore.t('دسترسی فقط مشاهده (میز ویراستاری)', 'View-Only Access (Editorial Desk)') }}</span>
        <span class="text-muted-foreground text-[11px]">{{ languageStore.t('شما به عنوان ادمین تاپیک به این بخش دسترسی دارید؛ اما تایید یا رد پیشنهادات ویرایش منحصراً در اختیار ادمین اصلی و سازنده تاپیک است.', 'As a topic admin you can review proposals; however, approving or rejecting changes is restricted to the topic creator.') }}</span>
      </div>
    </div>

    <!-- Quick Stats & Toolbar Card -->
    <div class="w-full bg-card/45 backdrop-blur-md border border-border/40 rounded-3xl p-3.5 sm:p-4 shadow-xs flex flex-col sm:flex-row items-center justify-between gap-3">
      <!-- Left side: Tabs for filtering -->
      <Tabs :model-value="activeTab" class="w-full sm:w-auto" @update:model-value="handleTabChange">
        <TabsList class="grid grid-cols-2 w-full sm:w-[260px] h-9 p-0.5 rounded-2xl bg-muted/50 border border-border/40">
          <TabsTrigger 
            value="pending" 
            class="text-xs font-semibold rounded-xl gap-1.5 cursor-pointer data-[state=active]:bg-background data-[state=active]:shadow-xs"
          >
            <FileCheck2Icon class="size-3.5 text-primary" />
            <span>{{ languageStore.t('در انتظار', 'Pending') }}</span>
            <Badge 
              v-if="pendingProposals.length > 0" 
              variant="default" 
              class="h-4 px-1.5 text-[10px] rounded-full font-bold"
            >
              {{ pendingProposals.length }}
            </Badge>
          </TabsTrigger>
          <TabsTrigger 
            value="all" 
            class="text-xs font-semibold rounded-xl gap-1.5 cursor-pointer data-[state=active]:bg-background data-[state=active]:shadow-xs"
          >
            <HistoryIcon class="size-3.5 text-muted-foreground" />
            <span>{{ languageStore.t('همه سوابق', 'History') }}</span>
          </TabsTrigger>
        </TabsList>
      </Tabs>

      <!-- Right side: Actions -->
      <div class="flex items-center gap-2 w-full sm:w-auto justify-end">
        <!-- Reload Button -->
        <Button 
          variant="outline" 
          size="sm" 
          class="h-8.5 rounded-xl text-xs gap-1.5 border-border/60 cursor-pointer"
          :disabled="loading"
          @click="loadProposals"
        >
          <RefreshCwIcon class="size-3.5 text-muted-foreground" :class="{ 'animate-spin': loading }" />
          <span class="hidden sm:inline">{{ languageStore.t('بروزرسانی', 'Refresh') }}</span>
        </Button>

        <!-- Bulk Approve Button (فقط برای ادمین اصلی/مالک تاپیک) -->
        <Button 
          v-if="isOwner && pendingProposals.length > 1 && activeTab === 'pending'"
          size="sm" 
          class="h-8.5 bg-primary hover:bg-primary/90 text-primary-foreground font-semibold rounded-xl text-xs gap-1.5 shadow-none cursor-pointer"
          :disabled="isBulkApproving"
          @click="handleApproveAll"
        >
          <CheckCheckIcon class="size-4" :class="{ 'animate-spin': isBulkApproving }" />
          <span>{{ languageStore.t('تایید همه موارد', 'Approve All') }}</span>
        </Button>
      </div>
    </div>

    <!-- Content Area -->
    <div class="flex flex-col gap-4 w-full" :class="{ 'pb-36': !!editingProposal }">
      <!-- Loading Skeletons -->
      <template v-if="loading">
        <div 
          v-for="i in 2" 
          :key="'editorial-skel-' + i" 
          class="w-full bg-card/35 border border-border/40 rounded-3xl p-4 sm:p-5 flex flex-col gap-4 animate-pulse"
        >
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-3">
              <Skeleton class="size-10 rounded-full" />
              <div class="flex flex-col gap-2">
                <Skeleton class="h-4 w-28 rounded-md" />
                <Skeleton class="h-3 w-16 rounded-md" />
              </div>
            </div>
            <Skeleton class="h-6 w-20 rounded-full" />
          </div>
          <Skeleton class="h-20 w-full rounded-2xl" />
          <Skeleton class="h-20 w-full rounded-2xl" />
          <div class="flex justify-end gap-2 pt-2">
            <Skeleton class="h-8 w-20 rounded-xl" />
            <Skeleton class="h-8 w-28 rounded-xl" />
          </div>
        </div>
      </template>

      <!-- Empty State -->
      <div 
        v-else-if="filteredProposals.length === 0" 
        class="w-full bg-card/30 backdrop-blur-md border border-border/40 rounded-3xl p-8 sm:p-12 flex flex-col items-center justify-center text-center shadow-xs"
      >
        <div class="size-16 sm:size-20 rounded-3xl bg-emerald-500/10 text-emerald-500 flex items-center justify-center mb-4 shadow-inner">
          <CheckCircle2Icon class="size-8 sm:size-10" />
        </div>
        <h3 class="text-base sm:text-lg font-bold text-foreground mb-1.5">
          {{ activeTab === 'pending' 
            ? languageStore.t('صف ویراستاری خالی است', 'Queue is Clean!') 
            : languageStore.t('هیچ پیشنهادی یافت نشد', 'No Proposals Found') 
          }}
        </h3>
        <p class="text-xs sm:text-sm max-w-sm text-muted-foreground leading-relaxed mb-6">
          {{ activeTab === 'pending'
            ? languageStore.t('همه پیشنهادهای ویرایش بررسی شده‌اند و مورد جدیدی در انتظار تایید شما نیست.', 'All edit suggestions have been reviewed. There are no pending proposals.')
            : languageStore.t('تاکنون پیشنهادی برای ویرایش مطالب این تاپیک ارسال نشده است.', 'No edit proposals have been submitted for this topic yet.')
          }}
        </p>
        <Button 
          variant="outline" 
          size="sm" 
          class="rounded-2xl text-xs gap-2 cursor-pointer border-border/70 hover:bg-muted" 
          @click="emit('back')"
        >
          <ArrowRightIcon class="size-3.5 rtl:rotate-180" />
          <span>{{ languageStore.t('بازگشت به یادداشت‌ها', 'Back to Feed') }}</span>
        </Button>
      </div>

      <!-- Proposals List -->
      <template v-else>
        <EditorialDiffCard
          v-for="proposal in filteredProposals"
          :key="proposal.id"
          :proposal="proposal"
          :can-approve="isOwner"
          @approve="handleApprove"
          @reject="handleReject"
          @edit="handleStartEdit"
          @update="handleUpdateProposal"
        />
      </template>
    </div>

    <!-- Bottom Message Input Bar for Editing Proposal -->
    <transition name="sheet-slide">
      <div 
        v-if="editingProposal"
        class="fixed bottom-0 left-1/2 -translate-x-1/2 bg-background/80 dark:bg-background/70 backdrop-blur-md border-t border-border/40 p-4 pb-[max(1rem,env(safe-area-inset-bottom))] z-40 max-w-[500px] w-full shadow-lg"
      >
        <TopicMessageInput
          :key="'edit-prop-' + editingProposal.id"
          :is-proposal-mode="true"
          :initial-text="editingProposal.proposedContent"
          :placeholder="languageStore.t('متن اصلاح‌شده پیشنهاد را بنویسید...', 'Write corrected proposal...')"
          @submit-proposal="handleSaveProposalEdit"
          @cancel-proposal="handleCancelEditProposal"
        />
      </div>
    </transition>
  </div>
</template>

<style scoped>
.sheet-slide-enter-active,
.sheet-slide-leave-active {
  transition: transform 0.35s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.25s ease;
}

.sheet-slide-enter-from,
.sheet-slide-leave-to {
  transform: translate(-50%, 100%);
  opacity: 0;
}
</style>
