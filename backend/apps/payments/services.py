import logging
import uuid
from dataclasses import dataclass
from typing import Any, Optional

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .exceptions import (
    GatewayRequestError,
    GatewayVerificationError,
    PaymentNotFoundError,
)
from .gateways import get_gateway
from .handlers import get_payment_handler, resolve_client_redirect_url
from .models import PaymentTransaction

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CallbackOutcome:
    """Outcome returned to callback HTTP view after processing bank return."""

    success: bool
    status_label: str
    reason: str
    payment_trx: Optional[PaymentTransaction]
    redirect_url: Optional[str]


class PaymentService:
    """
    Central payment orchestrator managing gateway requests, idempotent verification,
    durable bank-proof persistence, and atomic domain handler execution.
    """

    @staticmethod
    def resolve_default_callback_url() -> str:
        """Build default centralized gateway callback URL from BACKEND_BASE_URL."""
        backend_base = getattr(settings, "BACKEND_BASE_URL", "http://localhost:8000").rstrip("/")
        return f"{backend_base}/api/v1/payments/callback/"

    @classmethod
    def initiate_payment(
        cls,
        *,
        purpose: str,
        reference_id: str,
        amount_tomans: int,
        user=None,
        description: str = "",
        callback_url: str = "",
        client_redirect_url: str = "",
        gateway_name: str = PaymentTransaction.Gateway.ZARINPAL,
        mobile: str | None = None,
        email: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> tuple[PaymentTransaction, Optional[str]]:
        """
        Initiate a centralized payment transaction.
        - If amount_tomans <= 0: records a FREE transaction and fulfills domain handler immediately.
        - Otherwise: requests a token/Authority from the configured gateway and creates PENDING record.
        """
        normalized_amount = int(amount_tomans)
        if normalized_amount < 0:
            raise GatewayRequestError("مبلغ پرداخت نمی‌تواند منفی باشد.")

        effective_user = user if (user is not None and getattr(user, "is_authenticated", False)) else None
        extra_metadata = dict(metadata or {})

        # Zero-amount flow (e.g. free books or 100% coupon orders)
        if normalized_amount == 0:
            return cls._settle_free_transaction(
                purpose=purpose,
                reference_id=str(reference_id),
                user=effective_user,
                description=description,
                client_redirect_url=client_redirect_url,
                metadata=extra_metadata,
            )

        effective_callback = (callback_url or "").strip() or cls.resolve_default_callback_url()
        gateway = get_gateway(gateway_name)

        init_result = gateway.request_payment(
            amount_tomans=normalized_amount,
            description=description or "پرداخت در پلتفرم تفکر",
            callback_url=effective_callback,
            mobile=mobile,
            email=email,
        )

        if not init_result.success or not init_result.authority or not init_result.gateway_url:
            raise GatewayRequestError(
                init_result.error_message or "خطا در برقراری ارتباط با درگاه پرداخت."
            )

        payment_trx = PaymentTransaction.objects.create(
            user=effective_user,
            purpose=purpose,
            reference_id=str(reference_id),
            amount=normalized_amount,
            currency="IRT",
            gateway=gateway.name,
            authority=init_result.authority,
            status=PaymentTransaction.Status.PENDING,
            description=(description or "")[:255],
            callback_url=effective_callback[:500],
            client_redirect_url=(client_redirect_url or "")[:500],
            metadata=extra_metadata,
            raw_request=init_result.raw_response or {},
        )

        logger.info(
            "Payment initiated: trx=%s purpose=%s ref=%s amount=%s authority=%s",
            payment_trx.id,
            payment_trx.purpose,
            payment_trx.reference_id,
            payment_trx.amount,
            payment_trx.authority,
        )
        return payment_trx, init_result.gateway_url

    @classmethod
    def _settle_free_transaction(
        cls,
        *,
        purpose: str,
        reference_id: str,
        user,
        description: str,
        client_redirect_url: str,
        metadata: dict[str, Any],
    ) -> tuple[PaymentTransaction, None]:
        """Settle a zero-amount transaction immediately without contacting an external bank."""
        handler = get_payment_handler(purpose)
        authority = f"FREE-{uuid.uuid4().hex[:12].upper()}"
        ref_id = f"REF-FREE-{uuid.uuid4().hex[:8].upper()}"
        now = timezone.now()

        with transaction.atomic():
            payment_trx = PaymentTransaction.objects.create(
                user=user,
                purpose=purpose,
                reference_id=reference_id,
                amount=0,
                currency="IRT",
                gateway=PaymentTransaction.Gateway.FREE,
                authority=authority,
                ref_id=ref_id,
                tracking_code=ref_id,
                status=PaymentTransaction.Status.VERIFIED,
                description=(description or "تراکنش با مبلغ صفر تومان")[:255],
                client_redirect_url=(client_redirect_url or "")[:500],
                metadata=metadata,
                raw_verify_response={"message": "تراکنش با مبلغ صفر تومان بدون درگاه تایید شد."},
                verified_at=now,
            )
            handler(payment_trx)
            payment_trx.status = PaymentTransaction.Status.SUCCESSFUL
            payment_trx.settled_at = timezone.now()
            payment_trx.save(update_fields=["status", "settled_at", "updated_at"])

        return payment_trx, None

    @classmethod
    def verify_and_finalize(
        cls,
        *,
        authority: str,
        status_param: str = "OK",
        gateway_ref: str | None = None,
        tracking_code: str | None = None,
    ) -> tuple[PaymentTransaction, bool]:
        """
        Verify a payment authority with the gateway and execute its domain handler safely.
        - Idempotent: returns (trx, True) immediately if already SUCCESSFUL.
        - Durable bank proof: persists VERIFIED status and ref_id before running domain handler.
        """
        if not authority:
            raise GatewayVerificationError("شناسه تراکنش (Authority) ارسال نشده است.")

        try:
            payment_trx = PaymentTransaction.objects.get(authority=authority)
        except PaymentTransaction.DoesNotExist as exc:
            raise PaymentNotFoundError("تراکنش پرداخت مورد نظر یافت نشد.") from exc

        if payment_trx.status == PaymentTransaction.Status.SUCCESSFUL:
            return payment_trx, True

        # Handle user cancellation reported on callback return
        if (status_param or "").strip().upper() != "OK":
            cls._mark_cancelled_or_failed(
                payment_trx.id,
                status_value=PaymentTransaction.Status.CANCELLED,
                reason="انصراف کاربر در صفحه درگاه بانکی",
                raw_response={"Status": status_param},
            )
            raise GatewayVerificationError("تراکنش در درگاه بانکی توسط کاربر لغو گردید.")

        # Verify against external gateway ONLY if bank proof hasn't already been persisted
        if payment_trx.status != PaymentTransaction.Status.VERIFIED:
            cls._verify_with_gateway_and_record(
                payment_trx=payment_trx,
                preverified_ref=gateway_ref,
                preverified_tracking=tracking_code,
            )

        # Execute domain fulfillment handler in its own atomic block so bank proof survives rare domain errors
        return cls._run_domain_fulfillment(payment_trx.id)

    @classmethod
    def _mark_cancelled_or_failed(
        cls,
        trx_id,
        *,
        status_value: str,
        reason: str,
        raw_response: dict[str, Any] | None = None,
    ) -> None:
        with transaction.atomic():
            trx = PaymentTransaction.objects.select_for_update().get(pk=trx_id)
            if trx.status in (PaymentTransaction.Status.SUCCESSFUL, PaymentTransaction.Status.VERIFIED):
                return
            trx.status = status_value
            trx.failure_reason = reason
            if raw_response is not None:
                trx.raw_verify_response = raw_response
            trx.save(update_fields=["status", "failure_reason", "raw_verify_response", "updated_at"])

    @classmethod
    def _verify_with_gateway_and_record(
        cls,
        *,
        payment_trx: PaymentTransaction,
        preverified_ref: str | None = None,
        preverified_tracking: str | None = None,
    ) -> None:
        """Call remote gateway verify endpoint (outside DB lock) and commit VERIFIED proof."""
        if preverified_ref:
            ref_id = str(preverified_ref)
            card_pan = ""
            fee = None
            raw_data: dict[str, Any] = {"source": "explicit_ref", "ref_id": ref_id}
        else:
            gateway = get_gateway(payment_trx.gateway)
            verify_res = gateway.verify_payment(
                authority=payment_trx.authority or "",
                amount_tomans=int(payment_trx.amount),
            )
            if not verify_res.success:
                cls._mark_cancelled_or_failed(
                    payment_trx.id,
                    status_value=PaymentTransaction.Status.FAILED,
                    reason=verify_res.error_message or "اعتبارسنجی درگاه ناموفق بود.",
                    raw_response=verify_res.raw_response,
                )
                raise GatewayVerificationError(
                    verify_res.error_message or "تراکنش در درگاه بانکی تایید نشد."
                )

            ref_id = verify_res.ref_id or payment_trx.authority or ""
            card_pan = verify_res.card_pan or ""
            fee = verify_res.fee
            raw_data = verify_res.raw_response or {}

        with transaction.atomic():
            locked_trx = PaymentTransaction.objects.select_for_update().get(pk=payment_trx.id)
            if locked_trx.status in (PaymentTransaction.Status.SUCCESSFUL, PaymentTransaction.Status.VERIFIED):
                return
            locked_trx.status = PaymentTransaction.Status.VERIFIED
            locked_trx.ref_id = ref_id
            locked_trx.tracking_code = str(preverified_tracking or ref_id)
            locked_trx.card_pan = card_pan
            locked_trx.fee = fee
            locked_trx.raw_verify_response = raw_data
            locked_trx.verified_at = timezone.now()
            locked_trx.failure_reason = ""
            locked_trx.save(
                update_fields=[
                    "status",
                    "ref_id",
                    "tracking_code",
                    "card_pan",
                    "fee",
                    "raw_verify_response",
                    "verified_at",
                    "failure_reason",
                    "updated_at",
                ]
            )

    @classmethod
    def _run_domain_fulfillment(cls, trx_id) -> tuple[PaymentTransaction, bool]:
        """Run registered domain handler atomically and mark PaymentTransaction SUCCESSFUL."""
        try:
            with transaction.atomic():
                locked_trx = PaymentTransaction.objects.select_for_update().get(pk=trx_id)
                if locked_trx.status == PaymentTransaction.Status.SUCCESSFUL:
                    return locked_trx, True

                handler = get_payment_handler(locked_trx.purpose)
                handler(locked_trx)

                locked_trx.status = PaymentTransaction.Status.SUCCESSFUL
                locked_trx.settled_at = timezone.now()
                locked_trx.save(update_fields=["status", "settled_at", "updated_at"])
                return locked_trx, False
        except Exception as exc:
            # Record fulfillment failure outside rolled-back inner block while preserving VERIFIED bank proof
            PaymentTransaction.objects.filter(
                pk=trx_id,
                status=PaymentTransaction.Status.VERIFIED,
            ).update(failure_reason=str(exc))
            raise

    @classmethod
    def process_gateway_callback(
        cls,
        *,
        authority: str | None,
        status_param: str = "",
        host_base: str = "",
    ) -> CallbackOutcome:
        """
        Handle browser return from the payment gateway without raising HTTP errors on
        expected user cancellation or bank rejection, returning redirect or status data.
        """
        if not authority:
            return CallbackOutcome(
                success=False,
                status_label="failed",
                reason="missing_authority",
                payment_trx=None,
                redirect_url=f"{host_base}/donate?payment=failed&reason=missing_authority" if host_base else None,
            )

        try:
            trx = PaymentTransaction.objects.get(authority=authority)
        except PaymentTransaction.DoesNotExist:
            return CallbackOutcome(
                success=False,
                status_label="failed",
                reason="not_found",
                payment_trx=None,
                redirect_url=(
                    f"{host_base}/donate?payment=failed&authority={authority}&reason=not_found"
                    if host_base
                    else None
                ),
            )

        if trx.status == PaymentTransaction.Status.SUCCESSFUL:
            redirect_url = resolve_client_redirect_url(
                trx,
                status_label="success",
                host_base=host_base,
            )
            return CallbackOutcome(
                success=True,
                status_label="success",
                reason="",
                payment_trx=trx,
                redirect_url=redirect_url,
            )

        if (status_param or "").strip().upper() != "OK":
            cls._mark_cancelled_or_failed(
                trx.id,
                status_value=PaymentTransaction.Status.FAILED,
                reason="لغو پرداخت توسط کاربر در درگاه",
                raw_response={"Status": status_param},
            )
            trx.refresh_from_db()
            redirect_url = resolve_client_redirect_url(
                trx,
                status_label="failed",
                reason="canceled",
                host_base=host_base,
            )
            return CallbackOutcome(
                success=False,
                status_label="failed",
                reason="canceled",
                payment_trx=trx,
                redirect_url=redirect_url,
            )

        try:
            settled_trx, _ = cls.verify_and_finalize(authority=authority, status_param="OK")
            redirect_url = resolve_client_redirect_url(
                settled_trx,
                status_label="success",
                host_base=host_base,
            )
            return CallbackOutcome(
                success=True,
                status_label="success",
                reason="",
                payment_trx=settled_trx,
                redirect_url=redirect_url,
            )
        except Exception as exc:
            logger.warning("Callback verification failed for authority=%s: %s", authority, exc)
            trx.refresh_from_db()
            if trx.status == PaymentTransaction.Status.VERIFIED:
                # Bank took money but domain handler failed: persist failure_reason for support
                PaymentTransaction.objects.filter(pk=trx.pk).update(failure_reason=str(exc))
                trx.refresh_from_db()
                reason = "fulfillment_failed"
            else:
                reason = "verification_failed"

            redirect_url = resolve_client_redirect_url(
                trx,
                status_label="failed",
                reason=reason,
                host_base=host_base,
            )
            return CallbackOutcome(
                success=False,
                status_label="failed",
                reason=reason,
                payment_trx=trx,
                redirect_url=redirect_url,
            )
