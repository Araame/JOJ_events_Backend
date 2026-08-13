from django.contrib import admin
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('objet', 'transaction', 'date', 'statut')
    list_filter = ('statut', 'date')
    search_fields = ('objet', 'contenu', 'spectateur__nom')