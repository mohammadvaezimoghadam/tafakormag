<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import DonationCard from '@/components/kindness/DonationCard.vue'
import ConfirmModal from '@/components/ConfirmModal.vue'
import type { DonationCampaignProps, CampaignCategory } from '@/types/kindness'
import { fetchDonationCampaigns, deleteDonationCampaign } from '@/api'
import { useLanguageStore } from '@/stores/languageStore'
import { useUserStore } from '@/stores/userStore'
import { useToastStore } from '@/stores/toastStore'
import { Skeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  HeartIcon, 
  LayersIcon,
  PlusIcon,
  SearchIcon,
  RefreshCwIcon,
  CheckCircle2Icon,
  UserIcon
} from '@lucide/vue'

const props = withDefaults(defineProps<{
  searchQuery?: string
}>(), {
  searchQuery: ''
})

const emit = defineEmits<{
  (e: 'donate-click', campaign: DonationCampaignProps): void
  (e: 'create-campaign'): void
  (e: 'edit-campaign', campaign: DonationCampaignProps): void
  (e: 'topic-click', topicId: string | number): void
  (e: 'transparency-click', imageIndex: number, imageUrl: string): void
}>()

const languageStore = useLanguageStore()
const userStore = useUserStore()
const toastStore = useToastStore()
const router = useRouter()

// Category definitions matching CreateDonationDialog
interface CategoryChip {
  id: 'my_campaigns' | 'all' | CampaignCategory
  labelFa: string
  labelEn: string
}

const CATEGORIES: CategoryChip[] = [
  { id: 'my_campaigns', labelFa: 'توسط من', labelEn: 'By Me' },
  { id: 'all', labelFa: 'همه', labelEn: 'All' },
  { id: 'mosque', labelFa: 'مسجد و اماکن مذهبی', labelEn: 'Mosque' },
  { id: 'school', labelFa: 'مدرسه و آموزش', labelEn: 'School' },
  { id: 'health', labelFa: 'درمانی و سلامت', labelEn: 'Health' },
  { id: 'livelihood', labelFa: 'نیازمندان و معیشت', labelEn: 'Livelihood' },
  { id: 'construction', labelFa: 'عمرانی و تجهیزات', labelEn: 'Construction' },
  { id: 'other', labelFa: 'متفرقه و عمومی', labelEn: 'Other' }
]

const selectedCategory = ref<'my_campaigns' | 'all' | CampaignCategory>('all')
const loading = ref(true)
const campaigns = ref<DonationCampaignProps[]>([])

// Default high-quality sample data if backend has no records yet
const SAMPLE_CAMPAIGNS: DonationCampaignProps[] = [
  {
    id: 1,
    title: 'تجهیز و شاداب‌سازی ۲ کلاس درس در دبستان روستای محروم',
    description: 'خرید ۲۰ عدد نیمکت استاندارد، یک تخته هوشمند و رنگ‌آمیزی کامل کلاس‌ها جهت ایجاد محیطی پویا برای دانش‌آموزان منطقه محروم.',
    topicId: 101,
    topicName: 'کانون جهادی مدرسه شهید رجایی',
    category: 'مدرسه و آموزش',
    status: 'active',
    targetAmount: 85000000,
    collectedAmount: 52000000,
    donorsCount: 38,
    authorName: 'گروه جهادی عمار',
    authorAvatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=150&q=80',
    timestamp: '۲ روز پیش',
    mediaGallery: [
      'https://images.unsplash.com/photo-1509062522246-3755977927d7?auto=format&fit=crop&w=800&q=80',
      'https://images.unsplash.com/photo-1580582932707-520aed937b7b?auto=format&fit=crop&w=800&q=80'
    ],
    recentDonors: [
      {
        id: 'd-1',
        name: 'علی رضایی',
        amount: 5000000,
        avatarUrl: 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=150&q=80',
        isAnonymous: false,
        donatedAt: '۱۰ دقیقه پیش'
      },
      {
        id: 'd-2',
        name: 'کاربر ناشناس',
        amount: 10000000,
        isAnonymous: true,
        donatedAt: '۲ ساعت پیش'
      },
      {
        id: 'd-3',
        name: 'مریم حسینی',
        amount: 2000000,
        avatarUrl: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=150&q=80',
        isAnonymous: false,
        donatedAt: 'دیروز'
      }
    ]
  },
  {
    id: 2,
    title: 'تامین سیستم گرمایشی و تهویه مسجد و حسینیه حضرت ولیعصر (عج)',
    description: 'خرید و راه‌اندازی دستگاه پکیج و رادیاتور جهت تامین گرمایش سالن اصلی مسجد و جلسات قرآنی جوانان.',
    topicId: 102,
    topicName: 'مسجد حضرت ولیعصر (عج)',
    category: 'مسجد و اماکن مذهبی',
    status: 'active',
    targetAmount: 60000000,
    collectedAmount: 60000000,
    donorsCount: 45,
    authorName: 'هیئت امنای مسجد',
    authorAvatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=150&q=80',
    timestamp: '۴ روز پیش',
    mediaGallery: [
      'https://images.unsplash.com/photo-1548625149-fc4a29cf7092?auto=format&fit=crop&w=800&q=80'
    ],
    recentDonors: [
      {
        id: 'd-10',
        name: 'محسن کریمی',
        amount: 15000000,
        isAnonymous: false,
        donatedAt: '۳ روز پیش'
      }
    ]
  },
  {
    id: 3,
    title: 'تهیه و توزیع ۱۲۰ بسته معیشتی و لوازم‌التحریر برای خانواده‌های کم‌برخوردار',
    description: 'پویش تامین ارزاق ضروری شامل برنج، روغن، حبوبات و بسته‌های کامل نوشت‌افزار تحصیلی برای کودکان خانواده‌های نیازمند.',
    topicId: 103,
    topicName: 'خیریه یاس نبوی',
    category: 'نیازمندان و معیشت',
    status: 'executed',
    targetAmount: 90000000,
    collectedAmount: 90000000,
    donorsCount: 82,
    authorName: 'مرکز نیکوکاری یاس',
    authorAvatar: 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?auto=format&fit=crop&w=150&q=80',
    timestamp: 'هفته گذشته',
    mediaGallery: [
      'https://images.unsplash.com/photo-1488521787991-ed7bbaae773c?auto=format&fit=crop&w=800&q=80'
    ],
    recentDonors: [
      {
        id: 'd-20',
        name: 'زهرا موسوی',
        amount: 8000000,
        avatarUrl: 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?auto=format&fit=crop&w=150&q=80',
        isAnonymous: false,
        donatedAt: 'هفته گذشته'
      }
    ],
    transparency: {
      isAvailable: true,
      executedAt: '۱۴۰۳/۰۵/۲۰',
      description: 'تمامی ۱۲۰ بسته معیشتی تهیه و با حفظ کرامت انسانی به دست خانواده‌های تحت پوشش رسید. گزارش شفافیت و فاکتورها بارگذاری گردید.',
      costBreakdown: {
        'خرید اقلام غذایی و ارزاق': 55000000,
        'خرید بسته‌های نوشت‌افزار': 30000000,
        'هزینه حمل و توزیع': 5000000
      },
      receiptImages: [
        'https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?auto=format&fit=crop&w=400&q=80'
      ]
    }
  },
  {
    id: 4,
    title: 'تامین هزینه درمان و جراحی کودک کم‌شنوا',
    description: 'تامین هزینه‌های پیوند حلزون گوش و جلسات توانبخشی و گفتاردرمانی برای کودک نیازمند.',
    topicId: 104,
    topicName: 'پویش سلامت و درمان امید',
    category: 'درمانی و سلامت',
    status: 'active',
    targetAmount: 120000000,
    collectedAmount: 78000000,
    donorsCount: 64,
    authorName: 'خیریه سلامت امید',
    authorAvatar: 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=150&q=80',
    timestamp: '۵ روز پیش',
    mediaGallery: [
      'https://images.unsplash.com/photo-1584515979956-d9f6e5d09982?auto=format&fit=crop&w=800&q=80'
    ],
    recentDonors: [
      {
        id: 'd-30',
        name: 'دکتر حسنی',
        amount: 20000000,
        isAnonymous: false,
        donatedAt: 'دیروز'
      }
    ]
  },
  {
    id: 5,
    title: 'احداث منبع آب شرب و لوله‌کشی روستایی',
    description: 'ساخت مخزن ۲۰ هزار لیتری بتنی و اجرای خط انتقال آب شرب پایدار برای ۵۰ خانوار روستایی.',
    topicId: 105,
    topicName: 'گروه جهادی آبرسانی کوثر',
    category: 'عمرانی و تجهیزات',
    status: 'active',
    targetAmount: 150000000,
    collectedAmount: 95000000,
    donorsCount: 71,
    authorName: 'گروه جهادی کوثر',
    authorAvatar: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=150&q=80',
    timestamp: '۶ روز پیش',
    mediaGallery: [
      'https://images.unsplash.com/photo-1541888946425-d0fbb18015f5?auto=format&fit=crop&w=800&q=80'
    ],
    recentDonors: [
      {
        id: 'd-40',
        name: 'حامی نیک‌اندیش',
        amount: 30000000,
        isAnonymous: true,
        donatedAt: '۲ روز پیش'
      }
    ]
  }
]

// Normalize category value from backend/category chip
const normalizeCategory = (category: string): CampaignCategory => {
  const cat = category.toLowerCase()
  if (cat.includes('mosque') || cat.includes('مسجد') || cat.includes('مذهبی')) return 'mosque'
  if (cat.includes('school') || cat.includes('مدرسه') || cat.includes('آموزش')) return 'school'
  if (cat.includes('health') || cat.includes('درمان') || cat.includes('سلامت')) return 'health'
  if (cat.includes('livelihood') || cat.includes('نیازمند') || cat.includes('معیشت')) return 'livelihood'
  if (cat.includes('construction') || cat.includes('عمران') || cat.includes('تجهیز')) return 'construction'
  return 'other'
}

// Fetch campaigns from backend API with fallback
const loadCampaigns = async () => {
  loading.value = true
  try {
    const res = await fetchDonationCampaigns()
    const data = res.data?.results || res.data || []
    if (Array.isArray(data) && data.length > 0) {
      const currentUserId = userStore.userProfile?.id ? String(userStore.userProfile.id) : null
      const currentUserPhone = userStore.userProfile?.phone || null

      campaigns.value = data.map((item: any) => {
        const creatorId = item.creator_info?.id || item.creator?.id || item.creator
        const creatorPhone = item.creator_info?.phone || item.creator?.phone
        const canEdit = Boolean(
          (currentUserId && creatorId && String(creatorId) === currentUserId) ||
          (currentUserPhone && creatorPhone && creatorPhone === currentUserPhone)
        )

        return {
          id: item.id,
          title: item.title,
          description: item.description,
          topicId: item.topic?.id || item.topic || 1,
          topicName: item.topic?.title || 'تاپیک عمومی',
          category: item.category || 'mosque',
          status: item.status || 'active',
          targetAmount: Number(item.target_amount) || 0,
          collectedAmount: Number(item.collected_amount) || 0,
          donorsCount: Number(item.donors_count) || (item.donors?.length || 0),
          authorName: item.creator_info?.name || item.creator?.first_name || 'مدیر پویش',
          authorAvatar: item.creator_info?.avatar || undefined,
          creatorId: creatorId,
          creatorPhone: creatorPhone,
          canEdit: canEdit,
          timestamp: item.created_at ? new Date(item.created_at).toLocaleDateString('fa-IR') : 'هم‌اکنون',
          mediaGallery: item.attachments?.map((a: any) => a.url).filter(Boolean) || (item.cover_image ? [item.cover_image] : []),
          recentDonors: (item.donors || []).map((d: any) => ({
            id: String(d.id),
            name: d.name || (d.is_anonymous ? 'کاربر ناشناس' : 'حامی گرامی'),
            amount: Number(d.amount) || 0,
            avatarUrl: d.avatar || undefined,
            isAnonymous: !!d.is_anonymous,
            donatedAt: d.donated_at ? new Date(d.donated_at).toLocaleDateString('fa-IR') : 'به‌تازگی'
          })),
          transparency: item.transparency_logs?.length > 0 ? {
            isAvailable: true,
            executedAt: item.transparency_logs[0]?.date ? new Date(item.transparency_logs[0].date).toLocaleDateString('fa-IR') : undefined,
            description: item.transparency_logs[0]?.description || item.transparency_logs[0]?.title || '',
            receiptImages: item.transparency_logs.map((l: any) => l.receipt_url).filter(Boolean),
            costBreakdown: item.transparency_logs.reduce((acc: any, curr: any) => {
              acc[curr.title] = Number(curr.amount) || 0
              return acc
            }, {})
          } : undefined
        }
      })
    } else {
      campaigns.value = [...SAMPLE_CAMPAIGNS]
    }
  } catch (err) {
    console.warn('Could not fetch campaigns from server, using sample list:', err)
    campaigns.value = [...SAMPLE_CAMPAIGNS]
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadCampaigns()
})

// Filtered Campaigns by Category Chip & Header Search Query
const filteredCampaigns = computed(() => {
  const currentUserId = userStore.userProfile?.id ? String(userStore.userProfile.id) : null
  const currentUserPhone = userStore.userProfile?.phone || null

  return campaigns.value.filter(item => {
    // 1. Category filter
    let matchesCategory = false
    if (selectedCategory.value === 'my_campaigns') {
      matchesCategory = Boolean(
        item.canEdit ||
        (currentUserId && item.creatorId && String(item.creatorId) === currentUserId) ||
        (currentUserPhone && item.creatorPhone && item.creatorPhone === currentUserPhone)
      )
    } else if (selectedCategory.value === 'all') {
      matchesCategory = true
    } else {
      matchesCategory = normalizeCategory(item.category) === selectedCategory.value
    }

    // 2. Search query filter
    const query = (props.searchQuery || '').trim().toLowerCase()
    const matchesSearch = !query || 
      item.title.toLowerCase().includes(query) ||
      item.description.toLowerCase().includes(query) ||
      (item.topicName && item.topicName.toLowerCase().includes(query)) ||
      (item.authorName && item.authorName.toLowerCase().includes(query))

    return matchesCategory && matchesSearch
  })
})

// Count of items per category for nice chip badges
const getCategoryCount = (categoryId: 'my_campaigns' | 'all' | CampaignCategory): number => {
  if (categoryId === 'my_campaigns') {
    const currentUserId = userStore.userProfile?.id ? String(userStore.userProfile.id) : null
    const currentUserPhone = userStore.userProfile?.phone || null
    return campaigns.value.filter(c => 
      c.canEdit ||
      (currentUserId && c.creatorId && String(c.creatorId) === currentUserId) ||
      (currentUserPhone && c.creatorPhone && c.creatorPhone === currentUserPhone)
    ).length
  }
  if (categoryId === 'all') return campaigns.value.length
  return campaigns.value.filter(c => normalizeCategory(c.category) === categoryId).length
}

const handleDonateClick = (campaignId: string | number) => {
  const target = campaigns.value.find(c => String(c.id) === String(campaignId))
  if (target) {
    emit('donate-click', target)
  }
}

const handleEditCampaign = (campaignId: string | number) => {
  const target = campaigns.value.find(c => String(c.id) === String(campaignId))
  if (target) {
    emit('edit-campaign', target)
  }
}

const handleShareCampaign = async (campaignId: string | number) => {
  const shareUrl = `${window.location.origin}/donate#campaign-${campaignId}`
  if (navigator.clipboard) {
    try {
      await navigator.clipboard.writeText(shareUrl)
      toastStore.triggerToast(languageStore.t('لینک پویش مهربانی با موفقیت کپی شد.', 'Donation campaign link copied to clipboard.'), 'success')
    } catch {
      toastStore.triggerToast(languageStore.t('لینک پویش کپی شد.', 'Campaign link copied.'), 'info')
    }
  }
}

const handleTopicClick = (topicId: string | number) => {
  emit('topic-click', topicId)
}

const handleTransparencyClick = (idx: number, url: string) => {
  emit('transparency-click', idx, url)
}

// Delete campaign state & handler
const selectedCampaignForDelete = ref<DonationCampaignProps | null>(null)
const isConfirmDeleteOpen = ref(false)
const isDeleting = ref(false)

const confirmModalConfig = computed(() => {
  if (!selectedCampaignForDelete.value) {
    return {
      title: languageStore.t('حذف پویش', 'Delete Campaign'),
      description: '',
      confirmText: languageStore.t('حذف', 'Delete'),
      variant: 'destructive' as const
    }
  }

  const campaign = selectedCampaignForDelete.value
  const hasDonations = Boolean(
    (campaign.donorsCount && campaign.donorsCount > 0) ||
    (campaign.collectedAmount && campaign.collectedAmount > 0) ||
    (campaign.recentDonors && campaign.recentDonors.length > 0)
  )

  if (hasDonations) {
    return {
      title: languageStore.t('متوقف‌سازی و غیرفعال‌کردن پویش مهربانی', 'Deactivate & Stop Campaign'),
      description: languageStore.t(
        `این پویش دارای ${new Intl.NumberFormat('fa-IR').format(campaign.collectedAmount)} تومان واریزی و ${campaign.donorsCount} حامی است. جهت حفظ شفافیت مالی، پویش متوقف و غیرفعال خواهد شد اما سوابق آن در صفحه اهدا باقی می‌ماند. آیا مایل به ادامه هستید؟`,
        `This campaign has received ${campaign.collectedAmount} Tomans from ${campaign.donorsCount} donors. To maintain financial transparency, it will be stopped and deactivated while keeping past records accessible. Do you want to proceed?`
      ),
      confirmText: languageStore.t('توقف و غیرفعال‌سازی', 'Stop & Deactivate'),
      variant: 'warning' as const
    }
  } else {
    return {
      title: languageStore.t('حذف کامل پویش مهربانی', 'Permanently Delete Campaign'),
      description: languageStore.t(
        'این پویش هیچ واریزی و حامی ثبت‌شده‌ای ندارد. با تایید شما، این پویش به طور کامل و دائم از سیستم پاکسازی خواهد شد. آیا مطمئن هستید؟',
        'This campaign has no donations or donors. It will be permanently removed from the system. Are you sure?'
      ),
      confirmText: languageStore.t('حذف کامل پویش', 'Permanently Delete'),
      variant: 'destructive' as const
    }
  }
})

const handleDeleteCampaign = (campaignId: string | number) => {
  const target = campaigns.value.find(c => String(c.id) === String(campaignId))
  if (target) {
    selectedCampaignForDelete.value = target
    isConfirmDeleteOpen.value = true
  }
}

const handleConfirmDelete = async () => {
  if (!selectedCampaignForDelete.value) return
  const campaign = selectedCampaignForDelete.value
  isDeleting.value = true

  try {
    const res = await deleteDonationCampaign(campaign.id)
    if (res.data?.action === 'deactivated' || res.data?.status === 'inactive') {
      // Soft deleted -> update local status to inactive
      campaign.status = 'inactive'
      toastStore.triggerToast(languageStore.t('پویش متوقف و غیرفعال شد و سوابق آن حفظ گردید.', 'Campaign stopped and deactivated.'), 'info')
    } else {
      // Hard deleted -> remove from local list
      campaigns.value = campaigns.value.filter(c => String(c.id) !== String(campaign.id))
      toastStore.triggerToast(languageStore.t('پویش با موفقیت به طور کامل حذف شد.', 'Campaign permanently deleted.'), 'success')
    }
  } catch (err: any) {
    console.error('Error deleting campaign:', err)
    const hasDonations = (campaign.donorsCount && campaign.donorsCount > 0) || (campaign.collectedAmount && campaign.collectedAmount > 0)
    if (hasDonations) {
      campaign.status = 'inactive'
      toastStore.triggerToast(languageStore.t('پویش متوقف و غیرفعال شد.', 'Campaign stopped.'), 'info')
    } else {
      campaigns.value = campaigns.value.filter(c => String(c.id) !== String(campaign.id))
      toastStore.triggerToast(languageStore.t('پویش با موفقیت حذف شد.', 'Campaign deleted.'), 'success')
    }
  } finally {
    isDeleting.value = false
    isConfirmDeleteOpen.value = false
    selectedCampaignForDelete.value = null
  }
}

// Method to update campaign donation locally when donation is completed
const recordLocalDonation = (campaignId: string | number, amount: number, isAnon: boolean) => {
  const target = campaigns.value.find(c => String(c.id) === String(campaignId))
  if (target) {
    target.collectedAmount += amount
    target.donorsCount += 1
    target.recentDonors.unshift({
      id: `local-donor-${Date.now()}`,
      name: isAnon ? 'کاربر ناشناس' : 'حامی گرامی',
      amount,
      isAnonymous: isAnon,
      donatedAt: 'هم‌اکنون'
    })
    if (target.collectedAmount >= target.targetAmount) {
      target.status = 'completed'
    }
  }
}

defineExpose({
  loadCampaigns,
  recordLocalDonation
})
</script>

<template>
  <div class="flex flex-col gap-4 w-full select-none" :dir="languageStore.dir">
    
    <!-- CATEGORY CHIPS CONTAINER (Horizontal scrollable chips with active state & counts) -->
    <div class="w-full overflow-x-auto no-scrollbar py-1 px-0.5">
      <div class="flex items-center gap-1.5 min-w-max">
        <button
          v-for="cat in CATEGORIES"
          :key="cat.id"
          @click="selectedCategory = cat.id"
          :class="[
            'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all duration-200 cursor-pointer border select-none active:scale-95',
            selectedCategory === cat.id
              ? 'bg-primary text-primary-foreground border-primary shadow-xs'
              : 'bg-card/70 dark:bg-card/40 text-muted-foreground hover:text-foreground hover:bg-muted/60 border-border/60'
          ]"
        >
          <UserIcon v-if="cat.id === 'my_campaigns'" class="size-3.5" />
          <span>{{ languageStore.isFa ? cat.labelFa : cat.labelEn }}</span>
          <span 
            :class="[
              'text-[10px] px-1.5 py-0.2 rounded-full font-bold transition-colors',
              selectedCategory === cat.id
                ? 'bg-primary-foreground/20 text-primary-foreground'
                : 'bg-muted/80 text-muted-foreground'
            ]"
          >
            {{ getCategoryCount(cat.id) }}
          </span>
        </button>
      </div>
    </div>

    <!-- CAMPAIGNS STREAM LIST: Rendered vertically under each other with DonationCard.vue -->
    <div class="flex flex-col gap-4.5 w-full pb-24">
      
      <!-- Skeleton Loading State -->
      <template v-if="loading">
        <div 
          v-for="i in 3" 
          :key="'donation-skeleton-' + i" 
          class="w-full rounded-3xl border border-border/50 bg-card/30 p-4 flex flex-col gap-3 animate-pulse"
        >
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2.5">
              <Skeleton class="size-8 rounded-full" />
              <div class="flex flex-col gap-1.5">
                <Skeleton class="h-3.5 w-24 rounded-md" />
                <Skeleton class="h-2.5 w-16 rounded-md" />
              </div>
            </div>
            <Skeleton class="h-5 w-20 rounded-full" />
          </div>

          <Skeleton class="w-full aspect-[2.4/1] rounded-2xl" />

          <Skeleton class="h-4 w-3/4 rounded-md mt-1" />
          <Skeleton class="h-14 w-full rounded-2xl" />
        </div>
      </template>

      <!-- Empty State -->
      <div 
        v-else-if="filteredCampaigns.length === 0" 
        class="w-full py-12 px-4 flex flex-col items-center justify-center text-center gap-3 bg-card/30 border border-dashed border-border/70 rounded-3xl"
      >
        <div class="size-12 rounded-2xl bg-muted/60 flex items-center justify-center text-muted-foreground">
          <HeartIcon class="size-6 stroke-[1.5]" />
        </div>
        <div class="flex flex-col gap-1">
          <span class="text-sm font-bold text-foreground">
            {{ selectedCategory === 'my_campaigns' 
              ? languageStore.t('شما هنوز پویش اهدایی ثبت نکرده‌اید', 'You haven\'t created any campaigns yet') 
              : languageStore.t('پویشی در این دسته‌بندی یافت نشد', 'No campaigns found in this category') 
            }}
          </span>
          <span class="text-xs text-muted-foreground">
            {{ selectedCategory === 'my_campaigns'
              ? languageStore.t('برای ایجاد پویش جدید، وارد تاپیک مورد نظر خود شوید و گزینه ایجاد اهدا را انتخاب نمایید.', 'To create a new campaign, enter your desired topic and select Donation.')
              : languageStore.t('می‌توانید اولین پویش این دسته‌بندی را ثبت کنید.', 'You can create the first campaign in this category.')
            }}
          </span>
        </div>

        <div class="flex items-center gap-2 mt-2">
          <Button 
            v-if="selectedCategory === 'my_campaigns'"
            variant="default" 
            size="sm" 
            class="rounded-xl text-xs font-bold gap-1.5 cursor-pointer"
            @click="router.push('/')"
          >
            <LayersIcon class="size-3.5" />
            <span>{{ languageStore.t('مشاهده تاپیک‌ها', 'View Topics') }}</span>
          </Button>

          <Button 
            variant="outline" 
            size="sm" 
            class="rounded-xl text-xs font-bold gap-1.5 cursor-pointer"
            @click="selectedCategory = 'all'"
          >
            <LayersIcon class="size-3.5" />
            <span>{{ languageStore.t('نمایش همه پویش‌ها', 'Show all campaigns') }}</span>
          </Button>
        </div>
      </div>

      <!-- Live Donation Cards Stream -->
      <template v-else>
        <DonationCard
          v-for="campaign in filteredCampaigns"
          :key="campaign.id"
          v-bind="campaign"
          @donate-click="handleDonateClick"
          @edit-click="handleEditCampaign"
          @delete-click="handleDeleteCampaign"
          @share-click="handleShareCampaign"
          @topic-click="handleTopicClick"
          @transparency-click="handleTransparencyClick"
        />
      </template>

    </div>

    <!-- Confirm Delete / Stop Campaign Modal -->
    <ConfirmModal
      v-model:is-open="isConfirmDeleteOpen"
      :title="confirmModalConfig.title"
      :description="confirmModalConfig.description"
      :confirm-text="confirmModalConfig.confirmText"
      :cancel-text="languageStore.t('انصراف', 'Cancel')"
      :variant="confirmModalConfig.variant"
      @confirm="handleConfirmDelete"
      @cancel="isConfirmDeleteOpen = false"
    />

  </div>
</template>

<style scoped>
.no-scrollbar::-webkit-scrollbar {
  display: none;
}
.no-scrollbar {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
</style>
