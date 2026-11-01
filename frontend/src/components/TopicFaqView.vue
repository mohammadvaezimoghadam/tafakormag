<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import PlatformHeader from './PlatformHeader.vue'
import CreateEditFaqModal from './CreateEditFaqModal.vue'
import ConfirmModal from './ConfirmModal.vue'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import {
  SearchIcon,
  PlusIcon,
  ChevronDownIcon,
  PencilIcon,
  Trash2Icon,
  HelpCircleIcon,
  XIcon
} from '@lucide/vue'
import { useLanguageStore } from '@/stores/languageStore'
import { useToastStore } from '@/stores/toastStore'
import {
  fetchTopicFaqs,
  createTopicFaq,
  updateTopicFaq,
  deleteTopicFaq,
  type TopicFAQ
} from '@/api'

const props = withDefaults(defineProps<{
  topic: {
    id: string | number
    name?: string
    title?: string
    created_by?: any
    [key: string]: any
  } | null
  isOwner?: boolean
  isAdmin?: boolean
  forcedState?: 'default' | 'loading' | 'empty' | null
  initialFaqs?: TopicFAQ[] | null
}>(), {
  topic: null,
  isOwner: false,
  isAdmin: false,
  forcedState: null,
  initialFaqs: null
})

const emit = defineEmits<{
  (e: 'back'): void
  (e: 'faq-count-changed', count: number): void
}>()

const languageStore = useLanguageStore()
const toastStore = useToastStore()

// State
const loading = ref(false)
const faqs = ref<TopicFAQ[]>([])
const searchQuery = ref('')
const openFaqId = ref<number | null>(null)

// Modal State
const isModalOpen = ref(false)
const faqToEdit = ref<TopicFAQ | null>(null)
const isSubmitting = ref(false)

// Delete State
const isConfirmDeleteOpen = ref(false)
const faqToDelete = ref<TopicFAQ | null>(null)
const isDeleting = ref(false)

const canManage = computed(() => {
  return props.isOwner || props.isAdmin
})

const loadFaqs = async () => {
  if (props.forcedState === 'loading') {
    loading.value = true
    return
  }
  if (props.forcedState === 'empty') {
    loading.value = false
    faqs.value = []
    emit('faq-count-changed', 0)
    return
  }
  if (props.initialFaqs) {
    loading.value = false
    faqs.value = [...props.initialFaqs]
    emit('faq-count-changed', faqs.value.length)
    return
  }

  if (!props.topic?.id) return
  loading.value = true
  try {
    const res = await fetchTopicFaqs(props.topic.id)
    faqs.value = res.data || []
    emit('faq-count-changed', faqs.value.length)
  } catch (err) {
    console.error('Failed to load FAQs:', err)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadFaqs()
})

watch(() => props.topic?.id, (newId) => {
  if (newId) {
    loadFaqs()
  }
})

watch(() => [props.forcedState, props.initialFaqs], () => {
  loadFaqs()
}, { deep: true })

// Filtered FAQs based on real-time search
const filteredFaqs = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()
  if (!query) return faqs.value
  return faqs.value.filter(item =>
    item.question.toLowerCase().includes(query) ||
    item.answer.toLowerCase().includes(query)
  )
})

const toggleAccordion = (id: number) => {
  openFaqId.value = openFaqId.value === id ? null : id
}

// Handlers for Add / Edit
const handleOpenCreateModal = () => {
  faqToEdit.value = null
  isModalOpen.value = true
}

const handleOpenEditModal = (faq: TopicFAQ) => {
  faqToEdit.value = faq
  isModalOpen.value = true
}

const handleSaveFaq = async (payload: { question: string; answer: string; order: number; is_published: boolean }) => {
  isSubmitting.value = true
  try {
    if (props.initialFaqs) {
      if (faqToEdit.value) {
        const index = faqs.value.findIndex(f => f.id === faqToEdit.value!.id)
        if (index !== -1 && faqs.value[index]) {
          const current = faqs.value[index]!
          faqs.value[index] = {
            ...current,
            ...payload,
            id: current.id,
            topic: current.topic,
            created_at: current.created_at,
            updated_at: new Date().toISOString()
          }
        }
      } else {
        const newFaq: TopicFAQ = {
          id: Date.now(),
          topic: Number(props.topic?.id) || 1,
          question: payload.question,
          answer: payload.answer,
          order: payload.order,
          is_published: payload.is_published,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        }
        faqs.value.push(newFaq)
        emit('faq-count-changed', faqs.value.length)
      }
      toastStore.triggerToast(languageStore.t('عملیات با موفقیت انجام شد.', 'Action completed successfully.'), 'success')
      isModalOpen.value = false
      return
    }

    if (!props.topic?.id) return
    if (faqToEdit.value) {
      const res = await updateTopicFaq(faqToEdit.value.id, payload)
      const index = faqs.value.findIndex(f => f.id === faqToEdit.value!.id)
      if (index !== -1) {
        faqs.value[index] = res.data
      }
      toastStore.triggerToast(languageStore.t('سوال متداول با موفقیت ویرایش شد.', 'FAQ updated successfully.'), 'success')
    } else {
      const res = await createTopicFaq(props.topic.id, payload)
      faqs.value.push(res.data)
      emit('faq-count-changed', faqs.value.length)
      toastStore.triggerToast(languageStore.t('سوال متداول با موفقیت ایجاد شد.', 'FAQ created successfully.'), 'success')
    }
    isModalOpen.value = false
  } catch (err: any) {
    console.error('Failed to save FAQ:', err)
  } finally {
    isSubmitting.value = false
  }
}

// Handlers for Delete
const handlePromptDelete = (faq: TopicFAQ) => {
  faqToDelete.value = faq
  isConfirmDeleteOpen.value = true
}

const handleConfirmDelete = async () => {
  if (!faqToDelete.value) return
  isDeleting.value = true
  try {
    if (props.initialFaqs) {
      faqs.value = faqs.value.filter(f => f.id !== faqToDelete.value!.id)
      emit('faq-count-changed', faqs.value.length)
      toastStore.triggerToast(languageStore.t('سوال متداول با موفقیت حذف شد.', 'FAQ deleted successfully.'), 'success')
      isConfirmDeleteOpen.value = false
      faqToDelete.value = null
      return
    }

    await deleteTopicFaq(faqToDelete.value.id)
    faqs.value = faqs.value.filter(f => f.id !== faqToDelete.value!.id)
    emit('faq-count-changed', faqs.value.length)
    toastStore.triggerToast(languageStore.t('سوال متداول با موفقیت حذف شد.', 'FAQ deleted successfully.'), 'success')
    isConfirmDeleteOpen.value = false
    faqToDelete.value = null
  } catch (err) {
    console.error('Failed to delete FAQ:', err)
  } finally {
    isDeleting.value = false
  }
}
</script>

<template>
  <div
    class="w-full flex flex-col gap-4 text-start font-sans animate-in fade-in slide-in-from-bottom-3 duration-300 pb-20"
    :dir="languageStore.dir"
  >
    <!-- Header -->
    <PlatformHeader
      :is-inner-page="true"
      :inner-title="languageStore.t('سوالات متداول', 'FAQ')"
      :title="topic?.name || topic?.title || languageStore.t('تاپیک', 'Topic')"
      @back="emit('back')"
    />

    <!-- Top Action Bar: Search & Add Button -->
    <div class="flex items-center gap-2 px-1">
      <!-- Live Search Input -->
      <div class="relative flex-1">
        <SearchIcon class="size-4 absolute start-3 top-1/2 -translate-y-1/2 text-muted-foreground/70 pointer-events-none" />
        <Input
          type="text"
          v-model="searchQuery"
          :placeholder="languageStore.t('جستجو در سوالات و پاسخ‌ها...', 'Search questions & answers...')"
          class="h-9.5 ps-9 text-xs font-medium focus-visible:ring-primary/20 bg-card/25 dark:bg-card/15 border-border/60"
        />
        <button
          v-if="searchQuery"
          @click="searchQuery = ''"
          class="size-5 absolute end-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground flex items-center justify-center cursor-pointer"
        >
          <XIcon class="size-3.5" />
        </button>
      </div>

      <!-- Add New FAQ Button (For Topic Owner / Admin) -->
      <Button
        v-if="canManage"
        size="sm"
        @click="handleOpenCreateModal"
        class="h-9.5 text-xs font-bold shrink-0 flex items-center gap-1.5 cursor-pointer shadow-xs"
      >
        <PlusIcon class="size-3.5" />
        <span class="hidden sm:inline">{{ languageStore.t('افزودن سوال', 'Add FAQ') }}</span>
      </Button>
    </div>

    <!-- Skeletons while Loading -->
    <div v-if="loading" class="flex flex-col gap-2.5 w-full">
      <div
        v-for="i in 3"
        :key="'faq-skel-' + i"
        class="w-full bg-card/25 dark:bg-card/15 border border-border/50 rounded-2xl p-4 flex flex-col gap-2.5 animate-pulse"
      >
        <div class="flex items-center justify-between">
          <Skeleton class="h-4 w-48 rounded-md" />
          <Skeleton class="size-4 rounded-full" />
        </div>
      </div>
    </div>

    <!-- Main FAQ List Container -->
    <div
      v-else-if="filteredFaqs.length > 0"
      class="flex flex-col gap-2 w-full bg-card/25 dark:bg-card/15 border border-border/50 rounded-3xl p-2.5 shadow-xs"
    >
      <Collapsible
        v-for="(faq, idx) in filteredFaqs"
        :key="faq.id"
        :open="openFaqId === faq.id"
        @update:open="toggleAccordion(faq.id)"
        class="w-full rounded-2xl border border-border/40 bg-card/30 dark:bg-card/20 overflow-hidden transition-all duration-200"
      >
        <!-- Question Trigger -->
        <CollapsibleTrigger class="w-full flex items-center justify-between gap-3 p-3.5 hover:bg-secondary/30 transition-colors text-start cursor-pointer group">
          <div class="flex items-center gap-2.5 min-w-0 flex-1">
            <!-- Number badge -->
            <span class="size-5.5 rounded-full bg-primary/10 text-primary font-bold text-[10px] flex items-center justify-center shrink-0 select-none">
              {{ idx + 1 }}
            </span>

            <!-- Question Text -->
            <span class="text-xs font-bold text-foreground leading-snug line-clamp-2">
              {{ faq.question }}
            </span>

            <!-- Draft Status Badge -->
            <Badge
              v-if="!faq.is_published"
              variant="outline"
              class="text-[9px] px-1.5 py-0 border-amber-500/30 text-amber-500 shrink-0 select-none"
            >
              {{ languageStore.t('پیش‌نویس', 'Draft') }}
            </Badge>
          </div>

          <div class="flex items-center gap-1.5 shrink-0" @click.stop>
            <!-- Admin Actions: Edit & Delete -->
            <template v-if="canManage">
              <button
                type="button"
                @click.stop="handleOpenEditModal(faq)"
                class="size-7 rounded-lg flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors cursor-pointer border-0 outline-none"
                :title="languageStore.t('ویرایش', 'Edit')"
              >
                <PencilIcon class="size-3.5" />
              </button>
              <button
                type="button"
                @click.stop="handlePromptDelete(faq)"
                class="size-7 rounded-lg flex items-center justify-center text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors cursor-pointer border-0 outline-none"
                :title="languageStore.t('حذف', 'Delete')"
              >
                <Trash2Icon class="size-3.5" />
              </button>
            </template>

            <!-- Accordion Chevron -->
            <div class="size-7 rounded-lg flex items-center justify-center text-muted-foreground transition-transform duration-200" :class="{ 'rotate-180 text-foreground': openFaqId === faq.id }">
              <ChevronDownIcon class="size-4" />
            </div>
          </div>
        </CollapsibleTrigger>

        <!-- Answer Content -->
        <CollapsibleContent>
          <div class="px-4 pb-4 pt-1 text-[11.5px] text-foreground/85 dark:text-muted-foreground leading-relaxed whitespace-pre-line border-t border-border/25">
            {{ faq.answer }}
          </div>
        </CollapsibleContent>
      </Collapsible>
    </div>

    <!-- Empty State -->
    <div
      v-else
      class="text-center py-14 px-4 bg-card/20 rounded-3xl border border-border/50 flex flex-col items-center gap-3 select-none"
    >
      <div class="size-12 rounded-2xl bg-primary/10 flex items-center justify-center text-primary mb-1">
        <HelpCircleIcon class="size-6" />
      </div>
      <p class="text-xs font-bold text-foreground">
        {{ searchQuery ? languageStore.t('هیچ سوالی با این عبارت یافت نشد.', 'No FAQs match your search.') : languageStore.t('هنوز سوال متداولی برای این تاپیک ثبت نشده است.', 'No FAQs registered for this topic yet.') }}
      </p>
      <p class="text-[11px] text-muted-foreground max-w-[280px]">
        {{ canManage ? languageStore.t('با افزودن سوالات پرتکرار، به مخاطبان و اعضای تاپیک در دسترسی سریع به پاسخ‌ها کمک کنید.', 'Add frequently asked questions to help members quickly find answers.') : languageStore.t('به زودی سوالات و راهنمایی‌های این تاپیک در اینجا قرار خواهد گرفت.', 'Frequently asked questions will be posted here soon.') }}
      </p>
      <Button
        v-if="canManage && !searchQuery"
        size="sm"
        @click="handleOpenCreateModal"
        class="mt-2 text-xs flex items-center gap-1.5 cursor-pointer"
      >
        <PlusIcon class="size-3.5" />
        {{ languageStore.t('افزودن اولین سوال', 'Add First FAQ') }}
      </Button>
    </div>

    <!-- Create / Edit Modal -->
    <CreateEditFaqModal
      :is-open="isModalOpen"
      :faq-to-edit="faqToEdit"
      :is-submitting="isSubmitting"
      @close="isModalOpen = false"
      @save="handleSaveFaq"
    />

    <!-- Delete Confirmation Modal -->
    <ConfirmModal
      :is-open="isConfirmDeleteOpen"
      :title="languageStore.t('حذف سوال متداول', 'Delete FAQ')"
      :description="languageStore.t('آیا از حذف این سوال متداول اطمینان دارید؟ این عمل غیرقابل بازگشت است.', 'Are you sure you want to delete this FAQ? This action cannot be undone.')"
      :confirm-text="languageStore.t('بله، حذف شود', 'Yes, Delete')"
      :cancel-text="languageStore.t('انصراف', 'Cancel')"
      variant="destructive"
      @cancel="isConfirmDeleteOpen = false"
      @confirm="handleConfirmDelete"
    />
  </div>
</template>
