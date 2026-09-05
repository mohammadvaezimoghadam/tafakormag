import axios from 'axios'
import type {
  QuranEdition,
  QuranSurah,
  QuranSurahDetail,
  QuranAyah,
  QuranJuz,
  QuranSearchResult,
  QuranSearchResponse,
  QuranCompareResponse,
  QuranFormatReferencePayload,
  QuranFormatReferenceResponse,
} from './types'

import bundledSurahsRaw from './data/surahs.json'
import bundledJuzsRaw from './data/juzs.json'
import bundledSampleRaw from './data/sample_quran.json'

const bundledSurahs: QuranSurah[] = (bundledSurahsRaw as any).surahs || bundledSurahsRaw
const bundledJuzs: QuranJuz[] = (bundledJuzsRaw as any).juzs || bundledJuzsRaw
const bundledSampleAyahs: any[] = (bundledSampleRaw as any).data || []

// Smart dynamic API base resolver supporting localhost, LAN IPs, and custom env
const getApiBase = () => {
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL
  }
  if (typeof window !== 'undefined' && window.location.hostname && window.location.hostname !== 'localhost') {
    return `${window.location.protocol}//${window.location.hostname}:8000`
  }
  return 'http://localhost:8000'
}

const getApiUrl = (endpoint: string) => {
  const base = getApiBase()
  const cleanBase = base.endsWith('/') ? base.slice(0, -1) : base
  return `${cleanBase}${endpoint}`
}

const getHeaders = () => {
  const token = typeof localStorage !== 'undefined' ? localStorage.getItem('auth_token') : null
  return token ? { Authorization: `Token ${token}` } : {}
}

const sampleToQuranAyah = (entry: any, targetEdition = 'quran-simple', transEdition?: string): QuranAyah => {
  const arabicText = entry.editions?.[targetEdition] || entry.editions?.['quran-simple'] || entry.editions?.['quran-uthmani'] || ''
  const transText = transEdition ? (entry.editions?.[transEdition] || entry.editions?.['fa.ansarian'] || entry.editions?.['en.sahih'] || '') : undefined

  const surahMeta = bundledSurahs.find(s => s.number === entry.surah_number)

  return {
    id: entry.global_number || (entry.surah_number * 1000 + entry.number_in_surah),
    edition: targetEdition,
    edition_name: targetEdition === 'quran-uthmani' ? 'عثمان طه' : 'متن ساده',
    edition_language: 'ar',
    surah: entry.surah_number,
    surah_name: surahMeta?.name || `سوره ${entry.surah_number}`,
    surah_english_name: surahMeta?.english_name || '',
    number: entry.global_number || entry.number_in_surah,
    number_in_surah: entry.number_in_surah,
    juz: entry.juz || surahMeta?.juz_start || 1,
    page: entry.page || surahMeta?.page_start || 1,
    text: arabicText,
    translation: transText ? {
      edition_id: transEdition || 'fa.ansarian',
      edition_name: transEdition === 'fa.makarem' ? 'مکارم شیرازی' : (transEdition === 'en.sahih' ? 'English Sahih' : 'حسین انصاریان'),
      text: transText,
    } : undefined,
  }
}

const generateFallbackAyah = (surahNumber: number, ayahNumber: number, targetEdition = 'quran-simple', transEdition?: string): QuranAyah => {
  const surahMeta = bundledSurahs.find(s => s.number === surahNumber)
  const transText = transEdition ? `ترجمه آیه ${ayahNumber} سوره مبارکه ${surahMeta?.name || surahNumber}` : undefined

  return {
    id: surahNumber * 1000 + ayahNumber,
    edition: targetEdition,
    edition_name: 'متن ساده',
    edition_language: 'ar',
    surah: surahNumber,
    surah_name: surahMeta?.name || `سوره ${surahNumber}`,
    surah_english_name: surahMeta?.english_name || '',
    number: ayahNumber,
    number_in_surah: ayahNumber,
    juz: surahMeta?.juz_start || 1,
    page: surahMeta?.page_start || 1,
    text: ayahNumber === 1 && surahNumber !== 9 ? 'بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ' : `آیه شماره ${ayahNumber} سوره ${surahMeta?.name || surahNumber}`,
    translation: transText ? {
      edition_id: transEdition || 'fa.ansarian',
      edition_name: 'ترجمه فارسی',
      text: transText,
    } : undefined,
  }
}

export const quranApi = {
  async getEditions(params?: {
    language?: string
    type?: string
    format?: string
    is_default?: boolean
    q?: string
  }): Promise<QuranEdition[]> {
    try {
      const res = await axios.get(getApiUrl('/api/plugins/quran/editions/'), {
        params,
        headers: getHeaders(),
        timeout: 4000,
      })
      if (Array.isArray(res.data) && res.data.length > 0) {
        return res.data
      }
    } catch (err) {
      console.warn('[QuranAPI] Remote editions fetch failed, returning default editions:', err)
    }

    return [
      {
        identifier: 'quran-simple',
        name: 'متن ساده قرآن کریم',
        english_name: 'Simple Arabic Text',
        language: 'ar',
        type: 'quran',
        format: 'text',
        direction: 'rtl',
        is_default: true,
        total_ayahs: 6236,
      },
      {
        identifier: 'fa.ansarian',
        name: 'ترجمه استاد حسین انصاریان',
        english_name: 'Hussein Ansarian Translation',
        language: 'fa',
        type: 'translation',
        format: 'text',
        direction: 'rtl',
        author: 'حسین انصاریان',
        is_default: true,
        total_ayahs: 6236,
      },
      {
        identifier: 'fa.makarem',
        name: 'ترجمه آیت‌الله مکارم شیرازی',
        english_name: 'Makarem Shirazi Translation',
        language: 'fa',
        type: 'translation',
        format: 'text',
        direction: 'rtl',
        author: 'ناصر مکارم شیرازی',
        is_default: false,
        total_ayahs: 6236,
      },
      {
        identifier: 'en.sahih',
        name: 'English Translation (Sahih)',
        english_name: 'Saheeh International',
        language: 'en',
        type: 'translation',
        format: 'text',
        direction: 'ltr',
        author: 'Saheeh International',
        is_default: false,
        total_ayahs: 6236,
      },
    ]
  },

  async getSurahs(params?: {
    revelation_type?: 'Meccan' | 'Medinan'
    juz?: number
  }): Promise<QuranSurah[]> {
    try {
      const res = await axios.get(getApiUrl('/api/plugins/quran/surahs/'), {
        params,
        headers: getHeaders(),
        timeout: 4000,
      })
      if (Array.isArray(res.data) && res.data.length > 0) {
        return res.data
      }
    } catch (err) {
      console.warn('[QuranAPI] Remote surahs fetch failed, using bundled metadata:', err)
    }

    let list = [...bundledSurahs]
    if (params?.revelation_type) {
      list = list.filter(s => s.revelation_type.toLowerCase() === params.revelation_type?.toLowerCase())
    }
    if (params?.juz) {
      list = list.filter(s => s.juz_start === params.juz)
    }
    return list
  },

  async getSurahDetail(number: number): Promise<QuranSurahDetail> {
    try {
      const res = await axios.get(getApiUrl(`/api/plugins/quran/surahs/${number}/`), {
        headers: getHeaders(),
        timeout: 4000,
      })
      if (res.data && res.data.number) {
        return res.data
      }
    } catch (err) {
      console.warn(`[QuranAPI] Remote surah detail for ${number} failed, using local fallback:`, err)
    }

    const surah = bundledSurahs.find(s => s.number === number) || {
      number,
      name: `سوره ${number}`,
      english_name: '',
      english_name_translation: '',
      revelation_type: 'Meccan',
      ayah_count: 7,
      juz_start: 1,
      bismillah_pre: number !== 9,
    } as QuranSurah

    const prev = number > 1 ? bundledSurahs.find(s => s.number === number - 1) : undefined
    const next = number < 114 ? bundledSurahs.find(s => s.number === number + 1) : undefined

    return {
      ...surah,
      prev_surah: prev ? { number: prev.number, name: prev.name } : undefined,
      next_surah: next ? { number: next.number, name: next.name } : undefined,
    }
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
    const opts = { all: true, ...options }
    try {
      const res = await axios.get(getApiUrl(`/api/plugins/quran/surahs/${number}/ayahs/`), {
        params: opts,
        headers: getHeaders(),
        timeout: 6000,
      })
      const raw = res.data
      const rawList = raw.ayahs || raw.results || (Array.isArray(raw) ? raw : [])
      if (rawList.length > 0) {
        return {
          surah: raw.surah || bundledSurahs.find(s => s.number === number)!,
          edition: raw.edition || options?.edition || 'quran-simple',
          with_translation: raw.with_translation || options?.with_translation,
          count: raw.count ?? rawList.length,
          ayahs: rawList,
        }
      }
    } catch (err) {
      console.warn(`[QuranAPI] Remote fetch for surah ${number} ayahs failed, using bundled fallback:`, err)
    }

    // Local fallback
    const surah = bundledSurahs.find(s => s.number === number) || {
      number,
      name: `سوره ${number}`,
      english_name: '',
      english_name_translation: '',
      revelation_type: 'Meccan',
      ayah_count: 7,
      juz_start: 1,
      bismillah_pre: number !== 9,
    } as QuranSurah

    const matches = bundledSampleAyahs.filter((a: any) => a.surah_number === number)
    let fallbackAyahs: QuranAyah[] = []
    if (matches.length > 0) {
      fallbackAyahs = matches.map((m: any) => sampleToQuranAyah(m, options?.edition, options?.with_translation))
    } else {
      const count = surah.ayah_count || 7
      for (let i = 1; i <= count; i++) {
        fallbackAyahs.push(generateFallbackAyah(number, i, options?.edition, options?.with_translation))
      }
    }

    return {
      surah,
      edition: options?.edition || 'quran-simple',
      with_translation: options?.with_translation,
      count: fallbackAyahs.length,
      ayahs: fallbackAyahs,
    }
  },

  async getAyah(
    surahNumber: number,
    ayahNumber: number,
    options?: { edition?: string; with_translation?: string }
  ): Promise<QuranAyah> {
    try {
      const res = await axios.get(
        getApiUrl(`/api/plugins/quran/ayahs/${surahNumber}/${ayahNumber}/`),
        { params: options, headers: getHeaders(), timeout: 4000 }
      )
      if (res.data && res.data.text) {
        return res.data
      }
    } catch (err) {
      // Graceful fallback below
    }

    // Search bundled sample ayahs
    const match = bundledSampleAyahs.find(
      (a: any) => a.surah_number === surahNumber && a.number_in_surah === ayahNumber
    )
    if (match) {
      return sampleToQuranAyah(match, options?.edition, options?.with_translation)
    }

    return generateFallbackAyah(surahNumber, ayahNumber, options?.edition, options?.with_translation)
  },

  async getAyahByGlobal(
    globalNumber: number,
    options?: { edition?: string; with_translation?: string }
  ): Promise<QuranAyah> {
    try {
      const res = await axios.get(
        getApiUrl(`/api/plugins/quran/ayahs/${globalNumber}/`),
        { params: options, headers: getHeaders(), timeout: 4000 }
      )
      if (res.data && res.data.text) {
        return res.data
      }
    } catch (err) {
      // Graceful fallback below
    }

    const match = bundledSampleAyahs.find((a: any) => a.global_number === globalNumber)
    if (match) {
      return sampleToQuranAyah(match, options?.edition, options?.with_translation)
    }

    return generateFallbackAyah(1, 1, options?.edition, options?.with_translation)
  },

  async getJuzs(): Promise<QuranJuz[]> {
    try {
      const res = await axios.get(getApiUrl('/api/plugins/quran/juz/'), {
        headers: getHeaders(),
        timeout: 4000,
      })
      if (Array.isArray(res.data) && res.data.length > 0) {
        return res.data
      }
    } catch (err) {
      console.warn('[QuranAPI] Remote fetch for juzs failed, using bundled metadata:', err)
    }

    return bundledJuzs
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
    try {
      const res = await axios.get(getApiUrl(`/api/plugins/quran/juzs/${number}/ayahs/`), {
        params: options,
        headers: getHeaders(),
        timeout: 5000,
      })
      if (res.data) {
        return res.data
      }
    } catch (err) {
      console.warn(`[QuranAPI] Remote fetch for juz ${number} ayahs failed, using local fallback:`, err)
    }

    const matches = bundledSampleAyahs.filter((a: any) => a.juz === number)
    const ayahs = matches.map((m: any) => sampleToQuranAyah(m, options?.edition, options?.with_translation))

    return {
      count: ayahs.length,
      ayahs,
    }
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
    try {
      const res = await axios.get(getApiUrl('/api/plugins/quran/search/'), {
        params,
        headers: getHeaders(),
        timeout: 5000,
      })
      if (res.data) {
        return res.data
      }
    } catch (err) {
      console.warn('[QuranAPI] Remote search failed, searching local sample dataset:', err)
    }

    const qLower = params.q.trim().toLowerCase()
    const matchedSample = bundledSampleAyahs.filter((a: any) => {
      const text = a.editions?.['quran-simple'] || ''
      const trans = a.editions?.['fa.ansarian'] || ''
      return text.includes(qLower) || trans.includes(qLower)
    })

    const results: QuranSearchResult[] = matchedSample.map((m: any) => {
      const surahMeta = bundledSurahs.find(s => s.number === m.surah_number)
      return {
        id: m.global_number || (m.surah_number * 1000 + m.number_in_surah),
        global_number: m.global_number || m.number_in_surah,
        number_in_surah: m.number_in_surah,
        surah_number: m.surah_number,
        surah_name: surahMeta?.name || `سوره ${m.surah_number}`,
        surah_english_name: surahMeta?.english_name || '',
        juz: m.juz || 1,
        page: m.page || 1,
        text: m.editions?.[params.edition || 'quran-simple'] || m.editions?.['quran-simple'] || '',
        normalized_text: m.editions?.[params.edition || 'quran-simple'] || '',
        translation: m.editions?.['fa.ansarian'] ? {
          edition_id: 'fa.ansarian',
          edition_name: 'حسین انصاریان',
          text: m.editions['fa.ansarian'],
        } : undefined,
      }
    })

    return {
      query: params.q,
      normalized_query: params.q,
      edition_id: params.edition || 'quran-simple',
      total_matches: results.length,
      page: params.page || 1,
      page_size: params.page_size || 20,
      total_pages: 1,
      results,
    }
  },

  async compare(params: {
    surah: number
    ayah: number
    editions?: string
  }): Promise<QuranCompareResponse> {
    try {
      const res = await axios.get(getApiUrl('/api/plugins/quran/compare/'), {
        params,
        headers: getHeaders(),
        timeout: 4000,
      })
      if (res.data) {
        return res.data
      }
    } catch (err) {
      console.warn('[QuranAPI] Remote compare failed, using fallback:', err)
    }

    const ayahSimple = await this.getAyah(params.surah, params.ayah, { edition: 'quran-simple' })
    const ayahAnsarian = await this.getAyah(params.surah, params.ayah, { edition: 'fa.ansarian' })

    const editions = await this.getEditions()
    const edSimple: QuranEdition = editions.find(e => e.identifier === 'quran-simple') || editions[0]!
    const edAnsarian: QuranEdition = editions.find(e => e.identifier === 'fa.ansarian') || editions[1] || editions[0]!

    return {
      surah: params.surah,
      ayah_number: params.ayah,
      global_number: ayahSimple.number,
      juz: ayahSimple.juz,
      page: ayahSimple.page,
      editions: [
        {
          edition: edSimple,
          text: ayahSimple.text,
        },
        {
          edition: edAnsarian,
          text: ayahAnsarian.translation?.text || ayahAnsarian.text,
        },
      ],
    }
  },

  async formatReference(payload: QuranFormatReferencePayload): Promise<QuranFormatReferenceResponse> {
    try {
      const res = await axios.post(getApiUrl('/api/plugins/quran/format-reference/'), payload, {
        headers: getHeaders(),
        timeout: 4000,
      })
      if (res.data && res.data.markdown) {
        return res.data
      }
    } catch (err) {
      console.warn('[QuranAPI] Remote format-reference failed, using client fallback generator:', err)
    }

    const surah = bundledSurahs.find(s => s.number === payload.surah_number)
    const surahName = surah ? surah.name : payload.surah_number
    const aNum = payload.ayah_number ?? payload.ayah_from ?? 1
    const ayah = await this.getAyah(payload.surah_number, aNum, {
      edition: payload.edition_id || 'quran-simple',
      with_translation: payload.translation_id,
    })

    let markdown = `> ﴿${ayah.text}﴾\n`
    if (ayah.translation?.text) {
      markdown += `> *${ayah.translation.text}*\n`
    }
    markdown += `> — **سوره ${surahName} (${payload.surah_number}:${aNum})**`

    return {
      surah_number: payload.surah_number,
      surah_name: String(surahName),
      surah_english_name: surah?.english_name,
      ayah_number: aNum,
      arabic_text: ayah.text,
      translation_text: ayah.translation?.text,
      translation_author: ayah.translation?.edition_name,
      markdown,
    }
  },
}
