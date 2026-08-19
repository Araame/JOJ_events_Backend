"""
Tests unitaires des signaux de paiement.

Vérifie que :
- Un paiement réussi (statut EN_COURS → REUSSI) :
    • envoie l'email de confirmation au spectateur
    • crée une notification SPECTATEUR
    • crée une notification SUPERADMIN
- Un paiement échoué ne déclenche aucune notification
- Une re-sauvegarde d'un paiement déjà REUSSI ne crée pas de doublon
"""
import pytest
from django.core import mail
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import time, timedelta

from paiements.models import (
    Payment, StatutPaiement, StatutBillet, Spectateur,
    MethodePaiement, Transaction,
)
from evenements.models import Evenement, Discipline, Categorie
from sites.models import Site
from notifications.models import Notification, DestinataireType

Personnel = get_user_model()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def simuler_paiement_reussi(payment):
    transaction_obj = Transaction.objects.create(
        numero_transaction=f"MOCK-{payment.reference}",
        mode_paiement=payment.methode,
        montant=payment.montant,
        telephone=payment.billet.spectateur.tel,
    )
    payment.billet.transaction = transaction_obj
    payment.billet.statut = StatutBillet.VALIDE
    payment.billet.save()

    payment.statut = StatutPaiement.REUSSI
    payment.statut_mis_a_jour = True   # ✅ OBLIGATOIRE
    payment.save()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def contexte_paiement():
    """Crée un spectateur + un événement + 1 billet prêt à payer."""
    spectateur = Spectateur.objects.create(
        nom='Diallo', prenom='Aminata',
        email='aminata.diallo@test.sn', tel='770000000',
    )
    site = Site.objects.create(
        nom='Dakar Arena', ville='Diamniadio', region='Dakar',
        latitude=14.75, longitude=-17.18, capacite=15000,
    )
    discipline = Discipline.objects.create(nom='Basket')
    categorie = Categorie.objects.create(nom='Hommes', discipline=discipline)
    evenement = Evenement.objects.create(
        titre='Finale Basket',
        date=timezone.now().date() + timedelta(days=7),
        heure=time(18, 0),
        site=site,
        categorie=categorie,
    )
    billet = spectateur.billets.create(
        evenement=evenement, type_billet='STANDARD',
    )
    return spectateur, evenement, billet


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
@pytest.mark.api
@pytest.mark.django_db
class TestSignalsPaiement:

    def setup_method(self):
        self.superadmin = Personnel.objects.create_user(
            username='superadmin_test', password='MotDePasse123!',
            role='SUPERADMIN',
        )

    # ------------------------------------------------------------------
    def test_paiement_reussi_notifie_spectateur_et_admin(self, contexte_paiement):
        """Un paiement réussi envoie l'email au spectateur et notifie
        les superadmins."""
        _, _, billet = contexte_paiement

        # 1. Création initiale (comme dans la view) : EN_COURS
        payment = Payment.objects.create(
            billet=billet, montant=5000,
            methode=MethodePaiement.ORANGE_MONEY,
            statut=StatutPaiement.EN_COURS,
        )

        # Aucune notification à ce stade
        assert Notification.objects.count() == 0
        assert len(mail.outbox) == 0

        # 2. Succès du gateway → transaction + billet validé + REUSSI
        simuler_paiement_reussi(payment)

        # → Email envoyé au spectateur
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to[0] == 'aminata.diallo@test.sn'
        assert '5000' in mail.outbox[0].body

        # → 1 notification spectateur + 1 par superadmin
        assert Notification.objects.filter(
            destinataire_type=DestinataireType.SPECTATEUR,
        ).count() == 1
        assert Notification.objects.filter(
            destinataire_type=DestinataireType.PERSONNEL,
        ).count() == 1

        # → La notification superadmin mentionne le spectateur et le montant
        notif_admin = Notification.objects.filter(
            destinataire_type=DestinataireType.PERSONNEL,
        ).first()
        assert 'Diallo' in notif_admin.contenu
        assert '5000' in notif_admin.contenu

        # → Le billet est bien validé
        billet.refresh_from_db()
        assert billet.statut == StatutBillet.VALIDE
        assert billet.transaction is not None

    # ------------------------------------------------------------------
    def test_paiement_echoue_ne_notifie_personne(self, contexte_paiement):
        """Un paiement échoué ne déclenche aucune notification ni email."""
        _, _, billet = contexte_paiement

        payment = Payment.objects.create(
            billet=billet, montant=5000,
            methode=MethodePaiement.WAVE,
            statut=StatutPaiement.EN_COURS,
        )
        payment.statut = StatutPaiement.ECHOUE
        payment.save()

        assert Notification.objects.count() == 0
        assert len(mail.outbox) == 0

    # ------------------------------------------------------------------
    def test_pas_de_doublon_si_double_save(self, contexte_paiement):
      _, _, billet = contexte_paiement

      payment = Payment.objects.create(
          billet=billet, montant=5000,
          methode=MethodePaiement.MOCK,
          statut=StatutPaiement.EN_COURS,
      )
      payment.statut = StatutPaiement.REUSSI
      payment.statut_mis_a_jour = True   # ✅ flag sur le 1er save uniquement
      payment.save()
      payment.save()  # ❌ PAS de flag ici → aucun email

      assert len(mail.outbox) == 1, "Doublon d'email détecté !"

    # ------------------------------------------------------------------
    def test_contenu_email_complet(self, contexte_paiement):
        """L'email de confirmation contient les infos essentielles :
        transaction, événement, type de billet, code unique."""
        _, _, billet = contexte_paiement

        payment = Payment.objects.create(
            billet=billet, montant=5000,
            methode=MethodePaiement.ORANGE_MONEY,
            statut=StatutPaiement.EN_COURS,
        )
        simuler_paiement_reussi(payment)

        corps = mail.outbox[0].body
        assert 'Aminata' in corps
        assert 'Finale Basket' in corps
        assert 'MOCK-' in corps
        assert 'Standard' in corps      # ✅ au lieu de 'STANDARD'
        assert str(billet.code_unique) in corps



