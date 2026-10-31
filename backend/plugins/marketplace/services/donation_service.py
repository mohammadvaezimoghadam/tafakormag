from typing import Optional
from django.db import transaction
from django.utils import timezone

from ..models.catalog import Item
from ..models.donation import DonationRequest, Donation
from ..models.location import Address
from ..models.interaction import DigitalAccess
from ..exceptions import (
    DonationError,
    ItemNotAvailableError,
    ItemNotDonationError,
    SelfDonationRequestError,
    DonationAlreadyRequestedError,
    UnauthorizedDonationActionError,
    InsufficientStockError,
    InvalidAddressError,
)


class DonationService:
    """
    Dedicated domain service orchestrating the peer-to-peer (C2C) book donation workflow:
    - Recipients submit motivation/need requests.
    - Donors review, accept or reject requests.
    - Automatic fulfillment for digital books and physical shipment tracking.
    """

    @classmethod
    @transaction.atomic
    def submit_request(cls, user, item_id: int, message: str = "") -> DonationRequest:
        """
        Submits a recipient's formal request for a donated book.
        - Enforces that the item is published as a DONATION.
        - Prevents donors from requesting their own books.
        - Enforces single pending request per recipient per item.
        """
        try:
            item = Item.objects.select_for_update().get(id=item_id)
        except Item.DoesNotExist:
            raise ItemNotAvailableError("کالای اهدایی مورد نظر یافت نشد.")

        if item.deal_type != Item.DealType.DONATION:
            raise ItemNotDonationError("این کتاب برای اهدای رایگان ثبت نشده است.")

        if item.status != Item.Status.AVAILABLE:
            raise ItemNotAvailableError("این کتاب اهدایی در حال حاضر در دسترس یا فعال نیست.")

        if item.seller_id == user.id:
            raise SelfDonationRequestError("شما نمی‌توانید برای کتاب اهدایی ثبت‌شده توسط خودتان درخواست ثبت کنید.")

        # Check existing active request
        existing_request = DonationRequest.objects.filter(
            item=item,
            requester=user,
            status__in=[DonationRequest.Status.PENDING, DonationRequest.Status.ACCEPTED]
        ).first()

        if existing_request:
            raise DonationAlreadyRequestedError("شما قبلاً برای دریافت این کتاب درخواست ثبت کرده‌اید.")

        return DonationRequest.objects.create(
            item=item,
            requester=user,
            message=message.strip(),
            status=DonationRequest.Status.PENDING,
        )

    @classmethod
    def cancel_request(cls, user, request_id: int) -> DonationRequest:
        """
        Allows prospective recipients to withdraw their pending donation request.
        """
        try:
            req = DonationRequest.objects.get(id=request_id, requester=user)
        except DonationRequest.DoesNotExist:
            raise DonationError("درخواست اهدایی مورد نظر یافت نشد.")

        if req.status != DonationRequest.Status.PENDING:
            raise DonationError("تنها درخواست‌های در انتظار تصمیم اهداکننده امکان انصراف دارند.")

        req.status = DonationRequest.Status.CANCELLED
        req.save(update_fields=["status"])
        return req

    @classmethod
    @transaction.atomic
    def accept_request(
        cls,
        donor_user,
        request_id: int,
        shipping_address_id: Optional[int] = None,
        shipping_payer: str = Donation.ShippingPayer.RECIPIENT
    ) -> Donation:
        """
        Donor accepts a recipient's request:
        - Locks item inventory and decrements stock.
        - Rejects other pending requests if item becomes out of stock.
        - Generates confirmed Donation record.
        - Instantly provisions DigitalAccess if it is a digital file.
        """
        try:
            req = (
                DonationRequest.objects.select_related("item", "requester")
                .select_for_update()
                .get(id=request_id)
            )
        except DonationRequest.DoesNotExist:
            raise DonationError("درخواست اهدایی مورد نظر یافت نشد.")

        item = req.item

        # Authorization: only the donor who listed the item can accept requests
        if item.seller_id != donor_user.id:
            raise UnauthorizedDonationActionError("تنها اهداکننده این کتاب مجاز به پذیرش درخواست است.")

        if req.status != DonationRequest.Status.PENDING:
            raise DonationError("این درخواست دیگر در وضعیت انتظار تصمیم نیست.")

        if not item.is_unlimited_stock and item.stock <= 0:
            raise InsufficientStockError("موجودی این کتاب اهدایی به پایان رسیده است.")

        # Handle shipping address if physical
        shipping_address = None
        if item.delivery_type == Item.DeliveryType.PHYSICAL:
            if shipping_address_id:
                try:
                    shipping_address = Address.objects.get(id=shipping_address_id, user=req.requester)
                except Address.DoesNotExist:
                    raise InvalidAddressError("آدرس پستی گیرنده نامعتبر است.")
            else:
                # Fallback to recipient's default address
                shipping_address = Address.objects.filter(user=req.requester, is_default=True).first()

        # 1. Update request status
        req.status = DonationRequest.Status.ACCEPTED
        req.save(update_fields=["status"])

        # 2. Create confirmed Donation record
        donation = Donation.objects.create(
            item=item,
            donor=donor_user,
            recipient=req.requester,
            donation_request=req,
            status=Donation.Status.ACCEPTED,
            shipping_address=shipping_address,
            shipping_payer=shipping_payer,
        )

        # 3. Decrement inventory
        if not item.is_unlimited_stock:
            item.stock = max(0, item.stock - 1)
            if item.stock == 0:
                item.status = Item.Status.COMPLETED
                # Auto-reject remaining pending requests since stock is depleted
                DonationRequest.objects.filter(
                    item=item,
                    status=DonationRequest.Status.PENDING
                ).exclude(id=req.id).update(status=DonationRequest.Status.REJECTED)
            item.save(update_fields=["stock", "status", "updated_at"])

        # 4. Immediate digital delivery
        if item.delivery_type == Item.DeliveryType.DIGITAL:
            DigitalAccess.objects.get_or_create(
                user=req.requester,
                item=item,
                donation=donation,
                defaults={
                    "granted_via": DigitalAccess.GrantedVia.DONATION,
                    "max_downloads": 10,
                }
            )

        return donation

    @classmethod
    def reject_request(cls, donor_user, request_id: int) -> DonationRequest:
        """
        Donor rejects a recipient's donation request.
        """
        try:
            req = DonationRequest.objects.select_related("item").get(id=request_id)
        except DonationRequest.DoesNotExist:
            raise DonationError("درخواست اهدایی مورد نظر یافت نشد.")

        if req.item.seller_id != donor_user.id:
            raise UnauthorizedDonationActionError("تنها اهداکننده این کتاب مجاز به رد درخواست است.")

        if req.status != DonationRequest.Status.PENDING:
            raise DonationError("این درخواست در وضعیت انتظار تصمیم نیست.")

        req.status = DonationRequest.Status.REJECTED
        req.save(update_fields=["status"])
        return req

    @classmethod
    def mark_as_shipped(cls, donor_user, donation_id: int, tracking_code: str) -> Donation:
        """
        Donor records postal dispatch and enters the tracking code.
        """
        try:
            donation = Donation.objects.get(id=donation_id, donor=donor_user)
        except Donation.DoesNotExist:
            raise DonationError("سند اهدای مورد نظر یافت نشد.")

        donation.status = Donation.Status.SHIPPED
        donation.tracking_code = tracking_code.strip()
        donation.shipped_at = timezone.now()
        donation.save(update_fields=["status", "tracking_code", "shipped_at"])
        return donation

    @classmethod
    def confirm_delivery(cls, recipient_user, donation_id: int) -> Donation:
        """
        Recipient acknowledges receipt of the donated book.
        """
        try:
            donation = Donation.objects.get(id=donation_id, recipient=recipient_user)
        except Donation.DoesNotExist:
            raise DonationError("سند اهدای مورد نظر یافت نشد.")

        donation.status = Donation.Status.DELIVERED
        donation.delivered_at = timezone.now()
        donation.save(update_fields=["status", "delivered_at"])
        return donation
