import logging
from decimal import Decimal
from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)

from apps.payments.handlers import register_payment_handler
from apps.payments.models import PaymentTransaction


def handle_marketplace_order_payment(payment_trx: PaymentTransaction) -> None:
    """
    Domain settlement handler executed inside PaymentService after bank verification
    for marketplace orders. Updates mirror Payment row and fulfills the Order atomically.
    """
    from .models.order import Order
    from .models.payment import Payment
    from .services.order_service import OrderService

    order_id = int(payment_trx.reference_id)
    with transaction.atomic():
        order = Order.objects.select_for_update().get(pk=order_id)

        mkt_payment = (
            Payment.objects.select_for_update()
            .filter(payment_transaction=payment_trx)
            .first()
        )
        if mkt_payment is None and payment_trx.authority:
            mkt_payment = (
                Payment.objects.select_for_update()
                .filter(authority=payment_trx.authority)
                .first()
            )

        ref_code = payment_trx.ref_id or payment_trx.tracking_code or ""
        paid_at = payment_trx.verified_at or timezone.now()

        if mkt_payment is None:
            Payment.objects.create(
                order=order,
                payment_transaction=payment_trx,
                amount=Decimal(payment_trx.amount),
                gateway=payment_trx.gateway,
                authority=payment_trx.authority,
                tracking_code=ref_code,
                status=Payment.Status.SUCCESSFUL,
                paid_at=paid_at,
                raw_response=payment_trx.raw_verify_response or {},
            )
        else:
            mkt_payment.payment_transaction = payment_trx
            mkt_payment.tracking_code = ref_code
            mkt_payment.status = Payment.Status.SUCCESSFUL
            mkt_payment.paid_at = paid_at
            if payment_trx.raw_verify_response:
                mkt_payment.raw_response = payment_trx.raw_verify_response
            mkt_payment.save(
                update_fields=[
                    "payment_transaction",
                    "tracking_code",
                    "status",
                    "paid_at",
                    "raw_response",
                ]
            )

        OrderService.confirm_payment_success(order, payment_reference=ref_code)


def register_marketplace_payment_handlers() -> None:
    """Bind centralized marketplace_order payment purpose to order fulfillment."""
    register_payment_handler(
        purpose=PaymentTransaction.Purpose.MARKETPLACE_ORDER,
        handler=handle_marketplace_order_payment,
    )


def link_pending_gifts_on_user_save(sender, instance, created, **kwargs) -> None:
    """
    Automatically claims pending book transfers to newly registered or phone-updated users.
    Ensures that when a recipient signs up, their gifted books appear in their account immediately
    with is_gift=True and status=CONFIRMED.
    """
    phone = getattr(instance, "phone", None) or getattr(instance, "username", None)
    if not phone:
        return
    from .services.shelf_service import ShelfService

    try:
        ShelfService.claim_pending_gifts_for_user(instance)
    except Exception as e:
        logger.exception("Error auto-claiming pending gifts on user save: %s", e)


