export interface QuranEdition {
  identifier: string
  name: string
  english_name: string
  language: string
  type: 'quran' | 'translation' | 'transliteration' | 'tafsir' | 'audio'
  format: 'text' | 'audio'
  direction: 'rtl' | 'ltr'
  author?: string
  is_default: boolean
  total_ayahs: number
  metadata?: Record<string, any>
}

export interface QuranSurah {
  number: number
  name: string
  english_name: string
  english_name_translation: string
  revelation_type: 'Meccan' | 'Medinan'
  ayah_count: number
  order_of_revelation?: number
  page_start?: number
  page_end?: number
  juz_start: number
  bismillah_pre: boolean
}

export interface QuranSurahDetail extends QuranSurah {
  prev_surah?: {
    number: number
    name?: string
  }
  next_surah?: {
    number: number
    name?: string
  }
}

export interface QuranAyahTranslation {
  edition_id?: string
  edition_name?: string
  author?: string
  text: string
}

export interface QuranAyah {
  id: number
  edition: string
  edition_name?: string
  edition_language?: string
  surah: number
  surah_name?: string
  surah_english_name?: string
  number: number
  number_in_surah: number
  juz: number
  page?: number
  manzil?: number
  ruku?: number
  hizb_quarter?: number
  sajda?: any
  text: string
  normalized_text?: string
  highlighted_text?: string
  audio_url?: string
  metadata?: Record<string, any>
  translation?: QuranAyahTranslation
}

export interface QuranJuz {
  number: number
  name: string
  start_surah: number
  start_surah_name?: string
  start_ayah: number
  end_surah: number
  end_surah_name?: string
  end_ayah: number
  surah_mapping?: any[]
}

export interface QuranSearchResult {
  id: number
  global_number: number
  number_in_surah: number
  surah_number: number
  surah_name: string
  surah_english_name: string
  juz: number
  page?: number
  text: string
  normalized_text: string
  highlighted_text?: string
  audio_url?: string
  translation?: {
    edition_id?: string
    edition_name?: string
    text: string
  }
}

export interface QuranSearchResponse {
  query: string
  normalized_query: string
  edition_id: string
  total_matches: number
  page: number
  page_size: number
  total_pages: number
  results: QuranSearchResult[]
}

export interface QuranCompareEdition {
  edition: QuranEdition
  text: string
  audio_url?: string
}

export interface QuranCompareResponse {
  surah: number
  ayah_number: number
  global_number: number
  juz: number
  page?: number
  editions: QuranCompareEdition[]
}

export interface QuranFormatReferencePayload {
  surah_number: number
  ayah_number?: number
  ayah_from?: number
  ayah_to?: number
  edition_id?: string
  translation_id?: string
  include_citation?: boolean
  lang?: string
}

export interface QuranFormatReferenceResponse {
  surah_number: number
  surah_name: string
  surah_english_name?: string
  ayah_from?: number
  ayah_to?: number
  ayah_number: number
  arabic_text: string
  translation_text?: string
  translation_author?: string
  markdown: string
  external_id?: string
  metadata?: Record<string, any>
}

export interface QuranBookmark {
  id: string
  surahNumber: number
  surahName: string
  ayahNumber: number
  addedAt: string
  textPreview: string
}

export interface QuranLastRead {
  surahNumber: number
  surahName: string
  ayahNumber: number
  timestamp: string
}

export interface QuranReciter {
  id: string
  name: string
  nameFa: string
  style: string
  subfolder?: string
  cdnType: 'everyayah' | 'islamicnetwork'
}
