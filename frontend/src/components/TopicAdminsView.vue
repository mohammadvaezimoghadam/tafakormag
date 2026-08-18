<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { 
  CrownIcon, 
  Trash2Icon, 
  UserPlusIcon, 
  Loader2Icon, 
  ShieldOffIcon, 
  UserIcon, 
  AlertTriangleIcon,
  CheckCircle2Icon,
  ArrowRightLeftIcon,
  XIcon
} from '@lucide/vue'
import PlatformHeader from './PlatformHeader.vue'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog'
import { useLanguageStore } from '@/stores/languageStore'
import { 
  getTopicAdmins, 
  addTopicAdmin, 
  removeTopicAdmin, 
  transferTopicOwnership,
  type UserSimple, 
  type TopicAdmin 
} from '@/api'

const languageStore = useLanguageStore()

const props = withDefaults(defineProps<{
  topicId?: string | number | null
  isOwner?: boolean
  forcedState?: 'default' | 'loading' | 'empty' | 'error' | null
}>(), {
  topicId: null,
  isOwner: false,
  forcedState: null,
})

const emit = defineEmits<{
  (e: 'back'): void
  (e: 'ownership-transferred', newOwner: UserSimple): void
}>()

// Internal States
const loading = ref(false)
const owner = ref<UserSimple | null>(null)
const admins = ref<TopicAdmin[]>([])
const activeTab = ref<'list' | 'add'>('list')

// Add Admin Form States
const targetUserId = ref('')
const customTitle = ref('')
const isSubmitting = ref(false)
const errorMessage = ref<string | null>(null)
const addSuccess = ref(false)

// Transfer Ownership States
const isTransferModalOpen = ref(false)
const transferTargetUser = ref<UserSimple | null>(null)
const isTransferring = ref(false)

// Revoking State tracker per user ID
const revokingUserIds = ref<Record<string | number, boolean>>({})

// Mock data generator for playground testing
const getMockData = () => {
  return {
    owner: {
      id: '1',
      phone: '09123456789',
      first_name: 'شایان',
      last_name: 'مهدوی',
      profile_image: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100&auto=format&fit=crop&q=80'
    },
    admins: [
      {
        id: '101',
        user: {
          id: '2',
          phone: '09987654321',
          first_name: 'امیرحسین',
          last_name: 'رضایی',
          profile_image: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&auto=format&fit=crop&q=80'
        },
        custom_title: 'مدیر محتوا',
        created_at: '2026-07-22T10:00:00Z'
      },
      {
        id: '102',
        user: {
          id: '3',
          phone: '09112223344',
          first_name: 'سارا',
          last_name: 'احمدی',
          profile_image: ''
        },
        custom_title: 'پشتیبان فنی',
        created_at: '2026-07-22T11:00:00Z'
      }
    ] as TopicAdmin[]
  }
}

const applyForcedState = () => {
  if (!props.forcedState) return false

  if (props.forcedState === 'loading') {
    loading.value = true
    errorMessage.value = null
    return true
  }

  if (props.forcedState === 'empty') {
    loading.value = false
    const mock = getMockData()
    owner.value = mock.owner
    admins.value = []
    errorMessage.value = null
    return true
  }

  if (props.forcedState === 'error') {
    loading.value = false
    const mock = getMockData()
    owner.value = mock.owner
    admins.value = mock.admins
    activeTab.value = 'add'
    errorMessage.value = languageStore.t(
      'کاربری با این شناسه یا شماره موبایل یافت نشد.',
      'User with this ID or phone number was not found.'
    )
    return true
  }

  if (props.forcedState === 'default') {
    loading.value = false
    const mock = getMockData()
    owner.value = mock.owner
    admins.value = mock.admins
    errorMessage.value = null
    return true
  }

  return false
}

const fetchAdmins = async () => {
  if (applyForcedState()) return

  if (!props.topicId) {
    // Playground default preview fallback
    const mock = getMockData()
    owner.value = mock.owner
    admins.value = mock.admins
    loading.value = false
    return
  }

  loading.value = true
  errorMessage.value = null

  try {
    const res = await getTopicAdmins(props.topicId)
    owner.value = res.data.owner || null
    admins.value = res.data.admins || []
  } catch (err: any) {
    console.error('Failed to load topic admins:', err)
  } finally {
    loading.value = false
  }
}

watch(() => props.forcedState, () => {
  fetchAdmins()
})

watch(() => props.topicId, () => {
  fetchAdmins()
})

onMounted(() => {
  fetchAdmins()
})

const handleAddAdmin = async () => {
  if (!targetUserId.value.trim()) return

  isSubmitting.value = true
  errorMessage.value = null
  addSuccess.value = false

  if (!props.topicId) {
    // Playground simulation add
    setTimeout(() => {
      isSubmitting.value = false
      if (targetUserId.value.trim() === 'error') {
        errorMessage.value = languageStore.t(
          'کاربری با این شناسه یا شماره موبایل یافت نشد.',
          'User with this ID or phone number was not found.'
        )
      } else {
        addSuccess.value = true
        admins.value.push({
          id: String(Date.now()),
          user: {
            id: String(Date.now()),
            phone: targetUserId.value.trim(),
            first_name: 'کاربر جدید',
            last_name: ''
          },
          custom_title: customTitle.value.trim() || 'Admin',
          created_at: new Date().toISOString()
        })
        targetUserId.value = ''
        customTitle.value = ''
        setTimeout(() => {
          addSuccess.value = false
          activeTab.value = 'list'
        }, 1200)
      }
    }, 600)
    return
  }

  try {
    await addTopicAdmin(props.topicId, {
      user_id: targetUserId.value.trim(),
      custom_title: customTitle.value.trim() || 'Admin'
    })
    
    addSuccess.value = true
    targetUserId.value = ''
    customTitle.value = ''
    
    await fetchAdmins()

    setTimeout(() => {
      addSuccess.value = false
      activeTab.value = 'list'
    }, 1200)
  } catch (err: any) {
    if (err.response && err.response.data && err.response.data.error) {
      errorMessage.value = err.response.data.error
    } else if (err.response && err.response.data && err.response.data.message) {
      errorMessage.value = err.response.data.message
    } else {
      errorMessage.value = languageStore.t(
        'خطایی در افزودن ادمین رخ داد.',
        'An error occurred while adding the admin.'
      )
    }
  } finally {
    isSubmitting.value = false
  }
}

const handleRemoveAdmin = async (userId: string | number) => {
  revokingUserIds.value[userId] = true

  if (!props.topicId) {
    // Playground simulation remove
    setTimeout(() => {
      admins.value = admins.value.filter(a => String(a.user.id) !== String(userId))
      revokingUserIds.value[userId] = false
    }, 400)
    return
  }

  try {
    await removeTopicAdmin(props.topicId, userId)
    admins.value = admins.value.filter(a => String(a.user.id) !== String(userId))
  } catch (err: any) {
    console.error('Failed to remove admin:', err)
  } finally {
    revokingUserIds.value[userId] = false
  }
}

const openTransferConfirmModal = (targetUser: UserSimple) => {
  transferTargetUser.value = targetUser
  isTransferModalOpen.value = true
}

const handleExecuteTransferOwnership = async () => {
  if (!transferTargetUser.value) return

  isTransferring.value = true

  if (!props.topicId) {
    // Playground simulation transfer
    setTimeout(() => {
      owner.value = transferTargetUser.value
      admins.value = admins.value.filter(a => String(a.user.id) !== String(transferTargetUser.value?.id))
      isTransferring.value = false
      isTransferModalOpen.value = false
    }, 500)
    return
  }

  try {
    const res = await transferTopicOwnership(props.topicId, {
      new_owner_id: transferTargetUser.value.id
    })
    owner.value = res.data.owner
    await fetchAdmins()
    isTransferModalOpen.value = false
    emit('ownership-transferred', res.data.owner)
  } catch (err: any) {
    if (err.response && err.response.data && err.response.data.error) {
      errorMessage.value = err.response.data.error
    } else {
      errorMessage.value = languageStore.t(
        'خطا در انتقال مالکیت تاپیک.',
        'An error occurred while transferring topic ownership.'
      )
    }
  } finally {
    isTransferring.value = false
  }
}

const getUserDisplayName = (user: UserSimple) => {
  if (user.first_name || user.last_name) {
    return `${user.first_name || ''} ${user.last_name || ''}`.trim()
  }
  return user.phone
}
</script>

<template>
  <div 
    class="w-full flex flex-col gap-4 text-start font-sans select-none" 
    :dir="languageStore.dir"
  >
    <!-- Subview Header -->
    <PlatformHeader 
      is-inner-page
      :inner-title="isOwner 
        ? languageStore.t('مدیریت ادمین‌ها', 'Manage Admins') 
        : languageStore.t('اطلاعات و ادمین‌ها', 'Admins & Info')
      "
      :show-options-button="false"
      @back="emit('back')"
    />

    <!-- Main Glass Card Container -->
    <div class="w-full bg-card/45 backdrop-blur-md border border-border/40 rounded-3xl p-5 shadow-xs flex flex-col gap-4">
      
      <!-- Loading Spinner -->
      <div v-if="loading" class="py-12 flex flex-col items-center justify-center gap-3">
        <Loader2Icon class="size-7 animate-spin text-primary" />
        <span class="text-xs font-semibold text-muted-foreground">
          {{ languageStore.t('در حال دریافت اطلاعات...', 'Loading data...') }}
        </span>
      </div>

      <!-- Main Content Block -->
      <div v-else class="flex flex-col gap-4">
        
        <!-- Owner Banner Card -->
        <div v-if="owner" class="bg-amber-500/10 border border-amber-500/20 rounded-2xl p-3 flex items-center justify-between gap-3">
          <div class="flex items-center gap-3 min-w-0">
            <Avatar class="size-9 border border-amber-500/30 shrink-0">
              <AvatarImage v-if="owner.profile_image" :src="owner.profile_image" />
              <AvatarFallback class="bg-amber-500/20 text-amber-600 dark:text-amber-400 font-bold text-xs">
                <CrownIcon class="size-4" />
              </AvatarFallback>
            </Avatar>
            <div class="flex flex-col text-start min-w-0">
              <span class="text-xs font-bold text-foreground truncate">
                {{ getUserDisplayName(owner) }}
              </span>
              <span class="text-[10px] text-muted-foreground dir-ltr text-start font-mono">
                {{ owner.phone }}
              </span>
            </div>
          </div>

          <Badge variant="secondary" class="bg-amber-500/15 border-amber-500/25 text-amber-700 dark:text-amber-300 text-[9px] font-bold px-2 py-0.5 rounded-lg flex items-center gap-1 shrink-0">
            <CrownIcon class="size-3 text-amber-500" />
            <span>{{ languageStore.t('مالک تاپیک', 'Topic Owner') }}</span>
          </Badge>
        </div>

        <!-- Navigation Tabs (Owner Only) -->
        <Tabs v-model="activeTab" class="w-full">
          
          <!-- Pure Original shadcn TabsList -->
          <TabsList v-if="isOwner" class="grid w-full grid-cols-2 bg-muted/60 dark:bg-muted/30 p-1 rounded-2xl mb-4">
            <TabsTrigger 
              value="list" 
              class="rounded-xl text-xs font-bold"
            >
              {{ languageStore.t('لیست ادمین‌ها', 'Admins List') }} ({{ languageStore.n(admins.length) }})
            </TabsTrigger>
            <TabsTrigger 
              value="add" 
              class="rounded-xl text-xs font-bold"
            >
              {{ languageStore.t('افزودن ادمین', 'Add Admin') }}
            </TabsTrigger>
          </TabsList>

          <!-- TAB 1: Admins List -->
          <TabsContent value="list" class="space-y-2.5 outline-none">
            
            <!-- Active Admins List -->
            <div v-if="admins.length > 0" class="space-y-2">
              <div 
                v-for="admin in admins" 
                :key="admin.id"
                class="bg-background/30 border border-border/40 hover:bg-muted/30 rounded-2xl p-3 flex items-center justify-between gap-3 transition-all"
              >
                <div class="flex items-center gap-3 min-w-0">
                  <Avatar class="size-9 shrink-0 border border-border/60">
                    <AvatarImage v-if="admin.user.profile_image" :src="admin.user.profile_image" />
                    <AvatarFallback class="bg-primary/10 text-primary font-bold text-xs">
                      <UserIcon class="size-4" />
                    </AvatarFallback>
                  </Avatar>
                  
                  <div class="flex flex-col text-start min-w-0">
                    <div class="flex items-center gap-2">
                      <span class="text-xs font-bold text-foreground truncate">
                        {{ getUserDisplayName(admin.user) }}
                      </span>
                      <Badge variant="outline" class="text-[8.5px] font-semibold px-2 py-0.5 rounded-md border-border/60 bg-muted/40">
                        {{ admin.custom_title || 'Admin' }}
                      </Badge>
                    </div>
                    <span class="text-[10px] text-muted-foreground dir-ltr text-start font-mono">
                      {{ admin.user.phone }}
                    </span>
                  </div>
                </div>

                <!-- Admin Action Buttons (Owner Only) -->
                <div v-if="isOwner" class="flex items-center gap-1.5 shrink-0">
                  <Button 
                    @click="openTransferConfirmModal(admin.user)"
                    variant="outline" 
                    size="sm"
                    class="h-8 px-2 rounded-xl text-amber-600 dark:text-amber-400 border-amber-500/20 hover:bg-amber-500/10 shrink-0 cursor-pointer text-xs font-semibold flex items-center gap-1.5"
                    :title="languageStore.t('انتقال مالکیت تاپیک به این کاربر', 'Transfer Ownership to this user')"
                  >
                    <ArrowRightLeftIcon class="size-3.5" />
                    <span class="hidden sm:inline">{{ languageStore.t('انتقال مالکیت', 'Transfer') }}</span>
                  </Button>

                  <Button 
                    @click="handleRemoveAdmin(admin.user.id)"
                    :disabled="!!revokingUserIds[admin.user.id]"
                    variant="ghost" 
                    size="sm"
                    class="h-8 px-2 rounded-xl text-destructive hover:bg-destructive/10 hover:text-destructive shrink-0 cursor-pointer text-xs font-semibold flex items-center gap-1.5"
                    :title="languageStore.t('حذف ادمین', 'Revoke Admin')"
                  >
                    <Loader2Icon v-if="revokingUserIds[admin.user.id]" class="size-3.5 animate-spin" />
                    <Trash2Icon v-else class="size-3.5" />
                    <span>{{ languageStore.t('حذف', 'Revoke') }}</span>
                  </Button>
                </div>
              </div>
            </div>

            <!-- Zero Admins Empty State -->
            <div 
              v-else 
              class="bg-muted/20 border border-dashed border-border/60 rounded-2xl p-7 text-center text-muted-foreground flex flex-col items-center justify-center gap-2"
            >
              <ShieldOffIcon class="size-6 text-muted-foreground/50" />
              <span class="text-xs font-semibold text-foreground">
                {{ languageStore.t('هیچ ادمینی ثبت نشده است.', 'No administrators added yet.') }}
              </span>
            </div>

          </TabsContent>

          <!-- TAB 2: Add Admin Form (Owner Only) -->
          <TabsContent v-if="isOwner" value="add" class="outline-none pt-1">
            
            <!-- Styled Error Alert Banner matching BotConnectionCard -->
            <transition name="fade-slide">
              <div 
                v-if="errorMessage" 
                class="p-3.5 mb-3.5 bg-destructive/10 text-destructive rounded-2xl border border-destructive/20 text-xs font-semibold text-start flex items-start gap-2.5 shadow-xs"
              >
                <AlertTriangleIcon class="size-4 shrink-0 mt-0.5" />
                <span class="leading-relaxed flex-1">{{ errorMessage }}</span>
              </div>
            </transition>

            <!-- Clean Minimal Form -->
            <form @submit.prevent="handleAddAdmin" class="flex flex-col gap-3.5 text-start">
              
              <div class="flex flex-col gap-2 text-start">
                <Label for="admin-user-id" class="text-xs font-bold text-foreground/80">
                  {{ languageStore.t('شناسه کاربر یا شماره موبایل', 'User ID or Phone Number') }}
                </Label>
                <Input 
                  id="admin-user-id"
                  v-model="targetUserId"
                  type="text"
                  :placeholder="languageStore.t('مثال: 1 یا 09123456789', 'e.g. 1 or 09123456789')"
                  class="h-10.5 text-xs font-semibold focus-visible:ring-primary/20 bg-background/25 border-border/60 rounded-xl text-start"
                />
              </div>

              <div class="flex flex-col gap-2 text-start">
                <Label for="admin-custom-title" class="text-xs font-bold text-foreground/80">
                  {{ languageStore.t('عنوان اختصاصی (اختیاری)', 'Custom Title (Optional)') }}
                </Label>
                <Input 
                  id="admin-custom-title"
                  v-model="customTitle"
                  type="text"
                  :placeholder="languageStore.t('مثال: مدیر محتوا / Moderator', 'e.g. Content Manager / Moderator')"
                  class="h-10.5 text-xs font-semibold focus-visible:ring-primary/20 bg-background/25 border-border/60 rounded-xl text-start"
                />
              </div>

              <!-- Submit CTA Button -->
              <Button 
                type="submit"
                :disabled="isSubmitting || addSuccess || !targetUserId.trim()"
                class="w-full h-11 text-xs font-bold rounded-xl transition-all flex items-center justify-center gap-2 cursor-pointer shadow-xs active:scale-[0.98] mt-1"
                :variant="addSuccess ? 'secondary' : 'default'"
              >
                <Loader2Icon v-if="isSubmitting" class="size-4 animate-spin" />
                <CheckCircle2Icon v-else-if="addSuccess" class="size-4 text-emerald-600 dark:text-emerald-400" />
                <UserPlusIcon v-else class="size-4" />
                <span>
                  {{ isSubmitting 
                    ? languageStore.t('در حال ثبت ادمین...', 'Appointing Admin...') 
                    : addSuccess
                      ? languageStore.t('ادمین با موفقیت ثبت شد', 'Admin appointed successfully')
                      : languageStore.t('ثبت ادمین جدید', 'Appoint Admin') 
                  }}
                </span>
              </Button>

            </form>

          </TabsContent>

        </Tabs>

      </div>

    </div>

    <!-- Transfer Ownership Confirmation Dialog -->
    <Dialog :open="isTransferModalOpen" @update:open="(val) => isTransferModalOpen = val">
      <DialogContent class="max-w-[400px] p-5 rounded-3xl" :dir="languageStore.dir">
        <DialogHeader class="space-y-2">
          <DialogTitle class="text-xs font-bold text-foreground flex items-center gap-2">
            <ArrowRightLeftIcon class="size-4 text-amber-500" />
            <span>{{ languageStore.t('تایید انتقال مالکیت تاپیک', 'Confirm Ownership Transfer') }}</span>
          </DialogTitle>
          <DialogDescription class="text-xs text-muted-foreground leading-relaxed text-start">
            {{ languageStore.t(
              `آیا از انتقال مالکیت تاپیک به «${transferTargetUser ? getUserDisplayName(transferTargetUser) : ''}» اطمینان دارید؟ این کاربر مالک اصلی تاپیک شده و شما به ادمین تبدیل خواهید شد.`,
              `Are you sure you want to transfer topic ownership to "${transferTargetUser ? getUserDisplayName(transferTargetUser) : ''}"?`
            ) }}
          </DialogDescription>
        </DialogHeader>

        <div class="flex items-center justify-end gap-2 mt-4">
          <Button variant="outline" size="sm" @click="isTransferModalOpen = false" class="text-xs rounded-xl cursor-pointer">
            {{ languageStore.t('انصراف', 'Cancel') }}
          </Button>

          <Button 
            variant="default" 
            size="sm" 
            :disabled="isTransferring"
            @click="handleExecuteTransferOwnership" 
            class="text-xs rounded-xl bg-amber-600 hover:bg-amber-700 text-white font-bold flex items-center gap-1.5 cursor-pointer"
          >
            <Loader2Icon v-if="isTransferring" class="size-3.5 animate-spin" />
            <CrownIcon v-else class="size-3.5" />
            <span>{{ languageStore.t('انتقال مالکیت', 'Transfer Ownership') }}</span>
          </Button>
        </div>
      </DialogContent>
    </Dialog>

  </div>
</template>
