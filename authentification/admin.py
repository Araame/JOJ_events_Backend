from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from .models import Utilisateur

# Personnaliser l'affichage de l'admin pour Utilisateur
class UtilisateurAdmin(UserAdmin):
    list_display = ('username', 'email', 'is_staff', 'is_superuser', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'email')
    ordering = ('-date_joined',)
    
    fieldsets = UserAdmin.fieldsets + (
        ('Informations supplémentaires', {
            'fields': ('role', 'telephone'),
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informations supplémentaires', {
            'fields': ('role', 'telephone'),
        }),
    )

# Enregistrer le modèle Utilisateur
admin.site.register(Utilisateur, UtilisateurAdmin)

# Optionnel : Personnaliser l'affichage des groupes
admin.site.unregister(Group)
@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)