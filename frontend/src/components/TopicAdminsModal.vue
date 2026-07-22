<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { 
  ShieldCheckIcon, 
  CrownIcon, 
  Trash2Icon, 
  UserPlusIcon, 
  Loader2Icon, 
  ShieldOffIcon, 
  UserIcon, 
  AlertCircleIcon 
} from '@lucide/vue'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useLanguageStore } from '@/stores/languageStore'
import { 
  getTopicAdmins, 
  addTopicAdmin, 
  removeTopicAdmin, 
  type UserSimple, 
  type TopicAdmin 
} from '@/api'

const languageStore = useLanguageStore()

const props = withDefaults(defineProps<{
  isOpen: boolean
  topicId?: string | number | null
  isOwner?: boolean
}>(), {
  isOpen: false,
  topicId: null,
  isOwner: false,
})

const emit = defineEmits<{
  (e: 'update:isOpen', value: boolean): void
  (e: 'close'): void
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

// Revoking State tracker per user ID
const revokingUserIds = ref<Record<string | number, boolean>>({})

const fetchAdmins = async () => {
  if (!props.topicId) {
    owner.value = null
    admins.value = []
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

watch(() => props.isOpen, (newOpen) => {
  if (newOpen) {
    activeTab.value = 'list'
    targetUserId.value = ''
    customTitle.value = ''
    errorMessage.value = null
    fetchAdmins()
  }
})

watch(() => props.topicId, () => {
  if (props.isOpen) {
    fetchAdmins()
  }
})

const handleAddAdmin = async () => {
  if (!props.topicId || !targetUserId.value.trim()) return

  isSubmitting.value = true
  errorMessage.value = null

  try {
    await addTopicAdmin(props.topicId, {
      user_id: targetUserId.value.trim(),
      custom_title: customTitle.value.trim() || 'Admin'
    })
    
    // Reset form and return to list
    targetUserId.value = ''
    customTitle.value = ''
    activeTab.value = 'list'
    await fetchAdmins()
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
  if (!props.topicId) return

  revokingUserIds.value[userId] = true

  try {
    await removeTopicAdmin(props.topicId, userId)
    admins.value = admins.value.filter(a => String(a.user.id) !== String(userId))
  } catch (err: any) {
    console.error('Failed to remove admin:', err)
  } finally {
    revokingUserIds.value[userId] = false
  }
}

const getUserDisplayName = (user: UserSimple) => {
  if (user.first_name || user.last_name) {
    return `${user.first_name || ''} ${user.last_name || ''}`.trim()
  }
  return user.phone
}

const dialogOpen = computed({
  get: () => props.isOpen,
  set: (val: boolean) => {
    emit('update:isOpen', val)
    if (!val) emit('close')
  }
})
</script>

<template>
  <Dialog v-model:open="dialogOpen">
    <DialogContent 
      class="sm:max-w-md rounded-3xl p-6 shadow-2xl bg-background border border-border/80"
      :dir="languageStore.dir"
    >
      <!-- Modal Header -->
      <DialogHeader class="text-start">
        <div class="flex items-center gap-3">
          <div class="size-10 rounded-2xl bg-primary/10 flex items-center justify-center text-primary shrink-0">
            <ShieldCheckIcon class="size-5" />
          </div>
          <div>
            <DialogTitle class="text-base font-extrabold text-foreground">
              {{ isOwner 
                ? languageStore.t('مدیریت ادمین‌های تاپیک', 'Manage Topic Admins') 
                : languageStore.t('اطلاعات و ادمین‌های تاپیک', 'Topic Admins & Info') 
              }}
            </DialogTitle>
            <DialogDescription class="text-xs text-muted-foreground mt-0.5">
              {{ isOwner
                ? languageStore.t('تعیین ادمین جدید یا حذف دسترسی ادمین‌های فعلی', 'Appoint new admins or revoke existing admin access')
                : languageStore.t('مشاهده سازنده تاپیک و ادمین‌های فعال', 'View topic owner and active administrators')
              }}
            </DialogDescription>
          </div>
        </div>
      </DialogHeader>

      <!-- Loading State -->
      <div v-if="loading" class="py-12 flex flex-col items-center justify-center gap-3">
        <Loader2Icon class="size-8 animate-spin text-primary" />
        <span class="text-xs font-medium text-muted-foreground">
          {{ languageStore.t('در حال دریافت لیست ادمین‌ها...', 'Fetching admins list...') }}
        </span>
      </div>

      <!-- Main Content Tabs -->
      <div v-else class="mt-2">
        <Tabs v-model="activeTab" class="w-full">
          
          <!-- Tabs Navigation Trigger (Owner Only) -->
          <TabsList v-if="isOwner" class="grid w-full grid-cols-2 rounded-2xl bg-muted/60 p-1 mb-4">
            <TabsTrigger 
              value="list" 
              class="rounded-xl text-xs font-bold transition-all data-[state=active]:bg-background data-[state=active]:shadow-xs"
            >
              {{ languageStore.t('لیست ادمین‌ها', 'Admins List') }} ({{ languageStore.n(admins.length) }})
            </TabsTrigger>
            <TabsTrigger 
              value="add" 
              class="rounded-xl text-xs font-bold transition-all data-[state=active]:bg-background data-[state=active]:shadow-xs"
            >
              {{ languageStore.t('افزودن ادمین', 'Add Admin') }}
            </TabsTrigger>
          </TabsList>

          <!-- TAB 1: Admins List -->
          <TabsContent value="list" class="space-y-4 outline-none">
            
            <!-- Owner Banner Card -->
            <div v-if="owner" class="bg-amber-500/10 border border-amber-500/25 rounded-2xl p-3 flex items-center justify-between gap-3">
              <div class="flex items-center gap-3 min-w-0">
                <Avatar class="size-10 border-2 border-amber-500/40 shrink-0">
                  <AvatarImage v-if="owner.profile_image" :src="owner.profile_image" />
                  <AvatarFallback class="bg-amber-500/20 text-amber-600 dark:text-amber-400 font-bold">
                    <CrownIcon class="size-4" />
                  </AvatarFallback>
                </Avatar>
                <div class="flex flex-col text-start min-w-0">
                  <span class="text-xs font-extrabold text-foreground truncate">
                    {{ getUserDisplayName(owner) }}
                  </span>
                  <span class="text-[10px] text-muted-foreground dir-ltr text-start">
                    {{ owner.phone }}
                  </span>
                </div>
              </div>

              <Badge class="bg-amber-500/20 text-amber-700 dark:text-amber-300 border-amber-500/30 text-[10px] font-bold px-2 py-0.5 rounded-lg shrink-0">
                <CrownIcon class="size-3 me-1 text-amber-500" />
                {{ languageStore.t('مالک تاپیک', 'Owner') }}
              </Badge>
            </div>

            <!-- Active Admins Scroll List -->
            <div class="space-y-2">
              <span class="text-xs font-bold text-muted-foreground block text-start">
                {{ languageStore.t('ادمین‌های فعال:', 'Active Administrators:') }}
              </span>

              <div v-if="admins.length > 0" class="max-h-56 overflow-y-auto space-y-2 pr-1">
                <div 
                  v-for="admin in admins" 
                  :key="admin.id"
                  class="bg-card/60 border border-border/60 rounded-2xl p-3 flex items-center justify-between gap-3 transition-all hover:bg-muted/40"
                >
                  <div class="flex items-center gap-3 min-w-0">
                    <Avatar class="size-9 shrink-0 border border-border/80">
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
                        <Badge variant="outline" class="text-[9.5px] font-semibold px-1.5 py-0 rounded-md">
                          {{ admin.custom_title || 'Admin' }}
                        </Badge>
                      </div>
                      <span class="text-[10px] text-muted-foreground dir-ltr text-start">
                        {{ admin.user.phone }}
                      </span>
                    </div>
                  </div>

                  <!-- Revoke Admin Button (Owner Only) -->
                  <Button 
                    v-if="isOwner"
                    @click="handleRemoveAdmin(admin.user.id)"
                    :disabled="!!revokingUserIds[admin.user.id]"
                    variant="ghost" 
                    size="icon"
                    class="size-8 rounded-xl text-destructive hover:bg-destructive/10 hover:text-destructive shrink-0 cursor-pointer"
                    :title="languageStore.t('حذف ادمین', 'Revoke Admin')"
                  >
                    <Loader2Icon v-if="revokingUserIds[admin.user.id]" class="size-4 animate-spin" />
                    <Trash2Icon v-else class="size-4" />
                  </Button>
                </div>
              </div>

              <!-- Zero Admins Empty State -->
              <div 
                v-else 
                class="bg-muted/20 border border-dashed border-border/80 rounded-2xl p-6 text-center text-muted-foreground flex flex-col items-center justify-center gap-2"
              >
                <ShieldOffIcon class="size-8 text-muted-foreground/50" />
                <span class="text-xs font-semibold">
                  {{ languageStore.t('هیچ ادمینی برای این تاپیک تعریف نشده است.', 'No administrators added for this topic yet.') }}
                </span>
                <span v-if="isOwner" class="text-[11px] text-muted-foreground/70">
                  {{ languageStore.t('از تب «افزودن ادمین» اقدام به ارتقای کاربران کنید.', 'Use the "Add Admin" tab to promote users.') }}
                </span>
              </div>
            </div>

          </TabsContent>

          <!-- TAB 2: Add Admin Form (Owner Only) -->
          <TabsContent v-if="isOwner" value="add" class="space-y-4 outline-none">
            
            <!-- Inline Error Alert -->
            <div 
              v-if="errorMessage" 
              class="bg-destructive/10 border border-destructive/20 rounded-2xl p-3 flex items-center gap-2 text-destructive text-xs font-medium text-start"
            >
              <AlertCircleIcon class="size-4 shrink-0" />
              <span>{{ errorMessage }}</span>
            </div>

            <!-- Inputs Form -->
            <div class="space-y-3 text-start">
              
              <div class="space-y-1">
                <label class="text-xs font-bold text-foreground">
                  {{ languageStore.t('شناسه کاربر / شماره موبایل (User ID)', 'User ID / Phone') }}
                </label>
                <Input 
                  v-model="targetUserId"
                  type="text"
                  :placeholder="languageStore.t('مثال: 1 یا شماره موبایل کاربر', 'e.g. 1 or User Phone')"
                  class="rounded-xl h-10 text-xs"
                />
              </div>

              <div class="space-y-1">
                <label class="text-xs font-bold text-foreground">
                  {{ languageStore.t('عنوان اختصاصی (اختیاری)', 'Custom Title (Optional)') }}
                </label>
                <Input 
                  v-model="customTitle"
                  type="text"
                  :placeholder="languageStore.t('مثال: مدیر محتوا / Moderator', 'e.g. Content Manager / Moderator')"
                  class="rounded-xl h-10 text-xs"
                />
              </div>

            </div>

            <!-- Submit Button -->
            <Button 
              @click="handleAddAdmin"
              :disabled="isSubmitting || !targetUserId.trim()"
              class="w-full rounded-2xl h-10 text-xs font-extrabold flex items-center justify-center gap-2 cursor-pointer shadow-sm mt-2"
            >
              <Loader2Icon v-if="isSubmitting" class="size-4 animate-spin" />
              <UserPlusIcon v-else class="size-4" />
              <span>
                {{ isSubmitting 
                  ? languageStore.t('در حال ثبت ادمین...', 'Appointing Admin...') 
                  : languageStore.t('انتصاب کاربر به عنوان ادمین', 'Appoint User as Admin') 
                }}
              </span>
            </Button>

          </TabsContent>

        </Tabs>
      </div>

    </DialogContent>
  </Dialog>
</template>
