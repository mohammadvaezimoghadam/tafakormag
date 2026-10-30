export interface BookDetailInfo {
  author?: string
  translator?: string
  publisher?: string
  isbn?: string | null
  publication_year?: number | null
  pages_count?: number | null
}

export interface StoreItemImage {
  id: number
  image_url: string
  is_cover: boolean
  sort_order: number
}

export interface StoreItem {
  id: number
  title: string
  slug?: string | null
  category: number
  category_name: string
  seller_name: string
  deal_type: 'sale' | 'donation'
  delivery_type: 'physical' | 'digital'
  condition?: 'new' | 'like_new' | 'used' | 'damaged' | null
  price: string
  discount_price?: string | null
  effective_price: number
  has_active_discount: boolean
  stock: number
  is_unlimited_stock: boolean
  status: 'draft' | 'available' | 'reserved' | 'completed' | 'archived'
  cover_image?: string | null
  views_count: number
  is_featured: boolean
  created_at: string
  description?: string
  city?: number | null
  city_name?: string
  province_name?: string
  weight_grams?: number
  images?: StoreItemImage[]
  book_detail?: BookDetailInfo | null
  attributes?: Array<{ id: number; attribute_key: string; attribute_value: string }>
}

export interface StoreCategory {
  id: number
  name: string
  slug: string
  icon?: string
  parent?: number | null
  children?: StoreCategory[]
  order?: number
}

export interface CartItem {
  item: StoreItem
  quantity: number
}
