<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { useLanguageStore } from '@/stores/languageStore'
const languageStore = useLanguageStore()
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
import LoadingDialog from '@/components/LoadingDialog.vue'
import TopicImportView from '@/components/TopicImportView.vue'
import ConfirmModal from '@/components/ConfirmModal.vue'
import DuplicateWarningDialog from '@/components/DuplicateWarningDialog.vue'
import TopicAdminsView from '@/components/TopicAdminsView.vue'
import EditProfileModal from '@/components/EditProfileModal.vue'
import ChangelogModal from '@/components/ChangelogModal.vue'
import AIRefinerDrawer from '@/components/AIRefinerDrawer.vue'
import DonationCard from '@/components/kindness/DonationCard.vue'
import DonationModal from '@/components/kindness/DonationModal.vue'
import CreateDonationDialog from '@/components/kindness/CreateDonationDialog.vue'
import DonationChatCard from '@/components/kindness/DonationChatCard.vue'
import UnderDevelopmentCard from '@/components/UnderDevelopmentCard.vue'
import type { DonationCampaignProps, CreateDonationPayload, CampaignCategory } from '@/types/kindness'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter
} from '@/components/ui/dialog'
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
  LanguagesIcon,
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
  HistoryIcon,
  SparklesIcon,
  PencilIcon,
  MessageCircleIcon,
  ChevronLeftIcon,
  PlusIcon,
  CopyIcon,
  CheckIcon,
  Trash2Icon,
  AlertTriangleIcon,
  UploadCloudIcon,
  ShieldCheckIcon,
  Wand2Icon,
  HandHeartIcon,
  HeartIcon,
  ConstructionIcon,
  RocketIcon,
  WrenchIcon,
  ClockIcon,
  LayersIcon,
  EyeIcon
} from '@lucide/vue'

// Simulator configs
const currentComponent = ref<'profile' | 'login' | 'header' | 'nav' | 'topic' | 'search' | 'profile-option' | 'profile-card-header' | 'post' | 'create-topic-modal' | 'bot-connection' | 'topic-input' | 'topic-edit' | 'topic-connections' | 'loading-dialog' | 'topic-import' | 'confirm-modal' | 'duplicate-warning-dialog' | 'topic-admins' | 'edit-profile-modal' | 'changelog-modal' | 'ai-refiner-drawer' | 'donation-card' | 'donation-chat-card' | 'create-donation-dialog' | 'under-dev'>('create-donation-dialog')

// DonationChatCard (In-Topic Message Card) simulation state
const simulatorChatCardTitle = ref('تجهیز و شاداب‌سازی مدرسه ابتدایی روستا')
const simulatorChatCardCategory = ref<CampaignCategory>('school')
const simulatorChatCardTargetAmount = ref<number>(30000000)
const simulatorChatCardCollectedAmount = ref<number>(18500000)
const simulatorChatCardDesc = ref('این پویش جهت خرید میز، نیمکت و سیستم گرمایشی برای دانش‌آموزان این منطقه راه‌اندازی شده است.')
const simulatorChatCardHasMedia = ref(true)
const simulatorChatCardMediaUrl = ref('https://images.unsplash.com/photo-1509062522246-3755977927d7?auto=format&fit=crop&w=800&q=80')
const simulatorChatCardMediaType = ref<'image' | 'video'>('image')
const simulatorChatCardMediaCount = ref(3)
const simulatorChatCardAutoPin = ref(true)
const simulatorChatCardDeadline = ref('۱۰ روز آینده')
const simulatorChatCardTopicName = ref('کانون جهادی و فرهنگی')
const simulatorChatCardAuthorName = ref('مدیر گروه جهادی')
const simulatorChatCardIsPreview = ref(false)

// CreateDonationDialog simulation state
const isSimulatorCreateDonationOpen = ref(false)
const simulatorCreateDonationTopicName = ref('کانون جهادی و فرهنگی امام رضا (ع)')
const simulatorCreateDonationAuthorName = ref('مسئول گروه جهادی')
const simulatorLastCreatedDonation = ref<CreateDonationPayload | null>(null)

// UnderDevelopmentCard simulation state
const simulatorUnderDevTitle = ref('تحلیل هوشمند و آمار پیشرفته')
const simulatorUnderDevDesc = ref('این بخش به‌زودی با امکانات تحلیلی و گزارش‌های زنده در دسترس قرار می‌گیرد.')
const simulatorUnderDevBadge = ref('به‌زودی')
const simulatorUnderDevBadgeVariant = ref<'default' | 'secondary' | 'outline' | 'destructive'>('secondary')
const simulatorUnderDevEta = ref('نسخه ۲.۵')
const simulatorUnderDevSpeed = ref<'slow' | 'normal' | 'fast'>('normal')
const simulatorUnderDevPattern = ref<'stripes' | 'grid' | 'dots'>('stripes')
const simulatorUnderDevIconName = ref<'construction' | 'sparkles' | 'rocket' | 'wrench' | 'layers'>('construction')
const simulatorUnderDevShowBack = ref(true)
const simulatorUnderDevBackText = ref('')
const simulatorUnderDevActionText = ref('اطلاع‌رسانی هنگام انتشار')
const simulatorUnderDevFeatures = ref(['آمار زنده تاپیک‌ها', 'پیشنهاد هوشمند محتوا', 'گزارش‌های تحلیلی'])
const newUnderDevFeatureInput = ref('')

const addUnderDevFeature = () => {
  if (newUnderDevFeatureInput.value.trim()) {
    simulatorUnderDevFeatures.value.push(newUnderDevFeatureInput.value.trim())
    newUnderDevFeatureInput.value = ''
    logEvent('UnderDevCard: Feature item added', { features: simulatorUnderDevFeatures.value })
  }
}

const removeUnderDevFeature = (index: number) => {
  simulatorUnderDevFeatures.value.splice(index, 1)
  logEvent('UnderDevCard: Feature item removed', { index })
}

const currentUnderDevIconComponent = computed(() => {
  switch (simulatorUnderDevIconName.value) {
    case 'construction': return ConstructionIcon
    case 'rocket': return RocketIcon
    case 'wrench': return WrenchIcon
    case 'sparkles': return SparklesIcon
    case 'layers': return LayersIcon
    default: return ConstructionIcon
  }
})

// Dynamic Code Generator for UnderDevelopmentCard
const underDevCopied = ref(false)
const underDevActiveTab = ref<'preview' | 'code' | 'presets'>('preview')

const generatedUnderDevCode = computed(() => {
  const iconMap: Record<string, string> = {
    construction: 'ConstructionIcon',
    rocket: 'RocketIcon',
    wrench: 'WrenchIcon',
    sparkles: 'SparklesIcon',
    layers: 'LayersIcon'
  }
  const iconName = iconMap[simulatorUnderDevIconName.value] || 'ConstructionIcon'
  
  const lines: string[] = ['<UnderDevelopmentCard']
  if (simulatorUnderDevTitle.value) {
    lines.push(`  title="${simulatorUnderDevTitle.value}"`)
  }
  if (simulatorUnderDevDesc.value) {
    lines.push(`  description="${simulatorUnderDevDesc.value}"`)
  }
  lines.push(`  :icon="${iconName}"`)
  if (simulatorUnderDevEta.value) {
    lines.push(`  eta="${simulatorUnderDevEta.value}"`)
  }
  if (simulatorUnderDevFeatures.value && simulatorUnderDevFeatures.value.length > 0) {
    lines.push(`  :features="[\n    ${simulatorUnderDevFeatures.value.map(f => `'${f}'`).join(',\n    ')}\n  ]"`)
  }
  if (simulatorUnderDevActionText.value) {
    lines.push(`  action-text="${simulatorUnderDevActionText.value}"`)
    lines.push(`  @action="handleNotify"`)
  }
  if (simulatorUnderDevShowBack.value) {
    lines.push(`  :show-back-button="true"`)
    if (simulatorUnderDevBackText.value) {
      lines.push(`  back-button-text="${simulatorUnderDevBackText.value}"`)
    }
    lines.push(`  @back="handleBack"`)
  }
  if (simulatorUnderDevPattern.value !== 'stripes') {
    lines.push(`  pattern-style="${simulatorUnderDevPattern.value}"`)
  }
  if (simulatorUnderDevSpeed.value !== 'normal') {
    lines.push(`  pattern-speed="${simulatorUnderDevSpeed.value}"`)
  }
  lines.push('/>')
  
  const templateSnippet = lines.join('\n')
  const scriptSnippet = `<script setup lang="ts">\nimport UnderDevelopmentCard from '@/components/UnderDevelopmentCard.vue'\nimport { ${iconName} } from '@lucide/vue'\n\nconst handleNotify = () => {\n  console.log('User clicked notify')\n}\n\nconst handleBack = () => {\n  // Handle back navigation\n}\n<\/script>`

  return `<!-- 1. Script Setup -->\n${scriptSnippet}\n\n<!-- 2. Template Usage -->\n${templateSnippet}`
})

const copyUnderDevCode = async () => {
  try {
    await navigator.clipboard.writeText(generatedUnderDevCode.value)
    underDevCopied.value = true
    logEvent('UnderDevCard: Code Copied to Clipboard', { characters: generatedUnderDevCode.value.length })
    setTimeout(() => {
      underDevCopied.value = false
    }, 2500)
  } catch (err) {
    console.error('Failed to copy code:', err)
  }
}

const applyUnderDevPreset = (preset: 'minimal' | 'full' | 'ai' | 'rocket') => {
  if (preset === 'minimal') {
    simulatorUnderDevTitle.value = 'در حال توسعه'
    simulatorUnderDevDesc.value = 'این بخش به‌زودی در دسترس شما قرار می‌گیرد.'
    simulatorUnderDevIconName.value = 'construction'
    simulatorUnderDevPattern.value = 'stripes'
    simulatorUnderDevSpeed.value = 'normal'
    simulatorUnderDevFeatures.value = []
    simulatorUnderDevEta.value = ''
    simulatorUnderDevActionText.value = ''
    simulatorUnderDevShowBack.value = true
  } else if (preset === 'full') {
    simulatorUnderDevTitle.value = 'تحلیل هوشمند و آمار پیشرفته'
    simulatorUnderDevDesc.value = 'این بخش به‌زودی با امکانات تحلیلی و گزارش‌های زنده در دسترس قرار می‌گیرد.'
    simulatorUnderDevIconName.value = 'sparkles'
    simulatorUnderDevPattern.value = 'grid'
    simulatorUnderDevSpeed.value = 'normal'
    simulatorUnderDevFeatures.value = ['آمار زنده تاپیک‌ها', 'پیشنهاد هوشمند محتوا', 'گزارش‌های تحلیلی']
    simulatorUnderDevEta.value = 'نسخه ۲.۵'
    simulatorUnderDevActionText.value = 'اطلاع‌رسانی هنگام انتشار'
    simulatorUnderDevShowBack.value = true
  } else if (preset === 'ai') {
    simulatorUnderDevTitle.value = 'دستیار خودکار تولید محتوا'
    simulatorUnderDevDesc.value = 'تولید هوشمند پیش‌نویس پست‌ها و زمان‌بندی انتشار خودکار.'
    simulatorUnderDevIconName.value = 'sparkles'
    simulatorUnderDevPattern.value = 'dots'
    simulatorUnderDevSpeed.value = 'fast'
    simulatorUnderDevFeatures.value = ['تولید خودکار پیش‌نویس', 'بررسی لحن نگارش', 'انتشار در ساعات پربازدید']
    simulatorUnderDevEta.value = 'پاییز ۱۴۰۵'
    simulatorUnderDevActionText.value = 'ثبت‌نام در لیست انتظار'
    simulatorUnderDevShowBack.value = false
  } else if (preset === 'rocket') {
    simulatorUnderDevTitle.value = 'یکپارچه‌سازی با وب‌هوک‌ها'
    simulatorUnderDevDesc.value = 'اتصال مستقیم به پیام‌رسان‌ها و سرویس‌های خارجی از طریق API.'
    simulatorUnderDevIconName.value = 'rocket'
    simulatorUnderDevPattern.value = 'stripes'
    simulatorUnderDevSpeed.value = 'fast'
    simulatorUnderDevFeatures.value = ['پشتیبانی از Webhook', 'ارسال به کانال‌های چندگانه']
    simulatorUnderDevEta.value = 'نسخه ۳.۰'
    simulatorUnderDevActionText.value = 'مشاهده مستندات API'
    simulatorUnderDevShowBack.value = true
  }
  logEvent('UnderDevCard: Preset Applied', { preset })
}

// DonationCard simulation state
const simulatorDonationModalOpen = ref(false)
const simulatorDonationCampaign = reactive<DonationCampaignProps>({
  id: 'cmp-playground-1',
  title: 'تجهیز و شاداب‌سازی کلاس درس مدرسه ابتدایی در روستای محروم',
  description: 'این پویش جهت خرید ۲۰ عدد میز و نیمکت استاندارد، یک عدد تخته هوشمند و رنگ‌آمیزی کامل ۲ کلاس درس در منطقه محروم راه‌اندازی شده است.',
  topicId: 101,
  topicName: 'مدرسه شهید بهشتی - کانون جهادی',
  category: 'مدرسه و آموزش',
  status: 'active',
  targetAmount: 100000000,
  collectedAmount: 45000000,
  donorsCount: 28,
  mediaGallery: [
    'https://images.unsplash.com/photo-1509062522246-3755977927d7?auto=format&fit=crop&w=800&q=80',
    'https://images.unsplash.com/photo-1580582932707-520aed937b7b?auto=format&fit=crop&w=800&q=80',
    'https://images.unsplash.com/photo-1497633762265-9d179a990aa6?auto=format&fit=crop&w=800&q=80',
    'https://images.unsplash.com/photo-1577896851231-70ef18881754?auto=format&fit=crop&w=800&q=80',
    'https://images.unsplash.com/photo-1503676260728-1c00da094a0b?auto=format&fit=crop&w=800&q=80'
  ],
  recentDonors: [
    { id: 'd-1', name: 'رضا محمدی', amount: 5000000, isAnonymous: false, donatedAt: '۱۰ دقیقه پیش' },
    { id: 'd-2', name: 'کاربر ناشناس', amount: 10000000, isAnonymous: true, donatedAt: '۱ ساعت پیش' }
  ]
})

const handleDonateClick = (id: string | number) => {
  logEvent('DonationCard: Donate Clicked', { campaignId: id })
  simulatorDonationModalOpen.value = true
}

const handleDonationTopicClick = (topicId: string | number) => {
  logEvent('DonationCard: Topic Clicked', { topicId })
}

const handleTransparencyClick = (idx: number, url: string) => {
  logEvent('DonationCard: Transparency Image Clicked', { idx, url })
}

const handleDonationSubmit = (amount: number, isAnon: boolean) => {
  logEvent('DonationModal: Donation Submitted', { amount, isAnon })
  simulatorDonationCampaign.collectedAmount += amount
  simulatorDonationCampaign.donorsCount++
  simulatorDonationCampaign.recentDonors.unshift({
    id: `d-new-${Date.now()}`,
    name: isAnon ? 'کاربر ناشناس' : 'حامی جدید',
    amount,
    isAnonymous: isAnon,
    donatedAt: 'هم‌اکنون'
  })
}

const setDonationState = (status: 'active' | 'completed' | 'executed') => {
  simulatorDonationCampaign.status = status
  if (status === 'active') {
    simulatorDonationCampaign.collectedAmount = 45000000
    simulatorDonationCampaign.targetAmount = 100000000
  } else if (status === 'completed') {
    simulatorDonationCampaign.collectedAmount = 100000000
    simulatorDonationCampaign.targetAmount = 100000000
  } else if (status === 'executed') {
    simulatorDonationCampaign.collectedAmount = 80000000
    simulatorDonationCampaign.targetAmount = 80000000
    simulatorDonationCampaign.transparency = {
      isAvailable: true,
      executedAt: '۱۴۰۳/۰۵/۱۵',
      description: 'پویش با موفقیت ۱۰۰٪ به پایان رسید و تمام اقلام تهیه شده و به دست خانواده‌های هدف رسید.',
      costBreakdown: {
        'خرید ۱۰۰ بسته لوازم‌التحریر و کیف': 42000000,
        'خرید اقلام غذایی (برنج، روغن، حبوبات)': 35000000,
        'هزینه حمل و بسته‌بندی': 3000000
      },
      receiptImages: [
        'https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?auto=format&fit=crop&w=400&q=80'
      ]
    }
  }
  logEvent('DonationCard: State Changed', { newStatus: status })
}
const viewportWidth = ref<'100%' | '768px' | '375px'>('100%')
const sandboxBg = ref<'default' | 'gradient' | 'grid' | 'image'>('default')
const activeState = ref<'idle' | 'loading' | 'error' | 'empty' | 'success'>('idle')

// Topic Admins simulation state
const simulatorAdminsIsOpen = ref(false)
const simulatorAdminsTopicId = ref<string | number | null>(1)
const simulatorAdminsIsOwner = ref(true)
const simulatorAdminsForcedState = ref<'default' | 'loading' | 'empty' | 'error'>('default')

// Additional Modals & Drawers simulation state
const simulatorEditProfileIsOpen = ref(false)
const simulatorChangelogIsOpen = ref(false)
const simulatorAIRefinerIsOpen = ref(false)
const simulatorAIRefinerText = ref('این یک متن نمونه جهت تست دستیار بهبود متن هوش مصنوعی است.')

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

// Compute source file name for the current component
const currentComponentFile = computed(() => {
  switch (currentComponent.value) {
    case 'profile': return 'UserProfileCard.vue'
    case 'login': return 'LoginCard.vue'
    case 'header': return 'PlatformHeader.vue'
    case 'nav': return 'PlatformNavigation.vue'
    case 'topic': return 'TopicCard.vue'
    case 'search': return 'PlatformHeader.vue (Search Mode)'
    case 'profile-option': return 'ProfileOptionCard.vue'
    case 'profile-card-header': return 'ProfileCard.vue'
    case 'post': return 'PostCard.vue'
    case 'create-topic-modal': return 'CreateTopicModal.vue'
    case 'bot-connection': return 'BotConnectionCard.vue'
    case 'topic-input': return 'TopicMessageInput.vue'
    case 'topic-edit': return 'TopicEditView.vue'
    case 'topic-connections': return 'TopicConnectionsView.vue'
    case 'loading-dialog': return 'LoadingDialog.vue'
    case 'topic-import': return 'TopicImportView.vue'
    case 'confirm-modal': return 'ConfirmModal.vue'
    case 'duplicate-warning-dialog': return 'DuplicateWarningDialog.vue'
    case 'topic-admins': return 'TopicAdminsView.vue'
    case 'edit-profile-modal': return 'EditProfileModal.vue'
    case 'changelog-modal': return 'ChangelogModal.vue'
    case 'ai-refiner-drawer': return 'AIRefinerDrawer.vue'
    case 'donation-card': return 'DonationCard.vue'
    case 'donation-chat-card': return 'DonationChatCard.vue'
    case 'create-donation-dialog': return 'CreateDonationDialog.vue'
    case 'under-dev': return 'UnderDevelopmentCard.vue'
    default: return ''
  }
})

const isCopied = ref(false)

const copyComponentFile = async () => {
  if (!currentComponentFile.value) return
  try {
    await navigator.clipboard.writeText(currentComponentFile.value.split(' ')[0] || '') // Strip extra details if any
    isCopied.value = true
    setTimeout(() => {
      isCopied.value = false
    }, 1500)
    logEvent('Playground: Copied component filename', { filename: currentComponentFile.value })
  } catch (err) {
    console.error('Failed to copy text:', err)
  }
}

const handleComponentChange = (comp: typeof currentComponent.value) => {
  currentComponent.value = comp
  activeState.value = 'idle'
  if (comp === 'create-donation-dialog') {
    isSimulatorCreateDonationOpen.value = true
  }
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
const enInitialUser: UserProfile = {
  name: 'Shayan Mahdavi',
  email: 'shayan@example.com',
  role: 'UI/UX Designer',
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

const faMockChats = [
  { id: 1, name: 'پشتیبانی تفکر', message: 'سلام! انیمیشن تفکیک دکمه...', time: '۱۲:۳۰', avatar: 'پ' },
  { id: 2, name: 'کانال اطلاعیه‌ها', message: 'نسخه جدید دشبورد منتشر شد.', time: '۱۰:۱۵', avatar: 'ا' },
  { id: 3, name: 'امیرحسین رضایی', message: 'طرح کارت لاگین رو بررسی کردی؟', time: 'دیروز', avatar: 'ا' }
]

const enMockChats = [
  { id: 1, name: 'Tafakor Support', message: 'Hello! The separation animation of...', time: '12:30', avatar: 'S' },
  { id: 2, name: 'Announcements Channel', message: 'The new dashboard version is live.', time: '10:15', avatar: 'A' },
  { id: 3, name: 'Amirhossein Rezaei', message: 'Did you check the login card layout?', time: 'Yesterday', avatar: 'A' }
]

const mockChats = reactive([...faMockChats])

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

const handleSimulatorTopicImport = () => {
  logEvent('Header: Topic Import History Opened', { topicTitle: simulatorInnerTitle.value })
  currentComponent.value = 'topic-import'
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

const getImageUrl = (image: string | File | null | undefined): string => {
  if (!image) return ''
  if (typeof image === 'string') return image
  return URL.createObjectURL(image)
}

// Platform Navigation simulation variables
const simulatorActiveTab = ref<'home' | 'donate' | 'marketplace' | 'profile'>('home')

const handleNavChange = (tab: 'home' | 'donate' | 'marketplace' | 'profile') => {
  logEvent('Nav: Active Tab Changed', { tab })
}

// Topic Card simulation state
const faMockTopics = [
  { id: 1, title: 'گروه توسعه تفکر', description: 'شایان: طرح هدر پلتفرم را اصلاح کردم و انیمیشن بک به درستی کار می‌کند.', unreadCount: 5, time: '۱۲:۳۰', labels: ['فناوری', 'توسعه'], pinned: true },
  { id: 2, title: 'کانال عمومی اخبار پلتفرم', description: 'اطلاعیه: نسخه بتای آزمایشگاه تست شبیه‌سازها هم‌اکنون به صورت آزمایشی در دسترس قرار گرفت.', unreadCount: 12, time: '۱۰:۱۵', labels: ['اخبار', 'تفکر'], pinned: false },
  { id: 3, title: 'تیم طراحی رابط کاربری', description: 'امیر: لطفا آیکون‌ها و رنگ‌های شیشه‌ای را مجدداً هماهنگ کنید.', unreadCount: 0, time: 'دیروز', labels: ['طراحی', 'UI/UX'], pinned: false }
]

const enMockTopics = [
  { id: 1, title: 'Tafakor Dev Group', description: 'Shayan: I revised the header layout and the back animation works perfectly.', unreadCount: 5, time: '12:30', labels: ['Tech', 'Dev'], pinned: true },
  { id: 2, title: 'Platform News Channel', description: 'Announcement: The beta version of simulator testing lab is now available for testing.', unreadCount: 12, time: '10:15', labels: ['News', 'Platform'], pinned: false },
  { id: 3, title: 'UI/UX Design Team', description: 'Amir: Please coordinate the icons and glass colors once again.', unreadCount: 0, time: 'Yesterday', labels: ['Design', 'UI/UX'], pinned: false }
]

const mockTopics = ref([...faMockTopics])

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
const simulatorConnectionsBadge = computed(() => languageStore.t('۳ فعال', '3 active'))
const simulatorAiBadge = computed(() => languageStore.t('جدید', 'New'))
const showLanguageDialog = ref(false)
const selectedLang = ref<'fa' | 'en'>(languageStore.currentLanguage)

watch(showLanguageDialog, (isOpen) => {
  if (isOpen) {
    selectedLang.value = languageStore.currentLanguage
  }
})

const handleConfirmLanguage = () => {
  languageStore.setLanguage(selectedLang.value)
  showLanguageDialog.value = false
}

const handleProfileOptionClick = (option: string) => {
  logEvent('Profile Option Clicked', { option })
  if (option === 'Language') {
    showLanguageDialog.value = true
  }
}

// ProfileCard simulation variables
const simulatorProfileCardName = computed(() => languageStore.t('شایان مهدوی', 'Shayan Mahdavi'))
const simulatorProfileCardPhone = computed(() => languageStore.t('۰۹۱۲۳۴۵۶۷۸۹', '09123456789'))
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

const faInitialPosts: Post[] = [
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

const enInitialPosts: Post[] = [
  {
    id: 1,
    author: {
      name: 'Sara Ahmadi',
      avatarUrl: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100&auto=format&fit=crop&q=80',
      role: 'Tafakor Product Manager'
    },
    type: 'text' as const,
    content: 'Hello team! I have prepared the initial layout for the posts and glassmorphism components. Please write your feedback about the new structure in the comments section.',
    timestamp: '14:32 - June 17, 2026',
    likesCount: 12,
    liked: true,
    comments: [
      { id: 101, authorName: 'Babak Rezaei', text: 'Looks very elegant and minimal, great job!', timestamp: '14:35' },
      { id: 102, authorName: 'Nasim Moradi', text: 'Does the blur effect work well on moving backgrounds?', timestamp: '14:40' }
    ],
    reactions: [
      { emoji: '👍', count: 4, reacted: true },
      { emoji: '❤️', count: 2, reacted: false }
    ]
  },
  {
    id: 2,
    author: {
      name: 'Saman Fotouhi',
      avatarUrl: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&auto=format&fit=crop&q=80',
      role: 'Lead UI/UX Designer'
    },
    type: 'image' as const,
    content: 'The new background image I designed for the platform header. What do you think? The transparency of the cards on this image looks beautiful.',
    mediaUrl: 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=800&auto=format&fit=crop&q=80',
    timestamp: '12:15 - June 17, 2026',
    likesCount: 28,
    liked: false,
    comments: [
      { id: 201, authorName: 'Sara Ahmadi', text: 'The colors are amazing, it matches dark mode very well.', timestamp: '12:20' }
    ],
    reactions: [
      { emoji: '🔥', count: 8, reacted: true },
      { emoji: '💯', count: 3, reacted: false }
    ]
  },
  {
    id: 3,
    author: {
      name: 'Ali Karimi',
      avatarUrl: '',
      role: 'Frontend Developer'
    },
    type: 'video' as const,
    content: 'Video testing the behavior of back button transition animations in mobile view. Be sure to check it.',
    mediaUrl: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4',
    posterUrl: 'https://images.unsplash.com/photo-1579546929518-9e396f3cc809?w=800&auto=format&fit=crop&q=80',
    timestamp: '10:05 - June 17, 2026',
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
      name: 'Pejman Moradi',
      avatarUrl: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=100&auto=format&fit=crop&q=80',
      role: 'UX Designer'
    },
    type: 'audio' as const,
    content: 'Voice note detailing the one-way messages scenario in topics and how comments are implemented on each post card.',
    mediaUrl: 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3',
    duration: '06:12',
    timestamp: '09:30 - June 17, 2026',
    likesCount: 15,
    liked: true,
    comments: [
      { id: 401, authorName: 'Ali Karimi', text: 'The audio file was very clear. Thanks.', timestamp: '09:45' }
    ],
    reactions: [
      { emoji: '👏', count: 5, reacted: false }
    ]
  }
]

const mockPosts = ref<Post[]>([])

// Language and mock data watcher
watch(() => languageStore.currentLanguage, (newLang) => {
  if (newLang === 'en') {
    Object.assign(mockUser, enInitialUser)
    mockChats.splice(0, mockChats.length, ...enMockChats)
    mockTopics.value = JSON.parse(JSON.stringify(enMockTopics))
    mockPosts.value = JSON.parse(JSON.stringify(enInitialPosts))
    simulatorInnerTitle.value = 'Tafakor Support'
    simulatorInputText.value = 'This is a long test message for testing topic message input. You can toggle the modal by clicking the expand button at the top right.'
  } else {
    Object.assign(mockUser, initialUser)
    mockChats.splice(0, mockChats.length, ...faMockChats)
    mockTopics.value = JSON.parse(JSON.stringify(faMockTopics))
    mockPosts.value = JSON.parse(JSON.stringify(faInitialPosts))
    simulatorInnerTitle.value = 'پشتیبانی تفکر'
    simulatorInputText.value = 'این یک متن تستی طولانی و چند سطری برای تست و بررسی کامپوننت ورودی پیام تاپیک است.\nشما می‌توانید با استفاده از دکمه بزرگ‌نمایی که در بالا سمت راست ظاهر می‌شود، این فیلد را به یک مودال تمام‌صفحه تبدیل کنید.\nاین مودال تا ۸۰ درصد صفحه را می‌گیرد تا بتوانید متن‌های طولانی را به راحتی ویرایش و مدیریت نمایید.\nاین متن دارای سطرها و کاراکترهای زیادی است و دکمه اکسپند را فعال می‌کند.'
  }
}, { immediate: true })

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

    // Update topic description with content of new first post, or fallback if empty
    if (mockTopics.value.length > 0) {
      const topicIndex = mockTopics.value.findIndex(t => t.id === 1)
      if (topicIndex !== -1 && mockTopics.value[topicIndex]) {
        if (mockPosts.value.length > 0 && mockPosts.value[0]) {
          mockTopics.value[topicIndex]!.description = mockPosts.value[0]!.content || ''
        } else {
          mockTopics.value[topicIndex]!.description = languageStore.t(
            'درخواست راهنمایی در مورد دیزاین سیستم پلتفرم',
            'Help request regarding the platform design system'
          )
        }
      }
    }
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
  mockPosts.value.push(newPost)
  logEvent('Post: Simulated New Post Received', newPost)

  // Update topic description with content of new post
  if (mockTopics.value.length > 0) {
    const topicIndex = mockTopics.value.findIndex(t => t.id === 1)
    if (topicIndex !== -1 && mockTopics.value[topicIndex]) {
      mockTopics.value[topicIndex]!.description = newPost.content
    }
  }
}

const resetPosts = () => {
  mockPosts.value = JSON.parse(
    JSON.stringify(languageStore.isFa ? faInitialPosts : enInitialPosts)
  )
  logEvent('Post: Feed Reset to Default', {})
}

// LoadingDialog simulation state
const simulatorLoadingIsOpen = ref(false)
const simulatorLoadingProgress = ref(0)
const simulatorLoadingStatus = ref<'idle' | 'uploading' | 'validating' | 'importing' | 'completed' | 'failed'>('idle')
const simulatorLoadingIsProcessing = ref(true)
let simulatorLoadingIntervalId: any = null

const startLoadingSimulation = (shouldSucceed = true) => {
  // Clear any existing interval
  if (simulatorLoadingIntervalId) {
    clearInterval(simulatorLoadingIntervalId)
  }
  
  simulatorLoadingIsOpen.value = true
  simulatorLoadingProgress.value = 0
  simulatorLoadingStatus.value = 'uploading'
  simulatorLoadingIsProcessing.value = true
  logEvent('LoadingDialog: Simulation Started', { shouldSucceed })
  
  simulatorLoadingIntervalId = setInterval(() => {
    if (simulatorLoadingProgress.value < 100) {
      simulatorLoadingProgress.value += 5
      
      // Update statuses based on progress
      if (simulatorLoadingProgress.value >= 25 && simulatorLoadingProgress.value < 60) {
        simulatorLoadingStatus.value = 'validating'
      } else if (simulatorLoadingProgress.value >= 60 && simulatorLoadingProgress.value < 90) {
        simulatorLoadingStatus.value = 'importing'
      } else if (simulatorLoadingProgress.value >= 90) {
        if (shouldSucceed) {
          simulatorLoadingStatus.value = 'completed'
        } else {
          simulatorLoadingStatus.value = 'failed'
          simulatorLoadingIsProcessing.value = false
          clearInterval(simulatorLoadingIntervalId)
          logEvent('LoadingDialog: Simulation Failed at Import stage', {})
          return
        }
      }
    } else {
      // Completed successfully
      simulatorLoadingIsProcessing.value = false
      clearInterval(simulatorLoadingIntervalId)
      logEvent('LoadingDialog: Simulation Completed Successfully', {})
    }
  }, 200)
}

const stopLoadingSimulation = () => {
  if (simulatorLoadingIntervalId) {
    clearInterval(simulatorLoadingIntervalId)
  }
  simulatorLoadingIsOpen.value = false
  simulatorLoadingProgress.value = 0
  simulatorLoadingStatus.value = 'idle'
  simulatorLoadingIsProcessing.value = false
  logEvent('LoadingDialog: Simulation Closed/Reset', {})
}

// ConfirmModal simulation state
const simulatorConfirmIsOpen = ref(false)
const simulatorConfirmTitle = ref('')
const simulatorConfirmDescription = ref('')
const simulatorConfirmConfirmText = ref('')
const simulatorConfirmCancelText = ref('')
const simulatorConfirmVariant = ref<'destructive' | 'warning' | 'info'>('destructive')
const simulatorConfirmPost = ref<any | null>(null)

const openConfirmSimulation = (variant: 'destructive' | 'warning' | 'info') => {
  simulatorConfirmPost.value = null
  simulatorConfirmVariant.value = variant
  if (variant === 'destructive') {
    simulatorConfirmTitle.value = languageStore.isFa ? 'حذف تاپیک تستی؟' : 'Delete Test Topic?'
    simulatorConfirmDescription.value = languageStore.isFa 
      ? 'با حذف این تاپیک تمام داده‌های مربوط به آن به صورت دائمی از بین خواهد رفت.' 
      : 'Deleting this topic will permanently delete all associated data.'
    simulatorConfirmConfirmText.value = languageStore.isFa ? 'تایید و حذف' : 'Confirm & Delete'
    simulatorConfirmCancelText.value = languageStore.isFa ? 'انصراف' : 'Cancel'
  } else if (variant === 'warning') {
    simulatorConfirmTitle.value = languageStore.isFa ? 'خروج از حساب کاربری؟' : 'Logout?'
    simulatorConfirmDescription.value = languageStore.isFa 
      ? 'آیا مطمئن هستید که می‌خواهید از حساب خود خارج شوید؟ نشست فعال شما بسته خواهد شد.' 
      : 'Are you sure you want to log out? Your active session will be terminated.'
    simulatorConfirmConfirmText.value = languageStore.isFa ? 'تایید خروج' : 'Confirm Logout'
    simulatorConfirmCancelText.value = languageStore.isFa ? 'انصراف' : 'Cancel'
  } else {
    simulatorConfirmTitle.value = languageStore.isFa ? 'درون‌ریزی مجدد فایل؟' : 'Re-import File?'
    simulatorConfirmDescription.value = languageStore.isFa 
      ? 'فایل خروجی قبلاً درون‌ریزی شده است. آیا تمایل به درون‌ریزی مجدد و بازنویسی دارید؟' 
      : 'The export file has already been imported. Do you want to re-import and overwrite?'
    simulatorConfirmConfirmText.value = languageStore.isFa ? 'درون‌ریزی مجدد' : 'Re-import'
    simulatorConfirmCancelText.value = languageStore.isFa ? 'انصراف' : 'Cancel'
  }
  simulatorConfirmIsOpen.value = true
  logEvent('ConfirmModal: Opened Simulation', { variant })
}

const openSelectiveDeleteSimulation = () => {
  simulatorConfirmVariant.value = 'destructive'
  simulatorConfirmTitle.value = languageStore.isFa ? 'حذف انتخابی پست از پلتفرم‌ها' : 'Selective Post Deletion'
  simulatorConfirmDescription.value = languageStore.isFa
    ? 'پست انتخابی در تلگرام منتشر شده است. مشخص کنید پیام از کدام سیستم‌ها پاک شود:'
    : 'Selected post is published on Telegram. Specify which platforms it should be deleted from:'
  simulatorConfirmConfirmText.value = languageStore.isFa ? 'ثبت درخواست حذف' : 'Confirm Selective Deletion'
  simulatorConfirmCancelText.value = languageStore.isFa ? 'انصراف' : 'Cancel'
  simulatorConfirmPost.value = {
    id: 101,
    published_platforms: ['telegram'],
    telegram_message_ids: { chat_123: '456' },
    bale_message_ids: {}
  }
  simulatorConfirmIsOpen.value = true
  logEvent('ConfirmModal: Opened Selective Delete Simulation', { post: simulatorConfirmPost.value })
}

// Duplicate Warning Dialog simulation state
const simulatorDuplicateIsOpen = ref(false)
const simulatorDuplicatePostId = ref<string | number | null>(105)
const simulatorDuplicateCreatedAt = ref('۱۴:۳۲ - ۲۷ خرداد ۱۴۰۵')
const simulatorDuplicatePlatforms = ref<string[]>(['telegram', 'bale'])

const openDuplicateWarningSimulation = () => {
  simulatorDuplicateIsOpen.value = true
  logEvent('DuplicateWarningDialog: Opened Simulation', {
    postId: simulatorDuplicatePostId.value,
    createdAt: simulatorDuplicateCreatedAt.value,
    platforms: simulatorDuplicatePlatforms.value
  })
}
</script>

<template>
  <div 
    class="w-full flex justify-center animate-in fade-in duration-300" 
    :class="[languageStore.isFa ? 'text-right' : 'text-left']"
    :dir="languageStore.dir"
  >
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
                @click="handleComponentChange('topic-admins')"
                :class="[
                  'w-full text-right px-3 py-2.5 text-xs font-medium rounded-lg border transition-all flex items-center justify-between cursor-pointer',
                  currentComponent === 'topic-admins' 
                    ? 'bg-primary/5 text-primary border-primary/30 font-bold' 
                    : 'bg-background/20 border-border/40 text-foreground hover:bg-muted/40'
                ]"
              >
                <span class="flex items-center gap-2">
                  <ShieldCheckIcon class="size-3.5" />
                  مودال مدیریت ادمین‌ها (TopicAdminsModal)
                </span>
                <CheckCircle2Icon v-if="currentComponent === 'topic-admins'" class="size-3.5 text-primary" />
              </button>
              <button 
                @click="handleComponentChange('edit-profile-modal')"
                :class="[
                  'w-full text-right px-3 py-2.5 text-xs font-medium rounded-lg border transition-all flex items-center justify-between cursor-pointer',
                  currentComponent === 'edit-profile-modal' 
                    ? 'bg-primary/5 text-primary border-primary/30 font-bold' 
                    : 'bg-background/20 border-border/40 text-foreground hover:bg-muted/40'
                ]"
              >
                <span class="flex items-center gap-2">
                  <UserIcon class="size-3.5" />
                  مودال ویرایش حساب (EditProfileModal)
                </span>
                <CheckCircle2Icon v-if="currentComponent === 'edit-profile-modal'" class="size-3.5 text-primary" />
              </button>
              <button 
                @click="handleComponentChange('changelog-modal')"
                :class="[
                  'w-full text-right px-3 py-2.5 text-xs font-medium rounded-lg border transition-all flex items-center justify-between cursor-pointer',
                  currentComponent === 'changelog-modal' 
                    ? 'bg-primary/5 text-primary border-primary/30 font-bold' 
                    : 'bg-background/20 border-border/40 text-foreground hover:bg-muted/40'
                ]"
              >
                <span class="flex items-center gap-2">
                  <HistoryIcon class="size-3.5 text-primary" />
                  مودال بروزرسانی‌ها (ChangelogModal)
                </span>
                <CheckCircle2Icon v-if="currentComponent === 'changelog-modal'" class="size-3.5 text-primary" />
              </button>
              <button 
                @click="handleComponentChange('ai-refiner-drawer')"
                :class="[
                  'w-full text-right px-3 py-2.5 text-xs font-medium rounded-lg border transition-all flex items-center justify-between cursor-pointer',
                  currentComponent === 'ai-refiner-drawer' 
                    ? 'bg-primary/5 text-primary border-primary/30 font-bold' 
                    : 'bg-background/20 border-border/40 text-foreground hover:bg-muted/40'
                ]"
              >
                <span class="flex items-center gap-2">
                  <Wand2Icon class="size-3.5 text-amber-500" />
                  کشوی دستیار هوش مصنوعی (AIRefinerDrawer)
                </span>
                <CheckCircle2Icon v-if="currentComponent === 'ai-refiner-drawer'" class="size-3.5 text-primary" />
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
                  ورودی پیام تاپیک (جدید)
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
              <button 
                @click="handleComponentChange('loading-dialog')"
                :class="[
                  'w-full text-right px-3 py-2.5 text-xs font-medium rounded-lg border transition-all flex items-center justify-between cursor-pointer',
                  currentComponent === 'loading-dialog' 
                    ? 'bg-primary/5 text-primary border-primary/30 font-bold' 
                    : 'bg-background/20 border-border/40 text-foreground hover:bg-muted/40'
                ]"
              >
                <span class="flex items-center gap-2">
                  <FlaskConicalIcon class="size-3.5 text-primary" />
                  دیالوگ لودینگ مرحله‌ای (جدید)
                </span>
                <CheckCircle2Icon v-if="currentComponent === 'loading-dialog'" class="size-3.5 text-primary" />
              </button>
              <button 
                @click="handleComponentChange('topic-import')"
                :class="[
                  'w-full text-right px-3 py-2.5 text-xs font-medium rounded-lg border transition-all flex items-center justify-between cursor-pointer',
                  currentComponent === 'topic-import' 
                    ? 'bg-primary/5 text-primary border-primary/30 font-bold' 
                    : 'bg-background/20 border-border/40 text-foreground hover:bg-muted/40'
                ]"
              >
                <span class="flex items-center gap-2">
                  <UploadCloudIcon class="size-3.5 text-primary" />
                  درون‌ریزی تاریخچه کانال (جدید)
                </span>
                <CheckCircle2Icon v-if="currentComponent === 'topic-import'" class="size-3.5 text-primary" />
              </button>
              <button 
                @click="handleComponentChange('confirm-modal')"
                :class="[
                  'w-full text-right px-3 py-2.5 text-xs font-medium rounded-lg border transition-all flex items-center justify-between cursor-pointer',
                  currentComponent === 'confirm-modal' 
                    ? 'bg-primary/5 text-primary border-primary/30 font-bold' 
                    : 'bg-background/20 border-border/40 text-foreground hover:bg-muted/40'
                ]"
              >
                <span class="flex items-center gap-2">
                  <AlertTriangleIcon class="size-3.5 text-primary" />
                  دیالوگ تایید حذف/اقدام (جدید)
                </span>
                <CheckCircle2Icon v-if="currentComponent === 'confirm-modal'" class="size-3.5 text-primary" />
              </button>
              <button 
                @click="handleComponentChange('duplicate-warning-dialog')"
                :class="[
                  'w-full text-right px-3 py-2.5 text-xs font-medium rounded-lg border transition-all flex items-center justify-between cursor-pointer',
                  currentComponent === 'duplicate-warning-dialog' 
                    ? 'bg-primary/5 text-primary border-primary/30 font-bold' 
                    : 'bg-background/20 border-border/40 text-foreground hover:bg-muted/40'
                ]"
              >
                <span class="flex items-center gap-2">
                  <AlertTriangleIcon class="size-3.5 text-amber-500" />
                  هشدار پیام تکراری (جدید)
                </span>
                <CheckCircle2Icon v-if="currentComponent === 'duplicate-warning-dialog'" class="size-3.5 text-primary" />
              </button>
              <button 
                @click="handleComponentChange('donation-card')"
                :class="[
                  'w-full text-right px-3 py-2.5 text-xs font-medium rounded-lg border transition-all flex items-center justify-between cursor-pointer',
                  currentComponent === 'donation-card' 
                    ? 'bg-primary/5 text-primary border-primary/30 font-bold' 
                    : 'bg-background/20 border-border/40 text-foreground hover:bg-muted/40'
                ]"
              >
                <span class="flex items-center gap-2">
                  <HeartIcon class="size-3.5 text-primary fill-primary/20" />
                  کارت مهربانی (DonationCard - تب مهربانی) ✨
                </span>
                <CheckCircle2Icon v-if="currentComponent === 'donation-card'" class="size-3.5 text-primary" />
              </button>
              <button 
                @click="handleComponentChange('donation-chat-card')"
                :class="[
                  'w-full text-right px-3 py-2.5 text-xs font-medium rounded-lg border transition-all flex items-center justify-between cursor-pointer',
                  currentComponent === 'donation-chat-card' 
                    ? 'bg-primary/5 text-primary border-primary/30 font-bold' 
                    : 'bg-background/20 border-border/40 text-foreground hover:bg-muted/40'
                ]"
              >
                <span class="flex items-center gap-2">
                  <MessageCircleIcon class="size-3.5 text-emerald-500" />
                  کارت پویش داخل تاپیک (DonationChatCard) 💬
                </span>
                <CheckCircle2Icon v-if="currentComponent === 'donation-chat-card'" class="size-3.5 text-primary" />
              </button>
              <button 
                @click="handleComponentChange('create-donation-dialog')"
                :class="[
                  'w-full text-right px-3 py-2.5 text-xs font-medium rounded-lg border transition-all flex items-center justify-between cursor-pointer',
                  currentComponent === 'create-donation-dialog' 
                    ? 'bg-primary/5 text-primary border-primary/30 font-bold' 
                    : 'bg-background/20 border-border/40 text-foreground hover:bg-muted/40'
                ]"
              >
                <span class="flex items-center gap-2">
                  <HeartIcon class="size-3.5 text-rose-500 fill-rose-500/20" />
                  دیالوگ ایجاد پویش (CreateDonationDialog) 🚀
                </span>
                <CheckCircle2Icon v-if="currentComponent === 'create-donation-dialog'" class="size-3.5 text-primary" />
              </button>
              <button 
                @click="handleComponentChange('under-dev')"
                :class="[
                  'w-full text-right px-3 py-2.5 text-xs font-medium rounded-lg border transition-all flex items-center justify-between cursor-pointer',
                  currentComponent === 'under-dev' 
                    ? 'bg-primary/5 text-primary border-primary/30 font-bold' 
                    : 'bg-background/20 border-border/40 text-foreground hover:bg-muted/40'
                ]"
              >
                <span class="flex items-center gap-2">
                  <ConstructionIcon class="size-3.5 text-primary" />
                  کارت در حال توسعه (UnderDevelopment) 🚀
                </span>
                <CheckCircle2Icon v-if="currentComponent === 'under-dev'" class="size-3.5 text-primary" />
              </button>
            </div>
          </div>
        </div>

        <!-- Main Testing Sandbox -->
        <div class="lg:col-span-3 flex flex-col gap-6">
          
          <!-- Horizontal Settings Panel -->
          <div class="w-full bg-card/30 border border-border/60 rounded-xl p-5 shadow-xs flex flex-col gap-5">
            <div class="flex items-center justify-between border-b border-border/40 pb-3 flex-wrap gap-3">
              <div class="flex items-center gap-2">
                <h2 class="text-xs font-extrabold border-r-4 border-primary pr-2 leading-none text-foreground/90">تنظیمات و وضعیت شبیه‌ساز</h2>
                <Badge variant="secondary" class="text-[9px] px-2 py-0.5 border border-border/50 text-muted-foreground font-mono">Simulator Controls</Badge>
              </div>

              <!-- UnderDevelopmentCard Mode Tabs directly in header -->
              <Tabs v-if="currentComponent === 'under-dev'" v-model="underDevActiveTab" class="w-full sm:w-auto">
                <TabsList class="grid grid-cols-3 bg-muted/60 p-1 rounded-xl h-8 w-full sm:w-80">
                  <TabsTrigger value="preview" class="text-[11px] font-bold px-2.5 rounded-lg flex items-center gap-1.5 data-[state=active]:bg-background data-[state=active]:shadow-xs">
                    <EyeIcon class="size-3" />
                    <span>{{ languageStore.t('پیش‌نمایش زنده', 'Live Preview') }}</span>
                  </TabsTrigger>
                  <TabsTrigger value="code" class="text-[11px] font-bold px-2.5 rounded-lg flex items-center gap-1.5 data-[state=active]:bg-background data-[state=active]:shadow-xs">
                    <TerminalIcon class="size-3" />
                    <span>{{ languageStore.t('کد آماده (Vue)', 'Copy Code') }}</span>
                  </TabsTrigger>
                  <TabsTrigger value="presets" class="text-[11px] font-bold px-2.5 rounded-lg flex items-center gap-1.5 data-[state=active]:bg-background data-[state=active]:shadow-xs">
                    <SparklesIcon class="size-3" />
                    <span>{{ languageStore.t('قالب‌های آماده', 'Presets') }}</span>
                  </TabsTrigger>
                </TabsList>
              </Tabs>
            </div>

            <!-- Global Configurations (Horizontal Grid) -->
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 items-start">
              <!-- Language Selection -->
              <div class="flex flex-col gap-2">
                <Label class="text-[10px] font-semibold text-muted-foreground block">زبان و جهت چیدمان:</Label>
                <div class="grid grid-cols-2 gap-1 bg-muted/60 p-1 rounded-lg border border-border/40">
                  <button 
                    @click="languageStore.setLanguage('fa')"
                    :class="[
                      'flex flex-col items-center justify-center py-1.5 rounded-md text-[9px] font-medium transition-colors outline-none cursor-pointer',
                      languageStore.isFa ? 'bg-background text-foreground shadow-xs font-bold' : 'text-muted-foreground hover:text-foreground'
                    ]"
                  >
                    فارسی (RTL)
                  </button>
                  <button 
                    @click="languageStore.setLanguage('en')"
                    :class="[
                      'flex flex-col items-center justify-center py-1.5 rounded-md text-[9px] font-medium transition-colors outline-none cursor-pointer',
                      languageStore.isEn ? 'bg-background text-foreground shadow-xs font-bold' : 'text-muted-foreground hover:text-foreground'
                    ]"
                  >
                    English (LTR)
                  </button>
                </div>
              </div>

              <!-- Viewport Width Controls -->
              <div class="flex flex-col gap-2">
                <Label class="text-[10px] font-semibold text-muted-foreground block">اندازه پنجره نمایشگر:</Label>
                <div class="grid grid-cols-3 gap-1 bg-muted/60 p-1 rounded-lg border border-border/40">
                  <button 
                    @click="viewportWidth = '375px'"
                    :class="[
                      'flex flex-col items-center justify-center py-1 rounded-md text-[9px] font-medium transition-colors outline-none cursor-pointer',
                      viewportWidth === '375px' ? 'bg-background text-foreground shadow-xs font-bold' : 'text-muted-foreground hover:text-foreground'
                    ]"
                  >
                    موبایل
                  </button>
                  <button 
                    @click="viewportWidth = '768px'"
                    :class="[
                      'flex flex-col items-center justify-center py-1 rounded-md text-[9px] font-medium transition-colors outline-none cursor-pointer',
                      viewportWidth === '768px' ? 'bg-background text-foreground shadow-xs font-bold' : 'text-muted-foreground hover:text-foreground'
                    ]"
                  >
                    تبلت
                  </button>
                  <button 
                    @click="viewportWidth = '100%'"
                    :class="[
                      'flex flex-col items-center justify-center py-1 rounded-md text-[9px] font-medium transition-colors outline-none cursor-pointer',
                      viewportWidth === '100%' ? 'bg-background text-foreground shadow-xs font-bold' : 'text-muted-foreground hover:text-foreground'
                    ]"
                  >
                    دسکتاپ
                  </button>
                </div>
              </div>

              <!-- Viewport Background Controls -->
              <div class="flex flex-col gap-2">
                <Label class="text-[10px] font-semibold text-muted-foreground block">پس‌زمینه شبیه‌ساز (تست بلور):</Label>
                <div class="grid grid-cols-2 gap-1 bg-muted/60 p-1 rounded-lg border border-border/40">
                  <button 
                    @click="sandboxBg = 'default'; logEvent('Sandbox Background: Default', {})"
                    :class="[
                      'px-2 py-1 rounded-md text-[9px] font-semibold transition-all cursor-pointer outline-none border border-transparent',
                      sandboxBg === 'default'
                        ? 'bg-background text-primary font-bold shadow-xs'
                        : 'text-muted-foreground hover:text-foreground'
                    ]"
                  >
                    ساده
                  </button>
                  <button 
                    @click="sandboxBg = 'gradient'; logEvent('Sandbox Background: Colorful Gradient', {})"
                    :class="[
                      'px-2 py-1 rounded-md text-[9px] font-semibold transition-all cursor-pointer outline-none border border-transparent',
                      sandboxBg === 'gradient'
                        ? 'bg-background text-primary font-bold shadow-xs'
                        : 'text-muted-foreground hover:text-foreground'
                    ]"
                  >
                    گرادینت
                  </button>
                  <button 
                    @click="sandboxBg = 'grid'; logEvent('Sandbox Background: Figma Grid', {})"
                    :class="[
                      'px-2 py-1 rounded-md text-[9px] font-semibold transition-all cursor-pointer outline-none border border-transparent',
                      sandboxBg === 'grid'
                        ? 'bg-background text-primary font-bold shadow-xs'
                        : 'text-muted-foreground hover:text-foreground'
                    ]"
                  >
                    شبکه‌ای
                  </button>
                  <button 
                    @click="sandboxBg = 'image'; logEvent('Sandbox Background: Abstract Canvas', {})"
                    :class="[
                      'px-2 py-1 rounded-md text-[9px] font-semibold transition-all cursor-pointer outline-none border border-transparent',
                      sandboxBg === 'image'
                        ? 'bg-background text-primary font-bold shadow-xs'
                        : 'text-muted-foreground hover:text-foreground'
                    ]"
                  >
                    تصویر
                  </button>
                </div>
              </div>

              <!-- Component Active State Controls -->
              <div class="flex flex-col gap-2">
                <Label class="text-[10px] font-semibold text-muted-foreground block">وضعیت کامپوننت:</Label>
                <div class="grid grid-cols-2 gap-1 bg-muted/60 p-1 rounded-lg border border-border/40">
                  <button 
                    v-for="state in availableStates"
                    :key="state"
                    @click="activeState = state"
                    :class="[
                      'px-2 py-1 rounded-md text-[9px] font-semibold transition-all cursor-pointer outline-none flex items-center justify-center gap-1.5 border border-transparent',
                      activeState === state 
                        ? 'bg-background text-primary font-bold shadow-xs' 
                        : 'text-muted-foreground hover:text-foreground'
                    ]"
                  >
                    <span>
                      {{ 
                        state === 'idle' ? 'فعال (Idle)' :
                        state === 'loading' ? 'لودینگ' :
                        state === 'error' ? 'خطا (Error)' : 
                        state === 'empty' ? 'خالی' : 'موفق' 
                      }}
                    </span>
                    <span class="size-1.5 rounded-full" 
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
            </div>

            <!-- Component-Specific Configurations Section -->
            <div 
              v-if="currentComponent === 'header' || currentComponent === 'nav' || currentComponent === 'topic' || currentComponent === 'search' || currentComponent === 'profile-option' || currentComponent === 'profile-card-header' || currentComponent === 'post' || currentComponent === 'create-topic-modal' || currentComponent === 'bot-connection' || currentComponent === 'topic-input' || currentComponent === 'topic-edit' || currentComponent === 'topic-connections' || currentComponent === 'loading-dialog' || currentComponent === 'topic-import' || currentComponent === 'confirm-modal' || currentComponent === 'under-dev' || currentComponent === 'donation-chat-card' || currentComponent === 'create-donation-dialog'"
              class="border-t border-border/40 pt-4 mt-1 flex flex-col gap-3"
            >
              <Label class="text-[10.5px] font-extrabold text-foreground/80 block">تنظیمات اختصاصی کامپوننت {{ currentComponentFile }}:</Label>
              
              <!-- UnderDevelopmentCard Specific Controls -->
              <div v-if="currentComponent === 'under-dev'" class="flex flex-col gap-4">
                <!-- Pattern style & speed (Shadcn Tabs with rounded-lg active pill) -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div class="flex flex-col gap-1.5">
                    <Label class="text-[10px] text-muted-foreground">سبک پترن متحرک:</Label>
                    <Tabs v-model="simulatorUnderDevPattern" class="w-full">
                      <TabsList class="grid grid-cols-3 w-full bg-muted/60 p-1 rounded-xl h-8">
                        <TabsTrigger value="stripes" class="text-[11px] rounded-lg font-bold data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-xs">
                          خطوط مورب
                        </TabsTrigger>
                        <TabsTrigger value="grid" class="text-[11px] rounded-lg font-bold data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-xs">
                          شبکه گرید
                        </TabsTrigger>
                        <TabsTrigger value="dots" class="text-[11px] rounded-lg font-bold data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-xs">
                          ماتریکس نقطه‌ای
                        </TabsTrigger>
                      </TabsList>
                    </Tabs>
                  </div>

                  <div class="flex flex-col gap-1.5">
                    <Label class="text-[10px] text-muted-foreground">سرعت حرکت پترن:</Label>
                    <Tabs v-model="simulatorUnderDevSpeed" class="w-full">
                      <TabsList class="grid grid-cols-3 w-full bg-muted/60 p-1 rounded-xl h-8">
                        <TabsTrigger value="slow" class="text-[11px] rounded-lg font-bold data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-xs">
                          آرام
                        </TabsTrigger>
                        <TabsTrigger value="normal" class="text-[11px] rounded-lg font-bold data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-xs">
                          معمولی
                        </TabsTrigger>
                        <TabsTrigger value="fast" class="text-[11px] rounded-lg font-bold data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-xs">
                          سریع
                        </TabsTrigger>
                      </TabsList>
                    </Tabs>
                  </div>
                </div>

                <!-- Icon Switcher (Shadcn rounded pill grid) -->
                <div class="flex flex-col gap-1.5">
                  <Label class="text-[10px] text-muted-foreground">انتخاب آیکون لوسید اختصاصی:</Label>
                  <div class="grid grid-cols-2 md:grid-cols-5 gap-1.5 bg-muted/60 p-1 rounded-xl border border-border/40 text-xs">
                    <button
                      @click="simulatorUnderDevIconName = 'construction'"
                      :class="[
                        'flex items-center justify-center gap-1.5 py-1.5 px-2 rounded-lg transition-all cursor-pointer text-[11px]',
                        simulatorUnderDevIconName === 'construction' ? 'bg-background text-primary font-bold shadow-xs border border-border/40' : 'text-muted-foreground hover:text-foreground'
                      ]"
                    >
                      <ConstructionIcon class="size-3.5" />
                      <span>ساخت‌و‌ساز</span>
                    </button>
                    <button
                      @click="simulatorUnderDevIconName = 'rocket'"
                      :class="[
                        'flex items-center justify-center gap-1.5 py-1.5 px-2 rounded-lg transition-all cursor-pointer text-[11px]',
                        simulatorUnderDevIconName === 'rocket' ? 'bg-background text-primary font-bold shadow-xs border border-border/40' : 'text-muted-foreground hover:text-foreground'
                      ]"
                    >
                      <RocketIcon class="size-3.5" />
                      <span>موشک / پرتاب</span>
                    </button>
                    <button
                      @click="simulatorUnderDevIconName = 'wrench'"
                      :class="[
                        'flex items-center justify-center gap-1.5 py-1.5 px-2 rounded-lg transition-all cursor-pointer text-[11px]',
                        simulatorUnderDevIconName === 'wrench' ? 'bg-background text-primary font-bold shadow-xs border border-border/40' : 'text-muted-foreground hover:text-foreground'
                      ]"
                    >
                      <WrenchIcon class="size-3.5" />
                      <span>ابزار / آچار</span>
                    </button>
                    <button
                      @click="simulatorUnderDevIconName = 'sparkles'"
                      :class="[
                        'flex items-center justify-center gap-1.5 py-1.5 px-2 rounded-lg transition-all cursor-pointer text-[11px]',
                        simulatorUnderDevIconName === 'sparkles' ? 'bg-background text-primary font-bold shadow-xs border border-border/40' : 'text-muted-foreground hover:text-foreground'
                      ]"
                    >
                      <SparklesIcon class="size-3.5" />
                      <span>درخشش AI</span>
                    </button>
                    <button
                      @click="simulatorUnderDevIconName = 'layers'"
                      :class="[
                        'flex items-center justify-center gap-1.5 py-1.5 px-2 rounded-lg transition-all cursor-pointer text-[11px]',
                        simulatorUnderDevIconName === 'layers' ? 'bg-background text-primary font-bold shadow-xs border border-border/40' : 'text-muted-foreground hover:text-foreground'
                      ]"
                    >
                      <LayersIcon class="size-3.5" />
                      <span>لایه‌ها</span>
                    </button>
                  </div>
                </div>

                <!-- Text Controls in Live Inputs (Full Copywriting & Content Editor) -->
                <div class="rounded-xl border border-border/50 bg-background/30 p-3.5 flex flex-col gap-3">
                  <div class="flex items-center justify-between">
                    <Label class="text-[11px] font-bold text-foreground flex items-center gap-1.5">
                      <PencilIcon class="size-3.5 text-primary" />
                      <span>ویرایش آنلاین متون و محتوا (همگام با کد خروجی):</span>
                    </Label>
                    <span class="text-[9.5px] text-muted-foreground font-mono">Realtime Code Sync</span>
                  </div>

                  <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div class="flex flex-col gap-1">
                      <Label class="text-[10px] text-muted-foreground">عنوان کارت (title):</Label>
                      <Input v-model="simulatorUnderDevTitle" placeholder="مثال: در حال توسعه" class="h-8 text-xs bg-background/50" />
                    </div>
                    <div class="flex flex-col gap-1">
                      <Label class="text-[10px] text-muted-foreground">تخمین نسخه یا زمان (eta):</Label>
                      <Input v-model="simulatorUnderDevEta" placeholder="مثال: نسخه ۲.۵ یا پاییز ۱۴۰۵" class="h-8 text-xs bg-background/50" />
                    </div>
                  </div>

                  <div class="flex flex-col gap-1">
                    <Label class="text-[10px] text-muted-foreground">توضیحات کارت (description):</Label>
                    <Input v-model="simulatorUnderDevDesc" placeholder="توضیح کوتاه درباره این قابلیت..." class="h-8 text-xs bg-background/50" />
                  </div>

                  <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div class="flex flex-col gap-1">
                      <Label class="text-[10px] text-muted-foreground">متن دکمه اقدام (action-text):</Label>
                      <Input v-model="simulatorUnderDevActionText" placeholder="مثال: اطلاع‌رسانی هنگام انتشار (خالی = بدون دکمه)" class="h-8 text-xs bg-background/50" />
                    </div>
                    <div class="flex flex-col gap-1">
                      <Label class="text-[10px] text-muted-foreground">متن دکمه بازگشت (back-button-text):</Label>
                      <Input v-model="simulatorUnderDevBackText" placeholder="پیش‌فرض: بازگشت" class="h-8 text-xs bg-background/50" />
                    </div>
                  </div>

                  <!-- Feature Tags Editor -->
                  <div class="flex flex-col gap-1.5 pt-1 border-t border-border/30">
                    <div class="flex items-center justify-between">
                      <Label class="text-[10px] text-muted-foreground">آیتم‌های چک‌لیست ویژگی‌ها (features):</Label>
                      <span class="text-[9px] text-muted-foreground">{{ simulatorUnderDevFeatures.length }} مورد</span>
                    </div>

                    <!-- Tags list -->
                    <div class="flex flex-wrap gap-1.5 items-center min-h-7">
                      <div 
                        v-for="(feat, fIdx) in simulatorUnderDevFeatures" 
                        :key="fIdx"
                        class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-lg bg-primary/10 border border-primary/20 text-foreground text-[10.5px] font-medium"
                      >
                        <span>{{ feat }}</span>
                        <button 
                          @click="removeUnderDevFeature(fIdx)" 
                          class="hover:text-destructive text-muted-foreground transition-colors cursor-pointer text-xs leading-none"
                          title="حذف"
                        >×</button>
                      </div>
                      <span v-if="simulatorUnderDevFeatures.length === 0" class="text-[10px] text-muted-foreground italic">
                        چک‌لیستی فعال نیست.
                      </span>
                    </div>

                    <!-- Add Tag Input -->
                    <div class="flex items-center gap-2 mt-1">
                      <Input 
                        v-model="newUnderDevFeatureInput" 
                        @keydown.enter.prevent="addUnderDevFeature"
                        placeholder="افزودن ویژگی جدید (اینتر بزنید)..." 
                        class="h-7 text-[11px] bg-background/50 flex-1" 
                      />
                      <Button 
                        @click="addUnderDevFeature" 
                        size="xs" 
                        variant="secondary" 
                        class="h-7 px-3 text-[10.5px] font-semibold cursor-pointer rounded-lg shadow-2xs"
                      >
                        افزودن
                      </Button>
                    </div>
                  </div>
                </div>

                <!-- Buttons & Options Toggle -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <button
                    @click="simulatorUnderDevShowBack = !simulatorUnderDevShowBack"
                    class="w-full text-right px-3 py-2 text-xs rounded-lg border transition-all flex items-center justify-between bg-background/20 border-border/40 text-foreground hover:bg-muted/40 cursor-pointer"
                  >
                    <span>نمایش دکمه بازگشت</span>
                    <Badge :variant="simulatorUnderDevShowBack ? 'default' : 'outline'" class="text-[9px] px-1.5 h-4">
                      {{ simulatorUnderDevShowBack ? 'نمایش' : 'مخفی' }}
                    </Badge>
                  </button>

                  <button
                    @click="simulatorUnderDevFeatures = simulatorUnderDevFeatures.length > 0 ? [] : ['آمار زنده تاپیک‌ها', 'پیشنهاد هوشمند محتوا', 'گزارش‌های تحلیلی']"
                    class="w-full text-right px-3 py-2 text-xs rounded-lg border transition-all flex items-center justify-between bg-background/20 border-border/40 text-foreground hover:bg-muted/40 cursor-pointer"
                  >
                    <span>باکس ویژگی‌ها</span>
                    <Badge :variant="simulatorUnderDevFeatures.length > 0 ? 'secondary' : 'outline'" class="text-[9px] px-1.5 h-4">
                      {{ simulatorUnderDevFeatures.length > 0 ? 'فعال' : 'مخفی' }}
                    </Badge>
                  </button>
                </div>
              </div>
              
              <!-- Header Specific Controls -->
              <div v-if="currentComponent === 'header'" class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <button 
                  @click="simulatorIsInnerPage = false"
                  :class="[
                    'w-full text-right px-3 py-2.5 text-xs font-medium rounded-lg border transition-all flex items-center justify-between cursor-pointer',
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
                    'w-full text-right px-3 py-2.5 text-xs font-medium rounded-lg border transition-all flex items-center justify-between cursor-pointer',
                    simulatorIsInnerPage 
                      ? 'bg-primary/5 text-primary border-primary/30 font-bold' 
                      : 'bg-background/20 border-border/40 text-foreground hover:bg-muted/40'
                  ]"
                >
                  <span>صفحه داخلی (بک فعال)</span>
                  <Badge variant="secondary" class="text-[9px] px-1.5 h-4 text-muted-foreground">Inner</Badge>
                </button>
              </div>

              <!-- Navigation Specific Controls -->
              <div v-if="currentComponent === 'nav'" class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
                <button 
                  @click="simulatorActiveTab = 'home'; logEvent('Nav: Toggled via Sidebar', { tab: 'home' })"
                  :class="[
                    'w-full text-right px-3 py-2.5 text-xs font-medium rounded-lg border transition-all flex items-center justify-between cursor-pointer',
                    simulatorActiveTab === 'home' 
                      ? 'bg-primary/5 text-primary border-primary/30 font-bold' 
                      : 'bg-background/20 border-border/40 text-foreground hover:bg-muted/40'
                  ]"
                >
                  <span>صفحه خانه (خانه)</span>
                  <HomeIcon class="size-3.5 text-muted-foreground" />
                </button>
                <button 
                  @click="simulatorActiveTab = 'donate'; logEvent('Nav: Toggled via Sidebar', { tab: 'donate' })"
                  :class="[
                    'w-full text-right px-3 py-2.5 text-xs font-medium rounded-lg border transition-all flex items-center justify-between cursor-pointer',
                    simulatorActiveTab === 'donate' 
                      ? 'bg-primary/5 text-primary border-primary/30 font-bold' 
                      : 'bg-background/20 border-border/40 text-foreground hover:bg-muted/40'
                  ]"
                >
                  <span>صفحه اهدا (نیکوکاری)</span>
                  <HandHeartIcon class="size-3.5 text-muted-foreground" />
                </button>
                <button 
                  @click="simulatorActiveTab = 'marketplace'; logEvent('Nav: Toggled via Sidebar', { tab: 'marketplace' })"
                  :class="[
                    'w-full text-right px-3 py-2.5 text-xs font-medium rounded-lg border transition-all flex items-center justify-between cursor-pointer',
                    simulatorActiveTab === 'marketplace' 
                      ? 'bg-primary/5 text-primary border-primary/30 font-bold' 
                      : 'bg-background/20 border-border/40 text-foreground hover:bg-muted/40'
                  ]"
                >
                  <span>بازارچه افزونه‌ها</span>
                  <LayersIcon class="size-3.5 text-muted-foreground" />
                </button>
                <button 
                  @click="simulatorActiveTab = 'profile'; logEvent('Nav: Toggled via Sidebar', { tab: 'profile' })"
                  :class="[
                    'w-full text-right px-3 py-2.5 text-xs font-medium rounded-lg border transition-all flex items-center justify-between cursor-pointer',
                    simulatorActiveTab === 'profile' 
                      ? 'bg-primary/5 text-primary border-primary/30 font-bold' 
                      : 'bg-background/20 border-border/40 text-foreground hover:bg-muted/40'
                  ]"
                >
                  <span>صفحه پروفایل (کاربر)</span>
                  <UserIcon class="size-3.5 text-muted-foreground" />
                </button>
              </div>

              <!-- Topic Specific Controls -->
              <div v-if="currentComponent === 'topic'" class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Button 
                  size="sm" 
                  @click="addSimulatedMessage"
                  class="w-full text-xs font-semibold cursor-pointer h-9.5"
                >
                  شبیه‌سازی دریافت پیام جدید
                </Button>
                <Button 
                  size="sm" 
                  variant="outline"
                  @click="mockTopics.forEach(t => t.unreadCount = 0); logEvent('Topic: All Marked as Read', {})"
                  class="w-full text-xs font-semibold cursor-pointer h-9.5"
                >
                  خوانده شدن همه کارت‌ها
                </Button>
              </div>

              <!-- Search Specific Controls -->
              <div v-if="currentComponent === 'search'" class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Button 
                  size="sm" 
                  variant="outline"
                  @click="simulatorSearchQuery = 'توسعه'; logEvent('Search: Force Query = توسعه', {})"
                  class="w-full text-xs font-semibold cursor-pointer h-9.5"
                >
                  جستجوی کلمه «توسعه»
                </Button>
                <Button 
                  size="sm" 
                  variant="outline"
                  @click="simulatorSearchQuery = ''; logEvent('Search: Query Cleared via Sandbox', {})"
                  class="w-full text-xs font-semibold cursor-pointer h-9.5"
                >
                  پاک کردن متن جستجو
                </Button>
              </div>

              <!-- Profile Option Specific Controls -->
              <div v-if="currentComponent === 'profile-option'" class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <button 
                  @click="simulatorSettingsBadge = simulatorSettingsBadge ? '' : 'بروزرسانی'"
                  class="w-full text-right px-3 py-2.5 text-xs font-medium rounded-lg border transition-all flex items-center justify-between bg-background/20 border-border/40 text-foreground hover:bg-muted/40 cursor-pointer"
                >
                  <span>نشان‌گر تنظیمات (Settings)</span>
                  <Badge variant="secondary" class="text-[9px] px-1.5 h-4 text-muted-foreground">
                    {{ simulatorSettingsBadge || 'بدون نشان‌گر' }}
                  </Badge>
                </button>
                <button 
                  @click="simulatorConnectionsBadge = simulatorConnectionsBadge ? '' : '۳ فعال'"
                  class="w-full text-right px-3 py-2.5 text-xs font-medium rounded-lg border transition-all flex items-center justify-between bg-background/20 border-border/40 text-foreground hover:bg-muted/40 cursor-pointer"
                >
                  <span>نشان‌گر اتصال‌ها (Connections)</span>
                  <Badge variant="secondary" class="text-[9px] px-1.5 h-4 text-muted-foreground">
                    {{ simulatorConnectionsBadge || 'بدون نشان‌گر' }}
                  </Badge>
                </button>
                <button 
                  @click="simulatorAiBadge = simulatorAiBadge ? '' : 'جدید'"
                  class="w-full text-right px-3 py-2.5 text-xs font-medium rounded-lg border transition-all flex items-center justify-between bg-background/20 border-border/40 text-foreground hover:bg-muted/40 cursor-pointer"
                >
                  <span>نشان‌گر هوش مصنوعی (AI)</span>
                  <Badge variant="secondary" class="text-[9px] px-1.5 h-4 text-muted-foreground">
                    {{ simulatorAiBadge || 'بدون نشان‌گر' }}
                  </Badge>
                </button>
              </div>

              <!-- Profile Card Specific Controls -->
              <div v-if="currentComponent === 'profile-card-header'" class="grid grid-cols-1 md:grid-cols-2 gap-4 items-end">
                <div class="flex flex-col gap-1.5 text-start">
                  <Label class="text-[9px] text-muted-foreground">نام و نام خانوادگی:</Label>
                  <Input v-model="simulatorProfileCardName" class="h-8.5 text-xs font-semibold" placeholder="نام کاربر" />
                </div>
                <div class="flex flex-col gap-1.5 text-start">
                  <Label class="text-[9px] text-muted-foreground">وضعیت فعالیت:</Label>
                  <div class="grid grid-cols-4 gap-1 bg-muted/65 p-1 rounded-lg border border-border/40">
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

              <!-- Post Specific Controls -->
              <div v-if="currentComponent === 'post'" class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Button 
                  size="sm" 
                  @click="simulateNewPost"
                  class="w-full text-xs font-semibold cursor-pointer h-9.5"
                >
                  شبیه‌سازی دریافت پست جدید
                </Button>
                <Button 
                  size="sm" 
                  variant="outline"
                  @click="resetPosts"
                  class="w-full text-xs font-semibold cursor-pointer h-9.5"
                >
                  ریست کردن لیست پست‌ها
                </Button>
              </div>

              <!-- Create Topic Modal Specific Controls -->
              <div v-if="currentComponent === 'create-topic-modal'" class="grid grid-cols-1 gap-4">
                <Button 
                  size="sm" 
                  @click="simulatorIsModalOpen = true"
                  class="w-full text-xs font-semibold cursor-pointer h-9.5"
                >
                  باز کردن مودال ساخت تاپیک
                </Button>
              </div>

              <!-- Bot Connection Specific Controls -->
              <div v-if="currentComponent === 'bot-connection'" class="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
                <div class="flex flex-col gap-1.5 text-start">
                  <Label class="text-[9px] text-muted-foreground">پلتفرم:</Label>
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
                <div class="flex flex-col gap-1.5 text-start">
                  <Label class="text-[9px] text-muted-foreground">وضعیت اتصال:</Label>
                  <div class="grid grid-cols-4 gap-1 bg-muted/65 p-1 rounded-lg border border-border/40">
                    <button 
                      v-for="st in (['disconnected', 'connecting', 'connected', 'conflict'] as const)"
                      :key="st"
                      @click="simulatorBotStatus = st; logEvent(`Bot: Status set to ${st}`, {})"
                      :class="[
                        'py-1 rounded text-[9px] font-bold transition-all cursor-pointer outline-none border border-transparent',
                        simulatorBotStatus === st 
                          ? 'bg-background text-foreground shadow-xs font-black' 
                          : 'text-muted-foreground hover:text-foreground'
                      ]"
                    >
                      {{ 
                        st === 'disconnected' ? 'قطع' :
                        st === 'connecting' ? 'اتصال' :
                        st === 'connected' ? 'وصل' : 'تداخل'
                      }}
                    </button>
                  </div>
                </div>
                <div class="grid grid-cols-2 gap-2">
                  <Button 
                    size="sm" 
                    variant="outline"
                    @click="simulatorBotStatus = 'conflict'; logEvent('Bot: Simulated sudden disconnection error (conflict)', {})"
                    class="text-[9.5px] font-semibold text-amber-600 border-amber-550/20 hover:bg-amber-500/5 cursor-pointer h-9"
                  >
                    شبیه‌سازی تداخل
                  </Button>
                  <Button 
                    size="sm" 
                    variant="outline"
                    @click="simulatorBotToken = '123456:conflict-token'; logEvent('Bot: Force set conflict token', {})"
                    class="text-[9.5px] font-semibold cursor-pointer h-9"
                  >
                    توکن تداخل‌ساز
                  </Button>
                </div>
              </div>

              <!-- Topic Edit Specific Controls -->
              <div v-if="currentComponent === 'topic-edit'" class="grid grid-cols-1 md:grid-cols-2 gap-4 items-center">
                <p class="text-[9.5px] text-muted-foreground leading-relaxed text-start">
                  با استفاده از فرم پیش‌نمایش می‌توانید عنوان، توضیحات و تصویر تاپیک را ویرایش و ذخیره کنید. دکمه مقابل مقادیر را ریست می‌کند:
                </p>
                <Button 
                  size="sm" 
                  variant="outline"
                  @click="resetSimulatorTopicEdit"
                  class="w-full text-xs font-semibold cursor-pointer h-9.5"
                >
                  بازنشانی مقادیر اولیه تاپیک
                </Button>
              </div>

              <!-- Topic Connections Specific Controls -->
              <div v-if="currentComponent === 'topic-connections'" class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="flex flex-col gap-1.5 text-start">
                  <Label class="text-[9px] text-muted-foreground">وضعیت اتصال ربات تلگرام:</Label>
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
                <div class="flex flex-col gap-1.5 text-start">
                  <Label class="text-[9px] text-muted-foreground">وضعیت اتصال ربات بله:</Label>
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
              <div v-if="currentComponent === 'topic-input'" class="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
                <div class="flex flex-col gap-1.5 text-start">
                  <Label class="text-[9px] text-muted-foreground">سطح دسترسی نوشتن:</Label>
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
                <div class="flex flex-col gap-1.5 text-start md:col-span-2">
                  <Label class="text-[9px] text-muted-foreground">شبیه‌سازی آپلود پیوست:</Label>
                  <div class="grid grid-cols-4 gap-2">
                    <Button size="sm" variant="outline" @click="simulateAddAttachment('image')" class="text-[9.5px] font-semibold py-1 h-8.5 cursor-pointer">تصویر</Button>
                    <Button size="sm" variant="outline" @click="simulateAddAttachment('video')" class="text-[9.5px] font-semibold py-1 h-8.5 cursor-pointer">ویدیو</Button>
                    <Button size="sm" variant="outline" @click="simulateAddAttachment('audio')" class="text-[9.5px] font-semibold py-1 h-8.5 cursor-pointer">صوت</Button>
                    <Button size="sm" variant="outline" @click="simulateAddAttachment('file')" class="text-[9.5px] font-semibold py-1 h-8.5 cursor-pointer">سند/فایل</Button>
                  </div>
                </div>
              </div>

              <!-- LoadingDialog Specific Controls -->
              <div v-if="currentComponent === 'loading-dialog'" class="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
                <div class="flex flex-col gap-1.5 text-start">
                  <Label class="text-[9px] text-muted-foreground">شبیه‌سازی سناریو:</Label>
                  <div class="flex gap-2">
                    <Button 
                      size="sm" 
                      @click="startLoadingSimulation(true)"
                      class="flex-1 text-[10px] font-bold cursor-pointer bg-green-600 hover:bg-green-700 text-white"
                    >
                      شروع شبیه‌سازی موفق
                    </Button>
                    <Button 
                      size="sm" 
                      variant="destructive"
                      @click="startLoadingSimulation(false)"
                      class="flex-1 text-[10px] font-bold cursor-pointer"
                    >
                      شروع شبیه‌سازی خطا
                    </Button>
                  </div>
                </div>
                <div class="flex flex-col gap-1.5 text-start">
                  <Label class="text-[9px] text-muted-foreground">کنترل دیالوگ:</Label>
                  <Button 
                    size="sm" 
                    variant="outline"
                    @click="stopLoadingSimulation"
                    class="w-full text-[10px] font-bold cursor-pointer"
                  >
                    ریست و بستن دیالوگ
                  </Button>
                </div>
                <div class="flex flex-col gap-1 text-[10px] text-muted-foreground bg-muted/40 p-2 rounded-xl border border-border/40">
                  <div class="flex justify-between">
                    <span>وضعیت: {{ simulatorLoadingStatus }}</span>
                    <span>پیشرفت: {{ simulatorLoadingProgress }}%</span>
                  </div>
                  <div class="flex justify-between">
                    <span>در حال پردازش: {{ simulatorLoadingIsProcessing ? 'بله' : 'خیر' }}</span>
                  </div>
                </div>
              </div>

              <!-- TopicImport Specific Controls -->
              <div v-if="currentComponent === 'topic-import'" class="grid grid-cols-1 md:grid-cols-2 gap-4 items-center">
                <p class="text-[9.5px] text-muted-foreground leading-relaxed text-start">
                  این کامپوننت به کاربر امکان می‌دهد فایل نتیجه تلگرام (result.json) را درون‌ریزی کند. کلیک بر روی دکمه شروع در پیش‌نمایش، لودینگ شبیه‌سازی شده را فعال می‌کند.
                </p>
                <div class="flex gap-2">
                  <Button 
                    size="sm" 
                    variant="outline"
                    @click="logEvent('TopicImport: Simulated info request', {})"
                    class="w-full text-xs font-semibold cursor-pointer h-9.5"
                  >
                    مستندات درون‌ریزی
                  </Button>
                </div>
              </div>

              <!-- ConfirmModal Specific Controls -->
              <div v-if="currentComponent === 'confirm-modal'" class="grid grid-cols-1 md:grid-cols-4 gap-4 items-center">
                <div class="flex flex-col gap-1.5 text-start">
                  <Label class="text-[9px] text-muted-foreground">شبیه‌سازی سناریو (نوع دیالوگ):</Label>
                  <div class="flex gap-2 flex-wrap">
                    <Button 
                      size="sm" 
                      variant="destructive"
                      @click="openConfirmSimulation('destructive')"
                      class="text-[10px] font-bold cursor-pointer h-9"
                    >
                      مخرب (حذف تاپیک)
                    </Button>
                    <Button 
                      size="sm" 
                      @click="openConfirmSimulation('warning')"
                      class="text-[10px] font-bold cursor-pointer h-9 bg-amber-600 hover:bg-amber-700 text-white"
                    >
                      هشدار (خروج)
                    </Button>
                    <Button 
                      size="sm" 
                      @click="openConfirmSimulation('info')"
                      class="text-[10px] font-bold cursor-pointer h-9 bg-blue-600 hover:bg-blue-700 text-white"
                    >
                      اطلاعات (درون‌ریزی مجدد)
                    </Button>
                  </div>
                </div>
                <div class="flex flex-col gap-1.5 text-start md:col-span-2">
                  <Label class="text-[9px] text-muted-foreground">مشخصات دیالوگ جاری:</Label>
                  <div class="text-[10px] text-muted-foreground bg-muted/40 p-2.5 rounded-xl border border-border/40 space-y-1">
                    <div class="flex justify-between font-bold">
                      <span>عنوان: {{ simulatorConfirmTitle }}</span>
                      <Badge size="xs" :variant="simulatorConfirmVariant === 'destructive' ? 'destructive' : 'secondary'">
                        {{ simulatorConfirmVariant }}
                      </Badge>
                    </div>
                    <div class="text-[9px] truncate">توضیح: {{ simulatorConfirmDescription }}</div>
                  </div>
                </div>
                <div class="flex flex-col gap-1.5 text-start">
                  <Label class="text-[9px] text-muted-foreground">باز کردن مستقیم:</Label>
                  <Button 
                    size="sm" 
                    variant="outline"
                    @click="simulatorConfirmIsOpen = true"
                    class="text-[10px] font-bold cursor-pointer h-9 w-full"
                  >
                    نمایش مجدد دیالوگ
                  </Button>
                </div>
              </div>

              <!-- DonationChatCard Specific Controls -->
              <div v-if="currentComponent === 'donation-chat-card'" class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 text-start">
                <div class="flex flex-col gap-1">
                  <Label class="text-[9px] text-muted-foreground">دسته‌بندی پویش:</Label>
                  <select 
                    v-model="simulatorChatCardCategory"
                    class="h-8 rounded-lg border border-border/60 bg-background text-xs px-2 font-medium"
                  >
                    <option value="mosque">مسجد</option>
                    <option value="school">مدرسه و آموزش</option>
                    <option value="health">درمانی و سلامت</option>
                    <option value="livelihood">نیازمندان و معیشت</option>
                    <option value="construction">عمرانی و تجهیزات</option>
                    <option value="other">متفرقه</option>
                  </select>
                </div>
                <div class="flex flex-col gap-1">
                  <Label class="text-[9px] text-muted-foreground">جمع‌آوری شده (تومان):</Label>
                  <Input 
                    type="number"
                    v-model.number="simulatorChatCardCollectedAmount"
                    class="h-8 text-xs font-bold font-mono"
                  />
                </div>
                <div class="flex flex-col gap-1">
                  <Label class="text-[9px] text-muted-foreground">مبلغ هدف (تومان):</Label>
                  <Input 
                    type="number"
                    v-model.number="simulatorChatCardTargetAmount"
                    class="h-8 text-xs font-bold font-mono"
                  />
                </div>
                <div class="flex items-center gap-1.5 pt-4">
                  <button 
                    @click="simulatorChatCardAutoPin = !simulatorChatCardAutoPin"
                    class="px-2 py-1 text-[10px] rounded-lg border font-semibold cursor-pointer"
                    :class="simulatorChatCardAutoPin ? 'bg-primary/10 border-primary text-primary font-bold' : 'border-border/60 bg-muted/20 text-muted-foreground'"
                  >
                    {{ simulatorChatCardAutoPin ? 'پین‌شده' : 'عادی' }}
                  </button>
                  <button 
                    @click="simulatorChatCardHasMedia = !simulatorChatCardHasMedia"
                    class="px-2 py-1 text-[10px] rounded-lg border font-semibold cursor-pointer"
                    :class="simulatorChatCardHasMedia ? 'bg-primary/10 border-primary text-primary font-bold' : 'border-border/60 bg-muted/20 text-muted-foreground'"
                  >
                    {{ simulatorChatCardHasMedia ? 'تصویر' : 'بدون مدیا' }}
                  </button>
                  <button 
                    @click="simulatorChatCardIsPreview = !simulatorChatCardIsPreview"
                    class="px-2 py-1 text-[10px] rounded-lg border font-semibold cursor-pointer"
                    :class="simulatorChatCardIsPreview ? 'bg-amber-500/10 border-amber-500 text-amber-600 font-bold' : 'border-border/60 bg-muted/20 text-muted-foreground'"
                  >
                    پیش‌نمایش
                  </button>
                </div>
              </div>

              <!-- CreateDonationDialog Specific Controls -->
              <div v-if="currentComponent === 'create-donation-dialog'" class="grid grid-cols-1 sm:grid-cols-3 gap-3 text-start items-end">
                <div class="flex flex-col gap-1">
                  <Label class="text-[9px] text-muted-foreground">نام تاپیک شبیه‌سازی:</Label>
                  <Input 
                    v-model="simulatorCreateDonationTopicName"
                    class="h-8 text-xs font-medium"
                  />
                </div>
                <div class="flex flex-col gap-1">
                  <Label class="text-[9px] text-muted-foreground">نام ایجادکننده:</Label>
                  <Input 
                    v-model="simulatorCreateDonationAuthorName"
                    class="h-8 text-xs font-medium"
                  />
                </div>
                <Button 
                  size="sm"
                  class="h-8 text-xs font-bold gap-1.5 rounded-lg"
                  @click="isSimulatorCreateDonationOpen = true"
                >
                  <HeartIcon class="size-3.5 fill-current" data-icon="inline-start" />
                  <span>اجرای دیالوگ ساخت پویش</span>
                </Button>
              </div>
            </div>
            
            <!-- Dev Note & Quick Template Buttons (Horizontal flex) -->
            <div class="border-t border-border/45 pt-4 flex flex-col md:flex-row gap-4 items-center justify-between">
              <!-- Dev Note -->
              <div class="flex gap-2 text-[9.5px] leading-relaxed text-muted-foreground text-start flex-1">
                <InfoIcon class="size-3.5 text-primary shrink-0 mt-0.5" />
                <span>تغییر وضعیت یا تغییر ابعاد، رفتار کامپوننت را در یک محدوده عایق و ایزوله شبیه‌ساز شبیه‌سازی می‌کند.</span>
              </div>
              
              <!-- Quick Text templates (only if topic-input is selected) -->
              <div v-if="currentComponent === 'topic-input'" class="flex gap-2 items-center justify-end shrink-0">
                <Label class="text-[9px] text-muted-foreground font-semibold">قالب متن:</Label>
                <button 
                  @click="simulatorInputText = 'این یک متن تستی طولانی و چند سطری برای تست و بررسی کامپوننت ورودی پیام تاپیک است.\nشما می‌توانید با استفاده از دکمه بزرگ‌نمایی که در بالا سمت راست ظاهر می‌شود، این فیلد را به یک مودال تمام‌صفحه تبدیل کنید.\nاین مودال تا ۸۰ درصد صفحه را می‌گیرد تا بتوانید متن‌های طولانی را به راحتی ویرایش و مدیریت نمایید.\nاین متن دارای سطرها و کاراکترهای زیادی است و دکمه اکسپند را فعال می‌کند.'; logEvent('Input: Filled template text', {})"
                  class="px-2.5 py-1 text-[9px] font-bold rounded-lg border border-border/40 hover:bg-muted/40 transition-colors truncate cursor-pointer bg-background/20 text-foreground"
                >
                  قالب متن طولانی
                </button>
                <button 
                  @click="simulatorInputText = ''; simulatorInputAttachments = []; logEvent('Input: Cleared everything', {})"
                  class="px-2.5 py-1 text-[9px] font-bold rounded-lg border border-destructive/20 hover:bg-destructive/5 text-destructive transition-colors cursor-pointer bg-background/20"
                >
                  پاک کردن
                </button>
              </div>
            </div>
          </div>
          
          <!-- Live Preview Sandbox -->
          <div class="bg-card/30 border border-border/60 rounded-lg p-6 shadow-xs flex flex-col items-center">
            <div class="w-full flex justify-between items-center text-[10px] text-muted-foreground mb-4">
              <span class="font-mono">Width: {{ viewportWidth === '100%' ? 'Desktop (Auto)' : viewportWidth }}</span>
              <span class="flex items-center gap-2">
                <span class="bg-primary/10 text-primary px-2 py-0.5 rounded font-mono font-bold select-all">{{ currentComponentFile }}</span>
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
                      @topic-import="handleSimulatorTopicImport"
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
                      <div v-if="simulatorActiveTab === 'home'" key="home" class="flex flex-col items-center gap-2">
                        <div class="size-10 rounded-full bg-primary/10 flex items-center justify-center text-primary">
                          <HomeIcon class="size-5" />
                        </div>
                        <h4 class="text-xs font-extrabold text-foreground mt-1">پیشخوان پلتفرم تفکر (صفحه خانه)</h4>
                        <p class="text-[10px] text-muted-foreground max-w-xs leading-relaxed">
                          به بخش کاربری تفکر خوش آمدید. نویگیشن بار شناور در پایین صفحه قرار گرفته و به شما اجازه جابجایی می‌دهد.
                        </p>
                      </div>
                      <div v-else-if="simulatorActiveTab === 'donate'" key="donate" class="flex flex-col items-center gap-2">
                        <div class="size-10 rounded-full bg-primary/10 flex items-center justify-center text-primary">
                          <HandHeartIcon class="size-5" />
                        </div>
                        <h4 class="text-xs font-extrabold text-foreground mt-1">بخش پویش‌های اهدا و مهربانی (صفحه اهدا)</h4>
                        <p class="text-[10px] text-muted-foreground max-w-xs leading-relaxed">
                          در این بخش می‌توانید پویش‌های فعال نیکوکاری و حمایت‌های مالی را مشاهده و مبالغ دلخواه را اهدا نمایید.
                        </p>
                      </div>
                      <div v-else-if="simulatorActiveTab === 'marketplace'" key="marketplace" class="flex flex-col items-center gap-2">
                        <div class="size-10 rounded-full bg-primary/10 flex items-center justify-center text-primary">
                          <LayersIcon class="size-5" />
                        </div>
                        <h4 class="text-xs font-extrabold text-foreground mt-1">بازارچه افزونه‌های تفکر</h4>
                        <p class="text-[10px] text-muted-foreground max-w-xs leading-relaxed">
                          در این بخش می‌توانید افزونه‌های دلخواه خود را نصب کرده و به تاپیک‌ها متصل نمایید.
                        </p>
                      </div>
                      <div v-else key="profile" class="flex flex-col items-center gap-2">
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
                  :dir="languageStore.dir"
                >
                  <div class="flex items-center justify-between border-b border-border/40 pb-3 mb-1 px-1">
                    <h3 class="text-xs font-extrabold text-foreground">{{ languageStore.t('منوی کاربری (گزینه‌ها)', 'User Menu (Options)') }}</h3>
                    <Badge variant="secondary" class="text-[9px] px-2 py-0.5 border border-border/50 text-muted-foreground font-mono">Profile Menu Items</Badge>
                  </div>

                  <!-- Vertical menu list (menu stack of ProfileOptionCards) -->
                  <div class="flex flex-col gap-2.5 w-full">
                    <ProfileOptionCard
                      :title="languageStore.t('تنظیمات سیستم', 'System Settings')"
                      :description="languageStore.t('تنظیمات زبان، ظاهر، حریم خصوصی و اعلان‌ها', 'Language, appearance, privacy and notifications')"
                      :icon="SettingsIcon"
                      :badgeText="simulatorSettingsBadge || undefined"
                      :badgeVariant="'destructive'"
                      @click="handleProfileOptionClick('Settings')"
                    />
                    
                    <ProfileOptionCard
                      :title="languageStore.t('مدیریت اتصال‌ها', 'Manage Connections')"
                      :description="languageStore.t('مدیریت اتصال به ربات‌ها، کانال‌ها و پلتفرم‌های خارجی', 'Manage connection to bots, channels, and external platforms')"
                      :icon="LinkIcon"
                      :badgeText="simulatorConnectionsBadge || undefined"
                      :badgeVariant="'default'"
                      @click="handleProfileOptionClick('Connections')"
                    />

                    <ProfileOptionCard
                      :title="languageStore.t('زبان برنامه (Language)', 'App Language (Language)')"
                      :description="languageStore.t('تغییر زبان کلی سامانه و چیدمان راست‌چین/چپ‌چین', 'Toggle global app language and RTL/LTR layout')"
                      :icon="LanguagesIcon"
                      :badgeText="languageStore.currentLanguage.toUpperCase()"
                      :badgeVariant="'secondary'"
                      @click="handleProfileOptionClick('Language')"
                    />

                    <ProfileOptionCard
                      :title="languageStore.t('دستیار هوش مصنوعی', 'AI Assistant')"
                      :description="languageStore.t('تنظیمات مدل هوشمند تفکر، خلاقیت و کلیدهای API فعال', 'Smart thinking model, creativity, and active API keys')"
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
                  :dir="languageStore.dir"
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
                  :dir="languageStore.dir"
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
                  :dir="languageStore.dir"
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
                  :dir="languageStore.dir"
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
                  :dir="languageStore.dir"
                >
                  <TopicMessageInput
                    :placeholder="simulatorInputPlaceholder"
                    :disabled="simulatorInputDisabled"
                    :initialText="simulatorInputText"
                    :initialAttachments="simulatorInputAttachments"
                    @send="handleInputSend"
                    @attach="simulateAddAttachment('image')"
                    @plus="logEvent('TopicMessageInput: Plus Button Clicked -> Opened Action Sheet', {})"
                    @create-donation="isSimulatorCreateDonationOpen = true; logEvent('TopicMessageInput: Create Donation Clicked -> Opened CreateDonationDialog', {})"
                    @recordVoice="logEvent('TopicMessageInput: Voice Recording Started', {})"
                    @removeAttachment="handleInputRemoveAttachment"
                  />
                </div>

                <!-- TopicEditView Preview -->
                <div 
                  v-else-if="currentComponent === 'topic-edit'"
                  class="w-full flex flex-col"
                  :dir="languageStore.dir"
                >
                  <TopicEditView 
                    :topic="simulatorTopicData"
                    @back="logEvent('TopicEdit: Back Clicked', {}); currentComponent = 'header'"
                    @save="(data) => {
                      simulatorTopicData.title = data.title;
                      simulatorTopicData.description = data.description;
                      simulatorTopicData.image = getImageUrl(data.image);
                      logEvent('TopicEdit: Saved', data);
                    }"
                  />
                </div>

                <!-- TopicConnectionsView Preview -->
                <div 
                  v-else-if="currentComponent === 'topic-connections'"
                  class="w-full flex flex-col"
                  :dir="languageStore.dir"
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

                <!-- LoadingDialog Preview -->
                <div 
                  v-else-if="currentComponent === 'loading-dialog'"
                  class="w-full flex flex-col items-center justify-center py-10"
                  :dir="languageStore.dir"
                >
                  <Button @click="startLoadingSimulation(true)" class="cursor-pointer flex items-center gap-1.5" data-icon="inline-start">
                    <FlaskConicalIcon class="size-4 animate-bounce" />
                    شبیه‌سازی و باز کردن دیالوگ لودینگ
                  </Button>
                  
                  <p class="text-[10px] text-muted-foreground text-center mt-3 max-w-xs leading-relaxed">
                    با کلیک بر روی دکمه بالا، دیالوگ لودینگ شبیه‌سازی شده و فرآیند ۴ مرحله‌ای خط لوله آغاز می‌شود.
                  </p>
                  
                  <!-- LoadingDialog Component -->
                  <LoadingDialog
                    :isOpen="simulatorLoadingIsOpen"
                    :progress="simulatorLoadingProgress"
                    :currentStatus="simulatorLoadingStatus"
                    :isProcessing="simulatorLoadingIsProcessing"
                    @close="stopLoadingSimulation"
                    @action="() => {
                      logEvent('LoadingDialog: Action clicked (Redirection)', {});
                      stopLoadingSimulation();
                    }"
                  />
                </div>

                <!-- TopicImportView Preview -->
                <div 
                  v-else-if="currentComponent === 'topic-import'"
                  class="w-full flex flex-col"
                  :dir="languageStore.dir"
                >
                  <TopicImportView 
                    @import-complete="logEvent('TopicImport: Import completed successfully', {})"
                    @import-failed="(err) => logEvent('TopicImport: Import failed', { error: err })"
                  />
                </div>

                <!-- ConfirmModal Preview -->
                <div 
                  v-else-if="currentComponent === 'confirm-modal'"
                  class="w-full flex flex-col items-center justify-center py-10"
                  :dir="languageStore.dir"
                >
                  <div class="flex flex-col gap-2">
                    <Button @click="openConfirmSimulation('destructive')" class="cursor-pointer flex items-center gap-1.5 justify-center h-10 w-64 font-bold text-xs" variant="destructive">
                      <Trash2Icon class="size-4" />
                      {{ languageStore.t('شبیه‌سازی دیالوگ تایید حذف (Destructive)', 'Simulate Delete Dialog (Destructive)') }}
                    </Button>
                    <Button @click="openConfirmSimulation('warning')" class="cursor-pointer flex items-center gap-1.5 justify-center h-10 w-64 font-bold text-xs bg-amber-600 hover:bg-amber-700 text-white" variant="default">
                      <AlertTriangleIcon class="size-4" />
                      {{ languageStore.t('شبیه‌سازی دیالوگ تایید خروج (Warning)', 'Simulate Logout Dialog (Warning)') }}
                    </Button>
                    <Button @click="openConfirmSimulation('info')" class="cursor-pointer flex items-center gap-1.5 justify-center h-10 w-64 font-bold text-xs bg-blue-600 hover:bg-blue-700 text-white" variant="default">
                      <InfoIcon class="size-4" />
                      {{ languageStore.t('شبیه‌سازی دیالوگ تایید درون‌ریزی (Info)', 'Simulate Re-import Dialog (Info)') }}
                    </Button>
                    <Button @click="openSelectiveDeleteSimulation" class="cursor-pointer flex items-center gap-1.5 justify-center h-10 w-64 font-bold text-xs bg-emerald-600 hover:bg-emerald-700 text-white" variant="default">
                      <Trash2Icon class="size-4" />
                      {{ languageStore.t('شبیه‌سازی حذف انتخابی پست (Selective)', 'Simulate Selective Post Delete') }}
                    </Button>
                  </div>
                  
                  <p class="text-[10px] text-muted-foreground text-center mt-4 max-w-xs leading-relaxed">
                    {{ languageStore.t('با کلیک بر روی دکمه‌های بالا، سناریوهای تایید مختلف باز می‌شوند. رویدادهای «تایید» و «انصراف» در کنسول زیر لاگ خواهند شد.', 'Clicking the buttons above opens different confirmation scenarios. "Confirm" and "Cancel" events will be logged in the console below.') }}
                  </p>
                  
                  <!-- ConfirmModal Component -->
                  <ConfirmModal
                    v-model:is-open="simulatorConfirmIsOpen"
                    :post="simulatorConfirmPost"
                    :title="simulatorConfirmTitle"
                    :description="simulatorConfirmDescription"
                    :confirm-text="simulatorConfirmConfirmText"
                    :cancel-text="simulatorConfirmCancelText"
                    :variant="simulatorConfirmVariant"
                    @confirm="(opts) => logEvent('ConfirmModal: Confirmed', { variant: simulatorConfirmVariant, options: opts })"
                    @cancel="logEvent('ConfirmModal: Cancelled', { variant: simulatorConfirmVariant })"
                  />
                </div>

                <!-- TopicAdminsView Subview Preview -->
                <div 
                  v-else-if="currentComponent === 'topic-admins'"
                  class="w-full flex flex-col gap-4"
                  :dir="languageStore.dir"
                >
                  <!-- Controls Bar -->
                  <div class="flex flex-wrap items-center justify-between gap-3 bg-muted/30 p-3 rounded-2xl border border-border/60">
                    <div class="flex items-center gap-2">
                      <ShieldCheckIcon class="size-4 text-primary" />
                      <span class="text-xs font-extrabold text-foreground">
                        {{ languageStore.t('تست و بررسی تمام وضعیت‌های کارت مدیریت ادمین‌ها', 'Test all states of Topic Admins View') }}
                      </span>
                    </div>

                    <div class="flex flex-wrap items-center gap-2">
                      <!-- State Toggles -->
                      <Button 
                        @click="simulatorAdminsForcedState = 'default'"
                        :variant="simulatorAdminsForcedState === 'default' ? 'default' : 'outline'"
                        size="sm"
                        class="text-[11px] font-semibold h-7.5 cursor-pointer"
                      >
                        {{ languageStore.t('حالت معمولی (دیتا)', 'Normal') }}
                      </Button>

                      <Button 
                        @click="simulatorAdminsForcedState = 'loading'"
                        :variant="simulatorAdminsForcedState === 'loading' ? 'default' : 'outline'"
                        size="sm"
                        class="text-[11px] font-semibold h-7.5 cursor-pointer"
                      >
                        {{ languageStore.t('بارگذاری (Loading)', 'Loading') }}
                      </Button>

                      <Button 
                        @click="simulatorAdminsForcedState = 'empty'"
                        :variant="simulatorAdminsForcedState === 'empty' ? 'default' : 'outline'"
                        size="sm"
                        class="text-[11px] font-semibold h-7.5 cursor-pointer"
                      >
                        {{ languageStore.t('لیست خالی (Empty)', 'Empty') }}
                      </Button>

                      <Button 
                        @click="simulatorAdminsForcedState = 'error'"
                        :variant="simulatorAdminsForcedState === 'error' ? 'destructive' : 'outline'"
                        size="sm"
                        class="text-[11px] font-semibold h-7.5 cursor-pointer"
                      >
                        {{ languageStore.t('نمایش ارور (Error)', 'Error') }}
                      </Button>

                      <!-- Toggle: Owner vs Public Viewer -->
                      <Button 
                        @click="simulatorAdminsIsOwner = !simulatorAdminsIsOwner"
                        variant="outline"
                        size="sm"
                        class="text-[11px] font-semibold h-7.5 cursor-pointer border-primary/30"
                      >
                        {{ simulatorAdminsIsOwner 
                          ? languageStore.t('نقش: مالک (Owner)', 'Role: Owner') 
                          : languageStore.t('نقش: بیننده (Viewer)', 'Role: Viewer') 
                        }}
                      </Button>
                    </div>
                  </div>

                  <!-- Render Subview Page Component -->
                  <TopicAdminsView
                    :topic-id="simulatorAdminsTopicId"
                    :is-owner="simulatorAdminsIsOwner"
                    :forced-state="simulatorAdminsForcedState"
                    @back="logEvent('TopicAdminsView: Back button clicked', {})"
                  />
                </div>

                <!-- EditProfileModal Preview -->
                <div 
                  v-else-if="currentComponent === 'edit-profile-modal'"
                  class="w-full flex flex-col items-center justify-center py-10 gap-4 text-center"
                  :dir="languageStore.dir"
                >
                  <Button 
                    @click="simulatorEditProfileIsOpen = true" 
                    class="cursor-pointer flex items-center gap-2 h-10 px-6 font-bold text-xs shadow-md"
                  >
                    <UserIcon class="size-4" />
                    {{ languageStore.t('باز کردن مودال ویرایش حساب', 'Open Edit Profile Modal') }}
                  </Button>

                  <p class="text-[10px] text-muted-foreground text-center max-w-xs leading-relaxed">
                    {{ languageStore.t('تست و بررسی ویرایش تصویر، نام و نام خانوادگی حساب کاربری.', 'Test editing user image, first name, and last name.') }}
                  </p>

                  <EditProfileModal
                    :is-open="simulatorEditProfileIsOpen"
                    :user-profile="{ name: 'شایان مهدوی', first_name: 'شایان', last_name: 'مهدوی', phone: '09123456789' }"
                    @close="simulatorEditProfileIsOpen = false"
                    @update="(data) => { logEvent('EditProfileModal: Updated', data); simulatorEditProfileIsOpen = false; }"
                  />
                </div>

                <!-- UnderDevelopmentCard Sandbox Content (Driven by top Simulator Header Tabs) -->
                <div 
                  v-else-if="currentComponent === 'under-dev'"
                  class="w-full max-w-2xl mx-auto flex flex-col gap-4"
                  :dir="languageStore.dir"
                >
                  <!-- 1. Live Preview Content -->
                  <div v-if="underDevActiveTab === 'preview'" class="w-full flex justify-center py-2">
                    <UnderDevelopmentCard
                      :title="simulatorUnderDevTitle"
                      :description="simulatorUnderDevDesc"
                      :icon="currentUnderDevIconComponent"
                      :eta="simulatorUnderDevEta"
                      :features="simulatorUnderDevFeatures"
                      :action-text="simulatorUnderDevActionText"
                      :show-back-button="simulatorUnderDevShowBack"
                      :back-button-text="simulatorUnderDevBackText"
                      :pattern-speed="simulatorUnderDevSpeed"
                      :pattern-style="simulatorUnderDevPattern"
                      @action="logEvent('UnderDevCard: Action Clicked (Notify/Interest)', { title: simulatorUnderDevTitle })"
                      @back="logEvent('UnderDevCard: Back Button Clicked', {})"
                    />
                  </div>

                  <!-- 2. Code Snippet Content -->
                  <div v-else-if="underDevActiveTab === 'code'" class="w-full">
                    <div class="relative rounded-2xl bg-card/60 dark:bg-black/40 border border-border/60 p-4 shadow-sm backdrop-blur-md">
                      <!-- Code header -->
                      <div class="flex items-center justify-between border-b border-border/40 pb-2.5 mb-3" dir="ltr">
                        <div class="flex items-center gap-2">
                          <span class="size-2.5 rounded-full bg-rose-500/80 inline-block" />
                          <span class="size-2.5 rounded-full bg-amber-500/80 inline-block" />
                          <span class="size-2.5 rounded-full bg-emerald-500/80 inline-block" />
                          <span class="text-[11px] font-mono font-bold text-muted-foreground ml-2">UnderDevelopmentCard.vue</span>
                        </div>
                        
                        <Button
                          @click="copyUnderDevCode"
                          size="xs"
                          :variant="underDevCopied ? 'default' : 'secondary'"
                          class="h-7 text-[11px] font-semibold gap-1.5 cursor-pointer rounded-lg shadow-xs"
                        >
                          <CheckIcon v-if="underDevCopied" class="size-3" />
                          <CopyIcon v-else class="size-3" />
                          <span>{{ underDevCopied ? 'کپی شد!' : 'کپی تمپلیت' }}</span>
                        </Button>
                      </div>

                      <!-- Code display -->
                      <pre class="text-[11px] font-mono text-foreground/90 overflow-x-auto p-2 leading-relaxed select-all" dir="ltr"><code>{{ generatedUnderDevCode }}</code></pre>
                    </div>
                  </div>

                  <!-- 3. Presets Content -->
                  <div v-else-if="underDevActiveTab === 'presets'" class="w-full">
                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      <button
                        @click="applyUnderDevPreset('minimal')"
                        class="p-4 rounded-xl border border-border/40 bg-card/40 hover:bg-muted/40 hover:border-primary/30 transition-all text-start flex flex-col gap-1.5 cursor-pointer"
                      >
                        <div class="flex items-center justify-between w-full">
                          <span class="text-xs font-bold text-foreground">حالت مینیمال (ساده)</span>
                          <Badge variant="outline" class="text-[9px]">Minimal</Badge>
                        </div>
                        <span class="text-[11px] text-muted-foreground">فقط آیکون ساخت و ساز، عنوان، توضیح و دکمه بازگشت</span>
                      </button>

                      <button
                        @click="applyUnderDevPreset('full')"
                        class="p-4 rounded-xl border border-border/40 bg-card/40 hover:bg-muted/40 hover:border-primary/30 transition-all text-start flex flex-col gap-1.5 cursor-pointer"
                      >
                        <div class="flex items-center justify-between w-full">
                          <span class="text-xs font-bold text-foreground">حالت کامل (Full Featured)</span>
                          <Badge variant="secondary" class="text-[9px]">Full</Badge>
                        </div>
                        <span class="text-[11px] text-muted-foreground">شامل ویژگی‌ها، زمان تقریبی، پترن گرید و دکمه‌های اکشن</span>
                      </button>

                      <button
                        @click="applyUnderDevPreset('ai')"
                        class="p-4 rounded-xl border border-border/40 bg-card/40 hover:bg-muted/40 hover:border-primary/30 transition-all text-start flex flex-col gap-1.5 cursor-pointer"
                      >
                        <div class="flex items-center justify-between w-full">
                          <span class="text-xs font-bold text-foreground">حالت هوش مصنوعی (AI Assistant)</span>
                          <Badge variant="default" class="text-[9px]">AI Beta</Badge>
                        </div>
                        <span class="text-[11px] text-muted-foreground">آیکون Sparkles با پترن نقطه‌ای و لیست انتظار</span>
                      </button>

                      <button
                        @click="applyUnderDevPreset('rocket')"
                        class="p-4 rounded-xl border border-border/40 bg-card/40 hover:bg-muted/40 hover:border-primary/30 transition-all text-start flex flex-col gap-1.5 cursor-pointer"
                      >
                        <div class="flex items-center justify-between w-full">
                          <span class="text-xs font-bold text-foreground">حالت پرتاب و API (Rocket)</span>
                          <Badge variant="secondary" class="text-[9px]">v3.0</Badge>
                        </div>
                        <span class="text-[11px] text-muted-foreground">آیکون موشک با پترن پرسرعت و مشاهده مستندات</span>
                      </button>
                    </div>
                  </div>
                </div>

                <!-- ChangelogModal Preview -->
                <div 
                  v-else-if="currentComponent === 'changelog-modal'"
                  class="w-full flex flex-col items-center justify-center py-10 gap-4 text-center"
                  :dir="languageStore.dir"
                >
                  <Button 
                    @click="simulatorChangelogIsOpen = true" 
                    class="cursor-pointer flex items-center gap-2 h-10 px-6 font-bold text-xs shadow-md"
                  >
                    <SparklesIcon class="size-4 text-primary" />
                    {{ languageStore.t('باز کردن دیالوگ بروزرسانی‌ها (Changelog)', 'Open Changelog Modal') }}
                  </Button>

                  <p class="text-[10px] text-muted-foreground text-center max-w-xs leading-relaxed">
                    {{ languageStore.t('تست و بررسی لیست آکاردئونی تغییرات و نسخه جدید پلتفرم.', 'Test accordion updates list and new platform release notes.') }}
                  </p>

                  <ChangelogModal />
                </div>

                <!-- AIRefinerDrawer Preview -->
                <div 
                  v-else-if="currentComponent === 'ai-refiner-drawer'"
                  class="w-full flex flex-col items-center justify-center py-10 gap-4 text-center"
                  :dir="languageStore.dir"
                >
                  <Button 
                    @click="simulatorAIRefinerIsOpen = true" 
                    class="cursor-pointer flex items-center gap-2 h-10 px-6 font-bold text-xs shadow-md bg-amber-600 hover:bg-amber-700 text-white"
                  >
                    <Wand2Icon class="size-4" />
                    {{ languageStore.t('باز کردن کشوی دستیار هوش مصنوعی', 'Open AI Refiner Drawer') }}
                  </Button>

                  <p class="text-[10px] text-muted-foreground text-center max-w-xs leading-relaxed">
                    {{ languageStore.t('تست و بررسی بهبود متن، ترجمه و تغییر لحن پیام در کشوی هوش مصنوعی.', 'Test text refinement, translation, and tone shifts in AI drawer.') }}
                  </p>

                  <AIRefinerDrawer
                    :open="simulatorAIRefinerIsOpen"
                    :text="simulatorAIRefinerText"
                    @update:open="(val) => simulatorAIRefinerIsOpen = val"
                    @apply="(text) => { logEvent('AIRefinerDrawer: Refined Text Applied', { text }); simulatorAIRefinerText = text; }"
                  />
                </div>

                <!-- DonationCard Preview -->
                <div 
                  v-else-if="currentComponent === 'donation-card'"
                  class="w-full flex flex-col items-center justify-center py-4 gap-4"
                  :dir="languageStore.dir"
                >
                  <!-- In-place 3-State Testing Controls -->
                  <div class="flex flex-wrap items-center justify-between w-full max-w-md pb-2 border-b border-border/40 gap-2">
                    <span class="text-xs font-bold text-foreground">تست وضعیت‌های پویش:</span>
                    <div class="flex items-center gap-1 bg-muted/60 p-1 rounded-xl border border-border/40 text-xs">
                      <Button
                        size="xs"
                        :variant="simulatorDonationCampaign.status === 'active' ? 'default' : 'ghost'"
                        class="h-7 text-xs font-semibold rounded-lg cursor-pointer"
                        @click="setDonationState('active')"
                      >در حال جمع‌آوری</Button>
                      <Button
                        size="xs"
                        :variant="simulatorDonationCampaign.status === 'completed' ? 'default' : 'ghost'"
                        class="h-7 text-xs font-semibold rounded-lg cursor-pointer"
                        @click="setDonationState('completed')"
                      >تکمیل شده</Button>
                      <Button
                        size="xs"
                        :variant="simulatorDonationCampaign.status === 'executed' ? 'default' : 'ghost'"
                        class="h-7 text-xs font-semibold rounded-lg cursor-pointer"
                        @click="setDonationState('executed')"
                      >اجرا شده و شفاف</Button>
                    </div>
                  </div>

                  <DonationCard
                    v-bind="simulatorDonationCampaign"
                    @donate-click="handleDonateClick"
                    @topic-click="handleDonationTopicClick"
                    @transparency-click="handleTransparencyClick"
                  />

                  <DonationModal
                    v-model:open="simulatorDonationModalOpen"
                    :campaign-title="simulatorDonationCampaign.title"
                    @submit-donation="handleDonationSubmit"
                  />
                </div>

                <!-- DonationChatCard Preview (In-Topic Message Bubble) -->
                <div 
                  v-else-if="currentComponent === 'donation-chat-card'"
                  class="w-full flex flex-col items-center justify-center py-6 gap-4"
                  :dir="languageStore.dir"
                >
                  <div class="w-full max-w-md flex flex-col gap-2">
                    <div class="flex items-center justify-between text-xs text-muted-foreground px-1">
                      <span class="font-bold text-foreground">کارت فشرده پویش (داخل چت تاپیک):</span>
                      <Badge variant="outline" class="text-[10px] text-primary border-primary/30">DonationChatCard</Badge>
                    </div>
                    <DonationChatCard 
                      :title="simulatorChatCardTitle"
                      :category="simulatorChatCardCategory"
                      :target-amount="simulatorChatCardTargetAmount"
                      :collected-amount="simulatorChatCardCollectedAmount"
                      :description="simulatorChatCardDesc"
                      :media-url="simulatorChatCardHasMedia ? simulatorChatCardMediaUrl : undefined"
                      :media-type="simulatorChatCardMediaType"
                      :media-count="simulatorChatCardMediaCount"
                      :auto-pin="simulatorChatCardAutoPin"
                      :deadline="simulatorChatCardDeadline"
                      :topic-name="simulatorChatCardTopicName"
                      :author-name="simulatorChatCardAuthorName"
                      :is-preview="simulatorChatCardIsPreview"
                      @donate-click="logEvent('DonationChatCard: Donate Clicked', { title: simulatorChatCardTitle })"
                      @card-click="logEvent('DonationChatCard: Card Clicked', { title: simulatorChatCardTitle })"
                      @edit-click="(c) => {
                        logEvent('DonationChatCard: Edit Clicked -> Opening CreateDonationDialog in Edit Mode', c)
                        isSimulatorCreateDonationOpen = true
                      }"
                    />
                  </div>
                </div>

                <!-- CreateDonationDialog Preview -->
                <div 
                  v-else-if="currentComponent === 'create-donation-dialog'"
                  class="w-full flex flex-col items-center justify-center py-6 gap-5"
                  :dir="languageStore.dir"
                >
                  <!-- Direct Inline CreateDonationDialog Preview -->
                  <div class="w-full flex justify-center">
                    <CreateDonationDialog 
                      :is-inline="true"
                      :topic-id="'topic-simulator'"
                      :topic-name="simulatorCreateDonationTopicName"
                      :author-name="simulatorCreateDonationAuthorName"
                      @created="(payload) => {
                        simulatorLastCreatedDonation = payload
                        logEvent('CreateDonationDialog: Campaign Created (Inline)', payload)
                      }"
                    />
                  </div>

                  <!-- Live Chat Card Result if Created -->
                  <div v-if="simulatorLastCreatedDonation" class="flex flex-col items-center gap-3 w-full max-w-md animate-in fade-in-50 duration-300">
                    <div class="flex items-center gap-2 w-full justify-between px-1">
                      <span class="text-xs font-bold text-foreground flex items-center gap-1.5">
                        <SparklesIcon class="size-3.5 text-primary" />
                        آخرین پویش ایجاد شده (کارت در چت):
                      </span>
                      <Badge variant="outline" class="text-[10px] text-primary border-primary/30">
                        خروجی زنده
                      </Badge>
                    </div>
                    <DonationChatCard 
                      :title="simulatorLastCreatedDonation.title"
                      :category="simulatorLastCreatedDonation.category"
                      :target-amount="simulatorLastCreatedDonation.target_amount"
                      :collected-amount="0"
                      :description="simulatorLastCreatedDonation.description"
                      :auto-pin="simulatorLastCreatedDonation.auto_pin"
                      :deadline="simulatorLastCreatedDonation.deadline"
                      :topic-name="simulatorCreateDonationTopicName"
                      :author-name="simulatorCreateDonationAuthorName"
                    />
                  </div>
                </div>

                <!-- DuplicateWarningDialog Preview -->
                <div 
                  v-else-if="currentComponent === 'duplicate-warning-dialog'"
                  class="w-full flex flex-col items-center justify-center py-10 gap-4 text-center"
                  :dir="languageStore.dir"
                >
                  <Button 
                    @click="openDuplicateWarningSimulation" 
                    class="cursor-pointer flex items-center gap-2 h-10 px-6 font-bold text-xs shadow-md bg-amber-500 hover:bg-amber-600 text-white"
                  >
                    <AlertTriangleIcon class="size-4" />
                    {{ languageStore.t('شبیه‌سازی هشدار پیام تکراری (Duplicate Warning)', 'Simulate Duplicate Warning Dialog') }}
                  </Button>

                  <p class="text-[10px] text-muted-foreground text-center max-w-xs leading-relaxed">
                    {{ languageStore.t('تست و بررسی دیالوگ هشدار هوشمند ارسال پیام تکراری قبل از ثبت نهایی.', 'Test smart duplicate content warning dialog before final post creation.') }}
                  </p>

                  <DuplicateWarningDialog
                    v-model:is-open="simulatorDuplicateIsOpen"
                    :existing-post-id="simulatorDuplicatePostId"
                    :created-at="simulatorDuplicateCreatedAt"
                    :published-platforms="simulatorDuplicatePlatforms"
                    @go-to-existing="(id) => logEvent('DuplicateWarningDialog: Go To Existing Post Emitted', { postId: id })"
                    @force-submit="logEvent('DuplicateWarningDialog: Force Submit Emitted', {})"
                    @cancel="logEvent('DuplicateWarningDialog: Cancelled Emitted', {})"
                  />
                </div>

                <!-- UnderDevelopmentCard Preview -->
                <div 
                  v-else-if="currentComponent === 'under-dev'"
                  class="w-full max-w-xl mx-auto flex flex-col items-center justify-center py-4 gap-4"
                  :dir="languageStore.dir"
                >
                  <UnderDevelopmentCard
                    :title="simulatorUnderDevTitle"
                    :description="simulatorUnderDevDesc"
                    :icon="currentUnderDevIconComponent"
                    :badge-text="simulatorUnderDevBadge"
                    :badge-variant="simulatorUnderDevBadgeVariant"
                    :eta="simulatorUnderDevEta"
                    :features="simulatorUnderDevFeatures"
                    :action-text="simulatorUnderDevActionText"
                    :show-back-button="simulatorUnderDevShowBack"
                    :pattern-speed="simulatorUnderDevSpeed"
                    :pattern-style="simulatorUnderDevPattern"
                    @action="logEvent('UnderDevCard: Action Clicked (Notify/Interest)', { title: simulatorUnderDevTitle })"
                    @back="logEvent('UnderDevCard: Back Button Clicked', {})"
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

    <!-- Language Switcher Dialog -->
    <Dialog v-slot="{ open }" v-model:open="showLanguageDialog">
      <DialogContent :show-close-button="false" class="sm:max-w-[420px] p-0 overflow-hidden bg-card/90 dark:bg-zinc-950/90 backdrop-blur-lg border border-border/40">
        <DialogHeader class="p-6 pb-4 border-b border-border/10">
          <div class="flex items-center gap-2 justify-start">
            <div class="size-8 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
              <LanguagesIcon class="size-4.5" />
            </div>
            <DialogTitle class="text-sm font-black text-foreground flex flex-col gap-0.5 text-start">
              <span>تنظیم زبان و چیدمان برنامه</span>
              <span class="text-[10px] text-muted-foreground font-normal">App Language & Direction</span>
            </DialogTitle>
          </div>
          <DialogDescription class="text-[10px] text-muted-foreground text-start mt-2.5 flex flex-col gap-1 leading-relaxed">
            <span>زبان و جهت چیدمان رابط کاربری سامانه را در این قسمت انتخاب کنید.</span>
            <span class="opacity-80">Choose your preferred language and UI layout direction.</span>
          </DialogDescription>
        </DialogHeader>

        <!-- Selection List -->
        <div class="p-6 flex flex-col gap-3">
          <!-- Persian Option -->
          <div 
            @click="selectedLang = 'fa'"
            class="flex items-center justify-between p-4 rounded-xl border cursor-pointer transition-all duration-200"
            :class="selectedLang === 'fa' ? 'bg-primary/5 border-primary text-primary font-bold shadow-xs' : 'border-border/40 hover:bg-muted/40 text-foreground'"
          >
            <div class="flex items-center gap-3">
              <span class="text-lg">🇮🇷</span>
              <div class="flex flex-col text-start gap-0.5">
                <span class="text-xs font-bold">فارسی (Persian)</span>
                <span class="text-[9px] text-muted-foreground">راست‌چین / RTL Layout</span>
              </div>
            </div>
            <div 
              v-if="selectedLang === 'fa'"
              class="size-5 rounded-full bg-primary flex items-center justify-center text-primary-foreground"
            >
              <CheckIcon class="size-3" />
            </div>
          </div>

          <!-- English Option -->
          <div 
            @click="selectedLang = 'en'"
            class="flex items-center justify-between p-4 rounded-xl border cursor-pointer transition-all duration-200"
            :class="selectedLang === 'en' ? 'bg-primary/5 border-primary text-primary font-bold shadow-xs' : 'border-border/40 hover:bg-muted/40 text-foreground'"
          >
            <div class="flex items-center gap-3">
              <span class="text-lg">🇬🇧</span>
              <div class="flex flex-col text-start gap-0.5">
                <span class="text-xs font-bold">English (انگلیسی)</span>
                <span class="text-[9px] text-muted-foreground">چپ‌چین / LTR Layout</span>
              </div>
            </div>
            <div 
              v-if="selectedLang === 'en'"
              class="size-5 rounded-full bg-primary flex items-center justify-center text-primary-foreground"
            >
              <CheckIcon class="size-3" />
            </div>
          </div>
        </div>

        <DialogFooter class="p-4 bg-muted/10 dark:bg-muted/5 border-t border-border/10 flex justify-end gap-2" :dir="languageStore.dir">
          <Button variant="outline" size="sm" @click="showLanguageDialog = false" class="text-xs font-bold h-8 flex items-center gap-1.5 cursor-pointer">
            <span>بستن</span>
            <span class="text-[10px] opacity-70 border-s border-muted-foreground/30 ps-1.5 ms-1">Close</span>
          </Button>
          <Button variant="default" size="sm" @click="handleConfirmLanguage" class="text-xs font-bold h-8 flex items-center gap-1.5 cursor-pointer">
            <span>تایید</span>
            <span class="text-[10px] opacity-70 border-s border-primary-foreground/30 ps-1.5 ms-1">Confirm</span>
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <!-- CreateDonationDialog Simulator Instance -->
    <CreateDonationDialog 
      v-model:open="isSimulatorCreateDonationOpen"
      :topic-id="simulatorTopicData.id"
      :topic-name="simulatorCreateDonationTopicName"
      :author-name="simulatorCreateDonationAuthorName"
      @created="(payload) => {
        logEvent('CreateDonationDialog: Campaign Created', payload)
        simulatorLastCreatedDonation = payload
      }"
    />

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
