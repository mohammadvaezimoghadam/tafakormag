import { ref } from 'vue'
import type { QuranSurah, QuranAyah, QuranBookmark, QuranLastRead } from '../types'

const arabicEdition = ref<string>(
  localStorage.getItem('tafakor_quran_arabic_edition') || 'quran-simple'
)

const translationEdition = ref<string>(
  localStorage.getItem('tafakor_quran_translation_edition') || 'fa.ansarian'
)

const showTranslation = ref<boolean>(
  localStorage.getItem('tafakor_quran_show_translation') !== 'false'
)

const fontSize = ref<number>(
  Number(localStorage.getItem('tafakor_quran_font_size')) || 24
)

const bookmarks = ref<QuranBookmark[]>(
  (() => {
    try {
      const saved = localStorage.getItem('tafakor_quran_bookmarks')
      return saved ? JSON.parse(saved) : []
    } catch {
      return []
    }
  })()
)

const lastRead = ref<QuranLastRead | null>(
  (() => {
    try {
      const saved = localStorage.getItem('tafakor_quran_last_read')
      return saved ? JSON.parse(saved) : null
    } catch {
      return null
    }
  })()
)

export function useQuranReader() {
  const setArabicEdition = (editionId: string) => {
    arabicEdition.value = editionId
    try {
      localStorage.setItem('tafakor_quran_arabic_edition', editionId)
    } catch {}
  }

  const setTranslationEdition = (editionId: string) => {
    translationEdition.value = editionId
    try {
      localStorage.setItem('tafakor_quran_translation_edition', editionId)
    } catch {}
  }

  const setShowTranslation = (show: boolean) => {
    showTranslation.value = show
    try {
      localStorage.setItem('tafakor_quran_show_translation', String(show))
    } catch {}
  }

  const setFontSize = (size: number) => {
    fontSize.value = Math.max(16, Math.min(48, size))
    try {
      localStorage.setItem('tafakor_quran_font_size', String(fontSize.value))
    } catch {}
  }

  const isBookmarked = (surahNumber: number, ayahNumber: number): boolean => {
    return bookmarks.value.some(
      b => b.surahNumber === surahNumber && b.ayahNumber === ayahNumber
    )
  }

  const toggleBookmark = (surah: QuranSurah, ayah: QuranAyah) => {
    const existingIndex = bookmarks.value.findIndex(
      b => b.surahNumber === surah.number && b.ayahNumber === ayah.number_in_surah
    )

    if (existingIndex >= 0) {
      bookmarks.value.splice(existingIndex, 1)
    } else {
      const newBookmark: QuranBookmark = {
        id: `${surah.number}:${ayah.number_in_surah}`,
        surahNumber: surah.number,
        surahName: surah.name,
        ayahNumber: ayah.number_in_surah,
        addedAt: new Date().toISOString(),
        textPreview: ayah.text.slice(0, 60) + (ayah.text.length > 60 ? '...' : ''),
      }
      bookmarks.value.unshift(newBookmark)
    }

    try {
      localStorage.setItem('tafakor_quran_bookmarks', JSON.stringify(bookmarks.value))
    } catch {}
  }

  const removeBookmark = (bookmarkId: string) => {
    bookmarks.value = bookmarks.value.filter(b => b.id !== bookmarkId)
    try {
      localStorage.setItem('tafakor_quran_bookmarks', JSON.stringify(bookmarks.value))
    } catch {}
  }

  const saveLastRead = (surahNumber: number, surahName: string, ayahNumber: number) => {
    lastRead.value = {
      surahNumber,
      surahName,
      ayahNumber,
      timestamp: new Date().toISOString(),
    }
    try {
      localStorage.setItem('tafakor_quran_last_read', JSON.stringify(lastRead.value))
    } catch {}
  }

  return {
    arabicEdition,
    translationEdition,
    showTranslation,
    fontSize,
    bookmarks,
    lastRead,
    setArabicEdition,
    setTranslationEdition,
    setShowTranslation,
    setFontSize,
    isBookmarked,
    toggleBookmark,
    removeBookmark,
    saveLastRead,
  }
}
