from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission allowing read access to anyone,
    but restricting write access (PUT, PATCH, DELETE) exclusively to the object's owner/seller.
    """

    def has_object_permission(self, request, view, obj):
        # Read-only safe methods (GET, HEAD, OPTIONS) are allowed to all
        if request.method in permissions.SAFE_METHODS:
            return True

        # Check ownership based on common model patterns
        owner = getattr(obj, "seller", None) or getattr(obj, "user", None) or getattr(obj, "buyer", None)
        return owner == request.user


class IsAddressOwner(permissions.BasePermission):
    """
    Restricts address operations exclusively to the user who created the address.
    """

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class IsDonationParty(permissions.BasePermission):
    """
    Restricts access to donation records to either the donor or the recipient.
    """

    def has_object_permission(self, request, view, obj):
        return request.user in (obj.donor, obj.recipient)
