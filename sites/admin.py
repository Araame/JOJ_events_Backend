from django.contrib import admin
from .models import Site, Zone


class ZoneInline(admin.TabularInline):
    """Permet d'ajouter des zones directement depuis la fiche d'un site."""
    model = Zone
    extra = 2
    fields = ('nom', 'capacite')


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ('nom', 'ville', 'region', 'capacite')
    list_filter = ('region', 'ville')
    search_fields = ('nom', 'ville', 'region')
    inlines = [ZoneInline]


@admin.register(Zone)
class ZoneAdmin(admin.ModelAdmin):
    list_display = ('nom', 'site', 'capacite')
    list_filter = ('site', 'nom')
    search_fields = ('nom',)
# Register your models here.
