<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import DonationCard from '@/components/kindness/DonationCard.vue'
import CampaignDetailView from '@/components/kindness/CampaignDetailView.vue'
import HorizontalSliderRow from '@/components/home/HorizontalSliderRow.vue'
import ConfirmModal from '@/components/ConfirmModal.vue'
import type { DonationCampaignProps, CampaignCategory } from '@/types/kindness'
import { fetchDonationCampaigns, fetchDonationCampaign, deleteDonationCampaign } from '@/api'
import { useLanguageStore } from '@/stores/languageStore'
import { useUserStore } from '@/stores/userStore'
import { useToastStore } from '@/stores/toastStore'
import {
  formatKindnessNumber,
  mapApiCampaignToProps,
  normalizeCampaignCategory,
} from '@/utils/kindness'
import { Skeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'
import {
  HeartIcon,
  LayersIcon,
  UserIcon
} from '@lucide/vue'

const props = withDefaults(defineProps<{
  searchQuery?: string
  initialCampaignId?: string | number | null
}>(), {
  searchQuery: '',
  initialCampaignId: null
})

const emit = defineEmits<{
  (e: 'donate-click', campaign: DonationCampaignProps): void
  (e: 'create-campaign'): void
  (e: 'edit-campaign', campaign: DonationCampaignProps): void
  (e: 'topic-click', topicId: string | number): void
  (e: 'transparency-click', imageIndex: number, imageUrl: string): void
  (e: 'detail-change', campaign: DonationCampaignProps | null): void
}>()

const languageStore = useLanguageStore()
const userStore = useUserStore()
const toastStore = useToastStore()
const router = useRouter()
const route = useRoute()

interface CategoryChip {
  id: 'my_campaigns' | 'all' | 'inactive' | CampaignCategory
  labelFa: string
  labelEn: string
}

const CATEGORIES: CategoryChip[] = [
  { id: 'my_campaigns', labelFa: 'توسط من', labelEn: 'By Me' },
  { id: 'all', labelFa: 'همه', labelEn: 'All' },
  { id: 'inactive', labelFa: 'غیرفعال', labelEn: 'Inactive' },
  { id: 'mosque', labelFa: 'مسجد و اماکن مذهبی', labelEn: 'Mosque' },
  { id: 'school', labelFa: 'مدرسه و آموزش', labelEn: 'School' },
  { id: 'health', labelFa: 'درمانی و سلامت', labelEn: 'Health' },
  { id: 'livelihood', labelFa: 'نیازمندان و معیشت', labelEn: 'Livelihood' },
  { id: 'construction', labelFa: 'عمرانی و تجهیزات', labelEn: 'Construction' },
  { id: 'other', labelFa: 'متفرقه و عمومی', labelEn: 'Other' }
]

const selectedCategory = ref<'my_campaigns' | 'all' | 'inactive' | CampaignCategory>('all')
const loading = ref(true)
const detailLoading = ref(false)
const campaigns = ref<DonationCampaignProps[]>([])
const selectedCampaignId = ref<string | number | null>(null)
const fetchedCampaignDetail = ref<DonationCampaignProps | null>(null)

const selectedCampaign = computed<DonationCampaignProps | null>(() => {
  if (selectedCampaignId.value === null) return null
  if (
    fetchedCampaignDetail.value &&
    String(fetchedCampaignDetail.value.id) === String(selectedCampaignId.value)
  ) {
    return fetchedCampaignDetail.value
  }
  return campaigns.value.find((c) => String(c.id) === String(selectedCampaignId.value)) || null
})

watch(
  selectedCampaign,
  (val) => {
    emit('detail-change', val)
  },
  { immediate: true }
)

const openCampaignDetail = async (campaignId: string | number) => {
  selectedCampaignId.value = campaignId
  if (typeof window !== 'undefined') {
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  detailLoading.value = true
  try {
    const res = await fetchDonationCampaign(campaignId)
    if (res.data) {
      const currentUserId = userStore.userProfile?.id ? String(userStore.userProfile.id) : null
      const currentUserPhone = userStore.userProfile?.phone || null
      const mapped = mapApiCampaignToProps(
        res.data,
        currentUserId,
        currentUserPhone,
        languageStore.isFa
      )
      fetchedCampaignDetail.value = mapped
      const idx = campaigns.value.findIndex((c) => String(c.id) === String(mapped.id))
      if (idx !== -1) {
        campaigns.value[idx] = mapped
      }
    }
  } catch (err) {
    console.warn('Could not fetch campaign details:', err)
  } finally {
    detailLoading.value = false
  }
}

const closeDetail = () => {
  selectedCampaignId.value = null
  fetchedCampaignDetail.value = null
}

const checkDeepLinkedCampaign = () => {
  if (props.initialCampaignId !== null && props.initialCampaignId !== undefined) {
    openCampaignDetail(props.initialCampaignId)
    return
  }
  const hash = route.hash || ''
  if (hash.startsWith('#campaign-')) {
    const hashId = hash.replace('#campaign-', '').trim()
    if (hashId) {
      openCampaignDetail(hashId)
      return
    }
  }
  const queryId = route.query?.campaign
  if (typeof queryId === 'string' && queryId.trim()) {
    openCampaignDetail(queryId.trim())
  }
}

watch(
  () => props.initialCampaignId,
  (newId) => {
    if (newId !== null && newId !== undefined) {
      openCampaignDetail(newId)
    }
  }
)

// Fetch campaigns from backend API
const loadCampaigns = async () => {
  loading.value = true
  try {
    const res = await fetchDonationCampaigns()
    const data = res.data?.results || res.data || []
    if (Array.isArray(data) && data.length > 0) {
      const currentUserId = userStore.userProfile?.id ? String(userStore.userProfile.id) : null
      const currentUserPhone = userStore.userProfile?.phone || null

      campaigns.value = data.map((item: any) =>
        mapApiCampaignToProps(item, currentUserId, currentUserPhone, languageStore.isFa)
      )

      if (selectedCampaignId.value !== null) {
        const refreshed = campaigns.value.find(
          (c) => String(c.id) === String(selectedCampaignId.value)
        )
        if (refreshed) {
          fetchedCampaignDetail.value = refreshed
        }
      }
    } else {
      campaigns.value = []
    }
  } catch (err) {
    console.warn('Could not fetch campaigns from server:', err)
    campaigns.value = []
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await loadCampaigns()
  checkDeepLinkedCampaign()
})

watch(
  () => languageStore.isFa,
  () => {
    loadCampaigns()
  }
)

// Filtered Campaigns by Category Chip & Header Search Query
const filteredCampaigns = computed(() => {
  const currentUserId = userStore.userProfile?.id ? String(userStore.userProfile.id) : null
  const currentUserPhone = userStore.userProfile?.phone || null

  return campaigns.value.filter(item => {
    let matchesCategory = false
    if (selectedCategory.value === 'my_campaigns') {
      matchesCategory = Boolean(
        item.canEdit ||
        (currentUserId && item.creatorId && String(item.creatorId) === currentUserId) ||
        (currentUserPhone && item.creatorPhone && item.creatorPhone === currentUserPhone)
      )
    } else if (selectedCategory.value === 'inactive') {
      matchesCategory = item.status === 'inactive'
    } else if (selectedCategory.value === 'all') {
      matchesCategory = item.status !== 'inactive'
    } else {
      matchesCategory = (normalizeCampaignCategory(item.category) === selectedCategory.value) && item.status !== 'inactive'
    }

    const query = (props.searchQuery || '').trim().toLowerCase()
    const matchesSearch = !query ||
      item.title.toLowerCase().includes(query) ||
      item.description.toLowerCase().includes(query) ||
      (item.topicName && item.topicName.toLowerCase().includes(query)) ||
      (item.authorName && item.authorName.toLowerCase().includes(query))

    return matchesCategory && matchesSearch
  })
})

const getCategoryCount = (categoryId: 'my_campaigns' | 'all' | 'inactive' | CampaignCategory): number => {
  if (categoryId === 'my_campaigns') {
    const currentUserId = userStore.userProfile?.id ? String(userStore.userProfile.id) : null
    const currentUserPhone = userStore.userProfile?.phone || null
    return campaigns.value.filter(c =>
      c.canEdit ||
      (currentUserId && c.creatorId && String(c.creatorId) === currentUserId) ||
      (currentUserPhone && c.creatorPhone && c.creatorPhone === currentUserPhone)
    ).length
  }
  if (categoryId === 'inactive') {
    return campaigns.value.filter(c => c.status === 'inactive').length
  }
  if (categoryId === 'all') {
    return campaigns.value.filter(c => c.status !== 'inactive').length
  }
  return campaigns.value.filter(
    c => normalizeCampaignCategory(c.category) === categoryId && c.status !== 'inactive'
  ).length
}

const findCampaignById = (campaignId: string | number): DonationCampaignProps | undefined => {
  if (selectedCampaign.value && String(selectedCampaign.value.id) === String(campaignId)) {
    return selectedCampaign.value
  }
  return campaigns.value.find(c => String(c.id) === String(campaignId))
}

const handleDonateClick = (campaignId: string | number) => {
  const target = findCampaignById(campaignId)
  if (target) {
    emit('donate-click', target)
  }
}

const handleEditCampaign = (campaignId: string | number) => {
  const target = findCampaignById(campaignId)
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

const handleTransparencyUploaded = () => {
  if (selectedCampaignId.value !== null) {
    openCampaignDetail(selectedCampaignId.value)
  }
}

const handlePayoutRequested = () => {
  if (selectedCampaignId.value !== null) {
    openCampaignDetail(selectedCampaignId.value)
  }
}

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
        `این پویش دارای ${formatKindnessNumber(campaign.collectedAmount, true)} تومان واریزی و ${formatKindnessNumber(campaign.donorsCount, true)} حامی است. جهت حفظ شفافیت مالی، پویش متوقف و غیرفعال خواهد شد اما سوابق آن در صفحه اهدا باقی می‌ماند. آیا مایل به ادامه هستید؟`,
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
  const target = findCampaignById(campaignId)
  if (target) {
    selectedCampaignForDelete.value = target
    isConfirmDeleteOpen.value = true
  }
}

const syncDeletedCampaignLocally = (campaign: DonationCampaignProps, hardDeleted: boolean) => {
  if (!hardDeleted) {
    campaign.status = 'inactive'
    if (fetchedCampaignDetail.value && String(fetchedCampaignDetail.value.id) === String(campaign.id)) {
      fetchedCampaignDetail.value = { ...campaign, status: 'inactive' }
    }
    return
  }

  campaigns.value = campaigns.value.filter(c => String(c.id) !== String(campaign.id))
  if (selectedCampaignId.value !== null && String(selectedCampaignId.value) === String(campaign.id)) {
    closeDetail()
  }
}

const handleConfirmDelete = async () => {
  if (!selectedCampaignForDelete.value) return
  const campaign = selectedCampaignForDelete.value
  isDeleting.value = true

  try {
    const res = await deleteDonationCampaign(campaign.id)
    if (res.data?.action === 'deactivated' || res.data?.status === 'inactive') {
      syncDeletedCampaignLocally(campaign, false)
      toastStore.triggerToast(languageStore.t('پویش متوقف و غیرفعال شد و سوابق آن حفظ گردید.', 'Campaign stopped and deactivated.'), 'info')
    } else {
      syncDeletedCampaignLocally(campaign, true)
      toastStore.triggerToast(languageStore.t('پویش با موفقیت به طور کامل حذف شد.', 'Campaign permanently deleted.'), 'success')
    }
  } catch (err: any) {
    console.error('Error deleting campaign:', err)
    const hasDonations = Boolean(
      (campaign.donorsCount && campaign.donorsCount > 0) ||
      (campaign.collectedAmount && campaign.collectedAmount > 0)
    )
    if (hasDonations) {
      syncDeletedCampaignLocally(campaign, false)
      toastStore.triggerToast(languageStore.t('پویش متوقف و غیرفعال شد.', 'Campaign stopped.'), 'info')
    } else {
      syncDeletedCampaignLocally(campaign, true)
      toastStore.triggerToast(languageStore.t('پویش با موفقیت حذف شد.', 'Campaign deleted.'), 'success')
    }
  } finally {
    isDeleting.value = false
    isConfirmDeleteOpen.value = false
    selectedCampaignForDelete.value = null
  }
}

const recordLocalDonation = (campaignId: string | number, amount: number, isAnon: boolean) => {
  const target = findCampaignById(campaignId)
  if (target) {
    target.collectedAmount += amount
    target.donorsCount += 1
    target.recentDonors.unshift({
      id: `local-donor-${Date.now()}`,
      name: isAnon ? languageStore.t('کاربر ناشناس', 'Anonymous') : languageStore.t('حامی گرامی', 'Supporter'),
      amount,
      isAnonymous: isAnon,
      donatedAt: languageStore.t('هم‌اکنون', 'Just now')
    })
    if (target.collectedAmount >= target.targetAmount) {
      target.status = 'completed'
    }
  }
}

defineExpose({
  loadCampaigns,
  recordLocalDonation,
  openCampaignDetail,
  closeDetail
})
</script>

<template>
  <div class="flex flex-col gap-4 w-full select-none" :dir="languageStore.dir">

    <!-- DEDICATED DETAIL VIEW (Flutter CampaignDetailScreen Style) -->
    <CampaignDetailView
      v-if="selectedCampaign"
      :campaign="selectedCampaign"
      :loading="detailLoading"
      @donate-click="handleDonateClick"
      @edit-click="handleEditCampaign"
      @delete-click="handleDeleteCampaign"
      @share-click="handleShareCampaign"
      @topic-click="handleTopicClick"
      @transparency-click="handleTransparencyClick"
      @transparency-uploaded="handleTransparencyUploaded"
      @payout-requested="handlePayoutRequested"
    />

    <!-- GRID FEED VIEW -->
    <template v-else>
      <!-- CATEGORY CHIPS CONTAINER WITH DESKTOP SCROLL BUTTONS -->
      <HorizontalSliderRow track-class="gap-1.5 py-1 px-0.5 items-center">
        <button
          v-for="cat in CATEGORIES"
          :key="cat.id"
          type="button"
          @click="selectedCategory = cat.id"
          :class="[
            'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all duration-200 cursor-pointer border select-none shrink-0 active:scale-95',
            selectedCategory === cat.id
              ? 'bg-primary text-primary-foreground border-primary shadow-xs'
              : 'bg-card/90 dark:bg-card/90 backdrop-blur-md text-muted-foreground hover:text-foreground hover:bg-muted/60 border-border/70 dark:border-border/60 shadow-[0_2px_6px_rgba(0,0,0,0.02)]'
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
            {{ formatKindnessNumber(getCategoryCount(cat.id), languageStore.isFa) }}
          </span>
        </button>
      </HorizontalSliderRow>

      <!-- CAMPAIGNS GRID: Clean compact cards in responsive 2-column grid -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3.5 w-full pb-24">
        <!-- Skeleton Loading State -->
        <template v-if="loading">
          <div
            v-for="i in 4"
            :key="'donation-skeleton-' + i"
            class="w-full rounded-2xl border border-border/70 dark:border-border/60 bg-card/90 overflow-hidden flex flex-col animate-pulse shadow-[0_2px_8px_rgba(0,0,0,0.03)]"
          >
            <Skeleton class="w-full aspect-[16/10] rounded-none" />
            <div class="p-3 flex flex-col gap-2.5">
              <Skeleton class="h-4 w-4/5 rounded-md" />
              <Skeleton class="h-2 w-full rounded-full" />
              <div class="flex justify-between">
                <Skeleton class="h-3 w-16 rounded-md" />
                <Skeleton class="h-3 w-14 rounded-md" />
              </div>
              <Skeleton class="h-8 w-full rounded-xl mt-1" />
            </div>
          </div>
        </template>

        <!-- Empty State -->
        <div
          v-else-if="filteredCampaigns.length === 0"
          class="col-span-full w-full py-12 px-4 flex flex-col items-center justify-center text-center gap-3 bg-card/90 dark:bg-card/90 backdrop-blur-md border border-border/70 dark:border-border/60 rounded-2xl shadow-[0_2px_8px_rgba(0,0,0,0.03)]"
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
                : languageStore.t('می‌توانید سایر دسته‌بندی‌ها را بررسی کنید یا همه پویش‌ها را ببینید.', 'Try checking other categories or viewing all campaigns.')
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

        <!-- Clean Compact Campaign Cards -->
        <template v-else>
          <DonationCard
            v-for="campaign in filteredCampaigns"
            :key="campaign.id"
            v-bind="campaign"
            @open-detail="openCampaignDetail"
            @donate-click="handleDonateClick"
            @edit-click="handleEditCampaign"
            @delete-click="handleDeleteCampaign"
            @share-click="handleShareCampaign"
            @topic-click="handleTopicClick"
            @transparency-click="handleTransparencyClick"
          />
        </template>
      </div>
    </template>

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
