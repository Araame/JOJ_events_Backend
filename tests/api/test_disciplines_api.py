import pytest
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from evenements.models import Discipline, Categorie

Personnel = get_user_model()


@pytest.mark.api
@pytest.mark.django_db
class TestDisciplinesAPI(APITestCase):
    """
    Tests de l'API publique des disciplines olympiques.
    Cette API est en lecture seule (ReadOnlyModelViewSet) :
    les spectateurs anonymes peuvent consulter, mais personne
    ne peut créer ou supprimer via cette API.
    """

    def setUp(self):
        """Créer des données de test."""
        self.discipline = Discipline.objects.create(
            nom='Athlétisme',
            regle="Règles de l'athlétisme JOJ",
            accessibilite='Tous publics'
        )
        self.categorie = Categorie.objects.create(
            nom='100m hommes',
            description='Sprint 100 mètres',
            discipline=self.discipline
        )

    # ---- CONSULTATION PUBLIQUE (spectateur anonyme) ----

    def test_liste_disciplines_anonyme_ok(self):
        """Un spectateur anonyme peut consulter la liste des disciplines."""
        response = self.client.get('/api/disciplines/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) >= 1

    def test_detail_discipline_par_id(self):
        """Un spectateur anonyme peut consulter une discipline par son ID."""
        response = self.client.get(f'/api/disciplines/{self.discipline.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['nom'] == 'Athlétisme'

    def test_discipline_inexistante_404(self):
        """Une discipline inexistante retourne une 404."""
        response = self.client.get('/api/disciplines/999/')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_categories_d_une_discipline(self):
        """Un spectateur peut consulter les catégories d'une discipline."""
        response = self.client.get(f'/api/disciplines/{self.discipline.id}/categories/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) >= 1

    def test_affichage_nom_discipline(self):
        """Le nom de la discipline apparaît dans la réponse JSON."""
        response = self.client.get('/api/disciplines/')
        noms = [d['nom'] for d in response.json()]
        assert 'Athlétisme' in noms

    # ---- SÉCURITÉ : API EN LECTURE SEULE ----

    def test_creation_discipline_interdite(self):
        """L'API publique est en lecture seule.
        Un anonyme reçoit 401, un admin authentifié reçoit 405."""
        response = self.client.post('/api/disciplines/', {'nom': 'Natation'})
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )
        
        assert not Discipline.objects.filter(nom='Natation').exists()


    def test_creation_discipline_interdite_meme_admin(self):
        """Même un personnel authentifié ne peut pas créer via l'API publique."""
        admin = Personnel.objects.create_user(
            username='admin_test',
            password='MotDePasse123!',
            role='ADMIN'
        )
        self.client.force_authenticate(user=admin)

        response = self.client.post('/api/disciplines/', {'nom': 'Natation'})
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_suppression_discipline_interdite(self):
        """La suppression n'est pas possible via l'API publique."""
        admin = Personnel.objects.create_user(
            username='admin_test2',
            password='MotDePasse123!',
            role='ADMIN'
        )
        self.client.force_authenticate(user=admin)

        response = self.client.delete(f'/api/disciplines/{self.discipline.id}/')
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

        # Vérifier que la discipline existe toujours
        assert Discipline.objects.filter(pk=self.discipline.pk).exists()


@pytest.mark.api
@pytest.mark.django_db
class TestCategoriesAPI(APITestCase):
    """Tests de l'API publique des catégories d'épreuves."""

    def setUp(self):
        self.discipline = Discipline.objects.create(
            nom='Natation',
            regle="Règles de la natation JOJ",
            accessibilite='Tous publics'
        )
        self.categorie = Categorie.objects.create(
            nom='100m nage libre',
            description='Nage libre 100 mètres',
            discipline=self.discipline
        )

    def test_liste_categories_anonyme_ok(self):
        """Un spectateur anonyme peut consulter la liste des catégories."""
        response = self.client.get('/api/categories/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) >= 1

    def test_categorie_affiche_discipline_nom(self):
        """Le nom de la discipline parente est affiché dans la réponse."""
        response = self.client.get('/api/categories/')
        data = response.json()[0]
        assert data['discipline_nom'] == 'Natation'

    def test_filtrage_par_discipline(self):
        """On peut filtrer les catégories par discipline."""
        response = self.client.get(f'/api/categories/?discipline={self.discipline.id}')
        assert response.status_code == status.HTTP_200_OK
        for item in response.json():
            assert item['discipline'] == self.discipline.id