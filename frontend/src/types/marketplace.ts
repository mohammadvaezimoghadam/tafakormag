export interface MarketplaceApp {
  id: string | number
  title: string
  description?: string
  iconUrl?: string
  icon?: any // Lucide component reference
  isComingSoon?: boolean
  badge?: string
  badgeVariant?: 'default' | 'secondary' | 'outline' | 'destructive'
  category?: string
  developer?: string
  rating?: number
  downloadsCount?: number
  isInstalled?: boolean
  version?: string
  screenshots?: string[]
}

export type AppIconSize = 'sm' | 'md' | 'lg' | 'responsive'
