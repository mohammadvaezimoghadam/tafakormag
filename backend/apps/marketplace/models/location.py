from django.db import models
from django.conf import settings
from .base import MarketplaceBaseModel


class Province(models.Model):
    """
    Represents geographical provinces (e.g., Tehran, Isfahan, Fars).
    Used for shipping cost calculation and location-based filtering.
    """
    name = models.CharField(max_length=100, unique=True, verbose_name="نام استان")

    class Meta:
        db_table = "marketplace_provinces"
        verbose_name = "Province"
        verbose_name_plural = "Provinces"
        ordering = ["name"]

    def __str__(self):
        return self.name


class City(models.Model):
    """
    Represents cities belonging to a specific province.
    """
    province = models.ForeignKey(
        Province,
        on_delete=models.CASCADE,
        related_name="cities",
        verbose_name="Province"
    )
    name = models.CharField(max_length=100, verbose_name="City Name")

    class Meta:
        db_table = "marketplace_cities"
        verbose_name = "City"
        verbose_name_plural = "Cities"
        ordering = ["province", "name"]
        indexes = [
            models.Index(fields=["province"], name="idx_city_province"),
            models.Index(fields=["name"], name="idx_city_name"),
        ]

    def __str__(self):
        return f"{self.province.name} - {self.name}"


class Address(MarketplaceBaseModel):
    """
    Customer shipping addresses linked to the core User model.
    Supports soft-deletion and a single active default address per user.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="marketplace_addresses",
        verbose_name="User"
    )
    title = models.CharField(
        max_length=50,
        blank=True,
        default="",
        verbose_name="Address Title"
    )
    receiver_name = models.CharField(max_length=100, verbose_name="Receiver Name")
    receiver_phone = models.CharField(max_length=15, verbose_name="Receiver Phone")
    city = models.ForeignKey(
        City,
        on_delete=models.PROTECT,
        related_name="addresses",
        verbose_name="City"
    )
    postal_address = models.TextField(verbose_name="Postal Address")
    postal_code = models.CharField(max_length=10, verbose_name="Postal Code")
    is_default = models.BooleanField(default=False, verbose_name="Default Address")

    class Meta:
        db_table = "marketplace_addresses"
        verbose_name = "Address"
        verbose_name_plural = "Addresses"
        ordering = ["-is_default", "-created_at"]
        indexes = [
            models.Index(fields=["user"], name="idx_address_user"),
            models.Index(fields=["postal_code"], name="idx_address_postal_code"),
        ]

    def __str__(self):
        return f"{self.receiver_name} - {self.city.name} ({self.postal_code})"
