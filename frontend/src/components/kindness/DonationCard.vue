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
import { 
  HeartIcon, 
  UserIcon, 
  CheckCircle2Icon, 
  FileTextIcon, 
  ImageIcon,
  SparklesIcon,
  HandHeartIcon
} from '@lucide/vue'

const props = defineProps<DonationCampaignProps>()

const emit = defineEmits<{
  (e: 'donate-click', campaignId: string | number): void
  (e: 'topic-click', topicId: string | number): void
  (e: 'transparency-click', imageIndex: number, imageUrl: string): void
}>()

// Active Media Index for Bento Gallery
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

// Animated Completion Percentage
const completionPercentage = computed(() => {
  if (!props.targetAmount || props.targetAmount <= 0) return 0
  const pct = Math.round((props.collectedAmount / props.targetAmount) * 100)
  return Math.min(100, Math.max(0, pct))
})

// Status Badge Configuration
const statusConfig = computed(() => {
  switch (props.status) {
    case 'active':
      return {
        label: 'در حال جمع‌آوری',
        badgeClass: 'bg-primary text-primary-foreground font-medium'
      }
    case 'completed':
      return {
        label: 'ظرفیت تکمیل شده',
        badgeClass: 'bg-secondary text-secondary-foreground font-medium'
      }
    case 'executed':
      return {
        label: 'اجرا شده و شفاف',
        badgeClass: 'bg-accent text-accent-foreground border-border font-medium'
      }
    default:
      return {
        label: 'فعال',
        badgeClass: 'bg-primary text-primary-foreground font-medium'
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
  <Card class="w-full max-w-md mx-auto overflow-hidden border-border bg-card text-card-foreground shadow-xs transition-all hover:shadow-sm dir-rtl text-right rounded-2xl">
    
    <!-- Uniform Outer Padding Container (p-3 Equal All Around) -->
    <div class="p-3">
      <!-- Bento Grid Gallery Container (No background color) -->
      <template v-if="mediaGallery && mediaGallery.length > 0">
        <!-- Single Image Layout -->
        <div v-if="mediaGallery.length === 1" class="relative w-full aspect-[2.4/1] sm:aspect-[2.8/1] rounded-xl overflow-hidden border border-border/40">
          <img 
            :src="mediaGallery[0]" 
            :alt="title" 
            class="w-full h-full object-cover" 
          />
          <!-- Status Badge -->
          <div class="absolute top-2 right-2 z-20">
            <Badge :class="statusConfig.badgeClass" class="px-2.5 py-0.5 text-xs shadow-xs border-0 rounded-full backdrop-blur-md font-medium">
              <span v-if="status === 'executed'" class="inline-flex items-center gap-1">
                <CheckCircle2Icon class="size-3" />
                {{ statusConfig.label }}
              </span>
              <span v-else>
                {{ statusConfig.label }}
              </span>
            </Badge>
          </div>
        </div>

        <!-- Bento Grid 2-Section Layout: Right (Big Image) + Left (2x2 Grid of 4 Images) with gap-1 (4px) -->
        <div v-else class="grid grid-cols-12 gap-1 w-full aspect-[2.2/1] sm:aspect-[2.6/1] relative">
          
          <!-- Status Badge (Positioned on top right of the big main image) -->
          <div class="absolute top-2 right-2 z-20">
            <Badge :class="statusConfig.badgeClass" class="px-2.5 py-0.5 text-xs shadow-xs border-0 rounded-full backdrop-blur-md font-medium">
              <span v-if="status === 'executed'" class="inline-flex items-center gap-1">
                <CheckCircle2Icon class="size-3" />
                {{ statusConfig.label }}
              </span>
              <span v-else>
                {{ statusConfig.label }}
              </span>
            </Badge>
          </div>

          <!-- Right Section: Big Featured Image (Takes 7/12 cols) with rounded-xl border -->
          <div class="col-span-7 h-full relative rounded-xl overflow-hidden border border-border/40">
            <img 
              :src="mediaGallery[currentMediaIndex]" 
              :alt="title" 
              class="w-full h-full object-cover transition-all duration-300"
            />
          </div>

          <!-- Left Section: 4 Thumbnails in 2x2 Grid (Takes 5/12 cols, 4px gap) -->
          <div class="col-span-5 h-full grid grid-cols-2 grid-rows-2 gap-1">
            <div 
              v-for="(img, idx) in mediaGallery.slice(0, 4)" 
              :key="idx"
              class="relative h-full overflow-hidden rounded-lg cursor-pointer group border border-border/30"
              :class="idx === currentMediaIndex ? 'ring-2 ring-primary border-primary' : 'opacity-80 hover:opacity-100'"
              @click="selectMedia(idx)"
            >
              <img 
                :src="img" 
                :alt="`تصویر ${idx + 1}`" 
                class="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105" 
              />
              
              <!-- Count Overlay if Gallery > 4 -->
              <div 
                v-if="idx === 3 && mediaGallery.length > 4" 
                class="absolute inset-0 bg-black/60 backdrop-blur-xs flex items-center justify-center text-white text-xs font-bold rounded-lg"
              >
                +{{ mediaGallery.length - 4 }}
              </div>
            </div>
          </div>

        </div>
      </template>

      <template v-else>
        <!-- Media Placeholder -->
        <div class="w-full aspect-[2.6/1] flex flex-col items-center justify-center gap-1 text-muted-foreground rounded-xl border border-border/40">
          <HandHeartIcon class="size-8 stroke-[1.5]" />
          <span class="text-xs font-medium">پویش مهربانی</span>
        </div>
      </template>
    </div>

    <!-- Card Header (Equal Padding) -->
    <CardHeader class="p-3 pt-0 space-y-2">
      <!-- Category Badge & Topic Link -->
      <div class="flex items-center gap-1.5 flex-wrap">
        <Badge 
          variant="outline" 
          class="bg-accent/40 text-accent-foreground border-accent-foreground/20 hover:bg-accent cursor-pointer transition-colors text-xs font-medium px-2.5 py-0.5 rounded-lg"
          @click="emit('topic-click', topicId)"
        >
          <span>{{ category }}</span>
          <span class="mx-1 opacity-50">•</span>
          <span class="font-semibold">{{ topicName }}</span>
        </Badge>
      </div>

      <!-- Campaign Title -->
      <CardTitle class="text-base sm:text-lg font-bold leading-snug text-foreground line-clamp-2">
        {{ title }}
      </CardTitle>
    </CardHeader>

    <!-- Card Content (Tabs) -->
    <CardContent class="p-3 pt-0 space-y-3">
      <Tabs default-value="overview" class="w-full">
        <TabsList class="grid w-full grid-cols-3 mb-3 bg-muted/60 p-1 rounded-xl h-9">
          <TabsTrigger value="overview" class="text-xs font-semibold h-7 px-1 rounded-lg">
            معرفی
          </TabsTrigger>
          <TabsTrigger value="donors" class="text-xs font-semibold h-7 px-1 rounded-lg">
            حامیان ({{ formatCurrency(donorsCount) }})
          </TabsTrigger>
          <TabsTrigger 
            value="transparency" 
            class="text-xs font-semibold h-7 px-1 rounded-lg"
            :disabled="status !== 'executed' || !transparency?.isAvailable"
          >
            شفافیت
          </TabsTrigger>
        </TabsList>

        <!-- Tab 1: Overview -->
        <TabsContent value="overview" class="space-y-3 focus-visible:outline-none">
          <p class="text-xs sm:text-sm text-muted-foreground leading-relaxed whitespace-pre-line line-clamp-3">
            {{ description }}
          </p>

          <!-- Funding Progress Container -->
          <div class="space-y-2 bg-muted/30 p-2.5 sm:p-3 rounded-xl border border-border/50">
            <!-- Progress Amounts Readout -->
            <div class="flex flex-wrap items-baseline justify-between gap-1 text-xs">
              <div class="flex items-baseline gap-1">
                <span class="text-xs text-muted-foreground">جمع‌آوری شده:</span>
                <span class="font-bold text-primary text-xs sm:text-sm">
                  {{ formatCurrency(collectedAmount) }}
                </span>
                <span class="text-[11px] text-muted-foreground">تومان</span>
              </div>

              <div class="flex items-center gap-1 text-xs">
                <span class="text-muted-foreground">هدف:</span>
                <span class="font-semibold text-foreground">
                  {{ formatCurrency(targetAmount) }}
                </span>
                <span class="text-muted-foreground">تومان</span>
              </div>
            </div>

            <!-- Progress Bar -->
            <div class="relative">
              <Progress :model-value="completionPercentage" class="h-2 w-full bg-muted rounded-full" />
            </div>

            <!-- Percentage Footer -->
            <div class="flex justify-between items-center text-xs text-muted-foreground pt-0.5">
              <span class="flex items-center gap-1">
                <SparklesIcon class="size-3.5 text-primary" />
                <span>{{ formatCurrency(donorsCount) }} حامی</span>
              </span>
              <span class="font-bold text-primary bg-primary/10 px-2 py-0.5 rounded-full text-xs">
                {{ formatCurrency(completionPercentage) }}٪ پیشرفت
              </span>
            </div>
          </div>
        </TabsContent>

        <!-- Tab 2: Recent Donors -->
        <TabsContent value="donors" class="focus-visible:outline-none">
          <div v-if="recentDonors && recentDonors.length > 0" class="max-h-52 overflow-y-auto space-y-2 pl-0.5">
            <div 
              v-for="donor in recentDonors" 
              :key="donor.id" 
              class="flex items-center justify-between p-2 sm:p-2.5 rounded-xl bg-muted/30 border border-border/40 hover:bg-muted/50 transition-colors"
            >
              <div class="flex items-center gap-2.5 min-w-0">
                <Avatar class="size-8 border border-border shrink-0">
                  <AvatarImage 
                    v-if="!donor.isAnonymous && donor.avatarUrl" 
                    :src="donor.avatarUrl" 
                    :alt="donor.name" 
                  />
                  <AvatarFallback class="bg-primary/10 text-primary font-medium text-xs">
                    <UserIcon v-if="donor.isAnonymous" class="size-3.5 text-muted-foreground" />
                    <span v-else>{{ donor.name.substring(0, 2) }}</span>
                  </AvatarFallback>
                </Avatar>

                <div class="flex flex-col min-w-0">
                  <span class="text-xs sm:text-sm font-semibold text-foreground truncate">
                    {{ donor.isAnonymous ? 'کاربر ناشناس' : donor.name }}
                  </span>
                  <span class="text-[11px] text-muted-foreground">
                    {{ donor.donatedAt }}
                  </span>
                </div>
              </div>

              <div class="text-xs sm:text-sm font-bold text-primary flex items-center gap-1 shrink-0">
                <span>{{ formatCurrency(donor.amount) }}</span>
                <span class="text-xs font-normal text-muted-foreground">تومان</span>
              </div>
            </div>
          </div>

          <div v-else class="py-6 text-center text-muted-foreground text-xs bg-muted/20 rounded-xl border border-dashed border-border">
            هنوز مشارکتی برای این پویش ثبت نشده است.
          </div>
        </TabsContent>

        <!-- Tab 3: Transparency Report -->
        <TabsContent value="transparency" class="space-y-3 focus-visible:outline-none">
          <template v-if="transparency && transparency.isAvailable">
            <!-- Execution Summary Banner -->
            <div class="p-2.5 rounded-xl bg-accent/40 border border-accent-foreground/20 space-y-1">
              <div class="flex items-center justify-between text-xs font-semibold text-accent-foreground">
                <span class="flex items-center gap-1">
                  <CheckCircle2Icon class="size-3.5 text-primary" />
                  گزارش اجرای پویش
                </span>
                <span v-if="transparency.executedAt" class="text-muted-foreground font-normal text-xs">
                  {{ transparency.executedAt }}
                </span>
              </div>
              <p class="text-xs text-muted-foreground leading-relaxed line-clamp-3">
                {{ transparency.description }}
              </p>
            </div>

            <!-- Itemized Cost Breakdown Table -->
            <div v-if="transparency.costBreakdown && Object.keys(transparency.costBreakdown).length > 0" class="space-y-1.5">
              <span class="text-xs font-bold text-foreground flex items-center gap-1">
                <FileTextIcon class="size-3.5 text-primary" />
                ریز هزینه‌ها:
              </span>
              <div class="rounded-xl border border-border overflow-hidden text-xs">
                <table class="w-full text-right border-collapse">
                  <thead>
                    <tr class="bg-muted/70 text-muted-foreground border-b border-border font-medium text-xs">
                      <th class="p-2 pr-3">عنوان هزینه</th>
                      <th class="p-2 pl-3 text-left">مبلغ (تومان)</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-border/60">
                    <tr 
                      v-for="(cost, item) in transparency.costBreakdown" 
                      :key="item"
                      class="hover:bg-muted/30"
                    >
                      <td class="p-2 pr-3 text-foreground font-medium truncate max-w-[140px]">{{ item }}</td>
                      <td class="p-2 pl-3 text-left font-semibold text-primary">
                        {{ formatCurrency(cost) }}
                      </td>
                    </tr>
                    <tr class="bg-muted/40 font-bold border-t border-border">
                      <td class="p-2 pr-3 text-foreground">جمع کل</td>
                      <td class="p-2 pl-3 text-left text-primary">
                        {{ formatCurrency(totalTransparencyCost) }}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <!-- Receipts Gallery -->
            <div v-if="transparency.receiptImages && transparency.receiptImages.length > 0" class="space-y-1.5">
              <span class="text-xs font-bold text-foreground flex items-center gap-1">
                <ImageIcon class="size-3.5 text-primary" />
                فاکتورها:
              </span>
              <div class="grid grid-cols-3 gap-1.5">
                <div 
                  v-for="(receipt, idx) in transparency.receiptImages" 
                  :key="idx" 
                  class="relative aspect-square rounded-xl overflow-hidden border border-border group cursor-pointer"
                  @click="emit('transparency-click', idx, receipt)"
                >
                  <img 
                    :src="receipt" 
                    :alt="`فاکتور ${idx + 1}`" 
                    class="w-full h-full object-cover transition-transform group-hover:scale-110"
                  />
                  <div class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center text-white text-xs font-medium rounded-xl">
                    مشاهده
                  </div>
                </div>
              </div>
            </div>
          </template>

          <template v-else>
            <div class="py-6 text-center text-muted-foreground text-xs">
              گزارش شفافیت برای این پویش هنوز ثبت نشده است.
            </div>
          </template>
        </TabsContent>
      </Tabs>
    </CardContent>

    <Separator class="bg-border/60" />

    <!-- Card Footer (Equal Padding p-3) -->
    <CardFooter class="p-3 bg-muted/20 flex flex-col gap-1.5">
      <!-- Active Campaign Action Button -->
      <Button 
        v-if="status === 'active'"
        class="w-full h-10 text-xs sm:text-sm font-semibold rounded-xl gap-2 shadow-xs transition-all hover:shadow-sm cursor-pointer"
        @click="emit('donate-click', id)"
      >
        <HeartIcon class="size-4 fill-current text-primary-foreground" />
        <span>مشارکت در این مهربانی</span>
      </Button>

      <!-- Completed / Executed Campaign Action Button -->
      <Button 
        v-else
        variant="secondary" 
        disabled 
        class="w-full h-10 text-xs sm:text-sm font-semibold rounded-xl gap-2 opacity-80"
      >
        <CheckCircle2Icon v-if="status === 'executed'" class="size-4 text-primary" />
        <span>{{ status === 'executed' ? 'پایان و اجرای پویش' : 'ظرفیت تکمیل شده' }}</span>
      </Button>
    </CardFooter>
  </Card>
</template>
