<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useDark, useToggle } from '@vueuse/core'

import PlatformHeader from '@/components/PlatformHeader.vue'
import PlatformNavigation from '@/components/PlatformNavigation.vue'
import PostCard from '@/components/PostCard.vue'
import TopicCard from '@/components/TopicCard.vue'
import ProfileCard from '@/components/ProfileCard.vue'
import ProfileOptionCard from '@/components/ProfileOptionCard.vue'
import CreateTopicModal from '@/components/CreateTopicModal.vue'
import EditProfileModal from '@/components/EditProfileModal.vue'
import ConfirmModal from '@/components/ConfirmModal.vue'
import DuplicateWarningDialog from '@/components/DuplicateWarningDialog.vue'
import { checkDuplicatePost, createDonationCampaign, updateDonationCampaign, donateToCampaign } from '@/api'
import BotConnectionCard from '@/components/BotConnectionCard.vue'
import TopicEditView from '@/components/TopicEditView.vue'
import TopicConnectionsView from '@/components/TopicConnectionsView.vue'
import TopicImportView from '@/components/TopicImportView.vue'
import TopicMessageInput from '@/components/TopicMessageInput.vue'
import DonationsFeed from '@/components/kindness/DonationsFeed.vue'
import CreateDonationDialog from '@/components/kindness/CreateDonationDialog.vue'
import DonationChatCard from '@/components/kindness/DonationChatCard.vue'
import DonationModal from '@/components/kindness/DonationModal.vue'
import type { CreateDonationPayload } from '@/types/kindness'
import UnderDevelopmentCard from '@/components/UnderDevelopmentCard.vue'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import { ConstructionIcon, HandHeartIcon, LinkIcon, LogOutIcon, PlusIcon, ChevronRightIcon, SunIcon, MoonIcon, LanguagesIcon, CheckIcon, Loader2Icon } from '@lucide/vue'
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

// Tab state ('home' | 'donate' | 'profile')
const currentTab = ref<'home' | 'donate' | 'profile'>('home')

// Subview connection state
const showConnections = ref(false)

// Active topic subview ('feed' | 'edit' | 'connections' | 'import' | 'admins')
const activeTopicSubView = ref<'feed' | 'edit' | 'connections' | 'import' | 'admins'>('feed')

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
  } else if (route.path.startsWith('/topic/')) {
    currentTab.value = 'home'
    const topicId = Number(route.params.id)
    if (!isNaN(topicId)) {
      const found = topics.value.find(t => t.id === topicId)
      if (found) {
        selectedTopic.value = found
      } else {
        selectedTopic.value = { id: topicId, title: languageStore.t('در حال بارگذاری...', 'Loading...') } as any
      }
    }
  } else {
    currentTab.value = 'home'
    selectedTopic.value = null
  }
}

// Watchers to sync state to route
watch(() => route.path, () => {
  syncRouteToState()
})

watch(currentTab, (newTab) => {
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
  } else if (newTab === 'home') {
    if (route.path !== '/' && !route.path.startsWith('/topic/')) {
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

// Fetch data on mount
onMounted(async () => {
  window.addEventListener('scroll', handleFeedScroll)
  try {
    await userStore.loadProfile()
    await topicStore.loadTopics()
    syncRouteToState()
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
    return selectedTopic.value !== null
  } else {
    return showConnections.value
  }
})

const headerInnerTitle = computed(() => {
  if (currentTab.value === 'home') {
    return selectedTopic.value?.title || ''
  } else {
    return languageStore.t('مدیریت اتصالات', 'Connections Management')
  }
})

const headerTitle = computed(() => {
  if (currentTab.value === 'profile') {
    return languageStore.t('پروفایل', 'Profile')
  }
  if (currentTab.value === 'donate') {
    return languageStore.t('پویش‌های اهدا', 'Donation Campaigns')
  }
  return languageStore.t('تفکر', 'Tafakor')
})

const handleHeaderBack = () => {
  if (currentTab.value === 'home') {
    if (activeTopicSubView.value !== 'feed') {
      activeTopicSubView.value = 'feed'
    } else {
      selectedTopic.value = null
    }
  } else {
    showConnections.value = false
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
const isDonateModalOpen = ref(false)
const selectedDonationForPayment = ref<any>(null)
const editingDonation = ref<any>(null)
const isEditProfileOpen = ref(false)
const isAdminsModalOpen = ref(false)
const donationsFeedRef = ref<any>(null)

const handleOpenCreateDonation = () => {
  editingDonation.value = null
  isCreateDonationOpen.value = true
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
      payload.media_files.forEach((file) => {
        if (file) formData.append('uploaded_files', file)
      })
    }

    await createDonationCampaign(formData)
    toastStore.triggerToast(languageStore.t('پویش مهربانی با موفقیت ایجاد و ارسال شد.', 'Donation campaign created and posted successfully.'), 'success')
    
    // Refresh donations feed
    if (donationsFeedRef.value) {
      donationsFeedRef.value.loadCampaigns()
    }

    // Reload posts if inside a topic
    if (selectedTopic.value) {
      await postStore.loadPosts(selectedTopic.value.id)
      scrollToBottom(true)
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
      payload.media_files.forEach((file) => {
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
    isDonateModalOpen.value = false
    toastStore.triggerToast(languageStore.t('درخواست پرداخت با موفقیت ثبت شد.', 'Payment initiated successfully.'), 'success')
    
    if (donationsFeedRef.value) {
      donationsFeedRef.value.recordLocalDonation(selectedDonationForPayment.value.id, data.amount, data.isAnonymous)
    }

    if (res.data?.gateway_url) {
      window.location.href = res.data.gateway_url
    }
  } catch (err) {
    // If backend payment fails or in demo mode, update locally with friendly notification
    if (donationsFeedRef.value) {
      donationsFeedRef.value.recordLocalDonation(selectedDonationForPayment.value.id, data.amount, data.isAnonymous)
      isDonateModalOpen.value = false
      toastStore.triggerToast(languageStore.t('مشارکت شما با موفقیت ثبت شد.', 'Your donation was recorded successfully.'), 'success')
    } else {
      toastStore.triggerToast(languageStore.t('خطا در پردازش پرداخت دونیت', 'Failed to process donation payment'), 'error')
    }
  }
}

const handleDonationTopicClick = (topicId: string | number) => {
  currentTab.value = 'home'
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

const handleCreateTopic = async (newTopic: { title: string; description: string; image?: string }) => {
  let imageFile: File | undefined = undefined
  if (newTopic.image && newTopic.image.startsWith('data:')) {
    imageFile = dataURLtoFile(newTopic.image, 'topic_image.png')
  }
  
  try {
    await topicStore.addTopic({
      title: newTopic.title,
      description: newTopic.description,
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

const handleSaveTopicEdit = async (updatedTopic: { title: string; description: string; image: string | File }) => {
  if (!selectedTopic.value) return
  try {
    await topicStore.updateTopic(selectedTopic.value.id, {
      title: updatedTopic.title,
      description: updatedTopic.description,
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
  showConnections.value = true
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

const isTopicCreator = computed<boolean>(() => {
  if (!selectedTopic.value || !userProfile.value) return false
  if (!selectedTopic.value.created_by) return true
  return Boolean(
    String(selectedTopic.value.created_by) === String(userProfile.value.id) ||
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
    <div 
      v-if="currentTab === 'profile' || currentTab === 'donate' || (currentTab === 'home' && selectedTopic === null) || (currentTab === 'home' && selectedTopic !== null && activeTopicSubView === 'feed')"
      class="sticky top-0 z-40 bg-background/60 dark:bg-background/50 backdrop-blur-md pt-4 pb-2.5"
    >
      <PlatformHeader 
        :is-inner-page="headerIsInnerPage" 
        :inner-title="headerInnerTitle" 
        :title="headerTitle" 
        :loading="!!((telegramBotStatus === 'connecting' || baleBotStatus === 'connecting') && isTopicCreator)"
        :show-options-button="!!(currentTab === 'home' && selectedTopic !== null)"
        :is-owner="isTopicCreator"
        :show-search-button="(currentTab === 'home' && selectedTopic === null) || currentTab === 'donate'"
        v-model:search-query="searchQuery"
        @back="handleHeaderBack"
        @edit-topic="handleEditTopic"
        @delete-topic="handleDeleteTopic"
        @topic-connections="handleTopicConnections"
        @topic-import="handleTopicImport"
        @topic-admins="activeTopicSubView = 'admins'"
      />
    </div>

    <!-- MAIN CONTENT AREA -->
    <div class="w-full flex-1">
      <transition name="fade-slide" mode="out-in">
        <!-- TAB 1: HOME (TOPIC LIST & DETAILS & SUBVIEWS) -->
        <div v-if="currentTab === 'home'" key="home" class="flex flex-col gap-5 w-full">
          
          <transition name="fade-slide" mode="out-in">
            <!-- List View: Search and vertical TopicCards -->
            <div v-if="selectedTopic === null" key="list" class="flex flex-col gap-5 w-full pb-20">
              <!-- Grouped TopicCards Container (Borderless list grouped inside a single glass card wrapper) -->
              <div class="flex flex-col gap-1 w-full bg-card/25 dark:bg-card/15 border border-border/50 rounded-3xl p-2.5 shadow-xs">
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
            <div v-else-if="activeTopicSubView === 'feed'" key="feed" class="flex flex-col gap-4.5 w-full pb-32">
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
                  />
                </div>
              </template>
              
              <div v-if="filteredCurrentTopicPosts.length === 0" class="text-center py-12 bg-card/20 rounded-xl border border-border/60 text-xs text-muted-foreground font-medium">
                {{ languageStore.t('هیچ پست یا مطلبی در این تاپیک ثبت نشده است.', 'No posts in this topic yet.') }}
              </div>

              <!-- Message Input component at the bottom of the feed -->
              <div class="fixed bottom-0 left-1/2 -translate-x-1/2 bg-background/65 dark:bg-background/55 backdrop-blur-md border-t border-border/40 p-4 z-40 max-w-[500px] w-full">
                <TopicMessageInput 
                  :disabled="!isTopicCreator"
                  :placeholder="languageStore.t('یادداشت خود را بنویسید...', 'Write your note...')"
                  :isEditMode="!!editingPost"
                  :initialText="editingPost ? editingPost.content : ''"
                  @send="handleSendPost"
                  @save="handleSaveEdit"
                  @cancel-edit="handleCancelEdit"
                  @attach="triggerFileSelect"
                  @create-donation="handleOpenCreateDonation"
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
              />
            </div>
          </transition>

        </div>

        <!-- TAB 2: DONATE -->
        <div v-else-if="currentTab === 'donate'" key="donate" class="w-full flex flex-col gap-4">
          <DonationsFeed
            ref="donationsFeedRef"
            :search-query="searchQuery"
            @donate-click="handleOpenDonateModal"
            @create-campaign="handleOpenCreateDonation"
            @edit-campaign="handleEditDonation"
            @topic-click="handleDonationTopicClick"
            @transparency-click="handleDonationTransparencyClick"
          />
        </div>

        <!-- TAB 3: PROFILE -->
        <div v-else-if="currentTab === 'profile'" key="profile" class="w-full flex flex-col gap-4.5">
          
          <transition name="fade-slide" mode="out-in">
            <!-- Subview: Connections -->
            <div v-if="showConnections" key="connections-list" class="flex flex-col gap-4.5">
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

            <!-- Main Profile Menu -->
            <div v-else key="profile-main" class="flex flex-col gap-4.5">
              <!-- Profile Card -->
              <ProfileCard 
                v-if="userProfile"
                v-bind="userProfile"
                :topics-count="topics.length"
                :posts-count="posts.length"
                :donations-count="userProfile.donations_count ?? 0"
                @edit="handleProfileEdit"
              />

              <!-- Options -->
              <div class="flex flex-col gap-3">
                <ProfileOptionCard 
                  :title="languageStore.t('پویش‌های اهدا', 'Donation Campaigns')"
                  :description="languageStore.t('مشاهده و مشارکت در پویش‌های مهربانی و سازندگی', 'View and participate in donation campaigns')"
                  :icon="HandHeartIcon"
                  :badge-text="languageStore.n(userProfile?.donations_count ?? 0)"
                  badge-variant="secondary"
                  @click="currentTab = 'donate'"
                />

                <ProfileOptionCard 
                  :title="languageStore.t('اتصالات پیام‌رسان', 'Messenger Connections')"
                  :description="languageStore.t('مدیریت حساب‌های متصل و سرویس‌های خارجی', 'Manage connected accounts and external services')"
                  :icon="LinkIcon"
                  :badge-text="connectionsBadgeText"
                  :badge-variant="connectionsBadgeVariant"
                  @click="showConnections = true"
                />

                <!-- Light/Dark Mode Switcher -->
                <div
                  @click="isDark = !isDark"
                  class="w-full flex items-center justify-start p-3.5 rounded-2xl bg-card/45 backdrop-blur-md border border-border/40 hover:bg-muted/40 hover:border-primary/20 transition-all duration-200 cursor-pointer select-none relative active:scale-[0.995] group gap-3.5"
                  :class="[languageStore.isFa ? 'text-right' : 'text-left']"
                  :dir="languageStore.dir"
                >
                  <!-- Right side: Icon Container -->
                  <div class="size-10 rounded-xl bg-primary/[0.03] flex items-center justify-center text-primary shrink-0 transition-transform duration-200 group-hover:scale-102">
                    <transition name="icon-pop" mode="out-in">
                      <component :is="isDark ? MoonIcon : SunIcon" class="size-5 shrink-0" :key="isDark ? 'moon' : 'sun'" />
                    </transition>
                  </div>

                  <!-- Middle: Title & Description -->
                  <div class="flex-1 flex flex-col text-start gap-1 min-w-0">
                    <span class="text-xs font-bold text-foreground truncate leading-none">
                      {{ languageStore.t('حالت تاریک', 'Dark Mode') }}
                    </span>
                    <span class="text-[10px] text-muted-foreground truncate leading-relaxed">
                      {{ languageStore.t('تغییر تم رنگی برنامه به حالت شب یا روز', 'Toggle dark or light theme for the app') }}
                    </span>
                  </div>

                  <!-- Left side: Switch toggle -->
                  <div class="flex items-center gap-2 shrink-0" @click.stop>
                    <Switch v-model:checked="isDark" />
                  </div>
                </div>

                <!-- Language Switcher Option -->
                <ProfileOptionCard 
                  :title="languageStore.t('زبان برنامه (Language)', 'App Language (Language)')"
                  :description="languageStore.t('تغییر زبان کلی سامانه و چیدمان راست‌چین/چپ‌چین', 'Toggle global app language and RTL/LTR layout')"
                  :icon="LanguagesIcon"
                  :badge-text="languageStore.currentLanguage.toUpperCase()"
                  badge-variant="secondary"
                  @click="showLanguageDialog = true"
                />

                <ProfileOptionCard 
                  :title="languageStore.t('خروج از حساب کاربری', 'Log Out')"
                  :description="languageStore.t('خروج امن از سیستم و بازگشت به صفحه ورود', 'Safely log out of system and return to login')"
                  :icon="LogOutIcon"
                  badge-variant="destructive"
                  @click="handleLogout"
                />
              </div>
            </div>
          </transition>

        </div>
      </transition>
    </div>

    <!-- Bottom Navigation tabs -->
    <div v-if="selectedTopic === null" class="fixed bottom-6 inset-x-0 flex justify-center z-45 pointer-events-none px-6">
      <div class="pointer-events-auto">
        <PlatformNavigation v-model="currentTab" />
      </div>
    </div>

    <!-- Floating Plus Button to Create Topic (Bottom Right Corner - Raised above floating tab bar, aligned inside page grid) -->
    <Button 
      v-if="currentTab === 'home' && selectedTopic === null"
      @click="handleCreateTopicClick()"
      class="fixed bottom-24 right-6 md:right-[calc(50vw-226px)] z-45 pointer-events-auto size-12 rounded-full bg-primary text-primary-foreground flex items-center justify-center hover:scale-105 active:scale-95 transition-all shadow-lg outline-none cursor-pointer p-0"
      :title="languageStore.t('ایجاد تاپیک جدید', 'Create New Topic')"
    >
      <PlusIcon class="size-6" />
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

    <!-- Quick Donation Modal -->
    <DonationModal
      :open="isDonateModalOpen"
      :campaign-title="selectedDonationForPayment?.title"
      @update:open="(val) => isDonateModalOpen = val"
      @submit-donation="(amount, isAnon) => handleProcessDonationPayment({ amount, isAnonymous: isAnon })"
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

/* Icon Pop Transition */
.icon-pop-enter-active,
.icon-pop-leave-active {
  transition: all 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.icon-pop-enter-from {
  transform: scale(0.6) rotate(-90deg);
  opacity: 0;
}

.icon-pop-leave-to {
  transform: scale(0.6) rotate(90deg);
  opacity: 0;
}
</style>
