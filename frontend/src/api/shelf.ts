import api, { fetchDonationCampaigns } from './index'
import type {
  AdminDonationReportItem,
  AdminDonatePayload,
  BookCopyInspectResult,
  BookCopyJourneyResult,
  BookStationSummary,
  BookTransferRecord,
  DonateToPhonePayload,
  DonateToPhoneResult,
  DonationMethod,
  DonationRequestItem,
  HomeDonationCampaign,
  HomeMarketplaceItem,
  IncomingGiftItem,
  MarketplaceCategory,
  ShelfBook,
  ShelfBookCreatePayload,
  ShelfBookTitle,
  ShelfBookUpdatePayload,
  ShelfListFilters,
  ShelfPublishListingPayload,
  ShelfStartCirculationPayload,
  ShelfSummary,
  ShippingPayer,
  UserSearchResult,
} from '@/types/shelf'

function unwrapList<T>(data: T[] | { results?: T[] }): T[] {
  if (Array.isArray(data)) {
    return data
  }
  return Array.isArray(data?.results) ? data.results : []
}

export async function listMyShelfBooks(filters: ShelfListFilters = {}): Promise<ShelfBook[]> {
  const params: Record<string, string> = {}
  if (filters.search?.trim()) params.search = filters.search.trim()
  if (filters.reading_status) params.reading_status = filters.reading_status
  if (filters.disposition) params.disposition = filters.disposition
  if (filters.book_format) params.book_format = filters.book_format

  const { data } = await api.get<ShelfBook[] | { results: ShelfBook[] }>('/api/v1/marketplace/shelf/', { params })
  return unwrapList(data)
}

export async function getMyShelfSummary(): Promise<ShelfSummary> {
  const { data } = await api.get<ShelfSummary>('/api/v1/marketplace/shelf/summary/')
  return data
}

function buildShelfRequestBody(
  payload: ShelfBookCreatePayload | ShelfBookUpdatePayload
): FormData | ShelfBookCreatePayload | ShelfBookUpdatePayload {
  if (!(payload.cover_image instanceof File)) {
    return payload
  }
  const formData = new FormData()
  for (const [key, value] of Object.entries(payload)) {
    if (value === undefined) continue
    if (value instanceof File) {
      formData.append(key, value)
    } else if (value === null) {
      if (key === 'rating' || key === 'condition' || key === 'isbn' || key === 'book_title_id') {
        formData.append(key, '')
      }
    } else {
      formData.append(key, String(value))
    }
  }
  return formData
}

export async function createShelfBook(payload: ShelfBookCreatePayload): Promise<ShelfBook> {
  const body = buildShelfRequestBody(payload)
  const { data } = await api.post<ShelfBook>('/api/v1/marketplace/shelf/', body)
  return data
}

export async function updateShelfBook(id: number, payload: ShelfBookUpdatePayload): Promise<ShelfBook> {
  const body = buildShelfRequestBody(payload)
  const { data } = await api.patch<ShelfBook>(`/api/v1/marketplace/shelf/${id}/`, body)
  return data
}

export async function deleteShelfBook(id: number): Promise<void> {
  await api.delete(`/api/v1/marketplace/shelf/${id}/`)
}

export async function startShelfBookCirculation(
  id: number,
  payload: ShelfStartCirculationPayload = {}
): Promise<ShelfBook> {
  const { data } = await api.post<ShelfBook>(`/api/v1/marketplace/shelf/${id}/start-circulation/`, payload)
  return data
}

export async function publishShelfBookListing(
  id: number,
  payload: ShelfPublishListingPayload
): Promise<ShelfBook> {
  const { data } = await api.post<ShelfBook>(`/api/v1/marketplace/shelf/${id}/publish-listing/`, payload)
  return data
}

export async function withdrawShelfBookOffering(id: number): Promise<ShelfBook> {
  const { data } = await api.post<ShelfBook>(`/api/v1/marketplace/shelf/${id}/withdraw-offering/`)
  return data
}

export async function donateShelfBookToPhone(
  id: number,
  payload: DonateToPhonePayload
): Promise<DonateToPhoneResult> {
  const { data } = await api.post<DonateToPhoneResult>(
    `/api/v1/marketplace/shelf/${id}/donate-to-phone/`,
    payload
  )
  return data
}

export async function listIncomingGifts(): Promise<IncomingGiftItem[]> {
  const { data } = await api.get<IncomingGiftItem[] | { results: IncomingGiftItem[] }>(
    '/api/v1/marketplace/shelf/incoming-gifts/'
  )
  return unwrapList(data)
}

export async function confirmGift(transferId: number): Promise<{ status: string; message: string }> {
  const { data } = await api.post<{ status: string; message: string }>(
    '/api/v1/marketplace/shelf/confirm-gift/',
    { transfer_id: transferId }
  )
  return data
}

export async function rejectGift(transferId: number): Promise<{ status: string; message: string }> {
  const { data } = await api.post<{ status: string; message: string }>(
    '/api/v1/marketplace/shelf/reject-gift/',
    { transfer_id: transferId }
  )
  return data
}

export async function cancelGift(transferId: number): Promise<{ status: string; message: string }> {
  const { data } = await api.post<{ status: string; message: string }>(
    '/api/v1/marketplace/shelf/cancel-gift/',
    { transfer_id: transferId }
  )
  return data
}

export async function searchCatalogBookTitles(query: string): Promise<ShelfBookTitle[]> {
  const q = query.trim()
  if (!q) return []
  const { data } = await api.get<ShelfBookTitle[] | { results: ShelfBookTitle[] }>(
    '/api/v1/marketplace/book-titles/',
    { params: { q } }
  )
  return unwrapList(data)
}

export async function listMarketplaceCategories(): Promise<MarketplaceCategory[]> {
  const { data } = await api.get<MarketplaceCategory[]>('/api/v1/marketplace/categories/')
  return Array.isArray(data) ? data : []
}

export async function listMarketplaceItems(): Promise<HomeMarketplaceItem[]> {
  const { data } = await api.get<HomeMarketplaceItem[] | { results: HomeMarketplaceItem[] }>(
    '/api/v1/marketplace/items/'
  )
  return unwrapList(data)
}

export async function listBookDonations(params?: {
  search?: string
  donation_method?: DonationMethod | ''
}): Promise<HomeMarketplaceItem[]> {
  const query: Record<string, string> = { deal_type: 'donation' }
  if (params?.search?.trim()) query.search = params.search.trim()
  if (params?.donation_method) query.donation_method = params.donation_method
  const { data } = await api.get<HomeMarketplaceItem[] | { results: HomeMarketplaceItem[] }>(
    '/api/v1/marketplace/items/',
    { params: query }
  )
  return unwrapList(data)
}

export async function listBookStations(): Promise<BookStationSummary[]> {
  const { data } = await api.get<BookStationSummary[] | { results: BookStationSummary[] }>(
    '/api/v1/marketplace/book-stations/'
  )
  return unwrapList(data)
}

export async function inspectBookCopy(shortCode: string): Promise<BookCopyInspectResult> {
  const { data } = await api.get<BookCopyInspectResult>('/api/v1/marketplace/copies/inspect/', {
    params: { code: shortCode.trim() },
  })
  return data
}

export async function getBookCopyJourney(shortCode: string): Promise<BookCopyJourneyResult> {
  const { data } = await api.get<BookCopyJourneyResult>('/api/v1/marketplace/copies/journey/', {
    params: { code: shortCode.trim() },
  })
  return data
}

export async function listIncomingBookHandovers(): Promise<BookTransferRecord[]> {
  const { data } = await api.get<BookTransferRecord[]>('/api/v1/marketplace/copies/handover/incoming/')
  return Array.isArray(data) ? data : []
}

export async function claimBookCopy(payload: {
  short_code: string
  quantity?: number
  recipient_note?: string
}): Promise<BookTransferRecord> {
  const { data } = await api.post<BookTransferRecord>('/api/v1/marketplace/copies/handover/claim/', payload)
  return data
}

export async function initiateBookHandover(payload: {
  short_code: string
  recipient_phone?: string
  method?: 'scan_confirm' | 'otp_fallback'
  quantity?: number
  donor_note?: string
}): Promise<BookTransferRecord> {
  const { data } = await api.post<BookTransferRecord>('/api/v1/marketplace/copies/handover/initiate/', payload)
  return data
}

export async function confirmBookHandover(
  transferId: number,
  payload: { otp_code?: string; quantity?: number; donor_note?: string; recipient_note?: string } = {}
): Promise<BookTransferRecord> {
  const { data } = await api.post<BookTransferRecord>(
    `/api/v1/marketplace/copies/handover/${transferId}/confirm/`,
    payload
  )
  return data
}

export async function cancelBookHandover(transferId: number): Promise<BookTransferRecord> {
  const { data } = await api.post<BookTransferRecord>(
    `/api/v1/marketplace/copies/handover/${transferId}/cancel/`
  )
  return data
}

export async function depositBookToStation(payload: {
  short_code: string
  station_id: number
  donor_note?: string
}): Promise<BookTransferRecord> {
  const { data } = await api.post<BookTransferRecord>('/api/v1/marketplace/copies/station/deposit/', payload)
  return data
}

export async function pickupBookFromStation(payload: {
  short_code: string
  recipient_note?: string
}): Promise<BookTransferRecord> {
  const { data } = await api.post<BookTransferRecord>('/api/v1/marketplace/copies/station/pickup/', payload)
  return data
}

export async function submitDonationRequest(payload: {
  item_id: number
  message?: string
}): Promise<DonationRequestItem> {
  const { data } = await api.post<DonationRequestItem>('/api/v1/marketplace/donation-requests/', payload)
  return data
}

export async function listDonationRequests(): Promise<DonationRequestItem[]> {
  const { data } = await api.get<DonationRequestItem[] | { results: DonationRequestItem[] }>(
    '/api/v1/marketplace/donation-requests/'
  )
  return unwrapList(data)
}

export async function acceptDonationRequest(
  requestId: number,
  payload: { shipping_address_id?: number | null; shipping_payer?: ShippingPayer } = {}
): Promise<unknown> {
  const { data } = await api.post(`/api/v1/marketplace/donation-requests/${requestId}/accept/`, payload)
  return data
}

export async function rejectDonationRequest(requestId: number): Promise<DonationRequestItem> {
  const { data } = await api.post<DonationRequestItem>(`/api/v1/marketplace/donation-requests/${requestId}/reject/`)
  return data
}

export async function cancelDonationRequest(requestId: number): Promise<DonationRequestItem> {
  const { data } = await api.post<DonationRequestItem>(`/api/v1/marketplace/donation-requests/${requestId}/cancel/`)
  return data
}

export async function listMyMarketplaceItems(): Promise<HomeMarketplaceItem[]> {
  const { data } = await api.get<HomeMarketplaceItem[] | { results: HomeMarketplaceItem[] }>(
    '/api/v1/marketplace/items/my_items/'
  )
  return unwrapList(data)
}

export async function listHomeDonationCampaigns(): Promise<HomeDonationCampaign[]> {
  const { data } = await fetchDonationCampaigns()
  return unwrapList<HomeDonationCampaign>(data)
}

export async function searchUsers(query: string): Promise<UserSearchResult[]> {
  const q = query.trim()
  if (!q) return []
  const { data } = await api.get<UserSearchResult[] | { results: UserSearchResult[] }>(
    '/api/v1/accounts/users/search/',
    { params: { q } }
  )
  return unwrapList(data)
}

export async function listAdminDonationsReport(): Promise<AdminDonationReportItem[]> {
  const { data } = await api.get<AdminDonationReportItem[] | { results: AdminDonationReportItem[] }>(
    '/api/v1/marketplace/shelf/admin-donations-report/'
  )
  return unwrapList(data)
}

export async function adminDonateBook(
  shelfBookId: number,
  payload: AdminDonatePayload
): Promise<{ status: string; message: string; transfer_id?: number }> {
  const { data } = await api.post<{ status: string; message: string; transfer_id?: number }>(
    `/api/v1/marketplace/shelf/${shelfBookId}/admin-donate/`,
    payload
  )
  return data
}

export function extractApiErrorMessage(err: unknown, fallback = 'خطا در برقراری ارتباط با سرور'): string {
  const maybeErr = err as { response?: { data?: Record<string, unknown> } }
  const data = maybeErr?.response?.data
  if (!data) return fallback
  if (typeof data.detail === 'string' && data.detail) return data.detail
  if (typeof data.error === 'string' && data.error) return data.error
  if (Array.isArray(data.non_field_errors) && typeof data.non_field_errors[0] === 'string') {
    return data.non_field_errors[0]
  }
  const firstKey = Object.keys(data)[0]
  if (firstKey) {
    const val = data[firstKey]
    if (Array.isArray(val) && typeof val[0] === 'string') return val[0]
    if (typeof val === 'string') return val
  }
  return fallback
}
