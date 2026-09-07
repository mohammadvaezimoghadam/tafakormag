<script setup lang="ts">
import { ref } from 'vue'
import { useLanguageStore } from '@/stores/languageStore'
import PlatformHeader from '@/components/PlatformHeader.vue'
import TopicAiChatView from '@/components/TopicAiChatView.vue'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Label } from '@/components/ui/label'
import type { TopicFAQ } from '@/api'
import {
  HelpCircleIcon,
  ArrowRightIcon,
  CheckCircle2Icon,
  RefreshCwIcon,
  UserIcon,
  ShieldCheckIcon,
  SparklesIcon,
  TerminalIcon,
  ChevronLeftIcon
} from '@lucide/vue'

const languageStore = useLanguageStore()

// State
const activeSubView = ref<'feed' | 'faq'>('feed')
const isOwner = ref(true)
const forcedState = ref<'default' | 'loading' | 'empty'>('default')

// Mock FAQs
const createInitialFaqs = (): TopicFAQ[] => [
  {
    id: 1,
    topic: 101,
    question: 'قوانین و چارچوب فعالیت در این تاپیک چیست؟',
    answer: 'احترام متقابل به تمام اعضا، تمرکز بر موضوع تخصصی تاپیک، پرهیز از ارسال پیام‌های نامرتبط یا تبلیغاتی، و رعایت اصول گفت‌وگوی سازنده الزامی است.',
    order: 0,
    is_published: true,
    created_at: '2026-03-01T10:00:00Z',
    updated_at: '2026-03-01T10:00:00Z'
  },
  {
    id: 2,
    topic: 101,
    question: 'چگونه می‌توانم فایل‌ها و منابع جلسات را دریافت کنم؟',
    answer: 'تمامی فایل‌ها، اسلایدها و لینک‌های مرتبط با جلسات در بخش «پیام‌های سنجاق‌شده» (Pinned Messages) و تب اسناد تاپیک قرار داده می‌شوند.',
    order: 1,
    is_published: true,
    created_at: '2026-03-02T11:30:00Z',
    updated_at: '2026-03-02T11:30:00Z'
  },
  {
    id: 3,
    topic: 101,
    question: 'زمان برگزاری نشست‌های آنلاین هفتگی چه ساعتی است؟',
    answer: 'نشست‌های آنلاین گفت‌وگو و تبادل نظر هر هفته دوشنبه‌ها راس ساعت ۱۸:۳۰ به وقت تهران برگزار می‌گردد.',
    order: 2,
    is_published: true,
    created_at: '2026-03-03T09:15:00Z',
    updated_at: '2026-03-03T09:15:00Z'
  },
  {
    id: 4,
    topic: 101,
    question: 'برای پیشنهاد موضوع جدید یا ارائه در جلسات با چه کسی هماهنگ کنم؟',
    answer: 'می‌توانید خلاصه موضوع پیشنهادی را از طریق پیام خصوصی به مدیران تاپیک ارسال کنید تا در برنامه ماهانه ثبت شود.',
    order: 3,
    is_published: true,
    created_at: '2026-03-04T14:00:00Z',
    updated_at: '2026-03-04T14:00:00Z'
  }
]

const mockFaqs = ref<TopicFAQ[]>(createInitialFaqs())

const resetMockData = () => {
  mockFaqs.value = createInitialFaqs()
  forcedState.value = 'default'
  logEvent('Mock data reset to default', {})
}

// Event logging
interface EventLogItem {
  id: number
  time: string
  name: string
  data: string
}

const eventLogs = ref<EventLogItem[]>([])

const logEvent = (name: string, data: any) => {
  const now = new Date()
  const timeStr = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`
  eventLogs.value.unshift({
    id: Date.now() + Math.random(),
    time: timeStr,
    name,
    data: typeof data === 'object' ? JSON.stringify(data) : String(data)
  })
  if (eventLogs.value.length > 20) {
    eventLogs.value.pop()
  }
}
</script>

<template>
  <div class="min-h-screen bg-background text-foreground flex flex-col items-center p-4 sm:p-6 lg:p-8" :dir="languageStore.dir">
    <!-- Header / Navigation -->
    <header class="w-full max-w-5xl flex items-center justify-between border-b border-border/50 pb-4 mb-6">
      <div class="flex items-center gap-3">
        <router-link
          to="/playground"
          class="size-8 rounded-lg border border-border/60 hover:bg-muted/50 flex items-center justify-center transition-colors"
        >
          <ArrowRightIcon class="size-4 rtl:rotate-0 rotate-180" />
        </router-link>
        <div>
          <h1 class="text-base sm:text-lg font-black flex items-center gap-2">
            <HelpCircleIcon class="size-5 text-amber-500" />
            <span>آزمایشگاه سوالات متداول تاپیک (Topic FAQ Playground)</span>
          </h1>
          <p class="text-xs text-muted-foreground mt-0.5">
            تست رفتار دکمه شیشه‌ای شناور در فید تاپیک و صفحه آکاردئون سوالات متداول
          </p>
        </div>
      </div>

      <Badge variant="outline" class="text-xs font-mono px-2.5 py-1">
        Curated FAQ Scenario
      </Badge>
    </header>

    <!-- Main Content Container -->
    <main class="w-full max-w-5xl grid grid-cols-1 lg:grid-cols-12 gap-6">
      <!-- Control Panel -->
      <aside class="lg:col-span-5 flex flex-col gap-5">
        <!-- Mode Switcher -->
        <div class="bg-card/40 border border-border/60 rounded-2xl p-5 shadow-xs flex flex-col gap-4 text-start">
          <div class="flex items-center justify-between border-b border-border/40 pb-3">
            <span class="text-xs font-black text-foreground flex items-center gap-2">
              <SparklesIcon class="size-4 text-primary" />
              حالت نمایش
            </span>
            <Badge :variant="activeSubView === 'feed' ? 'secondary' : 'default'" class="text-[10px]">
              {{ activeSubView === 'feed' ? 'نمای فید تاپیک' : 'نمای سوالات متداول' }}
            </Badge>
          </div>

          <div class="grid grid-cols-2 gap-2">
            <button
              @click="activeSubView = 'feed'; logEvent('Switched to feed view', {})"
              :class="[
                'p-3 rounded-xl border text-xs font-bold transition-all text-start flex flex-col gap-1 cursor-pointer',
                activeSubView === 'feed'
                  ? 'bg-primary/10 border-primary text-primary shadow-xs'
                  : 'bg-background/40 border-border/50 text-muted-foreground hover:bg-muted/40'
              ]"
            >
              <span>۱. فید تاپیک</span>
              <span class="text-[10px] opacity-70 font-normal">نمایش دکمه شیشه‌ای شناور زیر هدر</span>
            </button>

            <button
              @click="activeSubView = 'faq'; logEvent('Switched to faq subview', {})"
              :class="[
                'p-3 rounded-xl border text-xs font-bold transition-all text-start flex flex-col gap-1 cursor-pointer',
                activeSubView === 'faq'
                  ? 'bg-primary/10 border-primary text-primary shadow-xs'
                  : 'bg-background/40 border-border/50 text-muted-foreground hover:bg-muted/40'
              ]"
            >
              <span>۲. صفحه سوالات</span>
              <span class="text-[10px] opacity-70 font-normal">آکاردئون، جستجو و ویرایش</span>
            </button>
          </div>
        </div>

        <!-- Role & Simulator Settings -->
        <div class="bg-card/40 border border-border/60 rounded-2xl p-5 shadow-xs flex flex-col gap-4 text-start">
          <span class="text-xs font-black text-foreground border-b border-border/40 pb-2.5 flex items-center gap-2">
            <ShieldCheckIcon class="size-4 text-emerald-500" />
            نقش و اختیارات کاربری
          </span>

          <div class="flex flex-col gap-2">
            <button
              @click="isOwner = true; logEvent('Role changed to Owner/Admin', {})"
              :class="[
                'p-2.5 rounded-xl border text-xs font-bold transition-all flex items-center justify-between cursor-pointer',
                isOwner
                  ? 'bg-primary/10 border-primary text-primary'
                  : 'bg-background/30 border-border/40 text-muted-foreground hover:bg-muted/30'
              ]"
            >
              <div class="flex items-center gap-2">
                <ShieldCheckIcon class="size-4 text-primary" />
                <span>مالک و ادمین تاپیک (مدیریت کامل)</span>
              </div>
              <CheckCircle2Icon v-if="isOwner" class="size-4 text-primary" />
            </button>

            <button
              @click="isOwner = false; logEvent('Role changed to Regular Member', {})"
              :class="[
                'p-2.5 rounded-xl border text-xs font-bold transition-all flex items-center justify-between cursor-pointer',
                !isOwner
                  ? 'bg-primary/10 border-primary text-primary'
                  : 'bg-background/30 border-border/40 text-muted-foreground hover:bg-muted/30'
              ]"
            >
              <div class="flex items-center gap-2">
                <UserIcon class="size-4 text-muted-foreground" />
                <span>عضو عادی تاپیک (فقط مشاهده و جستجو)</span>
              </div>
              <CheckCircle2Icon v-if="!isOwner" class="size-4 text-primary" />
            </button>
          </div>

          <!-- Forced State -->
          <div class="pt-3 border-t border-border/30 flex flex-col gap-2">
            <Label class="text-[11px] text-muted-foreground font-semibold">شبیه‌سازی وضعیت پاسخ سرور:</Label>
            <div class="grid grid-cols-3 gap-1.5 bg-muted/40 p-1 rounded-xl border border-border/40">
              <button
                @click="forcedState = 'default'; logEvent('State changed to default', {})"
                :class="[
                  'py-1.5 text-xs rounded-lg font-bold transition-all cursor-pointer',
                  forcedState === 'default' ? 'bg-background text-primary shadow-xs' : 'text-muted-foreground hover:text-foreground'
                ]"
              >
                عادی
              </button>
              <button
                @click="forcedState = 'loading'; logEvent('State changed to loading', {})"
                :class="[
                  'py-1.5 text-xs rounded-lg font-bold transition-all cursor-pointer',
                  forcedState === 'loading' ? 'bg-background text-primary shadow-xs' : 'text-muted-foreground hover:text-foreground'
                ]"
              >
                لودینگ
              </button>
              <button
                @click="forcedState = 'empty'; logEvent('State changed to empty', {})"
                :class="[
                  'py-1.5 text-xs rounded-lg font-bold transition-all cursor-pointer',
                  forcedState === 'empty' ? 'bg-background text-primary shadow-xs' : 'text-muted-foreground hover:text-foreground'
                ]"
              >
                خالی
              </button>
            </div>
          </div>

          <Button
            size="sm"
            variant="outline"
            class="w-full text-xs font-bold gap-1.5 cursor-pointer mt-1"
            @click="resetMockData"
          >
            <RefreshCwIcon class="size-3.5" />
            <span>بازنشانی سوالات اولیه</span>
          </Button>
        </div>

        <!-- Event Logs -->
        <div class="bg-card/40 border border-border/60 rounded-2xl p-4 shadow-xs flex flex-col gap-2.5 text-start">
          <div class="flex items-center justify-between">
            <span class="text-xs font-extrabold text-foreground flex items-center gap-1.5">
              <TerminalIcon class="size-3.5 text-primary" />
              رویدادهای زنده (Live Event Log)
            </span>
            <Badge variant="secondary" class="text-[9px] font-mono">Reactive</Badge>
          </div>

          <div class="h-32 bg-background/80 border border-border/50 rounded-xl p-2.5 overflow-y-auto font-mono text-[10px] flex flex-col gap-1.5">
            <div v-if="eventLogs.length === 0" class="text-muted-foreground text-center py-6">
              رویدادی ثبت نشده است. روی دکمه‌ها کلیک کنید.
            </div>
            <div
              v-for="ev in eventLogs"
              :key="ev.id"
              class="flex items-start justify-between border-b border-border/20 pb-1 last:border-0"
            >
              <div class="flex items-start gap-1.5">
                <ChevronLeftIcon class="size-3 text-emerald-500 shrink-0 mt-0.5" />
                <span class="text-primary font-bold">{{ ev.name }}</span>
                <span class="text-muted-foreground truncate max-w-[160px]">{{ ev.data }}</span>
              </div>
              <span class="text-muted-foreground shrink-0 text-[9px]">{{ ev.time }}</span>
            </div>
          </div>
        </div>
      </aside>

      <!-- Mock Device Frame -->
      <section class="lg:col-span-7 flex flex-col items-center">
        <div class="w-full max-w-[420px] bg-card/80 border border-border/70 rounded-[32px] shadow-2xl overflow-hidden flex flex-col min-h-[640px] relative">
          <!-- Mock Phone Status Bar -->
          <div class="w-full bg-background/90 px-5 py-2 border-b border-border/30 flex items-center justify-between text-[11px] font-mono text-muted-foreground select-none">
            <span>۱۹:۴۵</span>
            <div class="flex items-center gap-2">
              <span class="size-2 rounded-full bg-emerald-500 inline-block animate-pulse"></span>
              <span>4G</span>
              <span>95%</span>
            </div>
          </div>

          <!-- Feed Mode -->
          <div v-if="activeSubView === 'feed'" class="flex-1 flex flex-col text-start relative">
            <!-- Topic Header with PlatformHeader -->
            <div class="px-3 py-2 bg-background/95 border-b border-border/50 sticky top-0 z-20 backdrop-blur-md">
              <PlatformHeader
                :is-inner-page="true"
                inner-title="کانون تفکر و نوآوری"
                :show-faq-button="true"
                :show-options-button="true"
                @topic-faq="activeSubView = 'faq'; logEvent('Header FAQ/AI button clicked -> Open AI Chat', {})"
                @back="logEvent('Header back clicked', {})"
              />
            </div>

            <!-- Highlight banner pointing to the header button -->
            <div class="px-3 py-1.5 bg-amber-500/10 border-b border-amber-500/20 flex items-center justify-between text-[10px]">
              <span class="text-amber-700 dark:text-amber-300 font-bold flex items-center gap-1">
                <HelpCircleIcon class="size-3 text-amber-500 shrink-0" />
                <span>دکمه علامت سوال در هدر (سمت راست سه‌نقطه) فعال است 👆</span>
              </span>
              <Badge variant="outline" class="text-[9px] bg-background/50">فید تاپیک</Badge>
            </div>

            <!-- Mock Feed Posts -->
            <div class="flex-1 p-4 space-y-3.5 overflow-y-auto">
              <div class="p-3.5 bg-card/60 border border-border/50 rounded-2xl space-y-2">
                <div class="flex items-center justify-between">
                  <span class="text-xs font-bold text-foreground">مدیر تاپیک</span>
                  <span class="text-[10px] text-muted-foreground font-mono">۱۰ دقیقه پیش</span>
                </div>
                <p class="text-xs text-foreground/90 leading-relaxed">
                  سلام به همه دوستان گرامی. دستیار هوشمند تاپیک با مدل زبانی و جستجوی RAG فعال گردید. می‌توانید از دکمه جدید در هدر سوالات خود را بپرسید.
                </p>
              </div>

              <div class="p-3.5 bg-muted/20 border border-border/40 rounded-2xl space-y-2">
                <div class="flex items-center justify-between">
                  <span class="text-xs font-bold text-foreground">سارا محمدی</span>
                  <span class="text-[10px] text-muted-foreground font-mono">۲۵ دقیقه پیش</span>
                </div>
                <p class="text-xs text-foreground/80 leading-relaxed">
                  برای جلسه دوشنبه آینده، اسلایدهای مرتبط با تفکر نقادانه را می‌توانیم در همین تاپیک به اشتراک بگذاریم؟
                </p>
              </div>

              <div class="p-3.5 bg-card/60 border border-border/50 rounded-2xl space-y-2">
                <div class="flex items-center justify-between">
                  <span class="text-xs font-bold text-foreground">علی رضایی</span>
                  <span class="text-[10px] text-muted-foreground font-mono">۱ ساعت پیش</span>
                </div>
                <p class="text-xs text-foreground/80 leading-relaxed">
                  بله، در سوالات متداول توضیح داده شده که تمام منابع در پیام‌های سنجاق‌شده درج می‌شوند.
                </p>
              </div>
            </div>
          </div>

          <!-- FAQ & AI Chat SubView Mode -->
          <div v-else class="flex-1 flex flex-col text-start overflow-hidden">
            <TopicAiChatView
              :topic="{ id: 101, title: 'کانون تفکر و نوآوری', name: 'کانون تفکر و نوآوری', description: 'بحث و تبادل نظر پیرامون تفکر نقادانه و حل مسئله' }"
              :is-owner="isOwner"
              :is-admin="isOwner"
              :simulated="true"
              :initial-faqs="mockFaqs"
              @back="activeSubView = 'feed'; logEvent('Back to topic feed clicked', {})"
            />
          </div>
        </div>
      </section>
    </main>
  </div>
</template>
