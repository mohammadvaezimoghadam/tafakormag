import { ref } from 'vue'
import { defineStore } from 'pinia'
import * as api from '../api'

export interface Comment {
  id: string | number
  authorName: string
  authorAvatar?: string
  text: string
  timestamp: string
}

export interface PostAuthor {
  name: string
  avatarUrl?: string
  role?: string
  phone?: string
}

export interface PostReaction {
  emoji: string
  count: number
  reacted: boolean
}

export interface Post {
  id: string | number
  author: PostAuthor
  type: 'text' | 'image' | 'video' | 'audio'
  content?: string
  mediaUrl?: string
  posterUrl?: string
  duration?: string
  timestamp: string
  likesCount?: number
  comments?: Comment[]
  liked?: boolean
  reactions?: PostReaction[]
  telegramMessageIds?: Record<string, any>
  baleMessageIds?: Record<string, any>
  publishedPlatforms?: string[]
}

export const usePostStore = defineStore('post', () => {
  const posts = ref<Post[]>([])
  const loading = ref(false)
  const loadingMore = ref(false)
  const currentPage = ref(1)
  const hasMore = ref(true)
  const totalPostsCount = ref(0)

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

  const mapComment = (c: any): Comment => {
    return {
      id: c.id,
      authorName: c.user_name || 'کاربر',
      text: c.content,
      timestamp: c.created_at || 'هم‌اکنون'
    }
  }

  const mapPost = (p: any): Post => {
    const reactions: PostReaction[] = []
    if (p.reactions_summary) {
      Object.entries(p.reactions_summary).forEach(([emoji, count]) => {
        // Skip Heart reaction from reactions array if we display it separately
        reactions.push({
          emoji,
          count: count as number,
          reacted: p.user_reaction === emoji
        })
      })
    }

    const likesCount = p.reactions_summary?.['❤️'] || 0
    const liked = p.user_reaction === '❤️'

    return {
      id: p.id,
      author: {
        name: p.author_name || 'کاربر',
        avatarUrl: getImageUrl(p.author_avatar),
        role: p.author_phone === localStorage.getItem('user_phone') ? 'نویسنده' : 'عضو تاپیک',
        phone: p.author_phone
      },
      type: p.media_type || 'text',
      content: p.content,
      mediaUrl: getImageUrl(p.media_file),
      timestamp: p.created_at || 'هم‌اکنون',
      likesCount,
      liked,
      reactions,
      comments: [],
      telegramMessageIds: p.telegram_message_ids || {},
      baleMessageIds: p.bale_message_ids || {},
      publishedPlatforms: p.published_platforms || []
    }
  }

  const loadPosts = async (topicId: number | string, page: number = 1, append: boolean = false) => {
    if (append) {
      loadingMore.value = true
    } else {
      loading.value = true
      posts.value = []
      currentPage.value = 1
      hasMore.value = true
    }

    try {
      const res = await api.fetchPosts(topicId, page, 20)
      const data = res.data

      let rawResults: any[] = []
      if (Array.isArray(data)) {
        rawResults = data
        hasMore.value = false
        totalPostsCount.value = data.length
      } else if (data && Array.isArray(data.results)) {
        rawResults = data.results
        hasMore.value = !!data.next
        totalPostsCount.value = data.count || 0
      }

      const mapped = rawResults.map(mapPost)
      mapped.reverse()

      if (append) {
        posts.value = [...mapped, ...posts.value]
      } else {
        posts.value = mapped
      }

      currentPage.value = page
      return posts.value
    } catch (err) {
      console.error('Error loading posts:', err)
      throw err
    } finally {
      loading.value = false
      loadingMore.value = false
    }
  }

  const loadNextPage = async (topicId: number | string) => {
    if (!hasMore.value || loadingMore.value || loading.value) return
    return loadPosts(topicId, currentPage.value + 1, true)
  }

  const createPost = async (formData: FormData) => {
    loading.value = true
    try {
      const res = await api.createPost(formData)
      const newPost = mapPost(res.data)
      posts.value.push(newPost)
      return newPost
    } catch (err) {
      console.error('Error creating post:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  const updatePost = async (id: string | number, formData: FormData) => {
    loading.value = true
    try {
      const res = await api.updatePost(id, formData)
      const updated = mapPost(res.data)
      const idx = posts.value.findIndex(p => p.id === id)
      if (idx !== -1) {
        posts.value[idx] = {
          ...posts.value[idx],
          ...updated
        }
      }
      return updated
    } catch (err) {
      console.error('Error updating post:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  const deletePost = async (id: string | number) => {
    loading.value = true
    try {
      await api.deletePost(id)
      posts.value = posts.value.filter(p => p.id !== id)
    } catch (err) {
      console.error('Error deleting post:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  const selectiveDeletePost = async (
    id: string | number,
    options: { delete_from_telegram: boolean; delete_from_bale: boolean; delete_from_db: boolean }
  ) => {
    loading.value = true
    try {
      await api.selectiveDeletePost(id, options)
      if (options.delete_from_db) {
        posts.value = posts.value.filter(p => p.id !== id)
      } else {
        const post = posts.value.find(p => p.id === id)
        if (post) {
          if (options.delete_from_telegram) {
            post.telegramMessageIds = {}
            post.publishedPlatforms = post.publishedPlatforms?.filter(plat => plat !== 'telegram')
          }
          if (options.delete_from_bale) {
            post.baleMessageIds = {}
            post.publishedPlatforms = post.publishedPlatforms?.filter(plat => plat !== 'bale')
          }
        }
      }
    } catch (err) {
      console.error('Error selective deleting post:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  const reactToPost = async (postId: string | number, emoji: string) => {
    try {
      await api.reactToPost(postId, emoji)
      const post = posts.value.find(p => p.id === postId)
      if (post) {
        // Find existing reaction
        const existing = post.reactions?.find(r => r.emoji === emoji)
        
        if (emoji === '❤️') {
          post.liked = !post.liked
          post.likesCount = post.liked ? (post.likesCount || 0) + 1 : Math.max(0, (post.likesCount || 1) - 1)
        }

        if (existing) {
          if (existing.reacted) {
            existing.count = Math.max(0, existing.count - 1)
            existing.reacted = false
            if (existing.count === 0) {
              post.reactions = post.reactions?.filter(r => r.emoji !== emoji)
            } else {
              post.reactions = [...(post.reactions || [])]
            }
          } else {
            existing.count++
            existing.reacted = true
            post.reactions = [...(post.reactions || [])]
          }
        } else {
          if (!post.reactions) post.reactions = []
          post.reactions = [...post.reactions, {
            emoji,
            count: 1,
            reacted: true
          }]
        }
      }
    } catch (err) {
      console.error('Error reacting to post:', err)
      throw err
    }
  }

  const likePost = async (postId: string | number, isLiked: boolean) => {
    // If local state liked status doesn't match API request (toggle)
    await reactToPost(postId, '❤️')
  }

  const fetchComments = async (postId: string | number) => {
    try {
      const res = await api.fetchComments(postId)
      const commentsList = (res.data ?? []).map(mapComment)
      const post = posts.value.find(p => p.id === postId)
      if (post) {
        post.comments = commentsList
      }
      return commentsList
    } catch (err) {
      console.error('Error fetching comments:', err)
      throw err
    }
  }

  const addComment = async (postId: string | number, content: string) => {
    try {
      const res = await api.createComment(postId, content)
      const newComment = mapComment(res.data)
      const post = posts.value.find(p => p.id === postId)
      if (post) {
        if (!post.comments) post.comments = []
        post.comments = [...post.comments, newComment]
      }
      return newComment
    } catch (err) {
      console.error('Error adding comment:', err)
      throw err
    }
  }

  return {
    posts,
    loading,
    loadingMore,
    currentPage,
    hasMore,
    totalPostsCount,
    loadPosts,
    loadNextPage,
    createPost,
    updatePost,
    deletePost,
    selectiveDeletePost,
    reactToPost,
    likePost,
    fetchComments,
    addComment
  }
})
