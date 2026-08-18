from django.db import transaction
from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, NotFound, ValidationError
from apps.notes.models import Post, Topic
from .models import DonationCampaign, DonationTransaction, TransparencyLog, CampaignAttachment
from .serializers import (
    DonationCampaignDetailSerializer,
    DonationCampaignCreateSerializer,
    DonationInitiateSerializer,
    TransparencyLogCreateSerializer,
    TransparencyLogSerializer
)
from . import services


class DonationCampaignListCreateView(generics.ListCreateAPIView):
    """
    GET: Returns a filtered list of donation campaigns for the Kindness Feed.
    POST: Atomically creates a new campaign and posts a notification card in the topic chat.
    """
    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return DonationCampaignCreateSerializer
        return DonationCampaignDetailSerializer

    def get_queryset(self):
        qs = DonationCampaign.objects.select_related('topic', 'creator').prefetch_related(
            'attachments', 'transparency_logs', 'transactions'
        ).all()

        category = self.request.query_params.get('category')
        if category:
            qs = qs.filter(category=category)

        status_param = self.request.query_params.get('status')
        if status_param:
            qs = qs.filter(status=status_param)

        topic_id = self.request.query_params.get('topic')
        if topic_id:
            qs = qs.filter(topic_id=topic_id)

        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(title__icontains=search)

        return qs

    def perform_create(self, serializer):
        uploaded_files = self.request.FILES.getlist('uploaded_files')
        
        # Transaction Boundary: Ensure both campaign and topic chat post are created atomically
        with transaction.atomic():
            campaign = serializer.save(creator=self.request.user)

            # Save attachments if any
            for file_obj in uploaded_files:
                is_video = file_obj.content_type.startswith('video/') if hasattr(file_obj, 'content_type') else False
                CampaignAttachment.objects.create(
                    campaign=campaign,
                    file=file_obj,
                    is_video=is_video
                )

            # Auto-inject synchronized campaign post into Topic chat
            post_content = f"🤲 **پویش مهربانی: {campaign.title}**\n\n{campaign.description}\n\n🎯 مبلغ هدف: {campaign.target_amount:,} تومان"
            post = Post.objects.create(
                topic=campaign.topic,
                author=self.request.user,
                content=post_content,
                media_type="image" if campaign.cover_image else "text",
                media_file=campaign.cover_image.name if campaign.cover_image else None
            )
            campaign.post = post
            campaign.save(update_fields=['post'])

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # Return full detail payload of the newly created campaign
        instance = serializer.instance
        detail_serializer = DonationCampaignDetailSerializer(instance, context={'request': request})
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED)


class DonationCampaignDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Returns full details for a single donation campaign.
    PUT/PATCH: Updates campaign details (creator/staff only) and syncs topic post content.
    DELETE: Deletes the campaign and linked topic post (creator/staff only).
    """
    queryset = DonationCampaign.objects.select_related('topic', 'creator').prefetch_related(
        'attachments', 'transparency_logs', 'transactions__donor'
    ).all()
    lookup_field = 'id'

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return DonationCampaignCreateSerializer
        return DonationCampaignDetailSerializer

    def get_object(self):
        obj = super().get_object()
        obj.check_and_update_status()
        return obj

    def perform_update(self, serializer):
        campaign = self.get_object()
        if campaign.creator != self.request.user and not self.request.user.is_staff:
            raise PermissionDenied('شما مجاز به ویرایش این پویش نیستید.')

        with transaction.atomic():
            updated_campaign = serializer.save()
            uploaded_files = self.request.FILES.getlist('uploaded_files')
            for file_obj in uploaded_files:
                is_video = file_obj.content_type.startswith('video/') if hasattr(file_obj, 'content_type') else False
                CampaignAttachment.objects.create(
                    campaign=updated_campaign,
                    file=file_obj,
                    is_video=is_video
                )

            # Sync topic post if linked
            if updated_campaign.post:
                post_content = f"🤲 **پویش مهربانی: {updated_campaign.title}**\n\n{updated_campaign.description}\n\n🎯 مبلغ هدف: {updated_campaign.target_amount:,} تومان"
                updated_campaign.post.content = post_content
                if updated_campaign.cover_image:
                    updated_campaign.post.media_file = updated_campaign.cover_image.name
                    updated_campaign.post.media_type = "image"
                updated_campaign.post.save(update_fields=['content', 'media_file', 'media_type', 'updated_at'])

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        detail_serializer = DonationCampaignDetailSerializer(serializer.instance, context={'request': request})
        return Response(detail_serializer.data, status=status.HTTP_200_OK)

    def perform_destroy(self, instance):
        pass

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.creator != self.request.user and not (self.request.user.is_staff or self.request.user.is_superuser):
            raise PermissionDenied('شما مجاز به حذف این پویش نیستید.')

        has_donations = (
            (instance.donors_count and instance.donors_count > 0) or
            (instance.collected_amount and instance.collected_amount > 0) or
            instance.transactions.filter(status=DonationTransaction.PaymentStatus.SUCCESSFUL).exists()
        )

        with transaction.atomic():
            if has_donations:
                # Soft delete: Mark campaign status as inactive so financial records & transparency remain accessible
                instance.status = DonationCampaign.StatusChoices.INACTIVE
                instance.save(update_fields=['status', 'updated_at'])

                # Update linked topic chat message
                if instance.post:
                    instance.post.content = f"🛑 **[پویش متوقف شد]** {instance.title}\n\n{instance.description}"
                    instance.post.save(update_fields=['content', 'updated_at'])

                serializer = DonationCampaignDetailSerializer(instance, context={'request': request})
                return Response({
                    'detail': 'پویش به دلیل داشتن واریزی متوقف و غیرفعال شد و سوابق آن جهت شفافیت حفظ گردید.',
                    'action': 'deactivated',
                    'campaign': serializer.data
                }, status=status.HTTP_200_OK)
            else:
                # Hard delete: Completely purge campaign, attachments, unfulfilled transactions and linked post
                if instance.post:
                    instance.post.delete()
                instance.transactions.all().delete()
                instance.delete()
                return Response({
                    'detail': 'پویش با موفقیت به طور کامل حذف شد.',
                    'action': 'deleted'
                }, status=status.HTTP_200_OK)


class DonationInitiateView(APIView):
    """
    POST: Initiates a pending donation transaction and returns the gateway redirect URL.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, id):
        serializer = DonationInitiateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        amount = serializer.validated_data['amount']
        is_anonymous = serializer.validated_data.get('is_anonymous', False)
        donor = request.user if request.user.is_authenticated else None

        trx, gateway_url = services.initiate_donation(
            campaign_id=id,
            amount=amount,
            is_anonymous=is_anonymous,
            donor=donor
        )

        return Response({
            'transaction_id': str(trx.id),
            'authority': trx.authority,
            'amount': trx.amount,
            'status': trx.status,
            'gateway_url': gateway_url
        }, status=status.HTTP_201_CREATED)


class PaymentVerifyView(APIView):
    """
    POST / GET: Payment gateway callback handler that triggers atomic verification and settlement.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        authority = request.query_params.get('authority') or request.query_params.get('Authority')
        gateway_ref = request.query_params.get('ref_id') or request.query_params.get('RefID')
        tracking_code = request.query_params.get('tracking_code')

        if not authority:
            return Response({'error': 'شناسه تراکنش (Authority) ارسال نشده است.'}, status=status.HTTP_400_BAD_REQUEST)

        trx = services.verify_and_settle_transaction(
            authority=authority,
            gateway_ref=gateway_ref,
            tracking_code=tracking_code
        )

        return Response({
            'status': 'success',
            'message': 'پرداخت با موفقیت انجام و ثبت گردید.',
            'transaction_id': str(trx.id),
            'campaign_id': str(trx.campaign_id),
            'amount': trx.amount,
            'tracking_code': trx.tracking_code,
            'gateway_reference_id': trx.gateway_reference_id,
            'completed_at': trx.completed_at.isoformat() if trx.completed_at else None
        }, status=status.HTTP_200_OK)

    def post(self, request):
        authority = request.data.get('authority')
        gateway_ref = request.data.get('gateway_ref')
        tracking_code = request.data.get('tracking_code')

        if not authority:
            return Response({'error': 'شناسه تراکنش (Authority) الزامی است.'}, status=status.HTTP_400_BAD_REQUEST)

        trx = services.verify_and_settle_transaction(
            authority=authority,
            gateway_ref=gateway_ref,
            tracking_code=tracking_code
        )

        return Response({
            'status': 'success',
            'message': 'پرداخت با موفقیت تأیید و تسویه شد.',
            'transaction_id': str(trx.id),
            'campaign_id': str(trx.campaign_id),
            'amount': trx.amount,
            'tracking_code': trx.tracking_code,
            'gateway_reference_id': trx.gateway_reference_id,
            'completed_at': trx.completed_at.isoformat() if trx.completed_at else None
        }, status=status.HTTP_200_OK)


class TransparencyLogCreateView(APIView):
    """
    POST: Uploads transparency logs/invoices for a campaign. Only allowed for campaign creator or admin.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        try:
            campaign = DonationCampaign.objects.get(id=id)
        except DonationCampaign.DoesNotExist:
            raise NotFound('پویش مورد نظر یافت نشد.')

        if campaign.creator != request.user and not request.user.is_staff:
            raise PermissionDenied('شما مجاز به ثبت گزارش شفافیت برای این پویش نیستید.')

        serializer = TransparencyLogCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        log = serializer.save(campaign=campaign)

        return Response(TransparencyLogSerializer(log).data, status=status.HTTP_201_CREATED)
