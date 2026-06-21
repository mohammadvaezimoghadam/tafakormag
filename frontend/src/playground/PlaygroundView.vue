<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import UserProfileCard from '@/components/UserProfileCard.vue'
import LoginCard from '@/components/LoginCard.vue'
import PlatformHeader from '@/components/PlatformHeader.vue'
import PlatformNavigation from '@/components/PlatformNavigation.vue'
import TopicCard from '@/components/TopicCard.vue'
import ProfileOptionCard from '@/components/ProfileOptionCard.vue'
import ProfileCard from '@/components/ProfileCard.vue'
import PostCard, { type PostReaction } from '@/components/PostCard.vue'
import CreateTopicModal from '@/components/CreateTopicModal.vue'
import BotConnectionCard from '@/components/BotConnectionCard.vue'
import TopicMessageInput from '@/components/TopicMessageInput.vue'
import TopicEditView from '@/components/TopicEditView.vue'
import TopicConnectionsView from '@/components/TopicConnectionsView.vue'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { 
  FlaskConicalIcon,
  SmartphoneIcon, 
  TabletIcon, 
  LaptopIcon, 
  PlayIcon,
  RefreshCwIcon,
  InfoIcon,
  TerminalIcon,
  CheckCircle2Icon,
  UserIcon,
  KeyRoundIcon,
  SignalIcon,
  WifiIcon,
  BatteryIcon,
  SendIcon,
  HomeIcon,
  SearchIcon,
  ArrowRightIcon,
  SettingsIcon,
  LinkIcon,
  SparklesIcon,
  PencilIcon,
  MessageCircleIcon,
  ChevronLeftIcon,
  PlusIcon
} from '@lucide/vue'

// Simulator configs
const currentComponent = ref<'profile' | 'login' | 'header' | 'nav' | 'topic' | 'search' | 'profile-option' | 'profile-card-header' | 'post' | 'create-topic-modal' | 'bot-connection' | 'topic-input' | 'topic-edit' | 'topic-connections'>('profile')
const viewportWidth = ref<'100%' | '768px' | '375px'>('100%')
const sandboxBg = ref<'default' | 'gradient' | 'grid' | 'image'>('default')
const activeState = ref<'idle' | 'loading' | 'error' | 'empty' | 'success'>('idle')

// Create Topic Modal simulation state
const simulatorIsModalOpen = ref(false)

const handleModalCreate = (topic: any) => {
  logEvent('CreateTopicModal: Topic Created', topic)
  simulatorIsModalOpen.value = false
}

const handleModalClose = () => {
  logEvent('CreateTopicModal: Modal Closed', {})
  simulatorIsModalOpen.value = false
}

// Bot Connection simulation state
const simulatorBotPlatform = ref<'telegram' | 'bale'>('telegram')
const simulatorBotStatus = ref<'disconnected' | 'connecting' | 'connected' | 'conflict'>('disconnected')
const simulatorBotToken = ref('')

const handleBotConnect = (token: string) => {
  simulatorBotToken.value = token
  logEvent('BotConnectionCard: Connect Attempt', { platform: simulatorBotPlatform.value, token })
  
  simulatorBotStatus.value = 'connecting'
  setTimeout(() => {
    if (token.includes('conflict')) {
      simulatorBotStatus.value = 'conflict'
      logEvent('BotConnectionCard: Connection Failed (Conflict)', { reason: 'Token already used by another project' })
    } else {
      simulatorBotStatus.value = 'connected'
      logEvent('BotConnectionCard: Connected Successfully', { platform: simulatorBotPlatform.value })
    }
  }, 1500)
}

const handleBotDisconnect = () => {
  simulatorBotStatus.value = 'disconnected'
  simulatorBotToken.value = ''
  logEvent('BotConnectionCard: Disconnected', { platform: simulatorBotPlatform.value })
}

const handleBotEdit = (token: string) => {
  logEvent('BotConnectionCard: Edit Token Requested', { platform: simulatorBotPlatform.value, currentToken: token })
}

// Topic Message Input simulation state
const simulatorInputDisabled = ref(false)
const simulatorInputPlaceholder = ref('پیام خود را بنویسید...')
const simulatorInputText = ref('')
const simulatorInputAttachments = ref<any[]>([])

const simulateAddAttachment = (type: 'image' | 'video' | 'audio' | 'file') => {
  const id = Date.now()
  let newFile: any = {
    id,
    name: '',
    type,
    status: 'uploading',
    progress: 0
  }
  
  if (type === 'image') {
    newFile.name = `image_${Math.floor(Math.random() * 1000)}.jpg`
    newFile.url = 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=100&auto=format&fit=crop&q=80'
  } else if (type === 'video') {
    newFile.name = `video_${Math.floor(Math.random() * 100)}.mp4`
  } else if (type === 'audio') {
    newFile.name = `voice_${Math.floor(Math.random() * 100)}.ogg`
    newFile.size = '0:14'
  } else {
    newFile.name = `doc_${Math.floor(Math.random() * 100)}.pdf`
    newFile.size = '1.4 MB'
  }
  
  simulatorInputAttachments.value.push(newFile)
  logEvent('TopicMessageInput: Simulated Attachment Added', { type, name: newFile.name })
  
  // Simulate progress
  const interval = setInterval(() => {
    const file = simulatorInputAttachments.value.find(f => f.id === id)
    if (!file) {
      clearInterval(interval)
      return
    }
    
    if (file.progress < 100) {
      file.progress += 25
      if (file.progress >= 100) {
        file.progress = 100
        file.status = 'completed'
        logEvent('TopicMessageInput: Simulated Attachment Upload Completed', { name: file.name })
        clearInterval(interval)
      }
    }
  }, 400)
}

const handleInputSend = (msg: any) => {
  logEvent('TopicMessageInput: Message Sent', msg)
  simulatorInputText.value = ''
  simulatorInputAttachments.value = []
}

const handleInputRemoveAttachment = (id: string | number) => {
  logEvent('TopicMessageInput: Attachment Removed', { id })
  simulatorInputAttachments.value = simulatorInputAttachments.value.filter(a => a.id !== id)
}

// Compute available states based on the active component
const availableStates = computed(() => {
  if (currentComponent.value === 'profile') {
    return ['idle', 'loading', 'error', 'empty'] as const
  } else {
    return ['idle', 'loading', 'error', 'success'] as const
  }
})

const handleComponentChange = (comp: 'profile' | 'login' | 'header' | 'nav' | 'topic' | 'search' | 'profile-option' | 'profile-card-header' | 'post' | 'create-topic-modal' | 'bot-connection' | 'topic-input' | 'topic-edit' | 'topic-connections') => {
  currentComponent.value = comp
  activeState.value = 'idle'
  logEvent('Component Changed', { component: comp })
}

// Mock user data structure
interface UserProfile {
  name: string
  email: string
  role: string
  status: 'active' | 'inactive'
}

const initialUser: UserProfile = {
  name: 'شایان مهدوی',
  email: 'shayan@example.com',
  role: 'طراح رابط کاربری (UI/UX)',
  status: 'active'
}
const mockUser = reactive<UserProfile>({ ...initialUser })

// Event logging system
interface SystemEvent {
  id: number
  time: string
  name: string
  data: string
}
const eventLog = ref<SystemEvent[]>([])
let logId = 0

const logEvent = (name: string, data: any) => {
  const now = new Date()
  const timeStr = now.toTimeString().split(' ')[0] ?? ''
  eventLog.value.unshift({
    id: ++logId,
    time: timeStr,
    name,
    data: JSON.stringify(data) ?? ''
  })
}

// Event Handlers
const handleSave = (updatedUser: UserProfile) => {
  mockUser.name = updatedUser.name
  mockUser.email = updatedUser.email
  mockUser.status = updatedUser.status
  logEvent('Save Button Clicked', updatedUser)
}

const handleStatusToggle = () => {
  mockUser.status = mockUser.status === 'active' ? 'inactive' : 'active'
  logEvent('Status Toggle Clicked', { newStatus: mockUser.status })
}

const resetData = () => {
  Object.assign(mockUser, initialUser)
  activeState.value = 'idle'
  simulatorIsInnerPage.value = false
  simulatorActiveTab.value = 'home'
  simulatorSearchQuery.value = ''
  simulatorSearchExpanded.value = false
  simulatorSettingsBadge.value = ''
  simulatorConnectionsBadge.value = '۳ فعال'
  simulatorAiBadge.value = 'جدید'
  simulatorProfileCardName.value = 'شایان مهدوی'
  simulatorProfileCardPhone.value = '۰۹۱۲۳۴۵۶۷۸۹'
  simulatorProfileCardStatus.value = 'success'
  mockTopics.value = [
    { id: 1, title: 'گروه توسعه تفکر', description: 'شایان: طرح هدر پلتفرم را اصلاح کردم و انیمیشن بک به درستی کار می‌کند.', unreadCount: 5, time: '۱۲:۳۰', labels: ['فناوری', 'توسعه'], pinned: true },
    { id: 2, title: 'کانال عمومی اخبار پلتفرم', description: 'اطلاعیه: نسخه بتای آزمایشگاه تست شبیه‌سازها هم‌اکنون به صورت آزمایشی در دسترس قرار گرفت.', unreadCount: 12, time: '۱۰:۱۵', labels: ['اخبار', 'تفکر'], pinned: false },
    { id: 3, title: 'تیم طراحی رابط کاربری', description: 'امیر: لطفا آیکون‌ها و رنگ‌های شیشه‌ای را مجدداً هماهنگ کنید.', unreadCount: 0, time: 'دیروز', labels: ['طراحی', 'UI/UX'], pinned: false }
  ]
  eventLog.value = []
  logEvent('Simulator Reset', {})
}

// Login card specific handlers
const handleLoginPhoneSubmit = (phone: string) => {
  logEvent('Login: Phone Submitted', { phone })
}

const handleLoginOtpSubmit = (otp: string) => {
  logEvent('Login: OTP Code Submitted', { otp })
}

const handleLoginStateChange = (newState: string) => {
  logEvent('Login: Component Internal State', { state: newState })
  if (newState === 'success') {
    activeState.value = 'success'
  } else if (newState === 'idle') {
    activeState.value = 'idle'
  }
}

// Platform Header simulation variables
const simulatorIsInnerPage = ref(false)
const simulatorInnerTitle = ref('پشتیبانی تفکر')

const mockChats = [
  { id: 1, name: 'پشتیبانی تفکر', message: 'سلام! انیمیشن تفکیک دکمه...', time: '۱۲:۳۰', avatar: 'پ' },
  { id: 2, name: 'کانال اطلاعیه‌ها', message: 'نسخه جدید دشبورد منتشر شد.', time: '۱۰:۱۵', avatar: 'ا' },
  { id: 3, name: 'امیرحسین رضایی', message: 'طرح کارت لاگین رو بررسی کردی؟', time: 'دیروز', avatar: 'ا' }
]

const enterChat = (chat: typeof mockChats[0]) => {
  simulatorInnerTitle.value = chat.name
  simulatorIsInnerPage.value = true
  logEvent('Header: Navigation to Chat', { chatName: chat.name })
}

const handleHeaderBack = () => {
  simulatorIsInnerPage.value = false
  logEvent('Header: Back Button Clicked', { action: 'Go back to Home' })
}

const handleHeaderAction = (actionName: string) => {
  logEvent(`Header: Action Clicked [${actionName}]`, {})
}

const handleSimulatorEditTopic = () => {
  const newTitle = prompt('ویرایش مشخصات تاپیک (نام تاپیک):', simulatorInnerTitle.value)
  if (newTitle !== null && newTitle.trim()) {
    simulatorInnerTitle.value = newTitle.trim()
    logEvent('Header: Topic Edited', { newTitle: newTitle.trim() })
  }
}

const handleSimulatorDeleteTopic = () => {
  logEvent('Header: Topic Deleted', { topicTitle: simulatorInnerTitle.value })
  simulatorIsInnerPage.value = false
}

const handleSimulatorTopicConnections = () => {
  logEvent('Header: Topic Connections Settings Opened', { topicTitle: simulatorInnerTitle.value })
  currentComponent.value = 'topic-connections'
}

// Simulator Topic Edit & Connections state variables
const simulatorTelegramConnected = ref(true)
const simulatorBaleConnected = ref(false)
const simulatorTopicData = ref({
  id: 1,
  title: 'پشتیبانی فنی پلتفرم',
  description: 'درخواست راهنمایی در مورد دیزاین سیستم پلتفرم',
  image: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100&auto=format&fit=crop&q=80',
  telegram_bot_active: true,
  bale_bot_active: false,
  telegram_connections: [1] as number[],
  bale_connections: [] as number[]
})

const resetSimulatorTopicEdit = () => {
  simulatorTopicData.value = {
    id: 1,
    title: 'پشتیبانی فنی پلتفرم',
    description: 'درخواست راهنمایی در مورد دیزاین سیستم پلتفرم',
    image: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100&auto=format&fit=crop&q=80',
    telegram_bot_active: true,
    bale_bot_active: false,
    telegram_connections: [1] as number[],
    bale_connections: [] as number[]
  }
  logEvent('Topic: Simulator Data Reset', {})
}

// Platform Navigation simulation variables
const simulatorActiveTab = ref<'home' | 'profile'>('home')

const handleNavChange = (tab: 'home' | 'profile') => {
  logEvent('Nav: Active Tab Changed', { tab })
}

// Topic Card simulation state
const mockTopics = ref([
  { id: 1, title: 'گروه توسعه تفکر', description: 'شایان: طرح هدر پلتفرم را اصلاح کردم و انیمیشن بک به درستی کار می‌کند.', unreadCount: 5, time: '۱۲:۳۰', labels: ['فناوری', 'توسعه'], pinned: true },
  { id: 2, title: 'کانال عمومی اخبار پلتفرم', description: 'اطلاعیه: نسخه بتای آزمایشگاه تست شبیه‌سازها هم‌اکنون به صورت آزمایشی در دسترس قرار گرفت.', unreadCount: 12, time: '۱۰:۱۵', labels: ['اخبار', 'تفکر'], pinned: false },
  { id: 3, title: 'تیم طراحی رابط کاربری', description: 'امیر: لطفا آیکون‌ها و رنگ‌های شیشه‌ای را مجدداً هماهنگ کنید.', unreadCount: 0, time: 'دیروز', labels: ['طراحی', 'UI/UX'], pinned: false }
])

const handleTopicClick = (topicId: number) => {
  const topic = mockTopics.value.find(t => t.id === topicId)
  if (topic) {
    topic.unreadCount = 0 // clear unread count on click
    logEvent('Topic: Clicked Card (Marked Read)', { id: topicId, title: topic.title })
  }
}

const addSimulatedMessage = () => {
  // Add a random unread count to a topic
  const randomIndex = Math.floor(Math.random() * mockTopics.value.length)
  const topic = mockTopics.value[randomIndex]
  if (topic) {
    topic.unreadCount += 1
    topic.time = new Date().toTimeString().split(' ')[0]?.slice(0, 5) ?? 'حالا'
    topic.description = 'پیام آزمایشی جدید در ثانیه جاری ارسال شد.'
    logEvent('Topic: Simulated Message Received', { title: topic.title })
  }
}

// Minimal Search simulation variables
const simulatorSearchQuery = ref('')
const simulatorSearchExpanded = ref(false)

const handleSearchEvent = (event: string, payload: any) => {
  logEvent(`Search: ${event}`, payload)
}

const filteredTopics = computed(() => {
  if (!simulatorSearchQuery.value.trim()) {
    return mockTopics.value
  }
  const searchLower = simulatorSearchQuery.value.toLowerCase()
  return mockTopics.value.filter(t => 
    t.title.toLowerCase().includes(searchLower) || 
    t.description.toLowerCase().includes(searchLower) ||
    t.labels.some(l => l.toLowerCase().includes(searchLower))
  )
})

// Profile menu options simulation variables
const simulatorSettingsBadge = ref('')
const simulatorConnectionsBadge = ref('۳ فعال')
const simulatorAiBadge = ref('جدید')

const handleProfileOptionClick = (option: string) => {
  logEvent('Profile Option Clicked', { option })
}

// ProfileCard simulation variables
const simulatorProfileCardName = ref('شایان مهدوی')
const simulatorProfileCardPhone = ref('۰۹۱۲۳۴۵۶۷۸۹')
const simulatorProfileCardStatus = ref<'success' | 'warning' | 'info' | 'muted'>('success')

const handleProfileCardEdit = () => {
  logEvent('ProfileCard: Edit Button Clicked', { name: simulatorProfileCardName.value })
}

// Post components simulation data and handlers
interface Comment {
  id: string | number
  authorName: string
  authorAvatar?: string
  text: string
  timestamp: string
}

interface Post {
  id: number
  author: {
    name: string
    avatarUrl: string
    role: string
  }
  type: 'text' | 'image' | 'video' | 'audio'
  content?: string
  mediaUrl?: string
  posterUrl?: string
  duration?: string
  timestamp: string
  likesCount: number
  liked: boolean
  comments: Comment[]
  reactions?: PostReaction[]
}

const initialPosts: Post[] = [
  {
    id: 1,
    author: {
      name: 'سارا احمدی',
      avatarUrl: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100&auto=format&fit=crop&q=80',
      role: 'مدیر محصول تفکر'
    },
    type: 'text' as const,
    content: 'سلام اعضای تیم! طرح اولیه بخش پست‌ها و کامپوننت‌های شیشه‌ای را آماده کردم. لطفاً نظرات خودتان را درباره ساختار جدید در بخش دیدگاه‌ها بنویسید.',
    timestamp: '۱۴:۳۲ - ۲۷ خرداد ۱۴۰۵',
    likesCount: 12,
    liked: true,
    comments: [
      { id: 101, authorName: 'بابک رضایی', text: 'بسیار عالی و مینیمال شده، خسته نباشید!', timestamp: '۱۴:۳۵' },
      { id: 102, authorName: 'نسیم مرادی', text: 'آیا افکت بلور در پس‌زمینه‌های متحرک هم به خوبی کار می‌کند؟', timestamp: '۱۴:۴۰' }
    ],
    reactions: [
      { emoji: '👍', count: 4, reacted: true },
      { emoji: '❤️', count: 2, reacted: false }
    ]
  },
  {
    id: 2,
    author: {
      name: 'سامان فتوحی',
      avatarUrl: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&auto=format&fit=crop&q=80',
      role: 'طراح ارشد رابط کاربری'
    },
    type: 'image' as const,
    content: 'تصویر پس‌زمینه جدیدی که برای هدر پلتفرم طراحی کردم. نظرتون چیه؟ شفافیت کارت‌های روی این تصویر خیلی قشنگ دیده میشه.',
    mediaUrl: 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=800&auto=format&fit=crop&q=80',
    timestamp: '۱۲:۱۵ - ۲۷ خرداد ۱۴۰۵',
    likesCount: 28,
    liked: false,
    comments: [
      { id: 201, authorName: 'سارا احمدی', text: 'رنگ‌هاش فوق‌العاده است، هماهنگی خوبی با حالت تیره داره.', timestamp: '۱۲:۲۰' }
    ],
    reactions: [
      { emoji: '🔥', count: 8, reacted: true },
      { emoji: '💯', count: 3, reacted: false }
    ]
  },
  {
    id: 3,
    author: {
      name: 'علی کریمی',
      avatarUrl: '',
      role: 'برنامه‌نویس فرانت‌اند'
    },
    type: 'video' as const,
    content: 'ویدیو تست کارکرد ترنزیشن‌های انیمیشن بازگشت هدر تفکر در نسخه موبایل. حتماً چک کنید.',
    mediaUrl: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4',
    posterUrl: 'https://images.unsplash.com/photo-1579546929518-9e396f3cc809?w=800&auto=format&fit=crop&q=80',
    timestamp: '۱۰:۰۵ - ۲۷ خرداد ۱۴۰۵',
    likesCount: 9,
    liked: false,
    comments: [],
    reactions: [
      { emoji: '👀', count: 3, reacted: false }
    ]
  },
  {
    id: 4,
    author: {
      name: 'پژمان مرادی',
      avatarUrl: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=100&auto=format&fit=crop&q=80',
      role: 'طراح تجربه کاربری'
    },
    type: 'audio' as const,
    content: 'توضیحات صوتی در خصوص سناریوی پیام‌های یک‌طرفه در تایپک‌ها و نحوه پیاده‌سازی بخش دیدگاه‌ها روی هر کارت پست.',
    mediaUrl: 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3',
    duration: '06:12',
    timestamp: '۰۹:۳۰ - ۲۷ خرداد ۱۴۰۵',
    likesCount: 15,
    liked: true,
    comments: [
      { id: 401, authorName: 'علی کریمی', text: 'فایل صوتی کاملاً واضح بود. ممنون.', timestamp: '۰۹:۴۵' }
    ],
    reactions: [
      { emoji: '👏', count: 5, reacted: false }
    ]
  }
]

const mockPosts = ref([...initialPosts])

const handlePostLike = (postId: number | string, liked: boolean) => {
  const post = mockPosts.value.find(p => p.id === postId)
  if (post) {
    post.liked = liked
    post.likesCount = liked ? (post.likesCount ?? 0) + 1 : (post.likesCount ?? 1) - 1
  }
  logEvent('Post: Like Toggle', { postId, liked })
}

const handlePostShare = (postId: number | string) => {
  logEvent('Post: Share Clicked', { postId })
}

const handlePostCommentAdded = (postId: number | string, comment: Comment) => {
  const post = mockPosts.value.find(p => p.id === postId)
  if (post) {
    if (!post.comments) post.comments = []
    post.comments.push(comment)
  }
  logEvent('Post: Comment Added', { postId, comment })
}

const handlePostReact = (postId: number | string, emoji: string, currentReactions: PostReaction[]) => {
  const post = mockPosts.value.find(p => p.id === postId)
  if (post) {
    post.reactions = currentReactions
  }
  logEvent('Post: Reacted', { postId, emoji, currentReactions })
}

const handlePostEdit = (postId: number | string) => {
  const post = mockPosts.value.find(p => p.id === postId)
  if (post) {
    const newContent = prompt('متن جدید پست را وارد کنید:', post.content || '')
    if (newContent !== null) {
      post.content = newContent
      logEvent('Post: Edited', { postId, newContent })
    }
  }
}

const handlePostDelete = (postId: number | string) => {
  const index = mockPosts.value.findIndex(p => p.id === postId)
  if (index !== -1) {
    mockPosts.value.splice(index, 1)
    logEvent('Post: Deleted', { postId })
  }
}

const handlePostPin = (postId: number | string) => {
  logEvent('Post: Pinned', { postId })
}

const handlePostCopy = (postId: number | string) => {
  logEvent('Post: Text Copied to Clipboard', { postId })
}

const simulateNewPost = () => {
  const newPost = {
    id: Date.now(),
    author: {
      name: 'شایان مهدوی',
      avatarUrl: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=100&auto=format&fit=crop&q=80',
      role: 'توسعه‌دهنده فرانت‌اند'
    },
    type: 'text' as const,
    content: 'این یک پست جدید شبیه‌سازی شده در تایپک است. برای مشاهده افکت شیشه‌ای و فاصله ۸ پیکسلی پست‌ها، اسکرول کنید.',
    timestamp: 'هم‌اکنون',
    likesCount: 0,
    liked: false,
    comments: [],
    reactions: []
  }
  mockPosts.value.unshift(newPost)
  logEvent('Post: Simulated New Post Received', newPost)
}

const resetPosts = () => {
  mockPosts.value = JSON.parse(JSON.stringify(initialPosts))
  logEvent('Post: Feed Reset to Default', {})
}
</script>

<template>
  <div class="w-full flex justify-center text-right" dir="rtl">
    <div class="w-full max-w-6xl py-10 px-6 flex flex-col gap-10">
      
      <!-- Header -->
      <div class="border-b border-border/60 pb-6 flex flex-col md:flex-row md:items-end md:justify-between gap-6 w-full text-right">
        <div class="flex flex-col gap-2">
          <div class="flex items-center gap-2 text-primary justify-start">
            <FlaskConicalIcon class="size-4" />
            <span class="text-[10px] font-bold uppercase tracking-wider text-primary/80">محیط ۳ - آزمایشگاه تست کامپوننت</span>
          </div>
          <h1 class="text-xl font-extrabold tracking-tight text-foreground">شبیه‌ساز و زمین بازی (Playground)</h1>
          <p class="text-muted-foreground text-xs mt-0.5">تست رفتار ریسپانسیو و کنترل کامل وضعیت‌های مختلف کامپوننت‌های بزرگتر.</p>
        </div>
        
        <!-- Reset button -->
        <Button variant="outline" size="sm" @click="resetData" class="self-start md:self-auto flex items-center cursor-pointer" data-icon="inline-start">
          <RefreshCwIcon />
          ریست شبیه‌ساز
        </Button>
      </div>

      <!-- Playground Workspace Panel -->
      <div class="grid grid-cols-1 lg:grid-cols-4 gap-10 w-full">
        
        <!-- Control Panel (Sidebar) -->
        <div class="lg:col-span-1 bg-card/30 border border-border/60 rounded-lg p-6 shadow-xs flex flex-col gap-6 self-start">
          <h2 class="text-xs font-extrabold border-r-4 border-primary pr-2 leading-none text-foreground/90">تنظیمات شبیه‌ساز</h2>

          <!-- Component Selection -->
          <div class="flex flex-col gap-3">
            <Label class="text-[11px] font-semibold text-muted-foreground block">انتخاب کامپوننت:</Label>
            <div class="flex flex-col gap-1.5">
              <button 
                @click="handleComponentChange('profile')"
                :class="[
                  'w-full text-right px-3 py-2.5 text-xs font-medium rounded-lg border transition-all flex items-center justify-between cursor-pointer',
                  currentComponent === 'profile' 
                    ? 'bg-primary/5 text-primary border-primary/30 font-bold' 
                    : 'bg-background/20 border-border/40 text-foreground hover:bg-muted/40'
                ]"
              >
                <span class="flex items-center gap-2">
                  <UserIcon class="size-3.5" />
                  کارت مشخصات کاربر
                </span>
                <CheckCircle2Icon v-if="currentComponent === 'profile'" class="size-3.5 text-primary" />
              </button>
              <button 
                @click="handleComponentChange('login')"
                :class="[
                  'w-full text-right px-3 py-2.5 text-xs font-medium rounded-lg border transition-all flex items-center justify-between cursor-pointer',
                  currentComponent === 'login' 
                    ? 'bg-primary/5 text-primary border-primary/30 font-bold' 
                    : 'bg-background/20 border-border/40 text-foreground hover:bg-muted/40'
                ]"
              >
                <span class="flex items-center gap-2">
                  <KeyRoundIcon class="size-3.5" />
                  کارت ورود (تفکر)
                </span>
                <CheckCircle2Icon v-if="currentComponent === 'login'" class="size-3.5 text-primary" />
              </button>
              <button 
                @click="handleComponentChange('header')"
                :class="[
                  'w-full text-right px-3 py-2.5 text-xs font-medium rounded-lg border transition-all flex items-center justify-between cursor-pointer',
                  currentComponent === 'header' 
                    ? 'bg-primary/5 text-primary border-primary/30 font-bold' 
                    : 'bg-background/20 border-border/40 text-foreground hover:bg-muted/40'
                ]"
              >
                <span class="flex items-center gap-2">
                  <SmartphoneIcon class="size-3.5" />
                  هدر پلتفرم (تفکر)
                </span>
                <CheckCircle2Icon v-if="currentComponent === 'header'" class="size-3.5 text-primary" />
              </button>
              <button 
                @click="handleComponentChange('nav')"
                :class="[
                  'w-full text-right px-3 py-2.5 text-xs font-medium rounded-lg border transition-all flex items-center justify-between cursor-pointer',
                  currentComponent === 'nav' 
                    ? 'bg-primary/5 text-primary border-primary/30 font-bold' 
                    : 'bg-background/20 border-border/40 text-foreground hover:bg-muted/40'
                ]"
              >
                <span class="flex items-center gap-2">
                  <HomeIcon class="size-3.5" />
                  منوی نویگیشن شناور
                </span>
                <CheckCircle2Icon v-if="currentComponent === 'nav'" class="size-3.5 text-primary" />
              </button>
              <button 
                @click="handleComponentChange('topic')"
                :class="[
                  'w-full text-right px-3 py-2.5 text-xs font-medium rounded-lg border transition-all flex items-center justify-between cursor-pointer',
                  currentComponent === 'topic' 
                    ? 'bg-primary/5 text-primary border-primary/30 font-bold' 
                    : 'bg-background/20 border-border/40 text-foreground hover:bg-muted/40'
                ]"
              >
                <span class="flex items-center gap-2">
                  <TerminalIcon class="size-3.5" />
                  کارت‌های تاپیک (لیست تلگرام)
                </span>
                <CheckCircle2Icon v-if="currentComponent === 'topic'" class="size-3.5 text-primary" />
              </button>
              <button 
                @click="handleComponentChange('search')"
                :class="[
                  'w-full text-right px-3 py-2.5 text-xs font-medium rounded-lg border transition-all flex items-center justify-between cursor-pointer',
                  currentComponent === 'search' 
                    ? 'bg-primary/5 text-primary border-primary/30 font-bold' 
                    : 'bg-background/20 border-border/40 text-foreground hover:bg-muted/40'
                ]"
              >
                <span class="flex items-center gap-2">
                  <SearchIcon class="size-3.5" />
                  جستجوی ادغام‌شده در هدر
                </span>
                <CheckCircle2Icon v-if="currentComponent === 'search'" class="size-3.5 text-primary" />
              </button>
              <button 
                @click="handleComponentChange('profile-option')"
                :class="[
                  'w-full text-right px-3 py-2.5 text-xs font-medium rounded-lg border transition-all flex items-center justify-between cursor-pointer',
                  currentComponent === 'profile-option' 
                    ? 'bg-primary/5 text-primary border-primary/30 font-bold' 
                    : 'bg-background/20 border-border/40 text-foreground hover:bg-muted/40'
                ]"
              >
                <span class="flex items-center gap-2">
                  <UserIcon class="size-3.5" />
                  گزینه‌های پروفایل (منوی افقی)
                </span>
                <CheckCircle2Icon v-if="currentComponent === 'profile-option'" class="size-3.5 text-primary" />
              </button>
              <button 
                @click="handleComponentChange('profile-card-header')"
                :class="[
                  'w-full text-right px-3 py-2.5 text-xs font-medium rounded-lg border transition-all flex items-center justify-between cursor-pointer',
                  currentComponent === 'profile-card-header' 
                    ? 'bg-primary/5 text-primary border-primary/30 font-bold' 
                    : 'bg-background/20 border-border/40 text-foreground hover:bg-muted/40'
                ]"
              >
                <span class="flex items-center gap-2">
                  <UserIcon class="size-3.5" />
                  کارت پروفایل (جدید)
                </span>
                <CheckCircle2Icon v-if="currentComponent === 'profile-card-header'" class="size-3.5 text-primary" />
              </button>
              <button 
                @click="handleComponentChange('post')"
                :class="[
                  'w-full text-right px-3 py-2.5 text-xs font-medium rounded-lg border transition-all flex items-center justify-between cursor-pointer',
                  currentComponent === 'post' 
                    ? 'bg-primary/5 text-primary border-primary/30 font-bold' 
                    : 'bg-background/20 border-border/40 text-foreground hover:bg-muted/40'
                ]"
              >
                <span class="flex items-center gap-2">
                  <MessageCircleIcon class="size-3.5" />
                  پست‌های تایپک (تلگرام)
                </span>
                <CheckCircle2Icon v-if="currentComponent === 'post'" class="size-3.5 text-primary" />
              </button>
              <button 
                @click="handleComponentChange('create-topic-modal')"
                :class="[
                  'w-full text-right px-3 py-2.5 text-xs font-medium rounded-lg border transition-all flex items-center justify-between cursor-pointer',
                  currentComponent === 'create-topic-modal' 
                    ? 'bg-primary/5 text-primary border-primary/30 font-bold' 
                    : 'bg-background/20 border-border/40 text-foreground hover:bg-muted/40'
                ]"
              >
                <span class="flex items-center gap-2">
                  <PlusIcon class="size-3.5 text-primary" />
                  مودال ساخت تاپیک (جدید)
                </span>
                <CheckCircle2Icon v-if="currentComponent === 'create-topic-modal'" class="size-3.5 text-primary" />
              </button>
              <button 
                @click="handleComponentChange('bot-connection')"
                :class="[
                  'w-full text-right px-3 py-2.5 text-xs font-medium rounded-lg border transition-all flex items-center justify-between cursor-pointer',
                  currentComponent === 'bot-connection' 
                    ? 'bg-primary/5 text-primary border-primary/30 font-bold' 
                    : 'bg-background/20 border-border/40 text-foreground hover:bg-muted/40'
                ]"
              >
                <span class="flex items-center gap-2">
                  <LinkIcon class="size-3.5 text-primary" />
                  کارت اتصال بات (جدید)
                </span>
                <CheckCircle2Icon v-if="currentComponent === 'bot-connection'" class="size-3.5 text-primary" />
              </button>
              <button 
                @click="handleComponentChange('topic-input')"
                :class="[
                  'w-full text-right px-3 py-2.5 text-xs font-medium rounded-lg border transition-all flex items-center justify-between cursor-pointer',
                  currentComponent === 'topic-input' 
                    ? 'bg-primary/5 text-primary border-primary/30 font-bold' 
                    : 'bg-background/20 border-border/40 text-foreground hover:bg-muted/40'
                ]"
              >
                <span class="flex items-center gap-2">
                  <MessageCircleIcon class="size-3.5 text-primary" />
                  ورودی پیام تایپک (جدید)
                </span>
                <CheckCircle2Icon v-if="currentComponent === 'topic-input'" class="size-3.5 text-primary" />
              </button>
              <button 
                @click="handleComponentChange('topic-edit')"
                :class="[
                  'w-full text-right px-3 py-2.5 text-xs font-medium rounded-lg border transition-all flex items-center justify-between cursor-pointer',
                  currentComponent === 'topic-edit' 
                    ? 'bg-primary/5 text-primary border-primary/30 font-bold' 
                    : 'bg-background/20 border-border/40 text-foreground hover:bg-muted/40'
                ]"
              >
                <span class="flex items-center gap-2">
                  <PencilIcon class="size-3.5 text-primary" />
                  صفحه ویرایش تاپیک (جدید)
                </span>
                <CheckCircle2Icon v-if="currentComponent === 'topic-edit'" class="size-3.5 text-primary" />
              </button>
              <button 
                @click="handleComponentChange('topic-connections')"
                :class="[
                  'w-full text-right px-3 py-2.5 text-xs font-medium rounded-lg border transition-all flex items-center justify-between cursor-pointer',
                  currentComponent === 'topic-connections' 
                    ? 'bg-primary/5 text-primary border-primary/30 font-bold' 
                    : 'bg-background/20 border-border/40 text-foreground hover:bg-muted/40'
                ]"
              >
                <span class="flex items-center gap-2">
                  <LinkIcon class="size-3.5 text-primary" />
                  اتصالات اختصاصی تاپیک (جدید)
                </span>
                <CheckCircle2Icon v-if="currentComponent === 'topic-connections'" class="size-3.5 text-primary" />
              </button>
            </div>
          </div>

          <!-- Viewport width controls -->
          <div class="flex flex-col gap-3">
            <Label class="text-[11px] font-semibold text-muted-foreground block">اندازه پنجره نمایشگر:</Label>
            <div class="grid grid-cols-3 gap-1.5 bg-muted/60 p-1 rounded-lg border border-border/40">
              <button 
                @click="viewportWidth = '375px'"
                :class="[
                  'flex flex-col items-center justify-center py-2 rounded-md text-[10px] font-medium transition-colors outline-none cursor-pointer',
                  viewportWidth === '375px' ? 'bg-background text-foreground shadow-xs font-bold' : 'text-muted-foreground hover:text-foreground'
                ]"
              >
                <SmartphoneIcon class="size-4 mb-1" />
                موبایل
              </button>
              <button 
                @click="viewportWidth = '768px'"
                :class="[
                  'flex flex-col items-center justify-center py-2 rounded-md text-[10px] font-medium transition-colors outline-none cursor-pointer',
                  viewportWidth === '768px' ? 'bg-background text-foreground shadow-xs font-bold' : 'text-muted-foreground hover:text-foreground'
                ]"
              >
                <TabletIcon class="size-4 mb-1" />
                تبلت
              </button>
              <button 
                @click="viewportWidth = '100%'"
                :class="[
                  'flex flex-col items-center justify-center py-2 rounded-md text-[10px] font-medium transition-colors outline-none cursor-pointer',
                  viewportWidth === '100%' ? 'bg-background text-foreground shadow-xs font-bold' : 'text-muted-foreground hover:text-foreground'
                ]"
              >
                <LaptopIcon class="size-4 mb-1" />
                دسکتاپ
              </button>
            </div>
          </div>

          <!-- Viewport background controls for glassmorphism testing -->
          <div class="flex flex-col gap-2.5">
            <Label class="text-[11px] font-semibold text-muted-foreground block">پس‌زمینه شبیه‌ساز (تست بلور):</Label>
            <div class="grid grid-cols-2 gap-1.5">
              <button 
                @click="sandboxBg = 'default'; logEvent('Sandbox Background: Default', {})"
                :class="[
                  'px-2 py-1.5 rounded-lg text-[9.5px] font-semibold border text-center transition-all cursor-pointer outline-none',
                  sandboxBg === 'default'
                    ? 'bg-primary/5 text-primary border-primary/30 font-bold shadow-xs'
                    : 'bg-background/20 border-border/40 text-foreground hover:bg-muted/40'
                ]"
              >
                ساده (پیش‌فرض)
              </button>
              <button 
                @click="sandboxBg = 'gradient'; logEvent('Sandbox Background: Colorful Gradient', {})"
                :class="[
                  'px-2 py-1.5 rounded-lg text-[9.5px] font-semibold border text-center transition-all cursor-pointer outline-none',
                  sandboxBg === 'gradient'
                    ? 'bg-primary/5 text-primary border-primary/30 font-bold shadow-xs'
                    : 'bg-background/20 border-border/40 text-foreground hover:bg-muted/40'
                ]"
              >
                گرادینت رنگی
              </button>
              <button 
                @click="sandboxBg = 'grid'; logEvent('Sandbox Background: Figma Grid', {})"
                :class="[
                  'px-2 py-1.5 rounded-lg text-[9.5px] font-semibold border text-center transition-all cursor-pointer outline-none',
                  sandboxBg === 'grid'
                    ? 'bg-primary/5 text-primary border-primary/30 font-bold shadow-xs'
                    : 'bg-background/20 border-border/40 text-foreground hover:bg-muted/40'
                ]"
              >
                پترن شبکه‌ای (Grid)
              </button>
              <button 
                @click="sandboxBg = 'image'; logEvent('Sandbox Background: Abstract Canvas', {})"
                :class="[
                  'px-2 py-1.5 rounded-lg text-[9.5px] font-semibold border text-center transition-all cursor-pointer outline-none',
                  sandboxBg === 'image'
                    ? 'bg-primary/5 text-primary border-primary/30 font-bold shadow-xs'
                    : 'bg-background/20 border-border/40 text-foreground hover:bg-muted/40'
                ]"
              >
                تصویر منظره
              </button>
            </div>
          </div>

          <!-- Component state controls -->
          <div class="flex flex-col gap-2.5">
            <Label class="text-[11px] font-semibold text-muted-foreground block">وضعیت کامپوننت:</Label>
            <div class="flex flex-col gap-1.5">
              <button 
                v-for="state in availableStates"
                :key="state"
                @click="activeState = state"
                :class="[
                  'w-full text-right px-3 py-2.5 text-xs font-medium rounded-lg border transition-all flex items-center justify-between cursor-pointer',
                  activeState === state 
                    ? 'bg-primary/5 text-primary border-primary/30 font-bold' 
                    : 'bg-background/20 border-border/40 text-foreground hover:bg-muted/40'
                ]"
              >
                <span>
                  {{ 
                    state === 'idle' ? 'حالت فعال (Idle)' :
                    state === 'loading' ? 'بارگذاری (Loading)' :
                    state === 'error' ? 'نمایش خطا (Error)' : 
                    state === 'empty' ? 'کامپوننت خالی (Empty)' : 'ورود موفق (Success)' 
                  }}
                </span>
                <span class="size-2 rounded-full" 
                  :class="[
                    state === 'idle' ? 'bg-green-500' :
                    state === 'loading' ? 'bg-amber-500 animate-pulse' :
                    state === 'error' ? 'bg-destructive' : 
                    state === 'success' ? 'bg-emerald-500' : 'bg-muted-foreground'
                  ]" 
                />
              </button>
            </div>
          </div>

          <!-- Header Specific Controls -->
          <div v-if="currentComponent === 'header'" class="flex flex-col gap-3 border-t border-border/40 pt-4 mt-1">
            <Label class="text-[11px] font-semibold text-muted-foreground block">موقعیت صفحه فعال:</Label>
            <div class="flex flex-col gap-1.5">
              <button 
                @click="simulatorIsInnerPage = false"
                :class="[
                  'w-full text-right px-3 py-2 text-xs font-medium rounded-lg border transition-all flex items-center justify-between cursor-pointer',
                  !simulatorIsInnerPage 
                    ? 'bg-primary/5 text-primary border-primary/30 font-bold' 
                    : 'bg-background/20 border-border/40 text-foreground hover:bg-muted/40'
                ]"
              >
                <span>صفحه اصلی (تفکر)</span>
                <Badge variant="secondary" class="text-[9px] px-1.5 h-4 text-muted-foreground">Home</Badge>
              </button>
              <button 
                @click="simulatorIsInnerPage = true"
                :class="[
                  'w-full text-right px-3 py-2 text-xs font-medium rounded-lg border transition-all flex items-center justify-between cursor-pointer',
                  simulatorIsInnerPage 
                    ? 'bg-primary/5 text-primary border-primary/30 font-bold' 
                    : 'bg-background/20 border-border/40 text-foreground hover:bg-muted/40'
                ]"
              >
                <span>صفحه داخلی (بک فعال)</span>
                <Badge variant="secondary" class="text-[9px] px-1.5 h-4 text-muted-foreground">Inner</Badge>
              </button>
            </div>
          </div>

          <!-- Navigation Specific Controls -->
          <div v-if="currentComponent === 'nav'" class="flex flex-col gap-3 border-t border-border/40 pt-4 mt-1">
            <Label class="text-[11px] font-semibold text-muted-foreground block">شبیه‌سازی منوی فعال:</Label>
            <div class="flex flex-col gap-1.5">
              <button 
                @click="simulatorActiveTab = 'home'; logEvent('Nav: Toggled via Sidebar', { tab: 'home' })"
                :class="[
                  'w-full text-right px-3 py-2 text-xs font-medium rounded-lg border transition-all flex items-center justify-between cursor-pointer',
                  simulatorActiveTab === 'home' 
                    ? 'bg-primary/5 text-primary border-primary/30 font-bold' 
                    : 'bg-background/20 border-border/40 text-foreground hover:bg-muted/40'
                ]"
              >
                <span>صفحه خانه (خانه)</span>
                <HomeIcon class="size-3.5 text-muted-foreground" />
              </button>
              <button 
                @click="simulatorActiveTab = 'profile'; logEvent('Nav: Toggled via Sidebar', { tab: 'profile' })"
                :class="[
                  'w-full text-right px-3 py-2 text-xs font-medium rounded-lg border transition-all flex items-center justify-between cursor-pointer',
                  simulatorActiveTab === 'profile' 
                    ? 'bg-primary/5 text-primary border-primary/30 font-bold' 
                    : 'bg-background/20 border-border/40 text-foreground hover:bg-muted/40'
                ]"
              >
                <span>صفحه پروفایل (کاربر)</span>
                <UserIcon class="size-3.5 text-muted-foreground" />
              </button>
            </div>
          </div>

          <!-- Topic Specific Controls -->
          <div v-if="currentComponent === 'topic'" class="flex flex-col gap-3 border-t border-border/40 pt-4 mt-1">
            <Label class="text-[11px] font-semibold text-muted-foreground block">شبیه‌سازی پیام‌ها:</Label>
            <div class="flex flex-col gap-1.5">
              <Button 
                size="sm" 
                @click="addSimulatedMessage"
                class="w-full text-xs font-semibold cursor-pointer"
              >
                شبیه‌سازی دریافت پیام جدید
              </Button>
              <Button 
                size="sm" 
                variant="outline"
                @click="mockTopics.forEach(t => t.unreadCount = 0); logEvent('Topic: All Marked as Read', {})"
                class="w-full text-xs font-semibold cursor-pointer"
              >
                خوانده شدن همه کارت‌ها
              </Button>
            </div>
          </div>

          <!-- Search Specific Controls -->
          <div v-if="currentComponent === 'search'" class="flex flex-col gap-3 border-t border-border/40 pt-4 mt-1">
            <Label class="text-[11px] font-semibold text-muted-foreground block">شبیه‌سازی وضعیت جستجو:</Label>
            <div class="flex flex-col gap-1.5">
              <Button 
                size="sm" 
                variant="outline"
                @click="simulatorSearchQuery = 'توسعه'; logEvent('Search: Force Query = توسعه', {})"
                class="w-full text-xs font-semibold cursor-pointer"
              >
                جستجوی کلمه «توسعه»
              </Button>
              <Button 
                size="sm" 
                variant="outline"
                @click="simulatorSearchQuery = ''; logEvent('Search: Query Cleared via Sandbox', {})"
                class="w-full text-xs font-semibold cursor-pointer"
              >
                پاک کردن متن جستجو
              </Button>
            </div>
          </div>

          <!-- Profile Option Specific Controls -->
          <div v-if="currentComponent === 'profile-option'" class="flex flex-col gap-3 border-t border-border/40 pt-4 mt-1">
            <Label class="text-[11px] font-semibold text-muted-foreground block">شبیه‌سازی نشان‌گر گزینه‌ها:</Label>
            <div class="flex flex-col gap-1.5">
              <button 
                @click="simulatorSettingsBadge = simulatorSettingsBadge ? '' : 'بروزرسانی'"
                class="w-full text-right px-3 py-2 text-xs font-medium rounded-lg border transition-all flex items-center justify-between bg-background/20 border-border/40 text-foreground hover:bg-muted/40 cursor-pointer"
              >
                <span>نشان‌گر تنظیمات (Settings)</span>
                <Badge variant="secondary" class="text-[9px] px-1.5 h-4 text-muted-foreground">
                  {{ simulatorSettingsBadge || 'بدون نشان‌گر' }}
                </Badge>
              </button>
              <button 
                @click="simulatorConnectionsBadge = simulatorConnectionsBadge ? '' : '۳ فعال'"
                class="w-full text-right px-3 py-2 text-xs font-medium rounded-lg border transition-all flex items-center justify-between bg-background/20 border-border/40 text-foreground hover:bg-muted/40 cursor-pointer"
              >
                <span>نشان‌گر اتصال‌ها (Connections)</span>
                <Badge variant="secondary" class="text-[9px] px-1.5 h-4 text-muted-foreground">
                  {{ simulatorConnectionsBadge || 'بدون نشان‌گر' }}
                </Badge>
              </button>
              <button 
                @click="simulatorAiBadge = simulatorAiBadge ? '' : 'جدید'"
                class="w-full text-right px-3 py-2 text-xs font-medium rounded-lg border transition-all flex items-center justify-between bg-background/20 border-border/40 text-foreground hover:bg-muted/40 cursor-pointer"
              >
                <span>نشان‌گر هوش مصنوعی (AI)</span>
                <Badge variant="secondary" class="text-[9px] px-1.5 h-4 text-muted-foreground">
                  {{ simulatorAiBadge || 'بدون نشان‌گر' }}
                </Badge>
              </button>
            </div>
          </div>

          <!-- Profile Card Specific Controls -->
          <div v-if="currentComponent === 'profile-card-header'" class="flex flex-col gap-3 border-t border-border/40 pt-4 mt-1">
            <Label class="text-[11px] font-semibold text-muted-foreground block">تنظیمات کارت پروفایل:</Label>
            <div class="flex flex-col gap-3">
              <div class="flex flex-col gap-1">
                <Label class="text-[9.5px] text-muted-foreground">نام و نام خانوادگی:</Label>
                <Input v-model="simulatorProfileCardName" class="h-8 text-xs font-semibold" placeholder="نام کاربر" />
              </div>
              <div class="flex flex-col gap-1">
                <Label class="text-[9.5px] text-muted-foreground">وضعیت فعالیت:</Label>
                <div class="grid grid-cols-2 gap-1 bg-muted/65 p-1 rounded-lg border border-border/40">
                  <button 
                    v-for="statusType in (['success', 'warning', 'info', 'muted'] as const)"
                    :key="statusType"
                    @click="simulatorProfileCardStatus = statusType"
                    :class="[
                      'py-1 rounded text-[9px] font-bold transition-all cursor-pointer outline-none border border-transparent',
                      simulatorProfileCardStatus === statusType 
                        ? 'bg-background text-foreground shadow-xs font-black' 
                        : 'text-muted-foreground hover:text-foreground'
                    ]"
                  >
                    {{ 
                      statusType === 'success' ? 'فعال' :
                      statusType === 'warning' ? 'مشغول' :
                      statusType === 'info' ? 'غایب' : 'آفلاین'
                    }}
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- Post Specific Controls -->
          <div v-if="currentComponent === 'post'" class="flex flex-col gap-3 border-t border-border/40 pt-4 mt-1">
            <Label class="text-[11px] font-semibold text-muted-foreground block">شبیه‌سازی فید پست‌ها:</Label>
            <div class="flex flex-col gap-1.5">
              <Button 
                size="sm" 
                @click="simulateNewPost"
                class="w-full text-xs font-semibold cursor-pointer"
              >
                شبیه‌سازی دریافت پست جدید
              </Button>
              <Button 
                size="sm" 
                variant="outline"
                @click="resetPosts"
                class="w-full text-xs font-semibold cursor-pointer"
              >
                ریست کردن لیست پست‌ها
              </Button>
            </div>
          </div>

          <!-- Create Topic Modal Specific Controls -->
          <div v-if="currentComponent === 'create-topic-modal'" class="flex flex-col gap-3 border-t border-border/40 pt-4 mt-1">
            <Label class="text-[11px] font-semibold text-muted-foreground block">تنظیمات مودال ساخت تاپیک:</Label>
            <div class="flex flex-col gap-1.5">
              <Button 
                size="sm" 
                @click="simulatorIsModalOpen = true"
                class="w-full text-xs font-semibold cursor-pointer"
              >
                باز کردن مودال
              </Button>
            </div>
          </div>

          <!-- Bot Connection Specific Controls -->
          <div v-if="currentComponent === 'bot-connection'" class="flex flex-col gap-3 border-t border-border/40 pt-4 mt-1">
            <Label class="text-[11px] font-semibold text-muted-foreground block">تنظیمات کارت اتصال بات:</Label>
            
            <!-- Platform Toggle -->
            <div class="flex flex-col gap-1.5">
              <Label class="text-[9.5px] text-muted-foreground">پلتفرم:</Label>
              <div class="grid grid-cols-2 gap-1 bg-muted/65 p-1 rounded-lg border border-border/40">
                <button 
                  @click="simulatorBotPlatform = 'telegram'; logEvent('Bot: Platform set to Telegram', {})"
                  :class="[
                    'py-1 rounded text-[9px] font-bold transition-all cursor-pointer outline-none border border-transparent',
                    simulatorBotPlatform === 'telegram' 
                      ? 'bg-background text-foreground shadow-xs font-black' 
                      : 'text-muted-foreground hover:text-foreground'
                  ]"
                >
                  تلگرام
                </button>
                <button 
                  @click="simulatorBotPlatform = 'bale'; logEvent('Bot: Platform set to Bale', {})"
                  :class="[
                    'py-1 rounded text-[9px] font-bold transition-all cursor-pointer outline-none border border-transparent',
                    simulatorBotPlatform === 'bale' 
                      ? 'bg-background text-foreground shadow-xs font-black' 
                      : 'text-muted-foreground hover:text-foreground'
                  ]"
                >
                  بله
                </button>
              </div>
            </div>

            <!-- Connection Status Selector -->
            <div class="flex flex-col gap-1.5">
              <Label class="text-[9.5px] text-muted-foreground">وضعیت اتصال:</Label>
              <div class="grid grid-cols-2 gap-1 bg-muted/65 p-1 rounded-lg border border-border/40">
                <button 
                  v-for="st in (['disconnected', 'connecting', 'connected', 'conflict'] as const)"
                  :key="st"
                  @click="simulatorBotStatus = st; logEvent(`Bot: Status set to ${st}`, {})"
                  :class="[
                    'py-1 rounded text-[9px] font-bold transition-all cursor-pointer outline-none border border-transparent',
                    simulatorBotStatus === st 
                      ? 'bg-background text-foreground shadow-xs font-black' 
                      : 'text-muted-foreground/80 hover:text-foreground'
                  ]"
                >
                  {{ 
                    st === 'disconnected' ? 'غیرمتصل' :
                    st === 'connecting' ? 'درحال اتصال' :
                    st === 'connected' ? 'متصل' : 'تداخل'
                  }}
                </button>
              </div>
            </div>

            <!-- Simulated Event Actions -->
            <div class="flex flex-col gap-1.5 mt-2">
              <Button 
                size="sm" 
                variant="outline"
                @click="simulatorBotStatus = 'conflict'; logEvent('Bot: Simulated sudden disconnection error (conflict)', {})"
                class="w-full text-xs font-semibold text-amber-600 border-amber-550/20 hover:bg-amber-500/5 cursor-pointer"
              >
                شبیه‌سازی خطای تداخل
              </Button>
              <Button 
                size="sm" 
                variant="outline"
                @click="simulatorBotToken = '123456:conflict-token'; logEvent('Bot: Force set conflict token', {})"
                class="w-full text-xs font-semibold cursor-pointer"
              >
                تنظیم توکن تداخل‌ساز
              </Button>
            </div>
          </div>

          <!-- Topic Edit Specific Controls -->
          <div v-if="currentComponent === 'topic-edit'" class="flex flex-col gap-3 border-t border-border/40 pt-4 mt-1">
            <Label class="text-[11px] font-semibold text-muted-foreground block">تنظیمات شبیه‌ساز ویرایش تاپیک:</Label>
            <p class="text-[9.5px] text-muted-foreground leading-relaxed">
              با استفاده از فرم روبرو می‌توانید عنوان، توضیحات و تصویر تاپیک شبیه‌سازی شده را ویرایش کرده و ذخیره کنید. دکمه زیر مقادیر را ریست می‌کند:
            </p>
            <Button 
              size="sm" 
              variant="outline"
              @click="resetSimulatorTopicEdit"
              class="w-full text-xs font-semibold cursor-pointer"
            >
              بازنشانی مقادیر اولیه تاپیک
            </Button>
          </div>

          <!-- Topic Connections Specific Controls -->
          <div v-if="currentComponent === 'topic-connections'" class="flex flex-col gap-3 border-t border-border/40 pt-4 mt-1">
            <Label class="text-[11px] font-semibold text-muted-foreground block">تنظیمات شبیه‌ساز اتصالات:</Label>
            
            <div class="flex flex-col gap-1.5">
              <Label class="text-[9.5px] text-muted-foreground">وضعیت اتصال ربات تلگرام:</Label>
              <div class="grid grid-cols-2 gap-1 bg-muted/65 p-1 rounded-lg border border-border/40">
                <button 
                  @click="simulatorTelegramConnected = true; logEvent('Connections: Telegram Connected', {})"
                  :class="[
                    'py-1 rounded text-[9px] font-bold transition-all cursor-pointer outline-none border border-transparent',
                    simulatorTelegramConnected 
                      ? 'bg-background text-foreground shadow-xs font-black' 
                      : 'text-muted-foreground hover:text-foreground'
                  ]"
                >
                  متصل
                </button>
                <button 
                  @click="simulatorTelegramConnected = false; logEvent('Connections: Telegram Disconnected', {})"
                  :class="[
                    'py-1 rounded text-[9px] font-bold transition-all cursor-pointer outline-none border border-transparent',
                    !simulatorTelegramConnected 
                      ? 'bg-background text-foreground shadow-xs font-black' 
                      : 'text-muted-foreground hover:text-foreground'
                  ]"
                >
                  قطع اتصال
                </button>
              </div>
            </div>

            <div class="flex flex-col gap-1.5">
              <Label class="text-[9.5px] text-muted-foreground">وضعیت اتصال ربات بله:</Label>
              <div class="grid grid-cols-2 gap-1 bg-muted/65 p-1 rounded-lg border border-border/40">
                <button 
                  @click="simulatorBaleConnected = true; logEvent('Connections: Bale Connected', {})"
                  :class="[
                    'py-1 rounded text-[9px] font-bold transition-all cursor-pointer outline-none border border-transparent',
                    simulatorBaleConnected 
                      ? 'bg-background text-foreground shadow-xs font-black' 
                      : 'text-muted-foreground hover:text-foreground'
                  ]"
                >
                  متصل
                </button>
                <button 
                  @click="simulatorBaleConnected = false; logEvent('Connections: Bale Disconnected', {})"
                  :class="[
                    'py-1 rounded text-[9px] font-bold transition-all cursor-pointer outline-none border border-transparent',
                    !simulatorBaleConnected 
                      ? 'bg-background text-foreground shadow-xs font-black' 
                      : 'text-muted-foreground hover:text-foreground'
                  ]"
                >
                  قطع اتصال
                </button>
              </div>
            </div>
          </div>

          <!-- Topic Message Input Specific Controls -->
          <div v-if="currentComponent === 'topic-input'" class="flex flex-col gap-3 border-t border-border/40 pt-4 mt-1">
            <Label class="text-[11px] font-semibold text-muted-foreground block">تنظیمات ورودی پیام تایپک:</Label>
            
            <!-- Access/Disabled Toggle -->
            <div class="flex flex-col gap-1.5">
              <Label class="text-[9.5px] text-muted-foreground">سطح دسترسی نوشتن:</Label>
              <div class="grid grid-cols-2 gap-1 bg-muted/65 p-1 rounded-lg border border-border/40">
                <button 
                  @click="simulatorInputDisabled = false; logEvent('Input: Writing enabled', {})"
                  :class="[
                    'py-1 rounded text-[9px] font-bold transition-all cursor-pointer outline-none border border-transparent',
                    !simulatorInputDisabled 
                      ? 'bg-background text-foreground shadow-xs font-black' 
                      : 'text-muted-foreground hover:text-foreground'
                  ]"
                >
                  مجاز
                </button>
                <button 
                  @click="simulatorInputDisabled = true; logEvent('Input: Muted/Disabled', {})"
                  :class="[
                    'py-1 rounded text-[9px] font-bold transition-all cursor-pointer outline-none border border-transparent',
                    simulatorInputDisabled 
                      ? 'bg-background text-foreground shadow-xs font-black' 
                      : 'text-muted-foreground hover:text-foreground'
                  ]"
                >
                  غیرمجاز (Mute)
                </button>
              </div>
            </div>

            <!-- Simulated Attachment Insertions -->
            <div class="flex flex-col gap-1.5">
              <Label class="text-[9.5px] text-muted-foreground">شبیه‌سازی آپلود پیوست:</Label>
              <div class="grid grid-cols-2 gap-1.5">
                <Button 
                  size="sm" 
                  variant="outline"
                  @click="simulateAddAttachment('image')"
                  class="text-[10px] font-semibold py-1 h-7.5 cursor-pointer"
                >
                  افزودن تصویر
                </Button>
                <Button 
                  size="sm" 
                  variant="outline"
                  @click="simulateAddAttachment('video')"
                  class="text-[10px] font-semibold py-1 h-7.5 cursor-pointer"
                >
                  افزودن ویدیو
                </Button>
                <Button 
                  size="sm" 
                  variant="outline"
                  @click="simulateAddAttachment('audio')"
                  class="text-[10px] font-semibold py-1 h-7.5 cursor-pointer"
                >
                  افزودن صوت/صدا
                </Button>
                <Button 
                  size="sm" 
                  variant="outline"
                  @click="simulateAddAttachment('file')"
                  class="text-[10px] font-semibold py-1 h-7.5 cursor-pointer"
                >
                  افزودن سند/فایل
                </Button>
              </div>
            </div>

            <!-- Quick Text templates -->
            <div class="flex flex-col gap-1.5 mt-1">
              <Label class="text-[9.5px] text-muted-foreground">پر کردن متن قالب:</Label>
              <div class="flex flex-col gap-1">
                <button 
                  @click="simulatorInputText = 'این یک متن تستی طولانی برای بررسی تغییر ارتفاع فیلد متنی است. با نوشتن سطرهای بیشتر، ورودی پیام به صورت عمودی بزرگتر می‌شود.'; logEvent('Input: Filled template text', {})"
                  class="w-full text-right px-2 py-1 text-[9px] font-semibold rounded border border-border/40 hover:bg-muted/40 transition-colors truncate cursor-pointer bg-background/20 text-foreground"
                >
                  قالب متن طولانی
                </button>
                <button 
                  @click="simulatorInputText = ''; simulatorInputAttachments = []; logEvent('Input: Cleared everything', {})"
                  class="w-full text-right px-2 py-1 text-[9px] font-semibold rounded border border-destructive/20 hover:bg-destructive/5 text-destructive transition-colors cursor-pointer bg-background/20"
                >
                  پاک کردن همه داده‌ها
                </button>
              </div>
            </div>
          </div>

          <!-- Dev Note -->
          <div class="p-3 bg-muted/40 border border-border/40 rounded-lg text-[10px] leading-relaxed text-muted-foreground flex gap-2">
            <InfoIcon class="size-3.5 text-primary shrink-0 mt-0.5" />
            <span>تغییر وضعیت یا تغییر ابعاد، رفتار کامپوننت را در یک محدوده عایق و ایزوله شبیه‌ساز شبیه‌سازی می‌کند.</span>
          </div>
        </div>

        <!-- Main Testing Sandbox -->
        <div class="lg:col-span-3 flex flex-col gap-6">
          
          <!-- Live Preview Sandbox -->
          <div class="bg-card/30 border border-border/60 rounded-lg p-6 shadow-xs flex flex-col items-center">
            <div class="w-full flex justify-between items-center text-[10px] text-muted-foreground mb-4">
              <span class="font-mono">Width: {{ viewportWidth === '100%' ? 'Desktop (Auto)' : viewportWidth }}</span>
              <span class="flex items-center gap-1">
                <span class="size-1.5 rounded-full bg-emerald-500 animate-ping" />
                پیش‌نمایش زنده کامپوننت
              </span>
            </div>

            <!-- Viewport Frame Wrapper with Resizable styling -->
            <div 
              :style="{ maxWidth: viewportWidth }" 
              :class="[
                'w-full border border-dashed border-border rounded-lg transition-all duration-300 ease-in-out shadow-xs overflow-hidden flex justify-center',
                currentComponent === 'header' ? 'p-0' : 'p-8',
                sandboxBg === 'default' ? 'bg-sandbox-default' : '',
                sandboxBg === 'gradient' ? 'bg-sandbox-gradient' : '',
                sandboxBg === 'grid' ? 'bg-sandbox-grid' : '',
                sandboxBg === 'image' ? 'bg-sandbox-image' : ''
              ]"
            >
              <div :class="['w-full flex justify-center transition-all duration-300', (currentComponent === 'header' || currentComponent === 'post') ? 'max-w-none' : 'max-w-md']">
                <UserProfileCard 
                  v-if="currentComponent === 'profile'"
                  :state="activeState === 'success' ? 'idle' : activeState" 
                  :user="mockUser" 
                  @save="handleSave"
                  @status-toggle="handleStatusToggle"
                />
                <LoginCard
                  v-else-if="currentComponent === 'login'"
                  :state="activeState === 'empty' ? 'idle' : (activeState as any)"
                  @submitPhone="handleLoginPhoneSubmit"
                  @submitOtp="handleLoginOtpSubmit"
                  @stateChange="handleLoginStateChange"
                />

                <!-- PlatformHeader Preview (Directly in sandbox, full-width, dynamic back button) -->
                <div 
                  v-else-if="currentComponent === 'header'"
                  class="w-full flex flex-col"
                  dir="rtl"
                >
                  <!-- Header Component wrapper (No horizontal padding, flush to screen left/right borders) -->
                  <div class="px-4 py-3 w-full border-b border-border/40 bg-card/10">
                    <PlatformHeader
                      :isInnerPage="simulatorIsInnerPage"
                      :innerTitle="simulatorInnerTitle"
                      :loading="activeState === 'loading'"
                      :error="activeState === 'error'"
                      @back="handleHeaderBack"
                      @actionClick="handleHeaderAction"
                      @edit-topic="handleSimulatorEditTopic"
                      @delete-topic="handleSimulatorDeleteTopic"
                      @topic-connections="handleSimulatorTopicConnections"
                    />
                  </div>
                  
                  <!-- Interactive Content Panel (Padded) -->
                  <div class="w-full p-4 flex flex-col gap-4">
                    <div class="w-full bg-card/40 border border-border/40 rounded-xl p-5 flex flex-col gap-4 text-right">
                      <div class="flex items-center justify-between border-b border-border/40 pb-3">
                        <h3 class="text-xs font-extrabold text-foreground">
                          شبیه‌ساز محتوای پلتفرم (تفکر)
                        </h3>
                        <Badge variant="secondary" class="text-[9px] px-2 py-0.5 font-mono font-bold select-none">
                          {{ simulatorIsInnerPage ? 'Inner Page' : 'Home' }}
                        </Badge>
                      </div>

                      <div v-if="!simulatorIsInnerPage" class="flex flex-col gap-2.5">
                        <p class="text-[11px] text-muted-foreground leading-relaxed">
                          این شبیه‌سازی وضعیت صفحه اصلی برنامه است. با کلیک بر روی هر یک از تاپیک‌های آزمایشی زیر، وارد صفحه چت شده و انیمیشن جدا شدن و فاصله‌گیری ۴ پیکسلی دکمه بازگشت از بدنه اصلی هدر را مشاهده خواهید کرد:
                        </p>
                        
                        <div class="grid grid-cols-1 md:grid-cols-3 gap-3 mt-1">
                          <div 
                            v-for="chat in mockChats" 
                            :key="chat.id"
                            @click="enterChat(chat)"
                            class="flex items-center gap-3 p-3 rounded-lg bg-background/60 hover:bg-muted/60 border border-border/45 cursor-pointer transition-all active:scale-[0.98]"
                          >
                            <div class="size-8 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center text-primary text-[10px] font-extrabold shrink-0">
                              {{ chat.avatar }}
                            </div>
                            <div class="flex-1 flex flex-col text-right overflow-hidden">
                              <span class="text-[10px] font-bold text-foreground truncate">{{ chat.name }}</span>
                              <span class="text-[8.5px] text-muted-foreground mt-0.5 truncate">{{ chat.message }}</span>
                            </div>
                          </div>
                        </div>
                      </div>

                      <div v-else class="flex flex-col gap-3">
                        <p class="text-[11px] text-muted-foreground leading-relaxed">
                          شما هم‌اکنون در صفحه تاپیک <code class="bg-muted px-1.5 py-0.5 rounded font-bold text-primary">{{ simulatorInnerTitle }}</code> هستید. هدر به صورت خودکار تغییر سایز داده و دکمه بازگشت در سمت راست جدا شده است. برای بازگشت به صفحه اصلی، روی دکمه بازگشت (فلش راست) در هدر کلیک کنید یا دکمه شبیه‌ساز زیر را بزنید:
                        </p>
                        
                        <div class="self-start mt-1">
                          <Button 
                            size="sm" 
                            variant="outline"
                            @click="handleHeaderBack"
                            class="text-xs font-semibold cursor-pointer"
                          >
                            شبیه‌سازی کلیک روی دکمه بازگشت
                          </Button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- PlatformNavigation Preview -->
                <div 
                  v-else-if="currentComponent === 'nav'"
                  class="w-full h-[250px] bg-muted/10 border border-border/40 rounded-xl relative overflow-hidden flex flex-col font-sans"
                  dir="rtl"
                >
                  <div class="flex-1 p-6 flex flex-col items-center justify-center text-center">
                    <transition name="fade-slide" mode="out-in">
                      <div v-if="simulatorActiveTab === 'home'" class="flex flex-col items-center gap-2">
                        <div class="size-10 rounded-full bg-primary/10 flex items-center justify-center text-primary">
                          <HomeIcon class="size-5" />
                        </div>
                        <h4 class="text-xs font-extrabold text-foreground mt-1">پیشخوان پلتفرم تفکر (صفحه خانه)</h4>
                        <p class="text-[10px] text-muted-foreground max-w-xs leading-relaxed">
                          به بخش کاربری تفکر خوش آمدید. نویگیشن بار شناور در پایین صفحه قرار گرفته و به شما اجازه جابجایی می‌دهد.
                        </p>
                      </div>
                      <div v-else class="flex flex-col items-center gap-2">
                        <div class="size-10 rounded-full bg-primary/10 flex items-center justify-center text-primary">
                          <UserIcon class="size-5" />
                        </div>
                        <h4 class="text-xs font-extrabold text-foreground mt-1">تنظیمات حساب کاربری (صفحه پروفایل)</h4>
                        <p class="text-[10px] text-muted-foreground max-w-xs leading-relaxed">
                          در این بخش اطلاعات کاربری و سطح دسترسی شما نمایش داده می‌شود. وضعیت فعال منو با انیمیشن در پایین مشخص است.
                        </p>
                      </div>
                    </transition>
                  </div>

                  <div class="absolute bottom-4 left-1/2 -translate-x-1/2 z-10 w-auto">
                    <PlatformNavigation 
                      v-model="simulatorActiveTab"
                      @change="handleNavChange"
                    />
                  </div>
                </div>

                <!-- TopicCard Vertical List Preview (Telegram Chat List Style) -->
                <div 
                  v-else-if="currentComponent === 'topic'"
                  class="w-full flex flex-col gap-2 bg-card/10 border border-border/40 rounded-xl p-3.5"
                  dir="rtl"
                >
                  <div class="flex items-center justify-between border-b border-border/40 pb-3 mb-1 px-1">
                    <h3 class="text-xs font-extrabold text-foreground">تاپیک‌های فعال</h3>
                    <Badge variant="secondary" class="text-[9px] px-2 py-0.5 border border-border/50 text-muted-foreground font-mono">Telegram Style</Badge>
                  </div>

                  <!-- Vertical list of borderless cards (No borders/lines, separated purely by whitespace and hover effect) -->
                  <div class="flex flex-col gap-1.5 w-full">
                    <TopicCard
                      v-for="topic in mockTopics"
                      :key="topic.id"
                      :title="topic.title"
                      :description="topic.description"
                      :unreadCount="topic.unreadCount"
                      :time="topic.time"
                      :labels="topic.labels"
                      :pinned="topic.pinned"
                      @click="handleTopicClick(topic.id)"
                    />
                  </div>
                </div>

                <!-- Platform Header Search Preview Section -->
                <div 
                  v-else-if="currentComponent === 'search'"
                  class="w-full flex flex-col gap-6"
                  dir="rtl"
                >
                  <!-- Integrated Live Search & Filtering Panel -->
                  <div class="w-full bg-card/45 border border-border/40 rounded-xl p-5 flex flex-col gap-4 text-right">
                    <div class="border-b border-border/40 pb-2 flex items-center justify-between">
                      <div>
                        <h3 class="text-xs font-extrabold text-foreground">جستجوی ادغام‌شده در هدر</h3>
                        <p class="text-[9.5px] text-muted-foreground mt-1">با کلیک روی آیکون جستجو در سمت چپ هدر، نوار جستجو فعال می‌شود و فیلترینگ به صورت زنده انجام می‌گردد.</p>
                      </div>
                      <Badge variant="outline" class="text-[9px] border-emerald-500/20 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 px-2 py-0.5 font-bold">جدید / ادغام‌شده</Badge>
                    </div>

                    <!-- Interactive Demo using PlatformHeader -->
                    <div class="w-full py-2 flex flex-col gap-4">
                      <div class="flex flex-col gap-1.5">
                        <span class="text-[10px] font-bold text-muted-foreground">پیش‌نمایش تعاملی هدر:</span>
                        <div class="w-full border border-border/60 rounded-2xl p-2.5 bg-background/40 backdrop-blur-md">
                          <PlatformHeader
                            :isInnerPage="false"
                            :showSearchButton="true"
                            v-model:searchQuery="simulatorSearchQuery"
                            :loading="activeState === 'loading'"
                            :error="activeState === 'error'"
                            @actionClick="(action) => logEvent('HeaderAction', { action })"
                          />
                        </div>
                      </div>
                    </div>

                    <!-- Live search filtering list below -->
                    <div class="flex flex-col gap-2 mt-1">
                      <div class="flex items-center justify-between px-1">
                        <span class="text-[10px] font-bold text-foreground">نتایج فیلتر شده بر اساس جستجو ({{ filteredTopics.length }} مورد)</span>
                        <Badge v-if="simulatorSearchQuery" variant="secondary" class="text-[9px] px-1.5 py-0.5">فیلتر فعال: {{ simulatorSearchQuery }}</Badge>
                      </div>

                      <div class="flex flex-col gap-1.5 bg-background/20 border border-border/40 rounded-xl p-2 min-h-24">
                        <div v-if="filteredTopics.length === 0" class="text-center py-8 text-[10px] text-muted-foreground">
                          هیچ تاپیکی با کلمه «{{ simulatorSearchQuery }}» یافت نشد.
                        </div>
                        <transition-group name="list-fade" v-else>
                          <TopicCard
                            v-for="topic in filteredTopics"
                            :key="topic.id"
                            :title="topic.title"
                            :description="topic.description"
                            :unreadCount="topic.unreadCount"
                            :time="topic.time"
                            :labels="topic.labels"
                            :pinned="topic.pinned"
                            @click="handleTopicClick(topic.id)"
                          />
                        </transition-group>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Profile Option Preview -->
                <div 
                  v-else-if="currentComponent === 'profile-option'"
                  class="w-full flex flex-col gap-4 bg-card/10 border border-border/40 rounded-xl p-4"
                  dir="rtl"
                >
                  <div class="flex items-center justify-between border-b border-border/40 pb-3 mb-1 px-1">
                    <h3 class="text-xs font-extrabold text-foreground">منوی کاربری (گزینه‌ها)</h3>
                    <Badge variant="secondary" class="text-[9px] px-2 py-0.5 border border-border/50 text-muted-foreground font-mono">Profile Menu Items</Badge>
                  </div>

                  <!-- Vertical menu list (menu stack of ProfileOptionCards) -->
                  <div class="flex flex-col gap-2.5 w-full">
                    <ProfileOptionCard
                      :title="'تنظیمات سیستم'"
                      :description="'تنظیمات زبان، ظاهر، حریم خصوصی و اعلان‌ها'"
                      :icon="SettingsIcon"
                      :badgeText="simulatorSettingsBadge || undefined"
                      :badgeVariant="'destructive'"
                      @click="handleProfileOptionClick('Settings')"
                    />
                    
                    <ProfileOptionCard
                      :title="'مدیریت اتصال‌ها'"
                      :description="'مدیریت اتصال به ربات‌ها، کانال‌ها و پلتفرم‌های خارجی'"
                      :icon="LinkIcon"
                      :badgeText="simulatorConnectionsBadge || undefined"
                      :badgeVariant="'default'"
                      @click="handleProfileOptionClick('Connections')"
                    />

                    <ProfileOptionCard
                      :title="'دستیار هوش مصنوعی'"
                      :description="'تنظیمات مدل هوشمند تفکر، خلاقیت و کلیدهای API فعال'"
                      :icon="SparklesIcon"
                      :badgeText="simulatorAiBadge || undefined"
                      :badgeVariant="'default'"
                      @click="handleProfileOptionClick('AI')"
                    />
                  </div>
                </div>

                <!-- ProfileCard Preview -->
                <div 
                  v-else-if="currentComponent === 'profile-card-header'"
                  class="w-full flex flex-col gap-4 bg-card/10 border border-border/40 rounded-xl p-4"
                  dir="rtl"
                >
                  <div class="flex items-center justify-between border-b border-border/40 pb-3 mb-1 px-1">
                    <h3 class="text-xs font-extrabold text-foreground">کارت هدر پروفایل</h3>
                    <Badge variant="secondary" class="text-[9px] px-2 py-0.5 border border-border/50 text-muted-foreground font-mono">Profile Header Card</Badge>
                  </div>

                  <div class="w-full max-w-xs mx-auto py-6">
                    <ProfileCard
                      :name="simulatorProfileCardName"
                      :phone="simulatorProfileCardPhone"
                      :statusVariant="simulatorProfileCardStatus"
                      :statusText="
                        simulatorProfileCardStatus === 'success' ? 'فعال' :
                        simulatorProfileCardStatus === 'warning' ? 'مشغول' :
                        simulatorProfileCardStatus === 'info' ? 'غایب' : 'آفلاین'
                      "
                      @edit="handleProfileCardEdit"
                    />
                  </div>
                </div>

                <!-- PostCard Preview Feed (Telegram Topic style) -->
                <div 
                  v-else-if="currentComponent === 'post'"
                  class="w-full flex flex-col gap-2 bg-radial from-card/5 to-card/0 border border-border/40 rounded-xl p-3.5 relative overflow-hidden"
                  dir="rtl"
                >
                  <!-- Simulated colorful background elements to highlight blur/transparency -->
                  <div class="absolute -top-12 -left-12 size-40 rounded-full bg-primary/8 blur-3xl pointer-events-none" />
                  <div class="absolute -bottom-12 -right-12 size-40 rounded-full bg-accent/8 blur-3xl pointer-events-none" />
                  
                  <div class="flex items-center justify-between border-b border-border/40 pb-3 mb-1 px-1 z-10">
                    <h3 class="text-xs font-extrabold text-foreground">تایپک: توسعه پلتفرم تفکر</h3>
                    <Badge variant="secondary" class="text-[9px] px-2 py-0.5 border border-border/50 text-muted-foreground font-mono">Full Width Glass Feed</Badge>
                  </div>

                  <!-- Feed of posts separated by exactly 8px (gap-2) -->
                  <div class="flex flex-col gap-2 w-full z-10">
                    <PostCard
                      v-for="post in mockPosts"
                      :key="post.id"
                      :id="post.id"
                      :author="post.author"
                      :type="post.type"
                      :content="post.content"
                      :mediaUrl="post.mediaUrl"
                      :posterUrl="post.posterUrl"
                      :duration="post.duration"
                      :timestamp="post.timestamp"
                      :likesCount="post.likesCount"
                      :comments="post.comments"
                      :liked="post.liked"
                      :reactions="post.reactions || []"
                      @like="handlePostLike"
                      @share="handlePostShare"
                      @add-comment="handlePostCommentAdded"
                      @react="handlePostReact"
                      @edit="handlePostEdit"
                      @delete="handlePostDelete"
                      @pin="handlePostPin"
                      @copy="handlePostCopy"
                    />
                  </div>
                </div>

                <!-- CreateTopicModal Preview -->
                <div 
                  v-else-if="currentComponent === 'create-topic-modal'"
                  class="w-full flex flex-col items-center justify-center py-10"
                  dir="rtl"
                >
                  <Button @click="simulatorIsModalOpen = true" class="cursor-pointer flex items-center" data-icon="inline-start">
                    <PlusIcon />
                    کلیک کنید تا مودال ساخت تاپیک باز شود
                  </Button>
                  
                  <p class="text-[10px] text-muted-foreground text-center mt-3 max-w-xs leading-relaxed">
                    با کلیک بر روی دکمه بالا، مودال ایجاد تاپیک باز می‌شود. رویدادهای «ایجاد» و «انصراف» در کنسول پایین ثبت خواهند شد.
                  </p>
                  
                  <CreateTopicModal
                    :isOpen="simulatorIsModalOpen"
                    @close="handleModalClose"
                    @create="handleModalCreate"
                  />
                </div>

                <!-- BotConnectionCard Preview -->
                <div 
                  v-else-if="currentComponent === 'bot-connection'"
                  class="w-full flex flex-col items-center py-4 px-2"
                  dir="rtl"
                >
                  <BotConnectionCard
                    :platform="simulatorBotPlatform"
                    :initialStatus="simulatorBotStatus"
                    :initialToken="simulatorBotToken"
                    @connect="handleBotConnect"
                    @disconnect="handleBotDisconnect"
                    @edit="handleBotEdit"
                    @update:status="(st) => { simulatorBotStatus = st }"
                  />
                </div>

                <!-- TopicMessageInput Preview -->
                <div 
                  v-else-if="currentComponent === 'topic-input'"
                  class="w-full flex flex-col items-center py-4 px-2"
                  dir="rtl"
                >
                  <TopicMessageInput
                    :placeholder="simulatorInputPlaceholder"
                    :disabled="simulatorInputDisabled"
                    :initialText="simulatorInputText"
                    :initialAttachments="simulatorInputAttachments"
                    @send="handleInputSend"
                    @removeAttachment="handleInputRemoveAttachment"
                  />
                </div>

                <!-- TopicEditView Preview -->
                <div 
                  v-else-if="currentComponent === 'topic-edit'"
                  class="w-full flex flex-col"
                  dir="rtl"
                >
                  <TopicEditView 
                    :topic="simulatorTopicData"
                    @back="logEvent('TopicEdit: Back Clicked', {}); currentComponent = 'header'"
                    @save="(data) => {
                      simulatorTopicData.title = data.title;
                      simulatorTopicData.description = data.description;
                      simulatorTopicData.image = data.image;
                      logEvent('TopicEdit: Saved', data);
                    }"
                  />
                </div>

                <!-- TopicConnectionsView Preview -->
                <div 
                  v-else-if="currentComponent === 'topic-connections'"
                  class="w-full flex flex-col"
                  dir="rtl"
                >
                  <TopicConnectionsView 
                    :topic="simulatorTopicData"
                    :telegramConnected="simulatorTelegramConnected"
                    :baleConnected="simulatorBaleConnected"
                    @back="logEvent('TopicConnections: Back Clicked', {}); currentComponent = 'header'"
                    @goToConnections="logEvent('TopicConnections: Redirected to Bot connections settings', {}); currentComponent = 'bot-connection'"
                    @save="(data) => {
                      simulatorTopicData.telegram_bot_active = data.telegram_bot_active;
                      simulatorTopicData.bale_bot_active = data.bale_bot_active;
                      simulatorTopicData.telegram_connections = data.telegram_connections;
                      simulatorTopicData.bale_connections = data.bale_connections;
                      logEvent('TopicConnections: Saved Settings', data);
                    }"
                  />
                </div>

              </div>
            </div>
          </div>

          <!-- Interactive Event Log Console -->
          <div class="bg-card/30 border border-border/60 rounded-lg p-6 shadow-xs flex flex-col gap-3">
            <div class="flex items-center justify-between">
              <h3 class="text-xs font-extrabold text-foreground flex items-center gap-1.5">
                <TerminalIcon class="size-3.5 text-primary" />
                کنسول ثبت رویدادها (Events Log)
              </h3>
              <Badge variant="secondary" class="text-[9px] px-2 py-0.5 border border-border/50 text-muted-foreground font-mono">Reactive Logs</Badge>
            </div>

            <div class="bg-background/80 border border-border/60 rounded-lg p-3 h-36 font-mono text-[10px] overflow-y-auto flex flex-col gap-2 scrollbar-thin">
              <div v-if="eventLog.length === 0" class="text-muted-foreground text-center py-8">
                هیچ رویدادی ثبت نشده است. روی دکمه‌های کامپوننت کلیک کنید.
              </div>
              <div 
                v-for="event in eventLog" 
                :key="event.id" 
                class="flex items-start justify-between border-b border-border/20 pb-1.5 last:border-0"
              >
                <div class="flex items-start gap-2 text-right">
                  <ChevronLeftIcon class="size-3 text-emerald-550 dark:text-emerald-400 shrink-0 mt-0.5" />
                  <div>
                    <span class="text-primary font-bold ml-1">[{{ event.name }}]</span>
                    <span class="text-muted-foreground leading-normal break-all">{{ event.data }}</span>
                  </div>
                </div>
                <span class="text-[9px] text-muted-foreground shrink-0 font-mono">{{ event.time }}</span>
              </div>
            </div>
          </div>

        </div>

      </div>

    </div>
  </div>
</template>

<style scoped>
/* Fade-slide transition for mockup screen navigation */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}
.fade-slide-enter-from {
  opacity: 0;
  transform: translateX(-15px);
}
.fade-slide-leave-to {
  opacity: 0;
  transform: translateX(15px);
}

/* Slide/fade transition for header title during search expansion */
.header-title-fade-enter-active,
.header-title-fade-leave-active {
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}
.header-title-fade-enter-from,
.header-title-fade-leave-to {
  opacity: 0;
  transform: translateX(15px);
}

/* Fade transition for reactive list filtering */
.list-fade-enter-active,
.list-fade-leave-active {
  transition: all 0.2s ease;
}
.list-fade-enter-from,
.list-fade-leave-to {
  opacity: 0;
  transform: translateY(5px);
}

/* Viewport Sandbox backgrounds for glassmorphism testing */
.bg-sandbox-default {
  background-color: var(--background);
}
.bg-sandbox-gradient {
  background: radial-gradient(circle at 10% 20%, oklch(0.65 0.18 310) 0%, transparent 50%),
              radial-gradient(circle at 90% 80%, oklch(0.55 0.16 190) 0%, transparent 50%),
              radial-gradient(circle at 50% 50%, oklch(0.75 0.12 85) 0%, transparent 60%),
              linear-gradient(135deg, oklch(0.25 0.08 260) 0%, oklch(0.18 0.04 280) 100%);
}
.dark .bg-sandbox-gradient {
  background: radial-gradient(circle at 10% 20%, oklch(0.35 0.12 310) 0%, transparent 50%),
              radial-gradient(circle at 90% 80%, oklch(0.25 0.1 190) 0%, transparent 50%),
              radial-gradient(circle at 50% 50%, oklch(0.35 0.08 85) 0%, transparent 60%),
              linear-gradient(135deg, oklch(0.12 0.03 260) 0%, oklch(0.08 0.02 280) 100%);
}
.bg-sandbox-grid {
  background-image: linear-gradient(to right, var(--border) 1px, transparent 1px),
                    linear-gradient(to bottom, var(--border) 1px, transparent 1px);
  background-size: 24px 24px;
  background-color: var(--background);
}
.bg-sandbox-image {
  background-image: url('https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=1200&auto=format&fit=crop&q=80');
  background-size: cover;
  background-position: center;
}
</style>
