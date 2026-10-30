from django.contrib import admin
from django.utils import timezone
from .models.location import Province, City, Address
from .models.finance import SellerBankAccount
from .models.catalog import Category, Item, ItemImage, BookDetail, ItemAttribute
from .models.cart import Cart, CartItem
from .models.discount import Coupon, CouponUsage
from .models.order import Order, OrderShipment, OrderItem, OrderStatusHistory, ShipmentStatusHistory
from .models.payment import Payment, SellerSettlement
from .models.donation import DonationRequest, Donation
from .models.interaction import Review, Wishlist, DigitalAccess


# ==============================================================================
# 1. Locations & Addresses
# ==============================================================================

@admin.register(Province)
class ProvinceAdmin(admin.ModelAdmin):
    list_display = ["id", "name"]
    search_fields = ["name"]


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "province"]
    list_filter = ["province"]
    search_fields = ["name", "province__name"]
    autocomplete_fields = ["province"]


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ["receiver_name", "user", "city", "receiver_phone", "postal_code", "is_default", "created_at"]
    list_filter = ["is_default", "city__province"]
    search_fields = ["receiver_name", "receiver_phone", "postal_code", "user__phone"]
    autocomplete_fields = ["user", "city"]


# ==============================================================================
# 2. Catalog & Products
# ==============================================================================

class BookDetailInline(admin.StackedInline):
    model = BookDetail
    can_delete = False
    extra = 0
    verbose_name = "Book Detail"
    verbose_name_plural = "Book Details"


class ItemImageInline(admin.TabularInline):
    model = ItemImage
    extra = 1
    fields = ["image", "alt_text", "is_cover", "order"]


class ItemAttributeInline(admin.TabularInline):
    model = ItemAttribute
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "parent", "is_active", "order"]
    list_filter = ["is_active"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    inlines = [BookDetailInline, ItemImageInline, ItemAttributeInline]
    list_display = [
        "title",
        "seller",
        "category",
        "deal_type",
        "delivery_type",
        "price",
        "discount_price",
        "stock",
        "status",
        "is_deleted",
        "is_featured",
        "created_at",
    ]
    list_filter = [
        "status",
        "deal_type",
        "delivery_type",
        "is_featured",
        "category",
        "created_at",
    ]
    search_fields = [
        "title",
        "slug",
        "description",
        "seller__phone",
        "book_detail__author",
        "book_detail__publisher",
        "book_detail__isbn",
    ]
    autocomplete_fields = ["seller", "category", "city"]
    actions = ["restore_deleted_items", "mark_as_available", "mark_as_featured"]

    def get_queryset(self, request):
        # Admins should be able to view soft-deleted records as well
        return Item.all_objects.all().select_related("seller", "category", "book_detail")

    @admin.action(description="Restore selected soft-deleted items")
    def restore_deleted_items(self, request, queryset):
        restored_count = 0
        for item in queryset:
            if item.is_deleted:
                item.restore()
                restored_count += 1
        self.message_user(request, f"{restored_count} item(s) restored successfully.")

    @admin.action(description="Mark selected items as available")
    def mark_as_available(self, request, queryset):
        queryset.update(status=Item.Status.AVAILABLE)

    @admin.action(description="Mark selected items as featured")
    def mark_as_featured(self, request, queryset):
        queryset.update(is_featured=True)



# ==============================================================================
# 3. Orders & Multi-Vendor Shipments
# ==============================================================================

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ["item", "quantity", "unit_price", "discount_amount"]


class OrderShipmentInline(admin.TabularInline):
    model = OrderShipment
    extra = 0
    fields = ["seller", "shipping_method", "tracking_code", "shipping_cost", "status", "shipped_at", "delivered_at"]


class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ["from_status", "to_status", "changed_by", "note", "created_at"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    inlines = [OrderShipmentInline, OrderItemInline, OrderStatusHistoryInline]
    list_display = [
        "order_number",
        "buyer",
        "status",
        "payment_status",
        "total_items_amount",
        "discount_amount",
        "payable_amount",
        "created_at",
    ]
    list_filter = ["status", "payment_status", "created_at"]
    search_fields = ["order_number", "buyer__phone"]
    readonly_fields = [
        "order_number",
        "total_items_amount",
        "total_shipping_cost",
        "discount_amount",
        "payable_amount",
        "created_at",
        "updated_at",
    ]


@admin.register(OrderShipment)
class OrderShipmentAdmin(admin.ModelAdmin):
    inlines = [OrderItemInline]
    list_display = [
        "id",
        "order",
        "seller",
        "shipping_method",
        "tracking_code",
        "status",
        "shipped_at",
        "delivered_at",
    ]
    list_filter = ["status", "shipping_method", "created_at"]
    search_fields = ["order__order_number", "tracking_code", "seller__phone"]
    autocomplete_fields = ["seller"]


# ==============================================================================
# 4. Finance, Payments & Escrow Settlements
# ==============================================================================

@admin.register(SellerBankAccount)
class SellerBankAccountAdmin(admin.ModelAdmin):
    list_display = ["user", "bank_name", "account_holder_name", "iban", "is_verified", "is_default", "created_at"]
    list_filter = ["is_verified", "bank_name", "created_at"]
    search_fields = ["iban", "user__phone", "account_holder_name"]
    autocomplete_fields = ["user"]
    actions = ["verify_accounts", "unverify_accounts"]

    @admin.action(description="Verify selected bank accounts")
    def verify_accounts(self, request, queryset):
        queryset.update(is_verified=True)
        self.message_user(request, "Selected bank accounts verified successfully.")

    @admin.action(description="Unverify selected bank accounts")
    def unverify_accounts(self, request, queryset):
        queryset.update(is_verified=False)


@admin.register(SellerSettlement)
class SellerSettlementAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "seller",
        "shipment",
        "gross_amount",
        "platform_fee",
        "net_amount",
        "status",
        "settled_at",
        "created_at",
    ]
    list_filter = ["status", "created_at"]
    search_fields = ["seller__phone", "shipment__order__order_number"]
    actions = ["approve_settlement", "mark_as_settled"]

    @admin.action(description="Approve selected settlements for payment")
    def approve_settlement(self, request, queryset):
        queryset.update(status=SellerSettlement.Status.APPROVED)

    @admin.action(description="Mark selected settlements as settled")
    def mark_as_settled(self, request, queryset):
        queryset.update(status=SellerSettlement.Status.SETTLED, settled_at=timezone.now())


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "order",
        "amount",
        "gateway",
        "authority",
        "tracking_code",
        "status",
        "paid_at",
        "created_at",
    ]
    list_filter = ["status", "gateway", "created_at"]
    search_fields = ["authority", "tracking_code", "order__order_number"]
    readonly_fields = ["raw_response", "paid_at", "created_at"]


# ==============================================================================
# 5. Coupons & Discounts
# ==============================================================================

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = [
        "code",
        "title",
        "discount_type",
        "discount_value",
        "used_count",
        "usage_limit",
        "valid_from",
        "valid_until",
        "is_active",
    ]
    list_filter = ["discount_type", "is_active", "discount_bearer"]
    search_fields = ["code", "title"]


@admin.register(CouponUsage)
class CouponUsageAdmin(admin.ModelAdmin):
    list_display = ["coupon", "user", "order", "discount_applied", "created_at"]
    search_fields = ["coupon__code", "user__phone", "order__order_number"]
    readonly_fields = ["created_at"]


# ==============================================================================
# 6. Book Charity & Donations
# ==============================================================================

@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "item",
        "donor",
        "recipient",
        "status",
        "shipping_payer",
        "tracking_code",
        "accepted_at",
        "shipped_at",
        "delivered_at",
    ]
    list_filter = ["status", "shipping_payer", "accepted_at"]
    search_fields = ["item__title", "donor__phone", "recipient__phone", "tracking_code"]


@admin.register(DonationRequest)
class DonationRequestAdmin(admin.ModelAdmin):
    list_display = ["id", "item", "requester", "status", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["item__title", "requester__phone", "message"]


# ==============================================================================
# 7. Interactions & Digital Library
# ==============================================================================

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["item", "reviewer", "rating", "created_at"]
    list_filter = ["rating", "created_at"]
    search_fields = ["item__title", "reviewer__phone", "comment"]


@admin.register(DigitalAccess)
class DigitalAccessAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "item",
        "granted_via",
        "download_count",
        "max_downloads",
        "expires_at",
        "last_downloaded_at",
    ]
    list_filter = ["granted_via", "created_at"]
    search_fields = ["user__phone", "item__title"]
