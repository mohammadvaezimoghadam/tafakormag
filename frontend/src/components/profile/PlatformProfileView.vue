<script setup lang="ts">
import { computed } from 'vue'
import { useLanguageStore } from '@/stores/languageStore'
import type { UserProfile } from '@/stores/userStore'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
import {
  BookOpenIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  HandHeartIcon,
  LanguagesIcon,
  LinkIcon,
  LogOutIcon,
  MoonIcon,
  PencilIcon,
  SunIcon,
  UserIcon,
} from '@lucide/vue'

type OptionBadgeVariant = 'default' | 'secondary' | 'destructive'

const props = withDefaults(
  defineProps<{
    userProfile: UserProfile | null
    topicsCount?: number
    postsCount?: number
    connectionsBadgeText: string
    connectionsBadgeVariant?: OptionBadgeVariant
    dark: boolean
  }>(),
  {
    topicsCount: 0,
    postsCount: 0,
    connectionsBadgeVariant: 'default',
  }
)

const emit = defineEmits<{
  (e: 'edit'): void
  (e: 'open-shelf'): void
  (e: 'open-donations'): void
  (e: 'open-connections'): void
  (e: 'open-language'): void
  (e: 'logout'): void
  (e: 'update:dark', value: boolean): void
}>()

const languageStore = useLanguageStore()

const nameLetter = computed(() => {
  return props.userProfile?.name ? props.userProfile.name.trim().charAt(0) : ''
})

const statusDotClass = computed(() => {
  switch (props.userProfile?.statusVariant) {
    case 'warning':
      return 'bg-amber-500'
    case 'info':
      return 'bg-blue-500'
    case 'muted':
      return 'bg-muted-foreground/60'
    case 'success':
    default:
      return 'bg-primary'
  }
})

const stats = computed(() => [
  {
    key: 'topics',
    value: props.topicsCount,
    label: languageStore.t('تاپیک‌ها', 'Topics'),
  },
  {
    key: 'posts',
    value: props.postsCount,
    label: languageStore.t('پست‌ها', 'Posts'),
  },
  {
    key: 'donations',
    value: props.userProfile?.donations_count ?? 0,
    label: languageStore.t('اهداها', 'Donations'),
  },
])

const settingsTiles = computed(() => [
  {
    key: 'shelf',
    title: languageStore.t('قفسه کتاب من', 'My Bookshelf'),
    icon: BookOpenIcon,
    badgeText: languageStore.n(props.userProfile?.shelf_books_count ?? 0),
    badgeVariant: 'secondary' as OptionBadgeVariant,
    onSelect: () => emit('open-shelf'),
  },
  {
    key: 'donations',
    title: languageStore.t('پویش‌های اهدا', 'Donation Campaigns'),
    icon: HandHeartIcon,
    badgeText: languageStore.n(props.userProfile?.donations_count ?? 0),
    badgeVariant: 'secondary' as OptionBadgeVariant,
    onSelect: () => emit('open-donations'),
  },
  {
    key: 'connections',
    title: languageStore.t('اتصالات پیام‌رسان', 'Messenger Connections'),
    icon: LinkIcon,
    badgeText: props.connectionsBadgeText,
    badgeVariant: props.connectionsBadgeVariant,
    onSelect: () => emit('open-connections'),
  },
  {
    key: 'language',
    title: languageStore.t('زبان برنامه (Language)', 'App Language (Language)'),
    icon: LanguagesIcon,
    badgeText: languageStore.currentLanguage.toUpperCase(),
    badgeVariant: 'secondary' as OptionBadgeVariant,
    onSelect: () => emit('open-language'),
  },
])
</script>

<template>
  <div class="w-full flex flex-col gap-3.5 pb-20" :dir="languageStore.dir">
    <!-- 1. User Header Card (Flutter ProfileScreen TafakorCard style) -->
    <div
      v-if="userProfile"
      class="w-full rounded-2xl bg-card/85 dark:bg-card/65 backdrop-blur-md border border-border/70 p-4 shadow-xs select-none"
    >
      <div class="flex items-center gap-3.5">
        <!-- Circular Avatar (56x56) -->
        <div class="relative shrink-0">
          <div class="size-14 rounded-full bg-primary/10 border-[1.5px] border-primary/25 flex items-center justify-center text-primary overflow-hidden">
            <img
              v-if="userProfile.avatar"
              :src="userProfile.avatar"
              :alt="userProfile.name"
              class="size-full object-cover"
            />
            <span v-else-if="nameLetter" class="text-lg font-extrabold">
              {{ nameLetter }}
            </span>
            <UserIcon v-else class="size-7" />
          </div>

          <span
            class="absolute bottom-0 end-0 size-3.5 rounded-full border-2 border-background dark:border-card"
            :class="statusDotClass"
          />
        </div>

        <!-- Name & Phone -->
        <div class="flex-1 min-w-0 flex flex-col justify-center text-start">
          <h3 class="text-[14.5px] font-bold text-foreground truncate leading-snug select-all">
            {{ userProfile.name }}
          </h3>
          <span class="text-xs text-muted-foreground mt-1 truncate select-all font-medium">
            {{ languageStore.n(userProfile.phone) }}
          </span>
        </div>

        <!-- Status Badge & Edit Button -->
        <div class="flex items-center gap-1.5 shrink-0">
          <span
            v-if="userProfile.statusText"
            class="px-2.5 py-1 rounded-xl bg-primary/10 border border-primary/20 text-primary text-[10px] font-bold leading-none"
          >
            {{ userProfile.statusText }}
          </span>

          <button
            type="button"
            @click="emit('edit')"
            class="size-8 rounded-xl bg-muted/50 hover:bg-muted border border-border/60 text-muted-foreground hover:text-foreground active:scale-95 transition-all flex items-center justify-center cursor-pointer"
            :title="languageStore.t('ویرایش حساب کاربری', 'Edit Profile')"
            :aria-label="languageStore.t('ویرایش حساب کاربری', 'Edit Profile')"
          >
            <PencilIcon class="size-3.5 shrink-0" />
          </button>
        </div>
      </div>

      <!-- Compact Stats Strip (Existing Website Stats Preserved) -->
      <div class="grid grid-cols-3 gap-2 w-full mt-3.5 pt-3 border-t border-border/50 text-center">
        <div v-for="stat in stats" :key="stat.key" class="flex flex-col gap-0.5">
          <span class="text-sm font-black text-foreground leading-tight">
            {{ languageStore.n(stat.value) }}
          </span>
          <span class="text-[10px] font-medium text-muted-foreground">
            {{ stat.label }}
          </span>
        </div>
      </div>
    </div>

    <!-- 2. Appearance & Theme Standalone Card (Flutter Dark Mode Card style) -->
    <div
      @click="emit('update:dark', !dark)"
      class="w-full rounded-2xl bg-card/85 dark:bg-card/65 backdrop-blur-md border border-border/70 px-4 py-2.5 shadow-xs flex items-center justify-between gap-3 cursor-pointer select-none hover:bg-muted/35 transition-colors"
    >
      <div class="flex items-center gap-3 min-w-0">
        <transition name="icon-pop" mode="out-in">
          <component
            :is="dark ? MoonIcon : SunIcon"
            :key="dark ? 'moon' : 'sun'"
            class="size-5 text-primary shrink-0"
          />
        </transition>
        <span class="text-[13px] font-medium text-foreground truncate">
          {{ languageStore.t('حالت تاریک', 'Dark Mode') }}
        </span>
      </div>

      <div class="shrink-0" @click.stop>
        <Switch :checked="dark" @update:checked="emit('update:dark', $event)" />
      </div>
    </div>

    <!-- 3. Grouped Apple-Settings Options Card (Flutter Quick Options Group style) -->
    <div class="w-full rounded-2xl bg-card/85 dark:bg-card/65 backdrop-blur-md border border-border/70 shadow-xs overflow-hidden divide-y divide-border/50 select-none">
      <button
        v-for="tile in settingsTiles"
        :key="tile.key"
        type="button"
        @click="tile.onSelect()"
        class="w-full px-4 py-3.5 flex items-center gap-3 hover:bg-muted/40 active:bg-muted/60 transition-colors cursor-pointer text-start outline-none"
      >
        <component :is="tile.icon" class="size-5 text-primary shrink-0" />

        <span class="flex-1 text-[13px] font-medium text-foreground truncate">
          {{ tile.title }}
        </span>

        <div class="flex items-center gap-2 shrink-0">
          <Badge
            v-if="tile.badgeText"
            :variant="tile.badgeVariant"
            class="text-[10px] font-bold px-2 py-0.5 rounded-lg border border-border/40"
          >
            {{ tile.badgeText }}
          </Badge>

          <ChevronLeftIcon
            v-if="languageStore.isFa"
            class="size-3.5 text-muted-foreground/55 shrink-0"
          />
          <ChevronRightIcon
            v-else
            class="size-3.5 text-muted-foreground/55 shrink-0"
          />
        </div>
      </button>
    </div>

    <!-- 4. Account Exit Grouped Card -->
    <div class="w-full rounded-2xl bg-card/85 dark:bg-card/65 backdrop-blur-md border border-border/70 shadow-xs overflow-hidden select-none">
      <button
        type="button"
        @click="emit('logout')"
        class="w-full px-4 py-3.5 flex items-center gap-3 hover:bg-destructive/5 active:bg-destructive/10 transition-colors cursor-pointer text-start outline-none"
      >
        <LogOutIcon class="size-5 text-destructive shrink-0" />

        <span class="flex-1 text-[13px] font-medium text-destructive truncate">
          {{ languageStore.t('خروج از حساب کاربری', 'Log Out') }}
        </span>

        <ChevronLeftIcon
          v-if="languageStore.isFa"
          class="size-3.5 text-destructive/50 shrink-0"
        />
        <ChevronRightIcon
          v-else
          class="size-3.5 text-destructive/50 shrink-0"
        />
      </button>
    </div>
  </div>
</template>

