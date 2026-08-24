<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { 
  SparklesIcon, 
  LayersIcon, 
  BookOpenIcon, 
  CodeIcon, 
  DownloadCloudIcon, 
  CheckIcon, 
  CopyIcon, 
  ClockIcon, 
  StarIcon,
  PlayIcon,
  RotateCcwIcon,
  InfoIcon,
  EyeIcon,
  TerminalIcon,
  CheckCircle2Icon,
  SmartphoneIcon,
  TabletIcon,
  LaptopIcon,
  ShieldCheckIcon,
  ChevronRightIcon,
  ChevronLeftIcon,
  ExternalLinkIcon
} from '@lucide/vue'
import MarketplaceAppIcon from '@/components/marketplace/MarketplaceAppIcon.vue'
import MarketplaceAppModal from '@/components/marketplace/MarketplaceAppModal.vue'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle, 
  DialogDescription, 
  DialogFooter 
} from '@/components/ui/dialog'
import { useLanguageStore } from '@/stores/languageStore'
import type { MarketplaceApp, AppIconSize } from '@/types/marketplace'

const languageStore = useLanguageStore()

// State for custom single icon playground
const selectedVariant = ref<'active' | 'coming-soon'>('active')
const customTitle = ref('افزونه قرآن کریم')
const customCategory = ref('فرهنگی و مذهبی')
const customIconType = ref<'image' | 'vector'>('image')
const customImageUrl = ref('https://images.unsplash.com/photo-1609599006353-e629aaabfeae?auto=format&fit=crop&w=400&q=80')
const customVectorIcon = ref<'book' | 'layers' | 'code' | 'sparkles'>('book')
const customSize = ref<AppIconSize>('responsive')
const customBadge = ref('')
const customBadgeVariant = ref<'default' | 'secondary' | 'outline' | 'destructive'>('secondary')
const customRating = ref(4.9)
const customIsInstalled = ref(false)
const customShowCategory = ref(false)
const customDisabled = ref(false)

const vectorIconComponent = computed(() => {
  switch (customIconType.value === 'vector' ? customVectorIcon.value : 'book') {
    case 'book': return BookOpenIcon
    case 'layers': return LayersIcon
    case 'code': return CodeIcon
    case 'sparkles': return SparklesIcon
    default: return BookOpenIcon
  }
})

// 3-Column Marketplace Row Simulation Apps
const marketplaceMockApps = ref<MarketplaceApp[]>([
  {
    id: 'app-quran',
    title: 'قرآن کریم',
    category: 'متن، ترجمه و صوت آیات',
    developer: 'تیم نرم‌افزاری تفکر',
    iconUrl: 'https://images.unsplash.com/photo-1609599006353-e629aaabfeae?auto=format&fit=crop&w=400&q=80',
    isComingSoon: false,
    badge: 'ویژه',
    badgeVariant: 'default',
    rating: 4.9,
    downloadsCount: 1450,
    isInstalled: true,
    version: '۱.۲.۰',
    description: 'افزونه جامع قرآن کریم شامل متن کامل قرآن با رسم الخط عثمان طه، ترجمه استاد انصاریان، صوت قاریان برجسته و قابلیت اشتراک‌گذاری آیات در تاپیک‌ها.',
    screenshots: [
      'https://images.unsplash.com/photo-1609599006353-e629aaabfeae?auto=format&fit=crop&w=800&q=80',
      'https://images.unsplash.com/photo-1584551246679-0daf3d275d0f?auto=format&fit=crop&w=800&q=80'
    ]
  },
  {
    id: 'app-hadith',
    title: 'احادیث و نهج‌البلاغه',
    category: 'حکمت‌ها و روایات معصومین',
    developer: 'کانون حکمت و اندیشه',
    iconUrl: 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?auto=format&fit=crop&w=400&q=80',
    isComingSoon: false,
    badge: 'جدید',
    badgeVariant: 'secondary',
    rating: 4.8,
    downloadsCount: 680,
    isInstalled: false,
    version: '۱.۰.۰',
    description: 'دسترسی سریع به حکمت‌های نهج‌البلاغه، احادیث اصول کافی و پیام‌های منتخب اخلاقی با امکان درج مستقیم در پیام‌های تاپیک.',
    screenshots: [
      'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?auto=format&fit=crop&w=800&q=80'
    ]
  },
  {
    id: 'app-ai-helper',
    title: 'دستیار ویراستار هوشمند',
    category: 'هوش مصنوعی و بهبود متن',
    developer: 'هسته هوش مصنوعی تفکر',
    iconUrl: '',
    icon: SparklesIcon,
    isComingSoon: true,
    badge: 'به‌زودی',
    badgeVariant: 'secondary',
    rating: 5.0,
    downloadsCount: 0,
    isInstalled: false,
    version: 'نسخه بتا',
    description: 'بهینه‌سازی خودکار لحن متن، تصحیح علائم نگارشی و خلاصه کردن پیام‌های طولانی قبل از انتشار در پیام‌رسان‌ها.',
    screenshots: []
  },
  {
    id: 'app-calendar',
    title: 'تقویم و اوقات شرعی',
    category: 'ابزارها و مناسبت‌ها',
    developer: 'تیم تفکر',
    iconUrl: 'https://images.unsplash.com/photo-1506784983877-45594efa4cbe?auto=format&fit=crop&w=400&q=80',
    isComingSoon: false,
    badge: '',
    badgeVariant: 'secondary',
    rating: 4.7,
    downloadsCount: 920,
    isInstalled: false,
    version: '۱.۱.۰',
    description: 'محاسبه دقیق اوقات شرعی افق شهرهای ایران و نمایش مناسبت‌های روز و یادآور اذان در تاپیک.',
    screenshots: []
  },
  {
    id: 'app-analytics',
    title: 'آمار و تحلیل بازدید',
    category: 'مدیریت و گزارش‌ها',
    developer: 'تیم تحلیل داده',
    iconUrl: '',
    icon: LayersIcon,
    isComingSoon: true,
    badge: 'به‌زودی',
    badgeVariant: 'secondary',
    rating: 0,
    downloadsCount: 0,
    isInstalled: false,
    version: 'نسخه ۲.۰',
    description: 'نمودار تعاملات کاربران، ساعات پربازدید کانال و ارزیابی واکنش‌های پست‌ها.',
    screenshots: []
  },
  {
    id: 'app-webhook',
    title: 'اتصال به وب‌هوک API',
    category: 'توسعه‌دهندگان',
    developer: 'جامعه متن‌باز تفکر',
    iconUrl: '',
    icon: CodeIcon,
    isComingSoon: true,
    badge: 'به‌زودی',
    badgeVariant: 'secondary',
    rating: 0,
    downloadsCount: 0,
    isInstalled: false,
    version: 'نسخه ۱.۰',
    description: 'ارسال خودکار محتوا به وب‌سایت‌ها، وبلاگ‌ها و سرورهای اختصاصی از طریق وب‌هوک HTTP POST.',
    screenshots: []
  }
])

// Details Dialog simulation for clicked app
const isDetailsDialogOpen = ref(false)
const selectedAppForDetails = ref<MarketplaceApp | null>(null)
const isInstallingModalApp = ref(false)

const openCustomModalTest = () => {
  const customApp: MarketplaceApp = {
    id: 'custom-test',
    title: customTitle.value,
    category: customCategory.value,
    developer: 'توسعه‌دهنده آزمایشی',
    isComingSoon: selectedVariant.value === 'coming-soon',
    iconUrl: customIconType.value === 'image' ? customImageUrl.value : '',
    icon: customIconType.value === 'vector' ? vectorIconComponent.value : undefined,
    badge: customBadge.value,
    badgeVariant: customBadgeVariant.value,
    rating: customRating.value,
    downloadsCount: 2450,
    isInstalled: customIsInstalled.value,
    version: '۱.۲.۰',
    description: 'افزونه سفارشی برای تست وضعیت‌های مختلف مودال نصب، امتیاز، باز کردن اپ و اعلان‌های به‌زودی.',
    capabilities: ['slash_command', 'audio_recitation', 'search_engine']
  }
  selectedAppForDetails.value = customApp
  isDetailsDialogOpen.value = true
  logEvent('Opened Custom App Details Modal', { title: customTitle.value, isComingSoon: customApp.isComingSoon })
}

const handleAppIconClick = (app?: MarketplaceApp) => {
  if (!app) {
    openCustomModalTest()
    return
  }
  logEvent('Marketplace App Icon Clicked (Navigating to Details)', { id: app.id, title: app.title })
  selectedAppForDetails.value = app
  isDetailsDialogOpen.value = true
}

const toggleInstallStatus = async (app?: MarketplaceApp) => {
  const target = app || selectedAppForDetails.value
  if (target) {
    isInstallingModalApp.value = true
    await new Promise(r => setTimeout(r, 600))
    target.isInstalled = !target.isInstalled
    isInstallingModalApp.value = false
    logEvent('App Install Status Changed', { 
      id: target.id, 
      installed: target.isInstalled 
    })
  }
}

const handleOpenAppFromPlayground = (app: MarketplaceApp) => {
  logEvent('Open Mini-App Button Clicked', { id: app.id, title: app.title })
  isDetailsDialogOpen.value = false
}

const handleNotifyFromPlayground = (app: MarketplaceApp) => {
  logEvent('Notify Me Button Toggled', { id: app.id, title: app.title })
}

// Event Log system
interface SystemEvent {
  id: number
  time: string
  name: string
  data: string
}
const eventLog = ref<SystemEvent[]>([])
let logId = 0

const logEvent = (name: string, data: any) => {
  const now = new Date()
  const timeStr = now.toTimeString().split(' ')[0] ?? ''
  eventLog.value.unshift({
    id: ++logId,
    time: timeStr,
    name,
    data: JSON.stringify(data)
  })
}

// Code Snippet Generator
const codeCopied = ref(false)
const activeTab = ref<'preview' | 'code'>('preview')

const generatedCode = computed(() => {
  const isComingSoon = selectedVariant.value === 'coming-soon'
  const lines: string[] = ['<MarketplaceAppIcon']
  lines.push(`  title="${customTitle.value}"`)
  if (customCategory.value && customShowCategory.value) {
    lines.push(`  category="${customCategory.value}"`)
    lines.push(`  :show-category="true"`)
  }
  if (isComingSoon) {
    lines.push(`  :is-coming-soon="true"`)
  }
  if (customIconType.value === 'image' && customImageUrl.value) {
    lines.push(`  icon-url="${customImageUrl.value}"`)
  } else if (customIconType.value === 'vector') {
    const iconName = customVectorIcon.value === 'book' ? 'BookOpenIcon' : 
                     customVectorIcon.value === 'layers' ? 'LayersIcon' : 
                     customVectorIcon.value === 'code' ? 'CodeIcon' : 'SparklesIcon'
    lines.push(`  :icon="${iconName}"`)
  }
  if (customSize.value !== 'responsive') {
    lines.push(`  size="${customSize.value}"`)
  }
  if (customBadge.value) {
    lines.push(`  badge="${customBadge.value}"`)
    if (customBadgeVariant.value !== 'secondary') {
      lines.push(`  badge-variant="${customBadgeVariant.value}"`)
    }
  }
  if (customRating.value > 0 && !isComingSoon) {
    lines.push(`  :rating="${customRating.value}"`)
  }
  if (customIsInstalled.value && !isComingSoon) {
    lines.push(`  :is-installed="true"`)
  }
  if (customDisabled.value) {
    lines.push(`  :disabled="true"`)
  }
  lines.push(`  @click="handleAppClick"`)
  lines.push('/>')

  return `<!-- 1. Script Setup -->\n<script setup lang="ts">\nimport MarketplaceAppIcon from '@/components/marketplace/MarketplaceAppIcon.vue'\n\nconst handleAppClick = (app?: any) => {\n  console.log('App icon clicked:', app)\n}\n<\/script>\n\n<!-- 2. Template -->\n${lines.join('\n')}`
})

const copyCode = async () => {
  try {
    await navigator.clipboard.writeText(generatedCode.value)
    codeCopied.value = true
    logEvent('Code Copied', { length: generatedCode.value.length })
    setTimeout(() => { codeCopied.value = false }, 2000)
  } catch (err) {
    console.error('Failed to copy code', err)
  }
}
</script>

<template>
  <div class="w-full max-w-6xl mx-auto p-4 sm:p-6 flex flex-col gap-6 select-none font-sans" :dir="languageStore.dir">
    
    <!-- Top Header & Breadcrumb -->
    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-border/60 pb-5">
      <div class="flex items-center gap-3">
        <div class="size-10 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary shadow-xs">
          <LayersIcon class="size-5" />
        </div>
        <div>
          <h1 class="text-base sm:text-lg font-black text-foreground">
            {{ languageStore.t('آیکون افزونه‌های بازارچه (MarketplaceAppIcon)', 'Marketplace App Icon Component') }}
          </h1>
          <p class="text-xs text-muted-foreground mt-0.5">
            {{ languageStore.t('طراحی مربعی با گوشه‌های گرد در دو حالت «دارای آیکون» و «به‌زودی» با چیدمان ۳ ستونه', 'Rounded squircle app icon in standard & Coming-Soon variants with 3-column row grid') }}
          </p>
        </div>
      </div>

      <!-- Mode / Code Tab Switcher -->
      <Tabs v-model="activeTab" class="w-full sm:w-auto">
        <TabsList class="grid grid-cols-2 bg-muted/60 p-1 rounded-xl h-9 w-full sm:w-60">
          <TabsTrigger value="preview" class="text-xs font-bold rounded-lg flex items-center gap-1.5 data-[state=active]:bg-background data-[state=active]:shadow-xs">
            <EyeIcon class="size-3.5" />
            <span>{{ languageStore.t('پیش‌نمایش زنده', 'Live Preview') }}</span>
          </TabsTrigger>
          <TabsTrigger value="code" class="text-xs font-bold rounded-lg flex items-center gap-1.5 data-[state=active]:bg-background data-[state=active]:shadow-xs">
            <TerminalIcon class="size-3.5" />
            <span>{{ languageStore.t('کد کامپوننت', 'Vue Code') }}</span>
          </TabsTrigger>
        </TabsList>
      </Tabs>
    </div>

    <!-- MAIN VIEW 1: PREVIEW -->
    <div v-if="activeTab === 'preview'" class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
      
      <!-- Left Column: Controls & Props Editor (5 Cols) -->
      <div class="lg:col-span-5 flex flex-col gap-5 bg-card/40 border border-border/60 rounded-2xl p-5 shadow-xs backdrop-blur-md">
        
        <div class="flex items-center justify-between border-b border-border/40 pb-3">
          <span class="text-xs font-extrabold text-foreground">{{ languageStore.t('تنظیمات آیکون نمونه', 'Icon Sandbox Controls') }}</span>
          <Badge variant="outline" class="text-[9.5px] font-mono font-bold">Props Editor</Badge>
        </div>

        <!-- 1. Mode Variant: Active vs Coming Soon -->
        <div class="flex flex-col gap-1.5 text-start">
          <Label class="text-[10px] text-muted-foreground">{{ languageStore.t('حالت نمایش کامپوننت (Variant):', 'Component Mode Variant:') }}</Label>
          <div class="grid grid-cols-2 gap-2 bg-muted/50 p-1 rounded-xl border border-border/40">
            <button
              @click="selectedVariant = 'active'; logEvent('Variant Changed', { mode: 'active' })"
              :class="[
                'py-2 px-3 rounded-lg text-xs font-bold transition-all cursor-pointer flex items-center justify-center gap-1.5',
                selectedVariant === 'active' ? 'bg-background text-primary shadow-xs border border-border/40' : 'text-muted-foreground hover:text-foreground'
              ]"
            >
              <CheckCircle2Icon class="size-3.5" />
              <span>{{ languageStore.t('دارای تصویر / فعال', 'Active / With Icon') }}</span>
            </button>
            <button
              @click="selectedVariant = 'coming-soon'; logEvent('Variant Changed', { mode: 'coming-soon' })"
              :class="[
                'py-2 px-3 rounded-lg text-xs font-bold transition-all cursor-pointer flex items-center justify-center gap-1.5',
                selectedVariant === 'coming-soon' ? 'bg-amber-500/10 text-amber-600 dark:text-amber-400 font-black shadow-xs border border-amber-500/30' : 'text-muted-foreground hover:text-foreground'
              ]"
            >
              <ClockIcon class="size-3.5" />
              <span>{{ languageStore.t('حالت به‌زودی (Coming Soon)', 'Coming Soon Mode') }}</span>
            </button>
          </div>
        </div>

        <!-- 2. Titles & Text Editor -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 text-start">
          <div class="flex flex-col gap-1">
            <Label class="text-[10px] text-muted-foreground">{{ languageStore.t('عنوان افزونه (title):', 'App Title:') }}</Label>
            <Input v-model="customTitle" class="h-8 text-xs font-bold" />
          </div>
          <div class="flex flex-col gap-1">
            <Label class="text-[10px] text-muted-foreground">{{ languageStore.t('دسته‌بندی (category):', 'Category:') }}</Label>
            <Input v-model="customCategory" class="h-8 text-xs" />
          </div>
        </div>

        <!-- 3. Icon Source: Image URL vs Lucide Vector Icon -->
        <div class="flex flex-col gap-2 text-start">
          <Label class="text-[10px] text-muted-foreground">{{ languageStore.t('نوع محتوای آیکون:', 'Icon Source Type:') }}</Label>
          <div class="grid grid-cols-2 gap-2">
            <button
              @click="customIconType = 'image'"
              :class="[
                'py-1.5 px-2 rounded-lg text-xs font-semibold border transition-all cursor-pointer',
                customIconType === 'image' ? 'bg-primary/10 border-primary text-primary font-bold' : 'border-border/60 bg-muted/20 text-muted-foreground'
              ]"
            >
              {{ languageStore.t('تصویر آنلاین (Image URL)', 'Image URL') }}
            </button>
            <button
              @click="customIconType = 'vector'"
              :class="[
                'py-1.5 px-2 rounded-lg text-xs font-semibold border transition-all cursor-pointer',
                customIconType === 'vector' ? 'bg-primary/10 border-primary text-primary font-bold' : 'border-border/60 bg-muted/20 text-muted-foreground'
              ]"
            >
              {{ languageStore.t('آیکون برداری (Lucide Icon)', 'Lucide Icon') }}
            </button>
          </div>

          <!-- Image URL Input -->
          <div v-if="customIconType === 'image'" class="flex flex-col gap-1 mt-1">
            <Input v-model="customImageUrl" placeholder="https://..." class="h-8 text-[11px] font-mono" />
          </div>

          <!-- Vector Icon Selector -->
          <div v-else class="grid grid-cols-4 gap-1.5 mt-1 bg-muted/30 p-1.5 rounded-xl border border-border/40">
            <button
              v-for="ic in (['book', 'layers', 'code', 'sparkles'] as const)"
              :key="ic"
              @click="customVectorIcon = ic"
              :class="[
                'py-1 rounded-lg text-[10px] font-bold flex flex-col items-center gap-1 transition-all cursor-pointer',
                customVectorIcon === ic ? 'bg-background text-primary shadow-xs border border-border/40' : 'text-muted-foreground hover:text-foreground'
              ]"
            >
              <BookOpenIcon v-if="ic === 'book'" class="size-4" />
              <LayersIcon v-else-if="ic === 'layers'" class="size-4" />
              <CodeIcon v-else-if="ic === 'code'" class="size-4" />
              <SparklesIcon v-else class="size-4" />
              <span>{{ ic }}</span>
            </button>
          </div>
        </div>

        <!-- 4. Sizing Switcher -->
        <div class="flex flex-col gap-1.5 text-start">
          <Label class="text-[10px] text-muted-foreground">{{ languageStore.t('اندازه آیکون (size):', 'Icon Size:') }}</Label>
          <div class="grid grid-cols-4 gap-1 bg-muted/50 p-1 rounded-xl border border-border/40 text-xs">
            <button
              v-for="sz in (['responsive', 'sm', 'md', 'lg'] as const)"
              :key="sz"
              @click="customSize = sz"
              :class="[
                'py-1 rounded-lg text-[10.5px] font-bold transition-all cursor-pointer',
                customSize === sz ? 'bg-background text-primary shadow-xs border border-border/40' : 'text-muted-foreground hover:text-foreground'
              ]"
            >
              {{ sz === 'responsive' ? 'پاسخگو' : sz.toUpperCase() }}
            </button>
          </div>
        </div>

        <!-- 5. Status & Badges -->
        <div class="grid grid-cols-2 gap-3 text-start">
          <div class="flex flex-col gap-1">
            <Label class="text-[10px] text-muted-foreground">{{ languageStore.t('نشان اختصاصی (badge):', 'Custom Badge:') }}</Label>
            <Input v-model="customBadge" placeholder="مثال: ویژه، رایگان" class="h-8 text-xs" />
          </div>
          <div class="flex flex-col gap-1">
            <Label class="text-[10px] text-muted-foreground">{{ languageStore.t('امتیاز ستاره‌ای (rating):', 'Star Rating:') }}</Label>
            <Input type="number" step="0.1" min="0" max="5" v-model.number="customRating" class="h-8 text-xs font-mono font-bold" />
          </div>
        </div>

        <!-- 6. Toggle Options -->
        <div class="grid grid-cols-2 gap-2 pt-2 border-t border-border/30">
          <button
            @click="customIsInstalled = !customIsInstalled"
            class="px-2.5 py-1.5 text-xs rounded-lg border flex items-center justify-between cursor-pointer transition-all"
            :class="customIsInstalled ? 'bg-primary/10 border-primary text-primary font-bold' : 'border-border/60 bg-muted/20 text-muted-foreground'"
          >
            <span>{{ languageStore.t('نصب‌شده', 'Installed') }}</span>
            <CheckIcon v-if="customIsInstalled" class="size-3.5" />
          </button>
          <button
            @click="customShowCategory = !customShowCategory"
            class="px-2.5 py-1.5 text-xs rounded-lg border flex items-center justify-between cursor-pointer transition-all"
            :class="customShowCategory ? 'bg-primary/10 border-primary text-primary font-bold' : 'border-border/60 bg-muted/20 text-muted-foreground'"
          >
            <span>{{ languageStore.t('نمایش دسته‌بندی', 'Show Category') }}</span>
            <CheckIcon v-if="customShowCategory" class="size-3.5" />
          </button>
        </div>

      </div>

      <!-- Right Column: Live Showcase & Marketplace Grid Row (7 Cols) -->
      <div class="lg:col-span-7 flex flex-col gap-6">
        
        <!-- Showcase Box 1: Single Icon Isolated Sandbox -->
        <div class="w-full bg-card/30 border border-border/60 rounded-2xl p-6 shadow-xs flex flex-col items-center justify-center min-h-[220px] relative overflow-hidden">
          <div class="absolute top-3 right-4 flex items-center gap-1.5 text-[10px] text-muted-foreground font-mono">
            <span class="size-2 rounded-full bg-emerald-500 animate-pulse" />
            <span>Single Icon Sandbox</span>
          </div>

          <!-- The Component Live Preview -->
          <div class="w-28 sm:w-36 flex flex-col items-center">
            <MarketplaceAppIcon
              :title="customTitle"
              :category="customCategory"
              :is-coming-soon="selectedVariant === 'coming-soon'"
              :icon-url="customIconType === 'image' ? customImageUrl : ''"
              :icon="customIconType === 'vector' ? vectorIconComponent : undefined"
              :size="customSize"
              :badge="customBadge"
              :badge-variant="customBadgeVariant"
              :rating="customRating"
              :is-installed="customIsInstalled"
              :show-category="customShowCategory"
              :disabled="customDisabled"
              @click="handleAppIconClick()"
            />

            <!-- Direct Modal Preview Button -->
            <Button
              size="sm"
              variant="outline"
              @click="openCustomModalTest"
              class="mt-3 text-xs font-bold gap-1.5 rounded-xl border-border/80 hover:bg-muted cursor-pointer shadow-2xs"
            >
              <EyeIcon class="size-3.5 text-primary" />
              <span>{{ languageStore.t('تست و باز کردن مودال نصب', 'Test Install Modal') }}</span>
            </Button>
          </div>
        </div>

        <!-- Showcase Box 2: 3-Column Marketplace Row Grid (Simulating Real Marketplace Layout) -->
        <div class="w-full bg-card/40 border border-border/60 rounded-2xl p-5 sm:p-6 shadow-xs flex flex-col gap-4">
          <div class="flex items-center justify-between border-b border-border/40 pb-3">
            <div class="flex items-center gap-2">
              <div class="size-7 rounded-xl bg-primary/10 flex items-center justify-center text-primary font-bold text-xs">
                ۳
              </div>
              <div class="flex flex-col text-start">
                <span class="text-xs font-black text-foreground">
                  {{ languageStore.t('شبیه‌سازی چیدمان بازارچه (۳ آیکون در هر ردیف)', 'Marketplace Layout Simulation (3 per row)') }}
                </span>
                <span class="text-[9.5px] text-muted-foreground">
                  {{ languageStore.t('روی هر آیکون کلیک کنید تا وارد صفحه مشخصات و دانلود شوید', 'Click on any icon to open download & specs details modal') }}
                </span>
              </div>
            </div>
            <Badge variant="secondary" class="text-[9px] px-2 py-0.5 font-bold">Grid 3-Col</Badge>
          </div>

          <!-- 3-Column Grid of Icons (Exact specification: 3 items per row) -->
          <div class="grid grid-cols-3 gap-3 sm:gap-6 w-full py-2">
            <div 
              v-for="app in marketplaceMockApps.slice(0, 3)" 
              :key="app.id"
              class="w-full flex justify-center"
            >
              <MarketplaceAppIcon
                :app="app"
                size="responsive"
                :show-category="true"
                @click="handleAppIconClick"
              />
            </div>
          </div>

          <!-- Second Row in Grid (Additional coming soon & installed items) -->
          <div class="border-t border-border/30 pt-3 flex flex-col gap-2">
            <span class="text-[10px] font-bold text-muted-foreground text-start">
              {{ languageStore.t('ردیف دوم (نمونه‌های بیشتر):', 'Second Row (More Samples):') }}
            </span>
            <div class="grid grid-cols-3 gap-3 sm:gap-6 w-full py-1">
              <div 
                v-for="app in marketplaceMockApps.slice(3, 6)" 
                :key="app.id"
                class="w-full flex justify-center"
              >
                <MarketplaceAppIcon
                  :app="app"
                  size="responsive"
                  :show-category="true"
                  @click="handleAppIconClick"
                />
              </div>
            </div>
          </div>
        </div>

        <!-- Showcase Box 3: Event Log -->
        <div class="w-full bg-card/25 border border-border/40 rounded-xl p-4 flex flex-col gap-2 text-start">
          <div class="flex items-center justify-between border-b border-border/20 pb-2">
            <span class="text-[10px] font-bold text-muted-foreground flex items-center gap-1.5">
              <TerminalIcon class="size-3 text-primary" />
              <span>لاگ رویدادها و کلیک‌ها (Event Logger):</span>
            </span>
            <button 
              @click="eventLog = []" 
              class="text-[9.5px] text-muted-foreground hover:text-destructive transition-colors cursor-pointer"
            >
              پاکسازی لاگ
            </button>
          </div>
          <div class="flex flex-col gap-1 max-h-28 overflow-y-auto font-mono text-[10px]">
            <div 
              v-for="ev in eventLog" 
              :key="ev.id" 
              class="flex items-center gap-2 py-0.5 border-b border-border/10"
            >
              <span class="text-muted-foreground shrink-0">{{ ev.time }}</span>
              <span class="text-primary font-bold shrink-0">[{{ ev.name }}]</span>
              <span class="text-foreground/80 truncate">{{ ev.data }}</span>
            </div>
            <div v-if="eventLog.length === 0" class="text-muted-foreground/60 italic text-[9.5px] py-1">
              هیچ رویدادی ثبت نشده است. روی آیکون‌ها کلیک کنید.
            </div>
          </div>
        </div>

      </div>

    </div>

    <!-- MAIN VIEW 2: VUE CODE GENERATOR -->
    <div v-else class="w-full flex flex-col gap-4 bg-card/40 border border-border/60 rounded-2xl p-6 shadow-xs">
      <div class="flex items-center justify-between border-b border-border/40 pb-3">
        <div class="flex items-center gap-2">
          <TerminalIcon class="size-4 text-primary" />
          <span class="text-xs font-bold text-foreground">کد آماده جهت استفاده در پروژه (Shadcn-Vue Pattern)</span>
        </div>
        <Button 
          size="sm" 
          variant="outline" 
          @click="copyCode" 
          class="text-xs font-bold gap-1.5 h-8 cursor-pointer"
        >
          <CheckIcon v-if="codeCopied" class="size-3.5 text-green-500" />
          <CopyIcon v-else class="size-3.5" />
          <span>{{ codeCopied ? 'کپی شد!' : 'کپی کد کامپوننت' }}</span>
        </Button>
      </div>

      <pre class="p-4 rounded-xl bg-muted/50 border border-border/40 font-mono text-xs text-foreground/90 overflow-x-auto text-start leading-relaxed whitespace-pre">{{ generatedCode }}</pre>
    </div>

    <!-- DETAILS & INSTALL MODAL (Modular Component) -->
    <MarketplaceAppModal
      v-model:open="isDetailsDialogOpen"
      :app="selectedAppForDetails"
      :is-installed="selectedAppForDetails?.isInstalled"
      :is-installing="isInstallingModalApp"
      @install="toggleInstallStatus"
      @open-app="handleOpenAppFromPlayground"
      @notify="handleNotifyFromPlayground"
    />

  </div>
</template>