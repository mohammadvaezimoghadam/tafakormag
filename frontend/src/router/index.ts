import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/userStore'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/HomeView.vue'),
      meta: { requiresGuest: true }
    },
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/FeedView.vue')
    },
    {
      path: '/topic/:id',
      name: 'topic',
      component: () => import('@/views/FeedView.vue')
    },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('@/views/FeedView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/donate',
      name: 'donate',
      component: () => import('@/views/FeedView.vue')
    },
    {
      path: '/playground/donation-card',
      name: 'donation-card-playground',
      component: () => import('@/views/playground/DonationCardPlayground.vue')
    },
    {
      path: '/playground/create-donation',
      name: 'create-donation-playground',
      component: () => import('@/views/playground/CreateDonationPlayground.vue')
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/'
    }
  ],
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('auth_token')
  
  if (to.meta.requiresAuth && !token) {
    const userStore = useUserStore()
    userStore.isLoginModalOpen = true
    if (!from.name) {
      next({ name: 'home' })
    } else {
      next(false)
    }
  } else if (to.meta.requiresGuest && token) {
    next({ name: 'home' })
  } else {
    next()
  }
})

export default router
