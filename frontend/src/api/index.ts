import axios from 'axios'
import { useToastStore } from '../stores/toastStore'
import { useUserStore } from '../stores/userStore'

const instance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
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
      userStore.isLoginModalOpen = true
      // Redirect to login if unauthenticated on auth page
      const path = window.location.pathname
      if (path !== '/' && path !== '/login') {
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

export const createComment = (postId: number | string, content: string) => 
  instance.post(`/api/notes/${postId}/comments/`, { content })

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

export default instance

