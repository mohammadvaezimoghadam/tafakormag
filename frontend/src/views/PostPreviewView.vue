<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDark, useToggle } from '@vueuse/core'
import { 
  fetchPostDetails, 
  fetchComments, 
  createAnonymousComment, 
  createComment 
} from '@/api'
import { useLanguageStore } from '@/stores/languageStore'
import { useToastStore } from '@/stores/toastStore'
import { useUserStore } from '@/stores/userStore'
import FormattedText from '@/components/common/FormattedText.vue'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { 
  ArrowRightIcon, 
  ArrowLeftIcon,
  MessageCircleIcon, 
  HeartIcon, 
  SendIcon, 
  SunIcon, 
  MoonIcon, 
  LanguagesIcon, 
  ExternalLinkIcon, 
  ChevronLeftIcon,
  ChevronRightIcon,
  PlayIcon,
  PauseIcon,
  Volume2Icon,
  VolumeXIcon,
  MusicIcon,
  Loader2Icon,
  SparklesIcon,
  AlertCircleIcon,
  LockIcon
} from '@lucide/vue'

const route = useRoute()
const router = useRouter()
const languageStore = useLanguageStore()
const toastStore = useToastStore()
const userStore = useUserStore()

// Dark mode support
const isDark = useDark({
  selector: 'html',
  attribute: 'class',
  valueDark: 'dark',
  valueLight: '',
})
const toggleTheme = useToggle(isDark)

// Route param
const postId = computed(() => route.params.id as string)

// State
const loading = ref(true)
const notFound = ref(false)
const post = ref<any>(null)
const comments = ref<any[]>([])
const commentsLoading = ref(false)

// Anonymous comment form state
const commentText = ref('')
const authorName = ref('')
const isSubmitting = ref(false)

// Custom Audio Player State
const audioRef = ref<HTMLAudioElement | null>(null)
const isAudioPlaying = ref(false)
const audioCurrentTime = ref(0)
const audioDuration = ref(0)
const isMuted = ref(false)

// Custom Video Player State
const videoRef = ref<HTMLVideoElement | null>(null)
const isVideoPlaying = ref(false)

const formatTime = (seconds: number) => {
  if (isNaN(seconds) || seconds < 0) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${languageStore.n(mins)}:${languageStore.n(secs < 10 ? '0' + secs : secs)}`
}

const toggleAudioPlay = () => {
  if (!audioRef.value) return
  if (isAudioPlaying.value) {
    audioRef.value.pause()
  } else {
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

onBeforeUnmount(() => {
  if (audioRef.value) audioRef.value.pause()
  if (videoRef.value) videoRef.value.pause()
})

const formatTimestamp = (isoString: string) => {
  if (!isoString) return ''
  try {
    const date = new Date(isoString)
    if (isNaN(date.getTime())) return languageStore.n(isoString)
    return date.toLocaleDateString(languageStore.isFa ? 'fa-IR' : 'en-US', {
      hour: '2-digit',
      minute: '2-digit',
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      numberingSystem: languageStore.isFa ? 'arabext' : 'latn'
    })
  } catch (e) {
    return languageStore.n(isoString)
  }
}

// Load Post and Comments
const loadPostData = async () => {
  if (!postId.value) return
  loading.value = true
  notFound.value = false

  try {
    const res = await fetchPostDetails(postId.value)
    post.value = res.data
    await loadComments()
  } catch (err: any) {
    console.error('Error fetching post preview:', err)
    if (err.response?.status === 404) {
      notFound.value = true
    } else {
      toastStore.triggerToast(languageStore.t('خطا در بارگذاری یادداشت', 'Error loading post'), 'error')
    }
  } finally {
    loading.value = false
  }
}

const loadComments = async () => {
  if (!postId.value) return
  commentsLoading.value = true
  try {
    const res = await fetchComments(postId.value)
    comments.value = res.data || []
  } catch (err) {
    console.error('Error fetching comments:', err)
  } finally {
    commentsLoading.value = false
  }
}

const handleSubmitComment = async () => {
  const content = commentText.value.trim()
  if (!content) return

  isSubmitting.value = true
  try {
    const name = authorName.value.trim()
    const res = userStore.isAuthenticated 
      ? await createComment(postId.value, content, true, name)
      : await createAnonymousComment(postId.value, content, name)

    comments.value.push(res.data)
    commentText.value = ''
    authorName.value = ''
    toastStore.triggerToast(
      languageStore.t('نظر ناشناس شما با موفقیت ثبت شد', 'Your anonymous comment has been posted'),
      'success'
    )
  } catch (err) {
    console.error('Error submitting anonymous comment:', err)
    toastStore.triggerToast(
      languageStore.t('خطا در ارسال نظر. لطفا مجدد تلاش کنید.', 'Failed to send comment. Please try again.'),
      'error'
    )
  } finally {
    isSubmitting.value = false
  }
}

const navigateToTopic = () => {
  if (!post.value?.topic) return
  router.push(`/topic/${post.value.topic}`)
}

const goHome = () => {
  router.push('/')
}

onMounted(() => {
  loadPostData()
})
</script>

<template>
  <div 
    class="w-full max-w-[500px] flex flex-col gap-4.5 pb-10 mx-auto px-3.5 pt-4 min-h-screen relative animate-in fade-in slide-in-from-bottom-3 duration-300"
    :class="[languageStore.isFa ? 'text-right' : 'text-left']"
    :dir="languageStore.dir"
  >
    <!-- TOP APP BAR -->
    <header class="w-full flex items-center justify-between pb-2 border-b border-border/40">
      <div class="flex items-center gap-2">
        <Button 
          variant="ghost" 
          size="icon" 
          class="size-8 rounded-full text-muted-foreground hover:text-foreground cursor-pointer"
          @click="goHome"
          :title="languageStore.t('بازگشت به تفکر', 'Back to Tafakor')"
        >
          <ArrowRightIcon v-if="languageStore.isFa" class="size-4.5" />
          <ArrowLeftIcon v-else class="size-4.5" />
        </Button>
        <div class="flex flex-col">
          <div class="flex items-center gap-1.5">
            <span class="text-sm font-extrabold text-foreground tracking-tight">{{ languageStore.t('تفکر', 'Tafakor') }}</span>
            <Badge variant="secondary" class="h-4 px-1.5 text-[9px] font-bold text-primary bg-primary/10 border-primary/20">
              {{ languageStore.t('پیش‌نمایش', 'Preview') }}
            </Badge>
          </div>
          <span class="text-[9.5px] text-muted-foreground">{{ languageStore.t('مشاهده یادداشت و گفتگوی آزاد', 'View note and open discussion') }}</span>
        </div>
      </div>

      <!-- Actions (Theme & Language) -->
      <div class="flex items-center gap-1">
        <Button 
          variant="ghost" 
          size="icon" 
          class="size-8 rounded-full text-muted-foreground hover:text-foreground cursor-pointer"
          @click="languageStore.setLanguage(languageStore.currentLanguage === 'fa' ? 'en' : 'fa')"
          :title="languageStore.t('تغییر زبان', 'Change language')"
        >
          <LanguagesIcon class="size-4" />
        </Button>
        <Button 
          variant="ghost" 
          size="icon" 
          class="size-8 rounded-full text-muted-foreground hover:text-foreground cursor-pointer"
          @click="toggleTheme()"
          :title="languageStore.t('تغییر تم', 'Toggle theme')"
        >
          <SunIcon v-if="isDark" class="size-4 text-amber-400" />
          <MoonIcon v-else class="size-4 text-primary" />
        </Button>
      </div>
    </header>

    <!-- SKELETON LOADING -->
    <div v-if="loading" class="flex flex-col gap-4 animate-pulse">
      <!-- Topic Header Skeleton -->
      <div class="w-full bg-card/25 border border-border/50 rounded-2xl p-3.5 flex items-center justify-between gap-3">
        <div class="flex items-center gap-3 min-w-0">
          <Skeleton class="size-11 rounded-xl shrink-0" />
          <div class="flex flex-col gap-1.5">
            <Skeleton class="h-4 w-28 rounded-md" />
            <Skeleton class="h-3 w-40 rounded-md" />
          </div>
        </div>
        <Skeleton class="h-8 w-20 rounded-xl" />
      </div>

      <!-- Post Card Skeleton -->
      <div class="w-full bg-card/25 border border-border/50 rounded-3xl p-5 flex flex-col gap-4">
        <div class="flex items-center gap-3">
          <Skeleton class="size-10 rounded-full shrink-0" />
          <div class="flex flex-col gap-1.5">
            <Skeleton class="h-4 w-24 rounded-md" />
            <Skeleton class="h-3 w-16 rounded-md" />
          </div>
        </div>
        <div class="flex flex-col gap-2">
          <Skeleton class="h-4 w-full rounded-md" />
          <Skeleton class="h-4 w-[90%] rounded-md" />
          <Skeleton class="h-4 w-[75%] rounded-md" />
        </div>
      </div>
    </div>

    <!-- 404 NOT FOUND STATE -->
    <div v-else-if="notFound || !post" class="py-16 flex flex-col items-center justify-center gap-4 text-center">
      <div class="size-14 rounded-2xl bg-destructive/10 text-destructive flex items-center justify-center">
        <AlertCircleIcon class="size-7" />
      </div>
      <div class="flex flex-col gap-1">
        <h2 class="text-base font-extrabold text-foreground">{{ languageStore.t('یادداشت یافت نشد', 'Post Not Found') }}</h2>
        <p class="text-xs text-muted-foreground max-w-xs leading-relaxed">
          {{ languageStore.t('این یادداشت ممکن است حذف شده باشد یا لینک وارد شده نادرست است.', 'This post may have been deleted or the link is invalid.') }}
        </p>
      </div>
      <Button variant="outline" @click="goHome" class="rounded-xl text-xs font-bold gap-2 mt-2">
        <ArrowRightIcon v-if="languageStore.isFa" class="size-3.5" />
        <ArrowLeftIcon v-else class="size-3.5" />
        {{ languageStore.t('ورود به صفحه اصلی تفکر', 'Go to Tafakor Home') }}
      </Button>
    </div>

    <!-- MAIN CONTENT -->
    <template v-else>
      <!-- TOPIC SOURCE BANNER -->
      <div 
        v-if="post.topic"
        class="w-full bg-card/40 backdrop-blur-md border border-border/50 rounded-2xl p-3.5 flex items-center justify-between gap-3 shadow-xs hover:border-primary/20 transition-all"
      >
        <div class="flex items-center gap-3 min-w-0">
          <Avatar class="size-11 rounded-xl shrink-0 border border-border/40">
            <AvatarImage :src="post.topic_image || ''" :alt="post.topic_name || ''" />
            <AvatarFallback class="rounded-xl bg-primary/10 text-primary font-bold text-sm">
              {{ (post.topic_name || 'ت').charAt(0) }}
            </AvatarFallback>
          </Avatar>
          <div class="flex flex-col min-w-0">
            <div class="flex items-center gap-1.5">
              <span class="text-xs font-extrabold text-foreground truncate">{{ post.topic_name || languageStore.t('تاپیک تفکر', 'Tafakor Topic') }}</span>
            </div>
            <span class="text-[10px] text-muted-foreground truncate">
              {{ post.topic_description || languageStore.t('منبع اصلی یادداشت‌ها و گفتگوها', 'Main source of notes & discussions') }}
            </span>
          </div>
        </div>

        <Button 
          variant="outline" 
          size="sm" 
          class="h-8 px-3 rounded-xl text-[11px] font-bold text-primary border-primary/30 hover:bg-primary/10 gap-1.5 shrink-0 cursor-pointer"
          @click="navigateToTopic"
        >
          <span>{{ languageStore.t('ورود به تاپیک', 'View Topic') }}</span>
          <ExternalLinkIcon class="size-3.5" />
        </Button>
      </div>

      <!-- MAIN POST CARD -->
      <article class="w-full bg-card/30 dark:bg-card/20 backdrop-blur-md border border-border/50 rounded-3xl overflow-hidden shadow-xs flex flex-col transition-all">
        <!-- Post Header -->
        <div class="px-5 pt-4.5 pb-3 flex items-center justify-between gap-3 border-b border-border/30">
          <div class="flex items-center gap-3 min-w-0">
            <Avatar class="size-9 rounded-full shrink-0 border border-border/40">
              <AvatarImage :src="post.author_avatar || ''" :alt="post.author_name || ''" />
              <AvatarFallback class="bg-primary/10 text-primary font-bold text-xs">
                {{ (post.author_name || 'ع').charAt(0) }}
              </AvatarFallback>
            </Avatar>
            <div class="flex flex-col min-w-0">
              <span class="text-xs font-bold text-foreground truncate">{{ post.author_name || languageStore.t('کاربر تفکر', 'Tafakor User') }}</span>
              <span class="text-[10px] text-muted-foreground font-medium">{{ formatTimestamp(post.created_at) }}</span>
            </div>
          </div>

          <Badge v-if="post.topic_name" variant="secondary" class="h-5 px-2 text-[9px] font-bold rounded-md bg-muted/60 text-muted-foreground border-border/40">
            {{ post.topic_name }}
          </Badge>
        </div>

        <!-- Post Media -->
        <div v-if="post.media_file" class="w-full overflow-hidden bg-black/5 dark:bg-black/20">
          <!-- Image -->
          <div v-if="post.media_type === 'image'" class="w-full flex justify-center bg-black/10">
            <img 
              :src="post.media_file" 
              :alt="post.author_name || 'Post media'" 
              class="w-full max-h-[460px] object-cover" 
              loading="lazy"
            />
          </div>

          <!-- Video Player -->
          <div v-else-if="post.media_type === 'video'" class="relative w-full bg-black flex items-center justify-center">
            <video 
              ref="videoRef"
              :src="post.media_file" 
              class="w-full max-h-[460px] object-contain"
              playsinline
              @play="onVideoPlayStateChange"
              @pause="onVideoPlayStateChange"
              @ended="isVideoPlaying = false"
              controls
            ></video>
          </div>

          <!-- Audio Player -->
          <div v-else-if="post.media_type === 'audio'" class="p-4 bg-primary/5 border-y border-border/30">
            <audio 
              ref="audioRef" 
              :src="post.media_file" 
              preload="metadata" 
              @timeupdate="onAudioTimeUpdate" 
              @loadedmetadata="onAudioLoadedMetadata" 
              @ended="onAudioEnded" 
              class="hidden"
            ></audio>

            <div class="flex items-center gap-3">
              <button 
                @click="toggleAudioPlay"
                class="size-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center shadow-sm hover:scale-105 active:scale-95 transition-all cursor-pointer shrink-0"
              >
                <PlayIcon v-if="!isAudioPlaying" class="size-4 ml-0.5 rtl:ml-0 rtl:mr-0.5" />
                <PauseIcon v-else class="size-4" />
              </button>

              <div class="flex-1 flex flex-col gap-1.5">
                <div class="flex items-center justify-between">
                  <span class="text-[10.5px] font-bold text-foreground flex items-center gap-1.5">
                    <MusicIcon class="size-3 text-primary" />
                    {{ languageStore.t('فایل صوتی پیوست', 'Attached Audio File') }}
                  </span>
                  <span class="text-[10px] text-muted-foreground font-bold">
                    {{ formatTime(audioCurrentTime) }} / {{ formatTime(audioDuration) }}
                  </span>
                </div>
                <input 
                  type="range"
                  min="0"
                  :max="audioDuration || 100"
                  :value="audioCurrentTime"
                  @input="onAudioSeek"
                  class="w-full h-1 bg-muted rounded-lg appearance-none cursor-pointer accent-primary border-0 p-0"
                />
              </div>

              <button 
                @click="toggleMute"
                class="size-8 rounded-full hover:bg-muted/60 flex items-center justify-center text-muted-foreground hover:text-foreground transition-colors cursor-pointer shrink-0"
              >
                <Volume2Icon v-if="!isMuted" class="size-4" />
                <VolumeXIcon v-else class="size-4 text-destructive" />
              </button>
            </div>
          </div>
        </div>

        <!-- Post Content Text (Full Markdown Text) -->
        <div class="px-5 py-4 text-start">
          <FormattedText 
            :text="post.content" 
            class="text-xs text-foreground/95 leading-relaxed tracking-normal break-words"
          />
        </div>

        <!-- Reactions & Stats Bar -->
        <div class="px-5 py-3 bg-white/2 dark:bg-black/10 border-t border-border/30 flex items-center justify-between gap-3">
          <!-- Emoji Reactions -->
          <div class="flex items-center gap-1.5 flex-wrap">
            <template v-if="post.reactions_summary && Object.keys(post.reactions_summary).length > 0">
              <span 
                v-for="(count, emoji) in post.reactions_summary" 
                :key="emoji"
                class="px-2.5 py-1 rounded-full text-xs font-semibold flex items-center gap-1 bg-muted/40 border border-border/40 text-foreground"
              >
                <span>{{ emoji }}</span>
                <span class="text-[10.5px] font-bold">{{ languageStore.n(count) }}</span>
              </span>
            </template>
            <span v-else class="text-[10.5px] text-muted-foreground font-medium flex items-center gap-1">
              <HeartIcon class="size-3.5 text-muted-foreground" />
              {{ languageStore.t('هنوز واکنشی ثبت نشده است', 'No reactions yet') }}
            </span>
          </div>

          <!-- Comments count badge -->
          <div class="flex items-center gap-1 text-muted-foreground text-[11px] font-bold">
            <MessageCircleIcon class="size-3.5" />
            <span>{{ languageStore.n(comments.length) }}</span>
            <span class="text-[10px] font-medium">{{ languageStore.t('نظر', 'comments') }}</span>
          </div>
        </div>
      </article>

      <!-- CTA TO TOPIC -->
      <div 
        @click="navigateToTopic"
        class="w-full p-4 rounded-2xl bg-gradient-to-r from-primary/10 via-primary/5 to-transparent border border-primary/20 flex items-center justify-between gap-3 cursor-pointer hover:border-primary/40 transition-all select-none group"
      >
        <div class="flex items-center gap-3 min-w-0">
          <div class="size-9 rounded-xl bg-primary/15 text-primary flex items-center justify-center shrink-0 group-hover:scale-105 transition-transform">
            <SparklesIcon class="size-4.5" />
          </div>
          <div class="flex flex-col min-w-0">
            <span class="text-xs font-extrabold text-foreground">{{ languageStore.t('مشاهده یادداشت در تاپیک اصلی تفکر', 'View post in main Tafakor topic') }}</span>
            <span class="text-[10px] text-muted-foreground">{{ languageStore.t('برای مطالعه مطالب مرتبط و پیوستن به این حلقه کلیک کنید', 'Click to read related notes & join discussion') }}</span>
          </div>
        </div>

        <ChevronLeftIcon v-if="languageStore.isFa" class="size-4 text-primary shrink-0 transition-transform group-hover:-translate-x-1" />
        <ChevronRightIcon v-else class="size-4 text-primary shrink-0 transition-transform group-hover:translate-x-1" />
      </div>

      <!-- COMMENTS SECTION -->
      <section class="w-full flex flex-col gap-4 mt-2">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <MessageCircleIcon class="size-4 text-primary" />
            <h3 class="text-xs font-extrabold text-foreground">{{ languageStore.t('نظرات و دیدگاه‌ها', 'Comments & Discussion') }}</h3>
            <Badge variant="secondary" class="h-4.5 px-1.5 rounded-full text-[9.5px] font-bold bg-primary/10 text-primary border-0">
              {{ languageStore.n(comments.length) }}
            </Badge>
          </div>
          <span class="text-[10px] text-muted-foreground">{{ languageStore.t('بدون نیاز به عضویت', 'No account required') }}</span>
        </div>

        <!-- Comments List -->
        <div class="flex flex-col gap-2.5">
          <div v-if="commentsLoading" class="flex flex-col gap-2.5 animate-pulse">
            <div v-for="i in 2" :key="'comment-skel-' + i" class="p-3 bg-card/20 rounded-2xl flex items-start gap-3">
              <Skeleton class="size-8 rounded-full shrink-0" />
              <div class="flex-1 flex flex-col gap-2">
                <Skeleton class="h-3 w-20 rounded-md" />
                <Skeleton class="h-3.5 w-full rounded-md" />
              </div>
            </div>
          </div>

          <div 
            v-else-if="comments.length === 0" 
            class="py-8 text-center bg-card/15 rounded-2xl border border-border/40 p-4 flex flex-col items-center justify-center gap-1.5"
          >
            <p class="text-xs text-foreground/80 font-semibold">{{ languageStore.t('هنوز نظری ثبت نشده است', 'No comments yet') }}</p>
            <p class="text-[10px] text-muted-foreground">{{ languageStore.t('شما اولین نفری باشید که دیدگاه یا بازخورد خود را به صورت ناشناس می‌نویسد.', 'Be the first to share your feedback anonymously.') }}</p>
          </div>

          <div 
            v-else
            v-for="c in comments" 
            :key="c.id" 
            class="p-3.5 bg-card/25 dark:bg-card/15 border border-border/40 rounded-2xl flex items-start gap-3 text-start shadow-2xs"
          >
            <!-- Avatar -->
            <Avatar class="size-8 shrink-0 border border-border/40">
              <AvatarFallback class="bg-primary/10 text-primary text-[10px] font-bold">
                {{ (c.user_name || 'ن').charAt(0) }}
              </AvatarFallback>
            </Avatar>

            <!-- Body -->
            <div class="flex-1 flex flex-col gap-1 min-w-0">
              <div class="flex items-center justify-between gap-2">
                <div class="flex items-center gap-1.5 min-w-0">
                  <span class="text-[11px] font-bold text-foreground truncate">{{ c.user_name || languageStore.t('کاربر ناشناس', 'Anonymous User') }}</span>
                  <Badge 
                    v-if="c.is_anonymous" 
                    variant="outline" 
                    class="h-4 px-1 rounded text-[8px] font-semibold text-primary/80 border-primary/20 bg-primary/5"
                  >
                    {{ languageStore.t('ناشناس', 'Anonymous') }}
                  </Badge>
                </div>
                <span class="text-[9.5px] text-muted-foreground shrink-0">{{ formatTimestamp(c.created_at) }}</span>
              </div>
              <p class="text-xs text-foreground/90 leading-relaxed break-words whitespace-pre-wrap">{{ c.content }}</p>
            </div>
          </div>
        </div>

        <!-- ANONYMOUS COMMENT COMPOSER -->
        <div class="w-full bg-card/35 dark:bg-card/20 backdrop-blur-md border border-border/50 rounded-2xl p-4 flex flex-col gap-3 shadow-xs mt-2">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-1.5 text-xs font-bold text-foreground">
              <LockIcon class="size-3.5 text-primary" />
              <span>{{ languageStore.t('ثبت نظر ناشناس', 'Post Anonymous Comment') }}</span>
            </div>
            <span class="text-[9.5px] text-muted-foreground">{{ languageStore.t('هویت شما پنهان می‌ماند', 'Your identity is hidden') }}</span>
          </div>

          <div class="flex flex-col gap-2">
            <Input 
              v-model="authorName" 
              :placeholder="languageStore.t('نام مستعار یا نمایشی (اختیاری)', 'Display nickname (optional)')" 
              class="h-9 text-xs font-semibold focus-visible:ring-primary/20"
              maxlength="40"
              dir="auto"
            />
            
            <textarea 
              v-model="commentText" 
              rows="3" 
              :placeholder="languageStore.t('نظر، دیدگاه یا پرسش خود را اینجا بنویسید...', 'Write your thought, feedback, or question here...')" 
              class="w-full text-xs p-3 rounded-xl bg-background/60 dark:bg-background/40 border border-border/60 focus:border-primary/50 focus:ring-2 focus:ring-primary/10 focus:outline-none resize-none transition-all placeholder:text-muted-foreground font-sans leading-relaxed"
              dir="auto"
              maxlength="1000"
            ></textarea>
          </div>

          <div class="flex items-center justify-between gap-3 pt-1">
            <span class="text-[9.5px] text-muted-foreground">
              {{ languageStore.n(1000 - commentText.length) }} {{ languageStore.t('کاراکتر باقی‌مانده', 'chars remaining') }}
            </span>

            <Button 
              :disabled="!commentText.trim() || isSubmitting" 
              @click="handleSubmitComment" 
              class="h-8.5 px-4 rounded-xl text-xs font-bold gap-2 cursor-pointer transition-all"
            >
              <Loader2Icon v-if="isSubmitting" class="size-3.5 animate-spin" />
              <SendIcon v-else class="size-3.5 rtl:rotate-180" />
              <span>{{ languageStore.t('ارسال نظر', 'Submit Comment') }}</span>
            </Button>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>
