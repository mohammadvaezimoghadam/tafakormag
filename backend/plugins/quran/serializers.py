"""
DRF Serializers for the Official Quran Plugin (`/api/plugins/quran/`).
Provides serialization for Editions, Surahs, Juzs, Ayahs, Search, Compare, and Composer Reference.
"""
from rest_framework import serializers
from plugins.quran.models import QuranEdition, QuranSurah, QuranJuz, QuranAyah


class QuranEditionSerializer(serializers.ModelSerializer):
    """Serializer for Quran Editions / Translations / Audio."""
    class Meta:
        model = QuranEdition
        fields = [
            'identifier',
            'name',
            'english_name',
            'language',
            'type',
            'format',
            'direction',
            'author',
            'is_default',
            'total_ayahs',
            'metadata',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields


class QuranSurahSerializer(serializers.ModelSerializer):
    """Serializer for canonical Surah catalog listing."""
    class Meta:
        model = QuranSurah
        fields = [
            'number',
            'name',
            'english_name',
            'english_name_translation',
            'revelation_type',
            'ayah_count',
            'order_of_revelation',
            'page_start',
            'page_end',
            'juz_start',
            'bismillah_pre',
        ]
        read_only_fields = fields


class QuranSurahDetailSerializer(QuranSurahSerializer):
    """Detailed Surah serializer with previous and next navigation links."""
    prev_surah = serializers.SerializerMethodField()
    next_surah = serializers.SerializerMethodField()

    class Meta(QuranSurahSerializer.Meta):
        fields = QuranSurahSerializer.Meta.fields + ['prev_surah', 'next_surah']

    def get_prev_surah(self, obj):
        if obj.number > 1:
            return {'number': obj.number - 1}
        return None

    def get_next_surah(self, obj):
        if obj.number < 114:
            return {'number': obj.number + 1}
        return None


class QuranJuzSerializer(serializers.ModelSerializer):
    """Serializer for Quran 30 Juzs."""
    start_surah_name = serializers.CharField(source='start_surah.name', read_only=True)
    end_surah_name = serializers.CharField(source='end_surah.name', read_only=True)

    class Meta:
        model = QuranJuz
        fields = [
            'number',
            'name',
            'start_surah',
            'start_surah_name',
            'start_ayah',
            'end_surah',
            'end_surah_name',
            'end_ayah',
            'surah_mapping',
        ]
        read_only_fields = fields


class QuranAyahSerializer(serializers.ModelSerializer):
    """Ayah serializer with paired translation support for Surah and Juz views."""
    surah_number = serializers.IntegerField(source='surah.number', read_only=True)
    surah_name = serializers.CharField(source='surah.name', read_only=True)
    surah_english_name = serializers.CharField(source='surah.english_name', read_only=True)
    edition_identifier = serializers.CharField(source='edition.identifier', read_only=True)
    edition_name = serializers.CharField(source='edition.name', read_only=True)
    edition_language = serializers.CharField(source='edition.language', read_only=True)
    translation = serializers.SerializerMethodField()

    class Meta:
        model = QuranAyah
        fields = [
            'id',
            'number',
            'number_in_surah',
            'surah',
            'surah_number',
            'surah_name',
            'surah_english_name',
            'edition',
            'edition_identifier',
            'edition_name',
            'edition_language',
            'juz',
            'page',
            'manzil',
            'ruku',
            'hizb_quarter',
            'sajda',
            'text',
            'audio_url',
            'translation',
        ]
        read_only_fields = fields

    def get_translation(self, obj):
        # Attached dynamically in view if with_translation param was requested
        return getattr(obj, '_translation_data', getattr(obj, '_attached_translation', None))


class QuranAyahDetailSerializer(serializers.ModelSerializer):
    """Full detail Ayah serializer."""
    surah = QuranSurahSerializer(read_only=True)
    edition = QuranEditionSerializer(read_only=True)
    translation = serializers.SerializerMethodField()
    highlighted_text = serializers.SerializerMethodField()

    class Meta:
        model = QuranAyah
        fields = [
            'id',
            'number',
            'number_in_surah',
            'surah',
            'edition',
            'juz',
            'page',
            'manzil',
            'ruku',
            'hizb_quarter',
            'sajda',
            'text',
            'normalized_text',
            'highlighted_text',
            'audio_url',
            'metadata',
            'translation',
        ]
        read_only_fields = fields

    def get_translation(self, obj):
        return getattr(obj, '_translation_data', getattr(obj, '_attached_translation', None))

    def get_highlighted_text(self, obj):
        return getattr(obj, '_highlighted_text', obj.text)


class QuranSearchResultItemSerializer(serializers.Serializer):
    """Single search match result."""
    id = serializers.IntegerField(required=False)
    surah = QuranSurahSerializer()
    edition = QuranEditionSerializer()
    number = serializers.IntegerField()
    number_in_surah = serializers.IntegerField()
    juz = serializers.IntegerField()
    page = serializers.IntegerField(allow_null=True)
    text = serializers.CharField()
    normalized_text = serializers.CharField()
    highlighted_text = serializers.CharField()
    audio_url = serializers.URLField(allow_null=True, required=False)
    translation = serializers.DictField(required=False, allow_null=True)


class QuranSearchResponseSerializer(serializers.Serializer):
    """Paginated search response envelope."""
    query = serializers.CharField()
    normalized_query = serializers.CharField()
    edition = serializers.CharField()
    count = serializers.IntegerField()
    total_matches = serializers.IntegerField()
    page = serializers.IntegerField()
    page_size = serializers.IntegerField()
    total_pages = serializers.IntegerField()
    results = QuranSearchResultItemSerializer(many=True)


class QuranCompareItemSerializer(serializers.Serializer):
    """Edition text in comparison response."""
    edition = QuranEditionSerializer()
    text = serializers.CharField()
    audio_url = serializers.URLField(allow_null=True, required=False)


class QuranCompareSerializer(serializers.Serializer):
    """Multi-edition parallel comparison response."""
    surah = QuranSurahSerializer()
    ayah_number = serializers.IntegerField()
    global_number = serializers.IntegerField()
    juz = serializers.IntegerField()
    page = serializers.IntegerField(allow_null=True)
    editions = QuranCompareItemSerializer(many=True)


class QuranFormatReferenceRequestSerializer(serializers.Serializer):
    """Request payload for formatting Markdown quote for Composer."""
    surah = serializers.IntegerField(min_value=1, max_value=114, required=False)
    surah_number = serializers.IntegerField(min_value=1, max_value=114, required=False)
    ayah_from = serializers.IntegerField(min_value=1, required=False)
    ayah_number = serializers.IntegerField(min_value=1, required=False)
    ayah_to = serializers.IntegerField(min_value=1, required=False)
    edition = serializers.CharField(required=False, default='quran-simple')
    edition_id = serializers.CharField(required=False, default='quran-simple')
    translation_edition = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    translation_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    include_citation = serializers.BooleanField(required=False, default=True)
    lang = serializers.ChoiceField(choices=['fa', 'en'], default='fa', required=False)

    def validate(self, data):
        surah_val = data.get('surah') or data.get('surah_number')
        if not surah_val:
            raise serializers.ValidationError({"surah": "Surah number is required."})
        data['surah'] = surah_val
        data['surah_number'] = surah_val

        from_val = data.get('ayah_from') or data.get('ayah_number') or 1
        to_val = data.get('ayah_to') or from_val
        data['ayah_from'] = from_val
        data['ayah_number'] = from_val
        data['ayah_to'] = to_val

        if to_val < from_val:
            raise serializers.ValidationError({"ayah_to": "ayah_to cannot be less than ayah_from."})

        edition_val = data.get('edition') or data.get('edition_id') or 'quran-simple'
        data['edition'] = edition_val
        data['edition_id'] = edition_val

        trans_val = data.get('translation_edition') or data.get('translation_id')
        data['translation_edition'] = trans_val
        data['translation_id'] = trans_val

        return data


class QuranFormatReferenceResponseSerializer(serializers.Serializer):
    """Response payload for formatted Markdown quote."""
    markdown = serializers.CharField()
    surah = serializers.DictField()
    surah_number = serializers.IntegerField(required=False)
    surah_name = serializers.CharField(required=False)
    surah_english_name = serializers.CharField(required=False)
    ayah_from = serializers.IntegerField()
    ayah_to = serializers.IntegerField()
    ayah_number = serializers.IntegerField(required=False)
    arabic_text = serializers.CharField(required=False)
    translation_text = serializers.CharField(required=False, allow_null=True)
    translation_author = serializers.CharField(required=False, allow_null=True)
    external_id = serializers.CharField()
    metadata = serializers.DictField()
