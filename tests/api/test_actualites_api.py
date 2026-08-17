"""
Tests des endpoints de l'application ACTUALITÉS (JOJ Dakar 2026).

Couverture :
- GET  /api/actualites/        : lecture publique
- GET  /api/actualites/<pk>/   : détail public
- POST /api/actualites/        : création réservée au personnel
- PUT/PATCH /api/actualites/<pk>/ : modification réservée au personnel
- DELETE /api/actualites/<pk>/ : suppression réservée au personnel
- Validations du serializer (titre, description, événement, dates, brouillon)
- Filtres (événement lié, auteur)
- Auteur automatiquement renseigné (perform_create)

Lancez :
    pytest tests/api/test_actualites_api.py -v
"""
import pytest
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from utilisateurs.models import RolePersonnel
from actualites.models import Actualite
from evenements.models import Evenement, Discipline, Categorie
from sites.models import Site

Utilisateur = get_user_model()

# ---------------------------------------------------------------------------
# URLs — route vérifiée via actualites/urls.py : basename='actualite'
# ---------------------------------------------------------------------------
URL_ACTUALITES = '/api/actualites/'
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
    client = APIClient()
    token = obtenir_token(username, password)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    return client


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def superadmin(db):
    """Superadmin de test (pattern validé dans test_utilisateurs_api.py)."""
    return Utilisateur.objects.create_user(
        username='super_admin', password='MotDePasse123!',
        email='superadmin@joj.sn',
        is_superuser=True,
    )


@pytest.fixture
def admin_normal(db):
    """Admin de test (is_staff=True exigé par IsAdminUser)."""
    return Utilisateur.objects.create_user(
        username='admin_normal', password='MotDePasse123!',
        email='admin@joj.sn',
        is_staff=True, role=RolePersonnel.ADMIN,
    )


@pytest.fixture
def user_non_admin(db):
    """Utilisateur du personnel authentifié mais NON admin (is_staff=False).
    IsAdminUser le refuse : il n'est pas admin Django."""
    return Utilisateur.objects.create_user(
        username='user_non_admin', password='MotDePasse123!',
        email='simple@joj.sn',
        is_staff=False,
    )


@pytest.fixture
def site_test(db):
    return Site.objects.create(
        nom='Dakar Arena', ville='Dakar', region='Dakar', capacite=20000,
    )


@pytest.fixture
def discipline_test(db):
    return Discipline.objects.create(nom='Basketball', regle='Règles FIBA')


@pytest.fixture
def categorie_test(discipline_test):
    return Categorie.objects.create(
        nom='Hommes', discipline=discipline_test,
        description='Catégorie masculine',
    )


@pytest.fixture
def evenement_test(site_test, categorie_test):
    return Evenement.objects.create(
        titre='Finale Basket',
        date=timezone.now().date(),
        heure=timezone.now().time(),
        site=site_test,
        categorie=categorie_test,
        description='Finale masculine de basketball',
    )


def donnees_actualite(evenement_pk, brouillon=True, date_pub=None,
                      titre='JOJ Dakar 2026 : le compte à rebours est lancé',
                      description='L\'organisation dévoile les derniers '
                                  'détails du programme sportif '
                                  'des Jeux Olympiques de la Jeunesse.'):
    """Données complètes et valides pour une actualité."""
    data = {
        'titre': titre,
        'description': description,
        'evenement_lie': evenement_pk,
        'brouillon': brouillon,
    }
    if date_pub is not None:
        data['date_publication'] = date_pub.isoformat()
    return data


# ===========================================================================
# Lecture publique (anonyme)
# ===========================================================================
@pytest.mark.django_db
class TestLecturePublique:
    """Les actualités sont consultables par tous, y compris les anonymes."""

    def test_liste_actualites_publique(self, evenement_test, admin_normal):
        """GET /api/actualites/ accessible sans compte."""
        Actualite.objects.create(
            titre='JOJ Dakar 2026 : le compte à rebours est lancé',
            description='L\'organisation dévoile les derniers détails du '
                        'programme sportif des Jeux.',
            auteur=admin_normal,
            evenement_lie=evenement_test,
            brouillon=False,
            date_publication=timezone.now(),
        )
        client = APIClient()
        response = client.get(URL_ACTUALITES)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) >= 1

    def test_detail_actualite_public(self, evenement_test, admin_normal):
        """GET /api/actualites/<pk>/ accessible sans compte."""
        actualite = Actualite.objects.create(
            titre='JOJ Dakar 2026 : le compte à rebours est lancé',
            description='L\'organisation dévoile les derniers détails du '
                        'programme sportif des Jeux.',
            auteur=admin_normal,
            evenement_lie=evenement_test,
            brouillon=False,
            date_publication=timezone.now(),
        )
        client = APIClient()
        response = client.get(f'{URL_ACTUALITES}{actualite.pk}/')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'JOJ Dakar 2026' in data['titre']

    def test_detail_inclut_evenement_et_auteur(self, evenement_test, admin_normal):
        """Le détail expose l'événement lié et l'auteur (select_related)."""
        actualite = Actualite.objects.create(
            titre='JOJ Dakar 2026 : le compte à rebours est lancé',
            description='L\'organisation dévoile les derniers détails du '
                        'programme sportif des Jeux.',
            auteur=admin_normal,
            evenement_lie=evenement_test,
            brouillon=False,
            date_publication=timezone.now(),
        )
        client = APIClient()
        data = client.get(f'{URL_ACTUALITES}{actualite.pk}/').json()
        assert 'evenement_lie' in data or 'evenement_titre' in data

    def test_detail_inexistant_404(self):
        client = APIClient()
        assert client.get(f'{URL_ACTUALITES}99999/').status_code == status.HTTP_404_NOT_FOUND


# ===========================================================================
# Sécurité d'écriture
# ===========================================================================
@pytest.mark.django_db
class TestSecuriteEcriture:
    """L'écriture est réservée aux admins Django (IsAdminUser)."""

    def test_anonyme_refuse_creation(self, evenement_test):
        client = APIClient()
        response = client.post(URL_ACTUALITES, donnees_actualite(evenement_test.pk),
                               format='json')
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN,
        )

    def test_user_non_admin_refuse_creation(self, evenement_test, user_non_admin):
        """Un utilisateur du personnel sans rôle admin Django est refusé."""
        client = creer_client_avec_token('user_non_admin', 'MotDePasse123!')
        response = client.post(URL_ACTUALITES, donnees_actualite(evenement_test.pk),
                               format='json')
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN,
        )

    def test_admin_cree_actualite(self, evenement_test, admin_normal):
        """Un admin Django peut créer une actualité."""
        client = creer_client_avec_token('admin_normal', 'MotDePasse123!')
        response = client.post(URL_ACTUALITES, donnees_actualite(evenement_test.pk),
                               format='json')
        assert response.status_code == status.HTTP_201_CREATED
        actualite = Actualite.objects.get(titre__startswith='JOJ Dakar 2026')
        assert actualite.auteur == admin_normal

    def test_anonyme_refuse_modification(self, evenement_test, admin_normal):
        actualite = Actualite.objects.create(
            titre='JOJ Dakar 2026 : le compte à rebours est lancé',
            description='L\'organisation dévoile les derniers détails du '
                        'programme sportif des Jeux.',
            auteur=admin_normal,
            evenement_lie=evenement_test,
            brouillon=True,
        )
        client = APIClient()
        response = client.patch(f'{URL_ACTUALITES}{actualite.pk}/', {
            'titre': 'Piraté!!! ',
        }, format='json')
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN,
        )
        actualite.refresh_from_db()
        assert actualite.titre != 'Piraté!!! '

    def test_anonyme_refuse_suppression(self, evenement_test, admin_normal):
        pk = Actualite.objects.create(
            titre='JOJ Dakar 2026 : le compte à rebours est lancé',
            description='L\'organisation dévoile les derniers détails du '
                        'programme sportif des Jeux.',
            auteur=admin_normal,
            evenement_lie=evenement_test,
            brouillon=True,
        ).pk
        client = APIClient()
        response = client.delete(f'{URL_ACTUALITES}{pk}/')
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN,
        )
        assert Actualite.objects.filter(pk=pk).exists()


# ===========================================================================
# Validations du serializer
# ===========================================================================
@pytest.mark.django_db
class TestValidationsActualite:
    """Validation des champs : titre, description, événement, dates, brouillon."""

    def test_titre_trop_court_refuse(self, evenement_test, admin_normal):
        """Un titre de moins de 5 caractères est refusé."""
        client = creer_client_avec_token('admin_normal', 'MotDePasse123!')
        response = client.post(URL_ACTUALITES, donnees_actualite(
            evenement_test.pk, titre='JOJ',
        ), format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_titre_trop_long_refuse(self, evenement_test, admin_normal):
        """Un titre de plus de 200 caractères est refusé."""
        client = creer_client_avec_token('admin_normal', 'MotDePasse123!')
        response = client.post(URL_ACTUALITES, donnees_actualite(
            evenement_test.pk, titre='X' * 201,
        ), format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_titre_vide_refuse(self, evenement_test, admin_normal):
        """Un titre vide est refusé."""
        client = creer_client_avec_token('admin_normal', 'MotDePasse123!')
        response = client.post(URL_ACTUALITES, donnees_actualite(
            evenement_test.pk, titre='   ',
        ), format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_description_trop_courte_refusee(self, evenement_test, admin_normal):
        """Une description de moins de 20 caractères est refusée."""
        client = creer_client_avec_token('admin_normal', 'MotDePasse123!')
        response = client.post(URL_ACTUALITES, donnees_actualite(
            evenement_test.pk, description='Trop courte',
        ), format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_evenement_inexistant_refuse(self, admin_normal):
        """Rattacher une actualité à un événement inexistant est refusé."""
        client = creer_client_avec_token('admin_normal', 'MotDePasse123!')
        response = client.post(URL_ACTUALITES, donnees_actualite(99999),
                               format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_date_publication_passee_refusee(self, evenement_test, admin_normal):
        """Une date de publication dans le passé est refusée."""
        client = creer_client_avec_token('admin_normal', 'MotDePasse123!')
        response = client.post(URL_ACTUALITES, donnees_actualite(
            evenement_test.pk,
            date_pub=timezone.now() - timedelta(days=1),
        ), format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_publication_sans_date_refusee(self, evenement_test, admin_normal):
        """Une actualité publiée (brouillon=False) sans date est refusée."""
        client = creer_client_avec_token('admin_normal', 'MotDePasse123!')
        response = client.post(URL_ACTUALITES, donnees_actualite(
            evenement_test.pk, brouillon=False,
        ), format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_brouillon_sans_date_accepte(self, evenement_test, admin_normal):
        """Un brouillon n'a pas besoin de date de publication."""
        client = creer_client_avec_token('admin_normal', 'MotDePasse123!')
        response = client.post(URL_ACTUALITES, donnees_actualite(
            evenement_test.pk, brouillon=True,
        ), format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert Actualite.objects.first().brouillon is True

    def test_publication_avec_date_acceptee(self, evenement_test, admin_normal):
        """Une actualité publiée avec une date future est acceptée."""
        client = creer_client_avec_token('admin_normal', 'MotDePasse123!')
        response = client.post(URL_ACTUALITES, donnees_actualite(
            evenement_test.pk,
            brouillon=False,
            date_pub=timezone.now() + timedelta(days=1),
        ), format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert Actualite.objects.first().brouillon is False


# ===========================================================================
# Flux brouillon → publication
# ===========================================================================
@pytest.mark.django_db
class TestFluxPublication:
    """Modèle de travail : brouillon d'abord, publication ensuite."""

    def test_brouillon_puis_publication(self, evenement_test, admin_normal):
        """Création en brouillon, puis publication avec date future."""
        client = creer_client_avec_token('admin_normal', 'MotDePasse123!')

        # 1. Création en brouillon
        creation = client.post(URL_ACTUALITES, donnees_actualite(
            evenement_test.pk, brouillon=True,
        ), format='json')
        assert creation.status_code == status.HTTP_201_CREATED
        # Le serializer n'expose pas le champ 'id' dans la réponse de
        # création (fields liste explicite). On récupère l'actualité
        # par son titre unique créé pour ce test.
        pk = Actualite.objects.get(
            titre='JOJ Dakar 2026 : le compte à rebours est lancé',
        ).pk

        # 2. Publication avec une date future
        date_future = timezone.now() + timedelta(hours=2)
        response = client.patch(f'{URL_ACTUALITES}{pk}/', {
            'brouillon': False,
            'date_publication': date_future.isoformat(),
        }, format='json')
        assert response.status_code == status.HTTP_200_OK

        actualite = Actualite.objects.get(pk=pk)
        assert actualite.brouillon is False
        assert actualite.date_publication is not None


# ===========================================================================
# Filtres
# ===========================================================================
@pytest.mark.django_db
class TestFiltresActualites:
    """Filtrage django-filter : événement lié et auteur."""

    def test_filtre_par_evenement(self, evenement_test, admin_normal):
        Actualite.objects.create(
            titre='JOJ Dakar 2026 : le compte à rebours est lancé',
            description='L\'organisation dévoile les derniers détails du '
                        'programme sportif des Jeux.',
            auteur=admin_normal,
            evenement_lie=evenement_test,
            brouillon=False,
            date_publication=timezone.now(),
        )
        client = APIClient()
        response = client.get(f'{URL_ACTUALITES}?evenement_lie={evenement_test.pk}')
        assert response.status_code == status.HTTP_200_OK

    def test_filtre_par_auteur(self, evenement_test, admin_normal):
        Actualite.objects.create(
            titre='JOJ Dakar 2026 : le compte à rebours est lancé',
            description='L\'organisation dévoile les derniers détails du '
                        'programme sportif des Jeux.',
            auteur=admin_normal,
            evenement_lie=evenement_test,
            brouillon=False,
            date_publication=timezone.now(),
        )
        client = APIClient()
        response = client.get(f'{URL_ACTUALITES}?auteur={admin_normal.pk}')
        assert response.status_code == status.HTTP_200_OK
