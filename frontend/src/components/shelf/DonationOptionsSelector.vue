<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useLanguageStore } from '@/stores/languageStore'
import { listBookStations } from '@/api/shelf'
import type { BookStationSummary, DonationMethod, ShelfBookFormat, ShippingPayer } from '@/types/shelf'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Switch } from '@/components/ui/switch'
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  CheckIcon,
  MapPinIcon,
  PackageIcon,
  QrCodeIcon,
  SmartphoneIcon,
} from '@lucide/vue'

const props = withDefaults(
  defineProps<{
    bookFormat: ShelfBookFormat
    donationMethods: DonationMethod[]
    stationId: string
    depositNow: boolean
    shippingPayer: ShippingPayer
    categoryId: string
    description: string
    categories: { id: number; label: string }[]
    textareaMode?: boolean
    hideCategory?: boolean
    descriptionLabel?: string
    descriptionPlaceholder?: string
  }>(),
  {
    textareaMode: false,
    hideCategory: false,
    descriptionLabel: '',
    descriptionPlaceholder: '',
  }
)

const emit = defineEmits<{
  (e: 'update:donationMethods', value: DonationMethod[]): void
  (e: 'update:stationId', value: string): void
  (e: 'update:depositNow', value: boolean): void
  (e: 'update:shippingPayer', value: ShippingPayer): void
  (e: 'update:categoryId', value: string): void
  (e: 'update:description', value: string): void
}>()

const CATEGORY_AUTO = '__auto__'
const STATION_NONE = '__none__'

const languageStore = useLanguageStore()
const stations = ref<BookStationSummary[]>([])
const loadingStations = ref(false)

const isDigital = computed(() => props.bookFormat === 'digital')
const hasPostal = computed(() => !isDigital.value && props.donationMethods.includes('postal'))
const hasStation = computed(() => !isDigital.value && props.donationMethods.includes('station'))

const physicalOptions: {
  value: Exclude<DonationMethod, 'digital'>
  faTitle: string
  enTitle: string
  faDesc: string
  enDesc: string
  icon: typeof QrCodeIcon
}[] = [
  {
    value: 'in_person',
    faTitle: 'اهدای حضوری (کد QR)',
    enTitle: 'In-Person (QR Code)',
    faDesc: 'ملاقات حضوری و ثبت سفرنامه با کد TK',
    enDesc: 'Meetup handover with TK journey code',
    icon: QrCodeIcon,
  },
  {
    value: 'postal',
    faTitle: 'ارسال پستی',
    enTitle: 'Postal Shipping',
    faDesc: 'ثبت درخواست آدرس‌دار و کد رهگیری',
    enDesc: 'Ship by post after request approval',
    icon: PackageIcon,
  },
  {
    value: 'station',
    faTitle: 'ایستگاه تفاخر',
    enTitle: 'Book Station',
    faDesc: 'قرار دادن یا تحویل در قفسه عمومی',
    enDesc: 'Drop off at a public Tafakor kiosk',
    icon: MapPinIcon,
  },
]

const togglePhysicalMethod = (method: Exclude<DonationMethod, 'digital'>) => {
  if (isDigital.value) return
  const current = props.donationMethods.filter((m): m is Exclude<DonationMethod, 'digital'> => m !== 'digital')
  const exists = current.includes(method)
  let next: DonationMethod[]
  if (exists) {
    if (current.length === 1) return // Ensure at least one handover type remains active
    next = current.filter((m) => m !== method)
    if (method === 'station') {
      emit('update:stationId', STATION_NONE)
      emit('update:depositNow', false)
    }
  } else {
    next = [...current, method]
  }
  emit('update:donationMethods', next)
}

onMounted(async () => {
  loadingStations.value = true
  try {
    stations.value = await listBookStations()
  } catch {
    stations.value = []
  } finally {
    loadingStations.value = false
  }
})
</script>

<template>
  <div class="flex flex-col gap-3">
    <!-- Digital Donation Mode Notice -->
    <div
      v-if="isDigital"
      class="rounded-2xl border border-primary/25 bg-primary/5 px-3 py-2.5 flex items-center gap-2.5"
    >
      <div class="size-8 rounded-xl bg-primary/10 text-primary flex items-center justify-center shrink-0">
        <SmartphoneIcon class="size-4" />
      </div>
      <div class="flex flex-col gap-0.5 min-w-0">
        <span class="text-xs font-bold text-foreground">
          {{ languageStore.t('نوع اهدا: نسخه دیجیتال (الکترونیک)', 'Donation Type: Digital Copy') }}
        </span>
        <span class="text-[11px] text-muted-foreground leading-relaxed">
          {{
            languageStore.t(
              'پس از تایید درخواست گیرنده، دسترسی دیجیتال کتاب بدون نیاز به ارسال فیزیکی یا کد QR واگذار می‌شود.',
              'Digital access is granted directly upon accepting a recipient request.'
            )
          }}
        </span>
      </div>
    </div>

    <!-- Physical Donation Handover Types (Multi-Select) -->
    <div v-else class="flex flex-col gap-2">
      <div class="flex items-center justify-between gap-2">
        <Label class="text-xs font-bold text-foreground">
          {{ languageStore.t('انواع اهدای مجاز این کتاب', 'Allowed Donation Methods') }}
        </Label>
        <span class="text-[10.5px] text-muted-foreground">
          {{ languageStore.t('امکان انتخاب چند روش هم‌زمان', 'Multi-select') }}
        </span>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-3 gap-2">
        <button
          v-for="opt in physicalOptions"
          :key="opt.value"
          type="button"
          class="relative flex flex-col items-start gap-1 rounded-2xl border p-2.5 text-start transition-all cursor-pointer"
          :class="
            donationMethods.includes(opt.value)
              ? 'border-primary bg-primary/10 text-foreground shadow-xs'
              : 'border-border/60 bg-background/60 text-muted-foreground hover:bg-muted/40'
          "
          @click="togglePhysicalMethod(opt.value)"
        >
          <div class="flex items-center justify-between w-full gap-1.5">
            <component
              :is="opt.icon"
              class="size-4 shrink-0"
              :class="donationMethods.includes(opt.value) ? 'text-primary' : 'text-muted-foreground'"
            />
            <span
              class="size-4 rounded-full border flex items-center justify-center shrink-0"
              :class="
                donationMethods.includes(opt.value)
                  ? 'border-primary bg-primary text-primary-foreground'
                  : 'border-border bg-background'
              "
            >
              <CheckIcon v-if="donationMethods.includes(opt.value)" class="size-2.5" />
            </span>
          </div>
          <span class="text-[11.5px] font-bold leading-tight text-foreground mt-0.5">
            {{ languageStore.t(opt.faTitle, opt.enTitle) }}
          </span>
          <span class="text-[10px] leading-snug text-muted-foreground line-clamp-2">
            {{ languageStore.t(opt.faDesc, opt.enDesc) }}
          </span>
        </button>
      </div>
    </div>

    <!-- Postal Payer Preference (Shown when postal is selected) -->
    <div
      v-if="hasPostal"
      class="flex items-center justify-between gap-2 rounded-2xl border border-border/50 bg-background/50 px-3 py-2"
    >
      <Label class="text-xs font-semibold text-foreground shrink-0">
        {{ languageStore.t('هزینه ارسال پستی', 'Shipping Cost') }}
      </Label>
      <div class="flex items-center gap-1.5">
        <button
          type="button"
          class="px-2.5 py-1 rounded-xl text-[11px] font-semibold border transition-colors cursor-pointer"
          :class="
            shippingPayer === 'recipient'
              ? 'border-primary bg-primary/10 text-primary'
              : 'border-border/60 text-muted-foreground hover:bg-muted/40'
          "
          @click="emit('update:shippingPayer', 'recipient')"
        >
          {{ languageStore.t('به عهده گیرنده', 'Recipient pays') }}
        </button>
        <button
          type="button"
          class="px-2.5 py-1 rounded-xl text-[11px] font-semibold border transition-colors cursor-pointer"
          :class="
            shippingPayer === 'donor'
              ? 'border-primary bg-primary/10 text-primary'
              : 'border-border/60 text-muted-foreground hover:bg-muted/40'
          "
          @click="emit('update:shippingPayer', 'donor')"
        >
          {{ languageStore.t('به عهده من (اهداکننده)', 'Donor pays') }}
        </button>
      </div>
    </div>

    <!-- Station Picker (Shown when station is selected) -->
    <div
      v-if="hasStation"
      class="flex flex-col gap-2.5 rounded-2xl border border-border/50 bg-background/50 p-3"
    >
      <div class="flex flex-col gap-1">
        <Label class="text-xs font-semibold text-foreground">
          {{ languageStore.t('انتخاب ایستگاه / قفسه تفاخر', 'Select Tafakor Book Station') }}
        </Label>
        <Select
          :model-value="stationId"
          @update:model-value="emit('update:stationId', String($event))"
        >
          <SelectTrigger class="rounded-2xl bg-input/50 border-transparent text-xs font-semibold">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectGroup>
              <SelectItem :value="STATION_NONE">
                {{
                  loadingStations
                    ? languageStore.t('در حال دریافت ایستگاه‌ها...', 'Loading stations...')
                    : stations.length > 0
                      ? languageStore.t('هماهنگی بعدی بدون ایستگاه ثابت', 'Choose station later')
                      : languageStore.t('هنوز ایستگاهی ثبت نشده است', 'No stations available yet')
                }}
              </SelectItem>
              <SelectItem
                v-for="st in stations"
                :key="st.id"
                :value="String(st.id)"
              >
                {{ st.name }} — {{ st.city_name }}
              </SelectItem>
            </SelectGroup>
          </SelectContent>
        </Select>
      </div>

      <div
        v-if="stationId !== STATION_NONE"
        class="flex items-center justify-between gap-2 pt-0.5"
      >
        <span class="text-[11px] text-muted-foreground leading-relaxed">
          {{
            languageStore.t(
              'کتاب هم‌اکنون در قفسه این ایستگاه قرار گرفته و با کد QR قابل برداشت است',
              'Book is already placed inside this station shelf'
            )
          }}
        </span>
        <Switch
          :checked="depositNow"
          @update:checked="(v: boolean) => emit('update:depositNow', v)"
        />
      </div>
    </div>

    <!-- Category & Donation Note -->
    <div class="grid grid-cols-1 gap-2.5" :class="!hideCategory && categories.length > 0 ? 'sm:grid-cols-2' : ''">
      <div v-if="!hideCategory && categories.length > 0" class="flex flex-col gap-1">
        <Label class="text-[11px] text-muted-foreground">
          {{ languageStore.t('دسته‌بندی (اختیاری)', 'Category (Optional)') }}
        </Label>
        <Select
          :model-value="categoryId"
          @update:model-value="emit('update:categoryId', String($event))"
        >
          <SelectTrigger class="rounded-2xl bg-input/50 border-transparent text-xs font-semibold">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectGroup>
              <SelectItem :value="CATEGORY_AUTO">{{ languageStore.t('انتخاب خودکار', 'Auto detect') }}</SelectItem>
              <SelectItem
                v-for="cat in categories"
                :key="cat.id"
                :value="String(cat.id)"
              >
                {{ cat.label }}
              </SelectItem>
            </SelectGroup>
          </SelectContent>
        </Select>
      </div>

      <div class="flex flex-col gap-1">
        <Label class="text-[11px] text-muted-foreground">
          {{
            descriptionLabel ||
              languageStore.t('توضیحات اهدا / محل تحویل (اختیاری)', 'Donation / Meetup Note (Optional)')
          }}
        </Label>
        <Textarea
          v-if="textareaMode"
          :model-value="description"
          rows="2"
          :placeholder="
            descriptionPlaceholder ||
              languageStore.t('مثلاً: تحویل حضوری حوالی میدان انقلاب یا ارسال پستی...', 'Condition notes or meetup details...')
          "
          @update:model-value="emit('update:description', String($event))"
        />
        <Input
          v-else
          :model-value="description"
          :placeholder="
            descriptionPlaceholder ||
              languageStore.t('مثلاً: تحویل حضوری در تهران یا ارسال پستی', 'e.g. Meetup in Tehran or post')
          "
          @update:model-value="emit('update:description', String($event))"
        />
      </div>
    </div>
  </div>
</template>

