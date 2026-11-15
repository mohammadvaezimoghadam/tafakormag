import logging
from typing import Any
import requests
from django.conf import settings

from .base import BasePaymentGateway, GatewayInitResult, GatewayVerifyResult

logger = logging.getLogger(__name__)


class ZarinPalGateway(BasePaymentGateway):
    """ZarinPal REST API v4 payment gateway implementation (Sandbox & Production)."""

    name = "zarinpal"
    REQUEST_TIMEOUT_SECONDS = 15
    SANDBOX_BASE_URL = "https://sandbox.zarinpal.com/pg"
    PRODUCTION_BASE_URL = "https://payment.zarinpal.com/pg"

    @classmethod
    def get_base_url(cls) -> str:
        """Return Sandbox or Production ZarinPal base URL based on settings."""
        if getattr(settings, "ZARINPAL_SANDBOX", True):
            return cls.SANDBOX_BASE_URL
        return cls.PRODUCTION_BASE_URL

    @classmethod
    def get_merchant_id(cls) -> str:
        """Return configured ZarinPal Merchant ID."""
        return getattr(settings, "ZARINPAL_MERCHANT_ID", "00000000-0000-0000-0000-000000000000")

    @staticmethod
    def _extract_error_message(res_data: dict[str, Any], fallback: str) -> str:
        """Extract a human-readable error string from a ZarinPal API v4 payload."""
        errors = res_data.get("errors")
        data = res_data.get("data")

        if isinstance(errors, dict) and errors.get("message"):
            return str(errors["message"])
        if isinstance(errors, list) and errors:
            first = errors[0]
            if isinstance(first, dict) and first.get("message"):
                return str(first["message"])
            return str(first)
        if isinstance(errors, str) and errors:
            return errors
        if isinstance(data, dict) and data.get("message"):
            return str(data["message"])
        return fallback

    def _post_json(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Execute JSON POST call to ZarinPal with uniform timeout and headers."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        response = requests.post(
            endpoint,
            json=payload,
            headers=headers,
            timeout=self.REQUEST_TIMEOUT_SECONDS,
        )
        return response.json()

    def request_payment(
        self,
        *,
        amount_tomans: int,
        description: str,
        callback_url: str,
        mobile: str | None = None,
        email: str | None = None,
    ) -> GatewayInitResult:
        """Send a payment request to ZarinPal and return an Authority and StartPay URL."""
        base_url = self.get_base_url()
        endpoint = f"{base_url}/v4/payment/request.json"

        metadata: dict[str, str] = {}
        if mobile:
            metadata["mobile"] = str(mobile)
        if email:
            metadata["email"] = str(email)

        payload = {
            "merchant_id": self.get_merchant_id(),
            "amount": int(amount_tomans),
            "currency": "IRT",
            "description": (description or "پرداخت در پلتفرم تفکر")[:255],
            "callback_url": callback_url,
            "metadata": metadata,
        }

        try:
            res_data = self._post_json(endpoint, payload)
        except Exception as exc:
            logger.exception("Exception requesting payment from ZarinPal: %s", exc)
            return GatewayInitResult(
                success=False,
                error_message=f"خطای ارتباط با درگاه پرداخت: {exc}",
            )

        data = res_data.get("data")
        if isinstance(data, dict) and data.get("code") == 100 and data.get("authority"):
            authority = str(data["authority"])
            return GatewayInitResult(
                success=True,
                authority=authority,
                gateway_url=f"{base_url}/StartPay/{authority}",
                raw_response=res_data,
            )

        err_msg = self._extract_error_message(res_data, "خطا در برقراری ارتباط با درگاه زرین‌پال")
        logger.error("ZarinPal request failed: %s", res_data)
        return GatewayInitResult(
            success=False,
            error_message=err_msg,
            raw_response=res_data if isinstance(res_data, dict) else {},
        )

    def verify_payment(
        self,
        *,
        authority: str,
        amount_tomans: int,
    ) -> GatewayVerifyResult:
        """Verify an Authority against ZarinPal and return normalized settlement proof."""
        base_url = self.get_base_url()
        endpoint = f"{base_url}/v4/payment/verify.json"

        payload = {
            "merchant_id": self.get_merchant_id(),
            "amount": int(amount_tomans),
            "authority": authority,
        }

        try:
            res_data = self._post_json(endpoint, payload)
        except Exception as exc:
            logger.exception("Exception verifying payment with ZarinPal: %s", exc)
            return GatewayVerifyResult(
                success=False,
                error_message=f"خطای شبکه در تایید پرداخت: {exc}",
            )

        data = res_data.get("data")
        code = data.get("code") if isinstance(data, dict) else None

        # Code 100: First-time verification success; Code 101: Already verified by ZarinPal
        if code in (100, 101):
            raw_ref = data.get("ref_id")
            return GatewayVerifyResult(
                success=True,
                ref_id=str(raw_ref) if raw_ref is not None else "",
                card_pan=str(data.get("card_pan") or ""),
                fee=int(data["fee"]) if data.get("fee") is not None else None,
                already_verified=(code == 101),
                raw_response=res_data,
            )

        err_msg = self._extract_error_message(res_data, "تایید پرداخت در زرین‌پال ناموفق بود.")
        logger.warning("ZarinPal verify failed for authority=%s: %s", authority, res_data)
        return GatewayVerifyResult(
            success=False,
            error_message=err_msg,
            raw_response=res_data if isinstance(res_data, dict) else {},
        )

