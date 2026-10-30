<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { 
  BookOpenIcon, 
  SparklesIcon, 
  FeatherIcon, 
  BotIcon, 
  CalendarIcon, 
  MicIcon, 
  CalculatorIcon, 
  LibraryIcon, 
  PaletteIcon,
  LayersIcon
} from '@lucide/vue'
import { useLanguageStore } from '@/stores/languageStore'
import { useToastStore } from '@/stores/toastStore'
import { useUserStore } from '@/stores/userStore'
import { usePluginRegistryStore } from '@/plugins/core/pluginRegistry'
import MarketplaceAppIcon from './MarketplaceAppIcon.vue'
import MarketplaceAppModal from './MarketplaceAppModal.vue'
import type { MarketplaceApp } from '@/types/marketplace'

const languageStore = useLanguageStore()
const toastStore = useToastStore()
const userStore = useUserStore()
const pluginRegistry = usePluginRegistryStore()
const router = useRouter()

const selectedAppForModal = ref<MarketplaceApp | null>(null)
const isDetailsModalOpen = ref(false)
const isInstalling = ref(false)

// Exactly 9 Apps in a 3x3 Grid (3 columns x 3 rows)
const marketplaceApps = ref<MarketplaceApp[]>([
  {
    id: 'quran',
    title: 'قرآن کریم',
    category: 'متن، ترجمه و صوت',
    developer: 'تیم نرم‌افزاری تفکر',
    icon: BookOpenIcon,
    isComingSoon: false,
    badge: 'نصب‌شده',
    badgeVariant: 'outline',
    rating: 4.9,
    downloadsCount: 2450,
    isInstalled: true,
    version: '۱.۲.۰',
    description: 'افزونه جامع و رسمی قرآن کریم شامل متن کامل ۱۱۴ سوره، ۳۰ جزء، ترجمه انصاریان و مکارم شیرازی و قابلیت استناد سریع در پیام‌ها با دستور /quran.',
    capabilities: ['slash_command', 'audio_recitation', 'search_engine', 'translations'],
    screenshots: []
  },
  {
    id: 'nahj',
    title: 'نهج‌البلاغه و حکمت‌ها',
    category: 'کلام امیرالمؤمنین (ع)',
    developer: 'کانون اندیشه اسلامی',
    icon: FeatherIcon,
    isComingSoon: true,
    badge: 'به‌زودی',
    badgeVariant: 'outline',
    rating: 0,
    downloadsCount: 0,
    isInstalled: false,
    version: '۰.۹.۰',
    description: 'دسترسی سریع به خطبه‌ها، نامه‌ها و حکمت‌های نهج‌البلاغه با امکان جستجوی موضوعی و درج قطعات برگزیده در گفت‌وگوهای پلتفرم.',
    capabilities: ['slash_command', 'search_engine'],
    screenshots: []
  },
  {
    id: 'sahifeh',
    title: 'صحیفه سجادیه',
    category: 'ادعیه و مناجات',
    developer: 'تیم معارف تفکر',
    icon: SparklesIcon,
    isComingSoon: true,
    badge: 'به‌زودی',
    badgeVariant: 'outline',
    rating: 0,
    downloadsCount: 0,
    isInstalled: false,
    version: '۰.۸.۰',
    description: 'مجموعه دعاهای امام سجاد (ع) همراه با ترجمه روان و تفکیک موضوعی جهت مطالعه و اشتراک‌گذاری در تاپیک‌ها.',
    capabilities: ['slash_command', 'translations'],
    screenshots: []
  },
  {
    id: 'ai-editor',
    title: 'دستیار ویراستار',
    category: 'هوش مصنوعی و متن',
    developer: 'هسته هوش مصنوعی تفکر',
    icon: BotIcon,
    isComingSoon: true,
    badge: 'به‌زودی',
    badgeVariant: 'outline',
    rating: 0,
    downloadsCount: 0,
    isInstalled: false,
    version: '۱.۰.۰',
    description: 'پیشنهاد کلمات، اصلاح ساختار نگارشی، اعراب‌گذاری هوشمند و خلاصه‌سازی متون با استفاده از مدل‌های زبانی بومی.',
    capabilities: ['ai_tools', 'editor_extension'],
    screenshots: []
  },
  {
    id: 'calendar-adhan',
    title: 'تقویم و اوقات شرعی',
    category: 'اذان و رویدادها',
    developer: 'تیم تفکر',
    icon: CalendarIcon,
    isComingSoon: true,
    badge: 'به‌زودی',
    badgeVariant: 'outline',
    rating: 0,
    downloadsCount: 0,
    isInstalled: false,
    version: '۱.۰.۰',
    description: 'محاسبه دقیق اوقات شرعی شهرهای مختلف، تقویم هجری قمری و شمسی و یادآورهای زمان‌بندی‌شده رویدادها.',
    capabilities: ['notifications', 'calendar_sync'],
    screenshots: []
  },
  {
    id: 'voice-notes',
    title: 'یادداشت صوتی',
    category: 'تبدیل گفتار به متن',
    developer: 'تیم نرم‌افزاری تفکر',
    icon: MicIcon,
    isComingSoon: true,
    badge: 'به‌زودی',
    badgeVariant: 'outline',
    rating: 0,
    downloadsCount: 0,
    isInstalled: false,
    version: '۰.۹.۵',
    description: 'ضبط پیام صوتی و تبدیل بلادرنگ صوت به متن فارسی استاندارد جهت ارسال سریع در پیام‌ها و پیش‌نویس‌ها.',
    capabilities: ['speech_to_text', 'audio_player'],
    screenshots: []
  },
  {
    id: 'calculator-khums',
    title: 'محاسبه‌گر وجوهات',
    category: 'خمس، زکات و صدقه',
    developer: 'واحد مالی و شرعی',
    icon: CalculatorIcon,
    isComingSoon: true,
    badge: 'به‌زودی',
    badgeVariant: 'outline',
    rating: 0,
    downloadsCount: 0,
    isInstalled: false,
    version: '۱.۰.۰',
    description: 'ابزار دقیق و گام‌به‌گام برای محاسبه خمس سالانه، زکات فطره، رد مظالم و صدقات مستحبی با تطبیق فتاوای مراجع.',
    capabilities: ['calculator', 'donations_link'],
    screenshots: []
  },
  {
    id: 'hadith-library',
    title: 'کتابخانه حدیثی',
    category: 'اصول کافی و روایات',
    developer: 'مرکز تحقیقات حدیثی',
    icon: LibraryIcon,
    isComingSoon: true,
    badge: 'به‌زودی',
    badgeVariant: 'outline',
    rating: 0,
    downloadsCount: 0,
    isInstalled: false,
    version: '۰.۸.۵',
    description: 'بانک جامع احادیث معتبر شیعه با دسته‌بندی موضوعی اخلاقی، اعتقادی و اجتماعی و سندشناسی روایات.',
    capabilities: ['search_engine', 'slash_command'],
    screenshots: []
  },
  {
    id: 'quote-designer',
    title: 'کارت‌نگار و پوستر',
    category: 'طراحی تصویر و اشتراک',
    developer: 'تیم چندرسانه‌ای تفکر',
    icon: PaletteIcon,
    isComingSoon: true,
    badge: 'به‌زودی',
    badgeVariant: 'outline',
    rating: 0,
    downloadsCount: 0,
    isInstalled: false,
    version: '۱.۰.۰',
    description: 'تولید فوری پوسترهای متنی چشم‌نواز از آیات و احادیث برای اشتراک‌گذاری در استوری‌ها و پیام‌رسان‌ها.',
    capabilities: ['image_export', 'templates'],
    screenshots: []
  }
])

onMounted(async () => {
  try {
    await pluginRegistry.fetchMarketplacePlugins()
    const quranBackend = pluginRegistry.marketplacePlugins.find(p => p.identifier === 'quran')
    if (quranBackend && marketplaceApps.value[0]) {
      marketplaceApps.value[0].isInstalled = quranBackend.is_installed ?? true
    }
  } catch (e) {
    // Offline safe ignore
  }
})

const handleAppClick = (app?: MarketplaceApp) => {
  if (!app) return
  selectedAppForModal.value = app
  isDetailsModalOpen.value = true
}

const handleOpenApp = (app: MarketplaceApp) => {
  isDetailsModalOpen.value = false
  if (app.id === 'quran') {
    router.push('/apps/quran')
    return
  }
  toastStore.triggerToast(
    languageStore.t(`مینی‌اپ «${app.title}» به‌زودی در پلتفرم اصلی منتشر خواهد شد.`, `The \"${app.title}\" mini-app will be released soon in the platform.`),
    'info'
  )
}

const handleInstallApp = async (app: MarketplaceApp) => {
  if (!userStore.isAuthenticated) {
    isDetailsModalOpen.value = false
    userStore.isLoginModalOpen = true
    toastStore.triggerToast(
      languageStore.t('برای نصب و مدیریت افزونه‌ها، لطفاً ابتدا وارد حساب کاربری خود شوید.', 'Please sign in first to install and manage plugins.'),
      'warning'
    )
    return
  }

  isInstalling.value = true
  try {
    if (app.isInstalled) {
      await pluginRegistry.uninstallPlugin(String(app.id))
      app.isInstalled = false
      toastStore.triggerToast(
        languageStore.t(`افزونه «${app.title}» با موفقیت پاک شد.`, `Plugin \"${app.title}\" was removed.`),
        'info'
      )
    } else {
      await new Promise(resolve => setTimeout(resolve, 1500))
      await pluginRegistry.installPlugin(String(app.id))
      app.isInstalled = true
      toastStore.triggerToast(
        languageStore.t(`افزونه «${app.title}» با موفقیت نصب و فعال شد.`, `Plugin \"${app.title}\" installed and activated.`),
        'success'
      )
    }
  } catch (err) {
    app.isInstalled = !app.isInstalled
    toastStore.triggerToast(
      app.isInstalled 
        ? languageStore.t(`افزونه «${app.title}» با موفقیت فعال شد.`, `Plugin \"${app.title}\" activated.`)
        : languageStore.t(`افزونه «${app.title}» پاک شد.`, `Plugin \"${app.title}\" removed.`),
      'success'
    )
  } finally {
    isInstalling.value = false
  }
}
</script>

<template>
  <div class="w-full flex flex-col font-sans select-none pb-24" :dir="languageStore.dir">
    
    <!-- Header banner for apps -->
    <div class="w-full rounded-2xl p-4 bg-muted/30 border border-border/60 mb-3 text-start flex items-center justify-between">
      <div class="flex items-center gap-2">
        <LayersIcon class="size-4 text-primary" />
        <span class="text-xs font-bold text-foreground">بازارچه افزونه‌ها و مینی‌اپ‌های پلتفرم تفکر</span>
      </div>
      <span class="text-[10px] text-muted-foreground">۹ افزونه رسمی</span>
    </div>

    <!-- 3-Column Grid of 3 Rows (9 Apps Total) -->
    <div class="grid grid-cols-3 gap-3.5 sm:gap-6 w-full py-2">
      <div 
        v-for="app in marketplaceApps" 
        :key="app.id"
        class="w-full flex justify-center"
      >
        <MarketplaceAppIcon
          :app="app"
          size="responsive"
          :show-category="true"
          @click="handleAppClick"
        />
      </div>
    </div>

    <!-- Reusable Marketplace App Install / Details Modal -->
    <MarketplaceAppModal
      v-model:open="isDetailsModalOpen"
      :app="selectedAppForModal"
      :is-installed="selectedAppForModal?.isInstalled"
      :is-installing="isInstalling"
      @open-app="handleOpenApp"
      @install="handleInstallApp"
    />

  </div>
</template>
