import type { ClientPlugin } from '../core/pluginTypes'
import { quranManifest } from './manifest'

export const quranPlugin: ClientPlugin = {
  manifest: quranManifest,
  initialize: () => {
    console.log('[QuranPlugin] Official Quran Client Plugin initialized successfully.')
  },
}

export * from './manifest'
export * from './types'
export * from './api'
export * from './composables/useQuranAudio'
export * from './composables/useQuranReader'

export { default as AyahCard } from './components/AyahCard.vue'
export { default as SurahHeader } from './components/SurahHeader.vue'
export { default as EditionSwitcher } from './components/EditionSwitcher.vue'
export { default as QuranAudioBar } from './components/QuranAudioBar.vue'
export { default as QuranVersePickerDialog } from './components/QuranVersePickerDialog.vue'
export { default as QuranVersePickerModal } from './components/QuranVersePickerModal.vue'

export { default as QuranHomeView } from './views/QuranHomeView.vue'
export { default as SurahReaderView } from './views/SurahReaderView.vue'
export { default as JuzReaderView } from './views/JuzReaderView.vue'
export { default as QuranSearchView } from './views/QuranSearchView.vue'

export default quranPlugin
