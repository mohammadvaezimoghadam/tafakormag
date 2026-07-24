<script setup lang="ts">
import { ref, reactive, watch, onBeforeUnmount, computed, nextTick } from 'vue'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
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
  ClipboardIcon,
  CircleFadingArrowUpIcon
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
  isPinned?: boolean
  publishedPlatforms?: string[]
  telegramMessageIds?: Record<string, any>
  baleMessageIds?: Record<string, any>
}

const props = withDefaults(defineProps<Props>(), {
  likesCount: 0,
  comments: () => [],
  liked: false,
  reactions: () => [],
  isPinned: false,
  publishedPlatforms: () => [],
  telegramMessageIds: () => ({}),
  baleMessageIds: () => ({})
})

const emit = defineEmits<{
  (e: 'like', id: string | number, newState: boolean): void
  (e: 'share', id: string | number): void
  (e: 'add-comment', postId: string | number, comment: Comment): void
  (e: 'edit', id: string | number): void
  (e: 'delete', id: string | number): void
  (e: 'publication-status', id: string | number): void
  (e: 'pin', id: string | number): void
  (e: 'react', id: string | number, emoji: string, currentReactions: PostReaction[]): void
  (e: 'copy', id: string | number): void
}>()

import { useLanguageStore } from '@/stores/languageStore'
const languageStore = useLanguageStore()

// Helper for Farsi digits
const toPersianDigits = (num: number | string) => {
  return languageStore.n(num)
}

const formatTimestamp = (isoString: string) => {
  if (!isoString) return ''
  if (isoString === 'هم‌اکنون') return languageStore.t('هم‌اکنون', 'just now')
  if (isoString.includes(':') && !isoString.includes('-')) {
    return languageStore.n(isoString)
  }
  try {
    const date = new Date(isoString)
    if (isNaN(date.getTime())) return languageStore.n(isoString)
    
    return date.toLocaleDateString(languageStore.currentLanguage === 'fa' ? 'fa-IR' : 'en-US', {
      hour: '2-digit',
      minute: '2-digit',
      numberingSystem: languageStore.currentLanguage === 'fa' ? 'arabext' : 'latn'
    })
  } catch (e) {
    return languageStore.n(isoString)
  }
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
import PublicationStatusModal from './PublicationStatusModal.vue'
import { usePostStore } from '@/stores/postStore'
import { useUserStore } from '@/stores/userStore'

const postStore = usePostStore()
const userStore = useUserStore()
const isPublicationStatusOpen = ref(false)

const handlePublicationStatus = () => {
  isPublicationStatusOpen.value = true
  emit('publication-status', props.id)
}

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

const handleEditStart = () => {
  console.log('[PostCard] handleEditStart emitting edit for postId:', props.id)
  emit('edit', props.id)
  isContextMenuOpen.value = false
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
  if (isEditing.value) return
  cancelLongPress()
}

const handleMouseLeave = () => {
  if (isEditing.value) return
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
  if (isEditing.value) return
  cancelLongPress()
  if (isLongPressTriggered) {
    e.preventDefault()
  }
}

const handleTouchMove = (e: TouchEvent) => {
  if (isEditing.value) return
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

const commentsLoading = ref(false)

watch(showComments, async (newVal) => {
  if (newVal) {
    commentsLoading.value = true
    try {
      await postStore.fetchComments(props.id)
    } catch (err) {
      console.error('Error fetching comments:', err)
    } finally {
      commentsLoading.value = false
    }
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
  if (isNaN(timeInSeconds)) return languageStore.n('00:00')
  const minutes = Math.floor(timeInSeconds / 60)
  const seconds = Math.floor(timeInSeconds % 60)
  const pad = (num: number) => num < 10 ? '0' + num : num
  return languageStore.n(`${pad(minutes)}:${pad(seconds)}`)
}
</script>

<template>
  <div 
    ref="cardRef"
    :class="[
      'w-full bg-background/12 dark:bg-card/10 backdrop-blur-md border border-border/60 rounded-3xl shadow-none transition-all duration-300 flex flex-col overflow-hidden text-start',
      props.isPinned ? 'border-primary/45 bg-primary/[0.01]' : '',
      isEditing ? 'select-text' : 'select-none',
      isPressing ? 'scale-[0.96] shadow-inner bg-background/5 dark:bg-card/5 border-border/30 brightness-95' : 'scale-100'
    ]"
    :dir="languageStore.dir"
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
        <div class="flex flex-col text-start">
          <span class="text-xs font-bold text-foreground">{{ author.name }}</span>
          <span class="text-[10px] text-muted-foreground mt-0.5">{{ author.role || languageStore.t('عضو تاپیک', 'Topic Member') }}</span>
        </div>
      </div>

      <div class="flex items-center gap-2">
        <!-- Timestamp -->
        <div class="flex items-center gap-1.5 text-xs font-bold text-muted-foreground">
          <ClockIcon class="size-3.5 text-primary" />
          <span>{{ formatTimestamp(timestamp) }}</span>
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
      <p 
        v-if="content" 
        class="text-sm font-medium leading-relaxed text-foreground/90 whitespace-pre-line text-start"
        dir="auto"
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
            {{ languageStore.t('نمایش تصویر کامل', 'View Full Image') }}
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
                {{ languageStore.t('فایل صوتی ضمیمه شده', 'Attached audio file') }}
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
            {{ languageStore.t('جدید', 'New') }}
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
          <template v-if="commentsLoading">
            <div 
              v-for="i in 2" 
              :key="'comment-skeleton-' + i"
              class="flex items-start gap-3 text-start animate-pulse"
            >
              <Skeleton class="size-8 rounded-full shrink-0" />
              <div class="flex-1 flex flex-col gap-1.5 px-3.5 py-2.5 bg-white/5 dark:bg-black/15 rounded-2xl">
                <div class="flex justify-between items-center">
                  <Skeleton class="h-3.5 w-16 rounded-md" />
                  <Skeleton class="h-3 w-8 rounded-md" />
                </div>
                <Skeleton class="h-3.5 w-full rounded-md" />
              </div>
            </div>
          </template>
          <template v-else>
            <div v-if="localComments.length === 0" class="text-center py-4 text-[10.5px] text-muted-foreground font-medium">
              {{ languageStore.t('هنوز نظری ثبت نشده است. اولین نظر را شما بنویسید!', 'No comments yet. Be the first to comment!') }}
            </div>
            <div 
              v-for="comment in localComments" 
              :key="comment.id"
              class="flex items-start gap-3 text-start"
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
                  <span class="text-[10px] text-muted-foreground font-semibold">{{ formatTimestamp(comment.timestamp) }}</span>
                </div>
                <p class="text-[12.5px] leading-relaxed text-foreground/90 font-medium text-start" dir="auto">
                  {{ comment.text }}
                </p>
              </div>
            </div>
          </template>
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
              :placeholder="languageStore.t('دیدگاه خود را بنویسید...', 'Write a comment...')" 
              class="py-1.5 h-8.5 text-xs font-semibold rounded-xl bg-white dark:bg-black/40 border border-border/80 dark:border-border/40 focus-visible:ring-primary/30 text-start"
              :class="[languageStore.isFa ? 'pr-3 pl-10' : 'pl-3 pr-10']"
              dir="auto"
              @keydown.enter="submitComment"
            />
            <!-- Submit comment button inside input -->
            <Button 
              @click="submitComment"
              variant="outline"
              size="icon"
              class="absolute z-10 pointer-events-auto size-6 rounded-lg bg-primary/10 text-primary flex items-center justify-center hover:bg-primary/20 active:scale-95 transition-all border-none"
              :class="[languageStore.isFa ? 'left-1.5' : 'right-1.5']"
            >
              <CircleFadingArrowUpIcon class="size-4" />
            </Button>
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
      @publication-status="handlePublicationStatus"
      @pin="emit('pin', id)"
      @react="(postId, emoji) => handleReactionClick(emoji)"
      @copy="emit('copy', id)"
    />
  </Teleport>

  <!-- Publication Status Modal -->
  <PublicationStatusModal
    v-model:is-open="isPublicationStatusOpen"
    :published-platforms="publishedPlatforms"
    :telegram-message-ids="telegramMessageIds"
    :bale-message-ids="baleMessageIds"
    :created-at="timestamp"
    @close="isPublicationStatusOpen = false"
  />

  <!-- Teleported Edit Textarea Context Menu (Removed) -->
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
