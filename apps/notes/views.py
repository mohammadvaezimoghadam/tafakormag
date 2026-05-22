from django.db.models import Q
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Note, Channel
from .serializers import NoteSerializer, ChannelSerializer
from .services import create_bot_tasks


class NoteViewSet(viewsets.ModelViewSet):
    serializer_class = NoteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # فقط یادداشت‌های کاربر جاری
        return Note.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        note = serializer.save(user=self.request.user)
        create_bot_tasks(note, old_instance=None)

    def perform_update(self, serializer):
        old_note = self.get_object()
        note = serializer.save()
        create_bot_tasks(note, old_instance=old_note)

    def perform_destroy(self, instance):
        create_bot_tasks(instance, is_delete=True)
        instance.delete()

    @action(methods=['get'], detail=False, url_path='search')
    def search(self, request):
        query = request.query_params.get('q', '')
        if not query:
            return Response({"error": "پارامتر q الزامی است."}, status=status.HTTP_400_BAD_REQUEST)

        queryset = self.get_queryset().filter(
            Q(title__icontains=query) | Q(content__icontains=query)
        )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    


class ChannelViewSet(viewsets.ModelViewSet):
    queryset = Channel.objects.all()
    serializer_class = ChannelSerializer


    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated]
        return [permissions.AllowAny]
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.notes.exists():
            return Response(
                {"error": "این کانال یادداشت هایی دارد و قابل حذف نیست."}
            )
        return super().destroy(request, *args, **kwargs)
