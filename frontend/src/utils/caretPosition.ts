/**
 * محاسبه دقیق مختصات پیکسل‌های متن انتخاب‌شده در Textarea
 * برای قرارگیری بی‌نقص FloatingFormatMenu دقیقاً بالای کلمات هایلایت‌شده
 */

const styleProperties = [
  'direction',
  'boxSizing',
  'width',
  'height',
  'overflowX',
  'overflowY',
  'borderTopWidth',
  'borderRightWidth',
  'borderBottomWidth',
  'borderLeftWidth',
  'borderStyle',
  'paddingTop',
  'paddingRight',
  'paddingBottom',
  'paddingLeft',
  'fontStyle',
  'fontVariant',
  'fontWeight',
  'fontStretch',
  'fontSize',
  'fontSizeAdjust',
  'lineHeight',
  'fontFamily',
  'textAlign',
  'textTransform',
  'textIndent',
  'textDecoration',
  'letterSpacing',
  'wordSpacing',
  'tabSize',
  'whiteSpace',
  'wordBreak',
  'wordWrap'
] as const

export interface SelectionRect {
  top: number
  left: number
  right: number
  bottom: number
  width: number
  height: number
}

export function getCaretCoordinates(
  element: HTMLTextAreaElement,
  position: number
): { top: number; left: number; height: number } {
  const rect = getSelectionPixelRect(element, position, position)
  return {
    top: rect.top,
    left: rect.left,
    height: rect.height
  }
}

export function getSelectionPixelRect(
  element: HTMLTextAreaElement,
  selectionStart: number,
  selectionEnd: number
): SelectionRect {
  if (typeof window === 'undefined' || !element) {
    return { top: 0, left: 0, right: 0, bottom: 0, width: 0, height: 0 }
  }

  const computed = window.getComputedStyle(element)
  const isRtl = computed.direction === 'rtl'

  // ساخت المان آینه (Mirror Element)
  const mirror = document.createElement('div')
  mirror.id = '__textarea_caret_mirror__'
  document.body.appendChild(mirror)

  const mirrorStyle = mirror.style
  mirrorStyle.position = 'absolute'
  mirrorStyle.top = '0'
  mirrorStyle.left = '-9999px'
  mirrorStyle.visibility = 'hidden'
  mirrorStyle.pointerEvents = 'none'

  // کپی تمام خواص استایل مربوط به تایپوگرافی و جعبه متن
  for (const prop of styleProperties) {
    const val = (computed as any)[prop]
    if (val !== undefined) {
      mirrorStyle[prop as any] = val
    }
  }

  // تنظیم عرض دقیق و اسکرول آینه برابر با textarea
  mirrorStyle.width = `${element.clientWidth}px`
  mirrorStyle.whiteSpace = 'pre-wrap'
  mirrorStyle.wordWrap = 'break-word'

  const fullText = element.value
  const beforeText = fullText.substring(0, selectionStart)
  const selectedText = fullText.substring(selectionStart, selectionEnd)

  const beforeSpan = document.createElement('span')
  beforeSpan.textContent = beforeText
  mirror.appendChild(beforeSpan)

  const selectedSpan = document.createElement('span')
  selectedSpan.textContent = selectedText.length > 0 ? selectedText : '|'
  mirror.appendChild(selectedSpan)

  // محاسبه موقعیت با احتساب padding و border و scroll
  const spanOffsetTop = selectedSpan.offsetTop
  const spanOffsetLeft = selectedSpan.offsetLeft
  const spanWidth = selectedSpan.offsetWidth
  const spanHeight = selectedSpan.offsetHeight || parseInt(computed.lineHeight) || 20

  const paddingTop = parseFloat(computed.paddingTop) || 0
  const paddingLeft = parseFloat(computed.paddingLeft) || 0

  document.body.removeChild(mirror)

  // مختصات دقیق داخل المان با کم کردن مقدار اسکرول جاری
  const top = spanOffsetTop - element.scrollTop
  const left = spanOffsetLeft - element.scrollLeft

  return {
    top,
    left,
    right: left + spanWidth,
    bottom: top + spanHeight,
    width: spanWidth,
    height: spanHeight
  }
}
