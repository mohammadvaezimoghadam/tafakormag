from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class GatewayInitResult:
    """Normalized result returned after initiating a gateway payment session."""

    success: bool
    authority: str | None = None
    gateway_url: str | None = None
    error_message: str | None = None
    raw_response: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GatewayVerifyResult:
    """Normalized result returned after verifying a gateway payment transaction."""

    success: bool
    ref_id: str | None = None
    card_pan: str | None = None
    fee: int | None = None
    already_verified: bool = False
    error_message: str | None = None
    raw_response: dict[str, Any] = field(default_factory=dict)


class BasePaymentGateway(ABC):
    """Abstract interface implemented by every payment gateway driver."""

    name: str

    @abstractmethod
    def request_payment(
        self,
        *,
        amount_tomans: int,
        description: str,
        callback_url: str,
        mobile: str | None = None,
        email: str | None = None,
    ) -> GatewayInitResult:
        """Initiate a new transaction on the remote payment gateway."""

    @abstractmethod
    def verify_payment(
        self,
        *,
        authority: str,
        amount_tomans: int,
    ) -> GatewayVerifyResult:
        """Verify an existing transaction authority against the remote payment gateway."""

