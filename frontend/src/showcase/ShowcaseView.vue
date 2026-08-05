<script setup lang="ts">
import { ref } from 'vue'

// Import ALL 27 base UI primitives installed in src/components/ui
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert'
import { 
  AlertDialog, 
  AlertDialogTrigger, 
  AlertDialogContent, 
  AlertDialogHeader, 
  AlertDialogTitle, 
  AlertDialogDescription, 
  AlertDialogFooter, 
  AlertDialogAction, 
  AlertDialogCancel 
} from '@/components/ui/alert-dialog'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Calendar } from '@/components/ui/calendar'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card'
import { Checkbox } from '@/components/ui/checkbox'
import { Collapsible, CollapsibleTrigger, CollapsibleContent } from '@/components/ui/collapsible'
import { 
  Dialog, 
  DialogTrigger, 
  DialogContent, 
  DialogHeader, 
  DialogTitle, 
  DialogDescription, 
  DialogFooter, 
  DialogClose 
} from '@/components/ui/dialog'
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from '@/components/ui/dropdown-menu'
import { Input } from '@/components/ui/input'
import { InputOTP, InputOTPGroup, InputOTPSlot } from '@/components/ui/input-otp'
import { Label } from '@/components/ui/label'
import { NativeSelect, NativeSelectOption } from '@/components/ui/native-select'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { Progress } from '@/components/ui/progress'
import { ScrollArea } from '@/components/ui/scroll-area'
import { 
  Select, 
  SelectTrigger, 
  SelectValue, 
  SelectContent, 
  SelectGroup, 
  SelectItem, 
  SelectLabel 
} from '@/components/ui/select'
import { Separator } from '@/components/ui/separator'
import { 
  Sheet, 
  SheetTrigger, 
  SheetContent, 
  SheetHeader, 
  SheetTitle, 
  SheetDescription, 
  SheetFooter 
} from '@/components/ui/sheet'
import { Skeleton } from '@/components/ui/skeleton'
import { Switch } from '@/components/ui/switch'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Textarea } from '@/components/ui/textarea'
import { Toggle } from '@/components/ui/toggle'
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group'

import { 
  SparklesIcon, 
  Trash2Icon, 
  PlusIcon, 
  SettingsIcon, 
  CalendarIcon, 
  LockIcon, 
  CheckCircle2Icon, 
  InfoIcon,
  LayoutGridIcon,
  RulerIcon,
  TypeIcon,
  HomeIcon,
  UserIcon,
  MailIcon,
  SearchIcon,
  CheckIcon,
  XIcon,
  AlertTriangleIcon,
  HelpCircleIcon,
  ArrowLeftIcon,
  ArrowRightIcon,
  ChevronDownIcon,
  ChevronUpIcon,
  MenuIcon,
  BellIcon,
  ActivityIcon,
  HeartIcon,
  StarIcon,
  ShieldIcon,
  Share2Icon,
  EyeIcon,
  BoldIcon,
  ItalicIcon,
  UnderlineIcon,
  SlidersIcon
} from '@lucide/vue'
import { getLocalTimeZone, today } from '@internationalized/date'

// Tabs management
const activeTab = ref<'components' | 'tokens'>('components')

// Interactive state variables
const inputVal = ref('')
const textareaVal = ref('')
const checkboxVal = ref(false)
const checkboxInteractive = ref(false)
const checkboxIndeterminate = ref<'indeterminate' | boolean>('indeterminate')
const switchVal = ref(false)
const switchSmVal = ref(false)
const otpVal = ref('')
const nativeSelectVal = ref('')
const customSelectVal = ref('')
const toggleState = ref(false)
const toggleGroupVal = ref('bold')
const collapsibleOpen = ref(false)
const progressVal = ref(65)
const dateVal = ref<any>(today(getLocalTimeZone()))
const isPending = ref(false)

const triggerSimulatedPending = () => {
  isPending.value = true
  setTimeout(() => {
    isPending.value = false
  }, 2000)
}

// Spacing System data
const spacings = [
  { value: '1', rem: '0.25rem', px: '4px' },
  { value: '2', rem: '0.5rem', px: '8px' },
  { value: '3', rem: '0.75rem', px: '12px' },
  { value: '4', rem: '1rem', px: '16px' },
  { value: '6', rem: '1.5rem', px: '24px' },
  { value: '8', rem: '2rem', px: '32px' },
  { value: '12', rem: '3rem', px: '48px' },
  { value: '16', rem: '4rem', px: '64px' },
]

// Theme colors list
const colors = [
  { name: 'Background', class: 'bg-background text-foreground border border-border/80', desc: 'پس‌زمینه اصلی پلتفرم', variable: '--background' },
  { name: 'Foreground', class: 'bg-foreground text-background', desc: 'متون و عناصر متضاد اصلی', variable: '--foreground' },
  { name: 'Primary', class: 'bg-primary text-primary-foreground', desc: 'رنگ اصلی پلتفرم و کنش‌ها', variable: '--primary' },
  { name: 'Secondary', class: 'bg-secondary text-secondary-foreground border border-border/40', desc: 'رنگ عناصر ثانویه و مکمل', variable: '--secondary' },
  { name: 'Muted', class: 'bg-muted text-muted-foreground', desc: 'متون کم‌اهمیت و فرعی', variable: '--muted' },
  { name: 'Accent', class: 'bg-accent text-accent-foreground', desc: 'رنگ برجسته‌سازی و حالت فعال', variable: '--accent' },
  { name: 'Destructive', class: 'bg-destructive text-destructive-foreground', desc: 'رنگ پیام‌های هشدار و حذف', variable: '--destructive' },
  { name: 'Card', class: 'bg-card text-card-foreground border border-border/80', desc: 'باکس‌ها و کارت‌ها', variable: '--card' },
  { name: 'Popover', class: 'bg-popover text-popover-foreground border border-border/80', desc: 'پاپ‌آپ‌های شناور', variable: '--popover' },
]

const systemBorders = [
  { name: 'Border', class: 'bg-border', variable: '--border', desc: 'مرزبندی‌ها' },
  { name: 'Input', class: 'bg-input', variable: '--input', desc: 'فیلدهای ورودی' },
  { name: 'Ring', class: 'bg-ring', variable: '--ring', desc: 'حلقه فوکوس' },
]

// Font Sizes Scale data
const fontSizes = [
  { name: 'text-xs', size: '0.75rem', px: '12px', class: 'text-xs' },
  { name: 'text-sm', size: '0.875rem', px: '14px', class: 'text-sm' },
  { name: 'text-base', size: '1rem', px: '16px', class: 'text-base' },
  { name: 'text-lg', size: '1.125rem', px: '18px', class: 'text-lg' },
  { name: 'text-xl', size: '1.25rem', px: '20px', class: 'text-xl' },
  { name: 'text-2xl', size: '1.5rem', px: '24px', class: 'text-2xl' },
  { name: 'text-3xl', size: '1.875rem', px: '30px', class: 'text-3xl' },
  { name: 'text-4xl', size: '2.25rem', px: '36px', class: 'text-4xl' },
  { name: 'text-5xl', size: '3rem', px: '48px', class: 'text-5xl' },
]

// Border Radius Scale data
const borderRadii = [
  { name: 'radius-sm', value: 'calc(var(--radius) * 0.6)', px: '4.8px', class: 'rounded-sm' },
  { name: 'radius-md', value: 'calc(var(--radius) * 0.8)', px: '6.4px', class: 'rounded-md' },
  { name: 'radius-lg', value: 'var(--radius)', px: '8px', class: 'rounded-lg' },
  { name: 'radius-xl', value: 'calc(var(--radius) * 1.4)', px: '11.2px', class: 'rounded-xl' },
  { name: 'radius-2xl', value: 'calc(var(--radius) * 1.8)', px: '14.4px', class: 'rounded-2xl' },
  { name: 'radius-3xl', value: 'calc(var(--radius) * 2.2)', px: '17.6px', class: 'rounded-3xl' },
]

// Popular Lucide Icons
const baseIcons = [
  { name: 'Home', icon: HomeIcon },
  { name: 'User', icon: UserIcon },
  { name: 'Settings', icon: SettingsIcon },
  { name: 'Mail', icon: MailIcon },
  { name: 'Lock', icon: LockIcon },
  { name: 'Calendar', icon: CalendarIcon },
  { name: 'Search', icon: SearchIcon },
  { name: 'Plus', icon: PlusIcon },
  { name: 'Trash2', icon: Trash2Icon },
  { name: 'Check', icon: CheckIcon },
  { name: 'X', icon: XIcon },
  { name: 'AlertTriangle', icon: AlertTriangleIcon },
  { name: 'Info', icon: InfoIcon },
  { name: 'HelpCircle', icon: HelpCircleIcon },
  { name: 'ArrowLeft', icon: ArrowLeftIcon },
  { name: 'ArrowRight', icon: ArrowRightIcon },
  { name: 'ChevronDown', icon: ChevronDownIcon },
  { name: 'ChevronUp', icon: ChevronUpIcon },
  { name: 'Menu', icon: MenuIcon },
  { name: 'Bell', icon: BellIcon },
  { name: 'Activity', icon: ActivityIcon },
  { name: 'Heart', icon: HeartIcon },
  { name: 'Star', icon: StarIcon },
  { name: 'Shield', icon: ShieldIcon },
  { name: 'Share2', icon: Share2Icon },
  { name: 'Eye', icon: EyeIcon },
]
</script>

<template>
  <div class="w-full flex justify-center dir-rtl text-right">
    <div class="w-full max-w-6xl py-10 px-4 sm:px-6 flex flex-col gap-8 sm:gap-12">
      
      <!-- Header -->
      <div class="border-b border-border/60 pb-6 flex flex-col md:flex-row md:items-end md:justify-between gap-6 w-full text-right">
        <div class="flex flex-col gap-2">
          <div class="flex items-center gap-2 text-primary justify-start">
            <SparklesIcon class="size-4" />
            <span class="text-[10px] font-bold uppercase tracking-wider text-primary/80">نمایشگاه دیزاین سیستم پلتفرم</span>
          </div>
          <h1 class="text-xl sm:text-2xl font-extrabold tracking-tight text-foreground">آلبوم کامپوننت‌های پایه (Primitives Showcase)</h1>
          <p class="text-muted-foreground text-xs mt-0.5">تست تمامی ۲۷ کامپوننت پایه نصبی شدسن (shadcn-vue)، تم رنگی، تایپوگرافی و فواصل.</p>
        </div>

        <!-- Tab Selectors -->
        <div class="flex bg-muted/60 p-1 rounded-xl border border-border/40 shrink-0 self-start md:self-auto">
          <button 
            @click="activeTab = 'components'"
            :class="[
              'px-4 py-1.5 rounded-lg text-xs font-semibold transition-all outline-none cursor-pointer',
              activeTab === 'components' ? 'bg-background text-foreground shadow-xs' : 'text-muted-foreground hover:text-foreground'
            ]"
          >
            کامپوننت‌های پایه (۲۷ کامپوننت)
          </button>
          <button 
            @click="activeTab = 'tokens'"
            :class="[
              'px-4 py-1.5 rounded-lg text-xs font-semibold transition-all outline-none cursor-pointer',
              activeTab === 'tokens' ? 'bg-background text-foreground shadow-xs' : 'text-muted-foreground hover:text-foreground'
            ]"
          >
            توکن‌های رنگ، تایپوگرافی و فواصل
          </button>
        </div>
      </div>

      <!-- TAB 1: COMPONENTS (PRIMITIVES) -->
      <div v-if="activeTab === 'components'" class="grid grid-cols-1 lg:grid-cols-2 gap-8 w-full">
        
        <!-- 1. Buttons & Toggles Panel (Button, Toggle, ToggleGroup) -->
        <div class="bg-card/30 border border-border/60 rounded-xl p-5 sm:p-6 shadow-xs flex flex-col gap-6">
          <div class="flex flex-col gap-1">
            <h2 class="text-sm font-extrabold text-foreground">۱. دکمه‌ها و تایتل‌ها (Button, Toggle, ToggleGroup)</h2>
            <p class="text-[11px] text-muted-foreground">واریانت‌های مختلف دکمه، وضعیت‌های لودینگ، سوئیچ تک‌حالته و گروه‌های انتخابی.</p>
          </div>

          <div class="flex flex-col gap-5 border-t border-border/40 pt-4">
            <!-- Buttons -->
            <div class="flex flex-col gap-2">
              <span class="text-[10px] font-bold uppercase text-muted-foreground">Button Variants:</span>
              <div class="flex flex-wrap gap-2">
                <Button size="sm">پیش‌فرض</Button>
                <Button size="sm" variant="secondary">ثانویه</Button>
                <Button size="sm" variant="outline">دورخط‌دار</Button>
                <Button size="sm" variant="destructive" class="gap-1.5">
                  <Trash2Icon class="size-3.5" />
                  مخرب
                </Button>
                <Button size="sm" variant="ghost">شیشه‌ای</Button>
                <Button size="sm" variant="link">لینک</Button>
              </div>
            </div>

            <!-- Pending / Loading Button -->
            <div class="flex flex-col gap-2">
              <span class="text-[10px] font-bold uppercase text-muted-foreground">Button States & Pending:</span>
              <div class="flex flex-wrap gap-2">
                <Button size="sm" disabled>غیرفعال</Button>
                <Button size="sm" :disabled="isPending" @click="triggerSimulatedPending">
                  <span v-if="isPending" class="flex items-center gap-1.5">
                    <span class="size-3 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin" />
                    در حال بارگذاری...
                  </span>
                  <span v-else>کلیک برای تست لودینگ</span>
                </Button>
              </div>
            </div>

            <!-- Toggle & ToggleGroup -->
            <div class="flex flex-col gap-2">
              <span class="text-[10px] font-bold uppercase text-muted-foreground">Toggle & ToggleGroup:</span>
              <div class="flex flex-wrap items-center gap-3">
                <Toggle v-model:pressed="toggleState" variant="outline" size="sm" class="gap-1">
                  <StarIcon class="size-3.5" :class="toggleState ? 'fill-primary text-primary' : ''" />
                  <span>تشیخص ستاره</span>
                </Toggle>

                <ToggleGroup type="single" v-model="toggleGroupVal" variant="outline" size="sm">
                  <ToggleGroupItem value="bold" aria-label="Bold">
                    <BoldIcon class="size-3.5" />
                  </ToggleGroupItem>
                  <ToggleGroupItem value="italic" aria-label="Italic">
                    <ItalicIcon class="size-3.5" />
                  </ToggleGroupItem>
                  <ToggleGroupItem value="underline" aria-label="Underline">
                    <UnderlineIcon class="size-3.5" />
                  </ToggleGroupItem>
                </ToggleGroup>
              </div>
            </div>
          </div>
        </div>

        <!-- 2. Form Inputs Panel (Input, Textarea, Select, NativeSelect, Checkbox, Switch, InputOTP) -->
        <div class="bg-card/30 border border-border/60 rounded-xl p-5 sm:p-6 shadow-xs flex flex-col gap-6">
          <div class="flex flex-col gap-1">
            <h2 class="text-sm font-extrabold text-foreground">۲. فیلدهای ورودی و فرم‌ها (Input, Textarea, Select, Checkbox, Switch, OTP)</h2>
            <p class="text-[11px] text-muted-foreground">انواع ورودی‌های متنی، سلکت‌های کشویی، چک‌باکس و کلیدهای روشن/خاموش.</p>
          </div>

          <div class="flex flex-col gap-4 border-t border-border/40 pt-4">
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div class="space-y-1">
                <Label for="inp-demo" class="text-xs">Input متنی:</Label>
                <Input id="inp-demo" v-model="inputVal" placeholder="متنی بنویسید..." class="text-xs" />
              </div>

              <div class="space-y-1">
                <Label for="sel-native" class="text-xs">NativeSelect بومی:</Label>
                <NativeSelect id="sel-native" v-model="nativeSelectVal" class="text-xs">
                  <NativeSelectOption value="">انتخاب کنید...</NativeSelectOption>
                  <NativeSelectOption value="opt1">گزینه اول</NativeSelectOption>
                  <NativeSelectOption value="opt2">گزینه دوم</NativeSelectOption>
                </NativeSelect>
              </div>
            </div>

            <!-- Custom Shadcn Select -->
            <div class="space-y-1">
              <Label class="text-xs">Select تخصصی shadcn:</Label>
              <Select v-model="customSelectVal">
                <SelectTrigger class="w-full text-xs">
                  <SelectValue placeholder="یک گزینه انتخاب کنید..." />
                </SelectTrigger>
                <SelectContent dir="rtl">
                  <SelectGroup>
                    <SelectLabel class="text-xs font-bold">دسته‌بندی‌ها</SelectLabel>
                    <SelectItem value="cat-1" class="text-xs">مدرسه و آموزش</SelectItem>
                    <SelectItem value="cat-2" class="text-xs">مسجد و حسینیه</SelectItem>
                    <SelectItem value="cat-3" class="text-xs">امور خیریه</SelectItem>
                  </SelectGroup>
                </SelectContent>
              </Select>
            </div>

            <!-- Textarea -->
            <div class="space-y-1">
              <Label for="txt-demo" class="text-xs">Textarea چند خطی:</Label>
              <Textarea id="txt-demo" v-model="textareaVal" placeholder="توضیحات تکمیلی را وارد کنید..." rows="2" class="text-xs" />
            </div>

            <!-- Checkbox & Switch -->
            <div class="flex flex-wrap items-center justify-between gap-4 pt-1">
              <div class="flex items-center gap-2">
                <Checkbox id="chk-demo" v-model:checked="checkboxVal" />
                <Label for="chk-demo" class="text-xs cursor-pointer">چک‌باکس انتخابی</Label>
              </div>

              <div class="flex items-center gap-2">
                <Label for="sw-demo" class="text-xs cursor-pointer">کلید سویچ:</Label>
                <Switch id="sw-demo" v-model:checked="switchVal" />
              </div>
            </div>

            <!-- InputOTP -->
            <div class="space-y-1.5 pt-1">
              <Label class="text-xs font-semibold">کد تایید پیامکی (InputOTP):</Label>
              <div dir="ltr" class="flex justify-start">
                <InputOTP v-model="otpVal" :maxlength="4">
                  <InputOTPGroup>
                    <InputOTPSlot :index="0" />
                    <InputOTPSlot :index="1" />
                    <InputOTPSlot :index="2" />
                    <InputOTPSlot :index="3" />
                  </InputOTPGroup>
                </InputOTP>
              </div>
            </div>
          </div>
        </div>

        <!-- 3. Data Display & Feedback (Badge, Avatar, Alert, Progress, Skeleton, Card, Separator) -->
        <div class="bg-card/30 border border-border/60 rounded-xl p-5 sm:p-6 shadow-xs flex flex-col gap-6">
          <div class="flex flex-col gap-1">
            <h2 class="text-sm font-extrabold text-foreground">۳. نمایش داده و بازخورد (Badge, Avatar, Alert, Progress, Skeleton, Card, Separator)</h2>
            <p class="text-[11px] text-muted-foreground">بج‌ها، آواتارها، هشدارهای اطلاع‌رسانی، نوار پیشرفت و کاردها.</p>
          </div>

          <div class="flex flex-col gap-5 border-t border-border/40 pt-4">
            <!-- Badges -->
            <div class="flex flex-col gap-2">
              <span class="text-[10px] font-bold uppercase text-muted-foreground">Badges:</span>
              <div class="flex flex-wrap gap-2">
                <Badge variant="default">پیش‌فرض</Badge>
                <Badge variant="secondary">ثانویه</Badge>
                <Badge variant="outline">دورخط‌دار</Badge>
                <Badge variant="destructive">مخرب</Badge>
              </div>
            </div>

            <!-- Avatars -->
            <div class="flex flex-col gap-2">
              <span class="text-[10px] font-bold uppercase text-muted-foreground">Avatars:</span>
              <div class="flex items-center gap-3">
                <Avatar class="size-9">
                  <AvatarImage src="https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=150&q=80" />
                  <AvatarFallback>RM</AvatarFallback>
                </Avatar>
                <Avatar class="size-9">
                  <AvatarFallback class="bg-primary/10 text-primary font-bold text-xs">ش‌م</AvatarFallback>
                </Avatar>
              </div>
            </div>

            <!-- Progress Bar -->
            <div class="space-y-1.5">
              <div class="flex justify-between items-center text-xs">
                <span class="text-muted-foreground">نوار پیشرفت (Progress):</span>
                <span class="font-bold text-primary">{{ progressVal }}٪</span>
              </div>
              <Progress :model-value="progressVal" class="h-2 w-full" />
            </div>

            <!-- Alert Component -->
            <Alert variant="default" class="bg-muted/30">
              <InfoIcon class="size-4 text-primary" />
              <AlertTitle class="text-xs font-bold">اطلاعیه دیزاین سیستم</AlertTitle>
              <AlertDescription class="text-xs text-muted-foreground">
                تمام کامپوننت‌های این بخش منطبق بر متغیرهای تم تاریک/روشن پلتفرم هستند.
              </AlertDescription>
            </Alert>

            <!-- Skeleton Loading -->
            <div class="space-y-2">
              <span class="text-[10px] font-bold uppercase text-muted-foreground">Skeleton Loading:</span>
              <div class="flex items-center gap-3">
                <Skeleton class="size-9 rounded-full" />
                <div class="space-y-1.5 w-full">
                  <Skeleton class="h-3.5 w-3/4" />
                  <Skeleton class="h-2.5 w-1/2" />
                </div>
              </div>
            </div>

            <Separator class="bg-border/60" />

            <!-- Simple Card Demo -->
            <Card class="bg-card/60 p-4 border border-border/60 rounded-xl space-y-1.5">
              <CardTitle class="text-xs font-bold">نمونه کارت بومی (Card Component)</CardTitle>
              <CardDescription class="text-[11px] text-muted-foreground">تشکیل شده از CardHeader, CardTitle, CardContent و CardFooter.</CardDescription>
            </Card>
          </div>
        </div>

        <!-- 4. Overlays & Dialogs (Dialog, AlertDialog, Sheet, Popover, DropdownMenu) -->
        <div class="bg-card/30 border border-border/60 rounded-xl p-5 sm:p-6 shadow-xs flex flex-col gap-6">
          <div class="flex flex-col gap-1">
            <h2 class="text-sm font-extrabold text-foreground">۴. لایه‌های شناور و دیالوگ‌ها (Dialog, AlertDialog, Sheet, Popover, DropdownMenu)</h2>
            <p class="text-[11px] text-muted-foreground">دیالوگ‌های مودال، هشدارهای تایید، کشوهای جانبی و منوهای شناور.</p>
          </div>

          <div class="flex flex-col gap-4 border-t border-border/40 pt-4">
            <div class="flex flex-wrap gap-2.5">
              <!-- Dialog Modal -->
              <Dialog>
                <DialogTrigger as-child>
                  <Button variant="outline" size="sm" class="gap-1.5">
                    <SparklesIcon class="size-3.5" />
                    <span>مودال دیالوگ (Dialog)</span>
                  </Button>
                </DialogTrigger>
                <DialogContent class="sm:max-w-md dir-rtl text-right rounded-2xl">
                  <DialogHeader>
                    <DialogTitle class="text-base font-bold">تست دیالوگ عمومی</DialogTitle>
                    <DialogDescription class="text-xs text-muted-foreground">این یک دیالوگ نمونه از کامپوننت پایه Dialog است.</DialogDescription>
                  </DialogHeader>
                  <DialogFooter>
                    <DialogClose as-child>
                      <Button size="sm" variant="outline">بستن</Button>
                    </DialogClose>
                  </DialogFooter>
                </DialogContent>
              </Dialog>

              <!-- AlertDialog -->
              <AlertDialog>
                <AlertDialogTrigger as-child>
                  <Button variant="destructive" size="sm" class="gap-1.5">
                    <AlertTriangleIcon class="size-3.5" />
                    <span>دیالوگ هشدار (AlertDialog)</span>
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent class="sm:max-w-md dir-rtl text-right rounded-2xl">
                  <AlertDialogHeader>
                    <AlertDialogTitle class="text-base font-bold">آیا مطمئن هستید؟</AlertDialogTitle>
                    <AlertDialogDescription class="text-xs text-muted-foreground">این عمل قابل بازگشت نخواهد بود.</AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter class="flex gap-2">
                    <AlertDialogCancel as-child>
                      <Button size="sm" variant="outline">انصراف</Button>
                    </AlertDialogCancel>
                    <AlertDialogAction as-child>
                      <Button size="sm" variant="destructive">حذف کن</Button>
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>

              <!-- Sheet Drawer -->
              <Sheet>
                <SheetTrigger as-child>
                  <Button variant="secondary" size="sm" class="gap-1.5">
                    <MenuIcon class="size-3.5" />
                    <span>کشوی جانبی (Sheet)</span>
                  </Button>
                </SheetTrigger>
                <SheetContent side="right" class="dir-rtl text-right">
                  <SheetHeader>
                    <SheetTitle class="text-base font-bold">پنل تنظیمات جانبی</SheetTitle>
                    <SheetDescription class="text-xs text-muted-foreground">نمونه کشوی بازشونده جانبی Sheet.</SheetDescription>
                  </SheetHeader>
                </SheetContent>
              </Sheet>

              <!-- Popover -->
              <Popover>
                <PopoverTrigger as-child>
                  <Button variant="outline" size="sm" class="gap-1.5">
                    <CalendarIcon class="size-3.5" />
                    <span>پاپ‌اور (Popover)</span>
                  </Button>
                </PopoverTrigger>
                <PopoverContent class="w-auto p-0" align="start">
                  <Calendar v-model="dateVal" initial-focus />
                </PopoverContent>
              </Popover>

              <!-- DropdownMenu -->
              <DropdownMenu>
                <DropdownMenuTrigger as-child>
                  <Button variant="outline" size="sm" class="gap-1.5">
                    <SlidersIcon class="size-3.5" />
                    <span>منوی کشویی (DropdownMenu)</span>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent dir="rtl" class="w-48">
                  <DropdownMenuItem class="text-xs cursor-pointer">ویرایش پروفایل</DropdownMenuItem>
                  <DropdownMenuItem class="text-xs cursor-pointer">تنظیمات اعلانات</DropdownMenuItem>
                  <DropdownMenuItem class="text-xs text-destructive cursor-pointer">خروج از حساب</DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </div>

        <!-- 5. Navigation, Layout & Utilities (Tabs, Calendar, Collapsible, ScrollArea) -->
        <div class="bg-card/30 border border-border/60 rounded-xl p-5 sm:p-6 shadow-xs flex flex-col gap-6 lg:col-span-2">
          <div class="flex flex-col gap-1">
            <h2 class="text-sm font-extrabold text-foreground">۵. ناوبری و کانتینرهای چیدمان (Tabs, Calendar, Collapsible, ScrollArea)</h2>
            <p class="text-[11px] text-muted-foreground">زبانه ها، تقویم جلالی/میلادی، کانتینرهای آکاردئونی بازشونده و محدوده اسکرول سفارشی.</p>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-6 border-t border-border/40 pt-4">
            <!-- Tabs & Collapsible -->
            <div class="space-y-4">
              <div class="space-y-1.5">
                <span class="text-[10px] font-bold uppercase text-muted-foreground">Tabs Component:</span>
                <Tabs default-value="tab1" class="w-full">
                  <TabsList class="grid w-full grid-cols-2 bg-muted/60 p-0.5 rounded-lg h-8">
                    <TabsTrigger value="tab1" class="text-xs h-7">زبانه ۱</TabsTrigger>
                    <TabsTrigger value="tab2" class="text-xs h-7">زبانه ۲</TabsTrigger>
                  </TabsList>
                  <TabsContent value="tab1" class="p-3 bg-muted/20 rounded-lg text-xs text-muted-foreground mt-2">
                    محتوای زبانه اول
                  </TabsContent>
                  <TabsContent value="tab2" class="p-3 bg-muted/20 rounded-lg text-xs text-muted-foreground mt-2">
                    محتوای زبانه دوم
                  </TabsContent>
                </Tabs>
              </div>

              <!-- Collapsible -->
              <div class="space-y-1.5">
                <span class="text-[10px] font-bold uppercase text-muted-foreground">Collapsible Component:</span>
                <Collapsible v-model:open="collapsibleOpen" class="w-full space-y-1 border border-border/50 p-2.5 rounded-xl bg-card/40">
                  <div class="flex items-center justify-between">
                    <span class="text-xs font-semibold">توضیحات بیشتر (آکاردئون)</span>
                    <CollapsibleTrigger as-child>
                      <Button variant="ghost" size="sm" class="h-6 w-6 p-0">
                        <ChevronDownIcon class="size-3.5 transition-transform" :class="collapsibleOpen ? 'rotate-180' : ''" />
                      </Button>
                    </CollapsibleTrigger>
                  </div>
                  <CollapsibleContent class="text-xs text-muted-foreground pt-2">
                    این محتوا با کلیک بر روی آکاردئون باز و بسته می‌شود.
                  </CollapsibleContent>
                </Collapsible>
              </div>
            </div>

            <!-- ScrollArea -->
            <div class="space-y-1.5">
              <span class="text-[10px] font-bold uppercase text-muted-foreground">ScrollArea Component:</span>
              <ScrollArea class="h-40 w-full rounded-xl border border-border/50 p-3 bg-card/40">
                <div class="space-y-2 text-xs">
                  <div v-for="i in 10" :key="i" class="p-2 bg-muted/30 rounded-lg border border-border/30">
                    آیتم اسکرول‌پذیر شماره {{ i }}
                  </div>
                </div>
              </ScrollArea>
            </div>
          </div>
        </div>

      </div>

      <!-- TAB 2: TOKENS -->
      <div v-else class="flex flex-col gap-10 w-full">
        <!-- Colors Grid -->
        <div class="flex flex-col gap-4">
          <h2 class="text-sm font-extrabold text-foreground">پالت رنگی پلتفرم (Semantic Theme Tokens)</h2>
          <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
            <div 
              v-for="c in colors" 
              :key="c.name"
              class="p-4 rounded-xl shadow-xs flex flex-col gap-2 justify-between"
              :class="c.class"
            >
              <div class="flex justify-between items-center">
                <span class="font-bold text-xs">{{ c.name }}</span>
                <span class="text-[10px] opacity-75 font-mono">{{ c.variable }}</span>
              </div>
              <span class="text-[11px] opacity-85 leading-relaxed">{{ c.desc }}</span>
            </div>
          </div>
        </div>

        <!-- Typography Sizes -->
        <div class="flex flex-col gap-4">
          <h2 class="text-sm font-extrabold text-foreground">تایپوگرافی و فونت متغیر (Typography Scale)</h2>
          <div class="flex flex-col gap-2 bg-card/40 border border-border/60 p-4 rounded-xl">
            <div v-for="f in fontSizes" :key="f.name" class="flex items-center justify-between p-2 border-b border-border/40 last:border-0">
              <span class="text-xs font-mono text-muted-foreground">{{ f.name }} ({{ f.size }} / {{ f.px }})</span>
              <span :class="f.class" class="font-bold text-foreground">نمونه متن با سایز {{ f.name }}</span>
            </div>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>
