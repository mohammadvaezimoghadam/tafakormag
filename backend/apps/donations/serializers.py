from rest_framework import serializers
from apps.accounts.serializers import UserSerializer
from .models import DonationCampaign, DonationTransaction, TransparencyLog, CampaignAttachment, PayoutRequest


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
                url = image.url
                request = self.context.get('request')
                if request and url:
                    return request.build_absolute_uri(url)
                return url
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
                url = obj.receipt_image.url
                request = self.context.get('request')
                if request and url:
                    return request.build_absolute_uri(url)
                return url
            except Exception:
                return None
        return None


class DonationCampaignDetailSerializer(serializers.ModelSerializer):
    topic_title = serializers.SerializerMethodField()
    creator_info = serializers.SerializerMethodField()
    donors = serializers.SerializerMethodField()
    transparency_logs = serializers.SerializerMethodField()
    attachments = serializers.SerializerMethodField()
    available_payout_balance = serializers.IntegerField(read_only=True)
    total_settled_amount = serializers.IntegerField(read_only=True)
    is_ended = serializers.BooleanField(read_only=True)
    can_request_payout = serializers.SerializerMethodField()

    class Meta:
        model = DonationCampaign
        fields = [
            'id', 'topic', 'topic_title', 'creator', 'creator_info', 'title', 'description', 'category',
            'target_amount', 'collected_amount', 'donors_count', 'cover_image',
            'deadline', 'iban', 'status', 'is_public_donors_list', 'attachments',
            'donors', 'transparency_logs', 'available_payout_balance', 'total_settled_amount',
            'is_ended', 'can_request_payout', 'created_at', 'updated_at'
        ]

    def get_can_request_payout(self, obj):
        request = self.context.get('request')
        if not request or not request.user or not request.user.is_authenticated:
            return False
        is_creator = obj.creator_id == request.user.id
        is_staff = request.user.is_staff or request.user.is_superuser
        if not (is_creator or is_staff):
            return False
        # Regular creators can only request payout when the campaign has ended
        if not obj.is_ended and not is_staff:
            return False
        return obj.available_payout_balance > 0

    def get_topic_title(self, obj):
        return obj.topic.name if obj.topic else None

    def get_creator_info(self, obj):
        if not obj.creator:
            return None
        avatar_url = None
        image = getattr(obj.creator, 'profile_image', None)
        if image:
            try:
                url = image.url
                request = self.context.get('request')
                avatar_url = request.build_absolute_uri(url) if request else url
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
        ).select_related('donor').order_by('-completed_at')[:50]
        return DonorSerializer(successful_donations, many=True, context=self.context).data

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
    is_public_donors_list = serializers.BooleanField(default=True, required=False)

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


class PayoutRequestSerializer(serializers.ModelSerializer):
    campaign_title = serializers.CharField(source='campaign.title', read_only=True)
    requested_by_phone = serializers.CharField(source='requested_by.phone', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    receipt_url = serializers.SerializerMethodField()

    class Meta:
        model = PayoutRequest
        fields = [
            'id', 'campaign', 'campaign_title', 'requested_by', 'requested_by_phone',
            'amount', 'iban', 'account_holder_name', 'status', 'status_display',
            'tracking_number', 'receipt_file', 'receipt_url', 'rejection_reason',
            'admin_notes', 'settled_at', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'campaign', 'requested_by', 'status', 'tracking_number',
            'receipt_file', 'rejection_reason', 'admin_notes', 'settled_at',
            'created_at', 'updated_at'
        ]

    def get_receipt_url(self, obj):
        if obj.receipt_file:
            try:
                request = self.context.get('request')
                url = obj.receipt_file.url
                return request.build_absolute_uri(url) if request else url
            except Exception:
                return None
        return None


class PayoutRequestCreateSerializer(serializers.Serializer):
    amount = serializers.IntegerField(min_value=10000, required=True)
    iban = serializers.CharField(max_length=34, required=True)
    account_holder_name = serializers.CharField(max_length=150, required=True)


class PayoutProcessInputSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['complete', 'reject', 'approve'])
    tracking_number = serializers.CharField(max_length=100, required=False, allow_blank=True)
    receipt_file = serializers.FileField(required=False, allow_null=True)
    rejection_reason = serializers.CharField(max_length=500, required=False, allow_blank=True)
    notes = serializers.CharField(max_length=500, required=False, allow_blank=True)

