from django.db import models
from django.conf import settings


class SellerBankAccount(models.Model):
    """
    Seller IBAN and banking details for automated or manual Escrow settlements.
    Ensures safe payouts to verified bank accounts.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="seller_bank_accounts",
        verbose_name="فروشنده / کاربر"
    )
    bank_name = models.CharField(max_length=100, verbose_name="نام بانک (مثلاً ملت، ملی، پاسارگاد)")
    account_holder_name = models.CharField(max_length=150, verbose_name="نام و نام خانوادگی صاحب حساب")
    iban = models.CharField(
        max_length=34,
        unique=True,
        verbose_name="شماره شبا (IBAN بدون فاصله یا پیشوند)"
    )
    is_verified = models.BooleanField(
        default=False,
        verbose_name="وضعیت تایید حساب توسط ادمین / وب‌سرویس بانکی"
    )
    is_default = models.BooleanField(
        default=True,
        verbose_name="حساب پیش‌فرض واریز"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")

    class Meta:
        db_table = "marketplace_seller_bank_accounts"
        verbose_name = "Seller Bank Account"
        verbose_name_plural = "Seller Bank Accounts"
        ordering = ["-is_default", "-created_at"]
        indexes = [
            models.Index(fields=["user"], name="idx_seller_bank_user"),
            models.Index(fields=["iban"], name="idx_seller_bank_iban"),
        ]

    def __str__(self):
        return f"{self.bank_name} - {self.account_holder_name} ({self.iban})"
