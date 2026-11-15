import logging
from django.db.models import Count, Q
from rest_framework import viewsets, permissions, status, parsers
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.notes.models import normalize_persian_text
from ..models.circulation import (
    BookTitle,
    BookStation,
    PhysicalCopy,
    Transfer,
    Badge,
    BadgeAward,
)
from ..services.circulation_service import CirculationService
from ..services.badge_service import BadgeService
from ..serializers.circulation import (
    BookTitleSerializer,
    BookTitleCreateInputSerializer,
    BookStationSerializer,
    PhysicalCopyListSerializer,
    PhysicalCopyDetailSerializer,
    RegisterPhysicalCopyInputSerializer,
    InitiateHandoverInputSerializer,
    ClaimCopyInputSerializer,
    ConfirmHandoverInputSerializer,
    StationDepositInputSerializer,
    StationPickupInputSerializer,
    TransferSerializer,
    BadgeSerializer,
    BadgeAwardSerializer,
)
from ..exceptions import MarketplaceError

logger = logging.getLogger(__name__)


class BookTitleViewSet(viewsets.ModelViewSet):
    """
    Catalog of book titles (شناسنامه عناوین کتاب).
    Supports searching by title, author, or ISBN with Persian normalization.
    """
    serializer_class = BookTitleSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve", "search"]:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        qs = BookTitle.objects.all().order_by("title")
        q = self.request.query_params.get("q", "").strip()
        category = self.request.query_params.get("category", "").strip()
        isbn = self.request.query_params.get("isbn", "").strip()

        if q:
            norm_q = normalize_persian_text(q)
            qs = qs.filter(
                Q(normalized_title__icontains=norm_q)
                | Q(normalized_author__icontains=norm_q)
                | Q(normalized_translator__icontains=norm_q)
                | Q(isbn__icontains=q)
            )
        if category:
            qs = qs.filter(category__iexact=category)
        if isbn:
            qs = qs.filter(isbn=isbn)

        return qs

    def create(self, request, *args, **kwargs):
        serializer = BookTitleCreateInputSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        try:
            title_obj = CirculationService.register_book_title(
                user=request.user,
                data=serializer.validated_data
            )
            return Response(BookTitleSerializer(title_obj).data, status=status.HTTP_201_CREATED)
        except MarketplaceError as e:
            return Response({"detail": e.message}, status=status.HTTP_400_BAD_REQUEST)


class BookStationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public kiosks and physical shelves (قفسه‌ها و ایستگاه‌های فیزیکی تفاخر).
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = BookStationSerializer

    def get_queryset(self):
        return BookStation.objects.filter(is_active=True).select_related(
            "city"
        ).annotate(
            current_books_count=Count("books_on_shelf", filter=Q(books_on_shelf__status=PhysicalCopy.Status.IN_STATION))
        ).order_by("city__name", "name")

    @action(detail=True, methods=["get"], url_path="books")
    def available_books(self, request, pk=None):
        """
        Lists all book copies currently physically present on this shelf/station.
        """
        station = self.get_object()
        copies = PhysicalCopy.objects.filter(
            station=station,
            status=PhysicalCopy.Status.IN_STATION
        ).select_related("book_title", "station").order_by("-updated_at")

        serializer = PhysicalCopyListSerializer(copies, many=True, context={"request": request})
        return Response(serializer.data)


class PhysicalCopyViewSet(viewsets.GenericViewSet):
    """
    Circulation Controller managing physical book copies and handovers.
    Strictly thin views delegating entirely to CirculationService.
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]

    def get_permissions(self):
        # Public actions: inspecting a QR code or viewing journey
        if self.action in ["inspect", "journey", "retrieve"]:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def retrieve(self, request, pk=None):
        """
        Resolves short_code from URL path /copies/{short_code}/, returning book status and allowed actions.
        """
        if not pk:
            return Response({"detail": "شناسه یا کد کتاب الزامی است."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = CirculationService.inspect_copy_by_code(user=request.user, raw_short_code=pk)
            copy = result["copy"]
            copy._active_transfer = result["active_transfer"]

            detail_data = PhysicalCopyDetailSerializer(copy, context={"request": request}).data
            detail_data["can_claim"] = result["can_claim"]
            detail_data["is_holder"] = result["is_holder"]
            detail_data["available_quantity"] = result["available_quantity"]
            if result["active_transfer"]:
                detail_data["active_transfer_status"] = result["active_transfer"].status
                detail_data["active_transfer_method"] = result["active_transfer"].method
                detail_data["active_transfer_id"] = result["active_transfer"].id
                detail_data["active_transfer_quantity"] = result["active_transfer"].quantity

            if result["is_holder"] and request.user and request.user.is_authenticated:
                from ..models.shelf import UserShelfBook
                shelf_book = UserShelfBook.objects.filter(user=request.user, book_title=copy.book_title).first()
                if shelf_book:
                    detail_data["shelf_id"] = shelf_book.id
                    detail_data["available_quantity"] = max(1, shelf_book.available_quantity)

            return Response(detail_data)
        except MarketplaceError as e:
            return Response({"detail": e.message}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=["post"], url_path="register")
    def register_copy(self, request):
        """
        Registers a new physical book into circulation with a generated short_code.
        """
        serializer = RegisterPhysicalCopyInputSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        try:
            copy = CirculationService.register_physical_copy(
                user=request.user,
                book_title_id=serializer.validated_data.get("book_title_id"),
                title=serializer.validated_data.get("title", ""),
                author=serializer.validated_data.get("author", ""),
                publisher=serializer.validated_data.get("publisher", ""),
                quantity=serializer.validated_data.get("quantity", 1),
                cover_image=serializer.validated_data.get("cover_image"),
                condition=serializer.validated_data["condition"],
                privacy=serializer.validated_data["privacy"]
            )
            return Response(PhysicalCopyDetailSerializer(copy, context={"request": request}).data, status=status.HTTP_201_CREATED)
        except MarketplaceError as e:
            return Response({"detail": e.message}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"], url_path="inspect")
    def inspect(self, request):
        """
        Resolves short_code or scanned QR URL, returning book status and allowed actions.
        """
        code = request.query_params.get("code")
        if not code:
            return Response({"detail": "شناسه یا کد کتاب الزامی است."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = CirculationService.inspect_copy_by_code(user=request.user, raw_short_code=code)
            copy = result["copy"]
            copy._active_transfer = result["active_transfer"]

            detail_data = PhysicalCopyDetailSerializer(copy, context={"request": request}).data
            detail_data["can_claim"] = result["can_claim"]
            detail_data["is_holder"] = result["is_holder"]
            detail_data["available_quantity"] = result["available_quantity"]
            if result["active_transfer"]:
                detail_data["active_transfer_status"] = result["active_transfer"].status
                detail_data["active_transfer_method"] = result["active_transfer"].method
                detail_data["active_transfer_id"] = result["active_transfer"].id
                detail_data["active_transfer_quantity"] = result["active_transfer"].quantity

            if result["is_holder"] and request.user and request.user.is_authenticated:
                from ..models.shelf import UserShelfBook
                shelf_book = UserShelfBook.objects.filter(user=request.user, book_title=copy.book_title).first()
                if shelf_book:
                    detail_data["shelf_id"] = shelf_book.id
                    detail_data["available_quantity"] = max(1, shelf_book.available_quantity)

            return Response(detail_data)
        except MarketplaceError as e:
            return Response({"detail": e.message}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=["get"], url_path="journey")
    def journey(self, request):
        """
        Returns the travel timeline (سفرنامه) of a physical book copy.
        """
        code = request.query_params.get("code")
        if not code:
            return Response({"detail": "شناسه کتاب الزامی است."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = CirculationService.get_copy_journey(raw_short_code=code)
            return Response({
                "short_code": result["copy"].short_code,
                "book_title": BookTitleSerializer(result["book_title"]).data,
                "total_transfers": result["total_transfers"],
                "journey": result["journey"],
            })
        except MarketplaceError as e:
            return Response({"detail": e.message}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=["get"], url_path="my-books")
    def my_held_books(self, request):
        """
        Lists books currently in the possession of the authenticated user.
        """
        copies = PhysicalCopy.objects.filter(
            current_holder=request.user,
            status__in=[PhysicalCopy.Status.ACTIVE, PhysicalCopy.Status.TRANSFERRING]
        ).select_related("book_title", "station").order_by("-updated_at")

        serializer = PhysicalCopyListSerializer(copies, many=True, context={"request": request})
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="my-donations")
    def my_original_donations(self, request):
        """
        Lists books initially introduced to the network by the authenticated user.
        """
        copies = PhysicalCopy.objects.filter(
            original_donor=request.user
        ).select_related("book_title", "station", "current_holder").order_by("-created_at")

        serializer = PhysicalCopyListSerializer(copies, many=True, context={"request": request})
        return Response(serializer.data)

    # ------------------------------------------------------------------
    # Handover Actions
    # ------------------------------------------------------------------
    @action(detail=False, methods=["get"], url_path="handover/incoming")
    def incoming_handovers(self, request):
        """
        Lists pending in-person book handovers assigned directly to the authenticated recipient.
        """
        transfers = CirculationService.list_incoming_handovers(request.user)
        return Response(TransferSerializer(transfers, many=True, context={"request": request}).data)

    @action(detail=False, methods=["post"], url_path="handover/initiate")
    def initiate_handover(self, request):
        """
        Donor starts in-person handover. Generates 4-digit OTP if method=otp_fallback.
        """
        serializer = InitiateHandoverInputSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        try:
            transfer, plain_otp = CirculationService.initiate_handover(
                donor_user=request.user,
                short_code=data["short_code"],
                recipient_phone=data.get("recipient_phone"),
                method=data.get("method"),
                quantity=data.get("quantity", 1),
                donor_note=data.get("donor_note", "")
            )
            resp_data = TransferSerializer(transfer).data
            if plain_otp:
                resp_data["otp_code"] = plain_otp
            return Response(resp_data, status=status.HTTP_201_CREATED)
        except MarketplaceError as e:
            return Response({"detail": e.message}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"], url_path="handover/claim")
    def claim_by_recipient(self, request):
        """
        Recipient scans the physical book and submits a claim request.
        """
        serializer = ClaimCopyInputSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        try:
            transfer = CirculationService.claim_by_recipient(
                recipient_user=request.user,
                short_code=data["short_code"],
                quantity=data.get("quantity", 1),
                recipient_note=data.get("recipient_note", "")
            )
            return Response(TransferSerializer(transfer).data, status=status.HTTP_200_OK)
        except MarketplaceError as e:
            return Response({"detail": e.message}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"], url_path="handover/(?P<transfer_id>[^/.]+)/confirm")
    def confirm_handover(self, request, transfer_id=None):
        """
        Confirms and finalizes handover atomically (donor tap or OTP verification).
        """
        serializer = ConfirmHandoverInputSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        try:
            transfer = CirculationService.confirm_handover(
                user=request.user,
                transfer_id=int(transfer_id),
                otp_code=data.get("otp_code"),
                quantity=data.get("quantity"),
                donor_note=data.get("donor_note", ""),
                recipient_note=data.get("recipient_note", "")
            )
            return Response(TransferSerializer(transfer).data, status=status.HTTP_200_OK)
        except MarketplaceError as e:
            return Response({"detail": e.message}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"], url_path="handover/(?P<transfer_id>[^/.]+)/cancel")
    def cancel_handover(self, request, transfer_id=None):
        """
        Cancels a pending handover.
        """
        try:
            transfer = CirculationService.cancel_handover(
                user=request.user,
                transfer_id=int(transfer_id)
            )
            return Response(TransferSerializer(transfer).data, status=status.HTTP_200_OK)
        except MarketplaceError as e:
            return Response({"detail": e.message}, status=status.HTTP_400_BAD_REQUEST)

    # ------------------------------------------------------------------
    # Station Kiosk Actions
    # ------------------------------------------------------------------
    @action(detail=False, methods=["post"], url_path="station/deposit")
    def deposit_to_station(self, request):
        """
        Deposits a held book into a physical kiosk.
        """
        serializer = StationDepositInputSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        try:
            copy, transfer = CirculationService.deposit_to_station(
                user=request.user,
                short_code=data["short_code"],
                station_id=data["station_id"],
                donor_note=data.get("donor_note", "")
            )
            return Response(TransferSerializer(transfer).data, status=status.HTTP_200_OK)
        except MarketplaceError as e:
            return Response({"detail": e.message}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"], url_path="station/pickup")
    def pickup_from_station(self, request):
        """
        Picks up a book from a physical kiosk.
        """
        serializer = StationPickupInputSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        try:
            copy, transfer = CirculationService.pickup_from_station(
                user=request.user,
                short_code=data["short_code"],
                recipient_note=data.get("recipient_note", "")
            )
            return Response(TransferSerializer(transfer).data, status=status.HTTP_200_OK)
        except MarketplaceError as e:
            return Response({"detail": e.message}, status=status.HTTP_400_BAD_REQUEST)

    # ------------------------------------------------------------------
    # Lifecycle Management
    # ------------------------------------------------------------------
    @action(detail=False, methods=["post"], url_path="(?P<short_code>[^/.]+)/report-lost")
    def report_lost(self, request, short_code=None):
        try:
            copy = CirculationService.report_lost(
                user=request.user,
                short_code=short_code,
                reason=request.data.get("reason", "")
            )
            return Response(PhysicalCopyDetailSerializer(copy, context={"request": request}).data)
        except MarketplaceError as e:
            return Response({"detail": e.message}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"], url_path="(?P<short_code>[^/.]+)/retire")
    def retire(self, request, short_code=None):
        try:
            copy = CirculationService.retire_copy(
                user=request.user,
                short_code=short_code,
                reason=request.data.get("reason", "")
            )
            return Response(PhysicalCopyDetailSerializer(copy, context={"request": request}).data)
        except MarketplaceError as e:
            return Response({"detail": e.message}, status=status.HTTP_400_BAD_REQUEST)


class BadgeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Gamification badges and user achievements.
    """
    serializer_class = BadgeSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        BadgeService.ensure_default_badges_exist()
        return Badge.objects.all().order_by("order", "threshold")

    @action(detail=False, methods=["get"], url_path="my-badges")
    def my_badges(self, request):
        awards = BadgeAward.objects.filter(
            user=request.user
        ).select_related("badge").order_by("-created_at")

        serializer = BadgeAwardSerializer(awards, many=True, context={"request": request})
        return Response(serializer.data)

