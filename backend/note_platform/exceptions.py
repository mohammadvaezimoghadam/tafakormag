import logging
from django.http import Http404
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import (
    ValidationError,
    AuthenticationFailed,
    NotAuthenticated,
    PermissionDenied,
    NotFound,
    MethodNotAllowed,
)

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Unified Enterprise Exception Handler for Tafakor Platform.
    Produces a consistent, predictable JSON envelope across all endpoints:
    {
        "success": False,
        "error": "<Primary human-readable error message>",
        "code": "<MACHINE_READABLE_CODE>",
        "detail": "<Primary human-readable error message>",
        "details": <Full details or field dictionary>
    }
    """
    response = exception_handler(exc, context)

    if response is not None:
        primary_error = ""
        code = getattr(exc, 'default_code', 'ERROR')

        if isinstance(exc, ValidationError):
            code = "VALIDATION_ERROR"
            # Extract first human-readable message from dict or list
            if isinstance(response.data, dict):
                for field, errs in response.data.items():
                    if isinstance(errs, list) and errs:
                        first_err = str(errs[0])
                        primary_error = f"{field}: {first_err}" if field != 'non_field_errors' else first_err
                        break
                    elif isinstance(errs, str):
                        primary_error = f"{field}: {errs}" if field != 'non_field_errors' else errs
                        break
            elif isinstance(response.data, list) and response.data:
                primary_error = str(response.data[0])
        elif isinstance(exc, (AuthenticationFailed, NotAuthenticated)):
            code = "UNAUTHENTICATED"
            primary_error = "برای دسترسی به این بخش باید وارد حساب کاربری خود شوید."
        elif isinstance(exc, (PermissionDenied, DjangoPermissionDenied)):
            code = "PERMISSION_DENIED"
            primary_error = "شما اجازه دسترسی به این بخش یا انجام این عملیات را ندارید."
        elif isinstance(exc, (NotFound, Http404)):
            code = "NOT_FOUND"
            primary_error = "منبع مورد نظر یافت نشد."
        elif isinstance(exc, MethodNotAllowed):
            code = "METHOD_NOT_ALLOWED"
            primary_error = "متد درخواست مجاز نمی‌باشد."

        # Prioritize explicit error message if already set in response.data
        if isinstance(response.data, dict):
            if 'error' in response.data and isinstance(response.data['error'], str):
                primary_error = response.data['error']
            elif 'detail' in response.data and isinstance(response.data['detail'], str):
                primary_error = response.data['detail']

        if not primary_error:
            primary_error = "درخواست ارسال‌شده نامعتبر است."

        # Construct unified envelope
        envelope = {
            "success": False,
            "error": primary_error,
            "code": str(code).upper(),
            "detail": primary_error,
            "details": response.data,
        }

        response.data = envelope
        return response

    # Unhandled 500 server exception
    logger.exception(f"Unhandled server exception in API: {exc}", exc_info=exc)
    return Response(
        {
            "success": False,
            "error": "خطای غیرمنتظره‌ای در سرور رخ داده است. لطفاً بعداً تلاش فرمایید.",
            "code": "INTERNAL_SERVER_ERROR",
            "detail": "خطای غیرمنتظره‌ای در سرور رخ داده است.",
            "details": None,
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
