import { createRouter, createWebHistory } from 'vue-router'

const labsRouter = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/showcase',
    },
    {
      path: '/showcase',
      name: 'showcase',
      component: () => import('@/showcase/ShowcaseView.vue'),
    },
    {
      path: '/playground',
      name: 'playground',
      component: () => import('@/playground/PlaygroundView.vue'),
    },
    {
      path: '/playground/donation-card',
      name: 'donation-card-playground',
      component: () => import('@/views/playground/DonationCardPlayground.vue'),
    },
  ],
})

export default labsRouter
