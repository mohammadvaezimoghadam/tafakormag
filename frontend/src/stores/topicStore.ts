import { ref } from 'vue'
import { defineStore } from 'pinia'
import * as api from '../api'

export interface Topic {
  id: number
  title: string // maps to name in backend
  description: string
  post_badge?: string
  image?: string
  unreadCount?: number // maps to post_count in backend
  time: string // formatted created_at
  labels?: string[]
  pinned?: boolean
  created_by?: number
  created_by_phone?: string
  telegram_bot_active?: boolean
  bale_bot_active?: boolean
  telegram_connections?: any[]
  bale_connections?: any[]
}

export const useTopicStore = defineStore('topic', () => {
  const topics = ref<Topic[]>([])
  const selectedTopic = ref<Topic | null>(null)
  const loading = ref(false)

  const getImageUrl = (url?: string) => {
    if (!url) return ''
    const mediaIdx = url.indexOf('/media/')
    if (mediaIdx !== -1) {
      url = url.slice(mediaIdx)
    }
    const staticIdx = url.indexOf('/static/')
    if (staticIdx !== -1) {
      url = url.slice(staticIdx)
    }
    if (url.startsWith('http://') || url.startsWith('https://')) {
      return url
    }
    if (url.startsWith('//')) {
      url = url.slice(1)
    }
    const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
    if (apiBase === '/') {
      return url
    }
    const base = apiBase.endsWith('/') ? apiBase.slice(0, -1) : apiBase
    const path = url.startsWith('/') ? url : '/' + url
    return `${base}${path}`
  }

  const mapTopic = (data: any): Topic => {
    return {
      id: data.id,
      title: data.name,
      description: data.description || '',
      post_badge: data.post_badge || '',
      image: getImageUrl(data.image),
      unreadCount: data.post_count || 0,
      time: data.created_at || 'هم‌اکنون',
      labels: data.telegram_bot_active || data.bale_bot_active ? ['فعال'] : [],
      pinned: false,
      created_by: data.created_by,
      created_by_phone: data.created_by_phone,
      telegram_bot_active: data.telegram_bot_active,
      bale_bot_active: data.bale_bot_active,
      telegram_connections: data.telegram_connections,
      bale_connections: data.bale_connections
    }
  }

  const loadTopics = async () => {
    loading.value = true
    try {
      const res = await api.fetchTopics()
      topics.value = (res.data ?? []).map(mapTopic)
      
      // Update selectedTopic reference if it's currently set
      if (selectedTopic.value) {
        const found = topics.value.find(t => t.id === selectedTopic.value?.id)
        if (found) {
          selectedTopic.value = found
        }
      }
      return topics.value
    } catch (err) {
      console.error('Error loading topics:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  const addTopic = async (newTopic: { title: string; description: string; post_badge?: string; image?: File }) => {
    loading.value = true
    try {
      const formData = new FormData()
      formData.append('name', newTopic.title)
      formData.append('description', newTopic.description)
      if (newTopic.post_badge !== undefined) {
        formData.append('post_badge', newTopic.post_badge)
      }
      if (newTopic.image) {
        formData.append('image', newTopic.image)
      }
      const res = await api.createTopic(formData)
      await loadTopics()
      return mapTopic(res.data)
    } catch (err) {
      console.error('Error adding topic:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  const deleteTopic = async (id: number) => {
    loading.value = true
    try {
      await api.deleteTopic(id)
      if (selectedTopic.value?.id === id) {
        selectedTopic.value = null
      }
      await loadTopics()
    } catch (err) {
      console.error('Error deleting topic:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  const updateTopic = async (id: number, updatedTopic: { title: string; description: string; post_badge?: string; image?: string | File }) => {
    loading.value = true
    try {
      let payload: any
      if (updatedTopic.image instanceof File) {
        payload = new FormData()
        payload.append('name', updatedTopic.title)
        payload.append('description', updatedTopic.description)
        if (updatedTopic.post_badge !== undefined) {
          payload.append('post_badge', updatedTopic.post_badge)
        }
        payload.append('image', updatedTopic.image)
      } else {
        payload = {
          name: updatedTopic.title,
          description: updatedTopic.description
        }
        if (updatedTopic.post_badge !== undefined) {
          payload.post_badge = updatedTopic.post_badge
        }
        if (updatedTopic.image === '') {
          payload.image = null
        }
      }
      
      const res = await api.updateTopic(id, payload)
      await loadTopics()
      
      const mapped = mapTopic(res.data)
      if (selectedTopic.value?.id === id) {
        selectedTopic.value = mapped
      }
      return mapped
    } catch (err) {
      console.error('Error updating topic:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  const saveTopicConnections = async (id: number, data: { 
    telegram_bot_active: boolean
    bale_bot_active: boolean
    telegram_connections: number[]
    bale_connections: number[] 
  }) => {
    loading.value = true
    try {
      const res = await api.updateTopic(id, data)
      await loadTopics()
      const mapped = mapTopic(res.data)
      if (selectedTopic.value?.id === id) {
        selectedTopic.value = mapped
      }
      return mapped
    } catch (err) {
      console.error('Error saving connections:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    topics,
    selectedTopic,
    loading,
    loadTopics,
    addTopic,
    deleteTopic,
    updateTopic,
    saveTopicConnections
  }
})
