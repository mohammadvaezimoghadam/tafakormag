from rest_framework import viewsets, permissions
from ..models.location import Province, City, Address
from ..serializers.location import ProvinceSerializer, CitySerializer, AddressSerializer
from ..permissions import IsAddressOwner


class ProvinceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public API providing the list of provinces.
    """
    queryset = Province.objects.all().order_by("name")
    serializer_class = ProvinceSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None


class CityViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public API providing cities, optionally filtered by province ID.
    """
    serializer_class = CitySerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None

    def get_queryset(self):
        qs = City.objects.select_related("province").all().order_by("name")
        province_id = self.request.query_params.get("province_id")
        if province_id and province_id.isdigit():
            qs = qs.filter(province_id=int(province_id))
        return qs


class AddressViewSet(viewsets.ModelViewSet):
    """
    Customer address book API for checkout and delivery.
    """
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated, IsAddressOwner]

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user).select_related("city", "city__province").order_by("-is_default", "-created_at")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
