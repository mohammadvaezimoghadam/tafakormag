from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .exceptions import PaymentHandlerMissingError
from .models import PaymentTransaction

DomainHandlerFn = Callable[[PaymentTransaction], Any]
RedirectResolverFn = Callable[[PaymentTransaction, str, str, str], Optional[str]]


@dataclass(frozen=True)
class RegisteredDomainSpec:
    """Explicit domain callback & redirect specification registered per payment purpose."""

    handler: DomainHandlerFn
    redirect_resolver: Optional[RedirectResolverFn] = None


_DOMAIN_REGISTRY: Dict[str, RegisteredDomainSpec] = {}


def register_payment_handler(
    purpose: str,
    handler: DomainHandlerFn,
    redirect_resolver: Optional[RedirectResolverFn] = None,
) -> None:
    """
    Explicitly bind a payment purpose (e.g. 'donation', 'marketplace_order') to its
    atomic settlement handler and optional client redirect URL builder.
    """
    _DOMAIN_REGISTRY[str(purpose)] = RegisteredDomainSpec(
        handler=handler,
        redirect_resolver=redirect_resolver,
    )


def get_payment_handler(purpose: str) -> DomainHandlerFn:
    """Return the registered domain fulfillment handler for a payment purpose."""
    spec = _DOMAIN_REGISTRY.get(str(purpose))
    if spec is None:
        raise PaymentHandlerMissingError(
            f"پردازشگر تکمیل برای نوع پرداخت «{purpose}» ثبت نشده است."
        )
    return spec.handler


def append_query_params(base_url: str, params: dict[str, Any]) -> str:
    """Safely append query parameters onto an HTTP URL or custom mobile deep link."""
    parts = urlsplit(base_url)
    existing_params = dict(parse_qsl(parts.query, keep_blank_values=True))
    cleaned_new = {k: str(v) for k, v in params.items() if v is not None and str(v) != ""}
    existing_params.update(cleaned_new)
    return urlunsplit((
        parts.scheme,
        parts.netloc,
        parts.path,
        urlencode(existing_params),
        parts.fragment,
    ))


def resolve_client_redirect_url(
    payment_trx: PaymentTransaction,
    *,
    status_label: str,
    reason: str = "",
    host_base: str = "",
) -> Optional[str]:
    """
    Resolve final browser/app redirect URL after gateway callback using explicit
    client_redirect_url first, then the domain's registered redirect_resolver.
    """
    base_params: dict[str, Any] = {
        "payment": status_label,
        "authority": payment_trx.authority or "",
        "purpose": payment_trx.purpose,
        "reference_id": payment_trx.reference_id,
        "amount": payment_trx.amount,
    }
    if status_label == "success":
        base_params["ref_id"] = payment_trx.ref_id or payment_trx.tracking_code or payment_trx.authority
    elif reason:
        base_params["reason"] = reason

    if payment_trx.client_redirect_url:
        return append_query_params(payment_trx.client_redirect_url, base_params)

    spec = _DOMAIN_REGISTRY.get(str(payment_trx.purpose))
    if spec and spec.redirect_resolver:
        return spec.redirect_resolver(payment_trx, status_label, reason, host_base)

    return None

