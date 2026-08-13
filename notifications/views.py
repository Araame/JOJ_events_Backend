from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import Notification, DestinataireType
from .serializers import NotificationSerializer


class IsSuperadminPersonnel(permissions.BasePermission):
    """Seul le superadmin peut consulter les notifications back-office."""

    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated and getattr(request.user, 'role', None) == 'SUPERADMIN')


class NotificationBackofficeViewSet(viewsets.ModelViewSet):
    """
    API de gestion des notifications back-office pour le superadmin.
    CRUD complet : le superadmin peut lister, lire, marquer comme lu,
    et supprimer les notifications.
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated, IsSuperadminPersonnel]

    def get_queryset(self):
        """Ne retourne que les notifications du personnel (back-office)."""
        return Notification.objects.filter(
            destinataire_type=DestinataireType.PERSONNEL,
            personnel=self.request.user
        )

    def perform_destroy(self, instance):
        """Suppression d'une notification."""
        instance.delete()

    @action(detail=True, methods=['post'], url_path='marquer-lu')
    def marquer_lu(self, request, pk=None):
        """Marquer une notification comme lue."""
        notification = self.get_object()
        notification.statut = 'LU'
        notification.save()
        return Response({'statut': notification.statut})

    @action(detail=False, methods=['post'], url_path='tout-marquer-lu')
    def tout_marquer_lu(self, request):
        """Marquer toutes les notifications comme lues."""
        updated = self.get_queryset().update(statut='LU')
        return Response({'notifications_mises_a_jour': updated})

    @action(detail=False, methods=['get'], url_path='non-lues')
    def non_lues(self, request):
        """Lister uniquement les notifications non lues."""
        notifications = self.get_queryset().filter(statut='NON_LU')
        serializer = self.get_serializer(notifications, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='compteur')
    def compteur(self, request):
        """Retourner le nombre de notifications non lues."""
        count = self.get_queryset().filter(statut='NON_LU').count()
        return Response({'non_lues': count})