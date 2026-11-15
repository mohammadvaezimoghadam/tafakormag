import logging
from typing import Any, Dict

from apps.payments.exceptions import (
    GatewayVerificationError,
    PaymentDomainError,
    PaymentNotFoundError,
)
from apps.payments.models import PaymentTransaction
from apps.payments.services import PaymentService as CentralPaymentService
from ..exceptions import (
    OrderCheckoutError,
    PaymentAlreadyCompletedError,
    PaymentError,
    PaymentVerificationFailedError,
)
from ..models.order import Order
from ..models.payment import Payment

logger = logging.getLogger(__name__)


class PaymentService:
    """
    Marketplace payment adapter delegating real gateway initiation and verification
    to centralized apps.payments.services.PaymentService while keeping marketplace APIs intact.
    """

    @classmethod
    def initiate_payment(
        cls,
        order: Order,
        callback_url: str = "",
        gateway: str = "zarinpal",
        client_redirect_url: str = "",
    ) -> Dict[str, Any]:
        """
        Initiate payment for a marketplace Order via centralized PaymentService:
        - Rejects already-paid or cancelled orders.
        - Handles zero-amount orders immediately via centralized FREE flow.
        - Requests a real gateway Authority (e.g. ZarinPal) for paid orders and records link.
        """
        if order.payment_status == Order.PaymentStatus.PAID:
            raise PaymentAlreadyCompletedError("این سفارش قبلاً پرداخت و تایید شده است.")

        if order.status == Order.Status.CANCELLED:
            raise OrderCheckoutError("امکان پرداخت برای سفارش لغوشده وجود ندارد.")

        payable_tomans = int(order.payable_amount)

        try:
            central_trx, gateway_url = CentralPaymentService.initiate_payment(
                purpose=PaymentTransaction.Purpose.MARKETPLACE_ORDER,
                reference_id=str(order.id),
                amount_tomans=payable_tomans,
                user=order.buyer,
                description=f"پرداخت سفارش #{order.order_number}",
                callback_url=callback_url,
                client_redirect_url=client_redirect_url,
                gateway_name=gateway,
                mobile=getattr(order.buyer, "phone", None),
                metadata={"order_number": order.order_number},
            )
        except PaymentDomainError as exc:
            raise PaymentError(exc.message) from exc

        if payable_tomans <= 0:
            mkt_payment = Payment.objects.filter(payment_transaction=central_trx).first()
            return {
                "is_free": True,
                "payment_url": None,
                "authority": central_trx.authority,
                "payment_id": mkt_payment.id if mkt_payment else None,
                "transaction_id": str(central_trx.id),
                "tracking_code": central_trx.tracking_code,
            }

        mkt_payment = Payment.objects.create(
            order=order,
            payment_transaction=central_trx,
            amount=order.payable_amount,
            gateway=central_trx.gateway,
            authority=central_trx.authority,
            status=Payment.Status.PENDING,
            raw_response=central_trx.raw_request or {},
        )

        return {
            "is_free": False,
            "payment_url": gateway_url,
            "authority": central_trx.authority,
            "payment_id": mkt_payment.id,
            "transaction_id": str(central_trx.id),
            "amount": order.payable_amount,
        }

    @classmethod
    def verify_payment(
        cls,
        authority: str,
        status_param: str = "OK",
    ) -> Dict[str, Any]:
        """
        Verify a marketplace payment through centralized PaymentService and map domain errors.
        """
        try:
            central_trx, already_verified = CentralPaymentService.verify_and_finalize(
                authority=authority,
                status_param=status_param,
            )
        except PaymentNotFoundError as exc:
            raise PaymentError(exc.message) from exc
        except GatewayVerificationError as exc:
            Payment.objects.filter(
                authority=authority,
                status=Payment.Status.PENDING,
            ).update(
                status=Payment.Status.FAILED,
                raw_response={"status": status_param, "reason": exc.message},
            )
            raise PaymentVerificationFailedError(exc.message) from exc
        except PaymentDomainError as exc:
            raise PaymentError(exc.message) from exc

        order_number = central_trx.metadata.get("order_number", "")
        if not order_number:
            order = Order.objects.filter(pk=central_trx.reference_id).only("order_number").first()
            order_number = order.order_number if order else ""

        return {
            "success": True,
            "order_number": order_number,
            "tracking_code": central_trx.tracking_code or central_trx.ref_id,
            "ref_id": central_trx.ref_id,
            "transaction_id": str(central_trx.id),
            "amount": central_trx.amount,
            "paid_at": central_trx.verified_at,
            "already_verified": already_verified,
        }
