<script setup lang="ts">
import { ref, reactive, watch, onBeforeUnmount, computed, nextTick } from 'vue'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { 
  HeartIcon, 
  MessageCircleIcon, 
  Share2Icon, 
  PlayIcon, 
  PauseIcon, 
  Volume2Icon, 
  VolumeXIcon,
  MoreVerticalIcon, 
  SendIcon, 
  ClockIcon, 
  VideoIcon,
  MusicIcon,
  ImageIcon,
  UserIcon,
  CopyIcon,
  ClipboardIcon
} from '@lucide/vue'

// Interfaces
export interface Comment {
  id: string | number
  authorName: string
  authorAvatar?: string
  text: string
  timestamp: string
}

export interface PostAuthor {
  name: string
  avatarUrl?: string
  role?: string
  phone?: string
}

export interface PostReaction {
  emoji: string
  count: number
  reacted: boolean
}

interface Props {
  id: string | number
  author: PostAuthor
  type: 'text' | 'image' | 'video' | 'audio'
  content?: string
  mediaUrl?: string
  posterUrl?: string // For video/audio poster
  duration?: string
  timestamp: string
  likesCount?: number
  comments?: Comment[]
  liked?: boolean
  reactions?: PostReaction[]
}

const props = withDefaults(defineProps<Props>(), {
  likesCount: 0,
  comments: () => [],
  liked: false,
  reactions: () => []
})

const emit = defineEmits<{
  (e: 'like', id: string | number, newState: boolean): void
  (e: 'share', id: string | number): void
  (e: 'add-comment', postId: string | number, comment: Comment): void
  (e: 'edit', id: string | number): void
  (e: 'delete', id: string | number): void
  (e: 'pin', id: string | number): void
  (e: 'react', id: string | number, emoji: string, currentReactions: PostReaction[]): void
  (e: 'copy', id: string | number): void
}>()

// Helper for Farsi digits
const toPersianDigits = (num: number | string) => {
  const id = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹']
  return num.toString().replace(/[0-9]/g, (w) => id[+w]!)
}

// Local interactive state
const isLiked = ref(props.liked)
const localLikesCount = ref(props.likesCount)
const showComments = ref(false)
const localComments = ref<Comment[]>([...props.comments])
const newCommentText = ref('')
const localReactions = ref<PostReaction[]>([...props.reactions])
const touchX = ref(0)
const touchY = ref(0)
const isPressing = ref(false)

// Synchronize props changes
watch(() => props.liked, (newVal) => { isLiked.value = newVal })
watch(() => props.likesCount, (newVal) => { localLikesCount.value = newVal })
watch(() => props.comments, (newVal) => { localComments.value = [...newVal] }, { deep: true })
watch(() => props.reactions, (newVal) => { localReactions.value = [...newVal] }, { deep: true })

// PostContextMenu State and Logic
import PostContextMenu from './PostContextMenu.vue'
import { usePostStore } from '@/stores/postStore'
import { useUserStore } from '@/stores/userStore'

const postStore = usePostStore()
const userStore = useUserStore()

const isPostOwner = computed(() => {
  if (!userStore.isAuthenticated || !userStore.userProfile) return false
  return props.author.phone === userStore.userProfile.phone
})

const cardRef = ref<HTMLElement | null>(null)
const triggerRect = ref<DOMRect | null>(null)
const isContextMenuOpen = ref(false)

const isEditing = ref(false)
const editedContent = ref(props.content || '')
const textareaRef = ref<HTMLTextAreaElement | null>(null)

const adjustTextareaHeight = () => {
  if (textareaRef.value) {
    textareaRef.value.style.height = 'auto'
    textareaRef.value.style.height = `${textareaRef.value.scrollHeight}px`
    console.log('[PostCard] Height adjusted. scrollHeight:', textareaRef.value.scrollHeight, 'new height:', textareaRef.value.style.height)
  } else {
    console.log('[PostCard] adjustTextareaHeight called but textareaRef is null!')
  }
}

// Automatically adjust height when editing starts and textarea is rendered
watch(isEditing, (newVal) => {
  console.log('[PostCard] isEditing watcher:', newVal)
  if (newVal) {
    nextTick(() => {
      adjustTextareaHeight()
      setTimeout(adjustTextareaHeight, 30)
      setTimeout(adjustTextareaHeight, 100)
      setTimeout(adjustTextareaHeight, 250)
    })
  }
})

// Automatically adjust height whenever content changes (typing, pasting, initialization)
watch(editedContent, () => {
  console.log('[PostCard] editedContent watcher fired. New content length:', editedContent.value.length)
  if (isEditing.value) {
    nextTick(() => {
      adjustTextareaHeight()
    })
  }
})

// Custom dropdown menu for copy/paste inside editing textarea
const isEditTextareaContextMenuOpen = ref(false)
const editTextareaDropdownTriggerRef = ref<HTMLElement | null>(null)

const editTextareaMenuStyle = computed(() => {
  const menuWidth = 224
  const menuHeight = 80 // 2 menu items
  const viewportWidth = window.innerWidth
  const viewportHeight = window.innerHeight

  if (editTextareaDropdownTriggerRef.value) {
    const rect = editTextareaDropdownTriggerRef.value.getBoundingClientRect()
    const spaceBelow = viewportHeight - rect.bottom
    const spaceAbove = rect.top

    let top = 0
    if (spaceBelow > menuHeight + 20) {
      top = rect.bottom + 8
    } else if (spaceAbove > menuHeight + 20) {
      top = rect.top - menuHeight - 8
    } else {
      top = Math.max(16, rect.top + (rect.height - menuHeight) / 2)
    }

    let left = rect.left + (rect.width - menuWidth) / 2
    left = Math.max(16, Math.min(viewportWidth - menuWidth - 16, left))

    console.log('[PostCard] Dropdown positioned by button:', { top, left })
    return {
      top: `${top}px`,
      left: `${left}px`,
      position: 'fixed' as const
    }
  }

  const x = touchX.value
  const y = touchY.value

  let left = x - menuWidth / 2
  let top = y + 8

  if (y + menuHeight + 24 > viewportHeight) {
    top = y - menuHeight - 8
  }

  left = Math.max(16, Math.min(viewportWidth - menuWidth - 16, left))
  top = Math.max(16, Math.min(viewportHeight - menuHeight - 16, top))

  console.log('[PostCard] Dropdown positioned by touch/mouse coordinates:', { top, left, x, y })
  return {
    top: `${top}px`,
    left: `${left}px`,
    position: 'fixed' as const
  }
})

const handleEditTextareaContextMenu = (e: MouseEvent) => {
  console.log('[PostCard] handleEditTextareaContextMenu fired at:', e.clientX, e.clientY)
  e.preventDefault()
  touchX.value = e.clientX
  touchY.value = e.clientY
  editTextareaDropdownTriggerRef.value = null
  isEditTextareaContextMenuOpen.value = true
}

const handleEditTextareaDropdownToggle = (e: MouseEvent) => {
  e.stopPropagation()
  const target = e.currentTarget as HTMLElement
  console.log('[PostCard] handleEditTextareaDropdownToggle fired. Target:', target)
  editTextareaDropdownTriggerRef.value = target
  touchX.value = e.clientX
  touchY.value = e.clientY
  isEditTextareaContextMenuOpen.value = !isEditTextareaContextMenuOpen.value
  console.log('[PostCard] isEditTextareaContextMenuOpen state:', isEditTextareaContextMenuOpen.value)
}

const handleEditTextareaCopy = async () => {
  console.log('[PostCard] Copy requested. Content:', editedContent.value)
  if (editedContent.value) {
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(editedContent.value)
        console.log('[PostCard] Copied using clipboard API.')
      } else {
        // Fallback
        const textArea = document.createElement("textarea")
        textArea.value = editedContent.value
        textArea.style.position = "fixed"
        textArea.style.top = "0"
        textArea.style.left = "0"
        textArea.style.width = "2em"
        textArea.style.height = "2em"
        textArea.style.padding = "0"
        textArea.style.border = "none"
        textArea.style.outline = "none"
        textArea.style.boxShadow = "none"
        textArea.style.background = "transparent"
        document.body.appendChild(textArea)
        textArea.focus()
        textArea.select()
        document.execCommand('copy')
        document.body.removeChild(textArea)
        console.log('[PostCard] Copied using fallback execCommand.')
      }
    } catch (err) {
      console.error('Copy failed:', err)
    }
  }
  isEditTextareaContextMenuOpen.value = false
}

const handleEditTextareaPaste = async () => {
  console.log('[PostCard] Paste requested.')
  try {
    if (navigator.clipboard) {
      const text = await navigator.clipboard.readText()
      console.log('[PostCard] Paste content read from clipboard:', text)
      if (text) {
        if (textareaRef.value) {
          const start = textareaRef.value.selectionStart
          const end = textareaRef.value.selectionEnd
          const val = editedContent.value
          editedContent.value = val.substring(0, start) + text + val.substring(end)
          
          nextTick(() => {
            if (textareaRef.value) {
              textareaRef.value.focus()
              textareaRef.value.selectionStart = textareaRef.value.selectionEnd = start + text.length
              adjustTextareaHeight()
            }
          })
        } else {
          editedContent.value += text
        }
      }
    } else {
      console.warn('[PostCard] navigator.clipboard is undefined!')
    }
  } catch (err) {
    console.error('Paste failed:', err)
  }
  isEditTextareaContextMenuOpen.value = false
}

const handleEditStart = () => {
  console.log('[PostCard] handleEditStart. Content:', props.content)
  editedContent.value = props.content || ''
  isEditing.value = true
}

const handleEditCancel = () => {
  isEditing.value = false
}

const handleEditSave = async () => {
  if (editedContent.value.trim() === props.content) {
    isEditing.value = false
    return
  }
  
  const formData = new FormData()
  formData.append('content', editedContent.value)
  
  try {
    await postStore.updatePost(props.id, formData)
    isEditing.value = false
  } catch (err) {
    // Error will be caught and shown by global interceptor toast
  }
}

const isInteractiveElement = (target: HTMLElement) => {
  let el: HTMLElement | null = target
  while (el && el !== cardRef.value) {
    const tagName = el.tagName.toLowerCase()
    if (
      tagName === 'button' || 
      tagName === 'input' || 
      tagName === 'textarea' || 
      tagName === 'audio' || 
      tagName === 'video' ||
      tagName === 'a' ||
      el.getAttribute('role') === 'button' ||
      el.classList.contains('cursor-pointer') ||
      el.classList.contains('clickable') ||
      tagName === 'select' ||
      tagName === 'option'
    ) {
      return true
    }
    el = el.parentElement
  }
  return false
}

let longPressTimer: any = null
let isLongPressTriggered = false
let startX = 0
let startY = 0

const startLongPress = (clientX: number, clientY: number) => {
  isLongPressTriggered = false
  startX = clientX
  startY = clientY
  touchX.value = clientX
  touchY.value = clientY
  isPressing.value = true
  
  if (longPressTimer) clearTimeout(longPressTimer)
  
  longPressTimer = setTimeout(() => {
    isLongPressTriggered = true
    isPressing.value = false
    openContextMenu()
  }, 450)
}

const cancelLongPress = () => {
  isPressing.value = false
  if (longPressTimer) {
    clearTimeout(longPressTimer)
    longPressTimer = null
  }
}

const handleMouseDown = (e: MouseEvent) => {
  if (isEditing.value) return // Disable touch/press handling during edit mode
  if (e.button !== 0) return // Only left click
  if (isInteractiveElement(e.target as HTMLElement)) return
  startLongPress(e.clientX, e.clientY)
}

const handleMouseUp = () => {
  cancelLongPress()
}

const handleMouseLeave = () => {
  cancelLongPress()
}

const handleTouchStart = (e: TouchEvent) => {
  if (isEditing.value) return // Disable touch/press handling during edit mode
  if (isInteractiveElement(e.target as HTMLElement)) return
  const touch = e.touches[0]
  if (touch) {
    startLongPress(touch.clientX, touch.clientY)
  }
}

const handleTouchEnd = (e: TouchEvent) => {
  cancelLongPress()
  if (isLongPressTriggered) {
    e.preventDefault()
  }
}

const handleTouchMove = (e: TouchEvent) => {
  const touch = e.touches[0]
  if (touch) {
    const diffX = Math.abs(touch.clientX - startX)
    const diffY = Math.abs(touch.clientY - startY)
    if (diffX > 10 || diffY > 10) {
      cancelLongPress()
    }
  }
}

const handleContextMenu = (e: MouseEvent) => {
  if (isEditing.value) return
  if (isInteractiveElement(e.target as HTMLElement)) return
  e.preventDefault()
  touchX.value = e.clientX
  touchY.value = e.clientY
  openContextMenu()
}

const openContextMenu = () => {
  if (!cardRef.value) return
  triggerRect.value = cardRef.value.getBoundingClientRect()
  isContextMenuOpen.value = true
  isPressing.value = false
  
  if (navigator.vibrate) {
    navigator.vibrate(50)
  }
}

const handleThreeDotsClick = (e: MouseEvent) => {
  e.stopPropagation()
  touchX.value = e.clientX
  touchY.value = e.clientY
  openContextMenu()
}

const handleReact = (postId: string | number, emoji: string) => {
  const existing = localReactions.value.find(r => r.emoji === emoji)
  if (existing) {
    if (existing.reacted) {
      existing.count--
      existing.reacted = false
      if (existing.count <= 0) {
        localReactions.value = localReactions.value.filter(r => r.emoji !== emoji)
      }
    } else {
      existing.count++
      existing.reacted = true
    }
  } else {
    localReactions.value.push({
      emoji,
      count: 1,
      reacted: true
    })
  }
  emit('react', props.id, emoji, localReactions.value)
}

const handleReactionClick = (emoji: string) => {
  if (!userStore.isAuthenticated) {
    userStore.isLoginModalOpen = true
    return
  }
  handleReact(props.id, emoji)
}

const toggleLike = () => {
  if (!userStore.isAuthenticated) {
    userStore.isLoginModalOpen = true
    return
  }
  isLiked.value = !isLiked.value
  if (isLiked.value) {
    localLikesCount.value++
  } else {
    localLikesCount.value--
  }
  emit('like', props.id, isLiked.value)
}

const handleShare = () => {
  emit('share', props.id)
}

watch(showComments, (newVal) => {
  if (newVal) {
    postStore.fetchComments(props.id)
  }
})

const submitComment = async () => {
  if (!userStore.isAuthenticated) {
    userStore.isLoginModalOpen = true
    return
  }
  if (!newCommentText.value.trim()) return
  try {
    await postStore.addComment(props.id, newCommentText.value.trim())
    newCommentText.value = ''
  } catch (err) {
    console.error('Error submitting comment:', err)
  }
}

// Custom Audio Player State
const audioRef = ref<HTMLAudioElement | null>(null)
const isAudioPlaying = ref(false)
const audioCurrentTime = ref(0)
const audioDuration = ref(0)
const isMuted = ref(false)

const toggleAudioPlay = () => {
  if (!audioRef.value) return
  if (isAudioPlaying.value) {
    audioRef.value.pause()
  } else {
    // Pause any other playing audios/videos if possible
    audioRef.value.play()
  }
  isAudioPlaying.value = !isAudioPlaying.value
}

const toggleMute = () => {
  if (!audioRef.value) return
  audioRef.value.muted = !audioRef.value.muted
  isMuted.value = audioRef.value.muted
}

const onAudioTimeUpdate = () => {
  if (!audioRef.value) return
  audioCurrentTime.value = audioRef.value.currentTime
}

const onAudioLoadedMetadata = () => {
  if (!audioRef.value) return
  audioDuration.value = audioRef.value.duration
}

const onAudioEnded = () => {
  isAudioPlaying.value = false
  audioCurrentTime.value = 0
}

const onAudioSeek = (event: Event) => {
  if (!audioRef.value) return
  const target = event.target as HTMLInputElement
  const time = parseFloat(target.value)
  audioRef.value.currentTime = time
  audioCurrentTime.value = time
}

// Custom Video Player State
const videoRef = ref<HTMLVideoElement | null>(null)
const isVideoPlaying = ref(false)

const toggleVideoPlay = () => {
  if (!videoRef.value) return
  if (isVideoPlaying.value) {
    videoRef.value.pause()
    isVideoPlaying.value = false
  } else {
    videoRef.value.play()
    isVideoPlaying.value = true
  }
}

const onVideoPlayStateChange = () => {
  if (!videoRef.value) return
  isVideoPlaying.value = !videoRef.value.paused
}

// Clean up players on unmount
onBeforeUnmount(() => {
  if (audioRef.value) {
    audioRef.value.pause()
  }
  if (videoRef.value) {
    videoRef.value.pause()
  }
})

// Time formatter (mm:ss)
const formatTime = (timeInSeconds: number) => {
  if (isNaN(timeInSeconds)) return '۰۰:۰۰'
  const minutes = Math.floor(timeInSeconds / 60)
  const seconds = Math.floor(timeInSeconds % 60)
  const pad = (num: number) => num < 10 ? '0' + num : num
  return toPersianDigits(`${pad(minutes)}:${pad(seconds)}`)
}
</script>

<template>
  <div 
    ref="cardRef"
    :class="[
      'w-full bg-background/12 dark:bg-card/10 backdrop-blur-md border border-border/60 rounded-3xl shadow-none transition-all duration-300 flex flex-col overflow-hidden text-right select-none',
      isPressing ? 'scale-[0.96] shadow-inner bg-background/5 dark:bg-card/5 border-border/30 brightness-95' : 'scale-100'
    ]"
    dir="rtl"
    @mousedown="handleMouseDown"
    @mouseup="handleMouseUp"
    @mouseleave="handleMouseLeave"
    @touchstart="handleTouchStart"
    @touchend="handleTouchEnd"
    @touchmove="handleTouchMove"
    @contextmenu="handleContextMenu"
  >
    <!-- Card Top Header -->
    <div class="px-5 py-4 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <!-- Avatar -->
        <Avatar class="size-10 shadow-xs">
          <AvatarImage :src="author.avatarUrl || ''" :alt="author.name" />
          <AvatarFallback class="bg-primary/10 text-primary font-bold text-xs">
            {{ author.name.charAt(0) }}
          </AvatarFallback>
        </Avatar>
        
        <!-- Author Info -->
        <div class="flex flex-col text-right">
          <span class="text-xs font-bold text-foreground">{{ author.name }}</span>
          <span class="text-[10px] text-muted-foreground mt-0.5">{{ author.role || 'عضو تاپیک' }}</span>
        </div>
      </div>

      <div class="flex items-center gap-2">
        <!-- Timestamp -->
        <div class="flex items-center gap-1.5 text-xs font-bold text-muted-foreground">
          <ClockIcon class="size-3.5 text-primary" />
          <span>{{ toPersianDigits(timestamp) }}</span>
        </div>
        <!-- Options Menu (Simulated) -->
        <Button 
          variant="ghost" 
          size="icon" 
          class="size-7 rounded-full text-muted-foreground hover:text-foreground cursor-pointer"
          @click="handleThreeDotsClick"
        >
          <MoreVerticalIcon class="size-4" />
        </Button>
      </div>
    </div>

    <!-- Card Body Content -->
    <div class="p-5 flex flex-col gap-4">
      <!-- Post Text Content / Edit Box -->
      <div v-if="isEditing" class="flex flex-col gap-2 w-full text-right" dir="rtl">
        <textarea
          ref="textareaRef"
          v-model="editedContent"
          class="w-full min-h-[90px] p-3 text-xs font-semibold rounded-2xl bg-white dark:bg-black/40 border border-border/80 dark:border-border/40 focus:outline-none focus:ring-1 focus:ring-primary/20 text-foreground resize-none overflow-y-hidden select-text"
          style="-webkit-user-select: text !important; user-select: text !important;"
          placeholder="یادداشت خود را ویرایش کنید..."
          @input="adjustTextareaHeight"
          @contextmenu.prevent="handleEditTextareaContextMenu"
        />
        <div class="flex items-center justify-between w-full">
          <div>
            <Button 
              variant="ghost" 
              size="sm" 
              class="h-8 px-2 rounded-xl text-[10px] font-bold cursor-pointer text-muted-foreground hover:text-foreground flex items-center gap-1"
              @click="handleEditTextareaDropdownToggle"
            >
              <MoreVerticalIcon class="size-3.5" />
              <span>عملیات متن</span>
            </Button>
          </div>
          <div class="flex items-center gap-2">
            <Button 
              variant="outline" 
              size="sm" 
              class="h-8 px-3 rounded-xl text-[10px] font-bold cursor-pointer"
              @click="handleEditCancel"
            >
              انصراف
            </Button>
            <Button 
              size="sm" 
              class="h-8 px-3 rounded-xl text-[10px] font-bold cursor-pointer"
              @click="handleEditSave"
            >
              ذخیره تغییرات
            </Button>
          </div>
        </div>
      </div>
      
      <p 
        v-else-if="content" 
        class="text-sm font-medium leading-relaxed text-foreground/90 whitespace-pre-line"
      >
        {{ content }}
      </p>

      <!-- MEDIA RENDERERS -->
      <!-- 1. IMAGE POST -->
      <div 
        v-if="type === 'image' && mediaUrl" 
        class="relative w-full rounded-2xl overflow-hidden shadow-xs group"
      >
        <img 
          :src="mediaUrl" 
          alt="Post Image" 
          class="w-full h-auto max-h-[350px] object-cover transition-transform duration-500 group-hover:scale-[1.02]"
        />
        <div class="absolute inset-0 bg-linear-to-t from-black/40 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-end p-3">
          <span class="text-[9px] bg-black/60 backdrop-blur-xs text-white px-2.5 py-1 rounded-md flex items-center gap-1 font-bold">
            <ImageIcon class="size-3" />
            نمایش تصویر کامل
          </span>
        </div>
      </div>

      <!-- 2. VIDEO POST -->
      <div 
        v-else-if="type === 'video' && mediaUrl" 
        class="relative w-full rounded-2xl overflow-hidden shadow-xs bg-black/40 group"
      >
        <video 
          ref="videoRef"
          :src="mediaUrl"
          :poster="posterUrl"
          class="w-full h-auto max-h-[350px] object-cover"
          @play="onVideoPlayStateChange"
          @pause="onVideoPlayStateChange"
          controls
        />
        <!-- Custom overlay play button for high-end aesthetic -->
        <div 
          v-if="!isVideoPlaying"
          @click="toggleVideoPlay"
          class="absolute inset-0 flex items-center justify-center bg-black/15 group-hover:bg-black/25 transition-colors duration-300 cursor-pointer"
        >
          <div class="size-14 rounded-full bg-white/15 dark:bg-black/20 backdrop-blur-md border border-white/20 flex items-center justify-center text-white shadow-lg transform group-hover:scale-110 transition-transform duration-300">
            <PlayIcon class="size-6 fill-white ml-0.5" />
          </div>
        </div>
      </div>

      <!-- 3. AUDIO POST (Highly customized glassmorphic audio player) -->
      <div 
        v-else-if="type === 'audio' && mediaUrl" 
        class="w-full bg-white/5 dark:bg-black/10 rounded-2xl p-4 flex flex-col gap-3"
      >
        <audio 
          ref="audioRef"
          :src="mediaUrl"
          @timeupdate="onAudioTimeUpdate"
          @loadedmetadata="onAudioLoadedMetadata"
          @ended="onAudioEnded"
        />

        <div class="flex items-center gap-4">
          <!-- Play/Pause Glassmorphic Button -->
          <button 
            @click="toggleAudioPlay"
            class="size-11 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center text-primary hover:bg-primary/20 hover:scale-105 active:scale-95 transition-all cursor-pointer shadow-xs shrink-0"
          >
            <PlayIcon v-if="!isAudioPlaying" class="size-5 fill-primary ml-0.5" />
            <PauseIcon v-else class="size-5 fill-primary" />
          </button>

          <!-- Waveform / Info -->
          <div class="flex-1 flex flex-col gap-1.5 min-w-0">
            <div class="flex justify-between items-center gap-2">
              <span class="text-[10px] font-bold text-foreground truncate flex items-center gap-1">
                <MusicIcon class="size-3 text-primary" />
                فایل صوتی ضمیمه شده
              </span>
              <span class="text-[10px] text-muted-foreground font-bold shrink-0">
                {{ formatTime(audioCurrentTime) }} / {{ formatTime(audioDuration || parseFloat(duration || '0')) }}
              </span>
            </div>

            <!-- Custom Seek bar -->
            <div class="flex items-center gap-2 w-full">
              <input 
                type="range"
                min="0"
                :max="audioDuration || 100"
                :value="audioCurrentTime"
                @input="onAudioSeek"
                class="w-full h-1 bg-muted rounded-lg appearance-none cursor-pointer accent-primary border-0 p-0"
                style="outline: none;"
              />
            </div>
          </div>

          <!-- Mute/Unmute button -->
          <button 
            @click="toggleMute"
            class="size-8 rounded-full hover:bg-white/10 dark:hover:bg-white/5 flex items-center justify-center text-muted-foreground hover:text-foreground transition-colors cursor-pointer shrink-0"
          >
            <Volume2Icon v-if="!isMuted" class="size-4" />
            <VolumeXIcon v-else class="size-4 text-destructive" />
          </button>
        </div>
      </div>
    </div>

    <!-- Active Reactions (Telegram Style) -->
    <div 
      v-if="localReactions.length > 0" 
      class="px-5 pb-3 flex flex-wrap gap-1.5 justify-start"
      dir="rtl"
    >
      <button
        v-for="reaction in localReactions"
        :key="reaction.emoji"
        @click="handleReactionClick(reaction.emoji)"
        :class="[
          'px-2.5 py-1 rounded-full text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer border',
          reaction.reacted
            ? 'bg-primary/10 border-primary/20 text-primary shadow-xs'
            : 'bg-white/5 dark:bg-white/2 border-transparent text-muted-foreground hover:text-foreground hover:bg-white/10'
        ]"
      >
        <span>{{ reaction.emoji }}</span>
        <span class="text-[10px] font-bold">{{ toPersianDigits(reaction.count) }}</span>
      </button>
    </div>

    <!-- Card Footer Action Controls -->
    <div class="px-5 py-3 bg-white/2 dark:bg-black/2 flex items-center justify-between gap-4">
      <div class="flex items-center gap-2">
        <!-- Like Action Button -->
        <button 
          @click="toggleLike"
          :class="[
            'px-3.5 py-1.5 rounded-full text-xs font-semibold flex items-center gap-2 transition-all cursor-pointer border',
            isLiked 
              ? 'bg-destructive/10 border-destructive/20 text-destructive shadow-xs' 
              : 'bg-white/5 dark:bg-white/2 border-transparent text-muted-foreground hover:text-foreground hover:bg-white/10'
          ]"
        >
          <HeartIcon :class="['size-4 transition-transform duration-300', isLiked ? 'fill-destructive scale-110' : '']" />
          <span class="text-[11px] font-bold">{{ toPersianDigits(localLikesCount) }}</span>
        </button>

        <!-- Comments Action (Badge Toggle) -->
        <button 
          @click="showComments = !showComments"
          :class="[
            'px-3.5 py-1.5 rounded-full text-xs font-semibold flex items-center gap-2 transition-all cursor-pointer border',
            showComments
              ? 'bg-primary/10 border-primary/20 text-primary shadow-xs'
              : 'bg-white/5 dark:bg-white/2 border-transparent text-muted-foreground hover:text-foreground hover:bg-white/10'
          ]"
        >
          <MessageCircleIcon class="size-4" />
          <span class="text-[11px] font-bold">{{ toPersianDigits(localComments.length) }}</span>
          <Badge 
            v-if="localComments.length > 0" 
            variant="secondary" 
            class="h-4 px-1 rounded-sm text-[8px] bg-primary/20 text-primary border-0 font-bold"
          >
            جدید
          </Badge>
        </button>
      </div>

      <!-- Share Button -->
      <Button 
        variant="ghost" 
        size="icon" 
        class="size-8 rounded-full text-muted-foreground hover:text-foreground"
        @click="handleShare"
      >
        <Share2Icon class="size-4" />
      </Button>
    </div>

    <!-- COMMENTS DRAWER SECTION -->
    <transition name="expand-comments">
      <div 
        v-if="showComments" 
        class="bg-white/2 dark:bg-black/5 flex flex-col overflow-hidden"
      >
        <!-- Comments List -->
        <div class="px-5 py-4 flex flex-col gap-3.5 max-h-[250px] overflow-y-auto scrollbar-thin">
          <div v-if="localComments.length === 0" class="text-center py-4 text-[10.5px] text-muted-foreground font-medium">
            هنوز نظری ثبت نشده است. اولین نظر را شما بنویسید!
          </div>
          <div 
            v-for="comment in localComments" 
            :key="comment.id"
            class="flex items-start gap-3 text-right"
          >
            <!-- Commenter Avatar -->
            <Avatar class="size-8">
              <AvatarImage :src="comment.authorAvatar || ''" :alt="comment.authorName" />
              <AvatarFallback class="bg-primary/5 text-primary text-[10px] font-bold">
                {{ comment.authorName.charAt(0) }}
              </AvatarFallback>
            </Avatar>

            <!-- Comment Content Box -->
            <div class="flex-1 bg-white/5 dark:bg-black/15 rounded-2xl px-3.5 py-2.5 flex flex-col gap-1">
              <div class="flex justify-between items-center">
                <span class="text-[11.5px] font-extrabold text-foreground">{{ comment.authorName }}</span>
                <span class="text-[10px] text-muted-foreground font-semibold">{{ toPersianDigits(comment.timestamp) }}</span>
              </div>
              <p class="text-[12.5px] leading-relaxed text-foreground/90 font-medium">
                {{ comment.text }}
              </p>
            </div>
          </div>
        </div>

        <!-- Add Comment Form Input -->
        <div class="p-3 bg-white/3 dark:bg-black/10 flex items-center gap-2">
          <Avatar class="size-8 shrink-0">
            <AvatarFallback class="bg-primary/10 text-primary text-[10px] font-bold">
              <UserIcon class="size-3" />
            </AvatarFallback>
          </Avatar>
          <div class="flex-1 relative flex items-center">
            <Input 
              v-model="newCommentText"
              placeholder="دیدگاه خود را بنویسید..." 
              class="pr-3 pl-10 py-1.5 h-8.5 text-xs font-semibold rounded-xl bg-white dark:bg-black/40 border border-border/80 dark:border-border/40 focus-visible:ring-primary/30"
              @keydown.enter="submitComment"
            />
            <!-- Submit comment button inside input -->
            <button 
              @click="submitComment"
              class="absolute left-1.5 z-10 pointer-events-auto size-6 rounded-lg bg-primary/10 text-primary flex items-center justify-center hover:bg-primary/20 active:scale-95 transition-all cursor-pointer"
            >
              <SendIcon class="size-4 scale-x-[-1] -rotate-45" />
            </button>
          </div>
        </div>
      </div>
    </transition>
  </div>

  <!-- Teleported Context Menu Overlay -->
  <Teleport to="body">
    <PostContextMenu
      :isOpen="isContextMenuOpen"
      :triggerRect="triggerRect"
      :touchPos="{ x: touchX, y: touchY }"
      :postId="id"
      :postText="content"
      :isOwner="isPostOwner"
      @close="isContextMenuOpen = false"
      @edit="handleEditStart"
      @delete="emit('delete', id)"
      @pin="emit('pin', id)"
      @react="(postId, emoji) => handleReactionClick(emoji)"
      @copy="emit('copy', id)"
    />
  </Teleport>

  <!-- Teleported Edit Textarea Context Menu -->
  <Teleport to="body">
    <Transition name="fade">
      <div 
        v-if="isEditTextareaContextMenuOpen" 
        class="fixed inset-0 z-50 bg-black/35 dark:bg-black/55 backdrop-blur-xs flex items-center justify-center pointer-events-auto"
        @click="isEditTextareaContextMenuOpen = false"
        @contextmenu.prevent="isEditTextareaContextMenuOpen = false"
      >
        <div 
          class="flex flex-col gap-2 pointer-events-auto select-none scale-up text-right w-56 animate-menu-pop"
          :style="editTextareaMenuStyle"
          @click.stop
        >
          <div 
            class="bg-white/75 dark:bg-card/80 backdrop-blur-xl border border-white/30 dark:border-white/10 rounded-2xl p-1.5 shadow-xl flex flex-col gap-0.5 w-full"
            dir="rtl"
          >
            <!-- Copy Text -->
            <button 
              @click="handleEditTextareaCopy" 
              class="w-full text-right px-3 py-2 text-xs font-bold rounded-xl text-foreground hover:bg-secondary/60 flex items-center justify-between cursor-pointer transition-all active:scale-[0.98]"
            >
              <span>کپی کردن متن</span>
              <CopyIcon class="size-3.5 text-muted-foreground" />
            </button>
            
            <!-- Paste Text -->
            <button 
              @click="handleEditTextareaPaste" 
              class="w-full text-right px-3 py-2 text-xs font-bold rounded-xl text-foreground hover:bg-secondary/60 flex items-center justify-between cursor-pointer transition-all active:scale-[0.98]"
            >
              <span>پیست کردن متن</span>
              <ClipboardIcon class="size-3.5 text-muted-foreground" />
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
/* Scrollbar styling */
.scrollbar-thin::-webkit-scrollbar {
  width: 4px;
}
.scrollbar-thin::-webkit-scrollbar-track {
  background: transparent;
}
.scrollbar-thin::-webkit-scrollbar-thumb {
  background: var(--border);
  border-radius: 2px;
}

/* Expand transition for comments */
.expand-comments-enter-active,
.expand-comments-leave-active {
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
  max-height: 400px;
}

.expand-comments-enter-from,
.expand-comments-leave-to {
  max-height: 0;
  opacity: 0;
}

/* Audio seek input styling */
input[type="range"] {
  background: rgba(var(--primary), 0.1);
}
input[type="range"]::-webkit-slider-runnable-track {
  background: transparent;
}
input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  margin-top: -4px; /* Align thumb with track */
  background-color: var(--primary);
  height: 12px;
  width: 12px;
  border-radius: 50%;
}

/* Animations for Custom Context Menu */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@keyframes menuPop {
  0% {
    opacity: 0;
    transform: scale(0.92) translateY(5px);
  }
  100% {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.animate-menu-pop {
  animation: menuPop 0.2s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
}
</style>
