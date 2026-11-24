"""
DRF Views and ViewSets for Quran Khatm System (Group Campaigns & Personal Offline-First Plans).
"""
import logging
from datetime import timedelta
from django.shortcuts import get_object_or_404, render
from django.db import transaction, IntegrityError
from django.db.models import Q, F
from django.db.models.functions import Greatest
from django.utils import timezone
from django.views import View
from rest_framework import viewsets, generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.throttling import ScopedRateThrottle

from plugins.quran.models import (
    KhatmCategory,
    KhatmCampaign,
    KhatmSlot,
    PersonalKhatmPlan,
)
from plugins.quran.khatm_serializers import (
    KhatmCategorySerializer,
    KhatmSlotSerializer,
    KhatmCampaignListSerializer,
    KhatmCampaignDetailSerializer,
    KhatmCampaignCreateSerializer,
    ReserveSlotRequestSerializer,
    CompleteSlotRequestSerializer,
    PersonalKhatmPlanSerializer,
    PersonalKhatmPlanSyncRequestSerializer,
)

logger = logging.getLogger(__name__)


def _check_profile_name_complete(user):
    """
    Requires authenticated users to have both first_name and last_name populated
    before creating or participating in a Group Khatm campaign.
    """
    first_name = (getattr(user, 'first_name', '') or '').strip()
    last_name = (getattr(user, 'last_name', '') or '').strip()
    if not first_name or not last_name:
        return Response(
            {
                "code": "profile_name_required",
                "detail": "برای شرکت در ختم، لطفاً ابتدا نام و نام خانوادگی خود را تکمیل کنید.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    return None


class KhatmStandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class KhatmCategoryListView(generics.ListAPIView):
    """
    List of active Khatm categories / intentions (e.g. for deceased, healing, etc.).
    Public endpoint.
    """
    queryset = KhatmCategory.objects.filter(is_active=True).order_by('display_order', 'id')
    serializer_class = KhatmCategorySerializer
    permission_classes = [permissions.AllowAny]


class KhatmCampaignViewSet(viewsets.ModelViewSet):
    """
    Manages collective Khatm Campaigns: Explore feed, Create, Detail, Reserve, Complete, Release.
    """
    lookup_field = 'invite_code'
    lookup_url_kwarg = 'invite_code'
    pagination_class = KhatmStandardPagination
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'khatm_actions'

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return KhatmCampaignDetailSerializer
        if self.action == 'create':
            return KhatmCampaignCreateSerializer
        return KhatmCampaignListSerializer

    def get_queryset(self):
        qs = KhatmCampaign.objects.filter(
            deleted_at__isnull=True
        ).select_related('category', 'creator', 'target_surah')

        if self.action == 'retrieve':
            qs = qs.prefetch_related('slots__user')

        if self.action == 'list':
            # Public showcase feed
            qs = qs.filter(is_public=True)

            status_param = self.request.query_params.get('status', KhatmCampaign.Status.ACTIVE)
            if status_param != 'all':
                qs = qs.filter(status=status_param)

            category = self.request.query_params.get('category')
            if category:
                if category.isdigit():
                    qs = qs.filter(category_id=int(category))
                else:
                    qs = qs.filter(category__slug=category)

            unit_type = self.request.query_params.get('unit_type')
            if unit_type:
                qs = qs.filter(unit_type=unit_type)

            search = self.request.query_params.get('q')
            if search:
                qs = qs.filter(
                    Q(title__icontains=search) | Q(description__icontains=search)
                )

        return qs.order_by('-created_at')

    def create(self, request, *args, **kwargs):
        name_error = _check_profile_name_complete(request.user)
        if name_error is not None:
            return name_error

        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        campaign = serializer.save()

        # Return full detail serializer for immediate UI presentation
        detail_serializer = KhatmCampaignDetailSerializer(
            campaign, context={'request': request}
        )
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my(self, request):
        """
        List campaigns created by the current user or where the user has participation slots.
        """
        tab = request.query_params.get('tab', 'all')
        user = request.user

        qs = KhatmCampaign.objects.filter(
            deleted_at__isnull=True
        ).select_related('category', 'creator', 'target_surah')

        if tab == 'created':
            qs = qs.filter(creator=user).distinct()
        elif tab == 'participated':
            qs = qs.filter(slots__user=user).exclude(creator=user).distinct()
        else:
            qs = qs.filter(Q(creator=user) | Q(slots__user=user)).distinct()

        page = self.paginate_queryset(qs.order_by('-created_at'))
        if page is not None:
            serializer = KhatmCampaignListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = KhatmCampaignListSerializer(qs.order_by('-created_at'), many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def reserve(self, request, invite_code=None):
        """
        Atomically claims a slot in the campaign for the authenticated user.
        """
        name_error = _check_profile_name_complete(request.user)
        if name_error is not None:
            return name_error

        serializer = ReserveSlotRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        now = timezone.now()

        with transaction.atomic():
            campaign = get_object_or_404(
                KhatmCampaign.objects.select_for_update(),
                invite_code=invite_code,
                deleted_at__isnull=True
            )

            if campaign.status != KhatmCampaign.Status.ACTIVE:
                return Response(
                    {"detail": "این پویش در حال حاضر فعال نیست و امکان برداشتن سهم وجود ندارد."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if campaign.deadline and campaign.deadline < now:
                campaign.status = KhatmCampaign.Status.EXPIRED
                campaign.save(update_fields=['status'])
                return Response(
                    {"detail": "مهلت زمانی شرکت در این پویش به پایان رسیده است."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Slot expiry window: 48 hours or campaign deadline, whichever comes first
            slot_expiry = now + timedelta(hours=48)
            if campaign.deadline and campaign.deadline < slot_expiry:
                slot_expiry = campaign.deadline

            if campaign.unit_type in [KhatmCampaign.UnitType.JUZ, KhatmCampaign.UnitType.HIZB]:
                unit_number = serializer.validated_data.get('unit_number')
                max_units = 30 if campaign.unit_type == KhatmCampaign.UnitType.JUZ else 120

                if not unit_number or not (1 <= unit_number <= max_units):
                    return Response(
                        {"detail": f"شماره واحد نامعتبر است (باید بین ۱ تا {max_units} باشد)."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                slot = KhatmSlot.objects.select_for_update().filter(
                    campaign=campaign,
                    unit_number=unit_number
                ).first()

                if not slot:
                    return Response(
                        {"detail": "سهم مورد نظر یافت نشد."},
                        status=status.HTTP_404_NOT_FOUND
                    )

                # Check if already completed
                if slot.status == KhatmSlot.Status.COMPLETED:
                    return Response(
                        {"detail": "این سهم قبلاً توسط کاربر دیگری قرائت و تکمیل شده است."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Check if currently reserved by someone else and not yet expired
                if slot.status == KhatmSlot.Status.RESERVED and slot.user_id != user.id:
                    if slot.expires_at and slot.expires_at > now:
                        return Response(
                            {"detail": "این سهم در حال حاضر توسط کاربر دیگری در حال قرائت است."},
                            status=status.HTTP_409_CONFLICT
                        )

                # Claim slot
                is_reclaim = (slot.status == KhatmSlot.Status.RESERVED)
                slot.user = user
                slot.status = KhatmSlot.Status.RESERVED
                slot.reserved_at = now
                slot.expires_at = slot_expiry
                slot.save()

                if not is_reclaim:
                    KhatmCampaign.objects.filter(id=campaign.id).update(
                        reserved_units=F('reserved_units') + 1
                    )

            else:
                # Surah campaign: dynamic slot allocation
                quantity = serializer.validated_data.get('quantity', 1)
                remaining = campaign.target_units - (campaign.reserved_units + campaign.completed_units)

                if quantity > remaining:
                    return Response(
                        {"detail": f"تعداد سهم درخواستی ({quantity}) از باقیمانده پویش ({remaining}) بیشتر است."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                slot = KhatmSlot.objects.create(
                    campaign=campaign,
                    user=user,
                    quantity=quantity,
                    status=KhatmSlot.Status.RESERVED,
                    reserved_at=now,
                    expires_at=slot_expiry
                )
                KhatmCampaign.objects.filter(id=campaign.id).update(
                    reserved_units=F('reserved_units') + quantity
                )

        campaign.refresh_from_db()
        detail_serializer = KhatmCampaignDetailSerializer(
            campaign, context={'request': request}
        )
        return Response({
            "detail": "سهم با موفقیت برای شما ثبت شد.",
            "slot": KhatmSlotSerializer(slot, context={'request': request}).data,
            "campaign": detail_serializer.data,
        })

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def complete(self, request, invite_code=None):
        """
        Marks a reserved slot as completed. Decrements reserved_units, increments completed_units.
        """
        serializer = CompleteSlotRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        now = timezone.now()

        with transaction.atomic():
            campaign = get_object_or_404(
                KhatmCampaign.objects.select_for_update(),
                invite_code=invite_code,
                deleted_at__isnull=True
            )

            slot_id = serializer.validated_data.get('slot_id')
            unit_number = serializer.validated_data.get('unit_number')

            if slot_id:
                slot = KhatmSlot.objects.select_for_update().filter(
                    campaign=campaign,
                    id=slot_id
                ).first()
            elif unit_number:
                slot = KhatmSlot.objects.select_for_update().filter(
                    campaign=campaign,
                    unit_number=unit_number
                ).first()
            else:
                return Response(
                    {"detail": "ارسال slot_id یا unit_number الزامی است."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not slot:
                return Response(
                    {"detail": "سهم مورد نظر یافت نشد."},
                    status=status.HTTP_404_NOT_FOUND
                )

            if slot.status == KhatmSlot.Status.COMPLETED:
                return Response(
                    {"detail": "این سهم قبلاً به عنوان تکمیل‌شده ثبت گردیده است."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check permission: slot owner or campaign creator
            if slot.user and slot.user_id != user.id and campaign.creator_id != user.id:
                return Response(
                    {"detail": "شما دسترسی لازم برای ثبت اتمام این سهم را ندارید."},
                    status=status.HTTP_403_FORBIDDEN
                )

            was_reserved = (slot.status == KhatmSlot.Status.RESERVED)
            slot.status = KhatmSlot.Status.COMPLETED
            slot.completed_at = now
            slot.expires_at = None
            if not slot.user:
                slot.user = user
            slot.save()

            if was_reserved:
                KhatmCampaign.objects.filter(id=campaign.id).update(
                    reserved_units=Greatest(F('reserved_units') - slot.quantity, 0),
                    completed_units=F('completed_units') + slot.quantity
                )
            else:
                KhatmCampaign.objects.filter(id=campaign.id).update(
                    completed_units=F('completed_units') + slot.quantity
                )

            campaign.refresh_from_db()
            if campaign.completed_units >= campaign.target_units:
                campaign.status = KhatmCampaign.Status.COMPLETED
                campaign.save(update_fields=['status'])

        detail_serializer = KhatmCampaignDetailSerializer(
            campaign, context={'request': request}
        )
        return Response({
            "detail": "قبول حق؛ قرائت شما با موفقیت ثبت شد.",
            "slot": KhatmSlotSerializer(slot, context={'request': request}).data,
            "campaign": detail_serializer.data,
        })

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def release(self, request, invite_code=None):
        """
        Voluntarily cancels/releases a reserved slot before reading.
        """
        serializer = CompleteSlotRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        slot_id = serializer.validated_data.get('slot_id')
        unit_number = serializer.validated_data.get('unit_number')

        with transaction.atomic():
            campaign = get_object_or_404(
                KhatmCampaign.objects.select_for_update(),
                invite_code=invite_code,
                deleted_at__isnull=True
            )

            if slot_id:
                slot = KhatmSlot.objects.select_for_update().filter(
                    campaign=campaign, id=slot_id
                ).first()
            elif unit_number:
                slot = KhatmSlot.objects.select_for_update().filter(
                    campaign=campaign, unit_number=unit_number
                ).first()
            else:
                return Response(
                    {"detail": "ارسال slot_id یا unit_number الزامی است."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not slot:
                return Response(
                    {"detail": "سهم مورد نظر یافت نشد."},
                    status=status.HTTP_404_NOT_FOUND
                )

            if slot.status != KhatmSlot.Status.RESERVED:
                return Response(
                    {"detail": "تنها سهم‌های در حال قرائت قابل آزادسازی هستند."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if slot.user_id != user.id and campaign.creator_id != user.id:
                return Response(
                    {"detail": "شما مجاز به انصراف از سهم کاربر دیگری نیستید."},
                    status=status.HTTP_403_FORBIDDEN
                )

            if campaign.unit_type in [KhatmCampaign.UnitType.JUZ, KhatmCampaign.UnitType.HIZB]:
                slot.status = KhatmSlot.Status.AVAILABLE
                slot.user = None
                slot.reserved_at = None
                slot.expires_at = None
                slot.save()
            else:
                slot.delete()

            KhatmCampaign.objects.filter(id=campaign.id).update(
                reserved_units=Greatest(F('reserved_units') - slot.quantity, 0)
            )

        campaign.refresh_from_db()
        detail_serializer = KhatmCampaignDetailSerializer(
            campaign, context={'request': request}
        )
        return Response({
            "detail": "سهم با موفقیت آزاد شد.",
            "campaign": detail_serializer.data,
        })


# ==============================================================================
# Personal Khatm Plan Synchronization View (Offline-First)
# ==============================================================================

class PersonalKhatmPlanSyncView(APIView):
    """
    Offline-First bidirectional synchronization for Personal Khatm plans.
    Enforces Last-Write-Wins (LWW) resolution based on `client_updated_at`.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Returns all non-deleted personal plans for the authenticated user."""
        plans = PersonalKhatmPlan.objects.filter(
            user=request.user,
            deleted_at__isnull=True
        ).order_by('-updated_at')

        serializer = PersonalKhatmPlanSerializer(plans, many=True)
        return Response({
            "server_time": timezone.now(),
            "plans": serializer.data,
        })

    def post(self, request):
        """
        Synchronizes a batch of local plans from the mobile client.
        Applies Last-Write-Wins on conflicting client_id items.
        Returns the full current state of plans modified on the server.
        """
        serializer = PersonalKhatmPlanSyncRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        incoming_plans = serializer.validated_data.get('plans', [])
        last_synced_at = serializer.validated_data.get('last_synced_at')
        user = request.user

        with transaction.atomic():
            for plan_data in incoming_plans:
                client_id = plan_data['client_id']
                incoming_updated_at = plan_data['client_updated_at']

                existing = PersonalKhatmPlan.objects.select_for_update().filter(
                    user=user,
                    client_id=client_id
                ).first()

                if existing:
                    # Last-Write-Wins check
                    if incoming_updated_at > existing.client_updated_at:
                        for field, value in plan_data.items():
                            if field not in ['id', 'user']:
                                setattr(existing, field, value)
                        existing.save()
                        logger.info("Updated PersonalKhatm %s (LWW won by client)", client_id)
                else:
                    try:
                        with transaction.atomic():
                            PersonalKhatmPlan.objects.create(user=user, **plan_data)
                            logger.info("Created new PersonalKhatm %s for user %s", client_id, user.id)
                    except IntegrityError:
                        # Concurrently created by another request; update if newer
                        existing = PersonalKhatmPlan.objects.select_for_update().filter(
                            user=user,
                            client_id=client_id
                        ).first()
                        if existing and incoming_updated_at > existing.client_updated_at:
                            for field, value in plan_data.items():
                                if field not in ['id', 'user']:
                                    setattr(existing, field, value)
                            existing.save()

        # Extract server_time before running the query to avoid clock skew
        server_time = timezone.now()

        # Return updated records from server
        qs = PersonalKhatmPlan.objects.filter(user=user)
        if last_synced_at:
            qs = qs.filter(updated_at__gt=last_synced_at)
        else:
            qs = qs.filter(deleted_at__isnull=True)

        response_serializer = PersonalKhatmPlanSerializer(qs.order_by('-updated_at'), many=True)

        return Response({
            "server_time": server_time,
            "synced_count": len(incoming_plans),
            "plans": response_serializer.data,
        })


# ==============================================================================
# Web Preview & Social Sharing View (Eitaa, Telegram, Bale Open Graph)
# ==============================================================================

class KhatmWebPreviewView(View):
    """
    Renders an Open Graph preview card for social messengers (Eitaa, Telegram, Bale)
    with deep linking / Universal Link to open inside the Flutter Quran app.
    """
    def get(self, request, invite_code):
        campaign = get_object_or_404(
            KhatmCampaign.objects.select_related('category', 'creator', 'target_surah'),
            invite_code=invite_code,
            deleted_at__isnull=True
        )

        progress = 0
        if campaign.target_units > 0:
            progress = round((campaign.completed_units / campaign.target_units) * 100, 1)

        remaining = max(campaign.target_units - (campaign.reserved_units + campaign.completed_units), 0)

        context = {
            'campaign': campaign,
            'progress': progress,
            'remaining': remaining,
            'invite_url': request.build_absolute_uri(),
            'app_link': f"tafakor://quran/khatm/{campaign.invite_code}",
        }
        return render(request, 'quran/khatm_preview.html', context)
