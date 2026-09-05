<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { 
  BookOpenIcon, 
  SparklesIcon, 
  FeatherIcon, 
  BotIcon, 
  CalendarIcon, 
  RadioIcon, 
  CalculatorIcon, 
  ScrollTextIcon, 
  PaletteIcon
} from '@lucide/vue'
import { useLanguageStore } from '@/stores/languageStore'
import { useToastStore } from '@/stores/toastStore'
import { useUserStore } from '@/stores/userStore'
import { usePluginRegistryStore } from '@/plugins/core/pluginRegistry'
import MarketplaceAppIcon from '@/components/marketplace/MarketplaceAppIcon.vue'
import MarketplaceAppModal from '@/components/marketplace/MarketplaceAppModal.vue'
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
// In RTL: Index 0 is Top-Right (Quran - Active), rest are Coming Soon
const marketplaceApps = ref<MarketplaceApp[]>([
  // 1. Quran Plugin (Active - Top Right in RTL)
  {
    id: 'quran',
    title: 'قرآن کریم',
    category: 'متن، ترجمه و صوت',
    developer: 'تیم نرم‌افزاری تفکر',
    icon: BookOpenIcon,
    isComingSoon: false,
    badge: pluginRegistry.isPluginInstalled('quran') ? 'نصب‌شده' : 'رایگان',
    badgeVariant: 'outline',
    rating: 4.9,
    downloadsCount: 2450,
    isInstalled: pluginRegistry.isPluginInstalled('quran'),
    version: '۱.۲.۰',
    description: 'افزونه جامع و رسمی قرآن کریم شامل متن کامل ۱۱۴ سوره، ۳۰ جزء، ترجمه انصاریان و مکارم شیرازی و قابلیت استناد سریع در پیام‌ها با دستور /quran.',
    capabilities: ['slash_command', 'audio_recitation', 'search_engine', 'translations'],
    screenshots: []
  },
  // 2. Nahj al-Balagha (Coming Soon)
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
  // 3. Sahifeh Sajjadiyya (Coming Soon)
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
  // 4. AI Writing Assistant (Coming Soon)
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
  // 5. Boostan Saadi (Coming Soon - Row 2)
  {
    id: 'boostan',
    title: 'بوستان سعدی',
    category: 'شعر و حکمت کهن',
    developer: 'مرکز تحقیقات ادب فارسی',
    icon: ScrollTextIcon,
    isComingSoon: true,
    badge: 'به‌زودی',
    badgeVariant: 'outline',
    rating: 0,
    downloadsCount: 0,
    isInstalled: false,
    version: '۱.۰.۰',
    description: 'متن کامل ده باب بوستان سعدی (عدل، احسان، عشق، تواضع، رضا، قناعت، تربیت، شکر، توبه و مناجات) با امکان جستجوی ابیات، شرح لغات و درج در پیام‌ها.',
    capabilities: ['slash_command', 'search_engine', 'dictionary'],
    screenshots: []
  },
  // 6. Golha Program (Coming Soon - Row 2)
  {
    id: 'golha',
    title: 'برنامه گل‌ها',
    category: 'موسیقی و نوستالژی',
    developer: 'آرشیو رادیو گلها',
    icon: RadioIcon,
    isComingSoon: true,
    badge: 'به‌زودی',
    badgeVariant: 'outline',
    rating: 0,
    downloadsCount: 0,
    isInstalled: false,
    version: '۱.۰.۰',
    description: 'مجموعه فاخر و ماندگار برنامه‌های رادیو گل‌ها (گل‌های جاویدان، رنگارنگ، یک شاخه گل، برگ سبز و صحرایی) همراه با نوای ساز و آواز اساتید برجسته موسیقی اصیل ایرانی.',
    capabilities: ['audio_streaming', 'archive', 'nostalgia_player'],
    screenshots: []
  },
  // 7. Prayer Times & Calendar (Coming Soon - Row 3)
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
  // 8. Religious Financial Calculator (Coming Soon - Row 3)
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
  // 9. Quote Card Designer (Coming Soon)
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
  if (marketplaceApps.value[0]) {
    const isInstalled = pluginRegistry.isPluginInstalled('quran')
    marketplaceApps.value[0].isInstalled = isInstalled
    marketplaceApps.value[0].badge = isInstalled ? 'نصب‌شده' : 'رایگان'
  }
  try {
    await pluginRegistry.fetchMarketplacePlugins()
    const quranBackend = pluginRegistry.marketplacePlugins.find(p => p.identifier === 'quran')
    if (quranBackend && marketplaceApps.value[0]) {
      const isInstalled = pluginRegistry.isPluginInstalled('quran')
      marketplaceApps.value[0].isInstalled = isInstalled
      marketplaceApps.value[0].badge = isInstalled ? 'نصب‌شده' : 'رایگان'
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
      app.badge = languageStore.t('رایگان', 'Free')
      toastStore.triggerToast(
        languageStore.t(`افزونه «${app.title}» با موفقیت پاک شد.`, `Plugin \"${app.title}\" was removed.`),
        'info'
      )
    } else {
      // 3-second simulated installation delay requested by user
      await new Promise(resolve => setTimeout(resolve, 3000))
      await pluginRegistry.installPlugin(String(app.id))
      app.isInstalled = true
      app.badge = languageStore.t('نصب‌شده', 'Installed')
      toastStore.triggerToast(
        languageStore.t(`افزونه «${app.title}» با موفقیت نصب و فعال شد.`, `Plugin \"${app.title}\" installed and activated.`),
        'success'
      )
    }
  } catch (err) {
    // Graceful offline fallback
    app.isInstalled = !app.isInstalled
    if (app.isInstalled) {
      pluginRegistry.setPluginInstalledLocally(String(app.id), true)
      app.badge = languageStore.t('نصب‌شده', 'Installed')
    } else {
      pluginRegistry.setPluginInstalledLocally(String(app.id), false)
      app.badge = languageStore.t('رایگان', 'Free')
    }
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
    
    <!-- 3-Column Grid of 3 Rows (9 Apps Total) with standard spacing -->
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
