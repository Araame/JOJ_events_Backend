# utilisateurs/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Personnel, Admin, Superadmin


@admin.register(Personnel)
class PersonnelAdmin(UserAdmin):
    """
    Administration complète du personnel JOJ.
    """
    list_display = (
        'get_username', 'get_email', 'get_prenom', 'get_nom',
        'get_role', 'get_tel', 'get_est_membre', 'get_date_inscription'
    )
    list_filter = ('role', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')

    fieldsets = UserAdmin.fieldsets + (
        ('Informations JOJ', {'fields': ('role', 'tel')}),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informations personnelles', {'fields': ('first_name', 'last_name', 'email')}),
        ('Informations JOJ', {'fields': ('role', 'tel')}),
    )

    
    def get_username(self, obj):
        return obj.username
    get_username.short_description = "Nom d'utilisateur"

    def get_email(self, obj):
        return obj.email
    get_email.short_description = "Adresse e-mail"

    def get_prenom(self, obj):
        return obj.first_name
    get_prenom.short_description = "Prénom"

    def get_nom(self, obj):
        return obj.last_name
    get_nom.short_description = "Nom"

    def get_role(self, obj):
        return obj.get_role_display()
    get_role.short_description = "Rôle"

    def get_tel(self, obj):
        return obj.tel or "—"
    get_tel.short_description = "Téléphone"

    def get_est_membre(self, obj):
        return "Oui" if obj.is_staff else "Non"
    get_est_membre.short_description = "Accès back-office"

    def get_date_inscription(self, obj):
        return obj.date_joined.strftime("%d/%m/%Y %H:%M")
    get_date_inscription.short_description = "Date d'inscription"


@admin.register(Admin)
class AdminProxyAdmin(UserAdmin):
    """
    Vue dédiée aux administrateurs (rôle limité).
    Affiche uniquement les utilisateurs avec le rôle ADMIN.
    """
    list_display = ('get_username', 'get_email', 'get_prenom', 'get_nom')

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informations personnelles', {'fields': ('first_name', 'last_name', 'email')}),
        ('Informations JOJ', {'fields': ('role', 'tel')}),
    )

    def get_username(self, obj):
        return obj.username
    get_username.short_description = "Nom d'utilisateur"

    def get_email(self, obj):
        return obj.email
    get_email.short_description = "Adresse e-mail"

    def get_prenom(self, obj):
        return obj.first_name
    get_prenom.short_description = "Prénom"

    def get_nom(self, obj):
        return obj.last_name
    get_nom.short_description = "Nom"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(role='ADMIN')


@admin.register(Superadmin)
class SuperadminProxyAdmin(UserAdmin):
    """
    Vue dédiée aux super-administrateurs (tous les pouvoirs).
    Affiche uniquement les utilisateurs avec le rôle SUPERADMIN.
    """
    list_display = ('get_username', 'get_email', 'get_prenom', 'get_nom')

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informations personnelles', {'fields': ('first_name', 'last_name', 'email')}),
        ('Informations JOJ', {'fields': ('tel',)}),
    )

    def get_username(self, obj):
        return obj.username
    get_username.short_description = "Nom d'utilisateur"

    def get_email(self, obj):
        return obj.email
    get_email.short_description = "Adresse e-mail"

    def get_prenom(self, obj):
        return obj.first_name
    get_prenom.short_description = "Prénom"

    def get_nom(self, obj):
        return obj.last_name
    get_nom.short_description = "Nom"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(role='SUPERADMIN')