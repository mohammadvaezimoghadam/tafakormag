import axios from 'axios'
import { useToastStore } from '../stores/toastStore'
import { useUserStore } from '../stores/userStore'
import type { PostEditProposal, PostEditHistoryItem } from '@/types/editorial'

export const getApiBaseUrl = () => {
  if (import.meta.env.VITE_API_BASE_URL !== undefined && import.meta.env.VITE_API_BASE_URL !== '') {
    return import.meta.env.VITE_API_BASE_URL
  }
  return import.meta.env.DEV ? 'http://localhost:8000' : ''
}

const instance = axios.create({
  baseURL: getApiBaseUrl(),
  headers: { 'Content-Type': 'application/json' },
  timeout: 15000
})

// Request interceptor: attach token
instance.interceptors.request.use(config => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Token ${token}`
  }
  return config
})

// Response interceptor: handle errors
instance.interceptors.response.use(
  response => response,
  error => {
    const toastStore = useToastStore()

    if (!error.response) {
      toastStore.triggerToast('ارتباط با سرور برقرار نشد. لطفا اتصال اینترنت خود را بررسی کنید.', 'error')
      return Promise.reject(error)
    }

    const { status, data } = error.response
    const skipToast = error.config?.url?.includes('validate-custom-bot')

    if (status === 401) {
      const userStore = useUserStore()
      userStore.logout()
      
      const path = window.location.pathname
      const isPublicPath = path === '/' || path === '/login' || path.startsWith('/p/') || path.startsWith('/preview/') || path.startsWith('/playground')

      if (!isPublicPath) {
        userStore.isLoginModalOpen = true
        toastStore.triggerToast('جلسه کاری شما منقضی شده است. لطفا دوباره وارد شوید.', 'error')
        window.location.href = '/'
      }
    } else if (status === 400 && data?.error) {
      if (data?.code !== 'claimed_by_another_user' && !skipToast) {
        toastStore.triggerToast(data.error, 'error')
      }
    } else if (status === 404 && !skipToast) {
      toastStore.triggerToast('منبع درخواستی یافت نشد.', 'error')
    } else if (status >= 500 && !skipToast) {
      toastStore.triggerToast('خطایی در سرور رخ داده است. لطفا چند لحظه دیگر تلاش کنید.', 'error')
    } else if (!skipToast) {
      toastStore.triggerToast('خطای نامشخصی رخ داد. لطفا مجددا تلاش کنید.', 'error')
    }

    return Promise.reject(error)
  }
)

const getMultipartConfig = (data: any) => {
  return data instanceof FormData ? { headers: { 'Content-Type': 'multipart/form-data' } } : {}
}

// API functions
export const requestOtp = (phone: string, forceSms = false) => 
  instance.post('/api/auth/request-otp/', { phone, force_sms: forceSms })

export const verifyOtp = (phone: string, otp: string) => 
  instance.post('/api/auth/verify-otp/', { phone, otp })

// --- Topics API ---
export const fetchTopics = () => 
  instance.get('/api/notes/topics/')

export const createTopic = (data: any) => 
  instance.post('/api/notes/topics/', data, getMultipartConfig(data))

export const updateTopic = (id: number | string, data: any) => 
  instance.patch(`/api/notes/topics/${id}/`, data, getMultipartConfig(data))

export const deleteTopic = (id: number | string) => 
  instance.delete(`/api/notes/topics/${id}/`)

// --- Posts API ---
export const fetchPosts = (topicId?: number | string, page: number = 1, pageSize: number = 20) => 
  instance.get('/api/notes/', { 
    params: { 
      ...(topicId ? { topic: topicId } : {}),
      page,
      page_size: pageSize
    } 
  })

export const fetchPostDetails = (id: number | string) =>
  instance.get(`/api/notes/${id}/`)

export const createPost = (data: FormData) => 
  instance.post('/api/notes/', data, {
    ...getMultipartConfig(data),
    timeout: 0
  })

export const updatePost = (id: number | string, data: any) => 
  instance.patch(`/api/notes/${id}/`, data, {
    ...getMultipartConfig(data),
    timeout: 0
  })

export const deletePost = (id: number | string) => 
  instance.delete(`/api/notes/${id}/`)

export const selectiveDeletePost = (id: number | string, payload: { delete_from_telegram: boolean; delete_from_bale: boolean; delete_from_db: boolean }) => 
  instance.post(`/api/notes/${id}/selective-delete/`, payload)

export const checkDuplicatePost = (topicId: number | string, content: string) => 
  instance.post('/api/notes/check-duplicate/', { topic: topicId, content })

export const searchPosts = (query: string) => 
  instance.get('/api/notes/search/', { params: { q: query } })

// --- Reactions & Comments API ---
export const reactToPost = (postId: number | string, emoji: string) => 
  instance.post(`/api/notes/${postId}/react/`, { emoji })

export const fetchComments = (postId: number | string) => 
  instance.get(`/api/notes/${postId}/comments/`)

export const createComment = (postId: number | string, content: string, isAnonymous: boolean = false, authorName: string = '') => 
  instance.post(`/api/notes/${postId}/comments/`, { 
    content, 
    is_anonymous: isAnonymous, 
    author_name: authorName 
  })

export const createAnonymousComment = (postId: number | string, content: string, authorName: string = '') => 
  instance.post(`/api/notes/${postId}/comments/`, { 
    content, 
    is_anonymous: true, 
    author_name: authorName 
  })

// --- Destinations API ---
export const fetchDestinations = (platform: 'telegram' | 'bale') => 
  instance.get('/api/auth/destinations/', { params: { platform } })

export const createDestination = (data: any) => 
  instance.post('/api/auth/destinations/', data)

export const deleteUserDestination = (id: number | string) => 
  instance.post('/api/auth/delete-user-destination/', { destination_id: id })

// --- Profile & Bot APIs ---
export const getConnectToken = (platform: 'telegram' | 'bale') => 
  instance.get('/api/auth/connect-token/', { params: { platform } })

export const updateCustomBot = (platform: 'telegram' | 'bale', token: string, force = false) => 
  instance.post('/api/auth/update-custom-bot/', { platform, token, force })

export const validateCustomBot = (platform: 'telegram' | 'bale', token: string) => 
  instance.post('/api/auth/validate-custom-bot/', { platform, token })

export const fetchProfile = () => 
  instance.get('/api/auth/profile/')

export const updateProfile = (data: FormData) => 
  instance.patch('/api/auth/profile/', data, getMultipartConfig(data))

export const importHistory = (
  topicId: number | string, 
  data: FormData, 
  onUploadProgress?: (progressEvent: any) => void
) =>
  instance.post(`/api/notes/topics/${topicId}/import-json/`, data, {
    ...getMultipartConfig(data),
    timeout: 0,
    onUploadProgress
  })

export const getImportStatus = (taskId: string) =>
  instance.get(`/api/notes/import-tasks/${taskId}/status/`)

// --- Topic Admins API ---
export interface UserSimple {
  id: string | number
  phone: string
  first_name?: string
  last_name?: string
  profile_image?: string | null
}

export interface TopicAdmin {
  id: string
  user: UserSimple
  custom_title: string
  promoted_by?: UserSimple | null
  created_at: string
}

export const getTopicAdmins = (topicId: string | number) =>
  instance.get<{ owner: UserSimple | null; admins: TopicAdmin[] }>(`/api/notes/topics/${topicId}/admins/`)

export const addTopicAdmin = (
  topicId: string | number,
  payload: { user_id: string | number; custom_title?: string }
) =>
  instance.post<TopicAdmin>(`/api/notes/topics/${topicId}/add_admin/`, payload)

export const removeTopicAdmin = (topicId: string | number, userId: string | number) =>
  instance.delete<{ message: string }>(`/api/notes/topics/${topicId}/remove_admin/${userId}/`)

export const transferTopicOwnership = (
  topicId: string | number,
  payload: { new_owner_id: string | number }
) =>
  instance.post<{ message: string; owner: UserSimple }>(`/api/notes/topics/${topicId}/transfer_ownership/`, payload)

// --- Donations API ---
export const fetchDonationCampaigns = (params?: { category?: string; status?: string; topic?: string | number; search?: string }) =>
  instance.get('/api/v1/donations/campaigns/', { params })

export const fetchDonationCampaign = (id: string | number) =>
  instance.get(`/api/v1/donations/campaigns/${id}/`)

export const createDonationCampaign = (data: FormData) =>
  instance.post('/api/v1/donations/campaigns/', data, getMultipartConfig(data))

export const updateDonationCampaign = (id: string | number, data: FormData | Record<string, any>) =>
  instance.patch(`/api/v1/donations/campaigns/${id}/`, data, data instanceof FormData ? getMultipartConfig(data) : undefined)

export const deleteDonationCampaign = (id: string | number) =>
  instance.delete(`/api/v1/donations/campaigns/${id}/`)

export const donateToCampaign = (campaignId: string | number, payload: { amount: number; is_anonymous?: boolean }) =>
  instance.post(`/api/v1/donations/campaigns/${campaignId}/donate/`, payload)

// --- Topic FAQs API ---
export interface TopicFAQ {
  id: number
  topic: number
  question: string
  answer: string
  order: number
  is_published: boolean
  created_by?: UserSimple | null
  created_at: string
  updated_at: string
}

export const fetchTopicFaqs = (topicId: string | number, search?: string) =>
  instance.get<TopicFAQ[]>(`/api/notes/topics/${topicId}/faqs/`, {
    params: search ? { search } : undefined
  })

export const createTopicFaq = (
  topicId: string | number,
  payload: { question: string; answer: string; order?: number; is_published?: boolean }
) =>
  instance.post<TopicFAQ>(`/api/notes/topics/${topicId}/faqs/`, payload)

export const updateTopicFaq = (
  faqId: string | number,
  payload: Partial<{ question: string; answer: string; order?: number; is_published?: boolean }>
) =>
  instance.patch<TopicFAQ>(`/api/notes/faqs/${faqId}/`, payload)

export const deleteTopicFaq = (faqId: string | number) =>
  instance.delete(`/api/notes/faqs/${faqId}/`)

export const reorderTopicFaqs = (
  topicId: string | number,
  orders: { id: number | string; order: number }[]
) =>
  instance.post(`/api/notes/faqs/reorder/`, { topic_id: topicId, orders })

// --- Topic AI Chat (RAG) API ---
export interface TopicChatSource {
  type: 'post' | 'faq'
  id: number
  title: string
  preview?: string
  author?: string
  created_at?: string
}

export interface TopicChatMessage {
  id: string
  session?: string
  role: 'user' | 'assistant' | 'system'
  content: string
  sources?: TopicChatSource[]
  created_at: string
}

export interface TopicChatResponse {
  session_id: string
  user_message: TopicChatMessage
  assistant_message: TopicChatMessage
}

export const sendTopicChatMessage = (
  topicId: string | number,
  message: string,
  sessionId?: string | null
) =>
  instance.post<TopicChatResponse>(`/api/notes/topics/${topicId}/chat/`, {
    message,
    session_id: sessionId || undefined
  })

export const fetchTopicChatHistory = (
  topicId: string | number,
  sessionId?: string | null
) =>
  instance.get<{ session_id: string | null; messages: TopicChatMessage[] }>(
    `/api/notes/topics/${topicId}/chat-history/`,
    { params: sessionId ? { session_id: sessionId } : undefined }
  )

export const clearTopicChatHistory = (
  topicId: string | number,
  sessionId?: string | null
) =>
  instance.post(`/api/notes/topics/${topicId}/chat-clear/`, {
    session_id: sessionId || undefined
  })

// --- Editorial Workflow API ---
export const fetchEditProposals = (params?: {
  topic_id?: string | number
  post_id?: string | number
  status?: string
}) =>
  instance.get<PostEditProposal[]>('/api/notes/editorial/proposals/', { params })

export const submitEditProposal = (payload: {
  post_id: string | number
  proposed_content: string
  reason?: string
}) =>
  instance.post<PostEditProposal>('/api/notes/editorial/proposals/', payload)

export const updateEditProposal = (
  proposalId: string | number,
  payload: {
    proposed_content?: string
    proposedContent?: string
    reason?: string
  }
) =>
  instance.patch<PostEditProposal>(`/api/notes/editorial/proposals/${proposalId}/`, payload)

export const approveEditProposal = (
  proposalId: string | number,
  reviewNote?: string
) =>
  instance.post<PostEditProposal>(`/api/notes/editorial/proposals/${proposalId}/approve/`, {
    review_note: reviewNote || undefined
  })

export const rejectEditProposal = (
  proposalId: string | number,
  reviewNote?: string
) =>
  instance.post<PostEditProposal>(`/api/notes/editorial/proposals/${proposalId}/reject/`, {
    review_note: reviewNote || undefined
  })

export const approveAllEditProposals = (topicId: string | number) =>
  instance.post<{ message: string; approved_count: number }>(
    '/api/notes/editorial/proposals/approve-all/',
    { topic_id: topicId }
  )

export const fetchPostEditHistory = (postId: string | number) =>
  instance.get<PostEditHistoryItem[]>('/api/notes/editorial/history/', {
    params: { post_id: postId }
  })

export default instance


