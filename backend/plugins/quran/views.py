"""
DRF Views and ViewSets for Official Quran Plugin (`/api/plugins/quran/`).
Provides navigation, pagination, search, multi-edition comparison, and composer quote formatting.
"""
from rest_framework import viewsets, generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import NotFound
from django.shortcuts import get_object_or_404
from django.db.models import Q

from plugins.quran.models import QuranEdition, QuranSurah, QuranJuz, QuranAyah
from plugins.quran.serializers import (
    QuranEditionSerializer,
    QuranSurahSerializer,
    QuranSurahDetailSerializer,
    QuranJuzSerializer,
    QuranAyahSerializer,
    QuranAyahDetailSerializer,
    QuranFormatReferenceRequestSerializer,
    QuranFormatReferenceResponseSerializer,
    QuranCompareSerializer,
)
from plugins.quran.services.search_service import search_quran, QuranSearchService
from plugins.quran.services.formatter import format_quran_markdown_reference, QuranMarkdownFormatter


class QuranStandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 300


class QuranEditionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List and retrieve available Quran editions, translations, and audio recitations.
    """
    queryset = QuranEdition.objects.all()
    serializer_class = QuranEditionSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'identifier'
    lookup_url_kwarg = 'identifier'
    lookup_value_regex = r'[\w.-]+'

    def get_queryset(self):
        qs = super().get_queryset()
        language = self.request.query_params.get('language')
        type_ = self.request.query_params.get('type')
        format_ = self.request.query_params.get('format')
        is_default = self.request.query_params.get('is_default')
        q = self.request.query_params.get('q')

        if language:
            qs = qs.filter(language=language)
        if type_:
            qs = qs.filter(type=type_)
        if format_:
            qs = qs.filter(format=format_)
        if is_default is not None:
            qs = qs.filter(is_default=(is_default.lower() in ['true', '1']))
        if q:
            qs = qs.filter(
                Q(name__icontains=q) |
                Q(english_name__icontains=q) |
                Q(identifier__icontains=q) |
                Q(author__icontains=q)
            )
        return qs.order_by('language', 'type', 'name')


class QuranSurahViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List and retrieve Surahs and their Ayahs.
    """
    queryset = QuranSurah.objects.all().order_by('number')
    permission_classes = [permissions.AllowAny]
    lookup_field = 'number'
    lookup_url_kwarg = 'number'

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return QuranSurahDetailSerializer
        return QuranSurahSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        rev = self.request.query_params.get('revelation_type')
        juz = self.request.query_params.get('juz')
        if rev:
            qs = qs.filter(revelation_type__iexact=rev)
        if juz:
            qs = qs.filter(juz_start=juz)
        return qs

    @action(detail=True, methods=['get'], url_path='ayahs')
    def ayahs(self, request, number=None):
        """
        Retrieves all Ayahs in a Surah with optional paired translation.
        """
        surah = self.get_object()
        edition_id = request.query_params.get('edition')
        with_trans_id = request.query_params.get('with_translation') or request.query_params.get('with_translation_id')
        from_ayah = request.query_params.get('from_ayah')
        to_ayah = request.query_params.get('to_ayah')

        # Resolve primary edition
        if not edition_id:
            default_ed = QuranEdition.objects.filter(is_default=True, type='quran').first() or QuranEdition.objects.filter(type='quran').first()
            edition_id = default_ed.identifier if default_ed else 'quran-simple'

        ayahs_qs = QuranAyah.objects.filter(
            surah=surah,
            edition_id=edition_id
        ).select_related('surah', 'edition').order_by('number_in_surah')

        if from_ayah:
            ayahs_qs = ayahs_qs.filter(number_in_surah__gte=int(from_ayah))
        if to_ayah:
            ayahs_qs = ayahs_qs.filter(number_in_surah__lte=int(to_ayah))

        # Handle paired translation mapping
        trans_map = {}
        trans_name = None
        trans_author = None
        if with_trans_id:
            for a in QuranAyah.objects.filter(surah=surah, edition_id=with_trans_id).select_related('edition'):
                trans_map[a.number_in_surah] = a.text
            trans_ed = QuranEdition.objects.filter(identifier=with_trans_id).first()
            if trans_ed:
                trans_name = trans_ed.name
                trans_author = trans_ed.author

        paginator = QuranStandardPagination()
        # If pagination params are explicitly supplied, paginate; otherwise return full surah list
        if 'page' in request.query_params or (ayahs_qs.count() > 300 and 'all' not in request.query_params):
            page = paginator.paginate_queryset(ayahs_qs, request)
            for item in page:
                if with_trans_id:
                    item._translation_data = {
                        'edition': with_trans_id,
                        'edition_id': with_trans_id,
                        'edition_name': trans_name or with_trans_id,
                        'name': trans_name or with_trans_id,
                        'author': trans_author or '',
                        'text': trans_map.get(item.number_in_surah, '')
                    }
            serializer = QuranAyahSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        ayahs_list = list(ayahs_qs)
        for item in ayahs_list:
            if with_trans_id:
                item._translation_data = {
                    'edition': with_trans_id,
                    'edition_id': with_trans_id,
                    'edition_name': trans_name or with_trans_id,
                    'name': trans_name or with_trans_id,
                    'author': trans_author or '',
                    'text': trans_map.get(item.number_in_surah, '')
                }
        serializer = QuranAyahSerializer(ayahs_list, many=True)
        return Response({
            'surah': QuranSurahSerializer(surah).data,
            'edition': edition_id,
            'with_translation': with_trans_id,
            'count': len(ayahs_list),
            'ayahs': serializer.data
        })


class QuranJuzViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List and retrieve 30 Juzs and their Ayahs.
    """
    queryset = QuranJuz.objects.select_related('start_surah', 'end_surah').all().order_by('number')
    serializer_class = QuranJuzSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'number'
    lookup_url_kwarg = 'number'
    pagination_class = None

    @action(detail=True, methods=['get'], url_path='ayahs')
    def ayahs(self, request, number=None):
        juz = self.get_object()
        edition_id = request.query_params.get('edition')
        with_trans_id = request.query_params.get('with_translation') or request.query_params.get('with_translation_id')

        if not edition_id:
            default_ed = QuranEdition.objects.filter(is_default=True, type='quran').first() or QuranEdition.objects.filter(type='quran').first()
            edition_id = default_ed.identifier if default_ed else 'quran-simple'

        ayahs_qs = QuranAyah.objects.filter(
            juz=juz.number,
            edition_id=edition_id
        ).select_related('surah', 'edition').order_by('surah__number', 'number_in_surah')

        trans_map = {}
        trans_name = None
        trans_author = None
        if with_trans_id:
            for a in QuranAyah.objects.filter(juz=juz.number, edition_id=with_trans_id).select_related('edition'):
                trans_map[(a.surah_id, a.number_in_surah)] = a.text
            trans_ed = QuranEdition.objects.filter(identifier=with_trans_id).first()
            if trans_ed:
                trans_name = trans_ed.name
                trans_author = trans_ed.author

        paginator = QuranStandardPagination()
        page = paginator.paginate_queryset(ayahs_qs, request)
        for item in page:
            if with_trans_id:
                item._translation_data = {
                    'edition': with_trans_id,
                    'edition_id': with_trans_id,
                    'edition_name': trans_name or with_trans_id,
                    'name': trans_name or with_trans_id,
                    'author': trans_author or '',
                    'text': trans_map.get((item.surah_id, item.number_in_surah), '')
                }
        serializer = QuranAyahSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class QuranAyahDetailByGlobalView(APIView):
    """Retrieve Ayah by global index (1 to 6236)."""
    permission_classes = [permissions.AllowAny]

    def get(self, request, number):
        edition_id = request.query_params.get('edition')
        with_trans_id = request.query_params.get('with_translation') or request.query_params.get('with_translation_id')

        if not edition_id:
            default_ed = QuranEdition.objects.filter(is_default=True, type='quran').first() or QuranEdition.objects.filter(type='quran').first()
            edition_id = default_ed.identifier if default_ed else 'quran-simple'

        ayah = get_object_or_404(
            QuranAyah.objects.select_related('surah', 'edition'),
            number=number,
            edition_id=edition_id
        )

        if with_trans_id:
            trans_ayah = QuranAyah.objects.filter(
                surah=ayah.surah,
                number_in_surah=ayah.number_in_surah,
                edition_id=with_trans_id
            ).select_related('edition').first()
            if trans_ayah:
                ayah._translation_data = {
                    'edition': with_trans_id,
                    'edition_id': with_trans_id,
                    'edition_name': trans_ayah.edition.name,
                    'author': trans_ayah.edition.author,
                    'text': trans_ayah.text
                }

        serializer = QuranAyahDetailSerializer(ayah)
        return Response(serializer.data)


class QuranAyahDetailBySurahView(APIView):
    """Retrieve Ayah by Surah number and number_in_surah."""
    permission_classes = [permissions.AllowAny]

    def get(self, request, surah=None, ayah=None, surah_number=None, ayah_number=None):
        s_num = surah if surah is not None else surah_number
        a_num = ayah if ayah is not None else ayah_number

        edition_id = request.query_params.get('edition') or request.query_params.get('edition_id')
        with_trans_id = request.query_params.get('with_translation') or request.query_params.get('with_translation_id')

        if not edition_id:
            default_ed = QuranEdition.objects.filter(is_default=True, type='quran').first() or QuranEdition.objects.filter(type='quran').first()
            edition_id = default_ed.identifier if default_ed else 'quran-simple'

        ayah_obj = QuranAyah.objects.filter(
            surah__number=s_num,
            number_in_surah=a_num,
            edition_id=edition_id
        ).select_related('surah', 'edition').first()

        if not ayah_obj:
            # Fallback to any edition matching
            ayah_obj = QuranAyah.objects.filter(
                surah__number=s_num,
                number_in_surah=a_num
            ).select_related('surah', 'edition').first()

        if not ayah_obj:
            raise NotFound(f"Ayah {s_num}:{a_num} not found.")

        if with_trans_id:
            trans_ayah = QuranAyah.objects.filter(
                surah__number=s_num,
                number_in_surah=a_num,
                edition_id=with_trans_id
            ).select_related('edition').first()
            if trans_ayah:
                ayah_obj._translation_data = {
                    'edition': with_trans_id,
                    'edition_id': with_trans_id,
                    'edition_name': trans_ayah.edition.name,
                    'author': trans_ayah.edition.author,
                    'text': trans_ayah.text
                }

        serializer = QuranAyahDetailSerializer(ayah_obj)
        return Response(serializer.data)


# Backward-compatible view class definitions
QuranAyahDetailView = QuranAyahDetailBySurahView


class QuranEditionListView(generics.ListAPIView):
    queryset = QuranEdition.objects.all()
    serializer_class = QuranEditionSerializer
    permission_classes = [permissions.AllowAny]


class QuranEditionDetailView(generics.RetrieveAPIView):
    queryset = QuranEdition.objects.all()
    serializer_class = QuranEditionSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'identifier'


class QuranSurahListView(generics.ListAPIView):
    queryset = QuranSurah.objects.all().order_by('number')
    serializer_class = QuranSurahSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None


class QuranSurahDetailView(generics.RetrieveAPIView):
    queryset = QuranSurah.objects.all()
    serializer_class = QuranSurahDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'number'


class QuranSurahAyahsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, number):
        view = QuranSurahViewSet()
        view.request = request
        view.format_kwarg = None
        view.kwargs = {'number': number}
        return view.ayahs(request, number=number)


class QuranJuzListView(generics.ListAPIView):
    queryset = QuranJuz.objects.all().select_related('start_surah', 'end_surah').order_by('number')
    serializer_class = QuranJuzSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None


class QuranJuzDetailView(generics.RetrieveAPIView):
    queryset = QuranJuz.objects.all().select_related('start_surah', 'end_surah')
    serializer_class = QuranJuzSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'number'


class QuranSearchView(APIView):
    """Search Quran Ayahs or translations across database engines with highlighting."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        query = request.query_params.get('q', '').strip()
        if not query or len(query) < 2:
            return Response(
                {"error": "Search query 'q' is required and must be at least 2 characters."},
                status=status.HTTP_400_BAD_REQUEST
            )

        edition_id = request.query_params.get('edition') or request.query_params.get('edition_id')
        language = request.query_params.get('language')
        surah_num = request.query_params.get('surah') or request.query_params.get('surah_number')
        juz_num = request.query_params.get('juz') or request.query_params.get('juz_number')
        page_num = int(request.query_params.get('page', 1))
        page_size = min(int(request.query_params.get('page_size', 20)), 100)
        with_trans_id = request.query_params.get('with_translation') or request.query_params.get('with_translation_id') or request.query_params.get('with_translation_edition_id')
        exact = request.query_params.get('exact', '').lower() in ['true', '1']

        search_results = search_quran(
            query=query,
            edition_id=edition_id,
            language=language,
            surah_number=int(surah_num) if surah_num else None,
            juz_number=int(juz_num) if juz_num else None,
            page=page_num,
            page_size=page_size,
            exact=exact,
            with_translation=with_trans_id,
        )

        return Response(search_results, status=status.HTTP_200_OK)


class QuranCompareView(APIView):
    """Compare an Ayah across multiple editions/translations in parallel."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        surah_num = request.query_params.get('surah') or request.query_params.get('surah_number')
        ayah_num = request.query_params.get('ayah') or request.query_params.get('ayah_number')
        editions_str = request.query_params.get('editions') or request.query_params.get('edition_ids')

        if not surah_num or not ayah_num:
            return Response(
                {"error": "Both 'surah' and 'ayah' query parameters are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        surah = get_object_or_404(QuranSurah, number=int(surah_num))
        ayah_num = int(ayah_num)

        if editions_str:
            ed_ids = [e.strip() for e in editions_str.split(',') if e.strip()]
        else:
            ed_ids = list(QuranEdition.objects.filter(is_default=True).values_list('identifier', flat=True))
            if not ed_ids:
                ed_ids = list(QuranEdition.objects.values_list('identifier', flat=True)[:3])

        ayah_records = QuranAyah.objects.filter(
            surah=surah,
            number_in_surah=ayah_num,
            edition_id__in=ed_ids
        ).select_related('edition')

        if not ayah_records.exists():
            return Response({"error": "Ayah not found in specified editions."}, status=status.HTTP_404_NOT_FOUND)

        first_ayah = ayah_records.first()
        comparison_list = []
        for a in ayah_records:
            comparison_list.append({
                'edition': QuranEditionSerializer(a.edition).data,
                'text': a.text,
                'audio_url': a.audio_url
            })

        response_data = {
            'surah': QuranSurahSerializer(surah).data,
            'ayah_number': ayah_num,
            'global_number': first_ayah.number,
            'juz': first_ayah.juz,
            'page': first_ayah.page,
            'editions': comparison_list
        }
        return Response(response_data)


class QuranFormatReferenceView(APIView):
    """
    Format standard Markdown blockquote and metadata for Composer integration.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = QuranFormatReferenceRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        surah_num = data['surah']
        ayah_from = data['ayah_from']
        ayah_to = data['ayah_to']
        edition_id = data.get('edition') or 'quran-simple'
        trans_id = data.get('translation_edition') or data.get('translation_id')
        lang = data.get('lang', 'fa')

        surah = get_object_or_404(QuranSurah, number=surah_num)

        # Query Arabic Ayahs
        arabic_ayahs = list(QuranAyah.objects.filter(
            surah=surah,
            edition_id=edition_id,
            number_in_surah__gte=ayah_from,
            number_in_surah__lte=ayah_to
        ).order_by('number_in_surah'))

        if not arabic_ayahs:
            # Fallback to any arabic edition
            arabic_ayahs = list(QuranAyah.objects.filter(
                surah=surah,
                number_in_surah__gte=ayah_from,
                number_in_surah__lte=ayah_to
            ).order_by('number_in_surah'))

        if not arabic_ayahs:
            return Response(
                {"error": f"Ayahs {ayah_from}-{ayah_to} not found for Surah {surah_num}"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Query Translations if requested
        trans_ayahs = []
        trans_name = ""
        trans_author = ""
        if trans_id:
            trans_ayahs = list(QuranAyah.objects.filter(
                surah=surah,
                edition_id=trans_id,
                number_in_surah__gte=ayah_from,
                number_in_surah__lte=ayah_to
            ).order_by('number_in_surah'))
            trans_ed = QuranEdition.objects.filter(identifier=trans_id).first()
            if trans_ed:
                trans_name = trans_ed.name
                trans_author = trans_ed.author

        markdown_text = format_quran_markdown_reference(
            surah=surah,
            ayah_from=ayah_from,
            ayah_to=ayah_to,
            arabic_ayahs=arabic_ayahs,
            translation_ayahs=trans_ayahs,
            translation_edition_name=trans_name,
            lang=lang,
        )

        external_id = f"surah:{surah_num},ayah:{ayah_from}-{ayah_to}" if ayah_to > ayah_from else f"surah:{surah_num},ayah:{ayah_from}"
        metadata = {
            'surah': surah_num,
            'surah_name': surah.name,
            'ayah_from': ayah_from,
            'ayah_to': ayah_to,
            'edition': edition_id,
            'translation_edition': trans_id if trans_ayahs else None,
        }

        return Response({
            'markdown': markdown_text,
            'surah': {'number': surah.number, 'name': surah.name, 'english_name': surah.english_name},
            'surah_number': surah.number,
            'surah_name': surah.name,
            'surah_english_name': surah.english_name,
            'ayah_from': ayah_from,
            'ayah_to': ayah_to,
            'ayah_number': ayah_from,
            'arabic_text': arabic_ayahs[0].text if arabic_ayahs else '',
            'translation_text': trans_ayahs[0].text if trans_ayahs else None,
            'translation_author': trans_author or trans_name or None,
            'external_id': external_id,
            'metadata': metadata,
        }, status=status.HTTP_200_OK)
