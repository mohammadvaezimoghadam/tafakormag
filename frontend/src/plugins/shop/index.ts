import type { ClientPlugin } from '../core/pluginTypes'
import { shopManifest } from './manifest'

export const shopPlugin: ClientPlugin = {
  manifest: shopManifest,
  initialize: () => {
    console.log('[ShopPlugin] Tafakor Shop & Circulation Client Plugin initialized successfully.')
  },
}

export * from './manifest'
export * from './types'
export * from './api'
export { default as ShopItemCard } from './components/ShopItemCard.vue'
export { default as ShopEmptyState } from './components/ShopEmptyState.vue'
export { default as HandoverDialog } from './components/HandoverDialog.vue'
export { default as BookCitationDialog } from './components/BookCitationDialog.vue'
export { default as ShopHomeView } from './views/ShopHomeView.vue'
export { default as CopyJourneyView } from './views/CopyJourneyView.vue'

export default shopPlugin

