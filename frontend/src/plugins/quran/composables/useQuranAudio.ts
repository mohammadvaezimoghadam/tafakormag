import { ref, computed } from 'vue'
import type { QuranSurah, QuranAyah, QuranReciter } from '../types'

export const AVAILABLE_RECITERS: QuranReciter[] = [
  {
    id: 'ar.alafasy',
    name: 'Mishary Rashid Alafasy',
    nameFa: 'مشاری راشد العفاسی',
    style: 'مرتل',
    subfolder: 'Alafasy_128kbps',
    cdnType: 'islamicnetwork',
  },
  {
    id: 'ar.parhizgar',
    name: 'Shahriar Parhizgar',
    nameFa: 'شهریار پرهیزگار',
    style: 'ترتیل استاندارد',
    subfolder: 'Parhizgar_48kbps',
    cdnType: 'islamicnetwork',
  },
  {
    id: 'ar.abdulbasitmurattal',
    name: 'Abdul Basit Murattal',
    nameFa: 'عبدالباسط عبدالصمد (مرتل)',
    style: 'مرتل',
    subfolder: 'Abdul_Basit_Murattal_192kbps',
    cdnType: 'islamicnetwork',
  },
  {
    id: 'ar.minshawi',
    name: 'Mohamed Siddiq El-Minshawi',
    nameFa: 'محمد صدیق المنشاوی',
    style: 'مرتل',
    subfolder: 'Minshawy_Murattal_128kbps',
    cdnType: 'islamicnetwork',
  },
  {
    id: 'ar.husary',
    name: 'Mahmoud Khalil Al-Husary',
    nameFa: 'محمود خلیل الحصری',
    style: 'مرتل',
    subfolder: 'Husary_128kbps',
    cdnType: 'islamicnetwork',
  },
]

// Global singleton audio instance & state
let audioElement: HTMLAudioElement | null = null
const isPlaying = ref(false)
const isLoading = ref(false)
const currentSurah = ref<QuranSurah | null>(null)
const currentAyah = ref<QuranAyah | null>(null)
const currentAyahNumber = ref<number | null>(null)
const currentGlobalNumber = ref<number | null>(null)
const currentReciterId = ref<string>(
  localStorage.getItem('tafakor_quran_reciter') || 'ar.alafasy'
)
const playbackRate = ref<number>(1.0)
const currentTime = ref<number>(0)
const duration = ref<number>(0)
const repeatMode = ref<'none' | 'ayah' | 'surah'>('surah')
const volume = ref<number>(1.0)
const isMuted = ref(false)
const error = ref<string | null>(null)

type AyahChangeCallback = (surahNumber: number, ayahNumber: number) => void
const ayahChangeListeners = new Set<AyahChangeCallback>()

function getAudioElement(): HTMLAudioElement {
  if (!audioElement && typeof window !== 'undefined') {
    audioElement = new Audio()
    audioElement.preload = 'auto'

    audioElement.addEventListener('play', () => {
      isPlaying.value = true
    })

    audioElement.addEventListener('pause', () => {
      isPlaying.value = false
    })

    audioElement.addEventListener('waiting', () => {
      isLoading.value = true
    })

    audioElement.addEventListener('canplay', () => {
      isLoading.value = false
    })

    audioElement.addEventListener('timeupdate', () => {
      if (audioElement) {
        currentTime.value = audioElement.currentTime
        duration.value = audioElement.duration || 0
      }
    })

    audioElement.addEventListener('ended', () => {
      handleTrackEnded()
    })

    audioElement.addEventListener('error', (e) => {
      console.warn('[QuranAudio] Audio playback error:', e)
      isLoading.value = false
      isPlaying.value = false
      error.value = 'Failed to load audio stream'
    })
  }
  return audioElement!
}

function resolveAyahAudioUrl(surahNumber: number, ayahInSurah: number, globalAyahNum?: number): string {
  const reciter = AVAILABLE_RECITERS.find(r => r.id === currentReciterId.value) || AVAILABLE_RECITERS[0]
  if (!reciter) {
    return `https://cdn.islamic.network/quran/audio/128/ar.alafasy/${globalAyahNum || 1}.mp3`
  }

  const sPad = String(surahNumber).padStart(3, '0')
  const aPad = String(ayahInSurah).padStart(3, '0')

  if (reciter.cdnType === 'everyayah' && reciter.subfolder) {
    return `https://everyayah.com/data/${reciter.subfolder}/${sPad}${aPad}.mp3`
  }

  // Islamic Network CDN fallback / primary
  if (globalAyahNum) {
    return `https://cdn.islamic.network/quran/audio/128/${reciter.id}/${globalAyahNum}.mp3`
  }

  // Fallback EveryAyah URL
  return `https://everyayah.com/data/${reciter.subfolder || 'Alafasy_128kbps'}/${sPad}${aPad}.mp3`
}

function notifyAyahChange(surahNumber: number, ayahNumber: number) {
  ayahChangeListeners.forEach(cb => {
    try {
      cb(surahNumber, ayahNumber)
    } catch (e) {
      console.error('[QuranAudio] Error in ayah change listener:', e)
    }
  })
}

async function playAyah(
  surah: QuranSurah,
  ayahNum: number,
  ayahData?: QuranAyah
) {
  const audio = getAudioElement()
  error.value = null
  currentSurah.value = surah
  currentAyahNumber.value = ayahNum
  currentAyah.value = ayahData || null

  const globalNum = ayahData?.number || ayahData?.id
  currentGlobalNumber.value = globalNum || null

  const audioUrl = ayahData?.audio_url || resolveAyahAudioUrl(surah.number, ayahNum, globalNum)

  try {
    isLoading.value = true
    audio.src = audioUrl
    audio.playbackRate = playbackRate.value
    audio.volume = isMuted.value ? 0 : volume.value

    await audio.play()
    isPlaying.value = true
    notifyAyahChange(surah.number, ayahNum)
  } catch (err: any) {
    console.warn('[QuranAudio] Playback failed or autoplay prevented:', err)
    isPlaying.value = false
  } finally {
    isLoading.value = false
  }
}

function nextAyah() {
  if (!currentSurah.value || currentAyahNumber.value === null) return
  const nextNum = currentAyahNumber.value + 1
  if (nextNum <= currentSurah.value.ayah_count) {
    playAyah(currentSurah.value, nextNum)
  }
}

function prevAyah() {
  const audio = getAudioElement()
  if (!currentSurah.value || currentAyahNumber.value === null) return
  if (currentTime.value > 3) {
    audio.currentTime = 0
    return
  }
  const prevNum = currentAyahNumber.value - 1
  if (prevNum >= 1) {
    playAyah(currentSurah.value, prevNum)
  }
}

function togglePlayPause() {
  const audio = getAudioElement()
  if (isPlaying.value) {
    audio.pause()
  } else {
    audio.play().catch(console.warn)
  }
}

function handleTrackEnded() {
  if (repeatMode.value === 'ayah') {
    const audio = getAudioElement()
    audio.currentTime = 0
    audio.play().catch(console.warn)
    return
  }

  if (currentSurah.value && currentAyahNumber.value !== null) {
    const totalAyahs = currentSurah.value.ayah_count
    if (currentAyahNumber.value < totalAyahs) {
      nextAyah()
    } else if (repeatMode.value === 'surah') {
      // Loop back to ayah 1
      playAyah(currentSurah.value, 1)
    } else {
      isPlaying.value = false
    }
  }
}

export function useQuranAudio() {
  const audio = getAudioElement()

  const currentReciter = computed(() => {
    return AVAILABLE_RECITERS.find(r => r.id === currentReciterId.value) || AVAILABLE_RECITERS[0]
  })

  const progress = computed(() => {
    if (!duration.value || duration.value === 0) return 0
    return Math.min(100, Math.max(0, (currentTime.value / duration.value) * 100))
  })

  const seek = (progressPercent: number) => {
    if (!duration.value) return
    const target = (progressPercent / 100) * duration.value
    audio.currentTime = target
    currentTime.value = target
  }

  const setPlaybackRate = (rate: number) => {
    playbackRate.value = rate
    audio.playbackRate = rate
  }

  const setReciter = (reciterId: string) => {
    currentReciterId.value = reciterId
    try {
      localStorage.setItem('tafakor_quran_reciter', reciterId)
    } catch (e) {}

    // If currently playing, seamlessly reload current verse with new reciter
    if (currentSurah.value && currentAyahNumber.value !== null && isPlaying.value) {
      playAyah(currentSurah.value, currentAyahNumber.value, currentAyah.value || undefined)
    }
  }

  const setRepeatMode = (mode: 'none' | 'ayah' | 'surah') => {
    repeatMode.value = mode
  }

  const toggleMute = () => {
    isMuted.value = !isMuted.value
    audio.volume = isMuted.value ? 0 : volume.value
  }

  const setVolume = (val: number) => {
    volume.value = Math.max(0, Math.min(1, val))
    if (isMuted.value) isMuted.value = false
    audio.volume = volume.value
  }

  const stop = () => {
    audio.pause()
    audio.currentTime = 0
    isPlaying.value = false
    currentSurah.value = null
    currentAyahNumber.value = null
    currentAyah.value = null
  }

  const onAyahChanged = (cb: AyahChangeCallback) => {
    ayahChangeListeners.add(cb)
    return () => {
      ayahChangeListeners.delete(cb)
    }
  }

  return {
    isPlaying,
    isLoading,
    currentSurah,
    currentAyah,
    currentAyahNumber,
    currentGlobalNumber,
    currentReciterId,
    currentReciter,
    availableReciters: AVAILABLE_RECITERS,
    playbackRate,
    currentTime,
    duration,
    progress,
    repeatMode,
    volume,
    isMuted,
    error,
    playAyah,
    togglePlayPause,
    nextAyah,
    prevAyah,
    seek,
    setPlaybackRate,
    setReciter,
    setRepeatMode,
    toggleMute,
    setVolume,
    stop,
    onAyahChanged,
  }
}
