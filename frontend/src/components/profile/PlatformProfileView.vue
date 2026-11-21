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
  LayoutGridIcon,
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
</script>

<template>
  <div class="w-full flex flex-col gap-6 pb-20 select-none font-sans" :dir="languageStore.dir">
    
    <!-- ======================================================================= -->
    <!-- 1. INSTAGRAM HERO PROFILE HEADER (Responsive: Mobile + Desktop/Laptop)   -->
    <!-- ======================================================================= -->
    <div v-if="userProfile" class="w-full">
      
      <!-- DESKTOP / LAPTOP HERO (md: and up) -->
      <div class="hidden md:flex items-center gap-10 py-4 px-2 w-full">
        <!-- Large Avatar (size-32 / 128px) -->
        <div class="relative shrink-0">
          <div class="size-32 rounded-full ring-2 ring-border/80 p-1 flex items-center justify-center bg-card shadow-sm">
            <div class="size-full rounded-full overflow-hidden bg-primary/10 flex items-center justify-center text-primary">
              <img
                v-if="userProfile.avatar"
                :src="userProfile.avatar"
                :alt="userProfile.name"
                class="size-full object-cover"
              />
              <span v-else-if="nameLetter" class="text-4xl font-black">
                {{ nameLetter }}
              </span>
              <UserIcon v-else class="size-14" />
            </div>
          </div>
          <!-- Status dot -->
          <span
            class="absolute bottom-2 end-2 size-5 rounded-full border-3 border-background"
            :class="statusDotClass"
            :title="userProfile.statusText || 'Active'"
          />
        </div>

        <!-- Details Column -->
        <div class="flex-1 min-w-0 flex flex-col gap-4 text-start justify-center">
          
          <!-- Row 1: Username / Display Name + Action Buttons -->
          <div class="flex items-center gap-3.5 flex-wrap">
            <h2 class="text-2xl font-bold text-foreground tracking-tight truncate select-all">
              {{ userProfile.name }}
            </h2>

            <!-- Status Badge if present -->
            <span
              v-if="userProfile.statusText"
              class="px-2.5 py-0.5 rounded-full bg-primary/10 border border-primary/25 text-primary text-xs font-semibold"
            >
              {{ userProfile.statusText }}
            </span>

            <!-- Edit Profile Button (Instagram Style) -->
            <button
              type="button"
              @click="emit('edit')"
              class="h-9 px-4 rounded-xl bg-secondary/80 hover:bg-secondary text-secondary-foreground text-xs font-bold transition-all duration-200 flex items-center gap-1.5 cursor-pointer active:scale-95 shadow-xs"
            >
              <PencilIcon class="size-3.5 shrink-0" />
              <span>{{ languageStore.t('ویرایش پروفایل', 'Edit Profile') }}</span>
            </button>

            <!-- Quick Dark Mode Toggle Button -->
            <button
              type="button"
              @click="emit('update:dark', !dark)"
              class="size-9 rounded-xl bg-secondary/80 hover:bg-secondary text-muted-foreground hover:text-foreground transition-all duration-200 flex items-center justify-center cursor-pointer active:scale-95 shadow-xs"
              :title="dark ? languageStore.t('حالت روشن', 'Light Mode') : languageStore.t('حالت تاریک', 'Dark Mode')"
            >
              <SunIcon v-if="dark" class="size-4 text-amber-400" />
              <MoonIcon v-else class="size-4" />
            </button>

            <!-- Quick Logout Button -->
            <button
              type="button"
              @click="emit('logout')"
              class="size-9 rounded-xl bg-destructive/10 hover:bg-destructive/20 text-destructive transition-all duration-200 flex items-center justify-center cursor-pointer active:scale-95 shadow-xs"
              :title="languageStore.t('خروج از حساب کاربری', 'Log Out')"
            >
              <LogOutIcon class="size-4" />
            </button>
          </div>

          <!-- Row 2: Inline Stats (Like Instagram: 0 posts, 73 followers, 191 following) -->
          <div class="flex items-center gap-8 text-base">
            <div v-for="stat in stats" :key="'desktop-' + stat.key" class="flex items-baseline gap-1.5">
              <span class="font-extrabold text-foreground text-lg">
                {{ languageStore.n(stat.value) }}
              </span>
              <span class="text-muted-foreground text-sm font-medium">
                {{ stat.label }}
              </span>
            </div>
          </div>

          <!-- Row 3: Phone / Bio -->
          <div class="flex flex-col text-start gap-1">
            <span class="text-sm text-muted-foreground font-semibold dir-ltr text-start select-all">
              {{ languageStore.n(userProfile.phone) }}
            </span>
          </div>

        </div>
      </div>

      <!-- MOBILE HERO (< md) -->
      <div class="md:hidden flex flex-col gap-4 p-2 w-full">
        <div class="flex items-center gap-4">
          <!-- Avatar (size-20) -->
          <div class="relative shrink-0">
            <div class="size-20 rounded-full ring-2 ring-border/80 p-0.5 flex items-center justify-center bg-card shadow-sm">
              <div class="size-full rounded-full overflow-hidden bg-primary/10 flex items-center justify-center text-primary">
                <img
                  v-if="userProfile.avatar"
                  :src="userProfile.avatar"
                  :alt="userProfile.name"
                  class="size-full object-cover"
                />
                <span v-else-if="nameLetter" class="text-2xl font-black">
                  {{ nameLetter }}
                </span>
                <UserIcon v-else class="size-8" />
              </div>
            </div>
            <span
              class="absolute bottom-1 end-1 size-3.5 rounded-full border-2 border-background"
              :class="statusDotClass"
            />
          </div>

          <!-- Mobile Stats next to avatar -->
          <div class="flex-1 grid grid-cols-3 gap-2 text-center">
            <div v-for="stat in stats" :key="'mobile-' + stat.key" class="flex flex-col items-center">
              <span class="text-base font-black text-foreground">
                {{ languageStore.n(stat.value) }}
              </span>
              <span class="text-[11px] font-medium text-muted-foreground mt-0.5">
                {{ stat.label }}
              </span>
            </div>
          </div>
        </div>

        <!-- Name & Phone -->
        <div class="flex flex-col text-start gap-0.5">
          <div class="flex items-center gap-2">
            <h3 class="text-base font-bold text-foreground truncate select-all">
              {{ userProfile.name }}
            </h3>
            <span
              v-if="userProfile.statusText"
              class="px-2 py-0.5 rounded-full bg-primary/10 text-primary text-[10px] font-bold"
            >
              {{ userProfile.statusText }}
            </span>
          </div>
          <span class="text-xs text-muted-foreground font-medium dir-ltr text-start select-all">
            {{ languageStore.n(userProfile.phone) }}
          </span>
        </div>

        <!-- Action Buttons (Full width Edit Profile + Dark Mode + Logout) -->
        <div class="flex items-center gap-2 w-full mt-1">
          <button
            type="button"
            @click="emit('edit')"
            class="flex-1 h-9 rounded-xl bg-secondary/80 hover:bg-secondary text-secondary-foreground text-xs font-bold transition-all flex items-center justify-center gap-1.5 cursor-pointer active:scale-95 shadow-xs"
          >
            <PencilIcon class="size-3.5 shrink-0" />
            <span>{{ languageStore.t('ویرایش حساب کاربری', 'Edit Profile') }}</span>
          </button>

          <button
            type="button"
            @click="emit('update:dark', !dark)"
            class="size-9 rounded-xl bg-secondary/80 hover:bg-secondary text-muted-foreground hover:text-foreground transition-all flex items-center justify-center cursor-pointer active:scale-95 shadow-xs"
            :title="dark ? languageStore.t('حالت روشن', 'Light Mode') : languageStore.t('حالت تاریک', 'Dark Mode')"
          >
            <SunIcon v-if="dark" class="size-4 text-amber-400" />
            <MoonIcon v-else class="size-4" />
          </button>

          <button
            type="button"
            @click="emit('logout')"
            class="size-9 rounded-xl bg-destructive/10 hover:bg-destructive/20 text-destructive transition-all flex items-center justify-center cursor-pointer active:scale-95 shadow-xs"
            :title="languageStore.t('خروج از حساب کاربری', 'Log Out')"
          >
            <LogOutIcon class="size-4" />
          </button>
        </div>
      </div>

    </div>

    <!-- ======================================================================= -->
    <!-- 2. INSTAGRAM STORY HIGHLIGHTS (Circular Feature Shortcuts)               -->
    <!-- ======================================================================= -->
    <div class="w-full flex items-center gap-5 md:gap-7 overflow-x-auto py-2 px-2 no-scrollbar">
      <!-- 1. Bookshelf Highlight -->
      <div 
        @click="emit('open-shelf')"
        class="flex flex-col items-center gap-2 cursor-pointer group shrink-0"
      >
        <div class="size-16 md:size-20 rounded-full ring-2 ring-border/80 group-hover:ring-primary/60 p-1 transition-all duration-200 flex items-center justify-center bg-card shadow-xs group-hover:scale-105">
          <div class="size-full rounded-full bg-primary/10 group-hover:bg-primary/20 flex items-center justify-center text-primary transition-colors">
            <BookOpenIcon class="size-7 md:size-8" />
          </div>
        </div>
        <div class="flex items-center gap-1 max-w-[80px]">
          <span class="text-xs font-semibold text-foreground group-hover:text-primary transition-colors truncate">
            {{ languageStore.t('قفسه کتاب', 'Bookshelf') }}
          </span>
          <Badge v-if="userProfile?.shelf_books_count" variant="secondary" class="h-4 px-1 text-[10px] shrink-0 font-bold">
            {{ languageStore.n(userProfile.shelf_books_count) }}
          </Badge>
        </div>
      </div>

      <!-- 2. Donations Highlight -->
      <div 
        @click="emit('open-donations')"
        class="flex flex-col items-center gap-2 cursor-pointer group shrink-0"
      >
        <div class="size-16 md:size-20 rounded-full ring-2 ring-border/80 group-hover:ring-primary/60 p-1 transition-all duration-200 flex items-center justify-center bg-card shadow-xs group-hover:scale-105">
          <div class="size-full rounded-full bg-primary/10 group-hover:bg-primary/20 flex items-center justify-center text-primary transition-colors">
            <HandHeartIcon class="size-7 md:size-8" />
          </div>
        </div>
        <div class="flex items-center gap-1 max-w-[80px]">
          <span class="text-xs font-semibold text-foreground group-hover:text-primary transition-colors truncate">
            {{ languageStore.t('پویش‌ها', 'Donations') }}
          </span>
          <Badge v-if="userProfile?.donations_count" variant="secondary" class="h-4 px-1 text-[10px] shrink-0 font-bold">
            {{ languageStore.n(userProfile.donations_count) }}
          </Badge>
        </div>
      </div>

      <!-- 3. Messenger Connections Highlight -->
      <div 
        @click="emit('open-connections')"
        class="flex flex-col items-center gap-2 cursor-pointer group shrink-0"
      >
        <div class="size-16 md:size-20 rounded-full ring-2 ring-border/80 group-hover:ring-primary/60 p-1 transition-all duration-200 flex items-center justify-center bg-card shadow-xs group-hover:scale-105">
          <div class="size-full rounded-full bg-primary/10 group-hover:bg-primary/20 flex items-center justify-center text-primary transition-colors">
            <LinkIcon class="size-7 md:size-8" />
          </div>
        </div>
        <div class="flex items-center gap-1.5 max-w-[85px]">
          <span class="text-xs font-semibold text-foreground group-hover:text-primary transition-colors truncate">
            {{ languageStore.t('اتصالات', 'Connections') }}
          </span>
          <span
            class="size-2 rounded-full shrink-0"
            :class="connectionsBadgeVariant === 'destructive' ? 'bg-destructive' : 'bg-emerald-500'"
          />
        </div>
      </div>

      <!-- 4. Language Highlight -->
      <div 
        @click="emit('open-language')"
        class="flex flex-col items-center gap-2 cursor-pointer group shrink-0"
      >
        <div class="size-16 md:size-20 rounded-full ring-2 ring-border/80 group-hover:ring-primary/60 p-1 transition-all duration-200 flex items-center justify-center bg-card shadow-xs group-hover:scale-105">
          <div class="size-full rounded-full bg-primary/10 group-hover:bg-primary/20 flex items-center justify-center text-primary transition-colors">
            <LanguagesIcon class="size-7 md:size-8" />
          </div>
        </div>
        <span class="text-xs font-semibold text-foreground group-hover:text-primary transition-colors truncate">
          {{ languageStore.currentLanguage.toUpperCase() }}
        </span>
      </div>
    </div>

    <!-- ======================================================================= -->
    <!-- 3. INSTAGRAM TAB DIVIDER & OPTIONS GRID                                  -->
    <!-- ======================================================================= -->
    <div class="w-full border-t border-border/50 pt-6">
      
      <!-- Instagram-Style Tab Header -->
      <div class="flex items-center justify-center gap-8 -mt-[25px] mb-6">
        <div class="border-t-2 border-foreground pt-3 flex items-center gap-2 text-xs font-bold text-foreground cursor-pointer tracking-wider uppercase">
          <LayoutGridIcon class="size-3.5 shrink-0" />
          <span>{{ languageStore.t('تنظیمات و دسترسی‌ها', 'Options & Access') }}</span>
        </div>
      </div>

      <!-- Compact, Comfortable 2-Column Grid on Laptop/Desktop (1-Column on Mobile) -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-3 w-full">
        
        <!-- Tile 1: Bookshelf -->
        <button
          type="button"
          @click="emit('open-shelf')"
          class="w-full p-4 rounded-2xl bg-card/60 hover:bg-card/90 border border-border/60 hover:border-border transition-all duration-200 flex items-center justify-between gap-3 text-start cursor-pointer shadow-xs active:scale-[0.99] group"
        >
          <div class="flex items-center gap-3.5 min-w-0">
            <div class="size-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center shrink-0 group-hover:scale-105 transition-transform">
              <BookOpenIcon class="size-5" />
            </div>
            <div class="flex flex-col text-start">
              <span class="text-sm font-bold text-foreground truncate">
                {{ languageStore.t('قفسه کتاب من', 'My Bookshelf') }}
              </span>
              <span class="text-[11px] text-muted-foreground font-medium">
                {{ languageStore.t('مشاهده و مدیریت کتاب‌های اهدا شده', 'Manage donated books') }}
              </span>
            </div>
          </div>
          <div class="flex items-center gap-2 shrink-0">
            <Badge variant="secondary" class="text-xs font-bold px-2 py-0.5 rounded-lg">
              {{ languageStore.n(userProfile?.shelf_books_count ?? 0) }}
            </Badge>
            <ChevronLeftIcon v-if="languageStore.isFa" class="size-4 text-muted-foreground group-hover:translate-x-[-2px] transition-transform" />
            <ChevronRightIcon v-else class="size-4 text-muted-foreground group-hover:translate-x-[2px] transition-transform" />
          </div>
        </button>

        <!-- Tile 2: Donations -->
        <button
          type="button"
          @click="emit('open-donations')"
          class="w-full p-4 rounded-2xl bg-card/60 hover:bg-card/90 border border-border/60 hover:border-border transition-all duration-200 flex items-center justify-between gap-3 text-start cursor-pointer shadow-xs active:scale-[0.99] group"
        >
          <div class="flex items-center gap-3.5 min-w-0">
            <div class="size-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center shrink-0 group-hover:scale-105 transition-transform">
              <HandHeartIcon class="size-5" />
            </div>
            <div class="flex flex-col text-start">
              <span class="text-sm font-bold text-foreground truncate">
                {{ languageStore.t('پویش‌های اهدا', 'Donation Campaigns') }}
              </span>
              <span class="text-[11px] text-muted-foreground font-medium">
                {{ languageStore.t('مشارکت در اهدا و نیکوکاری', 'Participate in charity') }}
              </span>
            </div>
          </div>
          <div class="flex items-center gap-2 shrink-0">
            <Badge variant="secondary" class="text-xs font-bold px-2 py-0.5 rounded-lg">
              {{ languageStore.n(userProfile?.donations_count ?? 0) }}
            </Badge>
            <ChevronLeftIcon v-if="languageStore.isFa" class="size-4 text-muted-foreground group-hover:translate-x-[-2px] transition-transform" />
            <ChevronRightIcon v-else class="size-4 text-muted-foreground group-hover:translate-x-[2px] transition-transform" />
          </div>
        </button>

        <!-- Tile 3: Messenger Connections -->
        <button
          type="button"
          @click="emit('open-connections')"
          class="w-full p-4 rounded-2xl bg-card/60 hover:bg-card/90 border border-border/60 hover:border-border transition-all duration-200 flex items-center justify-between gap-3 text-start cursor-pointer shadow-xs active:scale-[0.99] group"
        >
          <div class="flex items-center gap-3.5 min-w-0">
            <div class="size-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center shrink-0 group-hover:scale-105 transition-transform">
              <LinkIcon class="size-5" />
            </div>
            <div class="flex flex-col text-start">
              <span class="text-sm font-bold text-foreground truncate">
                {{ languageStore.t('اتصالات پیام‌رسان', 'Messenger Connections') }}
              </span>
              <span class="text-[11px] text-muted-foreground font-medium">
                {{ languageStore.t('اتصال به بله و تلگرام', 'Telegram & Bale bot sync') }}
              </span>
            </div>
          </div>
          <div class="flex items-center gap-2 shrink-0">
            <Badge :variant="connectionsBadgeVariant" class="text-xs font-bold px-2 py-0.5 rounded-lg">
              {{ connectionsBadgeText }}
            </Badge>
            <ChevronLeftIcon v-if="languageStore.isFa" class="size-4 text-muted-foreground group-hover:translate-x-[-2px] transition-transform" />
            <ChevronRightIcon v-else class="size-4 text-muted-foreground group-hover:translate-x-[2px] transition-transform" />
          </div>
        </button>

        <!-- Tile 4: Language -->
        <button
          type="button"
          @click="emit('open-language')"
          class="w-full p-4 rounded-2xl bg-card/60 hover:bg-card/90 border border-border/60 hover:border-border transition-all duration-200 flex items-center justify-between gap-3 text-start cursor-pointer shadow-xs active:scale-[0.99] group"
        >
          <div class="flex items-center gap-3.5 min-w-0">
            <div class="size-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center shrink-0 group-hover:scale-105 transition-transform">
              <LanguagesIcon class="size-5" />
            </div>
            <div class="flex flex-col text-start">
              <span class="text-sm font-bold text-foreground truncate">
                {{ languageStore.t('زبان برنامه (Language)', 'App Language (Language)') }}
              </span>
              <span class="text-[11px] text-muted-foreground font-medium">
                {{ languageStore.t('تغییر زبان به فارسی یا انگلیسی', 'Switch Persian / English') }}
              </span>
            </div>
          </div>
          <div class="flex items-center gap-2 shrink-0">
            <Badge variant="secondary" class="text-xs font-bold px-2 py-0.5 rounded-lg">
              {{ languageStore.currentLanguage.toUpperCase() }}
            </Badge>
            <ChevronLeftIcon v-if="languageStore.isFa" class="size-4 text-muted-foreground group-hover:translate-x-[-2px] transition-transform" />
            <ChevronRightIcon v-else class="size-4 text-muted-foreground group-hover:translate-x-[2px] transition-transform" />
          </div>
        </button>

        <!-- Tile 5: Dark Mode Toggle Card -->
        <div
          @click="emit('update:dark', !dark)"
          class="w-full p-4 rounded-2xl bg-card/60 hover:bg-card/90 border border-border/60 hover:border-border transition-all duration-200 flex items-center justify-between gap-3 text-start cursor-pointer shadow-xs active:scale-[0.99] group select-none"
        >
          <div class="flex items-center gap-3.5 min-w-0">
            <div class="size-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center shrink-0 group-hover:scale-105 transition-transform">
              <SunIcon v-if="dark" class="size-5 text-amber-400" />
              <MoonIcon v-else class="size-5 text-primary" />
            </div>
            <div class="flex flex-col text-start">
              <span class="text-sm font-bold text-foreground truncate">
                {{ languageStore.t('حالت نمایش (تم)', 'Display Theme') }}
              </span>
              <span class="text-[11px] text-muted-foreground font-medium">
                {{ dark ? languageStore.t('حالت تاریک فعال است', 'Dark mode active') : languageStore.t('حالت روشن فعال است', 'Light mode active') }}
              </span>
            </div>
          </div>
          <div class="shrink-0" @click.stop>
            <Switch :checked="dark" @update:checked="emit('update:dark', $event)" />
          </div>
        </div>

        <!-- Tile 6: Log Out Card -->
        <button
          type="button"
          @click="emit('logout')"
          class="w-full p-4 rounded-2xl bg-destructive/5 hover:bg-destructive/10 border border-destructive/20 hover:border-destructive/30 transition-all duration-200 flex items-center justify-between gap-3 text-start cursor-pointer shadow-xs active:scale-[0.99] group select-none"
        >
          <div class="flex items-center gap-3.5 min-w-0">
            <div class="size-10 rounded-xl bg-destructive/10 text-destructive flex items-center justify-center shrink-0 group-hover:scale-105 transition-transform">
              <LogOutIcon class="size-5" />
            </div>
            <div class="flex flex-col text-start">
              <span class="text-sm font-bold text-destructive truncate">
                {{ languageStore.t('خروج از حساب کاربری', 'Log Out') }}
              </span>
              <span class="text-[11px] text-destructive/70 font-medium">
                {{ languageStore.t('پایان نشست فعلی', 'End current session') }}
              </span>
            </div>
          </div>
          <ChevronLeftIcon v-if="languageStore.isFa" class="size-4 text-destructive/60 group-hover:translate-x-[-2px] transition-transform" />
          <ChevronRightIcon v-else class="size-4 text-destructive/60 group-hover:translate-x-[2px] transition-transform" />
        </button>

      </div>
    </div>

  </div>
</template>
