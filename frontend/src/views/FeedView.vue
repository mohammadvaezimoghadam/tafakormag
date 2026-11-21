<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useDark, useToggle } from '@vueuse/core'

import PlatformHeader from '@/components/PlatformHeader.vue'
import PlatformNavigation from '@/components/PlatformNavigation.vue'
import PostCard from '@/components/PostCard.vue'
import TopicCard from '@/components/TopicCard.vue'
import CreateTopicModal from '@/components/CreateTopicModal.vue'
import EditProfileModal from '@/components/EditProfileModal.vue'
import ConfirmModal from '@/components/ConfirmModal.vue'
import DuplicateWarningDialog from '@/components/DuplicateWarningDialog.vue'
import { checkDuplicatePost, createDonationCampaign, updateDonationCampaign, deleteDonationCampaign, donateToCampaign, submitEditProposal, updateEditProposal } from '@/api'
import BotConnectionCard from '@/components/BotConnectionCard.vue'
import TopicEditView from '@/components/TopicEditView.vue'
import TopicConnectionsView from '@/components/TopicConnectionsView.vue'
import TopicImportView from '@/components/TopicImportView.vue'
import TopicAdminsView from '@/components/TopicAdminsView.vue'
import TopicAiChatView from '@/components/TopicAiChatView.vue'
import TopicMessageInput from '@/components/TopicMessageInput.vue'
import DonationsFeed from '@/components/kindness/DonationsFeed.vue'
import CreateDonationDialog from '@/components/kindness/CreateDonationDialog.vue'
import DonationChatCard from '@/components/kindness/DonationChatCard.vue'
import DonationModal from '@/components/kindness/DonationModal.vue'
import PaymentReceiptModal from '@/components/kindness/PaymentReceiptModal.vue'
import type { CreateDonationPayload, DonationCampaignProps } from '@/types/kindness'
import MarketplaceView from './MarketplaceView.vue'
import UnderDevelopmentCard from '@/components/UnderDevelopmentCard.vue'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { ConstructionIcon, PlusIcon, ChevronRightIcon, LanguagesIcon, CheckIcon, Loader2Icon, LayersIcon, CheckCircle2Icon } from '@lucide/vue'
import TopicEditorialView from '@/components/TopicEditorialView.vue'
import MyBookshelfView from '@/components/shelf/MyBookshelfView.vue'
import DonateBookFromShelfDialog from '@/components/shelf/DonateBookFromShelfDialog.vue'
import BookDonationDetailDialog from '@/components/shelf/BookDonationDetailDialog.vue'
import BookChatCard from '@/components/shelf/BookChatCard.vue'
import TopicBookDonationDialog from '@/components/shelf/TopicBookDonationDialog.vue'
import type { ShelfBook, BookDonationPostData } from '@/types/shelf'
import PlatformHomeHub from '@/components/home/PlatformHomeHub.vue'
import PlatformProfileView from '@/components/profile/PlatformProfileView.vue'

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter
} from '@/components/ui/dialog'
import { useLanguageStore } from '@/stores/languageStore'

import { useBotStore } from '@/stores/botStore'
import { useUserStore } from '@/stores/userStore'
import { useTopicStore } from '@/stores/topicStore'
import { usePostStore } from '@/stores/postStore'
import { useToastStore } from '@/stores/toastStore'

// Tab state ('home' | 'topics' | 'donate' | 'marketplace' | 'profile')
const currentTab = ref<'home' | 'topics' | 'donate' | 'marketplace' | 'profile'>('home')

// Home tab subview ('hub' = main action hub + sliders, 'topics' = topics list)
const homeSubView = ref<'hub' | 'topics'>('hub')
const platformHomeHubRef = ref<InstanceType<typeof PlatformHomeHub> | null>(null)
const isHomeDonateDialogOpen = ref(false)
const homeDonatePreselectedBookId = ref<number | null>(null)
const homeDonateInitialMode = ref<'donate' | 'receive'>('donate')
const isHomeHandoverDialogOpen = ref(false)
const activeHandoverShortCode = ref('')
const activeHandoverOtp = ref('')

// Profile subview navigation state
const activeProfileSubView = ref<'menu' | 'connections' | 'shelf'>('menu')

// Active topic subview ('feed' | 'edit' | 'connections' | 'import' | 'admins' | 'faq' | 'editorial')
const activeTopicSubView = ref<'feed' | 'edit' | 'connections' | 'import' | 'admins' | 'faq' | 'editorial'>('feed')

// Initialize Pinia stores
const botStore = useBotStore()
const userStore = useUserStore()
const topicStore = useTopicStore()
const postStore = usePostStore()
const toastStore = useToastStore()

const languageStore = useLanguageStore()
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

const { telegramBotStatus, telegramBotToken, baleBotStatus, baleBotToken } = storeToRefs(botStore)
const { userProfile } = storeToRefs(userStore)
const { topics, selectedTopic } = storeToRefs(topicStore)
const { posts } = storeToRefs(postStore)

const router = useRouter()
const route = useRoute()

// Sync router to tab/topic state
const syncRouteToState = () => {
  if (route.path === '/profile') {
    currentTab.value = 'profile'
    selectedTopic.value = null
  } else if (route.path === '/donate') {
    currentTab.value = 'donate'
    selectedTopic.value = null
  } else if (route.path === '/marketplace') {
    currentTab.value = 'marketplace'
    selectedTopic.value = null
  } else if (route.path === '/topics') {
    currentTab.value = 'topics'
    selectedTopic.value = null
  } else if (route.path.startsWith('/topic/')) {
    currentTab.value = 'topics'
    const topicId = Number(route.params.id)
    if (!isNaN(topicId)) {
      const found = topics.value.find(t => t.id === topicId)
      if (found) {
        selectedTopic.value = found
      } else {
        selectedTopic.value = { id: topicId, title: languageStore.t('در حال بارگذاری...', 'Loading...') } as any
      }
    }
  } else if (route.path.startsWith('/b/')) {
    currentTab.value = 'home'
    selectedTopic.value = null
    homeSubView.value = 'hub'
    const code = String(route.params.code || '').trim().toUpperCase()
    const otpQuery = typeof route.query.otp === 'string' ? route.query.otp.trim() : ''
    if (code) {
      activeHandoverShortCode.value = code
      activeHandoverOtp.value = otpQuery
      isHomeHandoverDialogOpen.value = true
    }
  } else {
    currentTab.value = 'home'
    selectedTopic.value = null
  }
}

watch(isHomeHandoverDialogOpen, (open) => {
  if (!open) {
    activeHandoverShortCode.value = ''
    activeHandoverOtp.value = ''
    if (route.path.startsWith('/b/')) {
      router.replace('/')
    }
  }
})

const handleOpenHomeBookDonate = (
  bookId: number | null = null,
  mode: 'donate' | 'receive' = 'donate'
) => {
  homeDonatePreselectedBookId.value = bookId
  homeDonateInitialMode.value = mode
  isHomeDonateDialogOpen.value = true
}

const handleOpenHandoverByCode = (shortCode: string) => {
  const cleaned = (shortCode || '').trim().toUpperCase()
  if (!cleaned) return
  activeHandoverShortCode.value = cleaned
  isHomeHandoverDialogOpen.value = true
}

const handleOpenShelfFromHome = () => {
  const hasToken = (typeof sessionStorage !== 'undefined' && sessionStorage.getItem('auth_token')) ||
    (typeof localStorage !== 'undefined' && localStorage.getItem('auth_token'))
  if (!userStore.isAuthenticated && !hasToken) {
    userStore.isLoginModalOpen = true
    return
  }
  currentTab.value = 'profile'
  activeProfileSubView.value = 'shelf'
}

const handleOpenShelfBookFromHome = (book: ShelfBook) => {
  if (!userStore.isAuthenticated) {
    userStore.isLoginModalOpen = true
    return
  }
  currentTab.value = 'profile'
  activeProfileSubView.value = 'shelf'
}

const handleHomeBookMutated = async () => {
  await Promise.allSettled([
    userStore.loadProfile(),
    platformHomeHubRef.value?.reload(),
  ])
}

// Watchers to sync state to route
watch(() => route.path, () => {
  syncRouteToState()
})

watch(currentTab, (newTab) => {
  if (newTab !== 'donate') {
    selectedDonationCampaign.value = null
    pendingDonationId.value = null
    donationDetailFromHome.value = false
  }
  if (newTab === 'profile') {
    if (!userStore.isAuthenticated) {
      userStore.isLoginModalOpen = true
      currentTab.value = 'home'
      return
    }
    if (route.path !== '/profile') {
      router.push('/profile')
    }
  } else if (newTab === 'donate') {
    if (route.path !== '/donate') {
      router.push('/donate')
    }
  } else if (newTab === 'topics') {
    if (route.path !== '/topics' && !route.path.startsWith('/topic/')) {
      router.push('/topics')
    }
  } else if (newTab === 'marketplace') {
    if (route.path !== '/marketplace') {
      router.push('/marketplace')
    }
  } else if (newTab === 'home') {
    if (route.path !== '/' && !route.path.startsWith('/b/')) {
      router.push('/')
    }
  }
})

const scrollToBottom = (smooth = true) => {
  const doScroll = () => {
    window.scrollTo({
      top: document.body.scrollHeight,
      behavior: smooth ? 'smooth' : 'auto'
    })
  }
  nextTick(() => {
    doScroll()
    requestAnimationFrame(() => {
      doScroll()
      setTimeout(doScroll, 100)
      setTimeout(doScroll, 350)
    })
  })
}

watch(() => postStore.loading, (isLoading) => {
  if (!isLoading && activeTopicSubView.value === 'feed' && selectedTopic.value) {
    scrollToBottom(false)
  }
})

watch(selectedTopic, async (newTopic) => {
  if (newTopic) {
    const targetPath = `/topic/${newTopic.id}`
    if (route.path !== targetPath) {
      router.push(targetPath)
    }
    try {
      await postStore.loadPosts(newTopic.id)
      scrollToBottom(false)
    } catch (err) {
      //
    }
  } else {
    if (route.path.startsWith('/topic/')) {
      router.push('/')
    }
  }
})

watch(() => topics.value, () => {
  if (route.path.startsWith('/topic/')) {
    const topicId = Number(route.params.id)
    if (!isNaN(topicId)) {
      const found = topics.value.find(t => t.id === topicId)
      if (found) {
        selectedTopic.value = found
      }
    }
  }
}, { deep: true })

const handleFeedScroll = async () => {
  if (activeTopicSubView.value !== 'feed' || !selectedTopic.value) return
  if (!postStore.hasMore || postStore.loadingMore || postStore.loading) return

  // When scrolling near top (<= 300px), load older messages and preserve scroll offset
  if (window.scrollY <= 300) {
    const oldScrollHeight = document.documentElement.scrollHeight
    const oldScrollY = window.scrollY
    await postStore.loadNextPage(selectedTopic.value.id)
    nextTick(() => {
      const newScrollHeight = document.documentElement.scrollHeight
      const heightDiff = newScrollHeight - oldScrollHeight
      window.scrollTo({
        top: oldScrollY + heightDiff,
        behavior: 'auto'
      })
    })
  }
}

// Payment Callback Receipt State

const isPaymentResultModalOpen = ref(false)
const paymentResultData = ref<{
  status: 'success' | 'failed'
  ref_id?: string
  amount?: number
  authority?: string
  campaign_id?: string
}>({ status: 'success' })

const formatDonationAmount = (val?: number): string => {
  if (!val) return '۰'
  return new Intl.NumberFormat('fa-IR').format(val)
}

const checkPaymentCallbackParams = () => {
  const query = route.query
  if (query.payment === 'success') {
    paymentResultData.value = {
      status: 'success',
      ref_id: (query.ref_id as string) || (query.RefID as string) || '',
      amount: query.amount ? Number(query.amount) : undefined,
      authority: (query.authority as string) || (query.Authority as string) || '',
      campaign_id: query.campaign_id as string
    }
    isPaymentResultModalOpen.value = true
    toastStore.triggerToast(languageStore.t('پرداخت با موفقیت انجام و ثبت گردید.', 'Payment completed and recorded successfully.'), 'success')
    
    // Refresh campaigns list
    if (donationsFeedRef.value) {
      donationsFeedRef.value.loadCampaigns()
    }

    // Clean query params smoothly
    router.replace({ path: route.path, query: {} })
  } else if (query.payment === 'failed') {
    const reason = query.reason
    const msg = reason === 'canceled'
      ? languageStore.t('پرداخت توسط کاربر لغو گردید.', 'Payment was canceled by user.')
      : languageStore.t('پرداخت درگاه ناموفق بود یا تایید نشد.', 'Payment failed or was not verified.')
    toastStore.triggerToast(msg, 'warning')
    router.replace({ path: route.path, query: {} })
  }
}

watch(() => route.query, () => {
  if (route.query.payment) {
    checkPaymentCallbackParams()
  }
})

// Fetch data on mount
onMounted(async () => {
  window.addEventListener('scroll', handleFeedScroll)
  syncRouteToState()
  try {
    await Promise.allSettled([
      userStore.loadProfile(),
      topicStore.loadTopics()
    ])
    checkPaymentCallbackParams()
  } catch (err) {
    console.error('Error on FeedView mount:', err)
  }
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleFeedScroll)
})


// Header computed states for platform and connections view
const headerIsInnerPage = computed(() => {
  if (currentTab.value === 'home') {
    return selectedTopic.value !== null || homeSubView.value === 'topics'
  } else if (currentTab.value === 'topics') {
    return selectedTopic.value !== null
  } else if (currentTab.value === 'donate') {
    return selectedDonationCampaign.value !== null
  } else if (currentTab.value === 'profile') {
    return activeProfileSubView.value !== 'menu'
  }
  return false
})

const headerInnerTitle = computed(() => {
  if (currentTab.value === 'home' || currentTab.value === 'topics') {
    if (selectedTopic.value === null && homeSubView.value === 'topics') {
      return languageStore.t('لیست تاپیک‌ها', 'Topics List')
    }
    if (activeTopicSubView.value === 'faq') {
      const topicName = selectedTopic.value?.title || ''
      return languageStore.t(`دستیار هوشمند ${topicName}`, `${topicName} AI Assistant`)
    }
    return selectedTopic.value?.title || ''
  } else if (currentTab.value === 'donate' && selectedDonationCampaign.value) {
    return selectedDonationCampaign.value.title || languageStore.t('جزئیات پویش', 'Campaign Details')
  } else if (currentTab.value === 'profile') {
    if (activeProfileSubView.value === 'shelf') {
      return languageStore.t('قفسه کتاب من', 'My Bookshelf')
    }
    return languageStore.t('مدیریت اتصالات', 'Connections Management')
  }
  return ''
})

const headerTitle = computed(() => {
  if (currentTab.value === 'profile') {
    return languageStore.t('پروفایل', 'Profile')
  }
  if (currentTab.value === 'topics') {
    return languageStore.t('تاپیک‌ها', 'Topics')
  }
  if (currentTab.value === 'donate') {
    return languageStore.t('پویش‌های اهدا', 'Donation Campaigns')
  }
  if (currentTab.value === 'marketplace') {
    return languageStore.t('بازارچه', 'Marketplace')
  }
  return languageStore.t('تفکر', 'Tafakor')
})

const handleHeaderBack = () => {
  if (currentTab.value === 'home') {
    if (selectedTopic.value !== null) {
      if (activeTopicSubView.value !== 'feed') {
        activeTopicSubView.value = 'feed'
      } else {
        selectedTopic.value = null
      }
    } else if (homeSubView.value === 'topics') {
      homeSubView.value = 'hub'
      searchQuery.value = ''
    }
  } else if (currentTab.value === 'topics') {
    if (selectedTopic.value !== null) {
      if (activeTopicSubView.value !== 'feed') {
        activeTopicSubView.value = 'feed'
      } else {
        selectedTopic.value = null
      }
    }
  } else if (currentTab.value === 'donate' && selectedDonationCampaign.value !== null) {
    donationsFeedRef.value?.closeDetail()
    selectedDonationCampaign.value = null
    pendingDonationId.value = null
    if (donationDetailFromHome.value) {
      donationDetailFromHome.value = false
      currentTab.value = 'home'
    }
  } else if (currentTab.value === 'profile') {
    activeProfileSubView.value = 'menu'
  }
}

const handleTelegramConnect = async (token: string) => {
  try {
    await botStore.connectTelegram(token, () => {
      triggerToast(languageStore.t('ربات تلگرام با موفقیت متصل شد.', 'Telegram bot connected successfully.'))
    })
  } catch (err) {
    //
  }
}

const handleTelegramDisconnect = async () => {
  try {
    await botStore.disconnectTelegram(() => {
      triggerToast(languageStore.t('اتصال ربات تلگرام قطع شد.', 'Telegram bot disconnected.'))
    })
  } catch (err) {
    //
  }
}

const handleBaleConnect = async (token: string) => {
  try {
    await botStore.connectBale(token, () => {
      triggerToast(languageStore.t('ربات بله با موفقیت متصل شد.', 'Bale bot connected successfully.'))
    })
  } catch (err) {
    //
  }
}

const handleBaleDisconnect = async () => {
  try {
    await botStore.disconnectBale(() => {
      triggerToast(languageStore.t('اتصال ربات بله قطع شد.', 'Bale bot disconnected.'))
    })
  } catch (err) {
    //
  }
}

const activeConnectionsCount = computed(() => {
  let count = 0
  if (telegramBotStatus.value === 'connected') count++
  if (baleBotStatus.value === 'connected') count++
  return count
})

const connectionsBadgeText = computed(() => {
  const count = activeConnectionsCount.value
  if (count === 0) return languageStore.t('بدون اتصال', 'No connection')
  return languageStore.t(count + ' فعال', count + ' active')
})

const connectionsBadgeVariant = computed(() => {
  return activeConnectionsCount.value > 0 ? 'secondary' : 'default'
})

// Search query binding
const searchQuery = ref('')

// Create Topic & Donation Modal State
const isCreateModalOpen = ref(false)
const isCreateDonationOpen = ref(false)
const isTopicBookDonationOpen = ref(false)
const isDonateModalOpen = ref(false)
const selectedDonationForPayment = ref<any>(null)
const editingDonation = ref<any>(null)
const isEditProfileOpen = ref(false)
const isAdminsModalOpen = ref(false)
const donationsFeedRef = ref<any>(null)
const selectedDonationCampaign = ref<DonationCampaignProps | null>(null)
const pendingDonationId = ref<string | number | null>(null)
const donationDetailFromHome = ref(false)

const handleOpenDonationsTab = () => {
  donationDetailFromHome.value = false
  pendingDonationId.value = null
  currentTab.value = 'donate'
}

const handleOpenCampaignFromHome = (campaignId: string | number) => {
  donationDetailFromHome.value = true
  pendingDonationId.value = campaignId
  currentTab.value = 'donate'
}

const handleOpenCreateDonation = () => {
  editingDonation.value = null
  isCreateDonationOpen.value = true
}

const handleOpenCreateBookDonation = () => {
  if (!userStore.isAuthenticated) {
    toastStore.triggerToast(
      languageStore.t('برای اهدای کتاب در تاپیک، ابتدا وارد حساب کاربری خود شوید.', 'Please sign in first to donate books in topic.'),
      'info'
    )
    return
  }
  isTopicBookDonationOpen.value = true
}

const handleBookDonationPublished = async () => {
  if (selectedTopic.value) {
    await postStore.loadPosts(selectedTopic.value.id)
    scrollToBottom(true)
  }
}

const isBookOwner = (book: any, postAuthor?: any) => {
  if (!userProfile.value) return false
  const currentUserId = userProfile.value.id ? String(userProfile.value.id) : null
  const currentUserPhone = userProfile.value.phone || null
  if (book?.seller_phone && currentUserPhone && book.seller_phone === currentUserPhone) return true
  if (postAuthor?.phone && currentUserPhone && postAuthor.phone === currentUserPhone) return true
  if (postAuthor?.id && currentUserId && String(postAuthor.id) === currentUserId) return true
  return false
}

const handleClaimBook = (book: any) => {
  if (book?.short_code) {
    activeHandoverShortCode.value = book.short_code
    isHomeHandoverDialogOpen.value = true
  } else {
    toastStore.triggerToast(
      languageStore.t('درخواست دریافت کتاب برای اهداکننده ارسال گردید.', 'Book claim requested.'),
      'success'
    )
  }
}

const handleInspectBookShortCode = (shortCode: string) => {
  if (shortCode) {
    activeHandoverShortCode.value = shortCode
    isHomeHandoverDialogOpen.value = true
  }
}

const handleShareBook = (book: any) => {
  const shareTitle = `اهدای کتاب: ${book.title}`
  const shareUrl = window.location.href
  if (navigator.share) {
    navigator.share({
      title: shareTitle,
      text: book.description || shareTitle,
      url: shareUrl,
    }).catch(() => {})
  } else {
    navigator.clipboard.writeText(shareUrl)
    toastStore.triggerToast(languageStore.t('لینک گفتگو کپی شد.', 'Link copied.'), 'success')
  }
}

const isCampaignCreator = (campaign: any, postAuthor?: any) => {
  if (!userProfile.value) return false
  const currentUserId = userProfile.value.id ? String(userProfile.value.id) : null
  const currentUserPhone = userProfile.value.phone || null

  if (campaign?.creatorId && currentUserId && String(campaign.creatorId) === currentUserId) return true
  if (campaign?.creator_id && currentUserId && String(campaign.creator_id) === currentUserId) return true
  if (campaign?.creator?.id && currentUserId && String(campaign.creator.id) === currentUserId) return true
  if (campaign?.creator_info?.id && currentUserId && String(campaign.creator_info.id) === currentUserId) return true
  
  if (campaign?.creator_info?.phone && currentUserPhone && campaign.creator_info.phone === currentUserPhone) return true
  if (campaign?.creator?.phone && currentUserPhone && campaign.creator.phone === currentUserPhone) return true
  if (campaign?.creatorPhone && currentUserPhone && campaign.creatorPhone === currentUserPhone) return true
  if (postAuthor?.phone && currentUserPhone && postAuthor.phone === currentUserPhone) return true
  if (postAuthor?.id && currentUserId && String(postAuthor.id) === currentUserId) return true

  return false
}

const handleEditDonation = (campaign: any) => {
  editingDonation.value = {
    id: campaign.id,
    title: campaign.title,
    category: campaign.category,
    targetAmount: campaign.targetAmount ?? campaign.target_amount,
    description: campaign.description,
    deadline: campaign.deadline,
    autoPin: campaign.autoPin ?? campaign.auto_pin ?? true
  }
  isCreateDonationOpen.value = true
}

const handleDonationCreated = async (payload: CreateDonationPayload) => {
  const targetTopicId = payload.topic_id || selectedTopic.value?.id || topics.value[0]?.id
  if (!targetTopicId) {
    toastStore.triggerToast(languageStore.t('ابتدا یک تاپیک انتخاب یا ایجاد کنید.', 'Please select or create a topic first.'), 'error')
    return
  }

  try {
    const formData = new FormData()
    formData.append('topic', String(targetTopicId))
    formData.append('title', payload.title)
    formData.append('description', payload.description)
    formData.append('category', payload.category)
    formData.append('target_amount', String(payload.target_amount || 0))
    if (payload.deadline) {
      formData.append('deadline', payload.deadline)
    }
    if (payload.media_files && payload.media_files.length > 0 && payload.media_files[0]) {
      formData.append('cover_image', payload.media_files[0])
      payload.media_files.forEach((file: any) => {
        if (file) formData.append('uploaded_files', file)
      })
    }

    const res = await createDonationCampaign(formData)
    const isPendingReview = res?.data?.status === 'pending_review'

    if (isPendingReview) {
      toastStore.triggerToast(
        languageStore.t(
          'پویش شما با موفقیت ثبت شد و پس از بررسی و تایید مدیریت منتشر خواهد شد.',
          'Campaign submitted successfully and will be published upon admin review.'
        ),
        'info'
      )
    } else {
      toastStore.triggerToast(
        languageStore.t(
          'پویش مهربانی با موفقیت ایجاد و ارسال شد.',
          'Donation campaign created and posted successfully.'
        ),
        'success'
      )
      // Reload posts if inside a topic only when published active
      if (selectedTopic.value) {
        await postStore.loadPosts(selectedTopic.value.id)
        scrollToBottom(true)
      }
    }
    
    // Refresh donations feed
    if (donationsFeedRef.value) {
      donationsFeedRef.value.loadCampaigns()
    }
  } catch (error: any) {
    console.error('Failed to create donation campaign:', error)
    toastStore.triggerToast(languageStore.t('خطا در ایجاد پویش مهربانی', 'Failed to create donation campaign'), 'error')
  }
}

const handleDonationUpdated = async (payload: CreateDonationPayload & { id?: string | number }) => {
  if (!payload.id) return

  try {
    const formData = new FormData()
    formData.append('title', payload.title)
    formData.append('description', payload.description)
    formData.append('category', payload.category)
    formData.append('target_amount', String(payload.target_amount || 0))
    if (payload.deadline) {
      formData.append('deadline', payload.deadline)
    }
    if (payload.media_files && payload.media_files.length > 0 && payload.media_files[0]) {
      formData.append('cover_image', payload.media_files[0])
      payload.media_files.forEach((file: any) => {
        if (file) formData.append('uploaded_files', file)
      })
    }

    await updateDonationCampaign(payload.id, formData)
    toastStore.triggerToast(languageStore.t('پویش مهربانی با موفقیت ویرایش و ذخیره شد.', 'Donation campaign updated successfully.'), 'success')
    
    if (donationsFeedRef.value) {
      donationsFeedRef.value.loadCampaigns()
    }

    if (selectedTopic.value) {
      await postStore.loadPosts(selectedTopic.value.id)
    }
  } catch (error: any) {
    console.error('Failed to update donation campaign:', error)
    toastStore.triggerToast(languageStore.t('خطا در ویرایش پویش مهربانی', 'Failed to update donation campaign'), 'error')
  }
}

const handleOpenDonateModal = (campaign: any) => {
  selectedDonationForPayment.value = campaign
  isDonateModalOpen.value = true
}

const handleProcessDonationPayment = async (data: { amount: number; isAnonymous: boolean }) => {
  if (!selectedDonationForPayment.value) return
  try {
    const res = await donateToCampaign(selectedDonationForPayment.value.id, {
      amount: data.amount,
      is_anonymous: data.isAnonymous
    })

    if (res.data?.gateway_url) {
      isDonateModalOpen.value = false
      toastStore.triggerToast(languageStore.t('در حال انتقال به درگاه پرداخت زرین‌پال...', 'Redirecting to ZarinPal payment gateway...'), 'info')
      window.location.href = res.data.gateway_url
    } else {
      toastStore.triggerToast(languageStore.t('خطا در دریافت آدرس درگاه پرداخت', 'Failed to retrieve gateway URL'), 'error')
    }
  } catch (err: any) {
    console.error('Donation payment error:', err)
    const errData = err.response?.data
    let errorMsg = languageStore.t('خطا در اتصال به درگاه پرداخت زرین‌پال', 'Failed to connect to ZarinPal gateway')

    if (errData) {
      if (errData.gateway) errorMsg = errData.gateway
      else if (errData.campaign) errorMsg = errData.campaign
      else if (errData.amount) errorMsg = Array.isArray(errData.amount) ? errData.amount[0] : errData.amount
      else if (errData.detail) errorMsg = errData.detail
      else if (typeof errData === 'string') errorMsg = errData
    }
    toastStore.triggerToast(errorMsg, 'error')
  }
}


const handleDonationTopicClick = (topicId: string | number) => {
  selectedDonationCampaign.value = null
  pendingDonationId.value = null
  donationDetailFromHome.value = false
  currentTab.value = 'home'
  homeSubView.value = 'topics'
  const numericId = Number(topicId)
  const found = topics.value.find(t => t.id === numericId)
  if (found) {
    selectedTopic.value = found
  } else {
    router.push(`/topic/${topicId}`)
  }
}

const handleDonationTransparencyClick = (idx: number, url: string) => {
  if (url) {
    window.open(url, '_blank')
  }
}

// Donation Campaign Delete State (from In-Topic Chat)
const selectedDonationForDelete = ref<any | null>(null)
const isConfirmDeleteDonationOpen = ref(false)
const isDeletingDonation = ref(false)

const confirmDonationDeleteConfig = computed(() => {
  if (!selectedDonationForDelete.value) {
    return {
      title: languageStore.t('حذف پویش', 'Delete Campaign'),
      description: '',
      confirmText: languageStore.t('حذف', 'Delete'),
      variant: 'destructive' as const
    }
  }

  const campaign = selectedDonationForDelete.value
  const hasDonations = Boolean(
    (campaign.donors_count && campaign.donors_count > 0) ||
    (campaign.collected_amount && campaign.collected_amount > 0) ||
    (campaign.donorsCount && campaign.donorsCount > 0) ||
    (campaign.collectedAmount && campaign.collectedAmount > 0)
  )

  const amount = campaign.collected_amount || campaign.collectedAmount || 0
  const donorsCount = campaign.donors_count || campaign.donorsCount || 0

  if (hasDonations) {
    return {
      title: languageStore.t('متوقف‌سازی و غیرفعال‌کردن پویش مهربانی', 'Deactivate & Stop Campaign'),
      description: languageStore.t(
        `این پویش دارای ${new Intl.NumberFormat('fa-IR').format(amount)} تومان واریزی و ${donorsCount} حامی است. جهت حفظ شفافیت مالی، پویش متوقف و غیرفعال خواهد شد اما سوابق آن باقی می‌ماند. آیا مایل به ادامه هستید؟`,
        `This campaign has received ${amount} Tomans from ${donorsCount} donors. To maintain financial transparency, it will be stopped and deactivated while keeping past records accessible. Do you want to proceed?`
      ),
      confirmText: languageStore.t('توقف و غیرفعال‌سازی', 'Stop & Deactivate'),
      variant: 'warning' as const
    }
  } else {
    return {
      title: languageStore.t('حذف کامل پویش مهربانی', 'Permanently Delete Campaign'),
      description: languageStore.t(
        'این پویش هیچ واریزی و حامی ثبت‌شده‌ای ندارد. با تایید شما، این پویش به طور کامل و دائم از سیستم پاکسازی خواهد شد. آیا مطمئن هستید؟',
        'This campaign has no donations or donors. It will be permanently removed from the system. Are you sure?'
      ),
      confirmText: languageStore.t('حذف کامل پویش', 'Permanently Delete'),
      variant: 'destructive' as const
    }
  }
})

const handleDeleteDonationFromChat = (campaign: any) => {
  if (!campaign) return
  selectedDonationForDelete.value = campaign
  isConfirmDeleteDonationOpen.value = true
}

const handleConfirmDeleteDonation = async () => {
  if (!selectedDonationForDelete.value?.id) return
  const campaign = selectedDonationForDelete.value
  isDeletingDonation.value = true

  try {
    const res = await deleteDonationCampaign(campaign.id)
    if (res.data?.action === 'deactivated' || res.data?.status === 'inactive') {
      toastStore.triggerToast(languageStore.t('پویش متوقف و غیرفعال شد و سوابق آن حفظ گردید.', 'Campaign stopped and deactivated.'), 'info')
    } else {
      toastStore.triggerToast(languageStore.t('پویش با موفقیت به طور کامل حذف شد.', 'Campaign permanently deleted.'), 'success')
    }

    if (donationsFeedRef.value) {
      donationsFeedRef.value.loadCampaigns()
    }
    if (selectedTopic.value) {
      await postStore.loadPosts(selectedTopic.value.id)
    }
  } catch (err) {
    console.error('Error deleting donation campaign:', err)
    toastStore.triggerToast(languageStore.t('خطا در حذف یا متوقف‌سازی پویش', 'Failed to delete or deactivate campaign'), 'error')
  } finally {
    isDeletingDonation.value = false
    isConfirmDeleteDonationOpen.value = false
    selectedDonationForDelete.value = null
  }
}

// Confirm Modals State
const isDeletePostOpen = ref(false)
const postToDeleteId = ref<string | number | null>(null)
const postToDelete = ref<any | null>(null)
const isDeleteTopicOpen = ref(false)

// Duplicate Warning State
const isDuplicateWarningOpen = ref(false)
const duplicatePostId = ref<string | number | null>(null)
const duplicateCreatedAt = ref<string | null>(null)
const duplicatePlatforms = ref<string[]>([])
const pendingPostMessage = ref<{ text: string } | null>(null)

const dataURLtoFile = (dataurl: string, filename: string) => {
  const arr = dataurl.split(',')
  const mimeMatch = arr[0] ? arr[0].match(/:(.*?);/) : null
  const mime = mimeMatch && mimeMatch[1] ? mimeMatch[1] : 'image/png'
  const base64Data = arr[1] || ''
  const bstr = atob(base64Data)
  let n = bstr.length
  const u8arr = new Uint8Array(n)
  while (n--) {
    u8arr[n] = bstr.charCodeAt(n)
  }
  return new File([u8arr], filename, { type: mime })
}

const handleCreateTopic = async (newTopic: { title: string; description: string; post_badge?: string; image?: string }) => {
  let imageFile: File | undefined = undefined
  if (newTopic.image && newTopic.image.startsWith('data:')) {
    imageFile = dataURLtoFile(newTopic.image, 'topic_image.png')
  }
  
  try {
    await topicStore.addTopic({
      title: newTopic.title,
      description: newTopic.description,
      post_badge: newTopic.post_badge,
      image: imageFile
    })
    isCreateModalOpen.value = false
    triggerToast(languageStore.t('تاپیک «' + newTopic.title + '» با موفقیت ایجاد شد.', 'Topic "' + newTopic.title + '" was created successfully.'))
  } catch (err) {
    //
  }
}

// Toast Notification state
const triggerToast = (message: string, type: 'success' | 'error' | 'info' | 'warning' = 'success') => {
  toastStore.triggerToast(message, type)
}

const isAuthenticated = computed(() => userStore.isAuthenticated)

const handleCreateTopicClick = () => {
  if (!isAuthenticated.value) {
    userStore.isLoginModalOpen = true
  } else {
    isCreateModalOpen.value = true
  }
}


const handleProfileEdit = () => {
  isEditProfileOpen.value = true
}

const handleProfileSave = async (data: { first_name: string; last_name: string; avatarFile?: File }) => {
  const formData = new FormData()
  formData.append('first_name', data.first_name)
  formData.append('last_name', data.last_name)
  if (data.avatarFile) {
    formData.append('profile_image', data.avatarFile)
  }
  
  try {
    await userStore.updateProfile(formData)
    isEditProfileOpen.value = false
    triggerToast(languageStore.t('اطلاعات کاربری با موفقیت به‌روزرسانی شد.', 'User profile updated successfully.'), 'success')
  } catch (err) {
    //
  }
}

const handleLogout = () => {
  triggerToast(languageStore.t('در حال خروج از سیستم...', 'Logging out...'))
  setTimeout(() => {
    selectedTopic.value = null
    homeSubView.value = 'hub'
    activeProfileSubView.value = 'menu'
    currentTab.value = 'home'
    userStore.logout()
    router.push('/')
  }, 1000)
}

// Filtering computed logic based on search
const filteredTopics = computed(() => {
  if (!searchQuery.value.trim()) return topics.value
  const q = searchQuery.value.toLowerCase().trim()
  return topics.value.filter(t => 
    t.title.toLowerCase().includes(q) || 
    t.description.toLowerCase().includes(q)
  )
})

const filteredCurrentTopicPosts = computed(() => {
  return posts.value.filter(p => {
    if (!searchQuery.value.trim()) return true
    const q = searchQuery.value.toLowerCase().trim()
    return (p.content && p.content.toLowerCase().includes(q)) || 
           p.author.name.toLowerCase().includes(q)
  })
})

const handlePostLike = async (postId: string | number, isLiked: boolean) => {
  try {
    await postStore.likePost(postId, isLiked)
  } catch (err) {
    //
  }
}

const handlePostShare = (postId: string | number) => {
  const targetTopicId = selectedTopic.value?.id || ''
  const shareUrl = `${window.location.origin}/topic/${targetTopicId}#post-${postId}`
  if (navigator.clipboard) {
    navigator.clipboard.writeText(shareUrl).then(() => {
      triggerToast(languageStore.t('لینک پست با موفقیت در حافظه موقت کپی شد.', 'Post link copied to clipboard.'));
    }).catch(() => {
      triggerToast(languageStore.t('لینک پست کپی شد.', 'Post link copied.'));
    })
  }
}

const handleAddComment = async (postId: string | number, comment: any) => {
  // Comments are submitted directly through the store from PostCard watcher,
  // but we keep this handler to display the toast message.
  triggerToast(languageStore.t('دیدگاه شما با موفقیت ثبت شد.', 'Your comment was posted successfully.'));
}

const handlePostReact = async (postId: string | number, emoji: string) => {
  try {
    await postStore.reactToPost(postId, emoji)
  } catch (err) {
    //
  }
}

const handlePostDelete = (postId: string | number) => {
  postToDeleteId.value = postId
  postToDelete.value = posts.value.find(p => p.id === postId) || null
  isDeletePostOpen.value = true
}

const confirmPostDelete = async (options?: { delete_from_telegram: boolean; delete_from_bale: boolean; delete_from_db: boolean }) => {
  if (postToDeleteId.value === null) return
  try {
    if (options) {
      await postStore.selectiveDeletePost(postToDeleteId.value, options)
    } else {
      await postStore.deletePost(postToDeleteId.value)
    }
    await topicStore.loadTopics()
    triggerToast(languageStore.t('درخواست حذف پست ثبت شد.', 'Post deletion request submitted.'))
  } catch (err) {
    //
  } finally {
    postToDeleteId.value = null
    postToDelete.value = null
  }
}

const handleSelectTopic = async (topic: any) => {
  selectedTopic.value = topic
  activeTopicSubView.value = 'feed'
  try {
    await postStore.loadPosts(topic.id)
    scrollToBottom(false)
  } catch (err) {
    //
  }
}

const handleEditTopic = () => {
  if (!selectedTopic.value) return
  activeTopicSubView.value = 'edit'
}

const handleDeleteTopic = () => {
  if (!selectedTopic.value) return
  isDeleteTopicOpen.value = true
}

const confirmTopicDelete = async () => {
  if (!selectedTopic.value) return
  const title = selectedTopic.value.title
  try {
    await topicStore.deleteTopic(selectedTopic.value.id)
    triggerToast(languageStore.t('تاپیک «' + title + '» با موفقیت حذف شد.', 'Topic "' + title + '" deleted successfully.'))
  } catch (err) {
    //
  }
}

const handleTopicConnections = () => {
  if (!selectedTopic.value) return
  activeTopicSubView.value = 'connections'
}

const handleTopicImport = () => {
  if (!selectedTopic.value) return
  activeTopicSubView.value = 'import'
}

const handleSaveTopicEdit = async (updatedTopic: { title: string; description: string; post_badge?: string; image: string | File }) => {
  if (!selectedTopic.value) return
  try {
    await topicStore.updateTopic(selectedTopic.value.id, {
      title: updatedTopic.title,
      description: updatedTopic.description,
      post_badge: updatedTopic.post_badge,
      image: updatedTopic.image
    })
    activeTopicSubView.value = 'feed'
    triggerToast(languageStore.t('مشخصات تاپیک با موفقیت ویرایش شد.', 'Topic details edited successfully.'))
  } catch (err) {
    //
  }
}

const handleSaveTopicConnections = async (data: { 
  telegram_bot_active: boolean
  bale_bot_active: boolean
  telegram_connections: number[]
  bale_connections: number[]
  telegram_post_badge?: string
  bale_post_badge?: string
  telegram_post_link_mode?: 'auto_long' | 'always' | 'disabled'
  bale_post_link_mode?: 'auto_long' | 'always' | 'disabled'
}) => {
  if (!selectedTopic.value) return
  try {
    await topicStore.saveTopicConnections(selectedTopic.value.id, data)
    triggerToast(languageStore.t('تنظیمات اتصالات تاپیک با موفقیت به روز رسانی شد.', 'Topic connections settings updated successfully.'))
  } catch (err) {
    throw err
  }
}

const handleGoToConnections = () => {
  activeTopicSubView.value = 'feed'
  selectedTopic.value = null
  currentTab.value = 'profile'
  activeProfileSubView.value = 'connections'
}

// Topic Message Input / Attachments flow
const postAttachments = ref<any[]>([])
const hiddenFileInput = ref<HTMLInputElement | null>(null)
const selectedAttachmentFile = ref<File | null>(null)
const editingPost = ref<{ id: string | number; content: string } | null>(null)

const handlePostEdit = (id: string | number) => {
  const post = postStore.posts.find(p => p.id === id)
  if (post) {
    editingPost.value = { id, content: post.content || '' }
    removePostAttachment()
  }
}

const handleSaveEdit = async (message: { text: string }) => {
  if (!editingPost.value) return
  const formData = new FormData()
  formData.append('content', message.text)
  try {
    await postStore.updatePost(editingPost.value.id, formData)
    triggerToast(languageStore.t('یادداشت با موفقیت ویرایش شد.', 'Note edited successfully.'), 'success')
    handleCancelEdit()
  } catch (err) {
    // Error caught globally
  }
}

const handleCancelEdit = () => {
  editingPost.value = null
}

const proposingPost = ref<{ id: string | number; content: string; proposalId?: string | number } | null>(null)

const handleProposeEdit = (payload: { id: string | number; content: string; proposalId?: string | number }) => {
  editingPost.value = null
  proposingPost.value = {
    id: payload.id,
    content: payload.content,
    proposalId: payload.proposalId
  }
}

const handleCancelProposal = () => {
  proposingPost.value = null
}

const handleSaveProposal = async (message: { text: string }) => {
  if (!proposingPost.value) return
  try {
    if (proposingPost.value.proposalId) {
      await updateEditProposal(proposingPost.value.proposalId, {
        proposed_content: message.text
      })
      triggerToast(languageStore.t('پیشنهاد ویرایش با موفقیت به‌روزرسانی شد.', 'Edit proposal updated successfully.'), 'success')
    } else {
      await submitEditProposal({
        post_id: proposingPost.value.id,
        proposed_content: message.text
      })
      triggerToast(languageStore.t('پیشنهاد با موفقیت به میز ویراستاری ارسال شد.', 'Proposal submitted to Editorial Desk successfully.'), 'success')
    }
    proposingPost.value = null
  } catch (err: any) {
    const errorMsg = err.response?.data?.detail || err.response?.data?.error || err.message || languageStore.t('خطا در ثبت پیشنهاد', 'Failed to submit proposal')
    triggerToast(errorMsg, 'error')
  }
}

const isTopicCreator = computed<boolean>(() => {
  if (!selectedTopic.value || !userProfile.value) return false
  if (!selectedTopic.value.created_by) return true
  const createdById = typeof selectedTopic.value.created_by === 'object' && selectedTopic.value.created_by !== null
    ? (selectedTopic.value.created_by as any).id
    : selectedTopic.value.created_by
  return Boolean(
    String(createdById) === String(userProfile.value.id) ||
    (selectedTopic.value.created_by_phone && userProfile.value.phone && 
     String(selectedTopic.value.created_by_phone) === String(userProfile.value.phone))
  )
})

const triggerFileSelect = () => {
  hiddenFileInput.value?.click()
}

const handleFileInputChange = (e: Event) => {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  selectedAttachmentFile.value = file
  
  let fileType: 'image' | 'video' | 'audio' | 'file' = 'file'
  if (file.type.startsWith('image/')) fileType = 'image'
  else if (file.type.startsWith('video/')) fileType = 'video'
  else if (file.type.startsWith('audio/')) fileType = 'audio'

  const sizeMB = (file.size / (1024 * 1024)).toFixed(1) + ' MB'
  const previewUrl = fileType === 'image' ? URL.createObjectURL(file) : ''

  postAttachments.value = [{
    id: 'attach_1',
    name: file.name,
    type: fileType,
    url: previewUrl,
    size: sizeMB,
    status: 'completed',
    progress: 100
  }]
}

const handlePastedFile = (file: File) => {
  selectedAttachmentFile.value = file
  let fileType: 'image' | 'video' | 'audio' | 'file' = 'file'
  if (file.type.startsWith('image/')) fileType = 'image'
  else if (file.type.startsWith('video/')) fileType = 'video'
  else if (file.type.startsWith('audio/')) fileType = 'audio'

  const sizeMB = (file.size / (1024 * 1024)).toFixed(1) + ' MB'
  const previewUrl = fileType === 'image' ? URL.createObjectURL(file) : ''

  postAttachments.value = [{
    id: `paste_${Date.now()}`,
    name: file.name || 'Pasted File',
    type: fileType,
    url: previewUrl,
    size: sizeMB,
    status: 'completed',
    progress: 100
  }]
}

// Touch keyboard height tracking for mobile browsers (iOS Safari / mobile Chrome)
const feedKeyboardOffset = ref(0)

const handleFeedVisualViewportChange = () => {
  if (typeof window === 'undefined') return
  const vv = window.visualViewport
  if (!vv) {
    feedKeyboardOffset.value = 0
    return
  }
  const offsetFromBottom = Math.max(0, window.innerHeight - (vv.height + vv.offsetTop))
  feedKeyboardOffset.value = offsetFromBottom > 40 ? offsetFromBottom : 0
}

onMounted(() => {
  if (typeof window !== 'undefined' && window.visualViewport) {
    window.visualViewport.addEventListener('resize', handleFeedVisualViewportChange)
    window.visualViewport.addEventListener('scroll', handleFeedVisualViewportChange)
  }
})

onUnmounted(() => {
  if (typeof window !== 'undefined' && window.visualViewport) {
    window.visualViewport.removeEventListener('resize', handleFeedVisualViewportChange)
    window.visualViewport.removeEventListener('scroll', handleFeedVisualViewportChange)
  }
})

const feedInputBarStyle = computed(() => {
  const bottomPx = feedKeyboardOffset.value > 0 ? `${feedKeyboardOffset.value}px` : '0px'
  return {
    bottom: bottomPx,
    transition: 'bottom 0.15s ease-out'
  }
})

const getTopicDraft = (topicId?: number | string | null) => {
  if (!topicId) return ''
  try {
    return localStorage.getItem(`tafakor_topic_draft_${topicId}`) || ''
  } catch (e) {
    return ''
  }
}

const saveTopicDraft = (topicId: number | string | null, text: string) => {
  if (!topicId) return
  try {
    if (text && text.trim()) {
      localStorage.setItem(`tafakor_topic_draft_${topicId}`, text)
    } else {
      localStorage.removeItem(`tafakor_topic_draft_${topicId}`)
    }
  } catch (e) {}
}

const handleDraftChange = (newText: string) => {
  if (!editingPost.value && !proposingPost.value && selectedTopic.value) {
    saveTopicDraft(selectedTopic.value.id, newText)
  }
}

const removePostAttachment = () => {
  postAttachments.value = []
  selectedAttachmentFile.value = null
  if (hiddenFileInput.value) hiddenFileInput.value.value = ''
}

const handleSendPost = async (message: { text: string }, forceSubmit = false) => {
  if (!selectedTopic.value) return

  // 1. Check for duplicates if text is present and forceSubmit is false
  if (!forceSubmit && message.text && message.text.trim()) {
    try {
      const res = await checkDuplicatePost(selectedTopic.value.id, message.text.trim())
      if (res.data && res.data.is_duplicate) {
        duplicatePostId.value = res.data.existing_post_id
        duplicateCreatedAt.value = res.data.created_at
        duplicatePlatforms.value = res.data.published_platforms || []
        pendingPostMessage.value = message
        isDuplicateWarningOpen.value = true
        return
      }
    } catch (err) {
      // If duplicate check endpoint fails, proceed with posting
    }
  }

  const formData = new FormData()
  formData.append('topic', String(selectedTopic.value.id))
  formData.append('content', message.text)
  
  let mediaType = 'text'
  if (selectedAttachmentFile.value) {
    const file = selectedAttachmentFile.value
    if (file.type.startsWith('image/')) mediaType = 'image'
    else if (file.type.startsWith('video/')) mediaType = 'video'
    else if (file.type.startsWith('audio/')) mediaType = 'audio'
    
    formData.append('media_file', file)
  }
  formData.append('media_type', mediaType)

  try {
    await postStore.createPost(formData)
    await topicStore.loadTopics()
    if (selectedTopic.value) {
      saveTopicDraft(selectedTopic.value.id, '')
    }
    triggerToast(languageStore.t('پست جدید ارسال و در کانال‌های فعال بازنشر شد', 'New post sent and republished in active channels'), 'success')
    removePostAttachment()
    pendingPostMessage.value = null
    isDuplicateWarningOpen.value = false
    scrollToBottom(true)
  } catch (err) {
    //
  }
}

const handleGoToExistingPost = (postId: string | number | null) => {
  if (!postId) return
  isDuplicateWarningOpen.value = false
  nextTick(() => {
    const el = document.getElementById(`post-${postId}`)
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' })
      el.classList.add('ring-2', 'ring-amber-500', 'transition-all', 'rounded-2xl')
      setTimeout(() => {
        el.classList.remove('ring-2', 'ring-amber-500', 'transition-all', 'rounded-2xl')
      }, 3000)
    }
  })
}

// Dark/Light theme manager via VueUse for global synchronization
const isDark = useDark({
  selector: 'html',
  attribute: 'class',
  valueDark: 'dark',
  valueLight: '',
})
const toggleTheme = useToggle(isDark)
</script>

<template>
  <div 
    class="w-full max-w-[500px] flex flex-col gap-5 pb-6 mx-auto relative animate-in fade-in slide-in-from-bottom-3 duration-300" 
    :class="[languageStore.isFa ? 'text-right' : 'text-left']"
    :dir="languageStore.dir"
  >
    
    <!-- Header - Sticky (Shown on main views, custom views render their own headers) -->
    <PlatformHeader 
      v-if="currentTab === 'profile' || currentTab === 'donate' || currentTab === 'marketplace' || ((currentTab === 'home' || currentTab === 'topics') && selectedTopic === null) || ((currentTab === 'home' || currentTab === 'topics') && selectedTopic !== null && (activeTopicSubView === 'feed' || activeTopicSubView === 'faq'))"
      :is-inner-page="headerIsInnerPage" 
      :inner-title="headerInnerTitle" 
      :title="headerTitle" 
      :center-title="!headerIsInnerPage"
      :loading="!!((telegramBotStatus === 'connecting' || baleBotStatus === 'connecting') && isTopicCreator)"
      :show-options-button="!!((currentTab === 'home' || currentTab === 'topics') && selectedTopic !== null && activeTopicSubView === 'feed')"
      :show-faq-button="!!((currentTab === 'home' || currentTab === 'topics') && selectedTopic !== null && activeTopicSubView === 'feed')"
      :is-owner="isTopicCreator"
      :show-search-button="(currentTab === 'home' && selectedTopic === null && homeSubView === 'topics') || (currentTab === 'topics' && selectedTopic === null) || (currentTab === 'donate' && selectedDonationCampaign === null)"
      v-model:search-query="searchQuery"
      @back="handleHeaderBack"
      @edit-topic="handleEditTopic"
      @delete-topic="handleDeleteTopic"
      @topic-connections="handleTopicConnections"
      @topic-import="handleTopicImport"
      @topic-admins="activeTopicSubView = 'admins'"
      @topic-editorial="activeTopicSubView = 'editorial'"
      @topic-faq="activeTopicSubView = 'faq'"
    />

    <!-- MAIN CONTENT AREA -->
    <div class="w-full flex-1">
      <transition name="fade-slide" mode="out-in">
        <!-- TAB 1: HOME & TOPICS (TOPIC LIST & DETAILS & SUBVIEWS) -->
        <div v-if="currentTab === 'home' || currentTab === 'topics'" key="home" class="flex flex-col gap-5 w-full">
          
          <transition name="fade-slide" mode="out-in">
            <!-- Home Hub View: 3-Button Action Hub + Books & Donations Sliders -->
            <div v-if="selectedTopic === null && currentTab === 'home' && homeSubView === 'hub'" key="hub" class="w-full">
              <PlatformHomeHub
                ref="platformHomeHubRef"
                :topics-count="topics.length"
                @open-topics="currentTab = 'topics'; selectedTopic = null"
                @open-donations="handleOpenDonationsTab"
                @open-book-donations="handleOpenShelfFromHome"
                @open-shelf="handleOpenShelfFromHome"
                @open-shelf-book="handleOpenShelfBookFromHome"
                @open-campaign="handleOpenCampaignFromHome"
              />
            </div>

            <!-- List View: Search and vertical TopicCards -->
            <div v-else-if="selectedTopic === null" key="list" class="flex flex-col gap-5 w-full pb-20">
              <!-- TopicCards Container (Clean, borderless list directly on background) -->
              <div class="flex flex-col gap-2.5 w-full">
                <!-- Skeleton Loading -->
                <template v-if="topicStore.loading">
                  <div 
                    v-for="i in 4" 
                    :key="'topic-skeleton-' + i" 
                    class="w-full flex items-center gap-3.5 p-3 rounded-2xl select-none text-start animate-pulse"
                  >
                    <Skeleton class="size-11 rounded-2xl shrink-0" />
                    <div class="flex-1 flex flex-col gap-2 min-w-0">
                      <div class="flex items-center gap-2">
                        <Skeleton class="h-4 w-28 rounded-md" />
                        <Skeleton class="h-4 w-10 rounded-md" />
                      </div>
                      <Skeleton class="h-3 w-40 rounded-md" />
                    </div>
                    <div class="flex flex-col items-end shrink-0 gap-2">
                      <Skeleton class="h-3 w-10 rounded-md" />
                      <Skeleton class="size-5 rounded-full" />
                    </div>
                  </div>
                </template>

                <!-- Real Content -->
                <template v-else>
                  <TopicCard 
                    v-for="topic in filteredTopics" 
                    :key="topic.id"
                    v-bind="topic"
                    @click="handleSelectTopic(topic)"
                  />
                  
                  <div v-if="filteredTopics.length === 0" class="text-center py-12 text-xs text-muted-foreground font-medium">
                    {{ languageStore.t('هیچ تاپیکی مطابق با جستجوی شما یافت نشد.', 'No topics match your search.') }}
                  </div>
                </template>
              </div>
            </div>

            <!-- Detail View: Topic Posts Feed -->
            <div v-else-if="activeTopicSubView === 'feed'" key="feed" class="flex flex-col gap-4.5 w-full pb-32 relative">

              <!-- Skeleton Loading -->
              <div v-if="postStore.loading" class="flex flex-col gap-4.5 w-full animate-pulse">
                <div 
                  v-for="i in 3" 
                  :key="'post-skeleton-' + i"
                  class="w-full bg-background/12 dark:bg-card/10 border border-border/60 rounded-3xl p-5 flex flex-col gap-4 text-start"
                >
                  <div class="flex items-center justify-between">
                    <div class="flex items-center gap-3">
                      <Skeleton class="size-10 rounded-full shrink-0" />
                      <div class="flex flex-col gap-1.5 text-start">
                        <Skeleton class="h-4 w-24 rounded-md" />
                        <Skeleton class="h-3 w-16 rounded-md" />
                      </div>
                    </div>
                    <div class="flex items-center gap-2">
                      <Skeleton class="h-4 w-12 rounded-md" />
                      <Skeleton class="size-7 rounded-full" />
                    </div>
                  </div>
                  <div class="flex flex-col gap-2">
                    <Skeleton class="h-4 w-full rounded-md" />
                    <Skeleton class="h-4 w-[90%] rounded-md" />
                    <Skeleton class="h-4 w-[60%] rounded-md" />
                  </div>
                </div>
              </div>

              <!-- Real Content -->
              <template v-else>
                <!-- Skeleton Loading for additional older posts when scrolling up -->
                <div v-if="postStore.loadingMore" class="flex flex-col gap-4 w-full animate-pulse mb-2">
                  <div 
                    v-for="i in 2" 
                    :key="'post-more-skeleton-' + i"
                    class="w-full bg-background/12 dark:bg-card/10 border border-border/60 rounded-3xl p-5 flex flex-col gap-4 text-start"
                  >
                    <div class="flex items-center justify-between">
                      <div class="flex items-center gap-3">
                        <Skeleton class="size-10 rounded-full shrink-0" />
                        <div class="flex flex-col gap-1.5 text-start">
                          <Skeleton class="h-4 w-24 rounded-md" />
                          <Skeleton class="h-3 w-16 rounded-md" />
                        </div>
                      </div>
                      <div class="flex items-center gap-2">
                        <Skeleton class="h-4 w-12 rounded-md" />
                        <Skeleton class="size-7 rounded-full" />
                      </div>
                    </div>
                    <div class="flex flex-col gap-2">
                      <Skeleton class="h-4 w-full rounded-md" />
                      <Skeleton class="h-4 w-[85%] rounded-md" />
                    </div>
                  </div>
                </div>

                <div 
                  v-for="post in filteredCurrentTopicPosts" 
                  :key="post.id"
                  :id="'post-' + post.id"
                  class="w-full"
                >
                  <!-- In-Topic Donation Campaign Card -->
                  <div v-if="post.donation_campaign" class="w-full">
                    <DonationChatCard
                      :id="post.donation_campaign.id"
                      :title="post.donation_campaign.title"
                      :category="post.donation_campaign.category"
                      :status="(post.donation_campaign.status as any)"
                      :target-amount="post.donation_campaign.target_amount"
                      :collected-amount="post.donation_campaign.collected_amount"
                      :description="post.donation_campaign.description"
                      :media-url="post.donation_campaign.cover_image || post.mediaUrl || undefined"
                      :media-type="post.type === 'video' ? 'video' : 'image'"
                      :deadline="post.donation_campaign.deadline"
                      :author-name="post.author.name || 'مدیر تاپیک'"
                      :author-avatar="post.author.avatarUrl || undefined"
                      :author-role="post.author.role || undefined"
                      :topic-name="selectedTopic?.title"
                      :can-edit="isCampaignCreator(post.donation_campaign, post.author)"
                      @donate-click="handleOpenDonateModal(post.donation_campaign)"
                      @card-click="handleOpenDonateModal(post.donation_campaign)"
                      @edit-click="handleEditDonation(post.donation_campaign)"
                      @delete-click="handleDeleteDonationFromChat(post.donation_campaign)"
                    />
                  </div>

                  <!-- In-Topic Book Donation Card -->
                  <div v-else-if="post.book_donation" class="w-full">
                    <BookChatCard
                      :book="post.book_donation"
                      :topic-name="selectedTopic?.title"
                      :author-name="post.author?.name || post.book_donation.seller_name"
                      :author-avatar="post.author?.avatarUrl || undefined"
                      :can-edit="isBookOwner(post.book_donation, post.author)"
                      @claim-click="handleClaimBook"
                      @inspect-click="handleInspectBookShortCode"
                      @share-click="handleShareBook"
                    />
                  </div>

                  <!-- Standard Post Card -->
                  <PostCard 
                    v-else
                    v-bind="post"
                    @like="handlePostLike"
                    @share="handlePostShare"
                    @add-comment="handleAddComment"
                    @react="handlePostReact"
                    @delete="handlePostDelete"
                    @edit="handlePostEdit"
                    @propose-edit="handleProposeEdit"
                  />
                </div>
              </template>
              
              <div v-if="filteredCurrentTopicPosts.length === 0" class="text-center py-12 bg-card/20 rounded-xl border border-border/60 text-xs text-muted-foreground font-medium">
                {{ languageStore.t('هیچ پست یا مطلبی در این تاپیک ثبت نشده است.', 'No posts in this topic yet.') }}
              </div>

              <!-- Message Input component at the bottom of the feed -->
              <div 
                class="fixed left-1/2 -translate-x-1/2 bg-background/65 dark:bg-background/55 backdrop-blur-md border-t border-border/40 p-4 pb-[max(1rem,env(safe-area-inset-bottom))] z-40 max-w-[500px] w-full"
                :style="feedInputBarStyle"
              >
                <TopicMessageInput 
                  :key="selectedTopic ? `topic-${selectedTopic.id}-${editingPost ? 'edit' : (proposingPost ? 'propose' : 'create')}` : 'no-topic'"
                  :disabled="!isTopicCreator && !proposingPost"
                  :placeholder="proposingPost ? languageStore.t('پیشنهاد ویرایش خود را بنویسید...', 'Write your edit proposal...') : languageStore.t('یادداشت خود را بنویسید...', 'Write your note...')"
                  :isEditMode="!!editingPost"
                  :isProposalMode="!!proposingPost"
                  :proposalBannerText="proposingPost ? (proposingPost.proposalId ? languageStore.t('ویرایش پیشنهاد ویراستاری', 'Edit editorial proposal') : languageStore.t('پیشنهاد ویراستاری برای این یادداشت', 'Draft edit proposal for this note')) : ''"
                  :initialText="editingPost ? editingPost.content : (proposingPost ? proposingPost.content : (selectedTopic ? getTopicDraft(selectedTopic.id) : ''))"
                  @input-change="handleDraftChange"
                  @send="handleSendPost"
                  @save="handleSaveEdit"
                  @cancel-edit="handleCancelEdit"
                  @submit-proposal="handleSaveProposal"
                  @cancel-proposal="handleCancelProposal"
                  @attach="triggerFileSelect"
                  @attach-file="handlePastedFile"
                  @create-donation="handleOpenCreateDonation"
                  @create-book-donation="handleOpenCreateBookDonation"
                  :initialAttachments="postAttachments"
                  @removeAttachment="removePostAttachment"
                />
                <input 
                  type="file" 
                  ref="hiddenFileInput" 
                  @change="handleFileInputChange" 
                  accept="image/*,video/*,audio/*" 
                  class="hidden" 
                />
              </div>
            </div>

            <!-- Topic Edit View -->
            <div v-else-if="activeTopicSubView === 'edit'" key="edit" class="w-full">
              <TopicEditView 
                :topic="selectedTopic"
                @back="activeTopicSubView = 'feed'"
                @save="handleSaveTopicEdit"
              />
            </div>

            <!-- Topic Connections View -->
            <div v-else-if="activeTopicSubView === 'connections'" key="connections" class="w-full">
              <TopicConnectionsView 
                :topic="selectedTopic"
                :telegram-connected="telegramBotStatus === 'connected'"
                :bale-connected="baleBotStatus === 'connected'"
                @back="activeTopicSubView = 'feed'"
                @goToConnections="handleGoToConnections"
                @save="handleSaveTopicConnections"
              />
            </div>

            <!-- Topic Import History View -->
            <div v-else-if="activeTopicSubView === 'import'" key="import" class="w-full">
              <TopicImportView 
                :topic-id="selectedTopic?.id"
                @back="activeTopicSubView = 'feed'"
                @import-complete="async () => {
                  activeTopicSubView = 'feed';
                  await topicStore.loadTopics();
                  if (selectedTopic) {
                    await postStore.loadPosts(selectedTopic.id);
                    scrollToBottom(false);
                  }
                }"
                @import-failed="activeTopicSubView = 'feed'"
              />
            </div>

            <!-- Topic Admins Subview Page -->
            <div v-else-if="activeTopicSubView === 'admins'" key="admins" class="w-full">
              <TopicAdminsView 
                :topic-id="selectedTopic?.id"
                :is-owner="isTopicCreator"
                @back="activeTopicSubView = 'feed'"
                @ownership-transferred="async () => {
                  await topicStore.loadTopics();
                }"
              />
            </div>

            <!-- Topic FAQ / AI Assistant Subview Page -->
            <div v-else-if="activeTopicSubView === 'faq'" key="faq" class="w-full flex-1 flex flex-col">
              <TopicAiChatView 
                :topic="selectedTopic"
                :is-owner="isTopicCreator"
                :is-admin="isTopicCreator"
                :show-header="false"
                @back="activeTopicSubView = 'feed'"
              />
            </div>

            <!-- Topic Editorial Desk Subview Page -->
            <div v-else-if="activeTopicSubView === 'editorial'" key="editorial" class="w-full">
              <TopicEditorialView 
                :topic-id="selectedTopic?.id"
                :topic-title="selectedTopic?.title"
                :is-owner="isTopicCreator"
                @back="activeTopicSubView = 'feed'"
                @proposals-updated="async () => {
                  if (selectedTopic) {
                    await postStore.loadPosts(selectedTopic.id);
                  }
                }"
              />
            </div>
          </transition>

        </div>

        <!-- TAB 2: DONATE -->
        <div v-else-if="currentTab === 'donate'" key="donate" class="w-full flex flex-col gap-4">
          <DonationsFeed
            ref="donationsFeedRef"
            :search-query="searchQuery"
            :initial-campaign-id="pendingDonationId"
            @detail-change="(camp) => { selectedDonationCampaign = camp; if (!camp) { pendingDonationId = null } }"
            @donate-click="handleOpenDonateModal"
            @create-campaign="handleOpenCreateDonation"
            @edit-campaign="handleEditDonation"
            @topic-click="handleDonationTopicClick"
            @transparency-click="handleDonationTransparencyClick"
          />
        </div>

        <!-- TAB 3: MARKETPLACE (Temporarily disabled as requested) -->
        <!--
        <div v-else-if="currentTab === 'marketplace'" key="marketplace" class="w-full flex flex-col gap-4">
          <MarketplaceView />
        </div>
        -->

        <!-- TAB 3: PROFILE -->
        <div v-else-if="currentTab === 'profile'" key="profile" class="w-full flex flex-col gap-4.5">
          
          <transition name="fade-slide" mode="out-in">
            <!-- Subview: Connections -->
            <div v-if="activeProfileSubView === 'connections'" key="connections-list" class="flex flex-col gap-4.5">
              <!-- Connection Cards list -->
              <div class="flex flex-col gap-4.5">
                <BotConnectionCard 
                  platform="telegram"
                  :initialStatus="telegramBotStatus"
                  :initialToken="telegramBotToken"
                  :botUsername="userProfile?.telegram_bot_username"
                  @connect="handleTelegramConnect"
                  @disconnect="handleTelegramDisconnect"
                />
                <BotConnectionCard 
                  platform="bale"
                  :initialStatus="baleBotStatus"
                  :initialToken="baleBotToken"
                  :botUsername="userProfile?.bale_bot_username"
                  @connect="handleBaleConnect"
                  @disconnect="handleBaleDisconnect"
                />
              </div>
            </div>

            <!-- Subview: My Bookshelf -->
            <div v-else-if="activeProfileSubView === 'shelf'" key="profile-shelf" class="flex flex-col gap-4">
              <MyBookshelfView @shelf-changed="userStore.loadProfile()" />
            </div>

            <!-- Main Profile Menu -->
            <div v-else key="profile-main" class="w-full">
              <PlatformProfileView
                v-model:dark="isDark"
                :user-profile="userProfile"
                :topics-count="topics.length"
                :posts-count="posts.length"
                :connections-badge-text="connectionsBadgeText"
                :connections-badge-variant="connectionsBadgeVariant"
                @edit="handleProfileEdit"
                @open-shelf="activeProfileSubView = 'shelf'"
                @open-donations="currentTab = 'donate'"
                @open-connections="activeProfileSubView = 'connections'"
                @open-language="showLanguageDialog = true"
                @logout="handleLogout"
              />
            </div>
          </transition>

        </div>
      </transition>
    </div>

    <!-- Platform Navigation (Responsive: Mobile Floating Bottom Bar + Desktop Collapsible Instagram-style Sidebar) -->
    <PlatformNavigation
      v-model="currentTab"
      :dark="isDark"
      :show-mobile-nav="selectedTopic === null && selectedDonationCampaign === null"
      @toggle-theme="toggleTheme()"
      @change="(tab) => {
        selectedDonationCampaign = null;
        pendingDonationId = null;
        donationDetailFromHome = false;
        if (tab === 'home') {
          homeSubView = 'hub';
          selectedTopic = null;
          searchQuery = '';
        } else if (tab === 'topics') {
          selectedTopic = null;
          searchQuery = '';
        }
      }"
    />

    <!-- Floating Plus Button to Create Topic (Responsive: Minimal Circle on Mobile, Extended Action Button on Desktop - Mirrored on Language Switch) -->
    <Button 
      v-if="currentTab === 'topics' && selectedTopic === null"
      @click="handleCreateTopicClick()"
      class="fixed bottom-24 md:bottom-8 z-45 pointer-events-auto h-12 w-12 sm:w-auto sm:px-5 rounded-full bg-primary text-primary-foreground flex items-center justify-center sm:gap-2.5 hover:scale-105 active:scale-95 transition-all duration-300 shadow-xl shadow-primary/25 hover:shadow-primary/40 outline-none cursor-pointer p-0 sm:py-2.5"
      :class="languageStore.isFa ? 'left-6 md:left-10 lg:left-16' : 'right-6 md:right-10 lg:right-16'"
      :title="languageStore.t('ایجاد تاپیک جدید', 'Create New Topic')"
    >
      <PlusIcon class="size-5 shrink-0" />
      <span class="hidden sm:inline-block font-bold text-sm whitespace-nowrap tracking-wide">
        {{ languageStore.t('ایجاد تاپیک جدید', 'Create New Topic') }}
      </span>
    </Button>

    <!-- Create Topic Modal -->
    <CreateTopicModal 
      :is-open="isCreateModalOpen" 
      @close="isCreateModalOpen = false" 
      @create="handleCreateTopic"
    />

    <!-- Edit Profile Modal -->
    <EditProfileModal
      :is-open="isEditProfileOpen"
      :userProfile="userProfile"
      @close="isEditProfileOpen = false"
      @update="handleProfileSave"
    />

    <!-- Home In-Person Book Donation Dialog (Direct on Home, no separate catalog page) -->
    <DonateBookFromShelfDialog
      v-model:open="isHomeDonateDialogOpen"
      :initial-book-id="homeDonatePreselectedBookId"
      :initial-mode="homeDonateInitialMode"
      @donated="handleHomeBookMutated"
      @open-handover="handleOpenHandoverByCode"
    />

    <!-- Direct In-Person QR / 4-Digit OTP Handover Modal (from QR, code input, /b/:code, or 'My Books' card) -->
    <BookDonationDetailDialog
      v-model:open="isHomeHandoverDialogOpen"
      :initial-short-code="activeHandoverShortCode"
      :initial-otp="activeHandoverOtp"
      in-person-only
      @changed="handleHomeBookMutated"
    />

    <!-- Language Switcher Dialog -->
    <Dialog v-model:open="showLanguageDialog">
      <DialogContent class="sm:max-w-md rounded-3xl p-6 bg-card border border-border/60 shadow-xl">
        <DialogHeader class="text-start">
          <div class="flex items-center gap-2.5 mb-1">
            <div class="size-10 rounded-2xl bg-primary/10 text-primary flex items-center justify-center shrink-0">
              <LanguagesIcon class="size-5 text-primary" />
            </div>
            <DialogTitle class="text-base font-black text-foreground">
              {{ languageStore.t('تنظیم زبان و چیدمان برنامه', 'Language & Layout') }}
            </DialogTitle>
          </div>
          <DialogDescription class="text-xs text-muted-foreground leading-relaxed">
            {{ languageStore.t('زبان مورد نظر و جهت چیدمان رابط کاربری سامانه را انتخاب کنید.', 'Select your preferred language and UI layout direction.') }}
          </DialogDescription>
        </DialogHeader>

        <!-- Selection List -->
        <div class="flex flex-col gap-3 py-3">
          <!-- Persian Option -->
          <div 
            @click="selectedLang = 'fa'"
            class="flex items-center justify-between p-3.5 rounded-2xl border cursor-pointer transition-all duration-200 select-none"
            :class="selectedLang === 'fa' ? 'bg-primary/10 border-primary text-primary font-bold shadow-xs' : 'border-border/60 hover:bg-muted/40 text-foreground'"
          >
            <div class="flex items-center gap-3">
              <span class="text-2xl">🇮🇷</span>
              <div class="flex flex-col text-start gap-0.5">
                <span class="text-xs font-bold text-foreground">فارسی (Persian)</span>
                <span class="text-[10px] text-muted-foreground">راست‌چین / RTL Layout</span>
              </div>
            </div>
            <div 
              v-if="selectedLang === 'fa'"
              class="size-5 rounded-full bg-primary flex items-center justify-center text-primary-foreground shadow-2xs"
            >
              <CheckIcon class="size-3" />
            </div>
          </div>

          <!-- English Option -->
          <div 
            @click="selectedLang = 'en'"
            class="flex items-center justify-between p-3.5 rounded-2xl border cursor-pointer transition-all duration-200 select-none"
            :class="selectedLang === 'en' ? 'bg-primary/10 border-primary text-primary font-bold shadow-xs' : 'border-border/60 hover:bg-muted/40 text-foreground'"
          >
            <div class="flex items-center gap-3">
              <span class="text-2xl">🇬🇧</span>
              <div class="flex flex-col text-start gap-0.5">
                <span class="text-xs font-bold text-foreground">English (انگلیسی)</span>
                <span class="text-[10px] text-muted-foreground">چپ‌چین / LTR Layout</span>
              </div>
            </div>
            <div 
              v-if="selectedLang === 'en'"
              class="size-5 rounded-full bg-primary flex items-center justify-center text-primary-foreground shadow-2xs"
            >
              <CheckIcon class="size-3" />
            </div>
          </div>
        </div>

        <DialogFooter class="gap-2 sm:justify-start">
          <Button type="button" variant="outline" class="rounded-2xl" @click="showLanguageDialog = false">
            {{ languageStore.t('انصراف', 'Cancel') }}
          </Button>
          <Button type="button" class="rounded-2xl bg-primary text-primary-foreground hover:bg-primary/90 font-bold" @click="handleConfirmLanguage">
            {{ languageStore.t('تایید و ذخیره', 'Confirm & Save') }}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <!-- Delete Post Confirmation Modal -->
    <ConfirmModal
      v-model:is-open="isDeletePostOpen"
      :post="postToDelete"
      :is-selective-delete="true"
      :title="languageStore.t('حذف انتخابی پست', 'Selective Post Deletion')"
      :description="languageStore.t('انتخاب کنید پیام این پست از کدام پلتفرم‌ها حذف شود:', 'Select which platforms this post should be deleted from:')"
      @confirm="confirmPostDelete"
    />

    <!-- Delete Topic Confirmation Modal -->
    <ConfirmModal
      v-model:is-open="isDeleteTopicOpen"
      :title="languageStore.t('حذف تاپیک و تمامی پیام‌ها؟', 'Delete Topic and all its messages?')"
      :description="languageStore.t('آیا مطمئن هستید که می‌خواهید این تاپیک را به همراه تمام پیام‌های آن حذف کنید؟ این عمل غیرقابل بازگشت است.', 'Are you sure you want to delete this topic along with all its messages? This action cannot be undone.')"
      @confirm="confirmTopicDelete"
    />

    <!-- Duplicate Post Warning Dialog -->
    <DuplicateWarningDialog
      v-model:is-open="isDuplicateWarningOpen"
      :existing-post-id="duplicatePostId"
      :created-at="duplicateCreatedAt"
      :published-platforms="duplicatePlatforms"
      @force-submit="() => pendingPostMessage && handleSendPost(pendingPostMessage, true)"
      @go-to-existing="handleGoToExistingPost"
      @cancel="() => { isDuplicateWarningOpen = false; pendingPostMessage = null }"
    />

    <!-- Create / Edit Donation Campaign Dialog -->
    <CreateDonationDialog 
      v-model:open="isCreateDonationOpen"
      :topic-id="selectedTopic?.id"
      :topic-name="selectedTopic?.title"
      :author-name="userProfile?.name || 'مدیر تاپیک'"
      :author-avatar="userProfile?.avatar"
      :is-edit-mode="!!editingDonation"
      :initial-data="editingDonation"
      @created="handleDonationCreated"
      @updated="handleDonationUpdated"
    />

    <!-- Topic Book Donation Dialog -->
    <TopicBookDonationDialog
      v-model:open="isTopicBookDonationOpen"
      :topic-id="selectedTopic?.id"
      :topic-name="selectedTopic?.title"
      @published="handleBookDonationPublished"
    />

    <!-- Quick Donation Modal -->
    <DonationModal
      :open="isDonateModalOpen"
      :campaign-title="selectedDonationForPayment?.title"
      @update:open="(val) => isDonateModalOpen = val"
      @submit-donation="(amount, isAnon) => handleProcessDonationPayment({ amount, isAnonymous: isAnon })"
    />

    <!-- Confirm Delete / Stop Donation Campaign Modal (Topic Chat) -->
    <ConfirmModal
      v-model:is-open="isConfirmDeleteDonationOpen"
      :title="confirmDonationDeleteConfig.title"
      :description="confirmDonationDeleteConfig.description"
      :confirm-text="confirmDonationDeleteConfig.confirmText"
      :cancel-text="languageStore.t('انصراف', 'Cancel')"
      :variant="confirmDonationDeleteConfig.variant"
      @confirm="handleConfirmDeleteDonation"
      @cancel="isConfirmDeleteDonationOpen = false"
    />

    <!-- ZarinPal Payment Receipt / Result Modal -->
    <PaymentReceiptModal
      v-model:open="isPaymentResultModalOpen"
      :amount="paymentResultData.amount"
      :ref-id="paymentResultData.ref_id"
      :authority="paymentResultData.authority"
    />


  </div>
</template>


<style scoped>

/* Minimal Fade & Slide transition */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
