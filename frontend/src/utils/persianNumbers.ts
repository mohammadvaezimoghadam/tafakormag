/**
 * Utility functions for Persian numbers, formatting, and number-to-words conversion.
 */

const PERSIAN_DIGITS = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹']

/**
 * Converts English digits to Persian digits
 */
export function toPersianDigits(input: string | number | null | undefined): string {
  if (input === null || input === undefined || input === '') return ''
  return String(input).replace(/[0-9]/g, (char) => PERSIAN_DIGITS[parseInt(char, 10)] || char)
}

/**
 * Converts Persian/Arabic digits to English digits
 */
export function toEnglishDigits(input: string | null | undefined): string {
  if (!input) return ''
  return input
    .replace(/[۰-۹]/g, (d) => String(d.charCodeAt(0) - 1776))
    .replace(/[٠-٩]/g, (d) => String(d.charCodeAt(0) - 1632))
}

/**
 * Formats a number with standard 3-digit comma separators in Persian digits
 */
export function formatCurrencyTomans(amount: number | null | undefined, includeUnit = true): string {
  if (amount === null || amount === undefined || isNaN(amount)) return includeUnit ? '۰ تومان' : '۰'
  const formatted = new Intl.NumberFormat('fa-IR').format(amount)
  return includeUnit ? `${formatted} تومان` : formatted
}

const ONES: Record<number, string> = {
  0: 'صفر',
  1: 'یک',
  2: 'دو',
  3: 'سه',
  4: 'چهار',
  5: 'پنج',
  6: 'شش',
  7: 'هفت',
  8: 'هشت',
  9: 'نه',
}

const TEENS: Record<number, string> = {
  10: 'ده',
  11: 'یازده',
  12: 'دوازده',
  13: 'سیزده',
  14: 'چهارده',
  15: 'پانزده',
  16: 'شانزده',
  17: 'هفده',
  18: 'هجده',
  19: 'نوزده',
}

const TENS: Record<number, string> = {
  2: 'بیست',
  3: 'سی',
  4: 'چهل',
  5: 'پنجاه',
  6: 'شصت',
  7: 'هفتاد',
  8: 'هشتاد',
  9: 'نود',
}

const HUNDREDS: Record<number, string> = {
  1: 'صد',
  2: 'دویست',
  3: 'سیصد',
  4: 'چهارصد',
  5: 'پانصد',
  6: 'ششصد',
  7: 'هفتصد',
  8: 'هشتصد',
  9: 'نهصد',
}

const SCALES: string[] = ['', 'هزار', 'میلیون', 'میلیارد', 'تریلیون']

/**
 * Converts a 3-digit chunk (0..999) to Persian words
 */
function chunkToWords(num: number): string {
  if (num === 0) return ''

  const parts: string[] = []

  // Hundreds
  const hundreds = Math.floor(num / 100)
  const remainder = num % 100

  const hundredsWord = HUNDREDS[hundreds]
  if (hundreds > 0 && hundredsWord) {
    parts.push(hundredsWord)
  }

  // Tens and Ones
  if (remainder >= 10 && remainder <= 19) {
    const teenWord = TEENS[remainder]
    if (teenWord) {
      parts.push(teenWord)
    }
  } else {
    const tens = Math.floor(remainder / 10)
    const ones = remainder % 10

    const tensWord = TENS[tens]
    if (tens > 1 && tensWord) {
      parts.push(tensWord)
    }
    const onesWord = ONES[ones]
    if (ones > 0 && onesWord) {
      parts.push(onesWord)
    }
  }

  return parts.join(' و ')
}

/**
 * Converts numeric amount in Tomans to Persian words
 * e.g., 20000000 -> "بیست میلیون تومان"
 */
export function numberToPersianWords(amount: number | null | undefined, unit = 'تومان'): string {
  if (amount === null || amount === undefined || isNaN(amount) || amount <= 0) {
    return ''
  }

  if (amount === 0) {
    return unit ? `صفر ${unit}` : 'صفر'
  }

  const chunks: number[] = []
  let n = Math.floor(Math.abs(amount))

  while (n > 0) {
    chunks.push(n % 1000)
    n = Math.floor(n / 1000)
  }

  const parts: string[] = []

  for (let i = chunks.length - 1; i >= 0; i--) {
    const chunk = chunks[i]
    if (chunk !== undefined && chunk > 0) {
      const words = chunkToWords(chunk)
      const scale = SCALES[i]
      if (scale) {
        parts.push(`${words} ${scale}`)
      } else {
        parts.push(words)
      }
    }
  }

  const result = parts.join(' و ')
  return unit ? `${result} ${unit}` : result
}
