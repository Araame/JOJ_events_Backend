"""
Tests des endpoints de l'application SITES (JOJ Dakar 2026).

Couverture :
- /api/sites/     : liste (publique), création (personnel), détails, modification, suppression
- /api/zones/     : liste (publique), création (personnel), détails, modification, suppression
- Permissions IsAdminPersonnel (lecture publique / écriture ADMIN ou SUPERADMIN)
- Validations du serializer (unicité nom, unicité zone par site, longueurs, champs obligatoires)
- Pagination des sites

Pré-requis :
- SimpleJWT configuré (routes obtenir-token / rafraichir-token dans utilisateurs/urls.py)
- Fixture de test recréée automatiquement par pytest-django

Lancez :
    pytest tests/api/test_sites_api.py -v
"""
import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APIClient

from sites.models import Site, Zone
from utilisateurs.models import RolePersonnel

Utilisateur = get_user_model()

# ---------------------------------------------------------------------------
# URLs (adaptez si votre include global change le préfixe)
# ---------------------------------------------------------------------------
URL_SITES = '/api/sites/'
URL_ZONES = '/api/zones/'
URL_TOKEN = '/api/utilisateurs/connexion/'


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def client_authentifie(client, identifiant, password):
    """Connecte un client de test avec JWT et retourne le client.

    La clé envoyée (username ou email) est déterminée automatiquement
    selon le USERNAME_FIELD de votre modèle Personnel.
    """
    from django.contrib.auth import get_user_model as _get_user_model
    cle = _get_user_model().USERNAME_FIELD
    client.post(URL_TOKEN, {
        cle: identifiant,
        'password': password,
    }, format='json')
    return client


def obtenir_token(identifiant, password):
    """Retourne le token JWT d'un utilisateur.

    Stratégie : génération directe via le serializer SimpleJWT
    (TokenObtainSerializer) — infaillible car elle ne dépend pas de la
    configuration HTTP du endpoint de connexion.
    """
    from rest_framework_simplejwt.serializers import TokenObtainSerializer

    # Le serializer attend la clé USERNAME_FIELD du modèle Personnel
    cle = Utilisateur.USERNAME_FIELD  # 'username' ou 'email'
    serializer = TokenObtainSerializer(data={
        cle: identifiant,
        'password': password,
    })
    serializer.is_valid(raise_exception=True)
    # Retourne le token d'accès s'il est disponible (cas d'un serializer
    # personnalisé enrichi), sinon construit un access token proprement
    if 'access' in serializer.validated_data:
        return serializer.validated_data['access']
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(serializer.user)
    return str(refresh.access_token)


def creer_client_avec_token(username, password):
    """Client APIClient authentifié avec le token JWT en header."""
    client = APIClient()
    token = obtenir_token(username, password)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    return client


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
def creer_comptes_reference():
    """Crée les comptes de référence exactement comme dans
    test_utilisateurs_api.py (pattern validé et passant).

    Retourne (username_superadmin, username_admin) pour la connexion.
    """
    superadmin = Utilisateur.objects.create_user(
        username='super_admin', password='MotDePasse123!',
        email='superadmin@joj.sn',
        is_superuser=True,
    )
    admin = Utilisateur.objects.create_user(
        username='admin_normal', password='MotDePasse123!',
        email='admin@joj.sn',
        is_staff=True, role=RolePersonnel.ADMIN,
    )
    return superadmin, admin


@pytest.fixture
def superadmin():
    """Superadmin de test (pattern validé dans test_utilisateurs_api.py)."""
    superadmin, _ = creer_comptes_reference()
    return superadmin


@pytest.fixture
def admin_normal(superadmin):
    """Admin de test (créé par creer_comptes_reference)."""
    return Utilisateur.objects.get(username='admin_normal')


@pytest.fixture
def site_test():
    """Un site de référence pour les tests."""
    return Site.objects.create(
        nom='Stade Iba Mar Diop',
        ville='Dakar',
        region='Dakar',
        latitude=14.7167,
        longitude=-17.4677,
        capacite=30000,
    )


@pytest.fixture
def zone_test(site_test):
    """Une zone de référence."""
    return Zone.objects.create(
        nom='Gradin Nord',
        site=site_test,
        capacite=10000,
    )


# ===========================================================================
# Tests du modèle Site
# ===========================================================================
class TestModeleSite:
    """Tests de la logique du modèle Site (hors API)."""
    pytestmark = pytest.mark.django_db

    def test_creation_site(self, site_test):
        """Un site se crée avec ses champs obligatoires."""
        assert site_test.pk is not None
        assert str(site_test).lower().find('iba mar') != -1 or 'Stade' in str(site_test)

    def test_champ_nom_existe(self):
        """Le champ nom est bien un CharField du modèle."""
        from django.db import models
        champ = Site._meta.get_field('nom')
        assert isinstance(champ, models.CharField)
        assert champ.max_length <= 255

    def test_champ_capacite_entier_positif(self):
        """capacite est un entier positif (PositiveIntegerField)."""
        champ = Site._meta.get_field('capacite')
        assert 'PositiveIntegerField' in type(champ).__name__


# ===========================================================================
# Tests du modèle Zone
# ===========================================================================
class TestModeleZone:
    """Tests de la logique du modèle Zone (hors API)."""
    pytestmark = pytest.mark.django_db

    def test_str_zone(self, zone_test):
        """Le __str__ affiche le nom de la zone et du site."""
        representation = str(zone_test)
        assert 'Gradin Nord' in representation
        assert 'Stade Iba Mar Diop' in representation

    def test_zone_sans_capacite_rejectee(self, site_test):
        """capacite ne peut pas être null (PositiveIntegerField non nullable)."""
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            Zone.objects.create(nom='Loge', site=site_test, capacite=None)


# ===========================================================================
# Tests d'accès (permissions IsAdminPersonnel)
# ===========================================================================
class TestAccesSites:
    """Le spectateur lit, le personnel écrit."""
    pytestmark = pytest.mark.django_db

    def test_spectateur_peut_lister_sites(self):
        """GET /api/sites/ est public."""
        client = APIClient()
        response = client.get(URL_SITES)
        assert response.status_code == status.HTTP_200_OK

    def test_spectateur_peut_lire_details_site(self, site_test):
        """GET /api/sites/<id>/ est public."""
        client = APIClient()
        response = client.get(f'{URL_SITES}{site_test.pk}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['nom'] == 'Stade Iba Mar Diop'

    def test_anonyme_ne_peut_pas_creer_site(self):
        """POST /api/sites/ exige un personnel authentifié."""
        client = APIClient()
        response = client.post(URL_SITES, {
            'nom': 'Nouveau site',
            'ville': 'Mbour',
            'region': 'Thiès',
            'latitude': 14.4,
            'longitude': -16.9,
            'capacite': 5000,
        }, format='json')
        assert response.status_code in (status.HTTP_401_UNAUTHORIZED,
                                        status.HTTP_403_FORBIDDEN)

    def test_anonyme_ne_peut_pas_modifier_site(self, site_test):
        """PUT /api/sites/<id>/ exige un personnel authentifié."""
        client = APIClient()
        response = client.put(f'{URL_SITES}{site_test.pk}/', {
            'nom': 'Nom modifié',
            'ville': 'Dakar',
            'region': 'Dakar',
            'latitude': 14.7167,
            'longitude': -17.4677,
            'capacite': 30000,
        }, format='json')
        assert response.status_code in (status.HTTP_401_UNAUTHORIZED,
                                        status.HTTP_403_FORBIDDEN)

    def test_anonyme_ne_peut_pas_supprimer_site(self, site_test):
        """DELETE /api/sites/<id>/ exige un personnel authentifié."""
        client = APIClient()
        response = client.delete(f'{URL_SITES}{site_test.pk}/')
        assert response.status_code in (status.HTTP_401_UNAUTHORIZED,
                                        status.HTTP_403_FORBIDDEN)

    def test_spectateur_non_personnel_refuse_en_ecriture(self):
        """Un utilisateur authentifié SANS rôle personnel est refusé en écriture."""
        Utilisateur.objects.create_user(
            username='spectateur_pseudo',
            email='spec@joj.sn',
            password='MotDePasse123!',
            role='SPECTATEUR',
        )
        client = creer_client_avec_token('spectateur_pseudo', 'MotDePasse123!')
        response = client.post(URL_SITES, {
            'nom': 'Site illégal',
            'ville': 'Dakar',
            'region': 'Dakar',
            'latitude': 14.7,
            'longitude': -17.4,
            'capacite': 1000,
        }, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ===========================================================================
# Tests CRUD Sites (personnel authentifié)
# ===========================================================================
class TestCRUDSites:
    """CRUD complet des sites par le personnel."""
    pytestmark = pytest.mark.django_db

    def test_superadmin_cree_site(self, superadmin):
        """POST /api/sites/ avec tous les champs obligatoires."""
        client = creer_client_avec_token('super_admin', 'MotDePasse123!')
        response = client.post(URL_SITES, {
            'nom': 'Dakar Arena',
            'ville': 'Diamniadio',
            'region': 'Dakar',
            'latitude': 14.75,
            'longitude': -17.18,
            'capacite': 15000,
        }, format='json')
        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert Site.objects.filter(nom='Dakar Arena').exists()

    def test_admin_cree_site(self, admin_normal):
        """Un ADMIN (limité) peut aussi créer un site."""
        client = creer_client_avec_token('admin_normal', 'MotDePasse123!')
        response = client.post(URL_SITES, {
            'nom': 'Complexe sportif Mbour',
            'ville': 'Mbour',
            'region': 'Thiès',
            'latitude': 14.4167,
            'longitude': -16.9667,
            'capacite': 8000,
        }, format='json')
        assert response.status_code == status.HTTP_201_CREATED

    def test_superadmin_modifie_site(self, superadmin, site_test):
        """PUT /api/sites/<id>/ : modification complète."""
        client = creer_client_avec_token('super_admin', 'MotDePasse123!')
        response = client.put(f'{URL_SITES}{site_test.pk}/', {
            'nom': 'Stade Iba Mar Diop - Rénové',
            'ville': 'Dakar',
            'region': 'Dakar',
            'latitude': 14.7167,
            'longitude': -17.4677,
            'capacite': 35000,
        }, format='json')
        assert response.status_code == status.HTTP_200_OK, response.data
        site_test.refresh_from_db()
        assert site_test.nom == 'Stade Iba Mar Diop - Rénové'
        assert site_test.capacite == 35000

    def test_superadmin_supprime_site(self, superadmin, site_test):
        """DELETE /api/sites/<id>/ : suppression physique."""
        pk = site_test.pk
        client = creer_client_avec_token('super_admin', 'MotDePasse123!')
        response = client.delete(f'{URL_SITES}{pk}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Site.objects.filter(pk=pk).exists()

    def test_id_inexistant_404(self, superadmin):
        """GET/DELETE d'un site inexistant → 404."""
        client = creer_client_avec_token('super_admin', 'MotDePasse123!')
        assert client.get(f'{URL_SITES}99999/').status_code == status.HTTP_404_NOT_FOUND
        assert client.delete(f'{URL_SITES}99999/').status_code == status.HTTP_404_NOT_FOUND

    def test_liste_pagination(self, site_test):
        """La liste des sites utilise la pagination configurée."""
        client = APIClient()
        response = client.get(URL_SITES)
        assert response.status_code == status.HTTP_200_OK
        # La pagination SitePagination doit envelopper dans {"count", "results", ...}
        assert 'count' in response.data or 'results' in response.data


# ===========================================================================
# Tests de validation du serializer Site
# ===========================================================================
class TestValidationSite:
    """Validations métier du SiteSerializer."""
    pytestmark = pytest.mark.django_db

    def test_nom_dupe_refuse(self, superadmin, site_test):
        """Deux sites ne peuvent pas avoir le même nom (unicité)."""
        client = creer_client_avec_token('super_admin', 'MotDePasse123!')
        response = client.post(URL_SITES, {
            'nom': 'Stade Iba Mar Diop',   # déjà existant
            'ville': 'Dakar',
            'region': 'Dakar',
            'latitude': 14.71,
            'longitude': -17.46,
            'capacite': 5000,
        }, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'nom' in response.data or response.data  # une erreur de validation présente

    def test_nom_vide_refuse(self, superadmin):
        """Un site sans nom est refusé."""
        client = creer_client_avec_token('super_admin', 'MotDePasse123!')
        response = client.post(URL_SITES, {
            'nom': '',
            'ville': 'Dakar',
            'region': 'Dakar',
            'latitude': 14.7,
            'longitude': -17.4,
            'capacite': 1000,
        }, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_capacite_negative_refusee(self, superadmin):
        """Une capacité négative est refusée (PositiveIntegerField)."""
        client = creer_client_avec_token('super_admin', 'MotDePasse123!')
        response = client.post(URL_SITES, {
            'nom': 'Site négatif',
            'ville': 'Dakar',
            'region': 'Dakar',
            'latitude': 14.7,
            'longitude': -17.4,
            'capacite': -500,
        }, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_capacite_manquante_refusee(self, superadmin):
        """capacite obligatoire à la création."""
        client = creer_client_avec_token('super_admin', 'MotDePasse123!')
        response = client.post(URL_SITES, {
            'nom': 'Site sans capacité',
            'ville': 'Dakar',
            'region': 'Dakar',
            'latitude': 14.7,
            'longitude': -17.4,
        }, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ===========================================================================
# Tests CRUD Zones
# ===========================================================================
class TestCRUDZones:
    """CRUD des zones par le personnel."""
    pytestmark = pytest.mark.django_db

    def test_superadmin_cree_zone(self, superadmin, site_test):
        """POST /api/zones/ avec site valide."""
        client = creer_client_avec_token('super_admin', 'MotDePasse123!')
        response = client.post(URL_ZONES, {
            'nom': 'Loge VIP',
            'site': site_test.pk,
            'capacite': 500,
        }, format='json')
        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert Zone.objects.filter(nom='Loge VIP', site=site_test).exists()

    def test_zone_sans_site_refusee(self, superadmin):
        """Une zone DOIT être rattachée à un site."""
        client = creer_client_avec_token('super_admin', 'MotDePasse123!')
        response = client.post(URL_ZONES, {
            'nom': 'Zone orpheline',
            'capacite': 100,
        }, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_zone_site_inexistant_400(self, superadmin):
        """Rattacher une zone à un site inexistant est refusé."""
        client = creer_client_avec_token('super_admin', 'MotDePasse123!')
        response = client.post(URL_ZONES, {
            'nom': 'Zone fantôme',
            'site': 99999,
            'capacite': 100,
        }, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_superadmin_modifie_zone(self, superadmin, zone_test):
        """PUT /api/zones/<id>/ : modification."""
        client = creer_client_avec_token('super_admin', 'MotDePasse123!')
        response = client.put(f'{URL_ZONES}{zone_test.pk}/', {
            'nom': 'Gradin Nord Élargi',
            'site': zone_test.site.pk,
            'capacite': 15000,
        }, format='json')
        assert response.status_code == status.HTTP_200_OK, response.data
        zone_test.refresh_from_db()
        assert zone_test.capacite == 15000

    def test_superadmin_supprime_zone(self, superadmin, zone_test):
        """DELETE /api/zones/<id>/."""
        pk = zone_test.pk
        client = creer_client_avec_token('super_admin', 'MotDePasse123!')
        response = client.delete(f'{URL_ZONES}{pk}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Zone.objects.filter(pk=pk).exists()

    def test_liste_zones_publique(self, zone_test):
        """GET /api/zones/ est publique."""
        client = APIClient()
        response = client.get(URL_ZONES)
        assert response.status_code == status.HTTP_200_OK
        noms = {z['nom'] for z in response.data}
        assert 'Gradin Nord' in noms

    def test_id_zone_inexistant_404(self, superadmin):
        """GET/DELETE d'une zone inexistante → 404."""
        client = creer_client_avec_token('super_admin', 'MotDePasse123!')
        assert client.get(f'{URL_ZONES}99999/').status_code == status.HTTP_404_NOT_FOUND
        assert client.delete(f'{URL_ZONES}99999/').status_code == status.HTTP_404_NOT_FOUND


# ===========================================================================
# Tests de validation du serializer Zone
# ===========================================================================
class TestValidationZone:
    """Validations métier du ZoneSerializer."""
    pytestmark = pytest.mark.django_db

    def test_zone_dupe_par_site_refusee(self, superadmin, site_test, zone_test):
        """Deux zones du même nom sur le même site sont interdites."""
        client = creer_client_avec_token('super_admin', 'MotDePasse123!')
        response = client.post(URL_ZONES, {
            'nom': 'Gradin Nord',   # déjà existant sur ce site
            'site': site_test.pk,
            'capacite': 500,
        }, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_meme_nom_autre_site_autorise(self, superadmin, site_test):
        """Le même nom de zone est autorisé sur un AUTRE site."""
        autre_site = Site.objects.create(
            nom='Stade de Mbour',
            ville='Mbour',
            region='Thiès',
            latitude=14.4167,
            longitude=-16.9667,
            capacite=8000,
        )
        client = creer_client_avec_token('super_admin', 'MotDePasse123!')
        response = client.post(URL_ZONES, {
            'nom': 'Gradin Nord',   # OK sur un autre site
            'site': autre_site.pk,
            'capacite': 3000,
        }, format='json')
        assert response.status_code == status.HTTP_201_CREATED, response.data

    def test_capacite_zone_zero_autorisee(self, superadmin, site_test):
        """Une capacité de 0 est acceptée (PositiveIntegerField autorise 0)."""
        client = creer_client_avec_token('super_admin', 'MotDePasse123!')
        response = client.post(URL_ZONES, {
            'nom': 'Zone fermée',
            'site': site_test.pk,
            'capacite': 0,
        }, format='json')
        assert response.status_code == status.HTTP_201_CREATED

    def test_nom_zone_vide_refuse(self, superadmin, site_test):
        """Un nom de zone vide est refusé."""
        client = creer_client_avec_token('super_admin', 'MotDePasse123!')
        response = client.post(URL_ZONES, {
            'nom': '',
            'site': site_test.pk,
            'capacite': 100,
        }, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
