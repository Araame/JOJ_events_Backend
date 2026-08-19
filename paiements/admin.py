from django.contrib import admin
from .models import Billet, Transaction, Payment


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('numero_transaction', 'mode_paiement', 'montant', 'telephone', 'date')
    list_filter = ('mode_paiement',)
    search_fields = ('numero_transaction', 'telephone')
    readonly_fields = ('date',)


@admin.register(Billet)
class BilletAdmin(admin.ModelAdmin):
    list_display = ('code_unique', 'evenement', 'type_billet', 'statut', 'date_commande')
    list_filter = ('type_billet', 'statut')
    search_fields = ('code_unique', 'utilisateur__username', 'evenement__titre')
    readonly_fields = ('code_unique', 'zones_accessibles', 'date_commande')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('reference', 'billet', 'montant', 'methode', 'statut', 'date_creation')
    list_filter = ('methode', 'statut')
    search_fields = ('reference', 'reference_prestataire')
    readonly_fields = ('reference', 'montant', 'date_creation', 'date_modification')
