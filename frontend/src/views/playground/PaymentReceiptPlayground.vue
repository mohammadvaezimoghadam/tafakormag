<script setup lang="ts">
import { ref, reactive } from 'vue'
import PaymentReceiptModal from '@/components/kindness/PaymentReceiptModal.vue'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { 
  CheckCircle2Icon, 
  SunIcon, 
  MoonIcon, 
  TerminalIcon,
  Trash2Icon,
  SparklesIcon,
  RotateCcwIcon,
  ReceiptTextIcon
} from '@lucide/vue'

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
const isModalOpen = ref(true)

// Reactive Receipt Data
const receiptData = reactive({
  amount: 500000,
  refId: '987654321',
  authority: 'S000000000000000000000000000005jy5do',
  campaignTitle: 'تجهیز و شاداب‌سازی کلاس درس مدرسه ابتدایی در روستای محروم'
})

// Preset options
const applyPreset = (preset: 'small' | 'medium' | 'large') => {
  if (preset === 'small') {
    receiptData.amount = 50000
    receiptData.refId = `REF-${Math.floor(100000 + Math.random() * 900000)}`
    receiptData.authority = `S00000000000000000000000000000${Math.floor(10000 + Math.random() * 90000)}`
    receiptData.campaignTitle = 'تهیه بسته آموزشی برای کودکان کم‌برخوردار'
  } else if (preset === 'medium') {
    receiptData.amount = 500000
    receiptData.refId = '987654321'
    receiptData.authority = 'S000000000000000000000000000005jy5do'
    receiptData.campaignTitle = 'تجهیز و شاداب‌سازی کلاس درس مدرسه ابتدایی در روستای محروم'
  } else {
    receiptData.amount = 20000000
    receiptData.refId = `REF-${Math.floor(10000000 + Math.random() * 90000000)}`
    receiptData.authority = `S00000000000000000000000000000${Math.floor(10000 + Math.random() * 90000)}`
    receiptData.campaignTitle = 'خرید دستگاه اکسیژن‌ساز برای مرکز درمانی خیریه'
  }
  isModalOpen.value = true
  addLog('preset-applied', { preset, ...receiptData })
}

// Generate random IDs
const generateRandomIds = () => {
  receiptData.refId = String(Math.floor(100000000 + Math.random() * 900000000))
  receiptData.authority = `S00000000000000000000000000000${Math.random().toString(36).substring(2, 8)}`
  addLog('random-ids-generated', { refId: receiptData.refId, authority: receiptData.authority })
}

// Logs
interface EventLog {
  id: number
  time: string
  name: string
  payload: string
}
const logs = ref<EventLog[]>([])
let logIdCounter = 0

const addLog = (name: string, payload: any) => {
  logIdCounter++
  const time = new Intl.DateTimeFormat('fa-IR', { 
    hour: '2-digit', 
    minute: '2-digit', 
    second: '2-digit' 
  }).format(new Date())

  logs.value.unshift({
    id: logIdCounter,
    time,
    name,
    payload: JSON.stringify(payload)
  })
}

const clearLogs = () => {
  logs.value = []
}

const handleClose = () => {
  addLog('modal-close-event', {})
}

const handleViewCampaign = () => {
  addLog('view-campaign-event', { campaignTitle: receiptData.campaignTitle })
}
</script>

<template>
  <div class="min-h-screen bg-background text-foreground dir-rtl font-sans p-4 sm:p-8 flex flex-col gap-6">
    
    <!-- Top Navigation / Header -->
    <header class="w-full max-w-5xl mx-auto flex items-center justify-between gap-4 p-4 rounded-3xl border border-border/60 bg-card shadow-xs">
      <div class="flex items-center gap-3">
        <div class="size-10 rounded-2xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 flex items-center justify-center shadow-xs">
          <ReceiptTextIcon class="size-5" />
        </div>
        <div>
          <div class="flex items-center gap-2">
            <h1 class="text-base sm:text-lg font-black text-foreground">
              پلی‌گراند رسید پرداخت موفق زرین‌پال (PaymentReceiptModal)
            </h1>
            <Badge variant="secondary" class="text-[10px] px-2 py-0.5 rounded-full font-mono text-emerald-600 border-emerald-500/20 bg-emerald-500/10">
              ZarinPal Sandbox
            </Badge>
          </div>
          <p class="text-xs text-muted-foreground">
            تست و شبیه‌سازی نمایش فاکتور و رسید موفق بازگشت از درگاه پرداخت به همراه لاگ رویدادها
          </p>
        </div>
      </div>

      <div class="flex items-center gap-2">
        <Button 
          variant="outline" 
          size="icon" 
          class="rounded-xl border-border/60 hover:bg-muted cursor-pointer"
          :title="isDarkMode ? 'حالت روشن' : 'حالت تیره'"
          @click="toggleDarkMode"
        >
          <SunIcon v-if="isDarkMode" class="size-4 text-amber-500" />
          <MoonIcon v-else class="size-4 text-slate-700" />
        </Button>
      </div>
    </header>

    <!-- Main Workspace -->
    <main class="w-full max-w-5xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-6">
      
      <!-- Left Column: Controls & Presets (6 cols) -->
      <section class="lg:col-span-6 flex flex-col gap-5">
        
        <!-- Presets Selection Card -->
        <Card class="rounded-3xl border-border/70 bg-card shadow-xs">
          <CardHeader class="p-5 pb-3">
            <CardTitle class="text-sm font-black flex items-center gap-2">
              <SparklesIcon class="size-4 text-primary" />
              <span>سناریوهای آماده تست</span>
            </CardTitle>
            <CardDescription class="text-xs text-muted-foreground">
              بارگذاری مبالغ و اطلاعات نمونه با یک کلیک
            </CardDescription>
          </CardHeader>
          <CardContent class="p-5 pt-0 space-y-2.5">
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-2">
              <Button 
                variant="outline" 
                class="h-auto py-2.5 px-3 flex flex-col items-start gap-1 text-right border-border/60 hover:border-primary/50 cursor-pointer"
                @click="applyPreset('small')"
              >
                <span class="text-xs font-bold text-foreground">۵۰ هزار تومان</span>
                <span class="text-[10px] text-muted-foreground">مبلغ خرد / حامی عادی</span>
              </Button>

              <Button 
                variant="outline" 
                class="h-auto py-2.5 px-3 flex flex-col items-start gap-1 text-right border-border/60 hover:border-primary/50 cursor-pointer"
                @click="applyPreset('medium')"
              >
                <span class="text-xs font-bold text-foreground">۵۰۰ هزار تومان</span>
                <span class="text-[10px] text-muted-foreground">مبلغ متوسط پویش</span>
              </Button>

              <Button 
                variant="outline" 
                class="h-auto py-2.5 px-3 flex flex-col items-start gap-1 text-right border-border/60 hover:border-primary/50 cursor-pointer"
                @click="applyPreset('large')"
              >
                <span class="text-xs font-bold text-foreground">۲۰ میلیون تومان</span>
                <span class="text-[10px] text-muted-foreground">مبلغ کلان جهادی</span>
              </Button>
            </div>
          </CardContent>
        </Card>

        <!-- Parameters Live Form -->
        <Card class="rounded-3xl border-border/70 bg-card shadow-xs">
          <CardHeader class="p-5 pb-3 flex flex-row items-center justify-between">
            <div>
              <CardTitle class="text-sm font-black text-foreground">تنظیمات زنده پارامترهای رسید</CardTitle>
              <CardDescription class="text-xs text-muted-foreground">تغییر مقادیر ورودی کامپوننت</CardDescription>
            </div>
            <Button size="xs" variant="outline" class="gap-1 text-[11px] h-7 cursor-pointer" @click="generateRandomIds">
              <RotateCcwIcon class="size-3" />
              <span>تولید کد جدید</span>
            </Button>
          </CardHeader>
          <CardContent class="p-5 pt-0 space-y-3.5">
            <div class="space-y-1.5">
              <Label class="text-xs font-bold text-foreground">مبلغ اهدایی (تومان):</Label>
              <Input 
                type="number" 
                v-model.number="receiptData.amount" 
                class="h-9 text-xs font-bold"
                placeholder="مبلغ به تومان" 
              />
            </div>

            <div class="space-y-1.5">
              <Label class="text-xs font-bold text-foreground">عنوان پویش مهربانی:</Label>
              <Input 
                v-model="receiptData.campaignTitle" 
                class="h-9 text-xs"
                placeholder="عنوان پویش" 
              />
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div class="space-y-1.5">
                <Label class="text-xs font-bold text-foreground">شماره پیگیری بانک (Ref ID):</Label>
                <Input 
                  v-model="receiptData.refId" 
                  class="h-9 text-xs font-mono"
                  placeholder="شماره پیگیری" 
                />
              </div>

              <div class="space-y-1.5">
                <Label class="text-xs font-bold text-foreground">شناسه تراکنش زرین‌پال (Authority):</Label>
                <Input 
                  v-model="receiptData.authority" 
                  class="h-9 text-xs font-mono"
                  placeholder="Authority" 
                />
              </div>
            </div>

            <div class="pt-2 flex justify-end">
              <Button 
                class="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs h-10 rounded-2xl gap-2 cursor-pointer shadow-md"
                @click="isModalOpen = true"
              >
                <CheckCircle2Icon class="size-4" />
                <span>نمایش و باز کردن مودال رسید پرداخت</span>
              </Button>
            </div>
          </CardContent>
        </Card>

      </section>

      <!-- Right Column: Live Preview & Event Logs (6 cols) -->
      <section class="lg:col-span-6 flex flex-col gap-5">
        
        <!-- Live Snapshot Card -->
        <Card class="rounded-3xl border-border/70 bg-card shadow-xs">
          <CardHeader class="p-5 pb-3">
            <div class="flex items-center justify-between">
              <CardTitle class="text-sm font-black flex items-center gap-2">
                <CheckCircle2Icon class="size-4 text-emerald-500" />
                <span>پیش‌نمایش اطلاعات فاکتور</span>
              </CardTitle>
              <Badge variant="outline" class="text-[10px] border-emerald-500/30 text-emerald-600 dark:text-emerald-400 bg-emerald-500/10">
                پرداخت موفق
              </Badge>
            </div>
            <CardDescription class="text-xs text-muted-foreground">
              خلاصه اطلاعاتی که در دیالوگ به کاربر نمایش داده می‌شود
            </CardDescription>
          </CardHeader>
          <CardContent class="p-5 pt-0">
            <div class="rounded-2xl border border-border/60 bg-muted/20 p-4 flex flex-col gap-3">
              <div class="flex items-center justify-between py-1.5 border-b border-border/40 text-xs">
                <span class="text-muted-foreground">مبلغ پرداختی:</span>
                <span class="font-extrabold text-sm text-emerald-600 dark:text-emerald-400">
                  {{ new Intl.NumberFormat('fa-IR').format(receiptData.amount) }} تومان
                </span>
              </div>
              <div class="flex items-center justify-between py-1.5 border-b border-border/40 text-xs">
                <span class="text-muted-foreground">شماره پیگیری:</span>
                <span class="font-mono font-bold">{{ receiptData.refId }}</span>
              </div>
              <div class="flex items-center justify-between py-1.5 border-b border-border/40 text-xs">
                <span class="text-muted-foreground">شناسه زرین‌پال:</span>
                <span class="font-mono text-[11px] text-muted-foreground truncate max-w-[200px]">{{ receiptData.authority }}</span>
              </div>
              <div class="flex items-center justify-between py-1 text-xs">
                <span class="text-muted-foreground">پویش:</span>
                <span class="font-medium text-foreground truncate max-w-[220px]">{{ receiptData.campaignTitle }}</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <!-- Event Log Monitor -->
        <Card class="rounded-3xl border-border/70 bg-card shadow-xs flex-1 flex flex-col">
          <CardHeader class="p-5 pb-3 flex flex-row items-center justify-between">
            <div class="space-y-0.5">
              <CardTitle class="text-sm font-black flex items-center gap-2">
                <TerminalIcon class="size-4 text-emerald-500" />
                <span>لاگ رویدادها (Event Log)</span>
              </CardTitle>
              <CardDescription class="text-xs text-muted-foreground">
                رویدادهای شلیک شده توسط کامپوننت رسید
              </CardDescription>
            </div>
            <Button 
              v-if="logs.length > 0"
              variant="ghost" 
              size="sm" 
              class="h-7 text-xs text-muted-foreground hover:text-destructive cursor-pointer"
              @click="clearLogs"
            >
              <Trash2Icon class="size-3.5" data-icon="inline-start" />
              <span>پاکسازی</span>
            </Button>
          </CardHeader>
          <CardContent class="p-5 pt-0 flex-1">
            <div v-if="logs.length === 0" class="h-40 flex flex-col items-center justify-center text-center p-4 border border-dashed border-border/60 rounded-2xl text-muted-foreground">
              <CheckCircle2Icon class="size-6 text-muted-foreground/40 mb-1" />
              <span class="text-xs">هنوز رویدادی شلیک نشده است.</span>
            </div>
            <div v-else class="space-y-2 max-h-56 overflow-y-auto pr-1">
              <div 
                v-for="log in logs" 
                :key="log.id"
                class="p-2.5 rounded-2xl bg-muted/40 border border-border/60 text-xs font-mono space-y-1"
                dir="ltr"
              >
                <div class="flex items-center justify-between text-[10px] text-muted-foreground font-sans font-bold dir-rtl">
                  <span class="text-primary font-bold">@{{ log.name }}</span>
                  <span>{{ log.time }}</span>
                </div>
                <pre class="text-[10px] text-foreground overflow-x-auto whitespace-pre-wrap">{{ log.payload }}</pre>
              </div>
            </div>
          </CardContent>
        </Card>

      </section>

    </main>

    <!-- The PaymentReceiptModal Instance -->
    <PaymentReceiptModal
      v-model:open="isModalOpen"
      :amount="receiptData.amount"
      :ref-id="receiptData.refId"
      :authority="receiptData.authority"
      :campaign-title="receiptData.campaignTitle"
      @close="handleClose"
      @view-campaign="handleViewCampaign"
    />

  </div>
</template>
