<script setup lang="ts">
import { ref, computed } from 'vue'
import type { DonationCampaignProps } from '@/types/kindness'
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar'
import { Separator } from '@/components/ui/separator'
import { cn } from '@/lib/utils'
import { 
  HeartIcon, 
  UserIcon, 
  UsersIcon,
  CheckCircle2Icon, 
  FileTextIcon, 
  ImageIcon,
  Share2Icon,
  ClockIcon,
  PencilIcon,
  Trash2Icon,
  BanIcon
} from '@lucide/vue'

const props = withDefaults(defineProps<DonationCampaignProps>(), {
  authorName: undefined,
  authorAvatar: undefined,
  timestamp: undefined,
  isEmbedded: false
})

const emit = defineEmits<{
  (e: 'donate-click', campaignId: string | number): void
  (e: 'topic-click', topicId: string | number): void
  (e: 'transparency-click', imageIndex: number, imageUrl: string): void
  (e: 'share-click', campaignId: string | number): void
  (e: 'edit-click', campaignId: string | number): void
  (e: 'delete-click', campaignId: string | number): void
}>()

// Check if campaign has any donations (donations amount > 0 or donorsCount > 0 or recentDonors length > 0)
const hasDonations = computed(() => {
  return Boolean(
    (props.donorsCount && props.donorsCount > 0) ||
    (props.collectedAmount && props.collectedAmount > 0) ||
    (props.recentDonors && props.recentDonors.length > 0)
  )
})

// Active Media Index for gallery preview
const currentMediaIndex = ref(0)

const selectMedia = (idx: number) => {
  if (props.mediaGallery && idx < props.mediaGallery.length) {
    currentMediaIndex.value = idx
  }
}

// Currency & Digit Formatter (fa-IR)
const formatCurrency = (amount: number): string => {
  if (amount === undefined || amount === null) return '۰'
  return new Intl.NumberFormat('fa-IR').format(amount)
}

// Completion Percentage Calculation (0 to 100%)
const completionPercentage = computed(() => {
  if (!props.targetAmount || props.targetAmount <= 0) return 0
  const pct = Math.round((props.collectedAmount / props.targetAmount) * 100)
  return Math.min(100, Math.max(0, pct))
})

// Status Badge Configuration using semantic badge variants & tokens
const statusConfig = computed(() => {
  switch (props.status) {
    case 'active':
      return {
        label: 'در حال جمع‌آوری',
        variant: 'secondary' as const,
        icon: null
      }
    case 'completed':
      return {
        label: 'تکمیل شده',
        variant: 'outline' as const,
        icon: null
      }
    case 'executed':
      return {
        label: 'اجرا شده و شفاف',
        variant: 'default' as const,
        icon: CheckCircle2Icon
      }
    case 'inactive':
      return {
        label: 'متوقف / غیرفعال',
        variant: 'destructive' as const,
        icon: BanIcon
      }
    default:
      return {
        label: 'فعال',
        variant: 'secondary' as const,
        icon: null
      }
  }
})

// Total Transparency Cost Breakdown
const totalTransparencyCost = computed(() => {
  if (!props.transparency?.costBreakdown) return 0
  return Object.values(props.transparency.costBreakdown).reduce((acc, curr) => acc + curr, 0)
})
</script>

<template>
  <Card class="relative w-full overflow-hidden rounded-2xl border border-border/70 dark:border-border/60 bg-card/95 backdrop-blur-md text-card-foreground shadow-[0_2px_8px_rgba(0,0,0,0.03)] hover:shadow-[0_4px_16px_rgba(0,0,0,0.06)] transition-all duration-300 dir-rtl text-right font-sans flex flex-col py-0 gap-0">
    
    <!-- 1. STREAM HEADER: Creator Profile Info & Status Badge -->
    <div class="px-4 py-3 border-b border-border/60 bg-muted/20 flex items-center justify-between gap-2">
      <div class="flex items-center gap-2.5 min-w-0">
        <Avatar class="size-9 rounded-xl border border-border/60 shrink-0 overflow-hidden">
          <AvatarImage v-if="authorAvatar" :src="authorAvatar" :alt="authorName || topicName" class="w-full h-full object-cover" />
          <AvatarFallback class="bg-primary/10 text-primary font-bold text-xs rounded-xl">
            <UserIcon v-if="!authorName" class="size-3.5 text-primary" />
            <span v-else>{{ authorName.charAt(0) }}</span>
          </AvatarFallback>
        </Avatar>

        <div class="flex flex-col min-w-0 text-start">
          <span 
            class="text-xs font-bold text-foreground truncate cursor-pointer hover:underline" 
            @click="emit('topic-click', topicId)"
          >
            {{ authorName || topicName || 'مدیر تاپیک' }}
          </span>
          <div class="flex items-center gap-1.5 text-[10px] text-muted-foreground mt-0.5">
            <span v-if="topicName && authorName" class="truncate">{{ topicName }}</span>
            <span v-if="timestamp && topicName && authorName">•</span>
            <div v-if="timestamp" class="flex items-center gap-1">
              <ClockIcon class="size-3 text-primary" />
              <span>{{ timestamp }}</span>
            </div>
          </div>
        </div>
      </div>

      <Badge 
        :variant="statusConfig.variant" 
        class="rounded-full shrink-0 text-[10px] px-2.5 py-0.5 font-semibold"
      >
        <component :is="statusConfig.icon" v-if="statusConfig.icon" data-icon="inline-start" />
        <span>{{ statusConfig.label }}</span>
      </Badge>
    </div>

    <!-- 2. MEDIA GALLERY CONTAINER -->
    <div v-if="mediaGallery && mediaGallery.length > 0" class="px-3.5 pt-3">
      <div class="relative w-full aspect-[2.4/1] sm:aspect-[2.8/1] rounded-2xl overflow-hidden border border-border/40 bg-muted/30 group">
        <img 
          :src="mediaGallery[currentMediaIndex]" 
          :alt="title" 
          class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-[1.02]"
        />

        <!-- Multi-image Thumbnail Bar Overlay -->
        <div 
          v-if="mediaGallery.length > 1" 
          class="absolute bottom-2 inset-x-2 flex items-center justify-center gap-1.5 p-1 bg-background/80 backdrop-blur-md rounded-lg max-w-fit mx-auto border border-border/40"
        >
          <button 
            v-for="(img, idx) in mediaGallery.slice(0, 5)" 
            :key="idx"
            type="button"
            @click="selectMedia(idx)"
            :class="cn(
              'size-5.5 rounded-md overflow-hidden border transition-all cursor-pointer',
              idx === currentMediaIndex ? 'border-primary ring-2 ring-primary/80 scale-105' : 'border-border/40 opacity-70 hover:opacity-100'
            )"
          >
            <img :src="img" :alt="`تصویر ${idx + 1}`" class="w-full h-full object-cover" />
          </button>
          <span v-if="mediaGallery.length > 5" class="text-[9.5px] text-foreground font-bold px-1">
            +{{ mediaGallery.length - 5 }}
          </span>
        </div>
      </div>
    </div>

    <!-- 3. CARD HEADER: Title & Category Badge -->
    <CardHeader class="px-4 pt-3 pb-0">
      <div class="flex items-start justify-between gap-2">
        <CardTitle class="cn-font-heading text-sm font-bold leading-snug text-foreground line-clamp-2 text-start flex-1">
          {{ title }}
        </CardTitle>
        <Badge variant="outline" class="text-[10px] px-2 py-0.5 rounded-md font-medium shrink-0 bg-muted/30 border-border/60">
          {{ category }}
        </Badge>
      </div>
    </CardHeader>

    <!-- 4. CARD CONTENT: Funding Metrics & Tabs -->
    <CardContent class="px-4 py-3 flex flex-col gap-2.5 flex-1">
      
      <!-- Funding Progress Box -->
      <div class="p-2.5 rounded-2xl bg-muted/30 border border-border/40 flex flex-col gap-2">
        <!-- Progress Amounts Readout -->
        <div class="flex flex-wrap items-baseline justify-between gap-2 text-xs">
          <div class="flex items-baseline gap-1">
            <span class="text-[11px] text-muted-foreground font-medium">جمع‌آوری شده:</span>
            <span class="font-bold text-primary text-xs">
              {{ formatCurrency(collectedAmount) }}
            </span>
            <span class="text-[10px] text-muted-foreground">تومان</span>
          </div>

          <div class="flex items-center gap-1 text-[11px]">
            <span class="text-muted-foreground font-medium">هدف:</span>
            <span class="font-bold text-foreground text-xs">
              {{ formatCurrency(targetAmount) }}
            </span>
            <span class="text-[10px] text-muted-foreground">تومان</span>
          </div>
        </div>

        <!-- Progress Bar -->
        <Progress :model-value="completionPercentage" class="h-1.5 w-full bg-muted rounded-full" />

        <!-- Percentage & Donors Readout Footer -->
        <div class="flex justify-between items-center text-[10.5px] text-muted-foreground pt-0.5">
          <span class="flex items-center gap-1 font-medium">
            <UsersIcon class="size-3 text-primary" />
            <span>{{ formatCurrency(donorsCount) }} حامی</span>
          </span>
          <Badge variant="secondary" class="font-bold text-[10px] px-2 py-0.5 rounded-full">
            {{ formatCurrency(completionPercentage) }}٪ پیشرفت
          </Badge>
        </div>
      </div>

      <!-- Shadcn Tabs System -->
      <Tabs default-value="overview" class="w-full">
        <TabsList class="grid w-full grid-cols-3 bg-muted/60 p-0.5 rounded-xl h-8">
          <TabsTrigger value="overview" class="text-[11px] font-bold h-7 rounded-lg">
            معرفی
          </TabsTrigger>
          <TabsTrigger value="donors" class="text-[11px] font-bold h-7 rounded-lg">
            حامیان ({{ formatCurrency(donorsCount) }})
          </TabsTrigger>
          <TabsTrigger 
            value="transparency" 
            class="text-[11px] font-bold h-7 rounded-lg"
            :disabled="status !== 'executed' || !transparency?.isAvailable"
          >
            شفافیت
          </TabsTrigger>
        </TabsList>

        <!-- Tab 1: Overview -->
        <TabsContent value="overview" class="pt-2.5 focus-visible:outline-none">
          <p class="text-xs text-muted-foreground leading-relaxed whitespace-pre-line line-clamp-3">
            {{ description }}
          </p>
        </TabsContent>

        <!-- Tab 2: Recent Donors List -->
        <TabsContent value="donors" class="pt-2.5 focus-visible:outline-none">
          <div v-if="recentDonors && recentDonors.length > 0" class="max-h-40 overflow-y-auto flex flex-col gap-1.5 pr-0.5 scrollbar-thin">
            <div 
              v-for="donor in recentDonors" 
              :key="donor.id" 
              class="flex items-center justify-between p-2 rounded-xl bg-muted/30 border border-border/30 text-xs"
            >
              <div class="flex items-center gap-2 min-w-0">
                <Avatar class="size-6 border border-border/50 shrink-0">
                  <AvatarImage v-if="!donor.isAnonymous && donor.avatarUrl" :src="donor.avatarUrl" :alt="donor.name" />
                  <AvatarFallback class="bg-primary/10 text-primary font-bold text-[9px]">
                    <UserIcon v-if="donor.isAnonymous" class="size-2.5 text-muted-foreground" />
                    <span v-else>{{ donor.name.substring(0, 2) }}</span>
                  </AvatarFallback>
                </Avatar>
                <div class="flex flex-col min-w-0">
                  <span class="font-bold text-foreground text-[11px] truncate">
                    {{ donor.isAnonymous ? 'کاربر ناشناس' : donor.name }}
                  </span>
                  <span class="text-[9.5px] text-muted-foreground font-medium">{{ donor.donatedAt }}</span>
                </div>
              </div>
              <div class="font-bold text-primary shrink-0 text-[11px]">
                {{ formatCurrency(donor.amount) }} <span class="text-[9px] font-normal text-muted-foreground">تومان</span>
              </div>
            </div>
          </div>
          <div v-else class="py-5 text-center text-muted-foreground text-xs bg-muted/20 rounded-2xl border border-dashed border-border/50">
            هنوز مشارکتی برای این پویش ثبت نشده است.
          </div>
        </TabsContent>

        <!-- Tab 3: Transparency Report -->
        <TabsContent value="transparency" class="pt-2.5 flex flex-col gap-2.5 focus-visible:outline-none text-xs">
          <template v-if="transparency && transparency.isAvailable">
            <div class="p-2.5 rounded-2xl bg-muted/40 border border-border/60 flex flex-col gap-1">
              <div class="flex items-center justify-between font-bold text-foreground text-[11px]">
                <span class="flex items-center gap-1.5">
                  <CheckCircle2Icon class="size-3 text-primary" />
                  گزارش رسمی اجرای پویش
                </span>
                <span v-if="transparency.executedAt" class="font-normal text-muted-foreground text-[10px]">{{ transparency.executedAt }}</span>
              </div>
              <p class="text-muted-foreground leading-relaxed text-xs line-clamp-3">{{ transparency.description }}</p>
            </div>

            <!-- Cost Breakdown Table -->
            <div v-if="transparency.costBreakdown" class="flex flex-col gap-1">
              <span class="font-bold text-foreground text-[11px] flex items-center gap-1">
                <FileTextIcon class="size-3 text-primary" />
                ریز هزینه‌ها:
              </span>
              <div class="rounded-xl border border-border/50 overflow-hidden text-[11px]">
                <table class="w-full text-right border-collapse">
                  <thead>
                    <tr class="bg-muted/70 text-muted-foreground border-b border-border/50 font-semibold text-[10.5px]">
                      <th class="p-1.5 pr-2.5">شرح هزینه</th>
                      <th class="p-1.5 pl-2.5 text-left">مبلغ (تومان)</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-border/30">
                    <tr 
                      v-for="(cost, item) in transparency.costBreakdown" 
                      :key="item"
                      class="hover:bg-muted/30"
                    >
                      <td class="p-1.5 pr-2.5 text-foreground font-medium truncate max-w-[130px]">{{ item }}</td>
                      <td class="p-1.5 pl-2.5 text-left font-bold text-primary">
                        {{ formatCurrency(cost) }}
                      </td>
                    </tr>
                    <tr class="bg-muted/40 font-bold border-t border-border/60">
                      <td class="p-1.5 pr-2.5 text-foreground">جمع کل</td>
                      <td class="p-1.5 pl-2.5 text-left text-primary">
                        {{ formatCurrency(totalTransparencyCost) }}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <!-- Receipt Images -->
            <div v-if="transparency.receiptImages && transparency.receiptImages.length > 0" class="flex flex-col gap-1">
              <span class="font-bold text-foreground text-[11px] flex items-center gap-1">
                <ImageIcon class="size-3 text-primary" />
                تصاویر فاکتورها:
              </span>
              <div class="grid grid-cols-3 gap-1.5">
                <div 
                  v-for="(receipt, idx) in transparency.receiptImages" 
                  :key="idx" 
                  class="relative aspect-square rounded-xl overflow-hidden border border-border/50 group cursor-pointer"
                  @click="emit('transparency-click', idx, receipt)"
                >
                  <img 
                    :src="receipt" 
                    :alt="`فاکتور ${idx + 1}`" 
                    class="w-full h-full object-cover transition-transform group-hover:scale-105"
                  />
                  <div class="absolute inset-0 bg-background/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center text-foreground text-[10px] font-semibold rounded-xl">
                    مشاهده
                  </div>
                </div>
              </div>
            </div>
          </template>

          <template v-else>
            <div class="py-5 text-center text-muted-foreground text-xs bg-muted/20 rounded-2xl border border-dashed border-border/50">
              گزارش شفافیت برای این پویش هنوز ثبت نشده است.
            </div>
          </template>
        </TabsContent>
      </Tabs>
    </CardContent>

    <Separator class="bg-border/50" />

    <!-- 5. ACTIONS FOOTER BAR -->
    <CardFooter class="p-3 bg-muted/20 border-t border-border/50 flex items-center justify-between gap-2">
      <!-- 1. Active State Action -->
      <Button 
        v-if="status === 'active'"
        variant="default"
        size="sm"
        class="h-9 px-3 text-xs font-bold rounded-xl shadow-md shadow-primary/20 active:scale-95 transition-all cursor-pointer flex-1"
        @click="emit('donate-click', id)"
      >
        <HeartIcon class="fill-current size-3.5" data-icon="inline-start" />
        <span>مشارکت در این مهربانی</span>
      </Button>

      <!-- 2. Inactive / Stopped State Action -->
      <Button 
        v-else-if="status === 'inactive'"
        variant="secondary" 
        disabled 
        size="sm"
        class="h-9 px-3 text-xs font-bold rounded-xl shadow-none flex-1 opacity-70 bg-muted text-muted-foreground border border-border/40"
      >
        <BanIcon class="size-3.5" data-icon="inline-start" />
        <span>پویش متوقف و غیرفعال شد</span>
      </Button>

      <!-- 3. Completed or Executed Action -->
      <Button 
        v-else
        variant="secondary" 
        disabled 
        size="sm"
        class="h-9 px-3 text-xs font-bold rounded-xl shadow-none flex-1 opacity-90"
      >
        <CheckCircle2Icon v-if="status === 'executed'" class="size-3.5" data-icon="inline-start" />
        <span>{{ status === 'executed' ? 'پایان و اجرای پویش' : 'تکمیل شده' }}</span>
      </Button>

      <!-- Edit Campaign Button -->
      <Button 
        v-if="canEdit && status !== 'inactive'"
        variant="outline" 
        size="icon" 
        class="size-9 rounded-xl border-border/70 dark:border-border/60 hover:bg-muted/50 text-primary hover:text-primary shrink-0 cursor-pointer shadow-none active:scale-95 transition-all"
        @click="emit('edit-click', id)"
        title="ویرایش پویش"
      >
        <PencilIcon class="size-3.5" />
      </Button>

      <!-- Delete / Purge Campaign Button (Clickable -> Opens Confirmation Modal) -->
      <Button 
        v-if="canEdit && status !== 'inactive'"
        variant="outline" 
        size="icon" 
        class="size-9 rounded-xl border-border/70 dark:border-border/60 shrink-0 shadow-none transition-all text-destructive hover:text-destructive hover:bg-destructive/10 cursor-pointer border-destructive/30 active:scale-95"
        @click="emit('delete-click', id)"
        :title="hasDonations ? 'متوقف‌سازی و غیرفعال‌کردن پویش' : 'پاکسازی و حذف کامل اهدا'"
      >
        <Trash2Icon class="size-3.5" />
      </Button>

      <!-- Share Button -->
      <Button 
        variant="outline" 
        size="icon" 
        class="size-9 rounded-xl border-border/70 dark:border-border/60 hover:bg-muted/50 text-muted-foreground hover:text-foreground shrink-0 cursor-pointer shadow-none active:scale-95 transition-all"
        @click="emit('share-click', id)"
        title="اشتراک‌گذاری"
      >
        <Share2Icon class="size-3.5" />
      </Button>
    </CardFooter>

  </Card>
</template>
