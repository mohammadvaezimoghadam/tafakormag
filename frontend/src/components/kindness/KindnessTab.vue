<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import DonationCard from '@/components/kindness/DonationCard.vue'
import DonationModal from '@/components/kindness/DonationModal.vue'
import type { DonationCampaignProps, CampaignStatus } from '@/types/kindness'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { 
  HeartIcon, 
  SearchIcon, 
  FilterIcon, 
  SparklesIcon, 
  PlusCircleIcon,
  CheckCircle2Icon
} from '@lucide/vue'

const router = useRouter()

// Modal State
const isModalOpen = ref(false)
const selectedCampaign = ref<DonationCampaignProps | null>(null)

// Filter & Search States
const activeFilter = ref<'all' | CampaignStatus>('all')
const searchQuery = ref('')

// Sample Global Kindness Campaigns Data
const campaigns = ref<DonationCampaignProps[]>([
  {
    id: 'k-1',
    title: 'تجهیز و شاداب‌سازی کلاس درس مدرسه ابتدایی در روستای محروم',
    description: 'این پویش جهت خرید ۲۰ عدد میز و نیمکت استاندارد، یک عدد تخته هوشمند و رنگ‌آمیزی کامل ۲ کلاس درس در منطقه محروم راه‌اندازی شده است.',
    topicId: 101,
    topicName: 'مدرسه شهید بهشتی - کانون جهادی',
    category: 'مدرسه و آموزش',
    status: 'active',
    targetAmount: 100000000,
    collectedAmount: 65000000,
    donorsCount: 42,
    mediaGallery: [
      'https://images.unsplash.com/photo-1509062522246-3755977927d7?auto=format&fit=crop&w=800&q=80',
      'https://images.unsplash.com/photo-1580582932707-520aed937b7b?auto=format&fit=crop&w=800&q=80'
    ],
    recentDonors: [
      {
        id: 'd-1',
        name: 'رضا محمدی',
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
        donatedAt: '۱ ساعت پیش'
      }
    ]
  },
  {
    id: 'k-2',
    title: 'تامین سیستم گرمایشی و سرمایشی مسجد و حسینیه حضرت ولیعصر (عج)',
    description: 'خرید و نصب دستگاه‌های سرمایش و گرمایش جهت راحتی نمازگزاران و کانون‌های قرآنی مسجد.',
    topicId: 102,
    topicName: 'مسجد حضرت ولیعصر (عج)',
    category: 'مسجد و حسینیه',
    status: 'completed',
    targetAmount: 60000000,
    collectedAmount: 60000000,
    donorsCount: 64,
    mediaGallery: [
      'https://images.unsplash.com/photo-1548625149-fc4a29cf7092?auto=format&fit=crop&w=800&q=80'
    ],
    recentDonors: [
      {
        id: 'd-10',
        name: 'امیرحسین رضایی',
        amount: 15000000,
        isAnonymous: false,
        donatedAt: '۲ روز پیش'
      }
    ]
  },
  {
    id: 'k-3',
    title: 'تهیه و توزیع ۱۰۰ بسته معیشتی و نوشت‌افزار برای خانواده‌های نیازمند',
    description: 'پویش تامین بسته‌های غذایی و کیف و لوازم‌التحریر کامل برای کودکان نیازمند محله.',
    topicId: 103,
    topicName: 'خیریه بقیه‌الله',
    category: 'امور خیریه و معیشت',
    status: 'executed',
    targetAmount: 80000000,
    collectedAmount: 80000000,
    donorsCount: 95,
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
      executedAt: '۱۴۰۳/۰۵/۱۵',
      description: 'پویش با موفقیت ۱۰۰٪ به پایان رسید و تمام ۱۰۰ بسته معیشتی و کیف و دفترها تهیه شده و به دست خانواده‌های هدف رسید.',
      costBreakdown: {
        'خرید ۱۰۰ بسته لوازم‌التحریر و کیف': 42000000,
        'خرید اقلام غذایی (برنج، روغن، حبوبات)': 35000000,
        'هزینه حمل و بسته‌بندی': 3000000
      },
      receiptImages: [
        'https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?auto=format&fit=crop&w=400&q=80'
      ]
    }
  }
])

// Computed Filtered List
const filteredCampaigns = computed(() => {
  return campaigns.value.filter(item => {
    const matchesFilter = activeFilter.value === 'all' || item.status === activeFilter.value
    const query = searchQuery.value.trim().toLowerCase()
    const matchesSearch = !query || 
      item.title.toLowerCase().includes(query) || 
      item.category.toLowerCase().includes(query) ||
      item.topicName.toLowerCase().includes(query)
    return matchesFilter && matchesSearch
  })
})

// Event Handlers
const handleDonateClick = (id: string | number) => {
  const target = campaigns.value.find(c => c.id === id)
  if (target) {
    selectedCampaign.value = target
    isModalOpen.value = true
  }
}

const handleTopicClick = (topicId: string | number) => {
  router.push(`/topic/${topicId}`)
}

const handleTransparencyClick = (idx: number, url: string) => {
  window.open(url, '_blank')
}

const handleDonationSubmit = (amount: number, isAnon: boolean) => {
  if (selectedCampaign.value) {
    selectedCampaign.value.collectedAmount += amount
    selectedCampaign.value.donorsCount++
    selectedCampaign.value.recentDonors.unshift({
      id: `donor-${Date.now()}`,
      name: isAnon ? 'کاربر ناشناس' : 'حامی گرامی',
      amount,
      isAnonymous: isAnon,
      donatedAt: 'هم‌اکنون'
    })
    if (selectedCampaign.value.collectedAmount >= selectedCampaign.value.targetAmount) {
      selectedCampaign.value.status = 'completed'
    }
  }
}
</script>

<template>
  <div class="space-y-6 dir-rtl text-right">
    <!-- Header Banner -->
    <div class="rounded-xl bg-gradient-to-r from-primary/10 via-accent/20 to-primary/5 p-6 border border-border/60 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
      <div class="space-y-1">
        <h2 class="text-xl font-bold text-foreground flex items-center gap-2">
          <HeartIcon class="size-6 text-primary fill-primary/20" />
          <span>تب مهربانی و پویش‌های مردمی</span>
        </h2>
        <p class="text-xs text-muted-foreground leading-relaxed max-w-xl">
          شفاف‌ترین بستر کمک‌رسانی به مساجد، مدارس و طرح‌های جهادی محلی. تمام تراکنش‌ها و هزینه‌کردها با گزارش شفافیت مالی قابل پیگیری است.
        </p>
      </div>

      <Button class="gap-2 font-semibold shadow-sm shrink-0">
        <PlusCircleIcon class="size-4" />
        <span>ثبت پویش جدید</span>
      </Button>
    </div>

    <!-- Filters & Search Controls -->
    <div class="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
      <!-- Status Filter Tabs -->
      <div class="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0">
        <Button
          size="sm"
          :variant="activeFilter === 'all' ? 'default' : 'outline'"
          class="text-xs rounded-full font-medium"
          @click="activeFilter = 'all'"
        >
          همه پویش‌ها
        </Button>
        <Button
          size="sm"
          :variant="activeFilter === 'active' ? 'default' : 'outline'"
          class="text-xs rounded-full font-medium"
          @click="activeFilter = 'active'"
        >
          در حال جمع‌آوری
        </Button>
        <Button
          size="sm"
          :variant="activeFilter === 'completed' ? 'default' : 'outline'"
          class="text-xs rounded-full font-medium"
          @click="activeFilter = 'completed'"
        >
          تکمیل شده
        </Button>
        <Button
          size="sm"
          :variant="activeFilter === 'executed' ? 'default' : 'outline'"
          class="text-xs rounded-full font-medium"
          @click="activeFilter = 'executed'"
        >
          اجرا شده و شفاف
        </Button>
      </div>

      <!-- Search Input -->
      <div class="relative min-w-[220px]">
        <SearchIcon class="absolute right-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
        <Input 
          v-model="searchQuery"
          placeholder="جستجوی پویش یا موضوع..." 
          class="pr-9 text-xs"
        />
      </div>
    </div>

    <!-- Campaigns Grid -->
    <div v-if="filteredCampaigns.length > 0" class="grid grid-cols-1 md:grid-cols-2 gap-6 items-start">
      <DonationCard
        v-for="campaign in filteredCampaigns"
        :key="campaign.id"
        v-bind="campaign"
        @donate-click="handleDonateClick"
        @topic-click="handleTopicClick"
        @transparency-click="handleTransparencyClick"
      />
    </div>

    <!-- Empty Filter State -->
    <div v-else class="py-12 text-center text-muted-foreground space-y-3 bg-muted/20 rounded-xl border border-dashed border-border">
      <HeartIcon class="size-10 mx-auto text-muted-foreground/50 stroke-[1.5]" />
      <div class="text-sm font-medium">پویشی با این مشخصات یافت نشد.</div>
      <Button variant="outline" size="sm" @click="activeFilter = 'all'; searchQuery = ''">
        نمایش همه پویش‌ها
      </Button>
    </div>

    <!-- Donation Modal -->
    <DonationModal
      v-model:open="isModalOpen"
      :campaign-title="selectedCampaign?.title"
      @submit-donation="handleDonationSubmit"
    />
  </div>
</template>
