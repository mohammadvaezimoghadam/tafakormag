export type ShelfBookFormat = 'physical' | 'digital'
export type ShelfReadingStatus = 'in_shelf' | 'want_to_read' | 'reading' | 'finished'
export type ShelfDisposition = 'keeping' | 'circulating' | 'for_donation' | 'for_sale'
export type ShelfCondition = 'new' | 'like_new' | 'good' | 'fair' | 'worn'
export type DonationMethod = 'in_person' | 'postal' | 'station' | 'digital'
export type ShippingPayer = 'recipient' | 'donor'

export interface ShelfBookTitle {
  id: number
  title: string
  author: string
  translator: string
  publisher: string
  category: string
  isbn: string | null
  publication_year: number | null
  edition: string
  description: string
  cover_image: string | null
  source: string
  verified_by_admin: boolean
  created_at: string
}

export interface ShelfLinkedCopySummary {
  id: string
  short_code: string
  status: string
  status_display: string
  transfer_count: number
  station_id?: number | null
  station_name?: string | null
  is_transferred_away: boolean
}

export interface BookStationSummary {
  id: number
  name: string
  city?: number | null
  city_name: string
  address_text: string
  capacity?: number
  current_books_count?: number
  is_active?: boolean
}

export interface ShelfLinkedItemSummary {
  id: number
  title: string
  deal_type: 'sale' | 'donation' | string
  deal_type_display: string
  delivery_type: string
  donation_methods?: DonationMethod[]
  donation_method_labels?: string[]
  shipping_payer?: ShippingPayer
  book_station_id?: number | null
  book_station_name?: string | null
  price: string | number
  stock: number
  status: string
  status_display: string
  category: number | null
  category_name: string
}

export interface ShelfBook {
  id: number
  book_title: ShelfBookTitle
  book_format: ShelfBookFormat
  book_format_display: string
  reading_status: ShelfReadingStatus
  reading_status_display: string
  disposition: ShelfDisposition
  disposition_display: string
  donation_methods: DonationMethod[]
  donation_method_labels: string[]
  shipping_payer: ShippingPayer
  preferred_station_summary: BookStationSummary | null
  quantity: number
  reserved_quantity?: number
  available_quantity?: number
  is_gift?: boolean
  can_donate?: boolean
  gifted_by_name?: string | null
  condition: ShelfCondition | null
  condition_display: string | null
  personal_note: string
  digital_reference: string
  acquired_from: string
  rating: number | null
  physical_copy_summary: ShelfLinkedCopySummary | null
  marketplace_item_summary: ShelfLinkedItemSummary | null
  created_at: string
  updated_at: string
}

export interface ShelfSummary {
  total: number
  total_copies?: number
  reading_count?: number
  finished_count?: number
  want_to_read_count?: number
  keeping_count?: number
  offering_count?: number
}

export interface ShelfListFilters {
  search?: string
  reading_status?: ShelfReadingStatus | ''
  disposition?: ShelfDisposition | ''
  book_format?: ShelfBookFormat | ''
}

export interface ShelfBookCreatePayload {
  book_title_id?: number | null
  title?: string
  author?: string
  translator?: string
  publisher?: string
  category?: string
  isbn?: string | null
  publication_year?: number | null
  edition?: string
  description?: string
  book_format: ShelfBookFormat
  reading_status: ShelfReadingStatus
  quantity?: number
  condition?: ShelfCondition | null
  personal_note?: string
  digital_reference?: string
  acquired_from?: string
  rating?: number | null
  cover_image?: File | null
}

export interface ShelfBookUpdatePayload {
  book_format?: ShelfBookFormat
  reading_status?: ShelfReadingStatus
  quantity?: number
  condition?: ShelfCondition | null
  personal_note?: string
  digital_reference?: string
  acquired_from?: string
  rating?: number | null
  cover_image?: File | null
}

export interface ShelfStartCirculationPayload {
  condition?: ShelfCondition | null
  privacy?: 'full_name' | 'first_name_only' | 'anonymous'
}

export interface ShelfPublishListingPayload {
  deal_type: 'donation' | 'sale'
  price?: number
  donation_methods?: DonationMethod[]
  station_id?: number | null
  deposit_now?: boolean
  shipping_payer?: ShippingPayer
  privacy?: 'full_name' | 'first_name_only' | 'anonymous'
  category_id?: number | null
  topic_id?: number | null
  city_id?: number | null
  stock?: number
  weight_grams?: number
  description?: string
  digital_file_key?: string
  file_format?: string
}

export interface MarketplaceCategory {
  id: number
  name: string
  slug: string
  children?: MarketplaceCategory[]
}

export interface HomeMarketplaceItem {
  id: number
  title: string
  slug: string | null
  author?: string | null
  book_title_id?: number | null
  category: number | null
  category_name: string
  seller?: number
  seller_name: string
  deal_type: 'sale' | 'donation'
  deal_type_display: string
  delivery_type: 'physical' | 'digital'
  donation_methods?: DonationMethod[]
  donation_method_labels?: string[]
  shipping_payer?: ShippingPayer
  physical_copy_summary?: {
    id: string
    short_code: string
    status: string
    transfer_count: number
  } | null
  station_summary?: BookStationSummary | null
  condition: string | null
  price: string | number
  discount_price: string | number | null
  effective_price: string | number
  has_active_discount: boolean
  badge_label: string
  badge_color: string
  stock: number
  is_unlimited_stock: boolean
  status: string
  cover_image: string | null
  views_count: number
  is_featured: boolean
  created_at: string
}

export interface DonationRequestItem {
  id: number
  item: HomeMarketplaceItem
  requester: number
  requester_name: string
  message: string
  status: 'pending' | 'accepted' | 'rejected' | 'cancelled'
  created_at: string
}

export interface BookTransferRecord {
  id: number
  short_code?: string
  copy_short_code?: string
  book_title_name?: string
  book_author?: string
  from_user?: number | null
  from_user_name?: string
  to_user?: number | null
  to_user_name?: string
  station?: number | null
  method: string
  status: string
  quantity?: number
  otp_code?: string
  otp_expires_at?: string | null
  donor_note?: string
  recipient_note?: string
  created_at: string
  confirmed_at?: string | null
}

export interface BookCopyInspectResult {
  id: string
  short_code: string
  book_title: ShelfBookTitle
  status: string
  status_display?: string
  condition?: string
  station: BookStationSummary | null
  transfer_count: number
  privacy?: string
  is_holder: boolean
  can_claim: boolean
  available_quantity?: number
  active_transfer_id: number | null
  active_transfer: BookTransferRecord | null
  created_at?: string
}

export interface BookCopyJourneyResult {
  short_code: string
  book_title: ShelfBookTitle
  total_transfers: number
  journey: Array<{
    id: number
    method: string
    method_display?: string
    quantity?: number
    from_display_name?: string
    to_display_name?: string
    station_name?: string | null
    city_name?: string | null
    donor_note?: string
    recipient_note?: string
    date?: string
  }>
}

export interface HomeDonationCampaign {
  id: string
  title: string
  description: string
  category: string
  status: string
  target_amount: number
  collected_amount: number
  donors_count: number
  cover_image: string | null
  deadline: string | null
  creator_info?: {
    id: number
    name: string
    avatar: string | null
    phone?: string
  } | null
  attachments?: {
    id: string
    url: string
    is_video: boolean
  }[]
  created_at: string
}

export interface BookDonationPostData {
  id: number
  title: string
  author?: string
  publisher?: string
  description?: string
  deal_type?: string
  status?: string
  condition?: string
  condition_display?: string
  donation_methods?: DonationMethod[]
  short_code?: string | null
  shipping_payer?: ShippingPayer
  cover_image?: string | null
  seller_name?: string | null
  seller_phone?: string | null
}

export interface IncomingGiftItem {
  transfer_id: number
  short_code: string
  book_title: string
  book_author?: string
  cover_image?: string | null
  from_user_name: string
  from_user_phone?: string
  quantity: number
  created_at: string
}

export interface DonateToPhonePayload {
  quantity?: number
  recipient_phone: string
  send_sms?: boolean
}

export interface DonateToPhoneResult {
  status: string
  transfer_id: number
  short_code: string
  recipient_phone: string
  sms_sent: boolean
  message: string
}

export interface UserSearchResult {
  id: number
  phone: string
  name: string
  full_name?: string
  first_name?: string
  last_name?: string
  avatar?: string | null
}

export interface AdminDonationReportItem {
  id: number
  book_title: string
  cover_image: string | null
  quantity: number
  recipient_phone: string
  recipient_name: string | null
  admin_name: string
  status?: string
  status_display?: string
  created_at: string
}

export interface AdminDonatePayload {
  quantity: number
  recipient_phone: string
}



