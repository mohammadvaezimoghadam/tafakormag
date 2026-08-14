from rest_framework import serializers
from apps.accounts.serializers import UserSerializer
from .models import DonationCampaign, DonationTransaction, TransparencyLog, CampaignAttachment


class DonorSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()
    donated_at = serializers.DateTimeField(source='completed_at', read_only=True)

    class Meta:
        model = DonationTransaction
        fields = ['id', 'name', 'avatar', 'amount', 'donated_at', 'is_anonymous']

    def get_name(self, obj):
        if obj.is_anonymous or not obj.donor:
            return "کاربر ناشناس"
        full_name = f"{obj.donor.first_name} {obj.donor.last_name}".strip()
        return full_name or obj.donor.phone or "کاربر تفکر"

    def get_avatar(self, obj):
        if obj.is_anonymous or not obj.donor:
            return None
        image = getattr(obj.donor, 'profile_image', None)
        if image:
            try:
                return image.url
            except Exception:
                return None
        return None


class CampaignAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CampaignAttachment
        fields = ['id', 'file', 'is_video', 'created_at']


class TransparencyLogSerializer(serializers.ModelSerializer):
    receipt_url = serializers.SerializerMethodField()
    date = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = TransparencyLog
        fields = ['id', 'title', 'description', 'amount', 'receipt_image', 'receipt_url', 'date', 'created_at']

    def get_receipt_url(self, obj):
        if obj.receipt_image:
            try:
                return obj.receipt_image.url
            except Exception:
                return None
        return None


class DonationCampaignDetailSerializer(serializers.ModelSerializer):
    creator_info = serializers.SerializerMethodField()
    donors = serializers.SerializerMethodField()
    transparency_logs = serializers.SerializerMethodField()
    attachments = serializers.SerializerMethodField()

    class Meta:
        model = DonationCampaign
        fields = [
            'id', 'topic', 'creator', 'creator_info', 'title', 'description', 'category',
            'target_amount', 'collected_amount', 'donors_count', 'cover_image',
            'deadline', 'iban', 'status', 'is_public_donors_list', 'attachments',
            'donors', 'transparency_logs', 'created_at', 'updated_at'
        ]

    def get_creator_info(self, obj):
        if not obj.creator:
            return None
        avatar_url = None
        image = getattr(obj.creator, 'profile_image', None)
        if image:
            try:
                avatar_url = image.url
            except Exception:
                pass
        full_name = f"{obj.creator.first_name} {obj.creator.last_name}".strip()
        return {
            'id': obj.creator.id,
            'name': full_name or obj.creator.phone or 'مدیر پویش',
            'avatar': avatar_url,
            'phone': obj.creator.phone
        }

    def get_donors(self, obj):
        if not obj.is_public_donors_list:
            return []
        successful_donations = obj.transactions.filter(
            status=DonationTransaction.PaymentStatus.SUCCESSFUL
        ).order_by('-completed_at')[:50]
        return DonorSerializer(successful_donations, many=True).data

    def get_transparency_logs(self, obj):
        logs = obj.transparency_logs.all().order_by('-created_at')
        return TransparencyLogSerializer(logs, many=True).data

    def get_attachments(self, obj):
        return [
            {
                'id': str(att.id),
                'url': att.file.url if att.file else '',
                'is_video': att.is_video
            }
            for att in obj.attachments.all()
        ]


class DonationCampaignCreateSerializer(serializers.ModelSerializer):
    uploaded_files = serializers.ListField(
        child=serializers.FileField(),
        required=False,
        write_only=True
    )
    deadline = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    class Meta:
        model = DonationCampaign
        fields = [
            'id', 'topic', 'title', 'description', 'category',
            'target_amount', 'cover_image', 'deadline', 'iban',
            'is_public_donors_list', 'uploaded_files', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def validate_target_amount(self, value):
        if value < 100000:
            raise serializers.ValidationError('حداقل مبلغ هدف پویش ۱۰۰,۰۰۰ تومان است.')
        return value

    def validate_deadline(self, value):
        if not value or str(value).lower() in ('none', 'null', '', 'undefined'):
            return None
        from django.utils import timezone
        from datetime import timedelta
        if value == '7_days':
            return timezone.now() + timedelta(days=7)
        if value == '14_days':
            return timezone.now() + timedelta(days=14)
        if value == '30_days':
            return timezone.now() + timedelta(days=30)
        
        try:
            from django.utils.dateparse import parse_datetime
            parsed = parse_datetime(value)
            if parsed:
                return parsed
        except Exception:
            pass
        return None

    def create(self, validated_data):
        validated_data.pop('uploaded_files', None)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data.pop('uploaded_files', None)
        return super().update(instance, validated_data)


class DonationInitiateSerializer(serializers.Serializer):
    amount = serializers.IntegerField(min_value=1000, required=True)
    is_anonymous = serializers.BooleanField(default=False)


class TransparencyLogCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransparencyLog
        fields = ['id', 'title', 'description', 'amount', 'receipt_image', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('مبلغ ثبت شده در لاگ شفافیت باید بزرگتر از صفر باشد.')
        return value
