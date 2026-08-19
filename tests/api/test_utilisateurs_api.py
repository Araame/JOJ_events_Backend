"""
Tests unitaires des endpoints de l'application utilisateurs.

Couvre 8 views :
- CreerSuperAdminView   : POST /api/utilisateurs/creer-superadmin/
- CreerAdminView        : POST /api/utilisateurs/creer-admin/
- ListeUtilisateursView : GET  /api/utilisateurs/liste/
- ProfilUtilisateurView : GET/PUT /api/utilisateurs/profil/
- ChangerMotDePasseView : PUT  /api/utilisateurs/changer-mot-de-passe/
- DeconnexionView       : POST /api/utilisateurs/deconnexion/
- RevoquerAccesView     : POST /api/utilisateurs/revoquer/<id>/
- ReactiverAccesView    : POST /api/utilisateurs/reactiver/<id>/

Scénarios de sécurité testés :
- Anonyme refusé sur les endpoints protégés
- Admin ordinaire ne peut PAS créer de superadmin
- Seul un superadmin peut créer des admins
- Mots de passe faibles refusés
- Mots de passe qui ne correspondent pas
- Révocation d'un superadmin interdite
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from utilisateurs.models import RolePersonnel, PermissionApp

Utilisateur = get_user_model()

# ---------------------------------------------------------------------------
# URLs des endpoints — à ADAPTER selon vos routes réelles dans urls.py
# ---------------------------------------------------------------------------
URL_CREER_SUPERADMIN = '/api/utilisateurs/creer-superadmin/'
URL_CREER_ADMIN = '/api/utilisateurs/creer-admin/'
URL_LISTE = '/api/utilisateurs/utilisateurs/'   # path('utilisateurs/', ListeUtilisateursView) dans urls.py
URL_PROFIL = '/api/utilisateurs/profil/'
URL_CHANGER_MDP = '/api/utilisateurs/changer-mot-de-passe/'
URL_DECONNEXION = '/api/utilisateurs/deconnexion/'
URL_REVOQUER = '/api/utilisateurs/revoquer-acces/{}/'
URL_REACTIVER = '/api/utilisateurs/reactiver-acces/{}/'

# ---------------------------------------------------------------------------
# URLs JWT — à adapter selon vos routes réelles (utilisateurs/urls.py)
# Vos routes actuelles : 'rafraichir-token/' et 'verifier-token/'
# Il manque 'obtenir-token/' (TokenObtainPairView) et 'blacklist-token/'
# (TokenBlacklistView) — voir le guide de correction fourni.
# ---------------------------------------------------------------------------
URL_TOKEN = '/api/utilisateurs/connexion/'          # JWT : POST username/password (TokenObtainPairView)
URL_TOKEN_REFRESH = '/api/utilisateurs/rafraichir-token/'


def obtenir_token(client, username, password):
    """Obtient un access + refresh token JWT pour un utilisateur.

    Échoue avec un message clair si la route JWT est introuvable
    (au lieu de l'erreur cryptique 'Content-Type text/html').
    """
    response = client.post(URL_TOKEN, {
        'username': username,
        'password': password,
    })
    if response.status_code != status.HTTP_200_OK:
        raise RuntimeError(
            f"Impossible d'obtenir un token JWT pour '{username}' sur {URL_TOKEN} "
            f"(code {response.status_code}, Content-Type: "
            f"{response.headers.get('Content-Type')}). "
            "Vérifiez que la route 'connexion/' existe dans vos urls.py "
            "et qu'elle pointe vers TokenObtainPairView (voir le guide fourni)."
        )
    return response.data['access'], response.data['refresh']


def client_authentifie(client, username, password):
    """Retourne un APIClient authentifié avec JWT."""
    client = APIClient()
    access, _ = obtenir_token(client, username, password)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
    return client


def donnees_utilisateur(prefixe, role_permissions=None, password='MotDePasse123!'):
    """Données complètes et valides pour créer un utilisateur."""
    data = {
        'username': f'{prefixe}_user',
        'email': f'{prefixe}@joj-test.sn',
        'first_name': 'Prenom',
        'last_name': 'Nom',
        'tel': '770000000',
        'password': password,
        'password2': password,
    }
    if role_permissions is not None:
        data['permissions_app'] = role_permissions
    return data


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
@pytest.mark.api
@pytest.mark.django_db
class TestCreerSuperAdmin:
    """POST /api/utilisateurs/creer-superadmin/"""

    def test_premier_superadmin_cree_librement(self):
        """Sans superadmin existant, la création est libre (AllowAny)."""
        client = APIClient()
        assert Utilisateur.objects.filter(is_superuser=True).count() == 0

        response = client.post(URL_CREER_SUPERADMIN, donnees_utilisateur('premier'))

        assert response.status_code == status.HTTP_201_CREATED
        assert Utilisateur.objects.get(username='premier_user').is_superuser

    def test_anonyme_refuse_si_superadmin_existant(self):
        """Si un superadmin existe déjà, l'anonyme est refusé (403)."""
        Utilisateur.objects.create_user(
            username='super_admin', password='MotDePasse123!',
            is_superuser=True,
        )
        client = APIClient()

        response = client.post(URL_CREER_SUPERADMIN, donnees_utilisateur('deuxieme'))

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert Utilisateur.objects.filter(username='deuxieme_user').count() == 0

    def test_admin_refuse_si_superadmin_existant(self):
        """Un simple ADMIN ne peut pas créer de superadmin (403)."""
        superadmin = Utilisateur.objects.create_user(
            username='super_admin', password='MotDePasse123!',
            is_superuser=True,
        )
        admin = Utilisateur.objects.create_user(
            username='admin_normal', password='MotDePasse123!',
            is_staff=True, role=RolePersonnel.ADMIN,
        )
        client = client_authentifie(APIClient(), 'admin_normal', 'MotDePasse123!')

        response = client.post(URL_CREER_SUPERADMIN, donnees_utilisateur('non_allowed'))

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_superadmin_peut_creer_un_autre_superadmin(self):
        """Un superadmin connecté peut créer un second superadmin."""
        Utilisateur.objects.create_user(
            username='super_admin', password='MotDePasse123!',
            is_superuser=True,
        )
        client = client_authentifie(APIClient(), 'super_admin', 'MotDePasse123!')

        response = client.post(URL_CREER_SUPERADMIN, donnees_utilisateur('deuxieme'))

        assert response.status_code == status.HTTP_201_CREATED
        nouveau = Utilisateur.objects.get(username='deuxieme_user')
        assert nouveau.is_superuser
        assert nouveau.role == RolePersonnel.SUPERADMIN

    def test_superadmin_role_et_permissions_imposés(self):
        """Le save() du modèle force role=SUPERADMIN et permissions=[TOUT]."""
        client = APIClient()
        client.post(URL_CREER_SUPERADMIN, donnees_utilisateur('test_role'))

        user = Utilisateur.objects.get(username='test_role_user')
        assert user.role == RolePersonnel.SUPERADMIN
        assert PermissionApp.TOUT in user.permissions_app

    def test_mots_de_passe_non_correspondants(self):
        """password != password2 → 400."""
        client = APIClient()
        data = donnees_utilisateur('test_mdp')
        data['password2'] = 'AutreMotDePasse123!'

        response = client.post(URL_CREER_SUPERADMIN, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_mot_de_passe_faible_refuse(self):
        """Un mot de passe trop simple est refusé par validate_password."""
        client = APIClient()
        data = donnees_utilisateur('test_faible')
        data['password'] = data['password2'] = '123'

        response = client.post(URL_CREER_SUPERADMIN, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert Utilisateur.objects.filter(username='test_faible_user').count() == 0

    def test_email_manquant_refuse(self):
        """L'email est obligatoire (required=True)."""
        client = APIClient()
        data = donnees_utilisateur('test_email')
        del data['email']

        response = client.post(URL_CREER_SUPERADMIN, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.api
@pytest.mark.django_db
class TestCreerAdmin:
    """POST /api/utilisateurs/creer-admin/"""

    def setup_method(self):
        self.superadmin = Utilisateur.objects.create_user(
            username='super_admin', password='MotDePasse123!',
            is_superuser=True,
        )

    def test_superadmin_cree_admin_avec_permissions(self):
        """Un superadmin crée un admin avec la liste de permissions voulue."""
        client = client_authentifie(APIClient(), 'super_admin', 'MotDePasse123!')
        data = donnees_utilisateur(
            'nouvel_admin',
            role_permissions=[PermissionApp.SITES, PermissionApp.BILLETS],
        )

        response = client.post(URL_CREER_ADMIN, data)

        assert response.status_code == status.HTTP_201_CREATED
        admin = Utilisateur.objects.get(username='nouvel_admin_user')
        assert admin.is_staff
        assert not admin.is_superuser
        assert PermissionApp.SITES in admin.permissions_app
        assert PermissionApp.BILLETS in admin.permissions_app

    def test_admin_ordinnaire_ne_peut_pas_creer_admin(self):
        """Un ADMIN sans EstSuperAdmin est refusé (403)."""
        admin = Utilisateur.objects.create_user(
            username='admin_normal', password='MotDePasse123!',
            is_staff=True, role=RolePersonnel.ADMIN,
        )
        client = client_authentifie(APIClient(), 'admin_normal', 'MotDePasse123!')
        data = donnees_utilisateur('non_allowed', role_permissions=[PermissionApp.ZONES])

        response = client.post(URL_CREER_ADMIN, data)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert Utilisateur.objects.filter(username='non_allowed_user').count() == 0

    def test_anonyme_refuse(self):
        """L'anonyme ne peut pas créer d'admin (401)."""
        client = APIClient()
        data = donnees_utilisateur('non_allowed', role_permissions=[PermissionApp.ZONES])

        response = client.post(URL_CREER_ADMIN, data)

        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN,
        )

    def test_permissions_app_manquantes_refusees(self):
        """permissions_app est requis et ne peut pas être vide."""
        client = client_authentifie(APIClient(), 'super_admin', 'MotDePasse123!')
        data = donnees_utilisateur('non_allowed')
        # retirer permissions_app

        response = client.post(URL_CREER_ADMIN, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_permissions_app_vide_refusee(self):
        """allow_empty=False : liste vide refusée."""
        client = client_authentifie(APIClient(), 'super_admin', 'MotDePasse123!')
        data = donnees_utilisateur('non_allowed', role_permissions=[])

        response = client.post(URL_CREER_ADMIN, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_permission_invalide_refusee(self):
        """Une valeur hors de PermissionApp.choices est refusée."""
        client = client_authentifie(APIClient(), 'super_admin', 'MotDePasse123!')
        data = donnees_utilisateur('non_allowed', role_permissions=['PERMISSION_INEXISTANTE'])

        response = client.post(URL_CREER_ADMIN, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.api
@pytest.mark.django_db
class TestListeUtilisateurs:
    """GET /api/utilisateurs/liste/"""

    def setup_method(self):
        self.superadmin = Utilisateur.objects.create_user(
            username='super_admin', password='MotDePasse123!',
            is_superuser=True,
        )
        self.admin = Utilisateur.objects.create_user(
            username='admin_normal', password='MotDePasse123!',
            is_staff=True, role=RolePersonnel.ADMIN,
        )

    def test_superadmin_voit_les_admins(self):
        """Le superadmin voit au minimum les utilisateurs créés par le setup."""
        from django.contrib.auth import get_user_model
        User = get_user_model()

        nb_admins_creés = User.objects.filter(role='ADMIN').count()

        client = client_authentifie(APIClient(), 'super_admin', 'MotDePasse123!')
        response = client.get(URL_LISTE)

        assert response.status_code == status.HTTP_200_OK

        donnees = response.data['results'] if isinstance(response.data, dict) else response.data
        assert len(donnees) >= nb_admins_creés

        # Tous les admins de la base sont bien dans la réponse :
        noms = {u['username'] for u in donnees}
        for admin in User.objects.filter(role='ADMIN'):
            assert admin.username in noms

        
    def test_admin_refuse(self):
        """Un simple ADMIN ne voit pas la liste (403)."""
        client = client_authentifie(APIClient(), 'admin_normal', 'MotDePasse123!')

        response = client.get(URL_LISTE)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_anonyme_refuse(self):
        """L'anonyme n'a pas accès (401)."""
        client = APIClient()

        response = client.get(URL_LISTE)

        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN,
        )


@pytest.mark.api
@pytest.mark.django_db
class TestProfilUtilisateur:
    """GET + PUT /api/utilisateurs/profil/"""

    def setup_method(self):
        self.admin = Utilisateur.objects.create_user(
            username='admin_profil', password='MotDePasse123!',
            is_staff=True, role=RolePersonnel.ADMIN,
        )

    def test_get_profil_sois_meme(self):
        """L'utilisateur authentifié récupère son propre profil."""
        client = client_authentifie(APIClient(), 'admin_profil', 'MotDePasse123!')

        response = client.get(URL_PROFIL)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['username'] == 'admin_profil'
        assert response.data['role'] == RolePersonnel.ADMIN
        # Champs read-only présents
        assert 'date_joined' in response.data
        assert 'is_active' in response.data

    def test_put_modifier_email(self):
        """Mise à jour partielle de l'email."""
        client = client_authentifie(APIClient(), 'admin_profil', 'MotDePasse123!')

        response = client.put(URL_PROFIL, {'email': 'nouvel@email.sn'})

        assert response.status_code == status.HTTP_200_OK
        self.admin.refresh_from_db()
        assert self.admin.email == 'nouvel@email.sn'

    def test_put_ne_peut_pas_modifier_son_role(self):
        """Le rôle est read_only : une tentative est ignorée."""
        client = client_authentifie(APIClient(), 'admin_profil', 'MotDePasse123!')

        response = client.put(URL_PROFIL, {'role': RolePersonnel.SUPERADMIN})

        assert response.status_code == status.HTTP_200_OK
        self.admin.refresh_from_db()
        assert self.admin.role == RolePersonnel.ADMIN   # inchangé

    def test_anonyme_refuse_profil(self):
        """L'anonyme ne peut pas voir un profil (401)."""
        client = APIClient()

        response = client.get(URL_PROFIL)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.api
@pytest.mark.django_db
class TestChangerMotDePasse:
    """PUT /api/utilisateurs/changer-mot-de-passe/"""

    def setup_method(self):
        self.admin = Utilisateur.objects.create_user(
            username='admin_mdp', password='MotDePasse123!',
            is_staff=True, role=RolePersonnel.ADMIN,
        )

    def test_changement_reussi(self):
        """Ancien mot de passe correct → mot de passe changé."""
        client = client_authentifie(APIClient(), 'admin_mdp', 'MotDePasse123!')

        response = client.put(URL_CHANGER_MDP, {
            'ancien_mot_de_passe': 'MotDePasse123!',
            'nouveau_mot_de_passe': 'NouveauMotDePasse456!',
            'confirmation_nouveau_mot_de_passe': 'NouveauMotDePasse456!',
        })

        assert response.status_code == status.HTTP_200_OK
        self.admin.refresh_from_db()
        assert self.admin.check_password('NouveauMotDePasse456!')

    def test_ancien_mot_de_passe_incorrect(self):
        """Ancien mot de passe faux → 400."""
        client = client_authentifie(APIClient(), 'admin_mdp', 'MotDePasse123!')

        response = client.put(URL_CHANGER_MDP, {
            'ancien_mot_de_passe': 'MauvaisMotDePasse!',
            'nouveau_mot_de_passe': 'NouveauMotDePasse456!',
            'confirmation_nouveau_mot_de_passe': 'NouveauMotDePasse456!',
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        self.admin.refresh_from_db()
        assert self.admin.check_password('MotDePasse123!')   # inchangé

    def test_nouveaux_mots_de_passe_non_correspondants(self):
        """nouveau != confirmation → 400."""
        client = client_authentifie(APIClient(), 'admin_mdp', 'MotDePasse123!')

        response = client.put(URL_CHANGER_MDP, {
            'ancien_mot_de_passe': 'MotDePasse123!',
            'nouveau_mot_de_passe': 'NouveauMotDePasse456!',
            'confirmation_nouveau_mot_de_passe': 'AutreMotDePasse789!',
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_nouveau_mot_de_passe_faible_refuse(self):
        """Un mot de passe faible (validator Django) est refusé."""
        client = client_authentifie(APIClient(), 'admin_mdp', 'MotDePasse123!')

        response = client.put(URL_CHANGER_MDP, {
            'ancien_mot_de_passe': 'MotDePasse123!',
            'nouveau_mot_de_passe': '123',
            'confirmation_nouveau_mot_de_passe': '123',
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.api
@pytest.mark.django_db
class TestDeconnexion:
    """POST /api/utilisateurs/deconnexion/"""

    def setup_method(self):
        self.admin = Utilisateur.objects.create_user(
            username='admin_deco', password='MotDePasse123!',
            is_staff=True, role=RolePersonnel.ADMIN,
        )

    def test_deconnexion_reussi(self):
        """Invalider un refresh token valide → 200 et token blacklisté."""
        client = APIClient()
        _, refresh = obtenir_token(client, 'admin_deco', 'MotDePasse123!')
        auth_client = client_authentifie(APIClient(), 'admin_deco', 'MotDePasse123!')

        response = auth_client.post(URL_DECONNEXION, {'refresh': refresh})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['message'] == 'Deconnecte avec succes'

    def test_refresh_token_manquant(self):
        """Refresh token absent → 400."""
        auth_client = client_authentifie(APIClient(), 'admin_deco', 'MotDePasse123!')

        response = auth_client.post(URL_DECONNEXION, {})

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_token_invalide_refuse(self):
        """Un refresh token invalide → 400."""
        auth_client = client_authentifie(APIClient(), 'admin_deco', 'MotDePasse123!')

        response = auth_client.post(URL_DECONNEXION, {'refresh': 'token_invalide'})

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_anonyme_refuse(self):
        """L'anonyme ne peut pas se déconnecter (401)."""
        client = APIClient()

        response = client.post(URL_DECONNEXION, {'refresh': 'un_token'})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.api
@pytest.mark.django_db
class TestRevoquerAcces:
    """POST /api/utilisateurs/revoquer/<id>/"""

    def setup_method(self):
        self.superadmin = Utilisateur.objects.create_user(
            username='super_admin', password='MotDePasse123!',
            is_superuser=True,
        )
        self.admin = Utilisateur.objects.create_user(
            username='admin_victime', password='MotDePasse123!',
            is_staff=True, role=RolePersonnel.ADMIN, is_active=True,
        )
        # Admin ACTIF servant à prouver que le refus vient de la permission
        # (un admin is_active=False ne peut pas obtenir de token JWT)
        self.admin_temoin = Utilisateur.objects.create_user(
            username='admin_temoin', password='MotDePasse123!',
            is_staff=True, role=RolePersonnel.ADMIN, is_active=True,
        )

    def test_superadmin_revoque_acces_admin(self):
        """Révocation d'un admin → is_active=False."""
        client = client_authentifie(APIClient(), 'super_admin', 'MotDePasse123!')

        response = client.post(URL_REVOQUER.format(self.admin.id))

        assert response.status_code == status.HTTP_200_OK
        self.admin.refresh_from_db()
        assert not self.admin.is_active
        assert 'admin_victime' in response.data['message']

    def test_superadmin_ne_peut_pas_revoquer_superadmin(self):
        """Révoquer un superadmin → 403 (protection)."""
        autre_superadmin = Utilisateur.objects.create_user(
            username='autre_super', password='MotDePasse123!',
            is_superuser=True,
        )
        client = client_authentifie(APIClient(), 'super_admin', 'MotDePasse123!')

        response = client.post(URL_REVOQUER.format(autre_superadmin.id))

        assert response.status_code == status.HTTP_403_FORBIDDEN
        autre_superadmin.refresh_from_db()
        assert autre_superadmin.is_active   # toujours actif

    def test_utilisateur_inexistant_404(self):
        """ID inexistant → 404."""
        client = client_authentifie(APIClient(), 'super_admin', 'MotDePasse123!')

        response = client.post(URL_REVOQUER.format(99999))

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_admin_refuse_revoquer(self):
        """Un simple ADMIN ne peut pas révoquer (403)."""
        client = client_authentifie(APIClient(), 'admin_temoin', 'MotDePasse123!')

        response = client.post(URL_REVOQUER.format(self.admin.id))

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.api
@pytest.mark.django_db
class TestReactiverAcces:
    """POST /api/utilisateurs/reactiver/<id>/"""

    def setup_method(self):
        self.superadmin = Utilisateur.objects.create_user(
            username='super_admin', password='MotDePasse123!',
            is_superuser=True,
        )
        self.admin = Utilisateur.objects.create_user(
            username='admin_victime', password='MotDePasse123!',
            is_staff=True, role=RolePersonnel.ADMIN, is_active=False,
        )
        # Admin ACTIF servant à prouver que le refus vient de la permission
        # (un admin is_active=False ne peut pas obtenir de token JWT)
        self.admin_temoin = Utilisateur.objects.create_user(
            username='admin_temoin', password='MotDePasse123!',
            is_staff=True, role=RolePersonnel.ADMIN, is_active=True,
        )

    def test_superadmin_reactive_admin(self):
        """Réactivation → is_active=True."""
        client = client_authentifie(APIClient(), 'super_admin', 'MotDePasse123!')

        response = client.post(URL_REACTIVER.format(self.admin.id))

        assert response.status_code == status.HTTP_200_OK
        self.admin.refresh_from_db()
        assert self.admin.is_active

    def test_utilisateur_inexistant_404(self):
        """ID inexistant → 404."""
        client = client_authentifie(APIClient(), 'super_admin', 'MotDePasse123!')

        response = client.post(URL_REACTIVER.format(99999))

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_admin_refuse_reactiver(self):
        """Un simple ADMIN ne peut pas réactiver (403)."""
        client = client_authentifie(APIClient(), 'admin_temoin', 'MotDePasse123!')

        response = client.post(URL_REACTIVER.format(self.admin.id))

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.api
@pytest.mark.django_db
class TestPermissionsModele:
    """Tests du modèle Personnel : has_permission()."""

    def test_superadmin_a_toutes_permissions(self):
        user = Utilisateur.objects.create_user(
            username='super_p', password='MotDePasse123!',
            is_superuser=True,
        )
        assert user.has_permission('PERMISSION_QUELCONQUE')

    def test_admin_limited_par_permissions_app(self):
        user = Utilisateur.objects.create_user(
            username='admin_p', password='MotDePasse123!',
            is_staff=True, role=RolePersonnel.ADMIN,
            permissions_app=[PermissionApp.SITES],
        )
        assert user.has_permission(PermissionApp.SITES)
        assert not user.has_permission(PermissionApp.BILLETS)

    def test_admin_avec_TOUT_a_toutes_permissions(self):
        user = Utilisateur.objects.create_user(
            username='admin_tout', password='MotDePasse123!',
            is_staff=True, role=RolePersonnel.ADMIN,
            permissions_app=[PermissionApp.TOUT],
        )
        assert user.has_permission(PermissionApp.ZONES)

    def test_role_impose_par_save_superadmin(self):
        """Créer un superuser force role=SUPERADMIN et permissions=[TOUT]."""
        user = Utilisateur.objects.create_superuser(
            username='super_p2', password='MotDePasse123!',
        )
        assert user.role == RolePersonnel.SUPERADMIN
        assert user.permissions_app == [PermissionApp.TOUT]
