<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useLanguageStore } from '@/stores/languageStore'
import { useUserStore } from '@/stores/userStore'
import {
  sendTopicChatMessage,
  fetchTopicChatHistory,
  clearTopicChatHistory,
  type TopicChatMessage,
  type TopicChatSource
} from '@/api'
import FormattedText from '@/components/common/FormattedText.vue'
import PlatformHeader from '@/components/PlatformHeader.vue'
import TopicMessageInput from '@/components/TopicMessageInput.vue'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Marker,
  MarkerContent,
  MarkerIcon
} from '@/components/ui/marker'
import {
  SparklesIcon,
  HelpCircleIcon,
  SendIcon,
  ArrowRightIcon,
  Trash2Icon,
  CopyIcon,
  CheckIcon,
  BookOpenIcon,
  FileTextIcon,
  BotIcon,
  UserIcon,
  ChevronDownIcon
} from '@lucide/vue'

interface Props {
  topic: { id: number | string; title?: string; name?: string; description?: string }
  isOwner?: boolean
  isAdmin?: boolean
  simulated?: boolean
  initialFaqs?: Array<{ id: number | string; question: string; answer?: string }>
  showHeader?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isOwner: false,
  isAdmin: false,
  simulated: false,
  initialFaqs: () => [],
  showHeader: false
})

const emit = defineEmits<{
  (e: 'back'): void
}>()

const languageStore = useLanguageStore()
const userStore = useUserStore()

const topicId = computed(() => props.topic?.id || '')
const topicName = computed(() => props.topic?.name || props.topic?.title || 'تاپیک')

const userProfile = computed(() => userStore.userProfile)
const userInitial = computed(() => {
  const name = userProfile.value?.first_name || userProfile.value?.name || 'U'
  return name.charAt(0).toUpperCase()
})

// Chat state
const messages = ref<TopicChatMessage[]>([])
const sessionId = ref<string | null>(null)
const inputQuery = ref('')
const isSending = ref(false)
const isLoadingHistory = ref(false)
const messagesContainerRef = ref<HTMLElement | null>(null)

// Copy feedback tracking
const copiedMessageId = ref<string | null>(null)

// Format timestamps
const formatTime = (dateStr?: string) => {
  if (!dateStr) return ''
  try {
    const d = new Date(dateStr)
    const hours = d.getHours().toString().padStart(2, '0')
    const minutes = d.getMinutes().toString().padStart(2, '0')
    return languageStore.n(`${hours}:${minutes}`)
  } catch {
    return ''
  }
}

const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainerRef.value) {
    messagesContainerRef.value.scrollTop = messagesContainerRef.value.scrollHeight
  }
}

const expandedSources = ref<Record<string | number, boolean>>({})
const toggleSources = (msgId: string | number) => {
  expandedSources.value[msgId] = !expandedSources.value[msgId]
}

// Load History
const loadHistory = async () => {
  if (props.simulated) {
    // In simulated mode, start clean with empty messages to show welcome state
    return
  }

  if (!topicId.value) return
  isLoadingHistory.value = true
  try {
    const res = await fetchTopicChatHistory(topicId.value, sessionId.value)
    if (res.data) {
      sessionId.value = res.data.session_id
      if (Array.isArray(res.data.messages) && res.data.messages.length > 0) {
        messages.value = res.data.messages
      } else {
        messages.value = []
      }
    }
  } catch (err) {
    messages.value = []
  } finally {
    isLoadingHistory.value = false
    scrollToBottom()
  }
}

// Send Message
const handleSendMessage = async (textToSend?: string) => {
  const query = (textToSend || inputQuery.value).trim()
  if (!query || isSending.value) return

  inputQuery.value = ''

  // Optimistic user message
  const tempUserMsg: TopicChatMessage = {
    id: `user-${Date.now()}`,
    role: 'user',
    content: query,
    created_at: new Date().toISOString()
  }
  messages.value.push(tempUserMsg)
  scrollToBottom()

  isSending.value = true

  if (props.simulated) {
    // Simulate RAG answer in Playground mode
    setTimeout(() => {
      let simulatedAnswer = `با بررسی محتوای پایگاه داده و یادداشت‌های تاپیک **${topicName.value}** (RAG):\n\nموضوع مطرح‌شده «${query}» بررسی گردید. بر اساس اسناد تاپیک، اطلاعات و نکات مرتبط در آرشیو تاپیک در دسترس اعضا می‌باشد.`
      const sources: TopicChatSource[] = [
        {
          type: 'post',
          id: 101,
          title: 'اسناد و چارچوب فعالیت تاپیک',
          preview: 'خلاصه آیین‌نامه و نحوه اشتراک‌گذاری منابع تاپیک'
        }
      ]

      messages.value.push({
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: simulatedAnswer,
        sources,
        created_at: new Date().toISOString()
      })
      isSending.value = false
      scrollToBottom()
    }, 600)
    return
  }

  try {
    const res = await sendTopicChatMessage(topicId.value, query, sessionId.value)
    if (res.data) {
      sessionId.value = res.data.session_id
      messages.value.push(res.data.assistant_message)
    }
  } catch (err: any) {
    messages.value.push({
      id: `err-${Date.now()}`,
      role: 'assistant',
      content: 'متاسفانه در برقراری ارتباط با مدل زبانی خطایی رخ داد. لطفا دوباره تلاش کنید.',
      created_at: new Date().toISOString()
    })
  } finally {
    isSending.value = false
    scrollToBottom()
  }
}

// Handle message sent from TopicMessageInput
const handleTopicInputSend = (message: { text: string }) => {
  if (message.text && message.text.trim()) {
    handleSendMessage(message.text.trim())
  }
}

// Clear chat history
const handleClearHistory = async () => {
  if (props.simulated) {
    messages.value = []
    return
  }

  try {
    await clearTopicChatHistory(topicId.value, sessionId.value)
    sessionId.value = null
    messages.value = []
    loadHistory()
  } catch (err) {
    //
  }
}

// Copy message text
const copyMessage = async (msg: TopicChatMessage) => {
  try {
    await navigator.clipboard.writeText(msg.content)
    copiedMessageId.value = msg.id
    setTimeout(() => {
      copiedMessageId.value = null
    }, 2000)
  } catch (err) {
    //
  }
}

onMounted(() => {
  loadHistory()
})
</script>

<template>
  <div 
    class="w-full flex-1 flex flex-col text-start font-sans select-none relative" 
    :class="[showHeader ? 'min-h-[calc(100vh-4rem)]' : 'h-[calc(100vh-6.5rem)]']"
    :dir="languageStore.dir"
  >
    <!-- Internal Header: Rendered only when requested by parent -->
    <PlatformHeader 
      v-if="showHeader"
      is-inner-page
      :inner-title="languageStore.t(`دستیار هوشمند ${topicName}`, `${topicName} AI Assistant`)"
      :show-options-button="false"
      :show-faq-button="false"
      @back="emit('back')"
    />

    <!-- Chat Messages Scroll Area -->
    <div 
      ref="messagesContainerRef"
      class="flex-1 min-h-0 overflow-y-auto px-4 py-4 flex flex-col gap-7 text-start scroll-smooth"
    >
      <!-- Empty State: Welcome in center with simple icon & waving hand 👋, disappears after first message -->
      <div 
        v-if="messages.length === 0 && !isLoadingHistory" 
        class="flex-1 flex flex-col items-center justify-center text-center p-6 my-auto gap-2 select-none animate-in fade-in zoom-in-95 duration-300"
      >
        <div class="size-16 rounded-3xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary shadow-xs">
          <BotIcon class="size-8" />
        </div>

        <h3 class="text-base font-extrabold text-foreground">
          {{ languageStore.t(`دستیار هوشمند ${topicName}`, `${topicName} AI Assistant`) }}
        </h3>
        
        <p class="text-xs text-muted-foreground/80 max-w-[280px] leading-relaxed">
          {{ languageStore.t('سلام! هر پرسشی درباره مطالب، اهداف یا اسناد این تاپیک دارید بپرسید تا با هوش مصنوعی پاسخ دهم.', 'Hello! Ask any question about this topic\'s content, goals, or documents.') }}
        </p>
      </div>

      <!-- Subtle Clear History Action when messages exist -->
      <div v-if="messages.length > 1" class="flex justify-center pb-2">
        <button
          type="button"
          @click="handleClearHistory"
          class="text-[10.5px] font-medium text-muted-foreground/60 hover:text-destructive flex items-center gap-1.5 px-3 py-1 rounded-full hover:bg-muted/40 transition-colors cursor-pointer"
          :title="languageStore.t('پاک کردن تاریخچه چت', 'Clear chat history')"
        >
          <Trash2Icon class="size-3" />
          <span>{{ languageStore.t('پاکسازی گفت‌وگو', 'Clear chat') }}</span>
        </button>
      </div>
      <template v-for="msg in messages" :key="msg.id">
        <!-- 1. USER MESSAGE (Aligned to Right in RTL, No Avatar, Post-like Card Background) -->
        <div v-if="msg.role === 'user'" class="flex flex-col items-start gap-1 w-full max-w-[85%] sm:max-w-[75%] pt-1">
          <div class="rounded-2xl px-4 py-2.5 text-xs font-medium leading-relaxed bg-card text-card-foreground border border-border/50 shadow-2xs text-right" dir="rtl">
            {{ msg.content }}
          </div>
          <span v-if="msg.created_at" class="pe-1 text-[10px] text-muted-foreground/70 font-sans font-medium">
            {{ formatTime(msg.created_at) }}
          </span>
        </div>

        <!-- 2. ASSISTANT MESSAGE (No background, icon at top in front of title with topic name) -->
        <div v-else class="flex flex-col items-start gap-2.5 w-full text-right pb-1" dir="rtl">
          <!-- Assistant Header: Icon + Title + AI/RAG Badge -->
          <div class="flex items-center gap-2 pb-0.5 text-[11px]">
            <div class="size-6 rounded-full bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-600 dark:text-amber-400 shrink-0">
              <HelpCircleIcon class="size-3.5" />
            </div>
            <span class="font-bold text-xs text-foreground/90">دستیار هوشمند {{ topicName }}</span>
            <Badge variant="secondary" class="text-[8.5px] px-1.5 py-0 h-4 border-none border-0 text-amber-600 dark:text-amber-400 bg-amber-500/10 font-mono shadow-none">
              AI • RAG
            </Badge>
          </div>

          <!-- Pure Markdown Generated Text (No background container) -->
          <div class="w-full text-foreground text-xs leading-relaxed ps-1 py-0.5">
            <FormattedText :content="msg.content" class-name="text-right" />
          </div>

          <!-- RAG Sources / Citations Pill List: Collapsible/Expandable -->
          <div v-if="msg.sources && msg.sources.length > 0" class="w-full mt-2 pt-1 ps-1 flex flex-col gap-2">
            <button
              type="button"
              @click="toggleSources(msg.id)"
              class="inline-flex items-center gap-1.5 text-[11px] font-bold text-muted-foreground hover:text-foreground transition-colors cursor-pointer select-none self-start py-0.5"
            >
              <BookOpenIcon class="size-3.5 text-amber-600 dark:text-amber-400" />
              <span>{{ languageStore.t('منابع استناد شده از تاپیک', 'Cited Topic Sources') }}</span>
              <span class="text-[9.5px] px-1.5 py-0.2 rounded-full bg-muted/70 text-muted-foreground font-mono">
                {{ languageStore.n(msg.sources.length) }}
              </span>
              <ChevronDownIcon 
                class="size-3.5 text-muted-foreground/70 transition-transform duration-200" 
                :class="{ 'rotate-180': expandedSources[msg.id] }" 
              />
            </button>

            <div v-if="expandedSources[msg.id]" class="flex flex-wrap gap-2 pt-1 animate-in fade-in duration-200">
              <div
                v-for="(source, sIdx) in msg.sources"
                :key="sIdx"
                class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-card border border-border/50 text-[10px] text-foreground/85 shadow-2xs hover:bg-muted/40 transition-colors"
                :title="source.preview || source.title"
              >
                <FileTextIcon class="size-3 text-blue-500 shrink-0" />
                <span class="font-semibold">{{ source.title }}</span>
              </div>
            </div>
          </div>

          <!-- Assistant Footer: Actions and Timestamp -->
          <div class="flex items-center gap-2 pt-1 ps-1">
            <Button
              variant="ghost"
              size="icon"
              class="size-6 rounded-md hover:bg-muted/80 text-muted-foreground hover:text-foreground cursor-pointer transition-colors"
              @click="copyMessage(msg)"
              :title="languageStore.t('کپی کردن پاسخ', 'Copy answer')"
              aria-label="Copy answer"
            >
              <CheckIcon v-if="copiedMessageId === msg.id" class="size-3 text-emerald-500" />
              <CopyIcon v-else class="size-3" />
            </Button>
            <span v-if="msg.created_at" class="text-[10px] font-sans font-medium text-muted-foreground/70">
              {{ formatTime(msg.created_at) }}
            </span>
          </div>
        </div>
      </template>

      <!-- 3. Thinking / Typing State via Marker -->
      <Marker v-if="isSending" role="status" class="px-3 py-1 items-center gap-2">
        <MarkerIcon>
          <SparklesIcon class="size-3.5 text-amber-500 animate-spin" />
        </MarkerIcon>
        <MarkerContent class="text-xs text-muted-foreground font-medium">
          در حال بررسی اطلاعات تاپیک و نگارش پاسخ...
        </MarkerContent>
      </Marker>
    </div>

    <!-- 5. Message Input Bar: Matching Topic page design, without file, voice, and plugins -->
    <div class="sticky bottom-0 inset-x-0 bg-background/65 dark:bg-background/55 backdrop-blur-md p-2.5 sm:p-3.5 pb-[max(0.75rem,env(safe-area-inset-bottom))] z-30 w-full shrink-0">
      <TopicMessageInput
        :placeholder="languageStore.t('پرسش خود را درباره این تاپیک بنویسید...\u200F', 'Ask a question about this topic...')"
        :disabled="isSending"
        :allow-attachments="false"
        :allow-voice="false"
        :allow-plugins="false"
        @send="handleTopicInputSend"
      />
    </div>
  </div>
</template>
