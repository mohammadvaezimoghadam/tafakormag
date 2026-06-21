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
}

export const usePostStore = defineStore('post', () => {
  const posts = ref<Post[]>([])
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

  const mapComment = (c: any): Comment => {
    const formattedDate = c.created_at ? new Date(c.created_at).toLocaleDateString('fa-IR', {
      hour: '2-digit',
      minute: '2-digit'
    }) : 'هم‌اکنون'
    
    return {
      id: c.id,
      authorName: c.user_name || 'کاربر',
      text: c.content,
      timestamp: formattedDate
    }
  }

  const mapPost = (p: any): Post => {
    const formattedDate = p.created_at ? new Date(p.created_at).toLocaleDateString('fa-IR', {
      hour: '2-digit',
      minute: '2-digit'
    }) : 'هم‌اکنون'
    
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
        role: p.author_phone === localStorage.getItem('user_phone') ? 'نویسنده' : 'عضو تاپیک'
      },
      type: p.media_type || 'text',
      content: p.content,
      mediaUrl: getImageUrl(p.media_file),
      timestamp: formattedDate,
      likesCount,
      liked,
      reactions,
      comments: []
    }
  }

  const loadPosts = async (topicId: number | string) => {
    loading.value = true
    try {
      const res = await api.fetchPosts(topicId)
      posts.value = (res.data ?? []).map(mapPost)
      return posts.value
    } catch (err) {
      console.error('Error loading posts:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  const createPost = async (formData: FormData) => {
    loading.value = true
    try {
      const res = await api.createPost(formData)
      const newPost = mapPost(res.data)
      posts.value.unshift(newPost)
      return newPost
    } catch (err) {
      console.error('Error creating post:', err)
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
            }
          } else {
            existing.count++
            existing.reacted = true
          }
        } else {
          if (!post.reactions) post.reactions = []
          post.reactions.push({
            emoji,
            count: 1,
            reacted: true
          })
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
        post.comments.push(newComment)
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
    loadPosts,
    createPost,
    deletePost,
    reactToPost,
    likePost,
    fetchComments,
    addComment
  }
})
