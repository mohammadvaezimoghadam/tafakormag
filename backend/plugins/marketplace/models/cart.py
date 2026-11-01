from django.db import models
from django.conf import settings
from .base import TimeStampedModel
from .catalog import Item


class Cart(TimeStampedModel):
    """
    User shopping cart. Exactly one persistent cart per user.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="marketplace_cart",
        verbose_name="کاربر"
    )

    class Meta:
        db_table = "marketplace_carts"
        verbose_name = "Cart"
        verbose_name_plural = "Carts"

    def __str__(self):
        return f"Cart for {self.user}"


class CartItem(TimeStampedModel):
    """
    Individual items placed within the shopping cart with specified quantities.
    """
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Cart"
    )
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name="cart_items",
        verbose_name="Item"
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name="Quantity")

    class Meta:
        db_table = "marketplace_cart_items"
        verbose_name = "Cart Item"
        verbose_name_plural = "Cart Items"
        constraints = [
            models.UniqueConstraint(fields=["cart", "item"], name="unique_cart_item")
        ]

    def __str__(self):
        return f"{self.quantity}x {self.item.title} in Cart #{self.cart_id}"
