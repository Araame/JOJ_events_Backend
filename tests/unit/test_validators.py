"""
Tests des validations des serializers.
Vérifie que les données incohérentes sont rejetées.
"""
import pytest
from evenements.models import Discipline, Categorie
from evenements.serializers import DisciplineSerializer, CategorieSerializer


@pytest.mark.unit
@pytest.mark.django_db
class TestDisciplineSerializerValidation:
    """Validations du serializer Discipline."""

    def setup_method(self):
        Discipline.objects.all().delete()

    def test_nom_unique_rejete(self):
        """Deux disciplines avec le même nom sont rejetées."""
        Discipline.objects.create(nom='Athlétisme')
        
        serializer = DisciplineSerializer(data={'nom': 'Athlétisme'})
        
        assert not serializer.is_valid()
        assert 'nom' in serializer.errors

    def test_nom_vide_rejete(self):
        """Un nom vide ou avec uniquement des espaces est rejeté."""
        serializer = DisciplineSerializer(data={'nom': '   '})
        assert not serializer.is_valid()

    def test_nom_valide_accepte(self):
        """Un nom correct passe la validation."""
        serializer = DisciplineSerializer(data={'nom': 'Natation'})
        assert serializer.is_valid(), serializer.errors


@pytest.mark.unit
@pytest.mark.django_db
class TestCategorieSerializerValidation:
    """Validations du serializer Categorie."""

    def setup_method(self):
        Discipline.objects.all().delete()
        Categorie.objects.all().delete()

    def test_categorie_sans_discipline_rejetee(self):
        """Une catégorie sans discipline est rejetée."""
        serializer = CategorieSerializer(data={
            'nom': '100m',
            'discipline': None
        })
        assert not serializer.is_valid()

    def test_nom_categorie_unique_rejete(self):
        """Deux catégories avec le même nom sont rejetées."""
        discipline = Discipline.objects.create(nom='Athlétisme')
        Categorie.objects.create(nom='100m', discipline=discipline)
        
        serializer = CategorieSerializer(data={
            'nom': '100m',
            'discipline': discipline.id
        })
        assert not serializer.is_valid()