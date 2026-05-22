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

export const fetchNotes = () => instance.get('/api/notes/')

export const searchNotes = (query) => instance.get('/api/notes/search/', { params: { q: query } })

export const createNote = (data) => instance.post('/api/notes/', data)

export const updateNote = (id, data) => instance.patch(`/api/notes/${id}/`, data)

export const deleteNote = (id) => instance.delete(`/api/notes/${id}/`)

export const getConnectToken = (platform) => instance.get('/api/auth/connect-token/', { params: { platform } })

export default instance