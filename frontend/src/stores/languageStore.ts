import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useLanguageStore = defineStore('language', () => {
  const getInitialLanguage = (): 'fa' | 'en' => {
    const stored = localStorage.getItem('lang')
    return (stored === 'fa' || stored === 'en') ? stored : 'fa'
  }
  const currentLanguage = ref<'fa' | 'en'>(getInitialLanguage())

  const isFa = computed(() => currentLanguage.value === 'fa')
  const isEn = computed(() => currentLanguage.value === 'en')
  
  const dir = computed(() => (currentLanguage.value === 'fa' ? 'rtl' : 'ltr'))

  const setLanguage = (lang: 'fa' | 'en') => {
    currentLanguage.value = lang
    localStorage.setItem('lang', lang)
    
    // Update HTML document attributes
    document.documentElement.lang = lang
    document.documentElement.dir = lang === 'fa' ? 'rtl' : 'ltr'
  }

  // Translation helper
  const t = (faText: string, enText: string) => {
    return currentLanguage.value === 'fa' ? faText : enText
  }

  // Digit formatting helper
  const toPersianDigits = (str: string | number): string => {
    const map: Record<string, string> = {
      '0': '۰', '1': '۱', '2': '۲', '3': '۳', '4': '۴',
      '5': '۵', '6': '۶', '7': '۷', '8': '۸', '9': '۹'
    }
    return String(str).replace(/[0-9]/g, w => map[w] || w)
  }

  const toEnglishDigits = (str: string | number): string => {
    const map: Record<string, string> = {
      '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
      '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9',
      '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4',
      '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9'
    }
    return String(str).replace(/[۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩]/g, w => map[w] || w)
  }

  const n = (num: number | string): string => {
    if (num === null || num === undefined) return ''
    return currentLanguage.value === 'fa' ? toPersianDigits(num) : toEnglishDigits(num)
  }

  // Initialize page settings on load
  const init = () => {
    document.documentElement.lang = currentLanguage.value
    document.documentElement.dir = dir.value
  }

  return {
    currentLanguage,
    isFa,
    isEn,
    dir,
    setLanguage,
    t,
    n,
    init
  }
})
