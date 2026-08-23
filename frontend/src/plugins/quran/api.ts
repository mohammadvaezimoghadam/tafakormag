import axios from 'axios'
import type {
  QuranEdition,
  QuranSurah,
  QuranSurahDetail,
  QuranAyah,
  QuranJuz,
  QuranSearchResponse,
  QuranCompareResponse,
  QuranFormatReferencePayload,
  QuranFormatReferenceResponse,
} from './types'

const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const getApiUrl = (endpoint: string) => {
  const base = apiBase.endsWith('/') ? apiBase.slice(0, -1) : apiBase
  return `${base}${endpoint}`
}

const getHeaders = () => {
  const token = localStorage.getItem('auth_token')
  return token ? { Authorization: `Token ${token}` } : {}
}

export const quranApi = {
  async getEditions(params?: {
    language?: string
    type?: string
    format?: string
    is_default?: boolean
    q?: string
  }): Promise<QuranEdition[]> {
    const res = await axios.get(getApiUrl('/api/plugins/quran/editions/'), {
      params,
      headers: getHeaders(),
    })
    return res.data
  },

  async getSurahs(params?: {
    revelation_type?: 'Meccan' | 'Medinan'
    juz?: number
  }): Promise<QuranSurah[]> {
    const res = await axios.get(getApiUrl('/api/plugins/quran/surahs/'), {
      params,
      headers: getHeaders(),
    })
    return res.data
  },

  async getSurahDetail(number: number): Promise<QuranSurahDetail> {
    const res = await axios.get(getApiUrl(`/api/plugins/quran/surahs/${number}/`), {
      headers: getHeaders(),
    })
    return res.data
  },

  async getSurahAyahs(
    number: number,
    options?: {
      edition?: string
      with_translation?: string
      from_ayah?: number
      to_ayah?: number
      page?: number
      page_size?: number
      all?: boolean
    }
  ): Promise<{
    surah: QuranSurah
    edition: string
    with_translation?: string
    count: number
    ayahs: QuranAyah[]
  }> {
    const res = await axios.get(getApiUrl(`/api/plugins/quran/surahs/${number}/ayahs/`), {
      params: options,
      headers: getHeaders(),
    })
    return res.data
  },

  async getAyah(
    surahNumber: number,
    ayahNumber: number,
    options?: { edition?: string; with_translation?: string }
  ): Promise<QuranAyah> {
    const res = await axios.get(
      getApiUrl(`/api/plugins/quran/ayahs/${surahNumber}/${ayahNumber}/`),
      { params: options, headers: getHeaders() }
    )
    return res.data
  },

  async getAyahByGlobal(
    globalNumber: number,
    options?: { edition?: string; with_translation?: string }
  ): Promise<QuranAyah> {
    const res = await axios.get(
      getApiUrl(`/api/plugins/quran/ayahs/${globalNumber}/`),
      { params: options, headers: getHeaders() }
    )
    return res.data
  },

  async getJuzs(): Promise<QuranJuz[]> {
    const res = await axios.get(getApiUrl('/api/plugins/quran/juz/'), {
      headers: getHeaders(),
    })
    return res.data
  },

  async getJuzAyahs(
    number: number,
    options?: {
      edition?: string
      with_translation?: string
      page?: number
      page_size?: number
    }
  ): Promise<{
    count: number
    results: QuranAyah[]
    next?: string | null
    previous?: string | null
  } | {
    count: number
    ayahs: QuranAyah[]
  }> {
    const res = await axios.get(getApiUrl(`/api/plugins/quran/juzs/${number}/ayahs/`), {
      params: options,
      headers: getHeaders(),
    })
    return res.data
  },

  async search(params: {
    q: string
    edition?: string
    language?: string
    surah?: number
    juz?: number
    exact?: boolean
    page?: number
    page_size?: number
    with_translation?: string
  }): Promise<QuranSearchResponse> {
    const res = await axios.get(getApiUrl('/api/plugins/quran/search/'), {
      params,
      headers: getHeaders(),
    })
    return res.data
  },

  async compare(params: {
    surah: number
    ayah: number
    editions?: string
  }): Promise<QuranCompareResponse> {
    const res = await axios.get(getApiUrl('/api/plugins/quran/compare/'), {
      params,
      headers: getHeaders(),
    })
    return res.data
  },

  async formatReference(payload: QuranFormatReferencePayload): Promise<QuranFormatReferenceResponse> {
    const res = await axios.post(getApiUrl('/api/plugins/quran/format-reference/'), payload, {
      headers: getHeaders(),
    })
    return res.data
  },
}
