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
  Message,
  MessageAvatar,
  MessageContent,
  MessageHeader,
  MessageFooter
} from '@/components/ui/message'
import {
  Bubble,
  BubbleContent
} from '@/components/ui/bubble'
import {
  Marker,
  MarkerContent,
  MarkerIcon
} from '@/components/ui/marker'
import {
  Avatar,
  AvatarImage,
  AvatarFallback
} from '@/components/ui/avatar'
import {
  SparklesIcon,
  SendIcon,
  ArrowRightIcon,
  Trash2Icon,
  CopyIcon,
  CheckIcon,
  BookOpenIcon,
  FileTextIcon,
  BotIcon,
  UserIcon
} from '@lucide/vue'

interface Props {
  topic: { id: number | string; title?: string; name?: string; description?: string }
  isOwner?: boolean
  isAdmin?: boolean
  simulated?: boolean
  initialFaqs?: Array<{ id: number | string; question: string; answer?: string }>
}

const props = withDefaults(defineProps<Props>(), {
  isOwner: false,
  isAdmin: false,
  simulated: false,
  initialFaqs: () => []
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
    return d.toLocaleTimeString('fa-IR', { hour: '2-digit', minute: '2-digit' })
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

// Load History
const loadHistory = async () => {
  if (props.simulated) {
    if (messages.value.length === 0) {
      messages.value = [
        {
          id: 'welcome-1',
          role: 'assistant',
          content: `سلام! من دستیار هوشمند تاپیک **${topicName.value}** هستم.\n\nمن به تمام محتوای تاپیک، یادداشت‌ها و اسناد دسترسی دارم. هر سوالی درباره این تاپیک، اهداف، برنامه‌ها یا موضوعات مطرح‌شده دارید بپرسید تا با استناد به پایگاه دانش تاپیک پاسخ دهم.`,
          sources: [
            { type: 'post', id: 1, title: 'مرام‌نامه و اهداف تاپیک', preview: 'اهداف کلی و ضوابط حضور در جلسات تاپیک' }
          ],
          created_at: new Date().toISOString()
        }
      ]
    }
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
        // Welcome message
        messages.value = [
          {
            id: 'welcome-default',
            role: 'assistant',
            content: `سلام! من دستیار هوشمند تاپیک **${topicName.value}** هستم.\n\nهر سوالی درباره اهداف، نوشته‌ها، جلسات یا ضوابط این تاپیک دارید مطرح فرمایید.`,
            sources: [],
            created_at: new Date().toISOString()
          }
        ]
      }
    }
  } catch (err) {
    // Fallback welcome message
    messages.value = [
      {
        id: 'welcome-fallback',
        role: 'assistant',
        content: `سلام! من دستیار هوشمند تاپیک **${topicName.value}** هستم. می‌توانید سوال خود را درباره این تاپیک مطرح کنید.`,
        sources: [],
        created_at: new Date().toISOString()
      }
    ]
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
    messages.value = [
      {
        id: 'welcome-reset',
        role: 'assistant',
        content: `تاریخچه پاک شد. هر سوالی درباره تاپیک **${topicName.value}** دارید می‌توانید بپرسید.`,
        created_at: new Date().toISOString()
      }
    ]
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
    class="w-full h-full flex flex-col gap-3 text-start font-sans select-none relative" 
    :dir="languageStore.dir"
  >
    <!-- Internal Header: Identical to other subviews and internal pages -->
    <PlatformHeader 
      is-inner-page
      :inner-title="languageStore.t('دستیار هوشمند تاپیک', 'Topic AI Assistant')"
      :show-options-button="false"
      :show-faq-button="false"
      @back="emit('back')"
    />

    <!-- Chat Messages Scroll Area: Rendered via shadcn-vue Message & Bubble -->
    <div 
      ref="messagesContainerRef"
      class="flex-1 overflow-y-auto px-4 py-2 space-y-4 text-start scroll-smooth"
    >
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
        <!-- 1. USER MESSAGE -->
        <Message v-if="msg.role === 'user'" align="end" class="items-end">
          <MessageAvatar>
            <Avatar class="size-7 ring-1 ring-primary/20">
              <AvatarImage v-if="userProfile?.avatar" :src="userProfile.avatar" :alt="userProfile.name" />
              <AvatarFallback class="text-[10px] font-bold bg-primary text-primary-foreground">
                {{ userInitial }}
              </AvatarFallback>
            </Avatar>
          </MessageAvatar>
          <MessageContent class="items-end">
            <Bubble variant="default">
              <BubbleContent class="rounded-2xl rounded-bl-none text-xs font-medium leading-relaxed shadow-xs text-right" dir="rtl">
                {{ msg.content }}
              </BubbleContent>
            </Bubble>
            <MessageFooter v-if="msg.created_at" class="pe-1 text-[9.5px] text-muted-foreground/60 font-mono">
              {{ formatTime(msg.created_at) }}
            </MessageFooter>
          </MessageContent>
        </Message>

        <!-- 2. ASSISTANT MESSAGE -->
        <Message v-else align="start" class="items-start">
          <MessageAvatar>
            <div class="size-7 rounded-full bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-600 dark:text-amber-400 shrink-0">
              <SparklesIcon class="size-3.5" />
            </div>
          </MessageAvatar>
          <MessageContent class="items-start max-w-[92%] sm:max-w-[85%]">
            <MessageHeader class="ps-1 gap-1.5 text-[10px]">
              <span class="font-black text-foreground/90">دستیار هوشمند تاپیک</span>
              <Badge variant="outline" class="text-[8.5px] px-1 py-0 h-4 border-amber-500/30 text-amber-600 dark:text-amber-400 bg-amber-500/5 font-mono">
                AI • RAG
              </Badge>
            </MessageHeader>

            <Bubble variant="outline" class="w-full max-w-full">
              <BubbleContent class="rounded-2xl rounded-br-none text-right bg-card border-border/60 text-foreground text-xs leading-relaxed p-3.5 space-y-2.5 shadow-xs w-full" dir="rtl">
                <!-- Markdown Rendered Content -->
                <FormattedText :content="msg.content" class-name="text-right" />

                <!-- RAG Sources / Citations Pill List -->
                <div v-if="msg.sources && msg.sources.length > 0" class="pt-2 border-t border-border/40 space-y-1.5">
                  <span class="text-[9.5px] font-bold text-muted-foreground flex items-center gap-1">
                    <BookOpenIcon class="size-3 text-primary" />
                    <span>منابع استناد شده از تاپیک:</span>
                  </span>
                  <div class="flex flex-wrap gap-1.5">
                    <div
                      v-for="(source, sIdx) in msg.sources"
                      :key="sIdx"
                      class="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-muted/40 border border-border/40 text-[9px] text-foreground/80"
                      :title="source.preview || source.title"
                    >
                      <FileTextIcon class="size-2.5 text-blue-500 shrink-0" />
                      <span class="font-semibold">{{ source.title }}</span>
                    </div>
                  </div>
                </div>
              </BubbleContent>
            </Bubble>

            <!-- Message Footer: Actions and Timestamp -->
            <MessageFooter class="ps-1 gap-2 pt-0.5">
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
              <span v-if="msg.created_at" class="text-[9.5px] font-mono text-muted-foreground/60">
                {{ formatTime(msg.created_at) }}
              </span>
            </MessageFooter>
          </MessageContent>
        </Message>
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
    <div class="sticky bottom-0 inset-x-0 bg-background/65 dark:bg-background/55 backdrop-blur-md border-t border-border/40 p-2.5 sm:p-3.5 z-30 w-full shrink-0">
      <TopicMessageInput
        :placeholder="languageStore.t('پرسش خود را درباره این تاپیک بنویسید...', 'Ask a question about this topic...')"
        :disabled="isSending"
        :allow-attachments="false"
        :allow-voice="false"
        :allow-plugins="false"
        @send="handleTopicInputSend"
      />
    </div>
  </div>
</template>
