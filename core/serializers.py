# myapp/views.py
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Address
from .serializers import AddressSerializer


class AddressListCreateView(generics.ListCreateAPIView):
    """GET  → list all addresses of logged-in user
       POST → create new address (auto-set default if requested)"""
    permission_classes = [IsAuthenticated]
    serializer_class = AddressSerializer

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user).order_by('-is_default', 'created_at')

    def perform_create(self, serializer):
        # If "set as default" → unset all others
        if self.request.data.get('is_default'):
            Address.objects.filter(user=self.request.user).update(is_default=False)
        serializer.save(user=self.request.user)


class AddressDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/ PATCH/ DELETE a single address"""
    permission_classes = [IsAuthenticated]
    serializer_class = AddressSerializer
    lookup_field = 'slug'

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)

    def perform_update(self, serializer):
        # When changing default → unset others
        if serializer.validated_data.get('is_default'):
            Address.objects.filter(user=self.request.user).exclude(slug=self.kwargs['slug']).update(is_default=False)
        serializer.save()