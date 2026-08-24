import DOMPurify from 'dompurify'

export type FormatType = 'bold' | 'italic' | 'strikethrough' | 'underline' | 'code' | 'quote'

export interface WrapResult {
  newText: string
  newCursorStart: number
  newCursorEnd: number
}

/**
 * تبدیل نشانه‌گذاری‌های تلگرام و بله به HTML ایمن
 * پشتیبانی از:
 * - بولد: **متن**
 * - ایتالیک: *متن* یا _متن_ (با پشتیبانی کامل از کاراکترهای فارسی و یونیکد \p{L} و نیم‌فاصله)
 * - خط‌خورده: ~~متن~~
 * - زیرخط: __متن__
 * - کد تک‌فاصله: `کد`
 * - نقل‌قول: > متن (پشتیبانی از نقل‌قول چندخطی پیوسته)
 */
export function parseMarkdownToHtml(rawText: string): string {
  if (!rawText || typeof rawText !== 'string') return ''

  // ۱. اسکیپ کردن کاراکترهای خاص HTML برای جلوگیری از تزریق اولیه
  let html = rawText
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')

  // ۲. استخراج و توکنایز کردن کدهای تک‌فاصله (Inline Code) در گام اول
  // تا کاراکترهای *, _, ~ و غیره داخل کد توسط سایر رگکس‌ها دستکاری نشوند
  const codeTokens: string[] = []
  html = html.replace(/`([^`\n]+?)`/g, (_match, codeContent) => {
    const token = `___CODE_TOKEN_${codeTokens.length}___`
    codeTokens.push(codeContent)
    return token
  })

  // ۳. مدیریت نقل‌قول‌ها (Blockquotes) - تجمیع خطوط متوالی نقل‌قول به یک بلوک واحد
  const lines = html.split('\n')
  const processedLines: string[] = []
  let inQuoteBlock = false
  let quoteBuffer: string[] = []

  const flushQuoteBuffer = () => {
    if (quoteBuffer.length > 0) {
      const quoteContent = quoteBuffer.join('<br>')
      processedLines.push(
        `<blockquote class="border-r-3 border-primary/70 bg-primary/5 dark:bg-primary/10 pr-3 pl-2.5 py-1.5 rounded-l-lg my-2 text-xs sm:text-sm italic text-foreground/90 leading-relaxed text-start border-solid">${quoteContent}</blockquote>`
      )
      quoteBuffer = []
    }
    inQuoteBlock = false
  }

  for (const line of lines) {
    const quoteMatch = line.match(/^&gt;\s?(.*)$/)
    if (quoteMatch) {
      inQuoteBlock = true
      quoteBuffer.push(quoteMatch[1] ?? '')
    } else {
      if (inQuoteBlock) {
        flushQuoteBuffer()
      }
      processedLines.push(line)
    }
  }
  if (inQuoteBlock) {
    flushQuoteBuffer()
  }

  html = processedLines.join('\n')

  // ۴. بولد (**متن**)
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong class="font-bold text-foreground">$1</strong>')

  // ۵. خط‌خورده (~~متن~~)
  html = html.replace(/~~(.+?)~~/g, '<del class="line-through opacity-70 decoration-foreground/60">$1</del>')

  // ۶. زیرخط (__متن__)
  html = html.replace(/__(.+?)__/g, '<u class="underline underline-offset-4 decoration-primary/70">$1</u>')

  // ۷. ایتالیک با ستاره (*متن*)
  // تطبیق ستاره‌های تکی که جزو ** نیستند
  html = html.replace(/(?<!\*)\*(?!\*)([^*\n]+?)(?<!\*)\*(?!\*)/g, '<em class="italic text-foreground/95">$1</em>')

  // ۸. ایتالیک با آندرلاین (_متن_) با پشتیبانی یونیکد برای کلمات فارسی و لاتین
  // استفاده از \p{L}، فاصله و نیم‌فاصله (\u200c) به عنوان مرز واژه‌ها
  html = html.replace(
    /(^|[\s\p{P}\u200c])_([^\s_\n](?:[^_\n]*?[^\s_\n])?)_($|[\s\p{P}\u200c])/gu,
    '$1<em class="italic text-foreground/95">$2</em>$3'
  )

  // ۹. بازگردانی توکن‌های کد با استایل نهایی
  codeTokens.forEach((codeContent, index) => {
    const token = `___CODE_TOKEN_${index}___`
    const codeHtml = `<code class="font-mono bg-muted/80 text-primary px-1.5 py-0.5 rounded text-[11px] sm:text-xs border border-border/60 select-text" dir="ltr">${codeContent}</code>`
    html = html.replace(token, codeHtml)
  })

  // ۱۰. تبدیل شکست خطوط به <br> خارج از تگ‌های بلوکی
  // جلوگیری از ایجاد خط اضافه قبل و بعد از blockquote
  html = html
    .replace(/<\/blockquote>\n/g, '</blockquote>')
    .replace(/\n<blockquote/g, '<blockquote')
    .replace(/\n/g, '<br>')

  // ۱۱. ضدعفونی نهایی با DOMPurify برای مصونیت کامل در برابر XSS
  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS: ['strong', 'em', 'del', 'u', 'code', 'blockquote', 'br', 'span', 'p'],
    ALLOWED_ATTR: ['class', 'dir']
  })
}

/**
 * اعمال فرمت روی متن انتخاب‌شده یا درج نشانه‌گذاری در محل نشانگر با قابلیت هوشمند Toggle-Off
 */
export function wrapSelection(
  fullText: string,
  start: number,
  end: number,
  format: FormatType
): WrapResult {
  const before = fullText.substring(0, start)
  const selected = fullText.substring(start, end)
  const after = fullText.substring(end)

  if (format === 'quote') {
    if (selected.length > 0) {
      const lines = selected.split('\n')
      const allQuoted = lines.every(l => l.trim() === '' || l.startsWith('> ') || l.startsWith('>'))
      
      if (allQuoted) {
        // Toggle-off (Unwrap quote): Remove leading > or > 
        const unquotedSelected = lines
          .map(line => line.replace(/^>\s?/, ''))
          .join('\n')
        const newText = `${before}${unquotedSelected}${after}`
        return {
          newText,
          newCursorStart: start,
          newCursorEnd: start + unquotedSelected.length
        }
      } else {
        // Wrap with quote
        const formattedSelected = lines
          .map(line => line.startsWith('> ') ? line : `> ${line}`)
          .join('\n')

        const needsLeadingNewline = before.length > 0 && !before.endsWith('\n')
        const prefix = needsLeadingNewline ? '\n' : ''
        const newText = `${before}${prefix}${formattedSelected}${after}`
        const addedLen = prefix.length

        return {
          newText,
          newCursorStart: start + addedLen,
          newCursorEnd: start + addedLen + formattedSelected.length
        }
      }
    } else {
      // Without selection: Insert quote line at cursor
      const needsLeadingNewline = before.length > 0 && !before.endsWith('\n')
      const insert = needsLeadingNewline ? '\n> ' : '> '
      const newText = `${before}${insert}${after}`
      return {
        newText,
        newCursorStart: start + insert.length,
        newCursorEnd: start + insert.length
      }
    }
  }

  let tag = ''
  switch (format) {
    case 'bold':
      tag = '**'
      break
    case 'italic':
      tag = '*'
      break
    case 'strikethrough':
      tag = '~~'
      break
    case 'underline':
      tag = '__'
      break
    case 'code':
      tag = '`'
      break
  }

  // 1. If no text is selected (cursor only)
  if (start === end) {
    // Check if cursor is right between matching empty tags e.g. **|**
    if (before.endsWith(tag) && after.startsWith(tag)) {
      // Remove the empty tags
      const newText = `${before.slice(0, -tag.length)}${after.slice(tag.length)}`
      return {
        newText,
        newCursorStart: start - tag.length,
        newCursorEnd: start - tag.length
      }
    }
    const newText = `${before}${tag}${tag}${after}`
    return {
      newText,
      newCursorStart: start + tag.length,
      newCursorEnd: start + tag.length
    }
  }

  // Handle selected text with potential leading/trailing whitespace
  const trimmedSelected = selected.trim()
  
  // 2. Check if selected text (or trimmed selection) already starts and ends with the exact tag (Enclosed Selection)
  // e.g. Selected is "**سلام**" or " **سلام** "
  if (
    trimmedSelected.length >= tag.length * 2 &&
    trimmedSelected.startsWith(tag) &&
    trimmedSelected.endsWith(tag) &&
    !(format === 'italic' && trimmedSelected.startsWith('**') && trimmedSelected.endsWith('**'))
  ) {
    const leadSpaces = selected.slice(0, selected.indexOf(trimmedSelected))
    const trailSpaces = selected.slice(selected.indexOf(trimmedSelected) + trimmedSelected.length)
    const unwrappedCore = trimmedSelected.slice(tag.length, -tag.length)
    const unwrapped = `${leadSpaces}${unwrappedCore}${trailSpaces}`
    const newText = `${before}${unwrapped}${after}`
    return {
      newText,
      newCursorStart: start + leadSpaces.length,
      newCursorEnd: start + leadSpaces.length + unwrappedCore.length
    }
  }

  // 3. Check if selection is immediately wrapped by the tag in fullText (External Wrapper)
  // e.g. fullText is "**سلام**" and user selected "سلام" (before ends with "**" and after starts with "**")
  if (
    before.endsWith(tag) &&
    after.startsWith(tag) &&
    !(format === 'italic' && before.endsWith('**') && after.startsWith('**'))
  ) {
    // Unwrap external tags
    const newBefore = before.slice(0, -tag.length)
    const newAfter = after.slice(tag.length)
    const newText = `${newBefore}${selected}${newAfter}`
    return {
      newText,
      newCursorStart: start - tag.length,
      newCursorEnd: end - tag.length
    }
  }

  // 4. Default: Wrap selection with format tags
  const newText = `${before}${tag}${selected}${tag}${after}`
  return {
    newText,
    newCursorStart: start + tag.length,
    newCursorEnd: end + tag.length
  }
}
