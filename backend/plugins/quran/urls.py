"""
URL Routing for the Official Quran Plugin (`/api/plugins/quran/`).
"""
from django.urls import path, include
from rest_framework.routers import SimpleRouter
from plugins.quran.views import (
    QuranEditionViewSet,
    QuranSurahViewSet,
    QuranJuzViewSet,
    QuranAyahDetailByGlobalView,
    QuranAyahDetailBySurahView,
    QuranSearchView,
    QuranCompareView,
    QuranFormatReferenceView,
    QuranJuzListView,
    QuranJuzDetailView,
)

router = SimpleRouter()
router.register(r'editions', QuranEditionViewSet, basename='quran-edition')
router.register(r'surahs', QuranSurahViewSet, basename='quran-surah')
router.register(r'juzs', QuranJuzViewSet, basename='quran-juzs')

from apps.plugin_system.views import PluginDetailView

urlpatterns = [
    # Root Plugin Detail for identifier='quran'
    path('', PluginDetailView.as_view(), {'identifier': 'quran'}, name='quran-plugin-detail'),

    # Fixed action endpoints
    path('search/', QuranSearchView.as_view(), name='quran-search'),
    path('compare/', QuranCompareView.as_view(), name='quran-compare'),
    path('format-reference/', QuranFormatReferenceView.as_view(), name='quran-format-reference'),

    # Ayah coordinate lookups
    path('ayahs/<int:surah>/<int:ayah>/', QuranAyahDetailBySurahView.as_view(), name='quran-ayah-by-surah'),
    path('ayahs/<int:number>/', QuranAyahDetailByGlobalView.as_view(), name='quran-ayah-by-global'),

    # Singular 'juz/' aliases for compatibility with frontend/tests
    path('juz/', QuranJuzViewSet.as_view({'get': 'list'}), name='quran-juz-list'),
    path('juz/<int:number>/', QuranJuzViewSet.as_view({'get': 'retrieve'}), name='quran-juz-detail'),
    path('juz/<int:number>/ayahs/', QuranJuzViewSet.as_view({'get': 'ayahs'}), name='quran-juz-ayahs'),

    # ViewSet Router endpoints (editions/, surahs/, surahs/<num>/ayahs/, juzs/, juzs/<num>/ayahs/)
    path('', include(router.urls)),
]
