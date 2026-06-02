import axios from 'axios'
import { toastState } from '../store/toastState'

const instance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' },
  timeout: 10000
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
    if (!error.response) {
      toastState.add({ message: 'قطع ارتباط با سرور', type: 'error' })
      return Promise.reject(error)
    }

    const { status, data } = error.response

    if (status === 401) {
      localStorage.removeItem('auth_token')
      toastState.add({ message: 'لطفاً دوباره وارد شوید', type: 'error' })
      window.location.href = '/login'
    } else if (status === 400 && data?.error) {
      toastState.add({ message: data.error, type: 'error' })
    } else if (status === 404) {
      toastState.add({ message: 'یافت نشد', type: 'error' })
    } else if (status >= 500) {
      toastState.add({ message: 'خطای سرور. لحظاتی دیگر تلاش کنید', type: 'error' })
    } else {
      toastState.add({ message: 'خطایی رخ داد', type: 'error' })
    }

    return Promise.reject(error)
  }
)

// API functions
export const requestOtp = (phone, forceSms = false) => instance.post('/api/auth/request-otp/', { phone, force_sms: forceSms })

export const verifyOtp = (phone, otp) => instance.post('/api/auth/verify-otp/', { phone, otp })

// --- Topics API ---
export const fetchTopics = () => instance.get('/api/notes/topics/')

export const createTopic = (data) => instance.post('/api/notes/topics/', data, {
  headers: { 'Content-Type': 'multipart/form-data' }
})

export const updateTopic = (id, data) => instance.patch(`/api/notes/topics/${id}/`, data, {
  headers: { 'Content-Type': 'multipart/form-data' }
})

export const deleteTopic = (id) => instance.delete(`/api/notes/topics/${id}/`)

// --- Posts API ---
export const fetchPosts = (topicId) => instance.get('/api/notes/', { params: { topic: topicId } })

export const createPost = (data) => instance.post('/api/notes/', data, {
  headers: { 'Content-Type': 'multipart/form-data' }
})

export const updatePost = (id, data) => instance.patch(`/api/notes/${id}/`, data, {
  headers: { 'Content-Type': 'multipart/form-data' }
})

export const deletePost = (id) => instance.delete(`/api/notes/${id}/`)

export const searchPosts = (query) => instance.get('/api/notes/search/', { params: { q: query } })

// --- Reactions & Comments API ---
export const reactToPost = (postId, emoji) => instance.post(`/api/notes/${postId}/react/`, { emoji })

export const fetchComments = (postId) => instance.get(`/api/notes/${postId}/comments/`)

export const createComment = (postId, content) => instance.post(`/api/notes/${postId}/comments/`, { content })

// --- Destinations API ---
export const fetchDestinations = (platform) => instance.get('/api/auth/destinations/', { params: { platform } })

// --- Profile & Bot APIs ---
export const getConnectToken = (platform) => instance.get('/api/auth/connect-token/', { params: { platform } })

export const updateCustomBot = (platform, token) => instance.post('/api/auth/update-custom-bot/', { platform, token })

export const fetchProfile = () => instance.get('/api/auth/profile/')

export const updateProfile = (data) => instance.patch('/api/auth/profile/', data, {
  headers: { 'Content-Type': 'multipart/form-data' }
})

export default instance