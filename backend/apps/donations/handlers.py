from django.db import transaction

from apps.payments.handlers import append_query_params, register_payment_handler
from apps.payments.models import PaymentTransaction


def handle_donation_payment_settlement(payment_trx: PaymentTransaction) -> None:
    """
    Domain settlement handler executed inside PaymentService after bank verification
    to mark the DonationTransaction successful and increment DonationCampaign metrics.
    """
    from .models import DonationTransaction
    from .services import verify_and_settle_transaction

    with transaction.atomic():
        donation_trx = (
            DonationTransaction.objects.select_for_update()
            .filter(payment_transaction=payment_trx)
            .first()
        )
        if donation_trx is None and payment_trx.authority:
            donation_trx = (
                DonationTransaction.objects.select_for_update()
                .filter(authority=payment_trx.authority)
                .first()
            )
            if donation_trx is not None and donation_trx.payment_transaction_id is None:
                donation_trx.payment_transaction = payment_trx
                DonationTransaction.objects.filter(pk=donation_trx.pk).update(
                    payment_transaction=payment_trx
                )

    if donation_trx is None:
        return

    verify_and_settle_transaction(
        authority=donation_trx.authority,
        gateway_ref=payment_trx.ref_id or None,
        tracking_code=payment_trx.tracking_code or payment_trx.ref_id or None,
    )


def resolve_donation_redirect_url(
    payment_trx: PaymentTransaction,
    status_label: str,
    reason: str,
    host_base: str,
) -> str:
    """Resolve browser redirect target for donation campaign payment callbacks."""
    campaign_id = payment_trx.metadata.get("campaign_id") or payment_trx.reference_id
    params = {
        "payment": status_label,
        "authority": payment_trx.authority or "",
        "campaign_id": str(campaign_id or ""),
    }
    if status_label == "success":
        params["ref_id"] = payment_trx.ref_id or payment_trx.tracking_code or payment_trx.authority
        params["amount"] = str(payment_trx.amount)
    elif reason:
        params["reason"] = reason

    return append_query_params(f"{host_base}/donate", params)


def register_donation_payment_handlers() -> None:
    """Bind centralized donation payment purpose to its settlement and redirect handlers."""
    register_payment_handler(
        purpose=PaymentTransaction.Purpose.DONATION,
        handler=handle_donation_payment_settlement,
        redirect_resolver=resolve_donation_redirect_url,
    )

