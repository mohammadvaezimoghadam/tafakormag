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
    {
      path: '/playground/create-donation',
      name: 'create-donation-playground',
      component: () => import('@/views/playground/CreateDonationPlayground.vue'),
    },
    {
      path: '/playground/text-formatting',
      name: 'text-formatting-playground',
      component: () => import('@/views/playground/TextFormattingPlayground.vue'),
    },
    {
      path: '/playground/marketplace-icon',
      name: 'marketplace-icon-playground',
      component: () => import('@/views/playground/MarketplaceIconPlayground.vue'),
    },
    {
      path: '/playground/quran-plugins',
      name: 'quran-plugins-playground',
      component: () => import('@/views/playground/PluginsAndQuranPlayground.vue'),
    },
    {
      path: '/playground/payment-receipt',
      name: 'payment-receipt-playground',
      component: () => import('@/views/playground/PaymentReceiptPlayground.vue'),
    },
  ],
})

export default labsRouter
