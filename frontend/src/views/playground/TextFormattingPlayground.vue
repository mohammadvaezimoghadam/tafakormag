<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { 
  TypeIcon, 
  Code2Icon, 
  ShieldCheckIcon, 
  QuoteIcon, 
  SparklesIcon, 
  CopyIcon, 
  CheckIcon,
  EyeIcon,
  RefreshCwIcon,
  ArrowRightIcon
} from '@lucide/vue'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import FormattedText from '@/components/common/FormattedText.vue'
import FloatingFormatMenu, { type MenuCoords, type ActionType } from '@/components/common/FloatingFormatMenu.vue'
import TopicMessageInput from '@/components/TopicMessageInput.vue'
import { parseMarkdownToHtml, wrapSelection, type FormatType } from '@/utils/textFormatter'
import { getSelectionPixelRect } from '@/utils/caretPosition'
import { useLanguageStore } from '@/stores/languageStore'
import { useRouter } from 'vue-router'

const languageStore = useLanguageStore()
const router = useRouter()

const editorTextareaRef = ref<HTMLTextAreaElement | null>(null)
const showEditorFormatMenu = ref(false)
const editorMenuCoords = ref<MenuCoords | null>(null)
const editorSelectedText = ref('')

const handleEditorSelect = () => {
  const el = editorTextareaRef.value
  if (!el) return

  const start = el.selectionStart ?? 0
  const end = el.selectionEnd ?? 0

  if (start >= end) {
    showEditorFormatMenu.value = false
    editorSelectedText.value = ''
    editorMenuCoords.value = null
    return
  }

  const rawSelection = el.value.substring(start, end)
  if (!rawSelection || rawSelection.trim().length === 0) {
    showEditorFormatMenu.value = false
    editorSelectedText.value = ''
    editorMenuCoords.value = null
    return
  }

  const rect = getSelectionPixelRect(el, start, end)
  const menuWidth = 330
  const menuHeight = 40
  const verticalGap = 10

  const centerX = rect.left + (rect.width / 2)
  const minX = (menuWidth / 2) + 12
  const maxX = Math.max(minX, el.clientWidth - (menuWidth / 2) - 12)
  const clampedX = Math.min(Math.max(centerX, minX), maxX)

  const candidateTopAbove = rect.top - menuHeight - verticalGap
  let top = 0
  let placement: 'top' | 'bottom' = 'top'

  if (candidateTopAbove >= 0) {
    top = candidateTopAbove
    placement = 'top'
  } else {
    top = rect.bottom + verticalGap
    placement = 'bottom'
  }

  editorMenuCoords.value = {
    top,
    left: clampedX,
    placement
  }
  editorSelectedText.value = rawSelection
  showEditorFormatMenu.value = true
}

const handleEditorTouchend = () => {
  handleEditorSelect()
  setTimeout(handleEditorSelect, 50)
  setTimeout(handleEditorSelect, 120)
}

const handleEditorBlur = () => {
  setTimeout(() => {
    const active = document.activeElement
    if (active && (active as HTMLElement).closest && (active as HTMLElement).closest('.floating-format-menu')) {
      return
    }
    showEditorFormatMenu.value = false
  }, 350)
}

const handleGlobalSelectionChange = () => {
  if (document.activeElement === editorTextareaRef.value) {
    handleEditorSelect()
  }
}

onMounted(() => {
  document.addEventListener('selectionchange', handleGlobalSelectionChange)
})

onUnmounted(() => {
  document.removeEventListener('selectionchange', handleGlobalSelectionChange)
})

const handleEditorAction = async (action: ActionType) => {
  const el = editorTextareaRef.value
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
      const before = currentText.value.substring(0, start)
      const after = currentText.value.substring(end)
      currentText.value = before + after
      setTimeout(() => {
        el.focus()
        el.setSelectionRange(start, start)
        handleEditorSelect()
      }, 0)
    }
  } else if (action === 'select-all') {
    el.focus()
    el.setSelectionRange(0, el.value.length)
    setTimeout(() => {
      handleEditorSelect()
    }, 0)
  } else if (action === 'paste') {
    try {
      const clipText = await navigator.clipboard.readText()
      if (clipText) {
        const before = currentText.value.substring(0, start)
        const after = currentText.value.substring(end)
        currentText.value = before + clipText + after
        setTimeout(() => {
          el.focus()
          el.setSelectionRange(start + clipText.length, start + clipText.length)
          handleEditorSelect()
        }, 0)
      }
    } catch (err) {
      console.warn('Clipboard paste failed:', err)
    }
  }
}

const applyEditorFormat = (format: FormatType) => {
  const el = editorTextareaRef.value
  if (!el) return

  const start = el.selectionStart ?? 0
  const end = el.selectionEnd ?? 0
  const res = wrapSelection(currentText.value, start, end, format)
  currentText.value = res.newText

  setTimeout(() => {
    el.focus()
    el.setSelectionRange(res.newCursorStart, res.newCursorEnd)
    handleEditorSelect()
  }, 0)
}

const handleEditorKeydown = (event: KeyboardEvent) => {
  const isCtrlOrMeta = event.ctrlKey || event.metaKey
  if (isCtrlOrMeta) {
    let format: FormatType | null = null
    const key = event.key.toLowerCase()

    if (key === 'b') format = 'bold'
    else if (key === 'i') format = 'italic'
    else if (key === 'u') format = 'underline'
    else if (key === 'x' && event.shiftKey) format = 'strikethrough'
    else if (key === '`') format = 'code'
    else if (key === 'q' && event.shiftKey) format = 'quote'

    if (format) {
      event.preventDefault()
      applyEditorFormat(format)
    }
  }
}

const sampleAll = `🧠 **هوش مصنوعی و تفکر**

این یک پیام آزمایشی برای بررسی قابلیت *قالب‌بندی غنی متن* است.
شما می‌توانید کلمات را __زیرخط‌دار__ یا ~~خط‌خورده~~ نمایید. همچنین تست ایتالیک _فارسی_ و *انگلیسی* بدون تداخل با نیم‌فاصله‌ها.

> این یک نقل‌قول زیبا در تفکر است.
> خط دوم نقل‌قول که باید در همان کادر نمایش داده شود.

برای استفاده در کد: \`const answer = calculate(42 * 2);\` بسیار سریع کار می‌کند!`

const sampleQuotes = `> بخش اول: تفکر نقادانه مهارتی اساسی در عصر اطلاعات است.
> بخش دوم: توانایی ارزیابی شواهد و تحلیل منطقی.
> بخش سوم: نتیجه‌گیری مبتنی بر واقعیت‌ها.

متن عادی پس از نقل‌قول‌ها برای بررسی فاصله‌گذاری و عدم چسبندگی خطوط.`

const sampleCode = `برای تعریف تابع فیلتر در جاوااسکریپت:
\`const evens = list.filter(item => item * 2 === 4);\`

و در پایتون با متغیرهای زیرخط‌دار:
\`def process_user_data(user_id, is_active=True):\`

کاراکترهای ویژه مانند \`<div> & <span class="test"> * 10\` به درستی ایمن‌سازی می‌شوند.`

const sampleXss = `⚠️ **تست امنیت و خنثی‌سازی کدهای مخرب (XSS Sanitization)**

متن عادی قبل از تگ‌های مخرب.
<script>alert("Hacked! XSS Script Executed");<\/script>
<img src="invalid-image" onerror="alert('Image XSS Triggered')" />
<a href="javascript:alert('Link XSS')">کلیک مخرب</a>
<iframe src="javascript:alert('Iframe XSS')"></iframe>

**نتیجه:** تمام تگ‌های غیرمجاز و اسکریپت‌ها توسط DOMPurify خنثی شده و تنها کاراکترهای مجاز نمایش داده می‌شوند.`

const currentText = ref(sampleAll)
const isCopied = ref(false)

const generatedHtml = computed(() => parseMarkdownToHtml(currentText.value))

const copyHtml = () => {
  navigator.clipboard.writeText(generatedHtml.value)
  isCopied.value = true
  setTimeout(() => {
    isCopied.value = false
  }, 2000)
}

const loadPreset = (preset: string) => {
  currentText.value = preset
}

const handleMockSend = (payload: { text: string }) => {
  currentText.value = payload.text
}
</script>

<template>
  <div class="min-h-screen bg-background text-foreground p-4 sm:p-6 md:p-8 font-sans" :dir="languageStore.dir">
    <!-- Top Header -->
    <div class="max-w-6xl mx-auto flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-border/40 mb-6">
      <div class="flex items-center gap-3">
        <Button 
          variant="ghost" 
          size="icon-sm" 
          class="rounded-xl"
          @click="router.push('/playground')"
        >
          <ArrowRightIcon class="size-4 rtl:rotate-180" />
        </Button>
        <div>
          <div class="flex items-center gap-2">
            <h1 class="text-xl sm:text-2xl font-black text-foreground">پلی‌گراند قالب‌بندی غنی متن</h1>
            <Badge variant="default" class="rounded-full text-[10px] font-mono font-bold bg-primary text-primary-foreground">
              Rich Text v1.0
            </Badge>
          </div>
          <p class="text-xs sm:text-sm text-muted-foreground mt-0.5">
            محیط تست ایزوله رندرینگ مارک‌داون، ایمنی DOMPurify و نوار ابزار شناور
          </p>
        </div>
      </div>

      <!-- Quick Preset Buttons -->
      <div class="flex flex-wrap items-center gap-1.5">
        <Button 
          variant="outline" 
          size="sm" 
          class="rounded-xl text-xs gap-1.5 cursor-pointer hover:border-primary/50"
          @click="loadPreset(sampleAll)"
        >
          <SparklesIcon class="size-3.5 text-primary" />
          <span>همه فرمت‌ها</span>
        </Button>
        <Button 
          variant="outline" 
          size="sm" 
          class="rounded-xl text-xs gap-1.5 cursor-pointer hover:border-primary/50"
          @click="loadPreset(sampleQuotes)"
        >
          <QuoteIcon class="size-3.5 text-sky-500" />
          <span>نقل‌قول چندخطی</span>
        </Button>
        <Button 
          variant="outline" 
          size="sm" 
          class="rounded-xl text-xs gap-1.5 cursor-pointer hover:border-primary/50"
          @click="loadPreset(sampleCode)"
        >
          <Code2Icon class="size-3.5 text-emerald-500" />
          <span>کد برنامه‌نویسی</span>
        </Button>
        <Button 
          variant="outline" 
          size="sm" 
          class="rounded-xl text-xs gap-1.5 cursor-pointer hover:border-destructive/50 text-destructive"
          @click="loadPreset(sampleXss)"
        >
          <ShieldCheckIcon class="size-3.5 text-destructive" />
          <span>تست حمله XSS</span>
        </Button>
      </div>
    </div>

    <!-- Main 2-Column Grid -->
    <div class="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-6">
      
      <!-- Left Column: Live Input & Editor -->
      <div class="flex flex-col gap-4">
        <Card class="border-border/60 shadow-sm rounded-3xl">
          <CardHeader class="pb-3">
            <div class="flex items-center justify-between">
              <CardTitle class="text-sm sm:text-base font-bold flex items-center gap-2">
                <TypeIcon class="size-4 text-primary" />
                <span>ویرایشگر زنده (Input Editor)</span>
              </CardTitle>
              <span class="text-[11px] text-muted-foreground font-mono font-bold">
                {{ currentText.length }} کاراکتر
              </span>
            </div>
            <CardDescription class="text-xs">
              متن را انتخاب کنید تا نوار ابزار شناور ظاهر شود، یا از میانبرهای کیبورد (Ctrl+B, Ctrl+I, Ctrl+U, Ctrl+Shift+X, Ctrl+`) استفاده نمایید.
            </CardDescription>
          </CardHeader>
          <CardContent class="space-y-4">
            <!-- Textarea Editor Area -->
            <div class="relative">
              <!-- Floating Format Toolbar (Editor) -->
              <FloatingFormatMenu
                :show="showEditorFormatMenu"
                :coords="editorMenuCoords"
                :selected-text="editorSelectedText"
                @format="applyEditorFormat"
                @action="handleEditorAction"
              />

              <textarea
                ref="editorTextareaRef"
                v-model="currentText"
                rows="10"
                class="w-full bg-muted/20 border border-border/60 rounded-2xl p-3.5 text-xs sm:text-sm font-medium leading-relaxed text-foreground placeholder:text-muted-foreground/60 outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/20 transition-all resize-y font-mono"
                placeholder="متن مارک‌داون خود را وارد نمایید..."
                dir="auto"
                @select="handleEditorSelect"
                @mouseup="handleEditorSelect"
                @keyup="handleEditorSelect"
                @touchend="handleEditorTouchend"
                @contextmenu.prevent.stop
                @blur="handleEditorBlur"
                @keydown="handleEditorKeydown"
              />
            </div>

            <!-- Interactive Message Input Component Preview -->
            <div class="pt-2 border-t border-border/40">
              <div class="text-xs font-bold text-muted-foreground mb-2 flex items-center justify-between">
                <span>پیش‌نمایش کامپوننت TopicMessageInput:</span>
                <span class="text-[10px] text-primary bg-primary/10 px-2 py-0.5 rounded-full font-semibold">ارسال = اعمال متن</span>
              </div>
              <TopicMessageInput
                :initial-text="currentText"
                placeholder="تایپ کنید و برای تست دکمه ارسال را بزنید..."
                @send="handleMockSend"
                @save="handleMockSend"
              />
            </div>
          </CardContent>
        </Card>
      </div>

      <!-- Right Column: Formatted Output & HTML Inspector -->
      <div class="flex flex-col gap-4">
        
        <!-- Live Formatted Output Card -->
        <Card class="border-border/60 shadow-sm rounded-3xl bg-card">
          <CardHeader class="pb-3">
            <div class="flex items-center justify-between">
              <CardTitle class="text-sm sm:text-base font-bold flex items-center gap-2">
                <EyeIcon class="size-4 text-emerald-500" />
                <span>خروجی زنده رندر شده (Formatted Output)</span>
              </CardTitle>
              <Badge variant="outline" class="text-[10px] text-emerald-600 bg-emerald-500/10 border-emerald-500/20">
                Safe & Sanitized
              </Badge>
            </div>
            <CardDescription class="text-xs">
              نحوه نمایش متن در پست‌ها، حباب‌های چت و کارت‌های تاپیک
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div class="p-4 sm:p-5 rounded-2xl bg-muted/15 border border-border/40 min-h-[140px]">
              <FormattedText 
                :content="currentText" 
                class-name="text-xs sm:text-sm font-medium text-foreground/90 leading-relaxed" 
              />
            </div>
          </CardContent>
        </Card>

        <!-- Sanitized HTML Inspector -->
        <Card class="border-border/60 shadow-sm rounded-3xl">
          <CardHeader class="pb-3">
            <div class="flex items-center justify-between">
              <CardTitle class="text-sm sm:text-base font-bold flex items-center gap-2">
                <Code2Icon class="size-4 text-violet-500" />
                <span>کد HTML تولید شده (Sanitized DOM)</span>
              </CardTitle>
              <Button 
                variant="ghost" 
                size="sm" 
                class="h-7 text-xs gap-1 rounded-xl cursor-pointer"
                @click="copyHtml"
              >
                <CheckIcon v-if="isCopied" class="size-3.5 text-emerald-500" />
                <CopyIcon v-else class="size-3.5" />
                <span>{{ isCopied ? 'کپی شد' : 'کپی HTML' }}</span>
              </Button>
            </div>
            <CardDescription class="text-xs">
              کد ضدعفونی‌شده نهایی که در المان DOM تزریق می‌شود
            </CardDescription>
          </CardHeader>
          <CardContent>
            <pre class="w-full bg-zinc-950 text-zinc-200 p-3.5 rounded-2xl text-[11px] font-mono overflow-x-auto max-h-[220px] scrollbar-thin border border-zinc-800 text-left" dir="ltr"><code>{{ generatedHtml }}</code></pre>
          </CardContent>
        </Card>

      </div>

    </div>
  </div>
</template>
