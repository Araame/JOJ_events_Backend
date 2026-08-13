from django.contrib import admin
from .models import Discipline, Categorie, Competiteur, Joueur, Equipe, Evenement, Resultat


@admin.register(Discipline)
class DisciplineAdmin(admin.ModelAdmin):
    list_display = ('nom',)
    search_fields = ('nom',)


@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ('nom', 'discipline')
    list_filter = ('discipline',)
    search_fields = ('nom',)


@admin.register(Competiteur)
class CompetiteurAdmin(admin.ModelAdmin):
    list_display = ('categorie', 'statut', 'pays')
    list_filter = ('pays', 'categorie')


@admin.register(Joueur)
class JoueurAdmin(admin.ModelAdmin):
    list_display = ('prenom', 'nom', 'pays', 'categorie', 'statut')
    list_filter = ('pays', 'categorie')
    search_fields = ('nom', 'prenom')


@admin.register(Equipe)
class EquipeAdmin(admin.ModelAdmin):
    list_display = ('nom', 'pays', 'categorie', 'statut')
    list_filter = ('pays', 'categorie')
    search_fields = ('nom',)


@admin.register(Evenement)
class EvenementAdmin(admin.ModelAdmin):
    list_display = ('titre', 'date', 'heure', 'site', 'categorie')
    list_filter = ('date', 'site', 'categorie')
    search_fields = ('titre',)
    filter_horizontal = ('competiteurs',)


@admin.register(Resultat)
class ResultatAdmin(admin.ModelAdmin):
    list_display = ('evenement', 'score', 'createur')
    search_fields = ('evenement__titre',)