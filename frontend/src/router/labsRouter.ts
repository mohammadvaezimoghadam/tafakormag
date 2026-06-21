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
  ],
})

export default labsRouter
