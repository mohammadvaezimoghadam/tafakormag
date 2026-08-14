<script setup lang="ts">
import { ref, reactive } from 'vue'
import CreateDonationDialog from '@/components/kindness/CreateDonationDialog.vue'
import DonationChatCard from '@/components/kindness/DonationChatCard.vue'
import type { CreateDonationPayload } from '@/types/kindness'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { 
  HeartIcon, 
  MessageSquareIcon, 
  SunIcon, 
  MoonIcon, 
  CheckCircle2Icon, 
  PlayIcon, 
  ArrowRightIcon, 
  TerminalIcon,
  Trash2Icon
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

// Dialog State
const isDialogOpen = ref(true)

// Captured Payloads & Logs
const emittedPayloads = ref<Array<{ timestamp: string; payload: CreateDonationPayload }>>([])

// Mock Topic Context
const topicContext = reactive({
  id: 'topic-mosque-7',
  name: 'کانون فرهنگی و جهادی امام رضا (ع)',
  authorName: 'مسئول گروه جهادی',
  authorAvatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=150&q=80'
})

// Last created campaign for inline simulation preview
const lastCreatedCampaign = ref<CreateDonationPayload | null>({
  topic_id: 'topic-mosque-7',
  title: 'تجهیز و نوسازی سیستم گرمایشی مدرسه محروم روستایی',
  category: 'school',
  target_amount: 35000000,
  description: 'با شروع فصل سرما، جهت خرید ۳ دستگاه پکیج و رادیاتور استاندارد برای کلاس‌های درس دانش‌آموزان به این مبلغ نیازمندیم.',
  media_files: [],
  auto_pin: true,
  deadline: '۱۴ روز آینده'
})

const handleCreated = (payload: CreateDonationPayload) => {
  const time = new Intl.DateTimeFormat('fa-IR', { 
    hour: '2-digit', 
    minute: '2-digit', 
    second: '2-digit' 
  }).format(new Date())

  emittedPayloads.value.unshift({
    timestamp: time,
    payload
  })

  lastCreatedCampaign.value = payload
}

const clearLogs = () => {
  emittedPayloads.value = []
}
</script>

<template>
  <div class="min-h-screen bg-background text-foreground dir-rtl font-sans p-4 sm:p-8 flex flex-col gap-6">
    
    <!-- Top Navigation / Header -->
    <header class="w-full max-w-5xl mx-auto flex items-center justify-between gap-4 p-4 rounded-3xl border border-border/60 bg-card shadow-xs">
      <div class="flex items-center gap-3">
        <div class="size-10 rounded-2xl bg-primary/10 text-primary flex items-center justify-center shadow-xs">
          <HeartIcon class="size-5 fill-primary/20" />
        </div>
        <div>
          <div class="flex items-center gap-2">
            <h1 class="text-base sm:text-lg font-black text-foreground">
              پلی‌گراند ساخت پویش مهربانی (CreateDonationDialog)
            </h1>
            <Badge variant="secondary" class="text-[10px] px-2 py-0.5 rounded-full font-mono">
              shadcn-vue
            </Badge>
          </div>
          <p class="text-xs text-muted-foreground">
            تست سناریوهای ویزارد ۳ مرحله‌ای، اعتبارسنجی‌ها، تبدیل مبالغ و پیش‌نمایش زنده
          </p>
        </div>
      </div>

      <div class="flex items-center gap-2">
        <Button 
          variant="outline" 
          size="icon" 
          class="rounded-xl border-border/60 hover:bg-muted"
          :title="isDarkMode ? 'حالت روشن' : 'حالت تیره'"
          @click="toggleDarkMode"
        >
          <SunIcon v-if="isDarkMode" class="size-4 text-amber-500" />
          <MoonIcon v-else class="size-4 text-slate-700" />
        </Button>
      </div>
    </header>

    <!-- Main Playground Workspace -->
    <main class="w-full max-w-5xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-6">
      
      <!-- Left Column: Controls & Triggers (5 cols) -->
      <section class="lg:col-span-5 flex flex-col gap-5">
        
        <!-- Direct Inline CreateDonationDialog -->
        <div class="w-full flex justify-center">
          <CreateDonationDialog 
            :is-inline="true"
            :topic-id="topicContext.id"
            :topic-name="topicContext.name"
            :author-name="topicContext.authorName"
            :author-avatar="topicContext.authorAvatar"
            @created="handleCreated"
          />
        </div>

        <!-- Output Event Log -->
        <Card class="rounded-3xl border-border/70 bg-card shadow-xs flex-1 flex flex-col">
          <CardHeader class="p-5 pb-3 flex flex-row items-center justify-between">
            <div class="space-y-0.5">
              <CardTitle class="text-sm font-black flex items-center gap-2">
                <TerminalIcon class="size-4 text-emerald-500" />
                <span>رویدادهای دریافتی (@created)</span>
              </CardTitle>
              <CardDescription class="text-xs text-muted-foreground">
                داده‌های تایپ‌شده ارسال شده از دیالوگ
              </CardDescription>
            </div>
            <Button 
              v-if="emittedPayloads.length > 0"
              variant="ghost" 
              size="sm" 
              class="h-7 text-xs text-muted-foreground hover:text-destructive"
              @click="clearLogs"
            >
              <Trash2Icon class="size-3.5" data-icon="inline-start" />
              <span>پاکسازی</span>
            </Button>
          </CardHeader>
          <CardContent class="p-5 pt-0 flex-1">
            <div v-if="emittedPayloads.length === 0" class="h-44 flex flex-col items-center justify-center text-center p-4 border border-dashed border-border/60 rounded-2xl text-muted-foreground">
              <CheckCircle2Icon class="size-6 text-muted-foreground/40 mb-1" />
              <span class="text-xs">هنوز پویشی ثبت نشده است.</span>
            </div>
            <div v-else class="space-y-3 max-h-72 overflow-y-auto pr-1">
              <div 
                v-for="(item, idx) in emittedPayloads" 
                :key="idx"
                class="p-3 rounded-2xl bg-muted/40 border border-border/60 text-xs font-mono space-y-1.5"
                dir="ltr"
              >
                <div class="flex items-center justify-between text-[11px] text-muted-foreground font-sans font-bold dir-rtl">
                  <span>ثبت شده در: {{ item.timestamp }}</span>
                  <Badge variant="outline" class="text-[10px]">{{ item.payload.category }}</Badge>
                </div>
                <pre class="text-[11px] text-foreground overflow-x-auto whitespace-pre-wrap">{{ JSON.stringify(item.payload, (k, v) => k === 'media_files' ? `[${v.length} File(s)]` : v, 2) }}</pre>
              </div>
            </div>
          </CardContent>
        </Card>

      </section>

      <!-- Right Column: Live Chat Simulation Preview (7 cols) -->
      <section class="lg:col-span-7 flex flex-col gap-5">
        <Card class="rounded-3xl border-border/70 bg-card shadow-xs flex-1 flex flex-col">
          <CardHeader class="p-5 pb-3">
            <div class="flex items-center justify-between">
              <CardTitle class="text-sm font-black flex items-center gap-2">
                <MessageSquareIcon class="size-4 text-primary" />
                <span>شبیه‌سازی کارت در محیط چت تاپیک</span>
              </CardTitle>
              <Badge variant="outline" class="text-[10px] border-emerald-500/40 bg-emerald-500/10 text-emerald-600 font-bold">
                نمایش زنده در چت
              </Badge>
            </div>
            <CardDescription class="text-xs text-muted-foreground">
              کارت ساخته شده به عنوان پیام یا کارت سنجاق‌شده در این قالب نمایش داده می‌شود.
            </CardDescription>
          </CardHeader>
          <CardContent class="p-5 flex-1 flex flex-col items-center justify-center bg-muted/15 rounded-b-3xl">
            <div v-if="lastCreatedCampaign" class="w-full max-w-md">
              <DonationChatCard 
                :title="lastCreatedCampaign.title"
                :category="lastCreatedCampaign.category"
                :target-amount="lastCreatedCampaign.target_amount"
                :collected-amount="0"
                :description="lastCreatedCampaign.description"
                :auto-pin="lastCreatedCampaign.auto_pin"
                :deadline="lastCreatedCampaign.deadline"
                :topic-name="topicContext.name"
                :author-name="topicContext.authorName"
                :author-avatar="topicContext.authorAvatar"
              />
            </div>
            <div v-else class="text-xs text-muted-foreground text-center p-8">
              برای مشاهده کارت، روی دکمه باز کردن دیالوگ کلیک کرده و یک پویش ایجاد کنید.
            </div>
          </CardContent>
        </Card>
      </section>

    </main>

    <!-- The Multi-step Create Donation Dialog Component -->
    <CreateDonationDialog 
      v-model:open="isDialogOpen"
      :topic-id="topicContext.id"
      :topic-name="topicContext.name"
      :author-name="topicContext.authorName"
      :author-avatar="topicContext.authorAvatar"
      @created="handleCreated"
    />

  </div>
</template>
