from django.db import transaction
from django.utils import timezone
from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, NotFound, ValidationError
from apps.notes.models import Post, Topic
from .models import DonationCampaign, DonationTransaction, TransparencyLog, CampaignAttachment, PayoutRequest
from .serializers import (
    DonationCampaignDetailSerializer,
    DonationCampaignCreateSerializer,
    DonationInitiateSerializer,
    TransparencyLogCreateSerializer,
    TransparencyLogSerializer,
    PayoutRequestSerializer,
    PayoutRequestCreateSerializer,
    PayoutProcessInputSerializer
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
        # Auto-expire overdue active campaigns in a single optimized DB update
        now = timezone.now()
        DonationCampaign.objects.filter(
            status=DonationCampaign.StatusChoices.ACTIVE,
            deadline__isnull=False,
            deadline__lt=now
        ).update(status=DonationCampaign.StatusChoices.EXPIRED, updated_at=now)

        qs = DonationCampaign.objects.select_related('topic', 'creator').prefetch_related(
            'attachments', 'transparency_logs', 'transactions__donor'
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

        # Hide pending_review campaigns from public; show to staff and the creator only
        user = self.request.user
        if user.is_authenticated and (user.is_staff or user.is_superuser):
            pass
        elif user.is_authenticated:
            from django.db.models import Q
            qs = qs.filter(
                Q(status=DonationCampaign.StatusChoices.PENDING_REVIEW, creator=user) |
                ~Q(status=DonationCampaign.StatusChoices.PENDING_REVIEW)
            )
        else:
            qs = qs.exclude(status=DonationCampaign.StatusChoices.PENDING_REVIEW)

        return qs

    def perform_create(self, serializer):
        uploaded_files = self.request.FILES.getlist('uploaded_files')
        
        # Transaction Boundary: Ensure both campaign and topic chat post are created atomically
        with transaction.atomic():
            # Staff/superuser campaigns go directly to active; regular users need admin approval
            initial_status = (
                DonationCampaign.StatusChoices.ACTIVE
                if self.request.user.is_staff or self.request.user.is_superuser
                else DonationCampaign.StatusChoices.PENDING_REVIEW
            )
            campaign = serializer.save(creator=self.request.user, status=initial_status)

            # Save attachments if any
            for file_obj in uploaded_files:
                is_video = file_obj.content_type.startswith('video/') if hasattr(file_obj, 'content_type') else False
                CampaignAttachment.objects.create(
                    campaign=campaign,
                    file=file_obj,
                    is_video=is_video
                )

            # Auto-inject synchronized campaign post into Topic chat ONLY if active (staff created)
            # Pending review campaigns will have their topic chat post created upon admin approval
            if campaign.status == DonationCampaign.StatusChoices.ACTIVE:
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

        callback_url = request.build_absolute_uri('/api/v1/payments/callback/')

        trx, gateway_url = services.initiate_donation(
            campaign_id=id,
            amount=amount,
            is_anonymous=is_anonymous,
            donor=donor,
            callback_url=callback_url
        )

        return Response({
            'transaction_id': str(trx.id),
            'authority': trx.authority,
            'amount': trx.amount,
            'status': trx.status,
            'gateway_url': gateway_url
        }, status=status.HTTP_201_CREATED)


from django.http import HttpResponseRedirect


class PaymentCallbackView(APIView):
    """
    GET: Compatibility browser return handler for donation ZarinPal callbacks.
    Delegates verification and atomic settlement to centralized payments services.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        authority = request.query_params.get('Authority') or request.query_params.get('authority')
        status_param = (request.query_params.get('Status') or request.query_params.get('status') or '').upper()

        host = request.get_host()
        scheme = 'https' if request.is_secure() else 'http'
        frontend_base = f"{scheme}://{host}"

        outcome = services.handle_donation_callback(
            authority=authority,
            status_param=status_param,
            frontend_base=frontend_base,
        )
        return HttpResponseRedirect(outcome.redirect_url or f"{frontend_base}/donate?payment=failed")


class PaymentVerifyView(APIView):
    """
    POST / GET: Programmatic API endpoint for donation payment verification and settlement.
    """
    permission_classes = [permissions.AllowAny]

    def _serialize_verified_transaction(self, trx: DonationTransaction, message: str):
        return Response({
            'status': 'success',
            'message': message,
            'transaction_id': str(trx.id),
            'campaign_id': str(trx.campaign_id),
            'amount': trx.amount,
            'tracking_code': trx.tracking_code,
            'gateway_reference_id': trx.gateway_reference_id,
            'completed_at': trx.completed_at.isoformat() if trx.completed_at else None
        }, status=status.HTTP_200_OK)

    def get(self, request):
        authority = request.query_params.get('authority') or request.query_params.get('Authority')
        gateway_ref = request.query_params.get('ref_id') or request.query_params.get('RefID')
        tracking_code = request.query_params.get('tracking_code')

        if not authority:
            return Response({'error': 'شناسه تراکنش (Authority) ارسال نشده است.'}, status=status.HTTP_400_BAD_REQUEST)

        trx = services.verify_donation_payment(
            authority=authority,
            gateway_ref=gateway_ref,
            tracking_code=tracking_code,
        )
        return self._serialize_verified_transaction(trx, 'پرداخت با موفقیت انجام و ثبت گردید.')

    def post(self, request):
        authority = request.data.get('authority')
        gateway_ref = request.data.get('gateway_ref')
        tracking_code = request.data.get('tracking_code')

        if not authority:
            return Response({'error': 'شناسه تراکنش (Authority) الزامی است.'}, status=status.HTTP_400_BAD_REQUEST)

        trx = services.verify_donation_payment(
            authority=authority,
            gateway_ref=gateway_ref,
            tracking_code=tracking_code,
        )
        return self._serialize_verified_transaction(trx, 'پرداخت با موفقیت تأیید و تسویه شد.')



class CampaignApproveView(APIView):
    """
    POST: Approves a pending_review campaign. Staff/superuser only.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        try:
            campaign = DonationCampaign.objects.get(id=id)
        except DonationCampaign.DoesNotExist:
            raise NotFound('پویش مورد نظر یافت نشد.')

        if not (request.user.is_staff or request.user.is_superuser):
            raise PermissionDenied('فقط مدیران مجاز به تأیید پویش هستند.')

        if campaign.status != DonationCampaign.StatusChoices.PENDING_REVIEW:
            raise ValidationError({'status': f'پویش در وضعیت «{campaign.get_status_display()}» است و قابل تأیید نیست.'})

        with transaction.atomic():
            campaign.status = DonationCampaign.StatusChoices.ACTIVE
            if not campaign.post:
                post_content = f"🤲 **پویش مهربانی: {campaign.title}**\n\n{campaign.description}\n\n🎯 مبلغ هدف: {campaign.target_amount:,} تومان"
                post = Post.objects.create(
                    topic=campaign.topic,
                    author=campaign.creator,
                    content=post_content,
                    media_type="image" if campaign.cover_image else "text",
                    media_file=campaign.cover_image.name if campaign.cover_image else None
                )
                campaign.post = post
                campaign.save(update_fields=['status', 'post', 'updated_at'])
            else:
                campaign.save(update_fields=['status', 'updated_at'])

        serializer = DonationCampaignDetailSerializer(campaign, context={'request': request})
        return Response({
            'detail': 'پویش با موفقیت تأیید و فعال شد.',
            'campaign': serializer.data
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


class CampaignPayoutListCreateView(APIView):
    """
    GET: List payout requests for a campaign (creator or staff only).
    POST: Submit a new payout request for a campaign.
    """
    permission_classes = [permissions.IsAuthenticated]

    def _get_campaign(self, campaign_id, user):
        try:
            campaign = DonationCampaign.objects.get(id=campaign_id)
        except DonationCampaign.DoesNotExist:
            raise NotFound('پویش مورد نظر یافت نشد.')

        if campaign.creator_id != user.id and not (user.is_staff or user.is_superuser):
            raise PermissionDenied('شما مجاز به مشاهده یا درخواست تسویه این پویش نیستید.')
        return campaign

    def get(self, request, id):
        campaign = self._get_campaign(id, request.user)
        qs = campaign.payout_requests.select_related('requested_by', 'campaign').order_by('-created_at')
        serializer = PayoutRequestSerializer(qs, many=True, context={'request': request})
        return Response({
            'available_balance': campaign.available_payout_balance,
            'collected_amount': campaign.collected_amount,
            'total_settled_amount': campaign.total_settled_amount,
            'default_iban': campaign.iban or '',
            'results': serializer.data
        }, status=status.HTTP_200_OK)

    def post(self, request, id):
        serializer = PayoutRequestCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        payout = services.create_payout_request(
            campaign_id=id,
            user=request.user,
            amount=data['amount'],
            iban=data['iban'],
            account_holder_name=data['account_holder_name'],
        )
        return Response(
            PayoutRequestSerializer(payout, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )


class AdminPayoutListView(generics.ListAPIView):
    """
    GET: List all payout requests across all campaigns (Staff only).
    """
    permission_classes = [permissions.IsAdminUser]
    serializer_class = PayoutRequestSerializer

    def get_queryset(self):
        qs = PayoutRequest.objects.select_related('campaign', 'requested_by', 'processed_by').order_by('-created_at')
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs


class PayoutProcessView(APIView):
    """
    POST: Process, complete, or reject a payout request (Staff only).
    """
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, id):
        serializer = PayoutProcessInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        payout = services.process_payout_settlement(
            payout_id=id,
            admin_user=request.user,
            action=data['action'],
            tracking_number=data.get('tracking_number', ''),
            receipt_file=request.FILES.get('receipt_file'),
            rejection_reason=data.get('rejection_reason', ''),
            notes=data.get('notes', ''),
        )
        return Response(
            PayoutRequestSerializer(payout, context={'request': request}).data,
            status=status.HTTP_200_OK
        )

