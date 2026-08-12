from django.contrib import admin
from .models import Spectateur, Transaction, Billet


@admin.register(Spectateur)
class SpectateurAdmin(admin.ModelAdmin):
    list_display = ('prenom', 'nom', 'email', 'tel')
    search_fields = ('nom', 'prenom', 'email', 'tel')


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ( 'mode_paiement', 'montant', 'telephone', 'date')
    list_filter = ('mode_paiement', 'date')
    search_fields = ('telephone',)
    readonly_fields = ('date',)


@admin.register(Billet)
class BilletAdmin(admin.ModelAdmin):
    list_display = ('qr_code', 'spectateur', 'evenement', 'zone', 'place')
    search_fields = ('qr_code', 'spectateur__nom', 'spectateur__email')
    list_filter = ('evenement', 'zone')
    readonly_fields = ('qr_code',)