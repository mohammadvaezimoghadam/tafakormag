<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import DonationCard from '@/components/kindness/DonationCard.vue'
import DonationModal from '@/components/kindness/DonationModal.vue'
import type { DonationCampaignProps, CampaignStatus } from '@/types/kindness'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { SunIcon, MoonIcon, PlayIcon, CheckCircleIcon, HeartHandshakeIcon, Trash2Icon } from '@lucide/vue'

// Dark mode state
const isDarkMode = ref(false)
const toggleDarkMode = () => {
  isDarkMode.value = !isDarkMode.value
  if (isDarkMode.value) {
    document.documentElement.classList.add('dark')
  } else {
    document.documentElement.classList.remove('dark')
  }
}

// Modal State
const isModalOpen = ref(false)

// Active Preset State (A, B, C, D)
const selectedState = ref<'stateA' | 'stateB' | 'stateC' | 'stateD'>('stateA')

// Mock Campaigns Preset Data
const mockStateA: DonationCampaignProps = {
  id: 'cmp-101',
  title: 'تجهیز و شاداب‌سازی کلاس درس مدرسه ابتدایی در روستای محروم',
  description: 'این پویش جهت خرید ۲۰ عدد میز و نیمکت استاندارد، یک عدد تخته هوشمند و رنگ‌آمیزی کامل ۲ کلاس درس در منطقه محروم راه‌اندازی شده است تا دانش‌آموزان عزیز در محیطی شاداب به تحصیل بپردازند.',
  topicId: 'topic-mosque-12',
  topicName: 'مدرسه شهید بهشتی - کانون جهادی',
  category: 'مدرسه و آموزش',
  status: 'active',
  targetAmount: 100000000,
  collectedAmount: 45000000,
  donorsCount: 28,
  canEdit: true,
  mediaGallery: [
    'https://images.unsplash.com/photo-1509062522246-3755977927d7?auto=format&fit=crop&w=800&q=80',
    'https://images.unsplash.com/photo-1580582932707-520aed937b7b?auto=format&fit=crop&w=800&q=80',
    'https://images.unsplash.com/photo-1497633762265-9d179a990aa6?auto=format&fit=crop&w=800&q=80',
    'https://images.unsplash.com/photo-1577896851231-70ef18881754?auto=format&fit=crop&w=800&q=80',
    'https://images.unsplash.com/photo-1503676260728-1c00da094a0b?auto=format&fit=crop&w=800&q=80'
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
    },
    {
      id: 'd-3',
      name: 'سارا احمدی',
      amount: 2500000,
      avatarUrl: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=150&q=80',
      isAnonymous: false,
      donatedAt: 'دیروز'
    }
  ]
}

const mockStateB: DonationCampaignProps = {
  id: 'cmp-102',
  title: 'تجهیز سیستم گرمایشی و سرمایشی مسجد و حسینیه حضرت ولیعصر (عج)',
  description: 'خرید و نصب ۲ دستگاه کولر گازی و تعمیر موتورخانه جهت استفاده نمازگزاران و مراکزی که جلسات قرآنی در آن برگزار می‌شود.',
  topicId: 'topic-mosque-99',
  topicName: 'مسجد حضرت ولیعصر (عج)',
  category: 'مسجد و حسینیه',
  status: 'completed',
  targetAmount: 60000000,
  collectedAmount: 60000000,
  donorsCount: 64,
  canEdit: true,
  mediaGallery: [
    'https://images.unsplash.com/photo-1548625149-fc4a29cf7092?auto=format&fit=crop&w=800&q=80',
    'https://images.unsplash.com/photo-1564769625905-50e93615e769?auto=format&fit=crop&w=800&q=80',
    'https://images.unsplash.com/photo-1519817650390-64a93db51149?auto=format&fit=crop&w=800&q=80',
    'https://images.unsplash.com/photo-1584551246679-0daf3d275d0f?auto=format&fit=crop&w=800&q=80',
    'https://images.unsplash.com/photo-1609599006353-e629aaabfeae?auto=format&fit=crop&w=800&q=80'
  ],
  recentDonors: [
    {
      id: 'd-10',
      name: 'امیرحسین رضایی',
      amount: 15000000,
      isAnonymous: false,
      donatedAt: '۲ روز پیش'
    },
    {
      id: 'd-11',
      name: 'کاربر ناشناس',
      amount: 5000000,
      isAnonymous: true,
      donatedAt: '۳ روز پیش'
    }
  ]
}

const mockStateC: DonationCampaignProps = {
  id: 'cmp-103',
  title: 'تهیه و توزیع ۱۰۰ بسته معیشتی و نوشت‌افزار برای خانواده‌های نیازمند',
  description: 'پویش تامین بسته‌های غذایی و کیف و لوازم‌التحریر کامل برای کودکان نیازمند محله در آستانه شروع سال تحصیلی جدید.',
  topicId: 'topic-charity-4',
  topicName: 'خیریه بقیه‌الله',
  category: 'امور خیریه و معیشت',
  status: 'executed',
  targetAmount: 80000000,
  collectedAmount: 80000000,
  donorsCount: 95,
  canEdit: true,
  mediaGallery: [
    'https://images.unsplash.com/photo-1488521787991-ed7bbaae773c?auto=format&fit=crop&w=800&q=80',
    'https://images.unsplash.com/photo-1593113598332-cd288d649433?auto=format&fit=crop&w=800&q=80',
    'https://images.unsplash.com/photo-1532629345422-7515f3d16bb6?auto=format&fit=crop&w=800&q=80',
    'https://images.unsplash.com/photo-1542810634-71277d95dcbb?auto=format&fit=crop&w=800&q=80',
    'https://images.unsplash.com/photo-1469571486292-0ba58a3f068b?auto=format&fit=crop&w=800&q=80'
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
    description: 'پویش با موفقیت ۱۰۰٪ به پایان رسید و تمام ۱۰۰ بسته معیشتی و کیف و دفترها تهیه شده و به دست خانواده‌های هدف رسید. فاکتورهای رسمی خرید و تصاویر اقلام در ادامه ضمیمه شده است.',
    costBreakdown: {
      'خرید ۱۰۰ بسته لوازم‌التحریر و کیف': 42000000,
      'خرید اقلام غذایی (برنج، روغن، حبوبات)': 35000000,
      'هزینه حمل و بسته‌بندی': 3000000
    },
    receiptImages: [
      'https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?auto=format&fit=crop&w=400&q=80',
      'https://images.unsplash.com/photo-1450133064473-71024230f91b?auto=format&fit=crop&w=400&q=80'
    ]
  }
}

const mockStateD: DonationCampaignProps = {
  id: 'cmp-104',
  title: 'پویش جدید ایجاد شده (بدون واریزی - تست دکمه پاکسازی)',
  description: 'این پویش به تازگی ایجاد شده و هنوز هیچ حامی یا مبلغی برای آن ثبت نشده است. بنابراین دکمه پاکسازی (حذف) در پایین کارت فعال بوده و قابل تست است.',
  topicId: 'topic-mosque-55',
  topicName: 'کانون فرهنگی نور',
  category: 'عمرانی و تجهیزات',
  status: 'active',
  targetAmount: 50000000,
  collectedAmount: 0,
  donorsCount: 0,
  canEdit: true,
  mediaGallery: [
    'https://images.unsplash.com/photo-1541888946425-d0fbb18086f6?auto=format&fit=crop&w=800&q=80',
    'https://images.unsplash.com/photo-1503387762-592deb58ef4e?auto=format&fit=crop&w=800&q=80'
  ],
  recentDonors: []
}

// Current Campaign Model (Reactive)
const currentCampaign = reactive<DonationCampaignProps>({ ...mockStateA })

const loadPreset = (state: 'stateA' | 'stateB' | 'stateC' | 'stateD') => {
  selectedState.value = state
  let preset: DonationCampaignProps
  if (state === 'stateA') preset = mockStateA
  else if (state === 'stateB') preset = mockStateB
  else if (state === 'stateC') preset = mockStateC
  else preset = mockStateD

  Object.assign(currentCampaign, JSON.parse(JSON.stringify(preset)))
}

// Event Log for Testing Verification
interface EventLog {
  id: number
  time: string
  name: string
  payload: string
}
const logs = ref<EventLog[]>([])
let logId = 0

const addLog = (name: string, payload: any) => {
  logId++
  const time = new Date().toLocaleTimeString('fa-IR')
  logs.value.unshift({
    id: logId,
    time,
    name,
    payload: JSON.stringify(payload)
  })
}

const clearLogs = () => {
  logs.value = []
}

// Event Handlers
const handleDonateClick = (campaignId: string | number) => {
  addLog('donate-click', { campaignId })
  isModalOpen.value = true
}

const handleTopicClick = (topicId: string | number) => {
  addLog('topic-click', { topicId })
}

const handleTransparencyClick = (index: number, url: string) => {
  addLog('transparency-click', { index, url })
}

const handleShareClick = (campaignId: string | number) => {
  addLog('share-click', { campaignId })
}

const handleEditClick = (campaignId: string | number) => {
  addLog('edit-click', { campaignId })
  alert(`رویداد ویرایش پویش (edit-click) برای شناسه ${campaignId} شلیک شد.`)
}

const handleDeleteClick = (campaignId: string | number) => {
  addLog('delete-click', { campaignId })
  if (confirm(`آیا از پاکسازی و حذف پویش «${currentCampaign.title}» اطمینان دارید؟`)) {
    addLog('delete-confirmed', { campaignId })
    alert(`پویش با شناسه ${campaignId} با موفقیت پاکسازی شد.`)
  }
}

const handleDonationSubmit = (amount: number, isAnon: boolean) => {
  addLog('submit-donation', { amount, isAnon })
  currentCampaign.collectedAmount += amount
  currentCampaign.donorsCount++
  currentCampaign.recentDonors.unshift({
    id: `d-new-${Date.now()}`,
    name: isAnon ? 'کاربر ناشناس' : 'حامی جدید',
    amount,
    isAnonymous: isAnon,
    donatedAt: 'هم‌اکنون'
  })
  if (currentCampaign.collectedAmount >= currentCampaign.targetAmount) {
    currentCampaign.status = 'completed'
  }
}
</script>

<template>
  <div class="min-h-screen bg-background text-foreground p-4 sm:p-8 dir-rtl text-right font-sans transition-colors duration-300">
    <div class="max-w-6xl mx-auto space-y-8">
      
      <!-- Top Bar / Playground Header -->
      <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-border pb-6">
        <div>
          <h1 class="text-2xl font-bold flex items-center gap-2 text-foreground">
            <HeartHandshakeIcon class="size-6 text-primary" />
            <span>محیط تست کارت مهربانی (DonationCard Playground)</span>
          </h1>
          <p class="text-xs text-muted-foreground mt-1">
            ارزیابی دقیق حالات سه‌گانه پویش، تم‌های تاریک/روشن، RTL و انتشار رویدادها
          </p>
        </div>

        <div class="flex items-center gap-3">
          <!-- Theme Switcher Button -->
          <Button 
            variant="outline" 
            size="sm" 
            class="gap-2 font-medium"
            @click="toggleDarkMode"
          >
            <MoonIcon v-if="!isDarkMode" class="size-4 text-primary" />
            <SunIcon v-else class="size-4 text-amber-400" />
            <span>{{ isDarkMode ? 'حالت روشن' : 'حالت تاریک' }}</span>
          </Button>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        
        <!-- Controls & State Switcher Panel (5 cols) -->
        <div class="lg:col-span-5 space-y-6">
          
          <!-- State Presets Switcher -->
          <Card class="border-border bg-card">
            <CardHeader class="p-4 pb-2">
              <CardTitle class="text-sm font-bold text-foreground">انتخاب حالت پیش‌فرض پویش</CardTitle>
            </CardHeader>
            <CardContent class="p-4 pt-2 space-y-3">
              <div class="grid grid-cols-1 gap-2">
                <Button
                  variant="outline"
                  class="justify-between h-auto py-3 px-4 text-right"
                  :class="selectedState === 'stateA' ? 'border-primary bg-primary/10 font-bold' : ''"
                  @click="loadPreset('stateA')"
                >
                  <div class="flex flex-col items-start gap-0.5">
                    <span class="text-xs font-bold text-foreground">State A: پویش در حال جمع‌آوری</span>
                    <span class="text-[11px] text-muted-foreground">امکان مشارکت، درصد پیشرفت جزئی</span>
                  </div>
                  <Badge variant="default" class="text-[10px]">فعال</Badge>
                </Button>

                <Button
                  variant="outline"
                  class="justify-between h-auto py-3 px-4 text-right"
                  :class="selectedState === 'stateB' ? 'border-primary bg-primary/10 font-bold' : ''"
                  @click="loadPreset('stateB')"
                >
                  <div class="flex flex-col items-start gap-0.5">
                    <span class="text-xs font-bold text-foreground">State B: پویش تکمیل شده</span>
                    <span class="text-[11px] text-muted-foreground">پیشرفت ۱۰۰٪، دکمه غیرفعال</span>
                  </div>
                  <Badge variant="secondary" class="text-[10px]">تکمیل</Badge>
                </Button>

                <Button
                  variant="outline"
                  class="justify-between h-auto py-3 px-4 text-right"
                  :class="selectedState === 'stateC' ? 'border-primary bg-primary/10 font-bold' : ''"
                  @click="loadPreset('stateC')"
                >
                  <div class="flex flex-col items-start gap-0.5">
                    <span class="text-xs font-bold text-foreground">State C: اجرا شده و شفاف</span>
                    <span class="text-[11px] text-muted-foreground">تب شفافیت فعال + ریز هزینه‌ها</span>
                  </div>
                  <Badge variant="outline" class="text-[10px]">اجرا شده</Badge>
                </Button>

                <Button
                  variant="outline"
                  class="justify-between h-auto py-3 px-4 text-right"
                  :class="selectedState === 'stateD' ? 'border-emerald-500 bg-emerald-500/10 font-bold' : ''"
                  @click="loadPreset('stateD')"
                >
                  <div class="flex flex-col items-start gap-0.5">
                    <span class="text-xs font-bold text-foreground">State D: پویش بدون واریزی (تست حذف)</span>
                    <span class="text-[11px] text-muted-foreground">مبلغ ۰ تومان، دکمه سطل زباله فعال</span>
                  </div>
                  <Badge variant="secondary" class="text-[10px] text-emerald-600 dark:text-emerald-400 border border-emerald-500/30">حذف فعال</Badge>
                </Button>
              </div>
            </CardContent>
          </Card>

          <!-- Interactive Property Controls -->
          <Card class="border-border bg-card">
            <CardHeader class="p-4 pb-2">
              <CardTitle class="text-sm font-bold text-foreground">تنظیمات زنده پارامترها</CardTitle>
            </CardHeader>
            <CardContent class="p-4 pt-2 space-y-4 text-xs">
              <div class="flex items-center justify-between p-2 rounded-xl bg-muted/30 border border-border/40">
                <div class="flex flex-col">
                  <span class="font-bold text-foreground">دسترسی مدیریت / سازنده (canEdit):</span>
                  <span class="text-[10px] text-muted-foreground">نمایش دکمه‌های ویرایش و حذف در پایین کارت</span>
                </div>
                <Button 
                  size="sm" 
                  :variant="currentCampaign.canEdit ? 'default' : 'outline'" 
                  class="h-7 text-xs font-semibold rounded-lg cursor-pointer"
                  @click="currentCampaign.canEdit = !currentCampaign.canEdit"
                >
                  {{ currentCampaign.canEdit ? 'فعال (مالک)' : 'غیرفعال (عادی)' }}
                </Button>
              </div>

              <div class="space-y-1">
                <label class="font-semibold text-muted-foreground">وضعیت پویش (Status):</label>
                <div class="flex gap-2">
                  <Button 
                    size="sm" 
                    variant="outline"
                    :class="currentCampaign.status === 'active' ? 'bg-primary text-primary-foreground' : ''"
                    @click="currentCampaign.status = 'active'"
                  >Active</Button>
                  <Button 
                    size="sm" 
                    variant="outline"
                    :class="currentCampaign.status === 'completed' ? 'bg-primary text-primary-foreground' : ''"
                    @click="currentCampaign.status = 'completed'"
                  >Completed</Button>
                  <Button 
                    size="sm" 
                    variant="outline"
                    :class="currentCampaign.status === 'executed' ? 'bg-primary text-primary-foreground' : ''"
                    @click="currentCampaign.status = 'executed'"
                  >Executed</Button>
                </div>
              </div>

              <div class="space-y-1">
                <label class="font-semibold text-muted-foreground">تعداد حامیان (Donors Count):</label>
                <input 
                  type="number" 
                  v-model.number="currentCampaign.donorsCount"
                  class="w-full p-2 rounded-md border border-border bg-background text-foreground text-start placeholder:text-start"
                />
              </div>

              <div class="space-y-1">
                <label class="font-semibold text-muted-foreground">مبلغ جمع‌آوری شده (تومان):</label>
                <input 
                  type="number" 
                  v-model.number="currentCampaign.collectedAmount"
                  class="w-full p-2 rounded-md border border-border bg-background text-foreground text-start placeholder:text-start"
                />
              </div>

              <div class="space-y-1">
                <label class="font-semibold text-muted-foreground">مبلغ هدف (تومان):</label>
                <input 
                  type="number" 
                  v-model.number="currentCampaign.targetAmount"
                  class="w-full p-2 rounded-md border border-border bg-background text-foreground text-start placeholder:text-start"
                />
              </div>
            </CardContent>
          </Card>

          <!-- Event Log Monitor -->
          <Card class="border-border bg-card">
            <CardHeader class="p-4 pb-2 flex flex-row items-center justify-between">
              <CardTitle class="text-sm font-bold text-foreground">لاگ رویدادها (Event Log)</CardTitle>
              <Button size="sm" variant="ghost" class="h-7 px-2 text-xs" @click="clearLogs">
                <Trash2Icon class="size-3.5 text-muted-foreground" />
              </Button>
            </CardHeader>
            <CardContent class="p-4 pt-2">
              <div v-if="logs.length > 0" class="max-h-40 overflow-y-auto space-y-1.5 font-mono text-[11px]">
                <div 
                  v-for="log in logs" 
                  :key="log.id" 
                  class="p-2 rounded bg-muted/50 border border-border/50 flex flex-col gap-0.5"
                >
                  <div class="flex items-center justify-between text-primary font-semibold">
                    <span>@{{ log.name }}</span>
                    <span class="text-muted-foreground text-[10px]">{{ log.time }}</span>
                  </div>
                  <div class="text-muted-foreground truncate">{{ log.payload }}</div>
                </div>
              </div>
              <div v-else class="py-6 text-center text-muted-foreground text-xs">
                هنوز هیچ رویدادی شلیک نشده است. روی دکمه‌ها یا عنوان‌ها کلیک کنید.
              </div>
            </CardContent>
          </Card>

        </div>

        <!-- Rendered Component Preview Panel (7 cols) -->
        <div class="lg:col-span-7 flex flex-col items-center justify-center space-y-4">
          <div class="w-full flex items-center justify-between">
            <span class="text-xs font-bold text-muted-foreground uppercase tracking-wider">پیش‌نمایش مولفه</span>
            <Badge variant="outline" class="text-xs">
              {{ currentCampaign.status }}
            </Badge>
          </div>

          <!-- DonationCard Component Under Test -->
          <DonationCard
            v-bind="currentCampaign"
            @donate-click="handleDonateClick"
            @topic-click="handleTopicClick"
            @transparency-click="handleTransparencyClick"
            @share-click="handleShareClick"
            @edit-click="handleEditClick"
            @delete-click="handleDeleteClick"
          />
        </div>

      </div>

      <!-- Donation Modal -->
      <DonationModal
        v-model:open="isModalOpen"
        :campaign-title="currentCampaign.title"
        @submit-donation="handleDonationSubmit"
      />

    </div>
  </div>
</template>
