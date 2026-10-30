import { ref, computed, watch } from 'vue'
import type { StoreItem, StoreCategory, CartItem } from '@/types/store'

// Global shared state for cart across components
const cartItems = ref<CartItem[]>([])

// Load cart from localStorage
try {
  const savedCart = localStorage.getItem('tafakor_store_cart')
  if (savedCart) {
    cartItems.value = JSON.parse(savedCart)
  }
} catch (e) {
  console.warn('Failed to parse saved cart:', e)
}

// Save cart on change
watch(cartItems, (newVal) => {
  try {
    localStorage.setItem('tafakor_store_cart', JSON.stringify(newVal))
  } catch (e) {
    console.warn('Failed to save cart to localStorage:', e)
  }
}, { deep: true })

export function useStoreCatalog() {
  const items = ref<StoreItem[]>([])
  const categories = ref<StoreCategory[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Filters
  const searchQuery = ref('')
  const selectedCategoryId = ref<number | null>(null)
  const selectedDealType = ref<'all' | 'sale' | 'donation'>('all')
  const selectedDeliveryType = ref<'all' | 'physical' | 'digital'>('all')
  const inStockOnly = ref(false)
  const hasDiscountOnly = ref(false)
  const minPrice = ref<number | null>(null)
  const maxPrice = ref<number | null>(null)
  const sortBy = ref<string>('newest')

  // Computed helper for active filter count (excluding search query)
  const activeFiltersCount = computed(() => {
    let count = 0
    if (selectedCategoryId.value !== null) count++
    if (selectedDealType.value !== 'all') count++
    if (selectedDeliveryType.value !== 'all') count++
    if (inStockOnly.value) count++
    if (hasDiscountOnly.value) count++
    if (minPrice.value !== null || maxPrice.value !== null) count++
    return count
  })

  const hasActiveFilters = computed(() => {
    return activeFiltersCount.value > 0 || searchQuery.value.trim().length > 0
  })

  const selectedCategoryObj = computed(() => {
    if (selectedCategoryId.value === null) return null
    return categories.value.find(c => c.id === selectedCategoryId.value) || null
  })

  const clearAllFilters = () => {
    selectedCategoryId.value = null
    selectedDealType.value = 'all'
    selectedDeliveryType.value = 'all'
    inStockOnly.value = false
    hasDiscountOnly.value = false
    minPrice.value = null
    maxPrice.value = null
    searchQuery.value = ''
  }

  const fetchCategories = async () => {
    try {
      const res = await fetch('/api/v1/marketplace/categories/')
      if (!res.ok) throw new Error(`HTTP error ${res.status}`)
      const data = await res.json()
      categories.value = data
    } catch (err: any) {
      console.error('Error fetching categories:', err)
    }
  }

  const fetchItems = async () => {
    loading.value = true
    error.value = null
    try {
      const params = new URLSearchParams()
      if (searchQuery.value.trim()) {
        params.append('search', searchQuery.value.trim())
      }
      if (selectedCategoryId.value !== null) {
        params.append('category', String(selectedCategoryId.value))
      }
      if (selectedDealType.value !== 'all') {
        params.append('deal_type', selectedDealType.value)
      }
      if (selectedDeliveryType.value !== 'all') {
        params.append('delivery_type', selectedDeliveryType.value)
      }
      if (inStockOnly.value) {
        params.append('in_stock', 'true')
      }
      if (hasDiscountOnly.value) {
        params.append('has_discount', 'true')
      }
      if (minPrice.value !== null && minPrice.value > 0) {
        params.append('min_price', String(minPrice.value))
      }
      if (maxPrice.value !== null && maxPrice.value > 0) {
        params.append('max_price', String(maxPrice.value))
      }
      if (sortBy.value) {
        params.append('ordering', sortBy.value)
      }

      const queryString = params.toString() ? `?${params.toString()}` : ''
      const res = await fetch(`/api/v1/marketplace/items/${queryString}`)
      if (!res.ok) throw new Error(`HTTP error ${res.status}`)
      const data = await res.json()
      items.value = Array.isArray(data) ? data : (data.results || [])
    } catch (err: any) {
      console.error('Error fetching marketplace items:', err)
      error.value = err.message || 'خطا در برقراری ارتباط با فروشگاه'
    } finally {
      loading.value = false
    }
  }

  const fetchItemDetail = async (id: number): Promise<StoreItem | null> => {
    try {
      const res = await fetch(`/api/v1/marketplace/items/${id}/`)
      if (!res.ok) throw new Error(`HTTP error ${res.status}`)
      return await res.json()
    } catch (err) {
      console.error(`Error fetching item ${id}:`, err)
      return null
    }
  }

  // Cart operations
  const cartCount = computed(() => {
    return cartItems.value.reduce((sum, ci) => sum + ci.quantity, 0)
  })

  const cartTotalAmount = computed(() => {
    return cartItems.value.reduce((sum, ci) => {
      const unitPrice = ci.item.effective_price || 0
      return sum + (unitPrice * ci.quantity)
    }, 0)
  })

  const addToCart = (item: StoreItem, quantity: number = 1) => {
    const existing = cartItems.value.find(ci => ci.item.id === item.id)
    if (existing) {
      existing.quantity += quantity
    } else {
      cartItems.value.push({ item, quantity })
    }
  }

  const removeFromCart = (itemId: number) => {
    cartItems.value = cartItems.value.filter(ci => ci.item.id !== itemId)
  }

  const updateCartQuantity = (itemId: number, quantity: number) => {
    if (quantity <= 0) {
      removeFromCart(itemId)
      return
    }
    const found = cartItems.value.find(ci => ci.item.id === itemId)
    if (found) {
      found.quantity = quantity
    }
  }

  const clearCart = () => {
    cartItems.value = []
  }

  // Helpers
  const formatToman = (amount: number | string | null | undefined): string => {
    if (amount === null || amount === undefined) return '۰'
    const num = Number(amount)
    if (isNaN(num)) return '۰'
    return new Intl.NumberFormat('fa-IR').format(num)
  }

  return {
    items,
    categories,
    loading,
    error,
    searchQuery,
    selectedCategoryId,
    selectedDealType,
    selectedDeliveryType,
    inStockOnly,
    hasDiscountOnly,
    minPrice,
    maxPrice,
    sortBy,
    activeFiltersCount,
    hasActiveFilters,
    selectedCategoryObj,
    clearAllFilters,
    fetchItems,
    fetchCategories,
    fetchItemDetail,
    // Cart
    cartItems,
    cartCount,
    cartTotalAmount,
    addToCart,
    removeFromCart,
    updateCartQuantity,
    clearCart,
    formatToman,
  }
}
