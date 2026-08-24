<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { 
  PaperclipIcon, 
  PlusIcon,
  SendIcon, 
  MicIcon, 
  XIcon, 
  Trash2Icon,
  CheckIcon,
  FileTextIcon, 
  ImageIcon, 
  VideoIcon, 
  MusicIcon,
  PlayIcon,
  Loader2Icon,
  AlertCircleIcon,
  Maximize2Icon,
  Minimize2Icon,
  CircleFadingArrowUpIcon,
  Wand2Icon,
  HeartIcon,
  BarChart3Icon,
  CalendarDaysIcon
} from '@lucide/vue'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle, 
  DialogDescription,
  DialogClose
} from '@/components/ui/dialog'
import AIRefinerDrawer from './AIRefinerDrawer.vue'
import FloatingFormatMenu, { type MenuCoords, type ActionType } from '@/components/common/FloatingFormatMenu.vue'
import PluginSlashCommandModal, { type SlashModalStep } from './PluginSlashCommandModal.vue'
import { quranApi } from '@/plugins/quran/api'
import type { QuranSurah, QuranAyah } from '@/plugins/quran/types'
import { wrapSelection, type FormatType } from '@/utils/textFormatter'
import { getSelectionPixelRect } from '@/utils/caretPosition'
import { usePluginRegistryStore } from '@/plugins/core/pluginRegistry'
import type { ComposerAction } from '@/plugins/core/pluginTypes'

interface Attachment {
  id: string | number
  name: string
  type: 'image' | 'video' | 'audio' | 'file'
  url?: string
  size?: string
  progress?: number // 0 to 100
  status?: 'uploading' | 'completed' | 'error'
}

const props = withDefaults(defineProps<{
  placeholder?: string
  disabled?: boolean
  initialText?: string
  initialAttachments?: Attachment[]
  isEditMode?: boolean
}>(), {
  placeholder: 'پیام خود را بنویسید...',
  disabled: false,
  initialText: '',
  initialAttachments: () => [],
  isEditMode: false
})

const emit = defineEmits<{
  (e: 'send', message: { text: string; attachments: Attachment[] }): void
  (e: 'attach'): void
  (e: 'plus'): void
  (e: 'create-donation'): void
  (e: 'recordVoice'): void
  (e: 'removeAttachment', id: string | number): void
  (e: 'save', message: { text: string }): void
  (e: 'cancel-edit'): void
}>()

// Local state
const text = ref(props.initialText)
const attachments = ref<Attachment[]>([...props.initialAttachments])
const isRecording = ref(false)
const recordingSeconds = ref(0)
let timerInterval: any = null

const textareaRef = ref<HTMLTextAreaElement | null>(null)
const showExpanded = ref(false)
const expandedTextareaRef = ref<HTMLTextAreaElement | null>(null)

const isAiRefinerOpen = ref(false)

const handleApplyRefinedText = (refinedText: string) => {
  text.value = refinedText
  isAiRefinerOpen.value = false
  
  nextTick(() => {
    if (showExpanded.value && expandedTextareaRef.value) {
      expandedTextareaRef.value.focus()
    } else if (textareaRef.value) {
      textareaRef.value.focus()
    }
  })
}
const actualHeight = ref(40)

// Check if line count is more than 4 lines
const lineCount = computed(() => {
  if (!text.value) return 0
  return text.value.split('\n').length
})

const isLongText = computed(() => {
  if (!text.value) return false
  
  // 1. Explicit line breaks (4 lines or more)
  if (lineCount.value >= 4) return true

  // 2. Character length fallback (> 100 characters roughly equals 3-4 lines)
  if (text.value.length > 100) return true

  // 3. Rendered height fallback (> 75px)
  if (actualHeight.value > 75) return true

  return false
})

// Watch edit mode to automatically trigger expanded modal
watch(() => props.isEditMode, (newVal) => {
  if (newVal) {
    showExpanded.value = true
  } else {
    showExpanded.value = false
  }
}, { immediate: true })

// Focus the expanded textarea when opened and lock body scroll
watch(showExpanded, (newVal) => {
  if (newVal) {
    document.body.style.overflow = 'hidden'
    nextTick(() => {
      expandedTextareaRef.value?.focus()
    })
  } else {
    document.body.style.overflow = ''
  }
})

const handleSendFromModal = () => {
  handleSend()
  showExpanded.value = false
}

// Sync from props
watch(() => props.initialText, (newVal) => {
  text.value = newVal
})

watch(() => props.initialAttachments, (newVal) => {
  attachments.value = [...newVal]
}, { deep: true })

onUnmounted(() => {
  stopTimer()
  document.body.style.overflow = ''
})

// Timer actions for voice recording
const startTimer = () => {
  recordingSeconds.value = 0
  timerInterval = setInterval(() => {
    recordingSeconds.value++
  }, 1000)
}

const stopTimer = () => {
  if (timerInterval) {
    clearInterval(timerInterval)
    timerInterval = null
  }
}

const formattedTime = computed(() => {
  const mins = Math.floor(recordingSeconds.value / 60)
  const secs = recordingSeconds.value % 60
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
})

// Dynamic action states
const hasContent = computed(() => {
  return text.value.trim().length > 0 || attachments.value.length > 0
})

const hasAttachments = computed(() => {
  return attachments.value.length > 0
})

// Auto-adjust height for textarea
const adjustHeight = () => {
  const el = textareaRef.value
  if (!el) return
  el.style.height = 'auto'
  const minHeight = hasAttachments.value ? 36 : 40
  const newHeight = Math.min(Math.max(el.scrollHeight, minHeight), 140)
  el.style.height = `${newHeight}px`
  actualHeight.value = el.scrollHeight
}

watch([text, hasAttachments], () => {
  nextTick(() => {
    adjustHeight()
  })
})

const handleGlobalSelectionChange = () => {
  const activeEl = document.activeElement
  if (activeEl === textareaRef.value) {
    handleTextareaSelect(false)
  } else if (activeEl === expandedTextareaRef.value) {
    handleTextareaSelect(true)
  }
}

onMounted(() => {
  nextTick(() => {
    adjustHeight()
  })
  document.addEventListener('selectionchange', handleGlobalSelectionChange)
})

onUnmounted(() => {
  document.removeEventListener('selectionchange', handleGlobalSelectionChange)
})

// Actions
const resolveTokens = async (rawText: string): Promise<string> => {
  const quranRegex = /\/quran-sureh:([a-zA-Z0-9_\-]+)-ayeh:([0-9]+)/g
  let resolved = rawText
  const matches = Array.from(rawText.matchAll(quranRegex))
  for (const m of matches) {
    const fullToken = m[0]
    const cached = quranTokenCache.get(fullToken)
    if (cached) {
      resolved = resolved.replace(fullToken, cached)
    } else {
      const ayahNum = Number(m[2])
      try {
        const formatted = await quranApi.formatReference({
          surah_number: 1,
          ayah_number: ayahNum,
          edition_id: 'quran-simple',
          translation_id: 'fa.ansarian',
          include_citation: true,
        })
        resolved = resolved.replace(fullToken, formatted.markdown)
      } catch {
        resolved = resolved.replace(fullToken, `> — قرآن کریم (آیه ${ayahNum})`)
      }
    }
  }
  return resolved
}

const handleSend = async () => {
  if (props.disabled) return
  if (!hasContent.value) return

  const resolvedText = await resolveTokens(text.value.trim())

  if (props.isEditMode) {
    emit('save', {
      text: resolvedText
    })
    return
  }

  // Filter out attachments that are still uploading
  const completedAttachments = attachments.value.filter(a => a.status !== 'uploading')

  emit('send', {
    text: resolvedText,
    attachments: completedAttachments
  })

  text.value = ''
  attachments.value = []

  nextTick(() => {
    adjustHeight()
  })
}

// Detect if the device is a mobile device to prevent sending message on Enter keypress
const isMobile = () => {
  if (typeof window === 'undefined') return false
  return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) || 
         ('ontouchstart' in window) || 
         (navigator.maxTouchPoints > 0)
}

const showFormatMenu = ref(false)
const showExpandedFormatMenu = ref(false)
const menuCoords = ref<MenuCoords | null>(null)
const expandedMenuCoords = ref<MenuCoords | null>(null)
const selectedText = ref('')
const expandedSelectedText = ref('')

// Hold & Long-Press Touch State
let touchHoldTimer: any = null
let touchStartX = 0
let touchStartY = 0
let touchHasMoved = false
let isTouchHolding = false

const calculateMenuCoordinates = (
  el: HTMLTextAreaElement,
  start: number,
  end: number,
  isExpanded: boolean,
  fallbackTouchPoint?: { clientX: number; clientY: number }
): MenuCoords => {
  const isContext = (start >= end)
  const menuWidth = isContext ? 190 : 330
  const menuHeight = 40
  const verticalGap = 8

  let centerX = 0
  let candidateTop = 0
  let placement: 'top' | 'bottom' = 'top'

  const elRect = el.getBoundingClientRect()

  if (fallbackTouchPoint) {
    centerX = fallbackTouchPoint.clientX - elRect.left
    const touchTopInEl = fallbackTouchPoint.clientY - elRect.top
    candidateTop = touchTopInEl - menuHeight - verticalGap
    if (candidateTop < 6 && !isExpanded) {
      candidateTop = -menuHeight - 8
      placement = 'top'
    } else if (candidateTop < 6 && isExpanded) {
      candidateTop = touchTopInEl + 24
      placement = 'bottom'
    }
  } else {
    const rect = getSelectionPixelRect(el, start, end)
    centerX = rect.left + (rect.width / 2)
    candidateTop = rect.top - menuHeight - verticalGap
    if (!isExpanded) {
      candidateTop = Math.min(candidateTop, -menuHeight - 6)
      placement = 'top'
    } else {
      const topInContainer = rect.top + 24
      const candidateAbove = topInContainer - menuHeight - verticalGap
      if (candidateAbove >= 8) {
        candidateTop = candidateAbove
        placement = 'top'
      } else {
        candidateTop = rect.bottom + 24 + verticalGap
        placement = 'bottom'
      }
    }
  }

  const containerWidth = el.clientWidth || 300
  const minX = (menuWidth / 2) + 8
  const maxX = Math.max(minX, containerWidth - (menuWidth / 2) - 8)
  const clampedX = Math.min(Math.max(centerX, minX), maxX)

  return {
    top: candidateTop,
    left: isExpanded ? clampedX + 24 : clampedX,
    placement
  }
}

const handleTextareaSelect = (isExpanded = false) => {
  const el = isExpanded ? expandedTextareaRef.value : textareaRef.value
  if (!el) return

  const start = el.selectionStart ?? 0
  const end = el.selectionEnd ?? 0

  if (start >= end) {
    if (isExpanded) {
      if (!isTouchHolding) {
        showExpandedFormatMenu.value = false
        expandedSelectedText.value = ''
        expandedMenuCoords.value = null
      }
    } else {
      if (!isTouchHolding) {
        showFormatMenu.value = false
        selectedText.value = ''
        menuCoords.value = null
      }
    }
    return
  }

  const rawSelection = el.value.substring(start, end)
  if (!rawSelection || rawSelection.trim().length === 0) {
    if (isExpanded) {
      if (!isTouchHolding) {
        showExpandedFormatMenu.value = false
        expandedSelectedText.value = ''
        expandedMenuCoords.value = null
      }
    } else {
      if (!isTouchHolding) {
        showFormatMenu.value = false
        selectedText.value = ''
        menuCoords.value = null
      }
    }
    return
  }

  const coords = calculateMenuCoordinates(el, start, end, isExpanded)

  if (isExpanded) {
    expandedSelectedText.value = rawSelection
    expandedMenuCoords.value = coords
    showExpandedFormatMenu.value = true
  } else {
    selectedText.value = rawSelection
    menuCoords.value = coords
    showFormatMenu.value = true
  }
}

const handleTouchStart = (e: TouchEvent, isExpanded = false) => {
  if (props.disabled) return
  if (!e.touches || e.touches.length === 0) return

  const touch = e.touches[0]
  if (!touch) return
  touchStartX = touch.clientX
  touchStartY = touch.clientY
  touchHasMoved = false
  isTouchHolding = false

  if (touchHoldTimer) clearTimeout(touchHoldTimer)
  touchHoldTimer = setTimeout(() => {
    if (!touchHasMoved) {
      isTouchHolding = true
      handleLongPressHold(touch, isExpanded)
    }
  }, 450)
}

const handleTouchMove = (e: TouchEvent) => {
  if (!e.touches || e.touches.length === 0) return
  const touch = e.touches[0]
  if (!touch) return
  const dx = Math.abs(touch.clientX - touchStartX)
  const dy = Math.abs(touch.clientY - touchStartY)
  if (dx > 10 || dy > 10) {
    touchHasMoved = true
    if (touchHoldTimer) {
      clearTimeout(touchHoldTimer)
      touchHoldTimer = null
    }
  }
}

const handleTouchEnd = (_e: TouchEvent, isExpanded = false) => {
  if (touchHoldTimer) {
    clearTimeout(touchHoldTimer)
    touchHoldTimer = null
  }
  if (isTouchHolding) {
    setTimeout(() => {
      isTouchHolding = false
    }, 300)
    return
  }
  handleTextareaSelect(isExpanded)
  setTimeout(() => handleTextareaSelect(isExpanded), 60)
  setTimeout(() => handleTextareaSelect(isExpanded), 160)
}

const handleLongPressHold = (touch: Touch, isExpanded = false) => {
  const el = isExpanded ? expandedTextareaRef.value : textareaRef.value
  if (!el) return

  const start = el.selectionStart ?? 0
  const end = el.selectionEnd ?? 0
  const sel = (start < end) ? el.value.substring(start, end) : ''

  const coords = calculateMenuCoordinates(el, start, end, isExpanded, {
    clientX: touch.clientX,
    clientY: touch.clientY
  })

  if (isExpanded) {
    expandedSelectedText.value = sel
    expandedMenuCoords.value = coords
    showExpandedFormatMenu.value = true
  } else {
    selectedText.value = sel
    menuCoords.value = coords
    showFormatMenu.value = true
  }
}

const handleContextMenu = (e: MouseEvent, isExpanded = false) => {
  if (isMobile()) {
    e.preventDefault()
    const el = isExpanded ? expandedTextareaRef.value : textareaRef.value
    if (el) {
      const start = el.selectionStart ?? 0
      const end = el.selectionEnd ?? 0
      const sel = (start < end) ? el.value.substring(start, end) : ''
      const coords = calculateMenuCoordinates(el, start, end, isExpanded, {
        clientX: e.clientX,
        clientY: e.clientY
      })
      if (isExpanded) {
        expandedSelectedText.value = sel
        expandedMenuCoords.value = coords
        showExpandedFormatMenu.value = true
      } else {
        selectedText.value = sel
        menuCoords.value = coords
        showFormatMenu.value = true
      }
    }
  }
}

const handleTextareaFocus = (isExpanded = false) => {
  handleTextareaSelect(isExpanded)
}

const handleTextareaBlur = (isExpanded = false) => {
  setTimeout(() => {
    const active = document.activeElement
    if (active && (active as HTMLElement).closest && (active as HTMLElement).closest('.floating-format-menu')) {
      return
    }
    if (isTouchHolding) {
      return
    }
    if (isExpanded) {
      showExpandedFormatMenu.value = false
    } else {
      showFormatMenu.value = false
    }
  }, 350)
}

const handleMenuAction = async (action: ActionType, isExpanded = false) => {
  const el = isExpanded ? expandedTextareaRef.value : textareaRef.value
  if (!el) return

  const start = el.selectionStart ?? 0
  const end = el.selectionEnd ?? 0
  const sel = el.value.substring(start, end)

  if (action === 'copy') {
    if (sel) {
      try {
        await navigator.clipboard.writeText(sel)
      } catch (e) {
        document.execCommand('copy')
      }
    }
  } else if (action === 'cut') {
    if (sel) {
      try {
        await navigator.clipboard.writeText(sel)
      } catch (e) {
        document.execCommand('copy')
      }
      const before = text.value.substring(0, start)
      const after = text.value.substring(end)
      text.value = before + after
      nextTick(() => {
        el.focus()
        el.setSelectionRange(start, start)
        handleTextareaSelect(isExpanded)
        adjustHeight()
      })
    }
  } else if (action === 'select-all') {
    el.focus()
    el.setSelectionRange(0, el.value.length)
    nextTick(() => {
      handleTextareaSelect(isExpanded)
    })
  } else if (action === 'paste') {
    try {
      const clipText = await navigator.clipboard.readText()
      if (clipText) {
        const before = text.value.substring(0, start)
        const after = text.value.substring(end)
        text.value = before + clipText + after
        nextTick(() => {
          el.focus()
          el.setSelectionRange(start + clipText.length, start + clipText.length)
          handleTextareaSelect(isExpanded)
          adjustHeight()
        })
      }
    } catch (err) {
      console.warn('Clipboard paste failed:', err)
    }
  }
}

const applyFormat = (format: FormatType, isExpanded = false) => {
  const el = isExpanded ? expandedTextareaRef.value : textareaRef.value
  if (!el) return

  const start = el.selectionStart ?? 0
  const end = el.selectionEnd ?? 0
  const res = wrapSelection(text.value, start, end, format)
  text.value = res.newText

  nextTick(() => {
    el.focus()
    el.setSelectionRange(res.newCursorStart, res.newCursorEnd)
    handleTextareaSelect(isExpanded)
    adjustHeight()
  })
}

const handleKeydown = (event: KeyboardEvent, isExpanded = false) => {
  // ۱. بررسی کلیدهای میانبر فرمت‌دهی متن (Ctrl/Cmd)
  const isCtrlOrMeta = event.ctrlKey || event.metaKey
  if (isCtrlOrMeta) {
    let format: FormatType | null = null
    const key = event.key.toLowerCase()

    if (key === 'b') {
      format = 'bold'
    } else if (key === 'i') {
      format = 'italic'
    } else if (key === 'u') {
      format = 'underline'
    } else if (key === 'x' && event.shiftKey) {
      format = 'strikethrough'
    } else if (key === '`') {
      format = 'code'
    } else if (key === 'q' && event.shiftKey) {
      format = 'quote'
    }

    if (format) {
      event.preventDefault()
      applyFormat(format, isExpanded)
      return
    }
  }

  // ۲. ارسال پیام با دکمه Enter
  if (!isExpanded && event.key === 'Enter' && !event.shiftKey) {
    if (isMobile()) {
      // On mobile, Enter should go to next line (default behavior)
      return
    }
    // On desktop, Enter sends the message
    event.preventDefault()
    handleSend()
  }
}

// Start Voice Recording
const startRecording = () => {
  if (props.disabled) return
  isRecording.value = true
  startTimer()
  emit('recordVoice')
}

// Cancel / Discard Voice Recording
const cancelRecording = () => {
  isRecording.value = false
  stopTimer()
  recordingSeconds.value = 0
}

// Stop and Send Voice Recording
const completeRecording = () => {
  if (props.disabled) return
  const durationStr = formattedTime.value
  isRecording.value = false
  stopTimer()

  // Generate a mock audio attachment to represent the voice recording
  const voiceAttachment: Attachment = {
    id: `voice_${Date.now()}`,
    name: `صدا_ضبط_شده_${durationStr.replace(':', '_')}.ogg`,
    type: 'audio',
    size: durationStr,
    status: 'completed',
    progress: 100
  }

  // Send the recording immediately
  emit('send', {
    text: '',
    attachments: [voiceAttachment]
  })
}

const handleAttachClick = () => {
  if (props.disabled) return
  emit('attach')
}

const isActionSheetOpen = ref(false)

const handlePlusClick = () => {
  if (props.disabled) return
  isActionSheetOpen.value = true
  emit('plus')
}

const handleSelectDonation = () => {
  isActionSheetOpen.value = false
  emit('create-donation')
}

const handleRemoveAttachment = (id: string | number) => {
  attachments.value = attachments.value.filter(a => a.id !== id)
  emit('removeAttachment', id)
}

// Dynamic classes based on attachment status
const containerClasses = computed(() => {
  if (hasAttachments.value || (isLongText.value && !isRecording.value) || props.isEditMode || isSlashModalOpen.value) {
    return 'w-full flex flex-col relative bg-white dark:bg-muted/20 border border-border/40 dark:border-border/20 rounded-3xl p-1.5 transition-all duration-300 focus-within:border-primary/40 focus-within:bg-white focus-within:dark:bg-muted/25'
  }
  return 'w-full flex flex-col relative transition-all duration-300'
})

const textareaClasses = computed(() => {
  if (hasAttachments.value || (isLongText.value && !isRecording.value) || isSlashModalOpen.value) {
    return 'w-full bg-transparent border-none outline-none focus-visible:ring-0 focus-visible:ring-offset-0 focus:ring-0 focus:outline-none focus-visible:outline-none text-xs font-semibold min-h-[36px] max-h-[140px] h-[36px] py-2 px-1.5 rounded-2xl flex-1 text-foreground placeholder:text-muted-foreground/60 transition-all duration-200 shadow-none resize-none overflow-y-auto scrollbar-none align-bottom text-start leading-relaxed'
  }
  return 'w-full bg-white dark:bg-muted/20 border border-border/40 dark:border-border/20 outline-none focus:border-primary/40 focus-within:border-primary/40 focus-visible:ring-0 focus-visible:ring-offset-0 focus:ring-0 focus:outline-none focus-visible:outline-none text-xs font-semibold min-h-[40px] max-h-[140px] h-10 py-2.5 px-3 rounded-2xl flex-1 text-foreground placeholder:text-muted-foreground/60 transition-all duration-200 shadow-none resize-none overflow-y-auto scrollbar-none align-bottom text-start leading-relaxed'
})

const recordingStatusClasses = computed(() => {
  if (hasAttachments.value) {
    return 'w-full bg-destructive/5 dark:bg-destructive/10 border border-destructive/10 text-destructive text-xs font-semibold h-9 px-3 rounded-2xl flex items-center justify-between transition-all duration-200 select-none'
  }
  return 'w-full bg-destructive/5 dark:bg-destructive/10 border border-destructive/20 text-destructive text-xs font-semibold h-10 px-4 rounded-2xl flex items-center justify-between transition-all duration-200 select-none'
})

import { useLanguageStore } from '@/stores/languageStore'
const languageStore = useLanguageStore()

const pluginRegistry = usePluginRegistryStore()
const pluginComposerActions = computed(() => pluginRegistry.composerActions)
const activePluginDialog = ref<ComposerAction | null>(null)

// Slash Command and Plugin Drawer State
const isSlashModalOpen = ref(false)
const slashModalStep = ref<SlashModalStep>('plugins')
const quranTokenCache = new Map<string, string>()

// Watch text changes to trigger slash modal when user types '/'
watch(text, (newVal) => {
  if (props.disabled) return
  if (newVal && (newVal.endsWith('/') || newVal.endsWith(' /') || newVal.endsWith('\n/'))) {
    if (!isSlashModalOpen.value) {
      isSlashModalOpen.value = true
      slashModalStep.value = 'plugins'
    }
  }
})

const handleSlashSelectPlugin = (pluginIdentifier: string, token: string) => {
  if (text.value.endsWith('/')) {
    text.value = text.value.slice(0, -1) + token
  } else {
    text.value = (text.value ? text.value + ' ' : '') + token
  }
  adjustHeight()
}

const handleSlashSelectSurah = (surah: QuranSurah, token: string) => {
  if (text.value.includes('/quran')) {
    text.value = text.value.replace(/\/quran(?:-sureh:[a-zA-Z0-9_\-]+)?\s*$/, token)
  } else {
    text.value = (text.value ? text.value + ' ' : '') + token
  }
  adjustHeight()
}

const handleSlashConfirm = (payload: {
  token: string
  surah: QuranSurah
  ayahNumber: number
  ayah: QuranAyah
  markdown: string
}) => {
  quranTokenCache.set(payload.token, payload.markdown)

  const regex = /\/quran(?:-sureh:[a-zA-Z0-9_\-]+(?:-ayeh:[0-9]+)?)?\s*$/
  if (regex.test(text.value)) {
    text.value = text.value.replace(regex, payload.token + ' ')
  } else {
    text.value = (text.value ? text.value + ' ' : '') + payload.token + ' '
  }

  isSlashModalOpen.value = false
  nextTick(() => {
    const el = textareaRef.value || expandedTextareaRef.value
    if (el) {
      el.focus()
      const len = text.value.length
      el.setSelectionRange(len, len)
    }
    adjustHeight()
  })
}

const detectedQuranTokens = computed(() => {
  const quranRegex = /\/quran-sureh:([a-zA-Z0-9_\-]+)-ayeh:([0-9]+)/g
  const list: { raw: string; surah: string; ayah: string }[] = []
  const matches = Array.from(text.value.matchAll(quranRegex))
  for (const m of matches) {
    list.push({
      raw: m[0],
      surah: m[1] || '',
      ayah: m[2] || ''
    })
  }
  return list
})

const removeQuranToken = (rawToken: string) => {
  text.value = text.value.replace(rawToken, '').replace(/\s{2,}/g, ' ').trim()
  quranTokenCache.delete(rawToken)
  adjustHeight()
}

const openSlashModalForQuran = () => {
  isSlashModalOpen.value = true
  slashModalStep.value = 'surah'
}

const handlePluginActionClick = (action: ComposerAction) => {
  isActionSheetOpen.value = false
  if (action.id === 'quran-insert-ayah' || action.id === 'quran') {
    isSlashModalOpen.value = true
    slashModalStep.value = 'surah'
  } else if (action.dialogComponent) {
    activePluginDialog.value = action
  } else if (action.execute) {
    action.execute({
      insertText: handlePluginInsert,
      currentText: text.value,
    })
  }
}

const handlePluginInsert = (insertedMarkdown: string) => {
  if (!insertedMarkdown) return
  const el = textareaRef.value || expandedTextareaRef.value
  if (el) {
    const start = el.selectionStart || 0
    const end = el.selectionEnd || 0
    const before = text.value.substring(0, start)
    const after = text.value.substring(end)
    const prefix = before && !before.endsWith('\n\n') ? (before.endsWith('\n') ? '\n' : '\n\n') : ''
    const suffix = after && !after.startsWith('\n\n') ? (after.startsWith('\n') ? '\n' : '\n\n') : ''
    text.value = before + prefix + insertedMarkdown + suffix + after
    nextTick(() => {
      el.focus()
      const newPos = (before + prefix + insertedMarkdown).length
      el.setSelectionRange(newPos, newPos)
    })
  } else {
    text.value = (text.value ? text.value + '\n\n' : '') + insertedMarkdown
  }
  activePluginDialog.value = null
}
</script>

<template>
  <div 
    :class="containerClasses"
    :dir="languageStore.dir"
  >
    <!-- Muted/Disabled overlay message -->
    <div 
      v-if="props.disabled" 
      class="absolute inset-0 bg-background/60 backdrop-blur-3xs rounded-3xl z-20 flex items-center justify-center border border-border/40"
    >
      <div class="bg-card/95 border border-border/80 rounded-2xl px-4 py-2 flex items-center gap-2 shadow-xs">
        <AlertCircleIcon class="size-4 text-muted-foreground animate-pulse" />
        <span class="text-[11px] font-bold text-muted-foreground">{{ languageStore.t('شما اجازه ارسال پیام در این تاپیک را ندارید.', 'You do not have permission to send messages in this topic.') }}</span>
      </div>
    </div>





    <!-- Attachments Preview Bar (Inside the container) -->
    <transition name="attachments-slide">
      <div 
        v-if="attachments.length > 0" 
        class="w-full flex gap-3 overflow-x-auto scrollbar-none z-10 text-start pb-2.5 mb-1.5 border-b border-border/20 px-2"
      >
        <div 
          v-for="file in attachments" 
          :key="file.id"
          class="size-16 rounded-xl border border-border/50 bg-background/40 relative overflow-hidden flex flex-col items-center justify-center shrink-0 group hover:border-primary/30 hover:scale-105 hover:shadow-md transition-all duration-300"
        >
          <!-- Delete button (Top Right in LTR, Top Left in RTL) -->
          <button 
            @click="handleRemoveAttachment(file.id)"
            class="absolute top-1.5 z-15 size-5 p-0 rounded-full bg-black/40 hover:bg-black/60 flex items-center justify-center text-white cursor-pointer transition-all duration-200 hover:rotate-90 hover:scale-110 shadow-xs outline-none"
            :class="[languageStore.isFa ? 'left-1.5' : 'right-1.5']"
            :title="languageStore.t('حذف پیوست', 'Remove attachment')"
          >
            <XIcon class="size-2.5" />
          </button>

          <!-- Uploading state overlay -->
          <div 
            v-if="file.status === 'uploading'" 
            class="absolute inset-0 bg-black/40 z-10 flex flex-col items-center justify-center text-white"
          >
            <Loader2Icon class="size-4 animate-spin text-primary-foreground" />
            <span class="text-[8px] font-mono font-bold mt-1">{{ file.progress || 0 }}%</span>
          </div>

          <!-- Thumbnail content based on file type -->
          <template v-if="file.type === 'image' && file.url">
            <img :src="file.url" class="w-full h-full object-cover" :alt="file.name" />
          </template>

          <template v-else-if="file.type === 'video'">
            <div class="size-full bg-slate-900 flex items-center justify-center relative">
              <VideoIcon class="size-5 text-white/70" />
              <PlayIcon class="size-2.5 text-white absolute bottom-1.5 left-1.5" />
            </div>
          </template>

          <template v-else-if="file.type === 'audio'">
            <div class="size-full flex flex-col items-center justify-center gap-1 p-1.5 bg-violet-500/10">
              <MusicIcon class="size-5 text-violet-500" />
              <span class="text-[8.5px] truncate max-w-full font-mono text-muted-foreground leading-none">{{ file.size || 'صدا' }}</span>
            </div>
          </template>

          <template v-else>
            <div class="size-full flex flex-col items-center justify-center gap-1 p-1.5 bg-sky-500/10">
              <FileTextIcon class="size-5 text-sky-500" />
              <span class="text-[8.5px] truncate max-w-full font-bold text-muted-foreground leading-none">{{ file.size || languageStore.t('فایل', 'File') }}</span>
            </div>
          </template>
          
          <!-- Hover filename tooltip/indicator -->
          <div class="absolute bottom-0 inset-x-0 bg-black/60 py-0.5 px-1.5 truncate text-[7.5px] text-white/90 text-center opacity-0 group-hover:opacity-100 transition-opacity">
            {{ file.name }}
          </div>
        </div>
      </div>
    </transition>

    <!-- Plugin Slash Command Inline Drawer (Inside the container above input row) -->
    <transition name="attachments-slide">
      <div 
        v-if="isSlashModalOpen"
        class="w-full z-20 text-start pb-2 px-1"
      >
        <PluginSlashCommandModal
          :is-open="isSlashModalOpen"
          :initial-step="slashModalStep"
          @close="isSlashModalOpen = false"
          @select-plugin="handleSlashSelectPlugin"
          @select-surah="handleSlashSelectSurah"
          @confirm="handleSlashConfirm"
        />
      </div>
    </transition>

    <!-- Main Message Input Row -->
    <div 
      class="w-full flex items-end gap-1.5 relative" 
      :class="{ 'pt-10': isLongText && !isRecording }"
      :dir="languageStore.dir"
    >
      
      <!-- Right Element: Attach File Button / Plus Menu Button / Cancel Recording Button / Cancel Edit Button -->
      <transition name="button-pop" mode="out-in">
        <!-- Cancel Edit Button -->
        <Button
          v-if="props.isEditMode"
          key="cancel-edit-btn"
          variant="outline"
          :size="hasAttachments || (isLongText && !isRecording) ? 'icon' : 'icon-lg'"
          class="group text-destructive hover:bg-destructive/10 active:scale-95 transition-all duration-200 bg-white dark:bg-muted/20 border border-destructive/20 rounded-2xl"
          :title="languageStore.t('لغو ویرایش', 'Cancel edit')"
          @click="emit('cancel-edit')"
        >
          <XIcon class="transition-transform duration-200 group-hover:scale-110" />
        </Button>

        <!-- Cancel Recording Button -->
        <Button 
          v-else-if="isRecording"
          key="cancel-record"
          variant="destructive"
          :size="hasAttachments ? 'icon' : 'icon-lg'"
          class="group bg-destructive/10 hover:bg-destructive/20 text-destructive border border-destructive/25 active:scale-95 transition-all duration-200"
          :title="languageStore.t('لغو ضبط', 'Cancel recording')"
          @click="cancelRecording"
        >
          <Trash2Icon class="transition-transform duration-200 group-hover:scale-110" />
        </Button>

        <!-- Action Buttons (Attach & Plus) -->
        <div 
          v-else 
          key="action-buttons" 
          class="flex items-center gap-1.5 shrink-0"
        >
          <!-- Plus / More Actions Button -->
          <Button 
            key="plus-btn"
            variant="outline"
            :size="hasAttachments || (isLongText && !isRecording) ? 'icon' : 'icon-lg'"
            class="group text-muted-foreground hover:text-foreground active:scale-95 transition-all duration-200 bg-white dark:bg-muted/20 border border-border/40"
            :disabled="props.disabled"
            :title="languageStore.t('گزینه‌های بیشتر', 'More options')"
            @click="handlePlusClick"
          >
            <PlusIcon class="transition-transform duration-200 group-hover:scale-110" />
          </Button>

          <!-- Normal Attach Button -->
          <Button 
            key="attach-file"
            variant="outline"
            :size="hasAttachments || (isLongText && !isRecording) ? 'icon' : 'icon-lg'"
            class="group text-muted-foreground hover:text-foreground active:scale-95 transition-all duration-200 bg-white dark:bg-muted/20 border border-border/40"
            :disabled="props.disabled"
            :title="languageStore.t('افزودن فایل پیوست', 'Attach file')"
            @click="handleAttachClick"
          >
            <PaperclipIcon class="transition-transform duration-200 group-hover:rotate-12 group-hover:scale-105" />
          </Button>
        </div>
      </transition>

      <!-- Center Element: Text Input / Recording Info Display -->
      <div class="flex-1 min-w-0 relative">
        <!-- Quran Token Visual Badges / Chips -->
        <div
          v-if="detectedQuranTokens.length > 0 && !isRecording"
          class="w-full flex flex-wrap gap-1.5 px-2 pb-1.5 z-10"
        >
          <div
            v-for="tok in detectedQuranTokens"
            :key="tok.raw"
            class="inline-flex items-center gap-1.5 px-2.5 py-0.5 bg-primary/10 border border-primary/20 text-primary rounded-xl text-[11px] font-medium animate-in fade-in"
          >
            <span class="font-mono text-[10px]">{{ tok.raw }}</span>
            <button
              type="button"
              @click="openSlashModalForQuran"
              class="hover:underline text-[10px] text-primary cursor-pointer font-medium"
            >
              {{ languageStore.t('ویرایش', 'Edit') }}
            </button>
            <button
              type="button"
              @click="removeQuranToken(tok.raw)"
              class="size-3.5 rounded-full hover:bg-primary/20 flex items-center justify-center text-[10px] text-primary transition-colors cursor-pointer"
              title="حذف"
            >
              ✕
            </button>
          </div>
        </div>

        <transition name="fade" mode="out-in">
          <!-- Voice Recording Display -->
          <div 
            v-if="isRecording"
            key="recording-status"
            :class="recordingStatusClasses"
          >
            <div class="flex items-center gap-2">
              <span class="size-1.5 bg-destructive rounded-full animate-pulse" />
              <span class="text-[10px] font-bold text-destructive/80">{{ languageStore.t('در حال ضبط صدا...', 'Recording voice...') }}</span>
            </div>
            <span class="font-mono text-[11px] font-bold text-destructive/90">{{ formattedTime }}</span>
          </div>

          <!-- Auto-growing Textarea -->
          <textarea
            v-else
            key="text-input"
            ref="textareaRef"
            v-model="text"
            :disabled="props.disabled"
            :placeholder="props.placeholder === 'پیام خود را بنویسید...' ? languageStore.t('پیام خود را بنویسید...', 'Type your message...') : props.placeholder"
            rows="1"
            :class="textareaClasses"
            dir="auto"
            @select="handleTextareaSelect(false)"
            @mouseup="handleTextareaSelect(false)"
            @keyup="handleTextareaSelect(false)"
            @touchstart="handleTouchStart($event, false)"
            @touchmove="handleTouchMove($event)"
            @touchend="handleTouchEnd($event, false)"
            @focus="handleTextareaFocus(false)"
            @contextmenu="handleContextMenu($event, false)"
            @blur="handleTextareaBlur(false)"
            @keydown="(e) => handleKeydown(e, false)"
          />
        </transition>

        <!-- Floating Format Toolbar (Main Input) -->
        <FloatingFormatMenu
          :show="showFormatMenu"
          :coords="menuCoords"
          :selected-text="selectedText"
          :has-text="Boolean(text.trim())"
          @format="(f) => applyFormat(f, false)"
          @action="(act) => handleMenuAction(act, false)"
        />
      </div>

      <!-- Left Element: Send Button / Record Voice Button / Save Edit Button -->
      <transition name="button-pop" mode="out-in">
        <!-- Save Edit Button -->
        <Button
          v-if="props.isEditMode"
          key="save-edit-btn"
          variant="default"
          :size="hasAttachments || (isLongText && !isRecording) ? 'icon' : 'icon-lg'"
          class="group bg-emerald-500 hover:bg-emerald-600 text-white shadow-md shadow-emerald-500/20 active:scale-95 transition-all duration-200 rounded-2xl border-none"
          :disabled="props.disabled || !hasContent"
          :title="languageStore.t('ذخیره تغییرات', 'Save changes')"
          @click="handleSend"
        >
          <CheckIcon class="transition-transform duration-200 group-hover:scale-110" />
        </Button>

        <!-- Stop/Send Recording Button -->
        <Button 
          v-else-if="isRecording"
          key="stop-record"
          :size="hasAttachments ? 'icon' : 'icon-lg'"
          class="group bg-emerald-500 hover:bg-emerald-600 text-white shadow-md shadow-emerald-500/20 active:scale-95 transition-all duration-200"
          :title="languageStore.t('ارسال صدا', 'Send voice')"
          @click="completeRecording"
        >
          <CheckIcon class="transition-transform duration-200 group-hover:scale-110" />
        </Button>

        <!-- Send message button -->
        <Button 
          v-else-if="hasContent"
          key="send-msg"
          variant="default"
          :size="hasAttachments || (isLongText && !isRecording) ? 'icon' : 'icon-lg'"
          class="group shadow-md shadow-primary/20 hover:scale-105 active:scale-95 transition-all duration-200"
          :disabled="props.disabled"
          :title="languageStore.t('ارسال پیام', 'Send message')"
          @click="handleSend"
        >
          <SendIcon 
            class="-rotate-45 transition-transform duration-200 group-hover:scale-110" 
            :class="[
              languageStore.isFa 
                ? 'scale-x-[-1] group-hover:translate-x-[-2px] group-hover:translate-y-[1px]' 
                : 'group-hover:translate-x-[2px] group-hover:translate-y-[-1px]'
            ]"
          />
        </Button>

        <!-- Record Voice Button -->
        <Button 
          v-else
          key="record-voice"
          variant="outline"
          :size="hasAttachments || (isLongText && !isRecording) ? 'icon' : 'icon-lg'"
          class="group text-muted-foreground hover:text-foreground active:scale-95 transition-all duration-200 bg-white dark:bg-muted/20 border border-border/40"
          :disabled="props.disabled"
          :title="languageStore.t('ضبط صدا', 'Record voice')"
          @click="startRecording"
        >
          <MicIcon class="transition-transform duration-200 group-hover:scale-110" />
        </Button>
      </transition>

      <!-- Expand Button (Positioned absolutely at the top of the input row) -->
      <Button
        v-if="isLongText && !isRecording"
        variant="ghost"
        size="icon-sm"
        :class="[
          'absolute z-30 text-zinc-500 dark:text-zinc-400 hover:text-primary transition-all duration-200 cursor-pointer outline-none active:scale-95 top-2', 
          languageStore.isFa ? 'right-2.5' : 'left-2.5'
        ]"
        :title="languageStore.t('ویرایش در نمای بزرگ', 'Edit in expanded view')"
        @click="showExpanded = true"
      >
        <Maximize2Icon />
      </Button>

      <!-- AI Refiner Sparkle Button (Positioned absolutely next to Expand button) -->
      <Button
        v-if="isLongText && !isRecording"
        variant="ghost"
        size="icon-sm"
        :class="[
          'absolute z-30 text-zinc-500 dark:text-zinc-400 hover:text-primary transition-all duration-200 cursor-pointer outline-none active:scale-95 top-2', 
          languageStore.isFa ? 'right-10' : 'left-10'
        ]"
        :title="languageStore.t('بهبود متن با هوش مصنوعی', 'Refine text with AI')"
        @click="isAiRefinerOpen = true"
      >
        <Wand2Icon />
      </Button>

    </div>

  </div>

  <!-- Expand Modal (Bottom Sheet, 80% screen height) -->
  <teleport to="body">
    <transition name="overlay-fade">
      <div 
        v-if="showExpanded" 
        class="fixed inset-0 bg-background/60 dark:bg-background/80 backdrop-blur-sm z-50 transition-opacity"
        @click="showExpanded = false"
      />
    </transition>

    <transition name="sheet-slide">
      <div 
        v-if="showExpanded" 
        class="fixed bottom-0 inset-x-0 h-[80dvh] bg-white dark:bg-zinc-900 border-t border-x border-border/60 dark:border-border/30 rounded-t-[calc(var(--radius)*1.5)] z-55 flex flex-col shadow-2xl transition-transform overflow-hidden"
        :dir="languageStore.dir"
        @click.stop
      >
        <!-- Drag Handle for Premium Feel -->
        <div class="w-full flex justify-center py-3 shrink-0">
          <div class="w-12 h-1.5 rounded-full bg-muted/60 dark:bg-muted/40 cursor-pointer" @click="showExpanded = false" />
        </div>

        <!-- Header -->
        <div class="px-6 pb-4 border-b border-border/10 flex items-center justify-between shrink-0">
          <div class="flex items-center gap-2">
            <span class="text-sm font-black text-foreground">{{ props.isEditMode ? languageStore.t('ویرایش پیام', 'Edit Message') : languageStore.t('ویرایش پیام طولانی', 'Edit Long Message') }}</span>
            <span class="text-[10px] text-muted-foreground bg-muted px-2 py-0.5 rounded-full font-bold">{{ languageStore.t('نمای بزرگ', 'Expanded View') }}</span>
          </div>
          
          <Button 
            variant="ghost"
            size="icon-sm"
            class="text-muted-foreground hover:text-foreground active:scale-95"
            :title="languageStore.t('بستن', 'Close')"
            @click="showExpanded = false"
          >
            <Minimize2Icon />
          </Button>
        </div>

        <!-- Body: Large Textarea -->
        <div class="flex-1 p-6 overflow-hidden flex flex-col min-h-0 relative">
          <!-- Floating Format Toolbar (Expanded Modal) -->
          <FloatingFormatMenu
            :show="showExpandedFormatMenu"
            :coords="expandedMenuCoords"
            :selected-text="expandedSelectedText"
            :has-text="Boolean(text.trim())"
            @format="(f) => applyFormat(f, true)"
            @action="(act) => handleMenuAction(act, true)"
          />

          <textarea
            ref="expandedTextareaRef"
            v-model="text"
            :placeholder="languageStore.t('پیام خود را بنویسید...', 'Type your message...')"
            class="w-full flex-1 bg-transparent border-none outline-none focus-visible:ring-0 focus-visible:ring-offset-0 focus:ring-0 focus:outline-none focus-visible:outline-none text-sm font-semibold leading-relaxed text-foreground placeholder:text-muted-foreground/50 resize-none overflow-y-auto scrollbar-thin text-start"
            dir="auto"
            @select="handleTextareaSelect(true)"
            @mouseup="handleTextareaSelect(true)"
            @keyup="handleTextareaSelect(true)"
            @touchstart="handleTouchStart($event, true)"
            @touchmove="handleTouchMove($event)"
            @touchend="handleTouchEnd($event, true)"
            @focus="handleTextareaFocus(true)"
            @contextmenu="handleContextMenu($event, true)"
            @blur="handleTextareaBlur(true)"
            @keydown="(e) => handleKeydown(e, true)"
          />
        </div>

        <!-- Footer -->
        <div class="px-6 py-4 border-t border-border/10 bg-muted/5 dark:bg-muted/2 flex items-center justify-between shrink-0 rounded-b-none flex-row-reverse">
          <!-- Actions -->
          <div class="flex items-center gap-2">
            <!-- AI Refiner Sparkle Button in Modal Footer -->
            <Button
              variant="outline"
              size="icon"
              class="rounded-xl border border-border/40 text-muted-foreground hover:text-foreground hover:bg-muted/50 active:scale-95 transition-all duration-200 cursor-pointer outline-none shrink-0"
              :title="languageStore.t('بهبود متن با هوش مصنوعی', 'Refine text with AI')"
              @click="isAiRefinerOpen = true"
            >
              <Wand2Icon class="size-5" />
            </Button>

            <!-- Simplified close/cancel button -->
            <Button
              variant="outline"
              size="icon"
              class="rounded-xl border border-border/40 text-muted-foreground hover:text-foreground hover:bg-muted/50 active:scale-95 transition-all duration-200 cursor-pointer outline-none shrink-0"
              :title="languageStore.t('انصراف', 'Cancel')"
              @click="showExpanded = false"
            >
              <XIcon class="size-5" />
            </Button>

            <!-- Simplified send/save button -->
            <Button 
              :variant="hasContent ? 'default' : 'outline'"
              size="icon"
              class="group rounded-xl active:scale-95 transition-all duration-200 cursor-pointer outline-none disabled:pointer-events-none disabled:opacity-50 shrink-0"
              :class="[
                hasContent 
                  ? 'bg-primary text-primary-foreground border-none' 
                  : 'border border-border/40 text-muted-foreground'
              ]"
              :disabled="props.disabled || !hasContent"
              :title="props.isEditMode ? languageStore.t('ذخیره تغییرات', 'Save Changes') : languageStore.t('ارسال پیام', 'Send Message')"
              @click="handleSendFromModal"
            >
              <SendIcon 
                class="size-5 -rotate-45 transition-transform duration-200 group-hover:scale-110" 
                :class="[
                  languageStore.isFa 
                    ? 'scale-x-[-1] group-hover:translate-x-[-2px] group-hover:translate-y-[1px]' 
                    : 'group-hover:translate-x-[2px] group-hover:translate-y-[-1px]'
                ]"
              />
            </Button>
          </div>

          <!-- Stats -->
          <div class="flex items-center gap-3 text-[10px] text-muted-foreground font-bold">
            <span>{{ languageStore.n(text.length) }} {{ languageStore.t('کاراکتر', 'characters') }}</span>
            <span class="size-1 bg-muted-foreground/30 rounded-full" />
            <span>{{ languageStore.n(lineCount) }} {{ languageStore.t('خط', 'lines') }}</span>
          </div>
        </div>
      </div>
    </transition>
  </teleport>

  <!-- AI Text Refiner Assistant Bottom Sheet -->
  <AIRefinerDrawer
    v-model:open="isAiRefinerOpen"
    :text="text"
    @apply="handleApplyRefinedText"
  />

  <!-- Plus Action Modal (Centered Dialog with 3 Square Cards in 1 Row) -->
  <Dialog :open="isActionSheetOpen" @update:open="(val: boolean) => isActionSheetOpen = val">
    <DialogContent 
      :show-close-button="true"
      class="max-w-[420px] w-[calc(100%-2rem)] rounded-3xl border border-border/70 bg-card p-5 sm:p-6 flex flex-col gap-4 text-start font-sans shadow-2xl z-[60]"
      :dir="languageStore.dir"
    >
      <!-- Header -->
      <DialogHeader class="p-0 space-y-1 text-start">
        <DialogTitle class="text-sm sm:text-base font-bold text-foreground">
          {{ languageStore.t('امکانات ویژه تاپیک', 'Topic Features') }}
        </DialogTitle>
        <DialogDescription class="text-xs text-muted-foreground">
          {{ languageStore.t('یک گزینه را جهت ایجاد و انتشار انتخاب نمایید', 'Select an option to create and post') }}
        </DialogDescription>
      </DialogHeader>

      <!-- 3 Square Action Items in 1 Row -->
      <div class="grid grid-cols-3 gap-2.5 pt-1">
        <!-- 1. Kindness / Donation Campaign (Active) -->
        <button
          type="button"
          class="group relative aspect-square rounded-2xl border border-primary/30 bg-primary/5 hover:bg-primary/10 hover:border-primary/60 flex flex-col items-center justify-center gap-2 p-2 transition-all duration-200 cursor-pointer shadow-xs active:scale-95 text-center select-none"
          @click="handleSelectDonation"
        >
          <div class="size-10 rounded-xl bg-primary/15 text-primary flex items-center justify-center group-hover:scale-110 transition-transform shadow-xs">
            <HeartIcon class="size-5 fill-primary/20" />
          </div>
          <span class="text-xs font-bold text-foreground group-hover:text-primary transition-colors">
            {{ languageStore.t('ایجاد اهدا', 'Donation') }}
          </span>
        </button>

        <!-- 2. Poll / Survey (Coming Soon with Blur & Badge) -->
        <div
          class="relative aspect-square rounded-2xl border border-border/40 bg-muted/20 flex flex-col items-center justify-center gap-2 p-2 opacity-60 backdrop-blur-sm cursor-not-allowed select-none text-center overflow-hidden"
        >
          <Badge 
            variant="secondary" 
            class="absolute top-1.5 right-1.5 text-[8px] font-bold px-1.5 h-4 rounded-full border border-border/40 shadow-xs"
          >
            {{ languageStore.t('به‌زودی', 'Soon') }}
          </Badge>
          <div class="size-10 rounded-xl bg-muted/40 text-muted-foreground flex items-center justify-center shadow-xs">
            <BarChart3Icon class="size-5" />
          </div>
          <span class="text-xs font-semibold text-muted-foreground">
            {{ languageStore.t('نظرسنجی', 'Poll') }}
          </span>
        </div>

        <!-- 3. Event / Meeting (Coming Soon with Blur & Badge) -->
        <div
          class="relative aspect-square rounded-2xl border border-border/40 bg-muted/20 flex flex-col items-center justify-center gap-2 p-2 opacity-60 backdrop-blur-sm cursor-not-allowed select-none text-center overflow-hidden"
        >
          <Badge 
            variant="secondary" 
            class="absolute top-1.5 right-1.5 text-[8px] font-bold px-1.5 h-4 rounded-full border border-border/40 shadow-xs"
          >
            {{ languageStore.t('به‌زودی', 'Soon') }}
          </Badge>
          <div class="size-10 rounded-xl bg-muted/40 text-muted-foreground flex items-center justify-center shadow-xs">
            <CalendarDaysIcon class="size-5" />
          </div>
          <span class="text-xs font-semibold text-muted-foreground">
            {{ languageStore.t('رویداد', 'Event') }}
          </span>
        </div>
      </div>

      <!-- Plugin Actions in Modal -->
      <template v-if="pluginComposerActions.length > 0">
        <div class="pt-2 border-t border-border/40 space-y-2">
          <span class="text-[11px] font-bold text-muted-foreground block">
            {{ languageStore.t('افزونه‌ها و ابزارها', 'Plugins & Tools') }}
          </span>
          <div class="grid grid-cols-3 gap-2.5">
            <button
              v-for="action in pluginComposerActions"
              :key="action.id"
              type="button"
              class="group relative aspect-square rounded-2xl border border-emerald-500/30 bg-emerald-50/10 hover:bg-emerald-50/20 hover:border-emerald-500/60 flex flex-col items-center justify-center gap-2 p-2 transition-all duration-200 cursor-pointer shadow-xs active:scale-95 text-center select-none"
              @click="handlePluginActionClick(action)"
            >
              <div class="size-10 rounded-xl bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 flex items-center justify-center text-xl group-hover:scale-110 transition-transform shadow-xs">
                {{ action.icon || '📖' }}
              </div>
              <span class="text-xs font-bold text-foreground group-hover:text-emerald-600 transition-colors">
                {{ action.label }}
              </span>
            </button>
          </div>
        </div>
      </template>
    </DialogContent>
  </Dialog>

  <!-- Active Plugin Dialog Component Container -->
  <component
    v-if="activePluginDialog && activePluginDialog.dialogComponent"
    :is="activePluginDialog.dialogComponent"
    :on-insert="handlePluginInsert"
    @insert="handlePluginInsert"
    @close="activePluginDialog = null"
  />
</template>

<style scoped>
/* Trans-slide for attachments strip and inline drawers */
.attachments-slide-enter-active,
.attachments-slide-leave-active {
  transition: all 0.35s cubic-bezier(0.16, 1, 0.3, 1);
  max-height: 420px;
  opacity: 1;
  overflow-y: hidden;
}
.attachments-slide-enter-from,
.attachments-slide-leave-to {
  max-height: 0;
  opacity: 0;
  padding-top: 0 !important;
  padding-bottom: 0 !important;
  margin-bottom: 0px;
  border-color: transparent;
  transform: translateY(12px);
}

/* Button Pop animation for swapping */
.button-pop-enter-active,
.button-pop-leave-active {
  transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.button-pop-enter-from {
  opacity: 0;
  transform: scale(0.7);
}
.button-pop-leave-to {
  opacity: 0;
  transform: scale(0.7);
}

/* Fade animation for input transition */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Overlay Fade */
.overlay-fade-enter-active,
.overlay-fade-leave-active {
  transition: opacity 0.3s ease;
}
.overlay-fade-enter-from,
.overlay-fade-leave-to {
  opacity: 0;
}

/* Sheet Slide Up */
.sheet-slide-enter-active,
.sheet-slide-leave-active {
  transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.4s ease;
}
.sheet-slide-enter-from,
.sheet-slide-leave-to {
  transform: translateY(100%);
  opacity: 0.8;
}

/* Scrollbar styling */
.scrollbar-none::-webkit-scrollbar {
  display: none;
}
.scrollbar-none {
  -ms-overflow-style: none;
  scrollbar-width: none;
}

/* Thin Scrollbar for textarea in modal */
.scrollbar-thin::-webkit-scrollbar {
  width: 6px;
}
.scrollbar-thin::-webkit-scrollbar-track {
  background: transparent;
}
.scrollbar-thin::-webkit-scrollbar-thumb {
  background: var(--color-border);
  border-radius: 9999px;
}
.scrollbar-thin::-webkit-scrollbar-thumb:hover {
  background: var(--color-muted-foreground);
}
</style>
