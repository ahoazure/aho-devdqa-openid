from rest_framework import permissions
from rest_framework.permissions import (DjangoModelPermissions)


class CustomDjangoModelPermissions(DjangoModelPermissions):
    message = "Sorry! You have no permission to edit or create new record(s)"
    def __init__(self):
        self.perms_map['GET'] = ['%(app_label)s.view_%(model_name)s']


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Method for custom permission to allow owner of an object to edit it.
    Enforced by return matching user attribute to the user making requests
    """
    def has_object_permission(self, request, view, obj):
        # SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS') allowed to any request.
        if request.method in permissions.SAFE_METHODS:
            return True # Read-only is granted to authenticated users
        return obj.user == request.user # CRUD permissions only to logged in owner


class BlocklistPermission(permissions.BasePermission):
    """
    Global permission check for blocked IP addresses.
    """
    def has_permission(self, request, view):
        ip_addr = request.META['REMOTE_ADDR']
        blocked = Blocklist.objects.filter(ip_addr=ip_addr).exists()
        return not blocked
