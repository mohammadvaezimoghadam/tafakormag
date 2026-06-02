<template>
  <div class="space-y-6 pt-4 max-w-md mx-auto text-right">
    <!-- تب‌های شیک پروفایل -->
    <div class="flex bg-white p-1 rounded-2xl border border-gray-100 shadow-sm">
      <button
        @click="activeTab = 'connections'"
        :class="activeTab === 'connections' ? 'bg-indigo-600 text-white shadow-md' : 'text-gray-500 hover:text-indigo-600 hover:bg-indigo-50/50'"
        class="flex-1 py-2.5 rounded-xl font-extrabold text-xs transition-all duration-300 active:scale-95"
      >
        🔌 اتصالات پیام‌رسان
      </button>
      <button
        @click="activeTab = 'account'"
        :class="activeTab === 'account' ? 'bg-indigo-600 text-white shadow-md' : 'text-gray-500 hover:text-indigo-600 hover:bg-indigo-50/50'"
        class="flex-1 py-2.5 rounded-xl font-extrabold text-xs transition-all duration-300 active:scale-95"
      >
        👤 حساب کاربری
      </button>
    </div>

    <!-- بدنه تب‌ها با ترانزیشن -->
    <Transition name="fade" mode="out-in">
      <!-- تب حساب کاربری -->
      <div v-if="activeTab === 'account'" class="space-y-5" :key="'account'">
        <!-- بخش فرم اطلاعات کاربر -->
        <div class="bg-white p-5 rounded-3xl border border-gray-100 shadow-sm space-y-4">
          <h3 class="text-sm font-black text-gray-800 border-b border-gray-50 pb-2 mb-1">ویرایش مشخصات شخصی</h3>

          <!-- عکس پروفایل -->
          <div class="flex flex-col items-center justify-center space-y-3 pb-2">
            <div class="relative shrink-0 group">
              <img
                v-if="profileImagePreview || currentProfileImageUrl"
                :src="profileImagePreview || currentProfileImageUrl"
                class="w-20 h-20 rounded-full object-cover border-2 border-indigo-500 shadow-md"
              />
              <div
                v-else
                class="w-20 h-20 bg-gradient-to-tr from-indigo-500 to-indigo-700 text-white rounded-full flex items-center justify-center font-black text-2xl shadow-lg border-2 border-indigo-400"
              >
                {{ profile.first_name ? profile.first_name.charAt(0) : 'U' }}
              </div>
              <!-- دکمه ویرایش آواتار -->
              <label class="absolute bottom-0 right-0 w-7 h-7 bg-indigo-600 hover:bg-indigo-700 text-white rounded-full flex items-center justify-center cursor-pointer shadow border border-white active:scale-90 transition-transform">
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                <input type="file" @change="handleProfileImageChange" accept="image/*" class="hidden" />
              </label>
            </div>
            <span class="text-[10px] text-gray-400">شماره حساب: <span class="font-bold text-gray-600">{{ profile.phone }}</span></span>
          </div>

          <!-- فیلدهای ورودی نام و فامیلی -->
          <BaseInput
            v-model="profileForm.first_name"
            label="نام"
            placeholder="نام خود را وارد کنید..."
          />

          <BaseInput
            v-model="profileForm.last_name"
            label="نام خانوادگی"
            placeholder="نام خانوادگی خود را وارد کنید..."
          />

          <!-- دکمه ذخیره پروفایل -->
          <BaseButton
            @click="handleSaveProfile"
            :loading="savingProfile"
            variant="primary"
            class="w-full rounded-2xl py-3 font-extrabold shadow-md mt-2"
          >
            ذخیره اطلاعات کاربری
          </BaseButton>
        </div>
      </div>

      <!-- تب اتصالات پیام‌رسان -->
      <div v-else class="space-y-4" :key="'connections'">
        <PlatformConnect
          platform="telegram"
          :connected="profile.is_telegram_bot_connected"
          :bot-username="profile.telegram_bot_username"
          @updated="loadProfile"
        />

        <PlatformConnect
          platform="bale"
          :connected="profile.is_bale_bot_connected"
          :bot-username="profile.bale_bot_username"
          @updated="loadProfile"
        />

        <!-- بخش کد اتصال برای ربات‌ها -->
        <div class="p-5 bg-white rounded-2xl shadow-sm border border-gray-100 space-y-4 text-right">
          <h3 class="text-xs font-black text-gray-800 border-b border-gray-50 pb-2 mb-1 flex items-center justify-between">
            <span>🔗 اتصال حساب کاربری به ربات</span>
          </h3>
          <p class="text-[11px] text-gray-400 leading-relaxed">
            جهت اتصال امن حساب کاربری خود به ربات‌ها (بدون نیاز به اشتراک‌گذاری مخاطب)، توکن اتصال خود را دریافت نموده و آن را به پی‌وی ربات مربوطه بفرستید.
          </p>
          
          <div class="flex flex-col gap-2">
            <div class="flex gap-2">
              <BaseButton
                @click="generateConnectToken('telegram')"
                :loading="loadingTgToken"
                variant="outline"
                size="sm"
                class="flex-1 text-[10px]"
              >
                دریافت توکن تلگرام
              </BaseButton>
              <BaseButton
                @click="generateConnectToken('bale')"
                :loading="loadingBaleToken"
                variant="outline"
                size="sm"
                class="flex-1 text-[10px]"
              >
                دریافت توکن بله
              </BaseButton>
            </div>
            
            <Transition name="fade">
              <div v-if="connectionToken" class="mt-2 p-3 bg-gray-50 rounded-xl border border-gray-100 flex flex-col gap-2">
                <div class="flex justify-between items-center text-[10px] text-gray-400">
                  <span>توکن موقت شما (اعتبار ۱۰ دقیقه):</span>
                  <button @click="copyToken" class="text-indigo-600 hover:underline font-bold">کپی کردن</button>
                </div>
                <span class="font-mono text-center font-bold text-gray-700 break-all select-all text-xs bg-white py-2 px-3 rounded-lg border border-gray-150">
                  {{ connectionToken }}
                </span>
                <p class="text-[10px] text-amber-600 text-center">
                  ⚠️ این توکن را کپی کرده و به پی‌وی ربات {{ tokenPlatform === 'telegram' ? 'تلگرام' : 'بله' }} بفرستید.
                </p>
              </div>
            </Transition>
          </div>
        </div>
      </div>
    </Transition>

    <!-- دکمه خروج در انتهای صفحه -->
    <div class="pt-4 border-t border-gray-150">
      <BaseButton
        variant="danger"
        @click="handleLogout"
        class="w-full rounded-2xl py-3 font-extrabold shadow"
      >
        🚪 خروج از حساب کاربری
      </BaseButton>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../composables/useAuth'
import PlatformConnect from '../components/profile/PlatformConnect.vue'
import BaseButton from '../components/ui/BaseButton.vue'
import BaseInput from '../components/ui/BaseInput.vue'
import { fetchProfile, updateProfile, getConnectToken } from '../api'
import { useToast } from '../composables/useToast'

const router = useRouter()
const { logout } = useAuth()
const { showToast } = useToast()

const activeTab = ref('connections')

const profile = ref({
  phone: '',
  first_name: '',
  last_name: '',
  profile_image: null,
  is_telegram_bot_connected: false,
  telegram_bot_username: '',
  is_bale_bot_connected: false,
  bale_bot_username: '',
})

const profileForm = reactive({
  first_name: '',
  last_name: ''
})

const selectedProfileImage = ref(null)
const profileImagePreview = ref('')
const savingProfile = ref(false)

const currentProfileImageUrl = computed(() => {
  if (!profile.value.profile_image) return ''
  const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
  if (profile.value.profile_image.startsWith('http://') || profile.value.profile_image.startsWith('https://')) {
    return profile.value.profile_image
  }
  if (apiBase === '/') {
    return profile.value.profile_image
  }
  const base = apiBase.endsWith('/') ? apiBase.slice(0, -1) : apiBase
  const path = profile.value.profile_image.startsWith('/') ? profile.value.profile_image : '/' + profile.value.profile_image
  return `${base}${path}`
})

const loadProfile = async () => {
  try {
    const res = await fetchProfile()
    profile.value = res.data
    profileForm.first_name = res.data.first_name || ''
    profileForm.last_name = res.data.last_name || ''
    if (res.data?.phone) {
      localStorage.setItem('user_phone', res.data.phone)
    }
  } catch (err) {
    // خطا توسط اینترسپتور مدیریت می‌شود
  }
}

const handleProfileImageChange = (e) => {
  const file = e.target.files[0]
  if (!file) return
  selectedProfileImage.value = file

  const reader = new FileReader()
  reader.onload = (event) => {
    profileImagePreview.value = event.target.result
  }
  reader.readAsDataURL(file)
}

const handleSaveProfile = async () => {
  savingProfile.value = true
  try {
    const formData = new FormData()
    formData.append('first_name', profileForm.first_name)
    formData.append('last_name', profileForm.last_name)
    if (selectedProfileImage.value) {
      formData.append('profile_image', selectedProfileImage.value)
    }

    const res = await updateProfile(formData)
    profile.value = res.data
    showToast('اطلاعات کاربری با موفقیت به‌روزرسانی شد.', 'success')
    profileImagePreview.value = ''
    selectedProfileImage.value = null
  } catch (err) {
    showToast('خطا در به‌روزرسانی اطلاعات پروفایل', 'error')
  } finally {
    savingProfile.value = false
  }
}

const handleLogout = () => {
  logout()
  router.push({ name: 'login' })
}

const loadingTgToken = ref(false)
const loadingBaleToken = ref(false)
const connectionToken = ref('')
const tokenPlatform = ref('')

const generateConnectToken = async (platform) => {
  if (platform === 'telegram') loadingTgToken.value = true
  else loadingBaleToken.value = true
  
  try {
    const res = await getConnectToken(platform)
    connectionToken.value = res.data.token
    tokenPlatform.value = platform
    showToast('توکن با موفقیت ایجاد شد', 'success')
  } catch (err) {
    showToast('خطا در دریافت توکن', 'error')
  } finally {
    loadingTgToken.value = false
    loadingBaleToken.value = false
  }
}

const copyToken = () => {
  if (!connectionToken.value) return
  navigator.clipboard.writeText(connectionToken.value)
  showToast('توکن در کلیپ‌بورد کپی شد', 'success')
}

onMounted(() => {
  loadProfile()
})
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: all 0.25s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(4px);
}
</style>