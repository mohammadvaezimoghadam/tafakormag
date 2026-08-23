import type { PluginManifest } from '../core/pluginTypes'
import QuranVersePickerDialog from './components/QuranVersePickerDialog.vue'

export const quranManifest: PluginManifest = {
  manifest_version: 1,
  identifier: 'quran',
  name: 'Official Quran Plugin',
  nameFa: 'افزونه رسمی قرآن کریم',
  version: '1.0.0',
  description: 'مطالعه، تلاوت، جستجوی آیات و درج ارجاعات قرآنی در متن یادداشت‌ها',
  descriptionFa: 'مطالعه، تلاوت، جستجوی آیات و درج ارجاعات قرآنی در متن یادداشت‌ها',
  author: 'Tafakor Core Team',
  icon: 'BookOpen',
  is_core: true,
  capabilities: ['composer_action', 'mini_app', 'search_provider'],
  scopes: ['read:content', 'read:quran'],
  routes: [
    {
      path: '/apps/quran',
      name: 'quran-home',
      component: () => import('./views/QuranHomeView.vue'),
      meta: { title: 'قرآن کریم', pluginId: 'quran' },
    },
    {
      path: '/apps/quran/surahs/:number',
      name: 'quran-surah-reader',
      component: () => import('./views/SurahReaderView.vue'),
      meta: { title: 'متن سوره قرآن', pluginId: 'quran' },
    },
    {
      path: '/apps/quran/juz/:number?',
      name: 'quran-juz-reader',
      component: () => import('./views/JuzReaderView.vue'),
      meta: { title: 'اجزای قرآن', pluginId: 'quran' },
    },
    {
      path: '/apps/quran/search',
      name: 'quran-search',
      component: () => import('./views/QuranSearchView.vue'),
      meta: { title: 'جستجوی قرآن', pluginId: 'quran' },
    },
  ],
  menuItems: [
    {
      id: 'quran-app',
      label: 'قرآن کریم',
      labelFa: 'قرآن کریم',
      icon: '📖',
      path: '/apps/quran',
      order: 10,
    },
  ],
  composerActions: [
    {
      id: 'quran-insert-ayah',
      label: 'درج آیه قرآن',
      labelFa: 'درج آیه قرآن',
      icon: '📖',
      tooltip: 'درج آیه قرآن به همراه ترجمه',
      tooltipFa: 'درج آیه قرآن به همراه ترجمه',
      dialogComponent: QuranVersePickerDialog,
    },
  ],
}
