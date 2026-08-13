"""
Tests unitaires des modèles JOJ_EVENT.
Valide la création des objets et les relations entre eux.
"""
import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import time

from sites.models import Site, Zone
from evenements.models import Discipline, Categorie, Evenement
from paiements.models import Spectateur, Billet


Personnel = get_user_model()


@pytest.mark.unit
@pytest.mark.django_db
class TestSiteEtZone:
    """Tests du couple Site + Zone."""

    def test_creer_site_valide(self, db):
        """Un site peut être créé avec des données valides."""
        site = Site.objects.create(
            nom='Dakar Arena',
            capacite=50000,
            ville='Dakar',
            region='Dakar',
            latitude=14.6937,
            longitude=-17.4441
        )
        assert site.pk is not None
        assert site.nom == 'Dakar Arena'
        assert site.capacite == 50000

    def test_zone_liee_a_site(self, db):
        """Une zone est toujours rattachée à un site."""
        site = Site.objects.create(
            nom='Stade Test', capacite=10000,
            ville='Dakar', region='Dakar'
        )
        zone = Zone.objects.create(nom='VIP', capacite=500, site=site)
        
        assert zone.site == site
        assert zone in site.zones.all()

    def test_site_a_plusieurs_zones(self, db):
        """Un site peut avoir plusieurs zones (Standard, VIP, PRM)."""
        site = Site.objects.create(
            nom='Dakar Arena', capacite=50000,
            ville='Dakar', region='Dakar'
        )
        Zone.objects.create(nom='Standard', capacite=40000, site=site)
        Zone.objects.create(nom='VIP', capacite=8000, site=site)
        Zone.objects.create(nom='PRM', capacite=2000, site=site)
        
        assert site.zones.count() == 3


@pytest.mark.unit
@pytest.mark.django_db
class TestDisciplineEtCategorie:
    """Tests de la hiérarchie Discipline > Catégorie."""

    def test_categorie_liee_a_discipline(self, db):
        """Une catégorie est rattachée à une discipline."""
        discipline = Discipline.objects.create(nom='Athlétisme')
        categorie = Categorie.objects.create(
            nom='100m Hommes',
            discipline=discipline
        )
        assert categorie.discipline == discipline
        assert categorie in discipline.categories.all()


@pytest.mark.unit
@pytest.mark.django_db
class TestEvenement:
    """Tests du modèle Evenement."""

    def test_evenement_futur_valide(self, db):
        """Un événement avec une date future est valide."""
        site = Site.objects.create(
            nom='Arena', capacite=50000,
            ville='Dakar', region='Dakar'
        )
        discipline = Discipline.objects.create(nom='Athlétisme')
        categorie = Categorie.objects.create(nom='100m', discipline=discipline)
        
        evenement = Evenement.objects.create(
            titre='Finale 100m',
            date=timezone.now().date() + timezone.timedelta(days=7),
            site=site,
            categorie=categorie,
            heure=time(14, 0),
                    
        )
        assert evenement.pk is not None
        assert evenement.date > timezone.now().date()


@pytest.mark.unit
@pytest.mark.django_db
class TestSpectateurAnonyme:
    """Tests du spectateur anonyme (pas de compte utilisateur)."""

    def test_spectateur_sans_compte_utilisateur(self, db):
        """Un spectateur est créé sans authentification Django."""
        spectateur = Spectateur.objects.create(
            nom='Diallo',
            prenom='Alpha',
            email='alpha@example.sn',
            tel='771234567'
        )
        assert spectateur.pk is not None
        # Le spectateur n'est pas un utilisateur Django
        assert not isinstance(spectateur, Personnel)