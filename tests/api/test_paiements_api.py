"""
Tests des endpoints de l'application PAIEMENTS (JOJ Dakar 2026).

Couverture :
- /api/payments/tickets/       : réservation de billets par un spectateur anonyme (POST)
- /api/payments/tickets/<pk>/  : détail d'un billet (GET)
- /api/payments/payments/      : initiation du paiement d'une commande (POST)
- /api/payments/payments/<pk>/ : détail d'un paiement (GET)

Scénarios validés :
- Réservation anonyme sans compte (le spectateur est créé/récupéré automatiquement)
- Calcul du prix côté serveur (non modifiable par le client)
- Validations : quantités, doublons de types, email, événement inexistant
- Paiement réussi : billets validés, transaction unique, notification
- Paiement échoué : billets inchangés, erreur 400
- Refus : billet déjà payé, billets de spectateurs différents, statut non payable
- Comportement du gateway MOCK (simulé) et test avec un gateway qui échoue

Le spectateur n'a pas besoin de compte : toutes les vues sont publiques
(permissions.AllowAny).

Lancez :
    pytest tests/api/test_paiements_api.py -v
"""
import pytest
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APIClient

from paiements.models import (
    Billet, Payment, Spectateur, Transaction,
    StatutPaiement, StatutBillet, TypeBillet, PRIX_PAR_TYPE,
)
from sites.models import Site
from evenements.models import Discipline, Categorie, Evenement
from paiements.gateway import PaymentGateway

Utilisateur = get_user_model()

# ---------------------------------------------------------------------------
# URLs — adaptez si l'include global change le préfixe
# ---------------------------------------------------------------------------
# URLs réelles vérifiées via reverse('billet-list-create') et reverse('payment-create')
URL_TICKETS = '/api/tickets/'
URL_PAYMENTS = '/api/payments/'
URL_TOKEN = '/api/utilisateurs/connexion/'


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def obtenir_token(identifiant, password):
    """Génère un token JWT directement via le serializer SimpleJWT."""
    from rest_framework_simplejwt.serializers import TokenObtainSerializer
    from rest_framework_simplejwt.tokens import RefreshToken

    cle = Utilisateur.USERNAME_FIELD
    serializer = TokenObtainSerializer(data={
        cle: identifiant,
        'password': password,
    })
    serializer.is_valid(raise_exception=True)
    if 'access' in serializer.validated_data:
        return serializer.validated_data['access']
    refresh = RefreshToken.for_user(serializer.user)
    return str(refresh.access_token)


def creer_client_avec_token(username, password):
    """Client APIClient authentifié avec le token JWT en header."""
    from rest_framework.test import APIClient as _APIClient
    client = _APIClient()
    token = obtenir_token(username, password)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    return client


def commande_valide(evenement_pk, lignes=None):
    """Données complètes et valides pour une commande de billets."""
    if lignes is None:
        lignes = [
            {'type_billet': TypeBillet.STANDARD, 'quantite': 2},
            {'type_billet': TypeBillet.VIP, 'quantite': 1},
        ]
    return {
        'spectateur': {
            'nom': 'Diallo',
            'prenom': 'Mamadou',
            'email': 'mamadou.diallo@joj-test.sn',
            'tel': '771234567',
        },
        'evenement': evenement_pk,
        'billets': lignes,
    }


# ---------------------------------------------------------------------------
# Gateway de simulation qui ÉCHOUE toujours (pour les tests d'échec)
# ---------------------------------------------------------------------------
class EchecPaymentGateway(PaymentGateway):
    """Gateway simulé qui échoue systématiquement."""

    def initier(self, reference: str, montant: float, methode: str) -> dict:
        return {
            'succes': False,
            'reference_prestataire': '',
            'message': 'Fonds insuffisants',
        }


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def evenement_test(db):
    """Événement de référence (l'événement minimal pour les réservations).

    Crée aussi un Site et une Catégorie de support, car le modèle Evenement
    exige l'heure, le site et la catégorie.
    """
    from django.utils import timezone

    # Site de support
    site = Site.objects.create(
        nom='Stade de Test',
        ville='Dakar',
        region='Dakar',
        capacite=50000,
    )

    # Discipline + Catégorie de support
    discipline = Discipline.objects.create(nom='Basketball')
    categorie = Categorie.objects.create(
        nom='Hommes', discipline=discipline,
    )

    return Evenement.objects.create(
        titre='Finale Basket',
        date=timezone.now().date(),
        heure=timezone.now().time(),
        site=site,
        categorie=categorie,
        description='Finale masculine de basketball',
    )


@pytest.fixture
def superadmin(db):
    """Superadmin de test (pattern validé dans test_utilisateurs_api.py)."""
    return Utilisateur.objects.create_user(
        username='super_admin', password='MotDePasse123!',
        email='superadmin@joj.sn',
        is_superuser=True,
    )


# ===========================================================================
# Tests de la commande de billets (spectateur anonyme)
# ===========================================================================
@pytest.mark.django_db
class TestCommandeBillets:
    """POST /api/payments/tickets/ — réservation sans compte."""

    def test_reservation_anonyme_reussie(self, evenement_test):
        """Un spectateur anonyme peut réserver sans créer de compte."""
        client = APIClient()
        response = client.post(URL_TICKETS, commande_valide(evenement_test.pk),
                               format='json')

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data['nombre_billets'] == 3
        assert data['total'] == 2 * 5000 + 1 * 15000  # 25000
        assert Billet.objects.count() == 3

    def test_spectateur_cree_automatiquement(self, evenement_test):
        """Le spectateur est créé automatiquement (get_or_create par email)."""
        client = APIClient()
        client.post(URL_TICKETS, commande_valide(evenement_test.pk),
                    format='json')

        assert Spectateur.objects.filter(email='mamadou.diallo@joj-test.sn').exists()

    def test_spectateur_reutilise_si_email_existant(self, evenement_test):
        """Un même email réutilise le spectateur existant (pas de doublon)."""
        client = APIClient()
        client.post(URL_TICKETS, commande_valide(evenement_test.pk),
                    format='json')
        assert Spectateur.objects.count() == 1

        # Deuxième commande avec le même email
        data = commande_valide(evenement_test.pk)
        data['spectateur']['prenom'] = 'Autre Prenom'
        client.post(URL_TICKETS, data, format='json')
        assert Spectateur.objects.count() == 1

    def test_prix_calcule_cote_serveur(self, evenement_test):
        """Le prix est déterminé par le serveur selon le type, jamais par le client."""
        client = APIClient()
        response = client.post(URL_TICKETS, commande_valide(evenement_test.pk),
                               format='json')
        billets = response.json()['billets']
        for billet in billets:
            prix_attendu = PRIX_PAR_TYPE[billet['type_billet']]
            assert billet['prix_unitaire'] == prix_attendu

    def test_billet_presse_gratuit(self, evenement_test):
        """Un billet PRESSE est gratuit (0 FCFA)."""
        client = APIClient()
        response = client.post(URL_TICKETS, commande_valide(
            evenement_test.pk,
            lignes=[{'type_billet': TypeBillet.PRESSE, 'quantite': 1}],
        ), format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()['total'] == 0

    def test_zones_accessibles_definies_automatiquement(self, evenement_test):
        """Les zones accessibles sont attribuées selon le type de billet."""
        from paiements.models import ZONES_PAR_TYPE

        client = APIClient()
        response = client.post(URL_TICKETS, commande_valide(evenement_test.pk),
                               format='json')
        billets = response.json()['billets']
        for billet in billets:
            assert set(billet['zones_accessibles']) == set(
                ZONES_PAR_TYPE[billet['type_billet']])

    def test_code_unique_genere(self, evenement_test):
        """Chaque billet reçoit un code_unique UUID généré automatiquement."""
        client = APIClient()
        response = client.post(URL_TICKETS, commande_valide(evenement_test.pk),
                               format='json')
        billets = response.json()['billets']
        codes = [b['code_unique'] for b in billets]
        assert len(codes) == len(set(codes))  # tous uniques
        assert all(c is not None for c in codes)

    def test_detail_billet_public(self, evenement_test):
        """Le détail d'un billet est accessible publiquement."""
        client = APIClient()
        response = client.post(URL_TICKETS, commande_valide(evenement_test.pk),
                               format='json')
        pk = response.json()['billets'][0]['id']

        detail = client.get(f'{URL_TICKETS}{pk}/')
        assert detail.status_code == status.HTTP_200_OK
        assert detail.json()['evenement_titre'] == 'Finale Basket'

    def test_detail_billet_inexistant_404(self):
        """Le détail d'un billet inexistant renvoie 404."""
        client = APIClient()
        assert client.get(f'{URL_TICKETS}99999/').status_code == status.HTTP_404_NOT_FOUND


# ===========================================================================
# Validations de la commande
# ===========================================================================
@pytest.mark.django_db
class TestValidationCommande:
    """Refus des commandes mal formées ou invalides."""

    def test_email_invalide_refuse(self, evenement_test):
        """Un email mal formé est refusé."""
        client = APIClient()
        data = commande_valide(evenement_test.pk)
        data['spectateur']['email'] = 'pas-un-email'

        response = client.post(URL_TICKETS, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_quantite_zero_refusee(self, evenement_test):
        """Une quantité de 0 est refusée (min_value=1)."""
        client = APIClient()
        data = commande_valide(
            evenement_test.pk,
            lignes=[{'type_billet': TypeBillet.STANDARD, 'quantite': 0}],
        )
        assert client.post(URL_TICKETS, data, format='json').status_code == status.HTTP_400_BAD_REQUEST

    def test_quantite_superieure_a_10_refusee(self, evenement_test):
        """Une quantité supérieure à 10 est refusée (max_value=10)."""
        client = APIClient()
        data = commande_valide(
            evenement_test.pk,
            lignes=[{'type_billet': TypeBillet.STANDARD, 'quantite': 11}],
        )
        assert client.post(URL_TICKETS, data, format='json').status_code == status.HTTP_400_BAD_REQUEST

    def test_types_dupliques_refuses(self, evenement_test):
        """Le même type de billet ne peut pas apparaître deux fois."""
        client = APIClient()
        data = commande_valide(
            evenement_test.pk,
            lignes=[
                {'type_billet': TypeBillet.STANDARD, 'quantite': 1},
                {'type_billet': TypeBillet.STANDARD, 'quantite': 2},
            ],
        )
        response = client.post(URL_TICKETS, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_commande_sans_billets_refusee(self, evenement_test):
        """Une commande vide (min_length=1) est refusée."""
        client = APIClient()
        data = commande_valide(evenement_test.pk, lignes=[])
        assert client.post(URL_TICKETS, data, format='json').status_code == status.HTTP_400_BAD_REQUEST

    def test_type_invalide_refuse(self, evenement_test):
        """Un type de billet hors choix (STANDARD/VIP/PRESSE) est refusé."""
        client = APIClient()
        data = commande_valide(
            evenement_test.pk,
            lignes=[{'type_billet': 'PREMIUM', 'quantite': 1}],
        )
        assert client.post(URL_TICKETS, data, format='json').status_code == status.HTTP_400_BAD_REQUEST

    def test_evenement_inexistant_refuse(self):
        """Rattacher une commande à un événement inexistant est refusé."""
        client = APIClient()
        data = commande_valide(99999)
        assert client.post(URL_TICKETS, data, format='json').status_code == status.HTTP_400_BAD_REQUEST

    def test_champs_spectateur_manquants_refuses(self, evenement_test):
        """Un spectateur incomplet (nom ou prénom vide) est refusé."""
        client = APIClient()
        data = commande_valide(evenement_test.pk)
        data['spectateur']['nom'] = ''
        assert client.post(URL_TICKETS, data, format='json').status_code == status.HTTP_400_BAD_REQUEST


# ===========================================================================
# Tests de paiement
# ===========================================================================
@pytest.mark.django_db
class TestPaiement:
    """POST /api/payments/payments/ — initiation et traitement du paiement."""

    def test_paiement_reussi_valide_billets(self, evenement_test):
        """Un paiement réussi valide les billets et crée la transaction."""
        client = APIClient()
        commande = client.post(URL_TICKETS, commande_valide(evenement_test.pk),
                               format='json')
        ids_billets = [b['id'] for b in commande.json()['billets']]

        response = client.post(URL_PAYMENTS, {
            'billets': ids_billets,
            'methode': 'MOCK',
        }, format='json')

        assert response.status_code == status.HTTP_201_CREATED

        for pk in ids_billets:
            billet = Billet.objects.get(pk=pk)
            assert billet.statut == StatutBillet.VALIDE
            assert billet.transaction is not None

        assert Payment.objects.count() >= 1
        payment = Payment.objects.order_by('-date_creation').first()
        assert payment.statut == StatutPaiement.REUSSI

    def test_transaction_unique_pour_la_commande(self, evenement_test):
        """Une seule transaction couvre tous les billets de la commande."""
        client = APIClient()
        commande = client.post(URL_TICKETS, commande_valide(evenement_test.pk),
                               format='json')
        ids_billets = [b['id'] for b in commande.json()['billets']]

        client.post(URL_PAYMENTS, {'billets': ids_billets, 'methode': 'MOCK'},
                    format='json')

        transactions = Transaction.objects.all()
        assert transactions.count() == 1
        # Le montant de la transaction est le total de la commande
        assert transactions.first().montant == Decimal('25000.00')

    def test_montant_calcule_cote_serveur(self, evenement_test):
        """Le montant du paiement est calculé par le serveur, pas par le client."""
        client = APIClient()
        commande = client.post(URL_TICKETS, commande_valide(evenement_test.pk),
                               format='json')
        ids_billets = [b['id'] for b in commande.json()['billets']]

        client.post(URL_PAYMENTS, {'billets': ids_billets, 'methode': 'MOCK'},
                    format='json')

        payment = Payment.objects.order_by('-date_creation').first()
        # 2 STANDARD (2x5000) + 1 VIP (15000) = 25000, quoi que le client envoie
        assert payment.montant == Decimal('25000.00')

    def test_reference_prestataire_enregistree(self, evenement_test):
        """La référence du prestataire (MOCK) est conservée en cas de succès."""
        client = APIClient()
        commande = client.post(URL_TICKETS, commande_valide(evenement_test.pk),
                               format='json')
        ids_billets = [b['id'] for b in commande.json()['billets']]

        client.post(URL_PAYMENTS, {'billets': ids_billets, 'methode': 'MOCK'},
                    format='json')

        payment = Payment.objects.order_by('-date_creation').first()
        assert payment.reference_prestataire.startswith('MOCK-')

    def test_paiement_echoue_billets_unchanged(self, evenement_test):
        """Si le gateway échoue : billets inchangés, paiement ECHOUE, erreur 400."""
        client = APIClient()
        commande = client.post(URL_TICKETS, commande_valide(evenement_test.pk),
                               format='json')
        ids_billets = [b['id'] for b in commande.json()['billets']]

        with patch('paiements.views.get_gateway', return_value=EchecPaymentGateway()):
            response = client.post(URL_PAYMENTS, {
                'billets': ids_billets, 'methode': 'MOCK',
            }, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()['erreur'] == 'Fonds insuffisants'

        for pk in ids_billets:
            billet = Billet.objects.get(pk=pk)
            assert billet.statut == StatutBillet.EN_ATTENTE
            assert billet.transaction is None

    def test_billet_deja_paye_refuse(self, evenement_test):
        """On ne peut pas payer deux fois le même billet."""
        client = APIClient()
        commande = client.post(URL_TICKETS, commande_valide(evenement_test.pk),
                               format='json')
        id_billet = commande.json()['billets'][0]['id']

        # Premier paiement : succès
        client.post(URL_PAYMENTS, {'billets': [id_billet], 'methode': 'MOCK'},
                    format='json')

        # Second paiement sur le même billet : refusé
        response = client.post(URL_PAYMENTS, {'billets': [id_billet], 'methode': 'MOCK'},
                               format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_billet_non_payable_refuse(self, evenement_test):
        """Un billet déjà VALIDE ne peut pas être repayé."""
        client = APIClient()
        commande = client.post(URL_TICKETS, commande_valide(evenement_test.pk),
                               format='json')
        id_billet = commande.json()['billets'][0]['id']
        billet = Billet.objects.get(pk=id_billet)
        billet.statut = StatutBillet.VALIDE
        billet.save()

        response = client.post(URL_PAYMENTS, {'billets': [id_billet], 'methode': 'MOCK'},
                               format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_billets_spectateurs_differents_refuses(self, evenement_test):
        """Une commande de paiement mélangeant des spectateurs différents est refusée."""
        client = APIClient()

        # Commande du spectateur A
        client.post(URL_TICKETS, commande_valide(evenement_test.pk), format='json')
        billet_a = Billet.objects.order_by('-date_commande').first().pk

        # Commande du spectateur B (email différent)
        data_b = commande_valide(evenement_test.pk)
        data_b['spectateur']['email'] = 'autre.personne@joj-test.sn'
        client.post(URL_TICKETS, data_b, format='json')
        billet_b = Billet.objects.order_by('-date_commande').first().pk

        response = client.post(URL_PAYMENTS, {
            'billets': [billet_a, billet_b], 'methode': 'MOCK',
        }, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_detail_paiement_public(self, evenement_test):
        """Le détail d'un paiement est accessible publiquement."""
        client = APIClient()
        commande = client.post(URL_TICKETS, commande_valide(evenement_test.pk),
                               format='json')
        ids_billets = [b['id'] for b in commande.json()['billets']]
        client.post(URL_PAYMENTS, {'billets': ids_billets, 'methode': 'MOCK'},
                    format='json')

        payment = Payment.objects.order_by('-date_creation').first()
        detail = client.get(f'{URL_PAYMENTS}{payment.pk}/')
        assert detail.status_code == status.HTTP_200_OK
        assert detail.json()['statut_display'] == 'Réussi'

    def test_detail_paiement_inexistant_404(self):
        """Le détail d'un paiement inexistant renvoie 404."""
        client = APIClient()
        assert client.get(f'{URL_PAYMENTS}99999/').status_code == status.HTTP_404_NOT_FOUND

    def test_methode_invalide_refusee(self, evenement_test):
        """Une méthode de paiement hors choix est refusée."""
        client = APIClient()
        commande = client.post(URL_TICKETS, commande_valide(evenement_test.pk),
                               format='json')
        ids_billets = [b['id'] for b in commande.json()['billets']]

        response = client.post(URL_PAYMENTS, {
            'billets': ids_billets, 'methode': 'CRYPTOMONNAIE',
        }, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_paiement_sans_billets_refuse(self):
        """Un paiement sans liste de billets est refusé (min_length=1)."""
        client = APIClient()
        response = client.post(URL_PAYMENTS, {
            'billets': [], 'methode': 'MOCK',
        }, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
