export interface CatalogItem {
  id: number
  title: string
  slug: string
  category: number
  category_name?: string
  seller_name: string
  deal_type: 'sale' | 'donation'
  deal_type_display?: string
  delivery_type: 'physical' | 'digital'
  condition: string
  price: number | string
  discount_price?: number | string | null
  effective_price: number | string
  has_active_discount: boolean
  badge_label: string
  badge_color: string
  stock: number
  is_unlimited_stock?: boolean
  status: string
  cover_image: string | null
  views_count?: number
  is_featured?: boolean
  created_at: string
}

export interface BookTitleItem {
  id: number
  title: string
  author: string
  translator?: string
  publisher?: string
  category?: string
  isbn?: string | null
  publication_year?: number | null
  edition?: string
  description?: string
  cover_image?: string | null
  source?: string
  verified_by_admin?: boolean
  created_at?: string
}

export interface BookStationItem {
  id: number
  name: string
  city?: number
  city_name?: string
  address_text: string
  latitude?: number | null
  longitude?: number | null
  capacity: number
  current_books_count: number
  is_active: boolean
}

export interface PhysicalCopyItem {
  id: string
  short_code: string
  book_title: BookTitleItem
  status: 'active' | 'transferring' | 'in_station' | 'lost' | 'retired'
  condition: string
  station?: BookStationItem | null
  station_name?: string | null
  transfer_count: number
  privacy: 'public_name' | 'first_name_only' | 'anonymous'
  is_holder?: boolean
  can_claim?: boolean
  active_transfer_id?: number | null
  active_transfer_status?: string
  created_at?: string
}

export interface TransferItem {
  id: number
  copy?: string
  copy_short_code: string
  book_title_name: string
  from_user?: number | null
  from_user_name: string
  to_user?: number | null
  to_user_name: string
  station?: number | null
  station_name?: string | null
  method: 'scan_confirm' | 'otp_fallback' | 'station_deposit' | 'station_pickup' | 'postal'
  status: 'pending_donor' | 'pending_recipient' | 'confirmed' | 'cancelled' | 'expired'
  donor_note?: string
  recipient_note?: string
  otp_code?: string
  confirmed_at?: string | null
  created_at: string
}

export interface JourneyEvent {
  id: number
  method: string
  method_display: string
  from_display_name: string
  to_display_name: string
  station_name?: string | null
  city_name?: string | null
  donor_note?: string
  recipient_note?: string
  date: string
}

export interface BookJourneyResponse {
  short_code: string
  book_title: BookTitleItem
  total_transfers: number
  journey: JourneyEvent[]
}

export interface BadgeItem {
  id: number
  slug: string
  title_fa: string
  title_en: string
  description_fa: string
  description_en: string
  icon: string
  threshold: number
  criteria: string
  order: number
}

export interface BadgeAwardItem {
  id: number
  badge: BadgeItem
  created_at: string
}

