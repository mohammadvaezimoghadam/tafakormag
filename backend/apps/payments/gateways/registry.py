from typing import Dict
from ..exceptions import GatewayRequestError
from .base import BasePaymentGateway
from .zarinpal import ZarinPalGateway

_GATEWAY_REGISTRY: Dict[str, type[BasePaymentGateway]] = {
    ZarinPalGateway.name: ZarinPalGateway,
}


def register_gateway(name: str, gateway_cls: type[BasePaymentGateway]) -> None:
    """Register a gateway driver class by lowercase name."""
    _GATEWAY_REGISTRY[name.strip().lower()] = gateway_cls


def get_gateway(name: str = "zarinpal") -> BasePaymentGateway:
    """Instantiate a registered payment gateway driver by name."""
    normalized = (name or "zarinpal").strip().lower()
    gateway_cls = _GATEWAY_REGISTRY.get(normalized)
    if gateway_cls is None:
        raise GatewayRequestError(f"درگاه پرداخت «{name}» در سیستم پشتیبانی نمی‌شود.")
    return gateway_cls()

