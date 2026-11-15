import axios from 'axios'
import type {
  CatalogItem,
  BookTitleItem,
  BookStationItem,
  PhysicalCopyItem,
  TransferItem,
  BookJourneyResponse,
  BadgeAwardItem,
} from './types'

// Smart dynamic API base resolver supporting localhost, LAN IPs, and custom env
const getApiBase = () => {
  if (import.meta.env.VITE_API_BASE_URL !== undefined && import.meta.env.VITE_API_BASE_URL !== '') {
    return import.meta.env.VITE_API_BASE_URL
  }
  if (import.meta.env.DEV) {
    if (typeof window !== 'undefined' && window.location.hostname && window.location.hostname !== 'localhost') {
      return `${window.location.protocol}//${window.location.hostname}:8000`
    }
    return 'http://localhost:8000'
  }
  return ''
}

const getApiUrl = (endpoint: string) => {
  const base = getApiBase()
  if (!base || base === '/') {
    return endpoint.startsWith('/') ? endpoint : `/${endpoint}`
  }
  const cleanBase = base.endsWith('/') ? base.slice(0, -1) : base
  return `${cleanBase}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`
}

const getHeaders = () => {
  const token = typeof localStorage !== 'undefined' ? localStorage.getItem('auth_token') : null
  return token ? { Authorization: `Token ${token}` } : {}
}

export interface CatalogFilterParams {
  search?: string
  deal_type?: 'sale' | 'donation'
  category?: string
  condition?: string
  ordering?: string
  topic_id?: number
}

// ----------------------------------------------------------------------
// Catalog API
// ----------------------------------------------------------------------
export async function fetchCatalogItems(params?: CatalogFilterParams): Promise<CatalogItem[]> {
  const res = await axios.get(getApiUrl('/api/v1/marketplace/items/'), {
    params,
    headers: getHeaders(),
  })
  // Handle paginated or direct array responses
  return Array.isArray(res.data) ? res.data : (res.data.results || [])
}

export async function fetchItemDetail(id: number): Promise<CatalogItem> {
  const res = await axios.get(getApiUrl(`/api/v1/marketplace/items/${id}/`), {
    headers: getHeaders(),
  })
  return res.data
}

// ----------------------------------------------------------------------
// Book Titles API
// ----------------------------------------------------------------------
export async function searchBookTitles(query: string): Promise<BookTitleItem[]> {
  const res = await axios.get(getApiUrl('/api/v1/marketplace/book-titles/'), {
    params: { q: query },
    headers: getHeaders(),
  })
  return Array.isArray(res.data) ? res.data : (res.data.results || [])
}

export async function registerBookTitle(data: Partial<BookTitleItem>): Promise<BookTitleItem> {
  const res = await axios.post(getApiUrl('/api/v1/marketplace/book-titles/'), data, {
    headers: getHeaders(),
  })
  return res.data
}

// ----------------------------------------------------------------------
// Physical Copies & Circulation API
// ----------------------------------------------------------------------
export async function registerPhysicalCopy(payload: {
  book_title_id: number
  condition?: string
  privacy?: string
}): Promise<PhysicalCopyItem> {
  const res = await axios.post(getApiUrl('/api/v1/marketplace/copies/register/'), payload, {
    headers: getHeaders(),
  })
  return res.data
}

export async function inspectCopy(code: string): Promise<PhysicalCopyItem> {
  const res = await axios.get(getApiUrl('/api/v1/marketplace/copies/inspect/'), {
    params: { code },
    headers: getHeaders(),
  })
  return res.data
}

export async function fetchMyHeldBooks(): Promise<PhysicalCopyItem[]> {
  const res = await axios.get(getApiUrl('/api/v1/marketplace/copies/my-books/'), {
    headers: getHeaders(),
  })
  return Array.isArray(res.data) ? res.data : (res.data.results || [])
}

export async function fetchMyDonations(): Promise<PhysicalCopyItem[]> {
  const res = await axios.get(getApiUrl('/api/v1/marketplace/copies/my-donations/'), {
    headers: getHeaders(),
  })
  return Array.isArray(res.data) ? res.data : (res.data.results || [])
}

export async function fetchBookJourney(code: string): Promise<BookJourneyResponse> {
  const res = await axios.get(getApiUrl('/api/v1/marketplace/copies/journey/'), {
    params: { code },
    headers: getHeaders(),
  })
  return res.data
}

// ----------------------------------------------------------------------
// In-Person Handover Workflows
// ----------------------------------------------------------------------
export async function claimCopy(payload: {
  short_code: string
  recipient_note?: string
}): Promise<TransferItem> {
  const res = await axios.post(getApiUrl('/api/v1/marketplace/copies/handover/claim/'), payload, {
    headers: getHeaders(),
  })
  return res.data
}

export async function confirmHandover(
  transferId: number,
  payload?: { otp_code?: string; recipient_note?: string }
): Promise<TransferItem> {
  const res = await axios.post(
    getApiUrl(`/api/v1/marketplace/copies/handover/${transferId}/confirm/`),
    payload || {},
    { headers: getHeaders() }
  )
  return res.data
}

export async function initiateHandover(payload: {
  short_code: string
  recipient_phone?: string
  method?: string
  donor_note?: string
}): Promise<TransferItem> {
  const res = await axios.post(
    getApiUrl('/api/v1/marketplace/copies/handover/initiate/'),
    payload,
    { headers: getHeaders() }
  )
  return res.data
}

export async function cancelHandover(transferId: number): Promise<TransferItem> {
  const res = await axios.post(
    getApiUrl(`/api/v1/marketplace/copies/handover/${transferId}/cancel/`),
    {},
    { headers: getHeaders() }
  )
  return res.data
}

// ----------------------------------------------------------------------
// Physical Stations / Kiosks API
// ----------------------------------------------------------------------
export async function fetchBookStations(): Promise<BookStationItem[]> {
  const res = await axios.get(getApiUrl('/api/v1/marketplace/book-stations/'), {
    headers: getHeaders(),
  })
  return Array.isArray(res.data) ? res.data : (res.data.results || [])
}

export async function fetchStationBooks(stationId: number): Promise<PhysicalCopyItem[]> {
  const res = await axios.get(getApiUrl(`/api/v1/marketplace/book-stations/${stationId}/books/`), {
    headers: getHeaders(),
  })
  return Array.isArray(res.data) ? res.data : (res.data.results || [])
}

export async function depositToStation(payload: {
  short_code: string
  station_id: number
  donor_note?: string
}): Promise<TransferItem> {
  const res = await axios.post(getApiUrl('/api/v1/marketplace/copies/station/deposit/'), payload, {
    headers: getHeaders(),
  })
  return res.data
}

export async function pickupFromStation(payload: {
  short_code: string
  recipient_note?: string
}): Promise<TransferItem> {
  const res = await axios.post(getApiUrl('/api/v1/marketplace/copies/station/pickup/'), payload, {
    headers: getHeaders(),
  })
  return res.data
}

// ----------------------------------------------------------------------
// Badges / Gamification API
// ----------------------------------------------------------------------
export async function fetchMyBadges(): Promise<BadgeAwardItem[]> {
  const res = await axios.get(getApiUrl('/api/v1/marketplace/badges/my-badges/'), {
    headers: getHeaders(),
  })
  return Array.isArray(res.data) ? res.data : (res.data.results || [])
}

