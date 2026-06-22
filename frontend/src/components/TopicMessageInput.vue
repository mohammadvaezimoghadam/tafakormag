<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import Input from '@/components/ui/input/Input.vue'
import { 
  PaperclipIcon, 
  SendIcon, 
  MicIcon, 
  XIcon, 
  Trash2Icon,
  CheckIcon,
  FileTextIcon, 
  ImageIcon, 
  VideoIcon, 
  MusicIcon,
  PlayIcon,
  Loader2Icon,
  AlertCircleIcon
} from '@lucide/vue'

interface Attachment {
  id: string | number
  name: string
  type: 'image' | 'video' | 'audio' | 'file'
  url?: string
  size?: string
  progress?: number // 0 to 100
  status?: 'uploading' | 'completed' | 'error'
}

const props = withDefaults(defineProps<{
  placeholder?: string
  disabled?: boolean
  initialText?: string
  initialAttachments?: Attachment[]
}>(), {
  placeholder: 'پیام خود را بنویسید...',
  disabled: false,
  initialText: '',
  initialAttachments: () => []
})

const emit = defineEmits<{
  (e: 'send', message: { text: string; attachments: Attachment[] }): void
  (e: 'attach'): void
  (e: 'recordVoice'): void
  (e: 'removeAttachment', id: string | number): void
}>()

// Local state
const text = ref(props.initialText)
const attachments = ref<Attachment[]>([...props.initialAttachments])
const isRecording = ref(false)
const recordingSeconds = ref(0)
let timerInterval: any = null

// Sync from props
watch(() => props.initialText, (newVal) => {
  text.value = newVal
})

watch(() => props.initialAttachments, (newVal) => {
  attachments.value = [...newVal]
}, { deep: true })

onUnmounted(() => {
  stopTimer()
})

// Timer actions for voice recording
const startTimer = () => {
  recordingSeconds.value = 0
  timerInterval = setInterval(() => {
    recordingSeconds.value++
  }, 1000)
}

const stopTimer = () => {
  if (timerInterval) {
    clearInterval(timerInterval)
    timerInterval = null
  }
}

const formattedTime = computed(() => {
  const mins = Math.floor(recordingSeconds.value / 60)
  const secs = recordingSeconds.value % 60
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
})

// Dynamic action states
const hasContent = computed(() => {
  return text.value.trim().length > 0 || attachments.value.length > 0
})

// Actions
const handleSend = () => {
  if (props.disabled) return
  if (!hasContent.value) return

  // Filter out attachments that are still uploading
  const completedAttachments = attachments.value.filter(a => a.status !== 'uploading')

  emit('send', {
    text: text.value.trim(),
    attachments: completedAttachments
  })

  // Clear inputs
  text.value = ''
  attachments.value = []
}

// Start Voice Recording
const startRecording = () => {
  if (props.disabled) return
  isRecording.value = true
  startTimer()
  emit('recordVoice')
}

// Cancel / Discard Voice Recording
const cancelRecording = () => {
  isRecording.value = false
  stopTimer()
  recordingSeconds.value = 0
}

// Stop and Send Voice Recording
const completeRecording = () => {
  if (props.disabled) return
  const durationStr = formattedTime.value
  isRecording.value = false
  stopTimer()

  // Generate a mock audio attachment to represent the voice recording
  const voiceAttachment: Attachment = {
    id: `voice_${Date.now()}`,
    name: `صدا_ضبط_شده_${durationStr.replace(':', '_')}.ogg`,
    type: 'audio',
    size: durationStr,
    status: 'completed',
    progress: 100
  }

  // Send the recording immediately
  emit('send', {
    text: '',
    attachments: [voiceAttachment]
  })
}

const handleAttachClick = () => {
  if (props.disabled) return
  emit('attach')
}

const handleRemoveAttachment = (id: string | number) => {
  attachments.value = attachments.value.filter(a => a.id !== id)
  emit('removeAttachment', id)
}
</script>

<template>
  <div 
    class="w-full flex flex-col relative transition-all duration-350"
    dir="rtl"
  >
    <!-- Muted/Disabled overlay message -->
    <div 
      v-if="props.disabled" 
      class="absolute inset-0 bg-background/60 backdrop-blur-3xs rounded-2xl z-20 flex items-center justify-center border border-border/40"
    >
      <div class="bg-card/95 border border-border/80 rounded-xl px-4 py-2 flex items-center gap-2 shadow-xs">
        <AlertCircleIcon class="size-4 text-muted-foreground animate-pulse" />
        <span class="text-[11px] font-bold text-muted-foreground">شما اجازه ارسال پیام در این تاپیک را ندارید.</span>
      </div>
    </div>

    <!-- Attachments Preview Bar (Above the main input box) -->
    <transition name="attachments-slide">
      <div 
        v-if="attachments.length > 0" 
        class="w-full bg-card/40 backdrop-blur-md border border-border/40 rounded-2xl p-3 flex gap-3 overflow-x-auto scrollbar-none z-10 text-right mb-2"
      >
        <div 
          v-for="file in attachments" 
          :key="file.id"
          class="size-16 rounded-xl border border-border/50 bg-background/40 relative overflow-hidden flex flex-col items-center justify-center shrink-0 group hover:border-primary/20 transition-all duration-200"
        >
          <!-- Delete button (Top Right) -->
          <button 
            @click="handleRemoveAttachment(file.id)"
            class="absolute top-1.5 right-1.5 z-15 size-5 p-0 rounded-full bg-black/40 hover:bg-black/60 flex items-center justify-center text-white cursor-pointer transition-colors shadow-xs outline-none"
            title="حذف پیوست"
          >
            <XIcon class="size-2.5" />
          </button>

          <!-- Uploading state overlay -->
          <div 
            v-if="file.status === 'uploading'" 
            class="absolute inset-0 bg-black/40 z-10 flex flex-col items-center justify-center text-white"
          >
            <Loader2Icon class="size-4 animate-spin text-primary-foreground" />
            <span class="text-[8px] font-mono font-bold mt-1">{{ file.progress || 0 }}%</span>
          </div>

          <!-- Thumbnail content based on file type -->
          <template v-if="file.type === 'image' && file.url">
            <img :src="file.url" class="w-full h-full object-cover" :alt="file.name" />
          </template>

          <template v-else-if="file.type === 'video'">
            <div class="size-full bg-slate-900 flex items-center justify-center relative">
              <VideoIcon class="size-5 text-white/70" />
              <PlayIcon class="size-2.5 text-white absolute bottom-1.5 left-1.5" />
            </div>
          </template>

          <template v-else-if="file.type === 'audio'">
            <div class="size-full flex flex-col items-center justify-center gap-1 p-1.5 bg-violet-500/10">
              <MusicIcon class="size-5 text-violet-500" />
              <span class="text-[8.5px] truncate max-w-full font-mono text-muted-foreground leading-none">{{ file.size || 'صدا' }}</span>
            </div>
          </template>

          <template v-else>
            <div class="size-full flex flex-col items-center justify-center gap-1 p-1.5 bg-sky-500/10">
              <FileTextIcon class="size-5 text-sky-500" />
              <span class="text-[8.5px] truncate max-w-full font-bold text-muted-foreground leading-none">{{ file.size || 'فایل' }}</span>
            </div>
          </template>
          
          <!-- Hover filename tooltip/indicator -->
          <div class="absolute bottom-0 inset-x-0 bg-black/60 py-0.5 px-1.5 truncate text-[7.5px] text-white/90 text-center opacity-0 group-hover:opacity-100 transition-opacity">
            {{ file.name }}
          </div>
        </div>
      </div>
    </transition>

    <!-- Main Message Input Row (RTL) -->
    <div class="w-full flex items-center gap-1" dir="rtl">
      
      <!-- Right Element: Attach File Button / Cancel Recording Button -->
      <transition name="button-pop" mode="out-in">
        <!-- Cancel Recording Button -->
        <button 
          v-if="isRecording"
          key="cancel-record"
          @click="cancelRecording"
          class="size-10 p-0 rounded-2xl flex items-center justify-center bg-destructive/10 text-destructive border border-destructive/25 hover:bg-destructive/20 transition-all duration-200 cursor-pointer shrink-0 outline-none active:scale-95"
          title="لغو ضبط"
        >
          <Trash2Icon class="size-5" />
        </button>

        <!-- Normal Attach Button -->
        <button 
          v-else
          key="attach-file"
          @click="handleAttachClick"
          :disabled="props.disabled"
          class="size-10 p-0 rounded-2xl flex items-center justify-center bg-muted/40 text-muted-foreground border border-border/20 hover:text-foreground hover:bg-muted/70 transition-all duration-200 cursor-pointer shrink-0 outline-none active:scale-95 disabled:pointer-events-none disabled:opacity-50"
          title="افزودن فایل پیوست"
        >
          <PaperclipIcon class="size-5" />
        </button>
      </transition>

      <!-- Center Element: Text Input / Recording Info Display -->
      <div class="flex-1 min-w-0">
        <transition name="fade" mode="out-in">
          <!-- Voice Recording Display -->
          <div 
            v-if="isRecording"
            key="recording-status"
            class="w-full bg-destructive/5 dark:bg-destructive/10 border border-destructive/20 text-destructive text-xs font-semibold h-10 px-4 rounded-2xl flex items-center justify-between transition-all duration-200 select-none"
          >
            <div class="flex items-center gap-2">
              <span class="size-2 bg-destructive rounded-full animate-pulse" />
              <span class="text-[11px] font-bold text-destructive/80">در حال ضبط صدا...</span>
            </div>
            <span class="font-mono text-xs font-bold text-destructive/90">{{ formattedTime }}</span>
          </div>

          <!-- Normal Shadcn Input -->
          <Input
            v-else
            key="text-input"
            v-model="text"
            :disabled="props.disabled"
            :placeholder="props.placeholder"
            class="bg-muted/40 border-none outline-none focus-visible:ring-0 focus-visible:ring-offset-0 focus:ring-0 focus:outline-none focus-visible:outline-none text-xs font-semibold h-10 px-4 rounded-2xl flex-1 text-foreground placeholder:text-muted-foreground/60 transition-all shadow-none"
            @keydown.enter.exact.prevent="handleSend"
          />
        </transition>
      </div>

      <!-- Left Element: Send Button / Record Voice Button -->
      <transition name="button-pop" mode="out-in">
        <!-- Stop/Send Recording Button -->
        <button 
          v-if="isRecording"
          key="stop-record"
          @click="completeRecording"
          class="size-10 p-0 rounded-2xl flex items-center justify-center bg-emerald-500 text-white shadow-md shadow-emerald-500/20 hover:bg-emerald-600 transition-all duration-200 cursor-pointer shrink-0 outline-none active:scale-95"
          title="ارسال صدا"
        >
          <CheckIcon class="size-5.5" />
        </button>

        <!-- Send message button -->
        <button 
          v-else-if="hasContent"
          key="send-msg"
          @click="handleSend"
          :disabled="props.disabled"
          class="size-10 p-0 rounded-2xl flex items-center justify-center bg-primary text-primary-foreground shadow-md shadow-primary/20 hover:bg-primary/95 transition-all duration-200 cursor-pointer shrink-0 outline-none active:scale-95 disabled:pointer-events-none disabled:opacity-50"
          title="ارسال پیام"
        >
          <SendIcon class="size-4.5 -rotate-45 relative translate-x-[2px] -translate-y-[1px]" />
        </button>

        <!-- Record Voice Button -->
        <button 
          v-else
          key="record-voice"
          @click="startRecording"
          :disabled="props.disabled"
          class="size-10 p-0 rounded-2xl flex items-center justify-center bg-muted/40 text-muted-foreground border border-border/20 hover:text-foreground hover:bg-muted/70 transition-all duration-200 cursor-pointer shrink-0 outline-none active:scale-95 disabled:pointer-events-none disabled:opacity-50"
          title="ضبط صدا"
        >
          <MicIcon class="size-5" />
        </button>
      </transition>

    </div>
  </div>
</template>

<style scoped>
/* Trans-slide for attachments strip */
.attachments-slide-enter-active,
.attachments-slide-leave-active {
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  max-height: 100px;
  opacity: 1;
}
.attachments-slide-enter-from,
.attachments-slide-leave-to {
  max-height: 0;
  opacity: 0;
  padding: 0 !important;
  margin-bottom: 0px;
  transform: translateY(8px);
}

/* Button Pop animation for swapping */
.button-pop-enter-active,
.button-pop-leave-active {
  transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.button-pop-enter-from {
  opacity: 0;
  transform: scale(0.7);
}
.button-pop-leave-to {
  opacity: 0;
  transform: scale(0.7);
}

/* Fade animation for input transition */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Scrollbar styling */
.scrollbar-none::-webkit-scrollbar {
  display: none;
}
.scrollbar-none {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
</style>
