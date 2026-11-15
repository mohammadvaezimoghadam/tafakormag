from urllib.parse import urlsplit
from django.conf import settings
from django.http import HttpResponse
from django.http.response import HttpResponseRedirectBase
from django.utils.html import escape
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import PaymentTransaction
from .serializers import PaymentTransactionSerializer, PaymentVerifyInputSerializer
from .services import CallbackOutcome, PaymentService

DEFAULT_DEEP_LINK_SCHEMES = ("tafakorshop", "tafakor")


class SafePaymentRedirect(HttpResponseRedirectBase):
    """Redirect response permitting validated HTTP(S) URLs and allowlisted app deep links."""

    status_code = 302
    allowed_schemes = ["http", "https", *DEFAULT_DEEP_LINK_SCHEMES]


def _allowed_http_hosts(request) -> set[str]:
    """Build allowlist of trusted redirect hosts to prevent open-redirect vulnerabilities."""
    hosts: set[str] = {request.get_host().lower()}

    frontend_url = getattr(settings, "FRONTEND_BASE_URL", "")
    if frontend_url:
        parsed = urlsplit(frontend_url)
        if parsed.netloc:
            hosts.add(parsed.netloc.lower())

    for origin in getattr(settings, "CSRF_TRUSTED_ORIGINS", []):
        parsed = urlsplit(origin)
        if parsed.netloc and "*" not in parsed.netloc:
            hosts.add(parsed.netloc.lower())

    for allowed in getattr(settings, "ALLOWED_HOSTS", []):
        cleaned = allowed.strip().lower()
        if cleaned and cleaned != "*":
            hosts.add(cleaned)

    return hosts


def is_safe_redirect_url(url: str, request) -> bool:
    """Validate that a callback redirect target is relative, an allowlisted deep link, or a trusted host."""
    if not url:
        return False
    if url.startswith("/") and not url.startswith("//"):
        return True

    parsed = urlsplit(url)
    scheme = (parsed.scheme or "").lower()
    allowed_deep_links = set(
        getattr(settings, "ALLOWED_PAYMENT_REDIRECT_SCHEMES", DEFAULT_DEEP_LINK_SCHEMES)
    )
    if scheme in allowed_deep_links:
        return True

    if scheme in ("http", "https"):
        netloc = parsed.netloc.lower()
        hostname = (parsed.hostname or "").lower()
        if settings.DEBUG and hostname in ("localhost", "127.0.0.1"):
            return True
        trusted = _allowed_http_hosts(request)
        return netloc in trusted or hostname in trusted

    return False


def _render_callback_html(outcome: CallbackOutcome) -> HttpResponse:
    """Render a minimal Persian receipt page when no client redirect URL is registered."""
    trx = outcome.payment_trx
    title = "پرداخت موفق" if outcome.success else "پرداخت ناموفق"
    heading = "پرداخت با موفقیت انجام و تایید شد" if outcome.success else "پرداخت تکمیل نشد"
    accent = "#0f766e" if outcome.success else "#b91c1c"

    ref_code = escape((trx.ref_id or trx.tracking_code or trx.authority or "-") if trx else "-")
    amount_str = f"{trx.amount:,} تومان" if trx else "-"
    reason_str = escape(outcome.reason or (trx.failure_reason if trx else ""))

    details_html = (
        f"<p>کد پیگیری: <strong dir='ltr'>{ref_code}</strong></p>"
        f"<p>مبلغ: <strong>{escape(amount_str)}</strong></p>"
    )
    if not outcome.success and reason_str:
        details_html += f"<p>وضعیت: <span>{reason_str}</span></p>"

    html = f"""<!doctype html>
<html lang="fa" dir="rtl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)} | تفکر</title>
  <style>
    body {{ font-family: Tahoma, Arial, sans-serif; background: #f8fafc; color: #0f172a; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; padding: 16px; }}
    .card {{ background: #ffffff; border: 1px solid #e2e8f0; border-radius: 16px; padding: 24px; max-width: 420px; width: 100%; box-shadow: 0 10px 25px rgba(15, 23, 42, 0.06); }}
    h1 {{ font-size: 18px; margin: 0 0 12px; color: {accent}; }}
    p {{ font-size: 14px; margin: 8px 0; color: #334155; }}
    .hint {{ margin-top: 16px; font-size: 12px; color: #64748b; }}
  </style>
</head>
<body>
  <div class="card">
    <h1>{escape(heading)}</h1>
    {details_html}
    <p class="hint">می‌توانید این صفحه را ببندید و به برنامه بازگردید.</p>
  </div>
</body>
</html>"""
    return HttpResponse(html, content_type="text/html; charset=utf-8")


class PaymentCallbackView(APIView):
    """
    GET: Unified bank return handler resolving transaction verification, atomic
    domain settlement, and safe redirect or receipt response.
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        authority = request.query_params.get("Authority") or request.query_params.get("authority")
        status_param = request.query_params.get("Status") or request.query_params.get("status") or ""

        scheme = "https" if request.is_secure() else "http"
        host_base = f"{scheme}://{request.get_host()}"

        outcome = PaymentService.process_gateway_callback(
            authority=authority,
            status_param=status_param,
            host_base=host_base,
        )

        if outcome.redirect_url and is_safe_redirect_url(outcome.redirect_url, request):
            allowed_schemes = list(
                {"http", "https", *getattr(settings, "ALLOWED_PAYMENT_REDIRECT_SCHEMES", DEFAULT_DEEP_LINK_SCHEMES)}
            )
            SafePaymentRedirect.allowed_schemes = allowed_schemes
            return SafePaymentRedirect(outcome.redirect_url)

        accept_header = request.META.get("HTTP_ACCEPT", "")
        if "application/json" in accept_header and "text/html" not in accept_header:
            trx = outcome.payment_trx
            return Response(
                {
                    "success": outcome.success,
                    "status": outcome.status_label,
                    "reason": outcome.reason,
                    "authority": trx.authority if trx else authority,
                    "ref_id": trx.ref_id if trx else "",
                    "amount": trx.amount if trx else 0,
                    "purpose": trx.purpose if trx else "",
                    "reference_id": trx.reference_id if trx else "",
                },
                status=status.HTTP_200_OK if outcome.success else status.HTTP_400_BAD_REQUEST,
            )

        return _render_callback_html(outcome)


class PaymentVerifyView(APIView):
    """GET / POST: Programmatic verification & settlement endpoint across all domains."""

    permission_classes = [permissions.AllowAny]

    def _handle_verify(self, raw_data):
        normalized = {
            "authority": raw_data.get("authority") or raw_data.get("Authority") or "",
            "status": raw_data.get("status") or raw_data.get("Status") or "OK",
            "gateway_ref": (
                raw_data.get("gateway_ref")
                or raw_data.get("ref_id")
                or raw_data.get("RefID")
                or ""
            ),
            "tracking_code": raw_data.get("tracking_code") or "",
        }
        serializer = PaymentVerifyInputSerializer(data=normalized)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        trx, already_verified = PaymentService.verify_and_finalize(
            authority=data["authority"],
            status_param=data.get("status", "OK"),
            gateway_ref=data.get("gateway_ref") or None,
            tracking_code=data.get("tracking_code") or None,
        )

        return Response(
            {
                "success": True,
                "status": "success",
                "already_verified": already_verified,
                "transaction_id": str(trx.id),
                "purpose": trx.purpose,
                "reference_id": trx.reference_id,
                "authority": trx.authority,
                "ref_id": trx.ref_id,
                "tracking_code": trx.tracking_code,
                "amount": trx.amount,
                "settled_at": trx.settled_at.isoformat() if trx.settled_at else None,
            },
            status=status.HTTP_200_OK,
        )

    def get(self, request):
        return self._handle_verify(request.query_params)

    def post(self, request):
        return self._handle_verify(request.data)


class PaymentTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """Authenticated user's centralized payment transaction history."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PaymentTransactionSerializer

    def get_queryset(self):
        return (
            PaymentTransaction.objects.filter(user=self.request.user)
            .select_related("user")
            .order_by("-created_at")
        )

