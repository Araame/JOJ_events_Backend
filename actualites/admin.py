from django.contrib import admin
from .models import Actualite


@admin.action(description="Publier les actualités sélectionnées")
def publier(modeladmin, request, queryset):
    queryset.update(brouillon=False)


@admin.action(description="Mettre en brouillon les actualités sélectionnées")
def mettre_en_brouillon(modeladmin, request, queryset):
    queryset.update(brouillon=True)


@admin.register(Actualite)
class ActualiteAdmin(admin.ModelAdmin):
    list_display = ('titre', 'auteur', 'evenement_lie', 'date_publication', 'brouillon')
    list_filter = ('brouillon', 'date_publication', 'auteur')
    search_fields = ('titre', 'description')
    actions = [publier, mettre_en_brouillon]