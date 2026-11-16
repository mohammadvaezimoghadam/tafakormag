import type { PluginManifest } from '../core/pluginTypes'
import BookCitationDialog from './components/BookCitationDialog.vue'

export const shopManifest: PluginManifest = {
  manifest_version: 1,
  identifier: 'shop',
  name: 'Tafakor Shop & Circulation',
  nameFa: 'فروشگاه و گردش کتاب تفکر',
  version: '1.0.0',
  description: 'بازارچه کتب و محصولات فرهنگی، اهدای رایگان، گردش حضوری با بارکد و قفسه‌های فیزیکی تفاخر',
  descriptionFa: 'بازارچه کتب و محصولات فرهنگی، اهدای رایگان، گردش حضوری با بارکد و قفسه‌های فیزیکی تفاخر',
  author: 'Tafakor Core Team',
  icon: 'ShoppingBag',
  is_core: true,
  capabilities: ['composer_action', 'mini_app', 'search_provider'],
  scopes: ['read:content', 'read:shop'],
  routes: [
    {
      path: '/apps/shop',
      name: 'shop-home',
      component: () => import('./views/ShopHomeView.vue'),
      meta: { title: 'فروشگاه و گردش کتاب تفکر', pluginId: 'shop' },
    },
    {
      path: '/apps/shop/copy/:code',
      name: 'shop-copy-journey',
      component: () => import('./views/CopyJourneyView.vue'),
      meta: { title: 'سفرنامه کتاب', pluginId: 'shop' },
    },
  ],
  menuItems: [
    {
      id: 'shop-app',
      label: 'فروشگاه تفکر',
      labelFa: 'فروشگاه تفکر',
      icon: '🛍️',
      path: '/apps/shop',
      order: 5,
    },
  ],
  composerActions: [
    {
      id: 'shop-insert-book',
      label: 'درج کتاب یا کالا',
      labelFa: 'درج کتاب یا کالا',
      icon: '📖',
      tooltip: 'درج ارجاع به کتاب یا محصول در متن یادداشت',
      tooltipFa: 'درج ارجاع به کتاب یا محصول در متن یادداشت',
      dialogComponent: BookCitationDialog,
    },
  ],
}

