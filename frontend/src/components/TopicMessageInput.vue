<script setup lang="ts">
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { Button } from '@/components/ui/button'
import { 
  PaperclipIcon, 
  SendIcon, 
  MicIcon, 
  SmileIcon, 
  XIcon, 
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
const textareaRef = ref<HTMLTextAreaElement | null>(null)
const isRecording = ref(false)

// Sync from props
watch(() => props.initialText, (newVal) => {
  text.value = newVal
  nextTick(adjustHeight)
})

watch(() => props.initialAttachments, (newVal) => {
  attachments.value = [...newVal]
}, { deep: true })

// Auto-resizing textarea logic
const adjustHeight = () => {
  const el = textareaRef.value
  if (!el) return
  el.style.height = 'auto'
  // Auto-clamp height between 40px and 160px
  const nextHeight = Math.min(el.scrollHeight, 160)
  el.style.height = `${Math.max(nextHeight, 40)}px`
}

onMounted(() => {
  adjustHeight()
})

// Dynamic action state
const hasContent = computed(() => {
  return text.value.trim().length > 0 || attachments.value.length > 0
})

const handleSend = () => {
  if (props.disabled) return
  if (!hasContent.value) {
    // If empty, click triggers record voice simulation
    handleRecordVoice()
    return
  }

  // Filter out attachments that are still uploading
  const completedAttachments = attachments.value.filter(a => a.status !== 'uploading')

  emit('send', {
    text: text.value.trim(),
    attachments: completedAttachments
  })

  // Clear inputs
  text.value = ''
  attachments.value = []
  nextTick(adjustHeight)
}

const handleRecordVoice = () => {
  if (props.disabled) return
  isRecording.value = !isRecording.value
  emit('recordVoice')
}

const handleRemoveAttachment = (id: string | number) => {
  attachments.value = attachments.value.filter(a => a.id !== id)
  emit('removeAttachment', id)
}

const handleAttachClick = () => {
  if (props.disabled) return
  emit('attach')
}
</script>

<template>
  <div 
    class="w-full flex flex-col gap-2 relative transition-all duration-300"
    dir="rtl"
  >
    <!-- Muted/Disabled overlay message -->
    <div 
      v-if="props.disabled" 
      class="absolute inset-0 bg-background/50 backdrop-blur-3xs rounded-xl z-20 flex items-center justify-center border border-border/40"
    >
      <div class="bg-card/90 border border-border/80 rounded-lg px-4 py-2.5 flex items-center gap-2 shadow-sm">
        <AlertCircleIcon class="size-4 text-muted-foreground" />
        <span class="text-[11px] font-bold text-muted-foreground">شما اجازه ارسال پیام در این تاپیک را ندارید.</span>
      </div>
    </div>

    <!-- Attachments Preview Bar (Above the main input box) -->
    <transition name="attachments-slide">
      <div 
        v-if="attachments.length > 0" 
        class="w-full bg-card/45 backdrop-blur-md border border-border/40 rounded-xl p-3 flex gap-3 overflow-x-auto scrollbar-none z-10 text-right"
      >
        <div 
          v-for="file in attachments" 
          :key="file.id"
          class="size-16 rounded-lg border border-border/60 bg-background/40 relative overflow-hidden flex flex-col items-center justify-center shrink-0 group hover:border-primary/20 transition-colors"
        >
          <!-- Delete button (Top Right) -->
          <button 
            @click="handleRemoveAttachment(file.id)"
            class="absolute top-1 right-1 z-15 size-4.5 rounded-full bg-black/45 hover:bg-black/65 flex items-center justify-center text-white cursor-pointer transition-colors shadow-sm outline-none"
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
              <PlayIcon class="size-2.5 text-white absolute bottom-1 left-1" />
            </div>
          </template>

          <template v-else-if="file.type === 'audio'">
            <div class="size-full flex flex-col items-center justify-center gap-1 p-1 bg-violet-500/10">
              <MusicIcon class="size-5 text-violet-500" />
              <span class="text-[7.5px] truncate max-w-full font-mono text-muted-foreground leading-none">{{ file.size || 'صدا' }}</span>
            </div>
          </template>

          <template v-else>
            <div class="size-full flex flex-col items-center justify-center gap-1 p-1 bg-sky-500/10">
              <FileTextIcon class="size-5 text-sky-500" />
              <span class="text-[7.5px] truncate max-w-full font-bold text-muted-foreground leading-none">{{ file.size || 'فایل' }}</span>
            </div>
          </template>
          
          <!-- Hover filename tooltip/indicator -->
          <div class="absolute bottom-0 inset-x-0 bg-black/60 py-0.5 px-1 truncate text-[7.5px] text-white/90 text-center opacity-0 group-hover:opacity-100 transition-opacity">
            {{ file.name }}
          </div>
        </div>
      </div>
    </transition>

    <!-- Main Message Input Container -->
    <div class="w-full bg-card/45 backdrop-blur-md border border-border/40 rounded-xl p-2 pr-3 flex items-end gap-2 shadow-xs min-h-[48px]">
      
      <!-- Attachment Button (Right) -->
      <button 
        @click="handleAttachClick"
        :disabled="props.disabled"
        class="size-9 rounded-lg flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-muted/80 transition-colors cursor-pointer shrink-0 outline-none active:scale-95"
        title="افزودن فایل پیوست"
      >
        <PaperclipIcon class="size-5.5" />
      </button>

      <!-- Auto-resizing Text Input Area -->
      <textarea
        ref="textareaRef"
        v-model="text"
        :disabled="props.disabled"
        :placeholder="props.placeholder"
        rows="1"
        class="flex-1 bg-transparent border-none outline-none resize-none text-xs font-semibold leading-relaxed py-2 h-[40px] max-h-[160px] text-foreground focus:outline-none focus:ring-0 focus:border-none focus-visible:ring-0 focus-visible:outline-none placeholder:text-muted-foreground/60 scrollbar-thin shadow-none"
        @input="adjustHeight"
        @keydown.enter.exact.prevent="handleSend"
      />

      <!-- Emoji Picker Button (Left Middle) -->
      <button 
        :disabled="props.disabled"
        class="size-9 rounded-lg flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-muted/80 transition-colors cursor-pointer shrink-0 outline-none active:scale-95"
        title="اموجی"
      >
        <SmileIcon class="size-5.5" />
      </button>

      <!-- Send/Record Button (Left) -->
      <button 
        @click="handleSend"
        :disabled="props.disabled"
        :class="[
          'size-9 rounded-lg flex items-center justify-center transition-all shrink-0 outline-none cursor-pointer',
          hasContent 
            ? 'bg-primary text-primary-foreground shadow-xs scale-100 active:scale-95' 
            : 'bg-transparent text-muted-foreground hover:text-foreground hover:bg-muted/80 active:scale-95'
        ]"
        :title="hasContent ? 'ارسال پیام' : 'ضبط صدا'"
      >
        <transition name="icon-swap" mode="out-in">
          <SendIcon v-if="hasContent" class="size-5.5" />
          <MicIcon v-else :class="['size-5.5', isRecording ? 'text-destructive animate-pulse' : '']" />
        </transition>
      </button>

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
  margin-bottom: -8px;
  transform: translateY(8px);
}

/* Icon Swap transition */
.icon-swap-enter-active,
.icon-swap-leave-active {
  transition: all 0.15s ease;
}
.icon-swap-enter-from {
  opacity: 0;
  transform: scale(0.8) rotate(-15deg);
}
.icon-swap-leave-to {
  opacity: 0;
  transform: scale(0.8) rotate(15deg);
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
