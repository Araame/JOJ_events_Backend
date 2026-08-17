"""
Tests unitaires des signaux de notification CRUD back-office.

Vérifie que chaque CRUD sur Actualite, Site, Zone, Evenement et Resultat
crée bien une notification pour les superadmins.

Modèles concernés (avec leurs champs réels) :
- Actualite   : titre, description, auteur, image, brouillon,
                date_publication, evenement_lie (obligatoire)
- Site        : nom, capacite, description, service, image,
                latitude, longitude, ville, region
- Evenement   : titre, date, heure, site, categorie, description, image
- Resultat    : evenement, score, createur, competiteur
"""
import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta, time

from notifications.models import Notification, DestinataireType

Personnel = get_user_model()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def contexte_evenement():
    """Crée un site + une discipline + une catégorie pour les événements."""
    from sites.models import Site
    from evenements.models import Discipline, Categorie

    site = Site.objects.create(
        nom='Dakar Arena', ville='Diamniadio', region='Dakar',
        latitude=14.75, longitude=-17.18, capacite=15000,
    )
    discipline = Discipline.objects.create(nom='Athlétisme')
    categorie = Categorie.objects.create(nom='100m', discipline=discipline)
    return site, categorie


@pytest.fixture
def evenement_reference(contexte_evenement):
    """Crée un événement de référence, utilisé pour lier les actualités
    (evenement_lie est obligatoire)."""
    from evenements.models import Evenement

    site, categorie = contexte_evenement
    return Evenement.objects.create(
        titre='Événement de référence',
        date=timezone.now().date() + timedelta(days=7),
        heure=time(14, 0),
        site=site,
        categorie=categorie,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
@pytest.mark.api
@pytest.mark.django_db
class TestNotificationsCRUDModeles:
    """
    Vérifie que chaque CRUD sur les 4 modèles crée bien
    une notification pour les superadmins.
    """

    def setup_method(self):
        self.superadmin = Personnel.objects.create_user(
            username='superadmin_test',
            password='MotDePasse123!',
            role='SUPERADMIN',
        )

    # ------------------------------------------------------------------
    def test_creation_actualite_notifie(self, evenement_reference):
        """La création d'une actualité notifie les superadmins."""
        from actualites.models import Actualite

        nb_avant = Notification.objects.filter(
            destinataire_type=DestinataireType.PERSONNEL,
        ).count()

        Actualite.objects.create(
            titre='Nouvelle actualité test',
            description='Contenu de test',
            date_publication=timezone.now().date(),
            auteur=self.superadmin,
            evenement_lie=evenement_reference,   # champ obligatoire
        )

        nb_apres = Notification.objects.filter(
            destinataire_type=DestinataireType.PERSONNEL,
        ).count()

        assert nb_apres == nb_avant + 1

    # ------------------------------------------------------------------
    def test_creation_site_notifie(self):
        """La création d'un site notifie les superadmins."""
        from sites.models import Site

        nb_avant = Notification.objects.filter(
            destinataire_type=DestinataireType.PERSONNEL,
        ).count()

        Site.objects.create(
            nom='Stade Iba Mar Diop',
            ville='Dakar',
            region='Dakar',
            latitude=14.7167,
            longitude=-17.4677,
            capacite=30000,
        )

        nb_apres = Notification.objects.filter(
            destinataire_type=DestinataireType.PERSONNEL,
        ).count()

        assert nb_apres == nb_avant + 1

    # ------------------------------------------------------------------
    def test_creation_zone_notifie(self):
        """La création d'une zone notifie les superadmins."""
        from sites.models import Site, Zone

        site = Site.objects.create(
            nom='Dakar Arena Zone', ville='Diamniadio', region='Dakar',
            latitude=14.75, longitude=-17.18, capacite=15000,
        )

        nb_avant = Notification.objects.filter(
            destinataire_type=DestinataireType.PERSONNEL,
        ).count()

        Zone.objects.create(
            site=site, nom='Gradins', capacite=10000,
        )

        nb_apres = Notification.objects.filter(
            destinataire_type=DestinataireType.PERSONNEL,
        ).count()

        assert nb_apres == nb_avant + 1

    # ------------------------------------------------------------------
    def test_creation_evenement_notifie(self, contexte_evenement):
        """La création d'un événement notifie les superadmins."""
        from evenements.models import Evenement

        site, categorie = contexte_evenement

        nb_avant = Notification.objects.filter(
            destinataire_type=DestinataireType.PERSONNEL,
        ).count()

        Evenement.objects.create(
            titre='Finale 100m',
            date=timezone.now().date() + timedelta(days=7),
            heure=time(14, 0),
            site=site,
            categorie=categorie,
        )

        nb_apres = Notification.objects.filter(
            destinataire_type=DestinataireType.PERSONNEL,
        ).count()

        assert nb_apres == nb_avant + 1

    # ------------------------------------------------------------------
    def test_modification_evenement_notifie(self, contexte_evenement):
        """La modification d'un événement notifie les superadmins."""
        from evenements.models import Evenement

        site, categorie = contexte_evenement
        evenement = Evenement.objects.create(
            titre='Série 100m',
            date=timezone.now().date() + timedelta(days=7),
            heure=time(10, 0),
            site=site,
            categorie=categorie,
        )

        nb_avant = Notification.objects.filter(
            destinataire_type=DestinataireType.PERSONNEL,
        ).count()

        # Modifier le titre
        evenement.titre = 'Série 100m (modifié)'
        evenement.save()

        nb_apres = Notification.objects.filter(
            destinataire_type=DestinataireType.PERSONNEL,
        ).count()

        assert nb_apres == nb_avant + 1

    # ------------------------------------------------------------------
    def test_suppression_actualite_notifie(self, evenement_reference):
        """La suppression d'une actualité notifie les superadmins."""
        from actualites.models import Actualite

        actualite = Actualite.objects.create(
            titre='À supprimer',
            description='Contenu',
            date_publication=timezone.now().date(),
            auteur=self.superadmin,
            evenement_lie=evenement_reference,   # champ obligatoire
        )

        nb_avant = Notification.objects.filter(
            destinataire_type=DestinataireType.PERSONNEL,
        ).count()

        actualite.delete()

        nb_apres = Notification.objects.filter(
            destinataire_type=DestinataireType.PERSONNEL,
        ).count()

        assert nb_apres == nb_avant + 1

    # ------------------------------------------------------------------
    def test_creation_resultat_notifie(self, contexte_evenement):
        """La création d'un résultat notifie les superadmins."""
        from evenements.models import Evenement, Resultat

        site, categorie = contexte_evenement
        evenement = Evenement.objects.create(
            titre='Finale 200m',
            date=timezone.now().date() + timedelta(days=7),
            heure=time(16, 0),
            site=site,
            categorie=categorie,
        )

        nb_avant = Notification.objects.filter(
            destinataire_type=DestinataireType.PERSONNEL,
        ).count()

        Resultat.objects.create(
            evenement=evenement,
            score='10.25s',
            createur=self.superadmin,
        )

        nb_apres = Notification.objects.filter(
            destinataire_type=DestinataireType.PERSONNEL,
        ).count()

        assert nb_apres == nb_avant + 1

    # ------------------------------------------------------------------
    def test_notification_superadmin_contenu_correct(self, contexte_evenement):
        """La notification créée mentionne le modèle, l'action et l'objet."""
        from evenements.models import Evenement

        site, categorie = contexte_evenement

        Evenement.objects.create(
            titre='Finale 400m',
            date=timezone.now().date() + timedelta(days=7),
            heure=time(18, 0),
            site=site,
            categorie=categorie,
        )

        # Filtrer directement sur l'objet de la notification créée
        notif = Notification.objects.filter(
            destinataire_type=DestinataireType.PERSONNEL,
            objet__contains='[Événement]',
        ).order_by('-id').first()

        assert notif is not None
        assert notif.personnel == self.superadmin
        assert 'Événement' in notif.objet
        assert 'CRÉATION' in notif.objet
        assert 'Finale 400m' in notif.objet
