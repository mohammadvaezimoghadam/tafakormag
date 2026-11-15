<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useLanguageStore } from '@/stores/languageStore'
import { useUserStore } from '@/stores/userStore'
import { useToastStore } from '@/stores/toastStore'
import {
  extractApiErrorMessage,
  listBookDonations,
  listBookStations,
} from '@/api/shelf'
import type {
  BookStationSummary,
  DonationMethod,
  HomeMarketplaceItem,
} from '@/types/shelf'
import DonateBookFromShelfDialog from './DonateBookFromShelfDialog.vue'
import BookDonationDetailDialog from './BookDonationDetailDialog.vue'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import {
  BookOpenIcon,
  HandHeartIcon,
  MapPinIcon,
  PackageIcon,
  PlusIcon,
  QrCodeIcon,
  SearchIcon,
  SmartphoneIcon,
} from '@lucide/vue'

const props = withDefaults(
  defineProps<{
    headerSearchQuery?: string
    initialScanCode?: string
  }>(),
  {
    headerSearchQuery: '',
    initialScanCode: '',
  }
)

const emit = defineEmits<{
  (e: 'changed'): void
  (e: 'clear-scan-code'): void
}>()

const languageStore = useLanguageStore()
const userStore = useUserStore()
const toastStore = useToastStore()

const donations = ref<HomeMarketplaceItem[]>([])
const stations = ref<BookStationSummary[]>([])
const isLoading = ref(true)
const selectedMethod = ref<DonationMethod | ''>('')
const localSearch = ref('')

const isAddDonateOpen = ref(false)
const isDetailOpen = ref(false)
const selectedItem = ref<HomeMarketplaceItem | null>(null)
const activeScanShortCode = ref('')
const lookupMode = ref(false)

let searchDebounce: ReturnType<typeof setTimeout> | null = null

const hasAuthSession = computed(
  () => userStore.isAuthenticated || Boolean(localStorage.getItem('auth_token'))
)

const methodFilters: {
  value: DonationMethod | ''
  faLabel: string
  enLabel: string
  icon?: typeof QrCodeIcon
}[] = [
  { value: '', faLabel: 'همه انواع اهدا', enLabel: 'All Types' },
  { value: 'in_person', faLabel: 'حضوری (QR)', enLabel: 'In-Person (QR)', icon: QrCodeIcon },
  { value: 'postal', faLabel: 'ارسال پستی', enLabel: 'Postal', icon: PackageIcon },
  { value: 'station', faLabel: 'ایستگاه تفاخر', enLabel: 'Book Stations', icon: MapPinIcon },
  { value: 'digital', faLabel: 'نسخه دیجیتال', enLabel: 'Digital', icon: SmartphoneIcon },
]

const effectiveSearch = computed(() =>
  (localSearch.value || props.headerSearchQuery || '').trim()
)

const resolveMediaUrl = (raw?: string | null): string | null => {
  if (!raw) return null
  if (raw.startsWith('http://') || raw.startsWith('https://') || raw.startsWith('/')) {
    return raw
  }
  return `/${raw}`
}

const getMethodsForItem = (item: HomeMarketplaceItem): DonationMethod[] => {
  if (item.donation_methods?.length) return item.donation_methods
  if (item.delivery_type === 'digital') return ['digital']
  if (item.station_summary) return ['station']
  if (item.physical_copy_summary) return ['in_person']
  return ['postal']
}

const methodBadge = (item: HomeMarketplaceItem, method: DonationMethod) => {
  if (method === 'in_person') {
    const code = item.physical_copy_summary?.short_code
    return {
      icon: QrCodeIcon,
      label: code ? `حضوری (${code})` : languageStore.t('حضوری (QR)', 'In-Person (QR)'),
    }
  }
  if (method === 'postal') {
    return {
      icon: PackageIcon,
      label: languageStore.t('ارسال پستی', 'Postal'),
    }
  }
  if (method === 'station') {
    return {
      icon: MapPinIcon,
      label: item.station_summary?.name
        ? languageStore.t(`ایستگاه: ${item.station_summary.name}`, `Station: ${item.station_summary.name}`)
        : languageStore.t('ایستگاه تفاخر', 'Book Station'),
    }
  }
  return {
    icon: SmartphoneIcon,
    label: languageStore.t('نسخه دیجیتال', 'Digital'),
  }
}

const loadDonations = async () => {
  isLoading.value = true
  try {
    const [itemsData, stationsData] = await Promise.all([
      listBookDonations({
        search: effectiveSearch.value,
        donation_method: selectedMethod.value,
      }),
      stations.value.length ? Promise.resolve(stations.value) : listBookStations().catch(() => []),
    ])
    donations.value = itemsData
    stations.value = stationsData
  } catch (err) {
    toastStore.triggerToast(
      extractApiErrorMessage(err, languageStore.t('خطا در دریافت لیست کتاب‌های اهدایی', 'Failed to load donated books')),
      'error'
    )
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  loadDonations()
})

watch(
  () => props.headerSearchQuery,
  () => {
    if (!localSearch.value) {
      loadDonations()
    }
  }
)

const selectMethod = (val: DonationMethod | '') => {
  if (selectedMethod.value === val) return
  selectedMethod.value = val
  loadDonations()
}

const handleSearchInput = () => {
  if (searchDebounce) clearTimeout(searchDebounce)
  searchDebounce = setTimeout(() => {
    loadDonations()
  }, 300)
}

const handleOpenDonateModal = () => {
  if (!hasAuthSession.value) {
    toastStore.triggerToast(
      languageStore.t('برای ثبت اهدای کتاب ابتدا وارد حساب کاربری خود شوید', 'Please sign in to donate a book'),
      'info'
    )
    userStore.isLoginModalOpen = true
    return
  }
  isAddDonateOpen.value = true
}

const handleOpenBookDetail = (item: HomeMarketplaceItem) => {
  lookupMode.value = false
  activeScanShortCode.value = ''
  selectedItem.value = item
  isDetailOpen.value = true
}

const handleOpenQrLookup = () => {
  lookupMode.value = true
  activeScanShortCode.value = ''
  selectedItem.value = null
  isDetailOpen.value = true
}

const handleOpenHandoverByCode = (shortCode: string) => {
  const cleaned = (shortCode || '').trim()
  if (!cleaned) return
  lookupMode.value = true
  selectedItem.value = null
  activeScanShortCode.value = cleaned
  isDetailOpen.value = true
}

const isMyDonationItem = (item: HomeMarketplaceItem): boolean => {
  if (!item.seller || !userStore.userProfile?.id) return false
  return Number(item.seller) === Number(userStore.userProfile.id)
}

watch(
  () => props.initialScanCode,
  (code) => {
    const trimmed = (code || '').trim()
    if (!trimmed) return
    handleOpenHandoverByCode(trimmed)
  },
  { immediate: true }
)

watch(isDetailOpen, (open) => {
  if (!open && props.initialScanCode) {
    emit('clear-scan-code')
  }
})

const handleMutated = async () => {
  await Promise.allSettled([loadDonations(), userStore.loadProfile()])
  emit('changed')
}
</script>

<template>
  <div class="flex flex-col gap-4 pb-24 w-full">
    <!-- Top Banner & CTAs -->
    <Card class="rounded-3xl border-border/60 shadow-xs py-4">
      <CardContent class="px-4 flex flex-col gap-3.5">
        <div class="flex items-start gap-3">
          <div class="size-10 rounded-2xl bg-primary/10 text-primary flex items-center justify-center shrink-0">
            <HandHeartIcon class="size-5" />
          </div>
          <div class="flex-1 min-w-0 flex flex-col gap-1">
            <h2 class="text-sm font-extrabold text-foreground">
              {{ languageStore.t('کتاب‌های اهدایی همراهان تفاخر', 'Community Book Donations') }}
            </h2>
            <p class="text-xs text-muted-foreground leading-relaxed">
              {{
                languageStore.t(
                  'کتاب‌ها را بر اساس روش تحویل (حضوری با کد گردش QR، ارسال پستی، ایستگاه‌های تفاخر یا نسخه دیجیتال) جستجو و دریافت کنید یا کتاب خود را اهدا نمایید.',
                  'Browse free donated books by handover type (In-Person QR, Postal, Book Stations, Digital) or donate one from your shelf.'
                )
              }}
            </p>
          </div>
        </div>

        <div class="flex items-center gap-2 flex-wrap">
          <Button type="button" size="sm" class="rounded-2xl" @click="handleOpenDonateModal">
            <PlusIcon data-icon="inline-start" />
            <span>{{ languageStore.t('اهدای کتاب من', 'Donate My Book') }}</span>
          </Button>
          <Button type="button" size="sm" variant="outline" class="rounded-2xl" @click="handleOpenQrLookup">
            <QrCodeIcon data-icon="inline-start" />
            <span>{{ languageStore.t('کد گردش QR / تحویل حضوری', 'Enter QR Code') }}</span>
          </Button>
        </div>
      </CardContent>
    </Card>

    <!-- Search & Donation Type Chips -->
    <div class="flex flex-col gap-2.5">
      <div class="relative">
        <SearchIcon class="size-4 text-muted-foreground absolute top-1/2 -translate-y-1/2 start-3.5 pointer-events-none" />
        <Input
          v-model="localSearch"
          class="ps-10 h-10 bg-card border-border/60 rounded-2xl"
          :placeholder="languageStore.t('جستجو در عنوان کتاب، نویسنده یا ناشر...', 'Search title, author, or publisher...')"
          @input="handleSearchInput"
        />
      </div>

      <div class="flex items-center gap-1.5 overflow-x-auto pb-1 no-scrollbar">
        <Button
          v-for="f in methodFilters"
          :key="f.value"
          type="button"
          size="xs"
          :variant="selectedMethod === f.value ? 'default' : 'outline'"
          class="rounded-full shrink-0 gap-1"
          @click="selectMethod(f.value)"
        >
          <component v-if="f.icon" :is="f.icon" class="size-3" />
          <span>{{ languageStore.t(f.faLabel, f.enLabel) }}</span>
        </Button>
      </div>
    </div>

    <!-- Active Stations Directory (shown on Station filter) -->
    <Card
      v-if="selectedMethod === 'station' && stations.length > 0"
      class="rounded-3xl border-border/60 bg-muted/20 py-3"
    >
      <CardContent class="px-4 flex flex-col gap-2">
        <span class="text-xs font-extrabold text-foreground flex items-center gap-1.5">
          <MapPinIcon class="size-3.5 text-primary" />
          <span>{{ languageStore.t('ایستگاه‌ها و قفسه‌های فعال کتاب تفاخر', 'Active Tafakor Book Stations') }}</span>
        </span>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
          <div
            v-for="st in stations"
            :key="st.id"
            class="rounded-2xl bg-card border border-border/50 px-3 py-2 flex flex-col gap-0.5"
          >
            <div class="flex items-center justify-between gap-2">
              <span class="text-xs font-bold text-foreground">{{ st.name }}</span>
              <Badge variant="outline" class="text-[10px]">{{ st.city_name }}</Badge>
            </div>
            <span class="text-[11px] text-muted-foreground line-clamp-2">{{ st.address_text }}</span>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- Loading Skeleton -->
    <div v-if="isLoading" class="grid grid-cols-1 sm:grid-cols-2 gap-3">
      <Card v-for="n in 4" :key="n" class="rounded-3xl border-border/50 py-3">
        <CardContent class="px-3 flex gap-3">
          <Skeleton class="w-16 h-24 rounded-2xl shrink-0" />
          <div class="flex-1 flex flex-col gap-2">
            <Skeleton class="h-4 w-3/4" />
            <Skeleton class="h-3 w-1/2" />
            <Skeleton class="h-5 w-24 rounded-full" />
          </div>
        </CardContent>
      </Card>
    </div>

    <!-- Empty State -->
    <Card v-else-if="donations.length === 0" class="rounded-3xl border-dashed border-border/70 py-8">
      <CardContent class="px-6 flex flex-col items-center text-center gap-3">
        <div class="size-12 rounded-2xl bg-muted flex items-center justify-center text-muted-foreground">
          <BookOpenIcon class="size-6" />
        </div>
        <div class="flex flex-col gap-1 max-w-sm">
          <span class="text-sm font-bold text-foreground">
            {{
              selectedMethod || effectiveSearch
                ? languageStore.t('کتاب اهدایی با این فیلتر یافت نشد', 'No donated books match this filter')
                : languageStore.t('هنوز کتابی برای اهدا ثبت نشده است', 'No donated books available yet')
            }}
          </span>
          <span class="text-xs text-muted-foreground leading-relaxed">
            {{
              languageStore.t(
                'می‌توانید اولین نفری باشید که یک کتاب از قفسه خود را به صورت حضوری، پستی یا در ایستگاه اهدا می‌کند.',
                'Be the first to donate a book in-person, by post, or via a station.'
              )
            }}
          </span>
        </div>
        <div class="flex items-center gap-2">
          <Button
            v-if="selectedMethod || localSearch"
            type="button"
            variant="outline"
            size="sm"
            @click="selectedMethod = ''; localSearch = ''; loadDonations()"
          >
            {{ languageStore.t('نمایش همه', 'Show All') }}
          </Button>
          <Button type="button" size="sm" @click="handleOpenDonateModal">
            <PlusIcon data-icon="inline-start" />
            <span>{{ languageStore.t('اهدای کتاب من', 'Donate My Book') }}</span>
          </Button>
        </div>
      </CardContent>
    </Card>

    <!-- Book Donations Grid -->
    <div v-else class="grid grid-cols-1 sm:grid-cols-2 gap-3">
      <Card
        v-for="item in donations"
        :key="item.id"
        class="rounded-3xl border-border/60 hover:border-primary/40 shadow-xs transition-all cursor-pointer py-3 flex flex-col justify-between"
        @click="handleOpenBookDetail(item)"
      >
        <CardContent class="px-3.5 flex flex-col gap-3 flex-1 justify-between">
          <div class="flex items-start gap-3">
            <div class="w-16 h-24 rounded-2xl overflow-hidden bg-muted/50 border border-border/50 flex items-center justify-center shrink-0">
              <img
                v-if="resolveMediaUrl(item.cover_image)"
                :src="resolveMediaUrl(item.cover_image)!"
                :alt="item.title"
                class="size-full object-cover"
              />
              <BookOpenIcon v-else class="size-6 text-muted-foreground/70" />
            </div>

            <div class="flex-1 min-w-0 flex flex-col gap-1">
              <h3 class="text-xs font-extrabold text-foreground line-clamp-2 leading-snug">
                {{ item.title }}
              </h3>
              <p class="text-[11px] text-muted-foreground truncate">
                {{ item.author || item.category_name }}
              </p>
              <p class="text-[10.5px] text-muted-foreground/85 truncate">
                {{ languageStore.t('اهداکننده:', 'Donor:') }} {{ item.seller_name }}
              </p>

              <!-- Donation Methods Badges -->
              <div class="flex items-center gap-1 flex-wrap pt-1">
                <Badge
                  v-for="m in getMethodsForItem(item)"
                  :key="m"
                  variant="secondary"
                  class="gap-1 px-1.5 py-0.5 text-[10px]"
                >
                  <component :is="methodBadge(item, m).icon" class="size-2.5 text-primary shrink-0" />
                  <span class="truncate max-w-[125px]">{{ methodBadge(item, m).label }}</span>
                </Badge>
              </div>
            </div>
          </div>

          <div class="flex items-center justify-between gap-2 pt-2 border-t border-border/40">
            <div class="flex items-center gap-1.5 min-w-0">
              <span class="text-[11px] font-bold text-primary">
                {{ languageStore.t('اهدای رایگان', 'Free Donation') }}
              </span>
              <Badge v-if="isMyDonationItem(item)" variant="outline" class="text-[9.5px] px-1.5 py-0">
                {{ languageStore.t('کتاب شما', 'Yours') }}
              </Badge>
            </div>
            <Button type="button" size="xs" variant="outline" class="rounded-xl shrink-0">
              {{
                isMyDonationItem(item)
                  ? languageStore.t('کد QR / تحویل', 'QR & Handover')
                  : languageStore.t('جزئیات و تحویل', 'View & Claim')
              }}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>

    <!-- Donate Book Dialog (select from personal shelf + optional mini button to register a new book) -->
    <DonateBookFromShelfDialog
      v-model:open="isAddDonateOpen"
      @donated="handleMutated"
      @open-handover="handleOpenHandoverByCode"
    />

    <!-- Detail / Request / QR Handover Dialog -->
    <BookDonationDetailDialog
      v-model:open="isDetailOpen"
      :item="selectedItem"
      :initial-short-code="activeScanShortCode"
      :code-lookup-mode="lookupMode"
      @changed="handleMutated"
    />
  </div>
</template>

