"""
DRF Serializers for Quran Khatm System (Group Campaigns & Personal Offline-First Plans).
"""
import logging
from rest_framework import serializers
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from plugins.quran.models import (
    KhatmCategory,
    KhatmCampaign,
    KhatmSlot,
    PersonalKhatmPlan,
    QuranSurah,
)

logger = logging.getLogger(__name__)
User = get_user_model()


def _resolve_display_name(target_user, request):
    """
    Returns privacy-safe display name for a campaign creator or slot holder.
    Unauthenticated guests receive None; authenticated users see full_name or "کاربر قرآن"
    without exposing raw or masked phone numbers.
    """
    if not (request and getattr(request, 'user', None) and request.user.is_authenticated):
        return None
    if not target_user:
        return "کاربر قرآن"
    full_name = (target_user.get_full_name() or "").strip()
    if full_name and full_name != target_user.phone:
        return full_name
    return "کاربر قرآن"


class KhatmCategorySerializer(serializers.ModelSerializer):
    """Serializer for Khatm Categories / Intentions."""
    class Meta:
        model = KhatmCategory
        fields = [
            'id',
            'title',
            'slug',
            'icon',
            'display_order',
            'is_active',
        ]
        read_only_fields = fields


class KhatmSlotSerializer(serializers.ModelSerializer):
    """Serializer for individual Khatm slot allocation."""
    user_display_name = serializers.SerializerMethodField()
    is_mine = serializers.SerializerMethodField()

    class Meta:
        model = KhatmSlot
        fields = [
            'id',
            'campaign_id',
            'unit_number',
            'quantity',
            'status',
            'user_id',
            'user_display_name',
            'is_mine',
            'reserved_at',
            'expires_at',
            'completed_at',
        ]
        read_only_fields = fields

    def get_user_display_name(self, obj):
        if not obj.user:
            return None
        return _resolve_display_name(obj.user, self.context.get('request'))

    def get_is_mine(self, obj):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            return obj.user_id == request.user.id
        return False


class KhatmCampaignListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for public feed and campaign lists."""
    category = KhatmCategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=KhatmCategory.objects.filter(is_active=True),
        source='category',
        write_only=True,
        required=False,
        allow_null=True
    )
    unit_type_display = serializers.CharField(source='get_unit_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    target_surah_name = serializers.CharField(source='target_surah.name', read_only=True, default=None)
    creator_display_name = serializers.SerializerMethodField()
    remaining_units = serializers.SerializerMethodField()
    progress_percentage = serializers.SerializerMethodField()
    is_creator = serializers.SerializerMethodField()

    class Meta:
        model = KhatmCampaign
        fields = [
            'id',
            'invite_code',
            'category',
            'category_id',
            'creator_id',
            'creator_display_name',
            'title',
            'description',
            'unit_type',
            'unit_type_display',
            'target_units',
            'target_surah_id',
            'target_surah_name',
            'reserved_units',
            'completed_units',
            'remaining_units',
            'progress_percentage',
            'is_public',
            'status',
            'status_display',
            'deadline',
            'created_at',
            'is_creator',
        ]
        read_only_fields = [
            'id',
            'invite_code',
            'creator_id',
            'creator_display_name',
            'reserved_units',
            'completed_units',
            'remaining_units',
            'progress_percentage',
            'created_at',
            'is_creator',
        ]

    def get_creator_display_name(self, obj):
        return _resolve_display_name(obj.creator, self.context.get('request'))

    def get_remaining_units(self, obj):
        return max(obj.target_units - (obj.reserved_units + obj.completed_units), 0)

    def get_progress_percentage(self, obj):
        if not obj.target_units or obj.target_units <= 0:
            return 0.0
        return round((obj.completed_units / obj.target_units) * 100.0, 1)

    def get_is_creator(self, obj):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            return obj.creator_id == request.user.id
        return False


class KhatmCampaignDetailSerializer(KhatmCampaignListSerializer):
    """Detailed serializer including all slots and invite URL."""
    slots = KhatmSlotSerializer(many=True, read_only=True)
    invite_url = serializers.SerializerMethodField()
    my_active_slots_count = serializers.SerializerMethodField()

    class Meta(KhatmCampaignListSerializer.Meta):
        fields = KhatmCampaignListSerializer.Meta.fields + [
            'slots',
            'invite_url',
            'my_active_slots_count',
        ]

    def get_invite_url(self, obj):
        return f"https://tafakor.ir/k/{obj.invite_code}"

    def get_my_active_slots_count(self, obj):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            return obj.slots.filter(
                user=request.user,
                status__in=[KhatmSlot.Status.RESERVED, KhatmSlot.Status.COMPLETED]
            ).count()
        return 0


class KhatmCampaignCreateSerializer(serializers.ModelSerializer):
    """Serializer for validating and creating a new collective Khatm Campaign."""
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=KhatmCategory.objects.filter(is_active=True),
        source='category',
        required=False,
        allow_null=True
    )
    target_surah_id = serializers.PrimaryKeyRelatedField(
        queryset=QuranSurah.objects.all(),
        source='target_surah',
        required=False,
        allow_null=True
    )
    target_units = serializers.IntegerField(
        required=False,
        allow_null=True
    )
    publish_to_topic_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        write_only=True,
        help_text="شناسه تاپیک در صورتی که سازنده بخواهد همزمان در تاپیک تحت مدیریتش پست شود"
    )

    class Meta:
        model = KhatmCampaign
        fields = [
            'id',
            'invite_code',
            'category_id',
            'title',
            'description',
            'unit_type',
            'target_units',
            'target_surah_id',
            'is_public',
            'deadline',
            'publish_to_topic_id',
            'created_at',
        ]
        read_only_fields = ['id', 'invite_code', 'created_at']

    def validate(self, attrs):
        unit_type = attrs.get('unit_type', KhatmCampaign.UnitType.JUZ)
        target_surah = attrs.get('target_surah')
        target_units = attrs.get('target_units')

        deadline = attrs.get('deadline')
        if deadline and deadline < timezone.now():
            raise serializers.ValidationError({
                'deadline': 'مهلت زمانی ختم نمی‌تواند در گذشته باشد.'
            })

        if unit_type == KhatmCampaign.UnitType.JUZ:
            attrs['target_units'] = 30
            attrs['target_surah'] = None
        elif unit_type == KhatmCampaign.UnitType.HIZB:
            attrs['target_units'] = 120
            attrs['target_surah'] = None
        elif unit_type == KhatmCampaign.UnitType.SURAH:
            if not target_surah:
                raise serializers.ValidationError({
                    'target_surah_id': 'برای ختم سوره، انتخاب سوره الزامی است.'
                })
            if not target_units or target_units < 1:
                raise serializers.ValidationError({
                    'target_units': 'تعداد هدف ختم سوره باید حداقل ۱ باشد.'
                })

        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['creator'] = user
        publish_to_topic_id = validated_data.pop('publish_to_topic_id', None)

        unit_type = validated_data.get('unit_type')
        target_units = validated_data.get('target_units', 30)

        with transaction.atomic():
            campaign = KhatmCampaign.objects.create(**validated_data)

            # Pre-generate discrete slots for Juz (30) or Hizb (120)
            if unit_type == KhatmCampaign.UnitType.JUZ:
                slots = [
                    KhatmSlot(
                        campaign=campaign,
                        unit_number=i,
                        quantity=1,
                        status=KhatmSlot.Status.AVAILABLE
                    )
                    for i in range(1, 31)
                ]
                KhatmSlot.objects.bulk_create(slots)

            elif unit_type == KhatmCampaign.UnitType.HIZB:
                slots = [
                    KhatmSlot(
                        campaign=campaign,
                        unit_number=i,
                        quantity=1,
                        status=KhatmSlot.Status.AVAILABLE
                    )
                    for i in range(1, 121)
                ]
                KhatmSlot.objects.bulk_create(slots)

            # For SURAH campaigns, slots are dynamic and allocated as users pick quantities.

            # Optional topic integration (PostPluginReference) executed safely on commit
            if publish_to_topic_id:
                def publish_to_topic():
                    try:
                        from apps.notes.models import Topic, Post, TopicAdmin
                        from apps.plugin_system.models import Plugin, PostPluginReference

                        topic = Topic.objects.filter(id=publish_to_topic_id).first()
                        if topic:
                            is_admin = (topic.created_by_id == user.id) or TopicAdmin.objects.filter(topic=topic, user=user).exists()
                            if is_admin:
                                quran_plugin = Plugin.objects.filter(identifier='quran').first()
                                if quran_plugin:
                                    post = Post.objects.create(
                                        topic=topic,
                                        author=user,
                                        content=f"📖 **{campaign.title}**\n\n{campaign.description or 'پویش جدید ختم قرآن کریم در تفکر ایجاد شد.'}\n\nجهت انتخاب سهم و قرائت: https://tafakor.ir/k/{campaign.invite_code}",
                                        media_type='text'
                                    )
                                    PostPluginReference.objects.create(
                                        post=post,
                                        plugin=quran_plugin,
                                        resource_type='khatm',
                                        external_id=campaign.invite_code,
                                        metadata={
                                            'title': campaign.title,
                                            'unit_type': campaign.unit_type,
                                            'target_units': campaign.target_units,
                                            'invite_code': campaign.invite_code,
                                        }
                                    )
                    except Exception:
                        logger.exception("Failed to publish campaign %s to topic %s", campaign.invite_code, publish_to_topic_id)

                transaction.on_commit(publish_to_topic)

        return campaign


class ReserveSlotRequestSerializer(serializers.Serializer):
    """Validates parameters for claiming a slot in a campaign."""
    unit_number = serializers.IntegerField(required=False, allow_null=True)
    quantity = serializers.IntegerField(required=False, default=1, min_value=1)


class CompleteSlotRequestSerializer(serializers.Serializer):
    """Validates parameters for marking a slot as completed."""
    slot_id = serializers.IntegerField(required=False, allow_null=True)
    unit_number = serializers.IntegerField(required=False, allow_null=True)


# ==============================================================================
# Personal Khatm Plan Serializers (Offline-First Cloud Sync)
# ==============================================================================

class PersonalKhatmPlanSerializer(serializers.ModelSerializer):
    """
    Serializer for a single personal Khatm plan matching Flutter domain entity.
    """
    class Meta:
        model = PersonalKhatmPlan
        fields = [
            'id',
            'client_id',
            'title',
            'unit_type',
            'range_from',
            'range_to',
            'planning_mode',
            'session_count',
            'quota_per_session',
            'cadence',
            'selected_weekdays',
            'start_date',
            'end_date',
            'sessions_progress',
            'completed_sessions',
            'is_completed',
            'is_archived',
            'client_updated_at',
            'created_at',
            'updated_at',
            'deleted_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PersonalKhatmPlanSyncRequestSerializer(serializers.Serializer):
    """Validates the bulk offline-sync request from mobile."""
    plans = PersonalKhatmPlanSerializer(many=True, required=False, default=list)
    last_synced_at = serializers.DateTimeField(required=False, allow_null=True)
