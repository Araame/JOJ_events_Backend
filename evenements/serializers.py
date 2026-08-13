from .models import Evenement
from rest_framework import serializers


class EvenementSerializer(serializers.ModelSerializer):
    # discipline = serializers.CharField(
    #     source = 'categorie.discipline.nom',
    #     read_only = True),
    # site = serializers.CharField(
    #     source = 'site.nom',
    # )
    class Meta:
        model = Evenement
        fields = ['titre','description','image','categorie','date','heure', 'site']


class DetailEventSerializer(serializers.ModelSerializer):
    class Meta:
        models = Evenement
        fields = '__All__'
        
from .models import Discipline, Categorie
# Critères d'acceptation
# GET /api/résultats/ retourne la liste des résultats
# GET /api/résultats/{id}/ retourne le détail
# GET /api/résultats/{id}/équipe/ retourne les événements associés
# Les données incluent évènement, dicipline, équipe si disponible



from rest_framework.serializers import ModelSerializer, SerializerMethodField
from .models import Resultat, Competiteur
from rest_framework import serializers
from .models import Discipline, Categorie, Equipe, Joueur

class CompetiteurSerializer(ModelSerializer):
    type= SerializerMethodField()
    nom_complet= SerializerMethodField()

    class Meta:
        model=Competiteur
        fields=[
            'id',
            'type',
            'nom_complet',
            'pays'
        ]

    def get_type(self,obj):
        if hasattr(obj, 'equipe'):
            return 'equipe'
        elif hasattr(obj, 'joueur'):
            return 'joueur'
        return 'inconnu'    

    def get_nom_complet(self, obj):
        if hasattr(obj, 'equipe'):
            return f"{obj.equipe.nom}"
        elif hasattr(obj, 'joueur'):
            return f"{obj.joueur.prenom} {obj.joueur.nom}"
        return str(obj)



class ResultatSerializer(ModelSerializer):
    info_competiteur= CompetiteurSerializer(source='competiteur', read_only=True)
    class Meta:
        model= Resultat
        fields=[
            'evenement',
            'score',
            'createur',
            'info_competiteur'
        ]

class EquipeSerializer(ModelSerializer):
    class Meta:
        model= Equipe
        fields=[
            'id',
            'nom',
            'statut',
            'pays',
            'image',
            'categorie',

        ]

class JoueurSerializer(ModelSerializer):
    class Meta:
        model= Joueur
        fields=[
            'id',
            'nom',
            'prenom',
            'statut',
            'pays',
            'image',
            'categorie',

        ]


class CategorieSerializer(serializers.ModelSerializer):
    """
    Serializer pour afficher une catégorie avec le nom de sa discipline.
    """
    discipline_nom = serializers.CharField(source='discipline.nom', read_only=True)
    
    class Meta:
        model = Categorie
        fields = ['id', 'nom', 'description', 'discipline', 'discipline_nom']

    def validate_nom(self, value):
        """ Unicité du nom de la catégorie """
        nom_nettoye = value.strip()
        if not nom_nettoye:
            raise serializers.ValidationError("Le nom de la catégorie ne peut pas être vide")
        
        queryset = Categorie.objects.all()
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.filter(nom__iexact=nom_nettoye).exists():
            raise serializers.ValidationError(f"Une catégorie nommée '{nom_nettoye}' existe déjà.")
        
        return nom_nettoye

    def validate_discipline(self, value):
        """ Vérifier que la discipline existe  """
        if value is None:
            raise serializers.ValidationError("La catégorie doit être rattachée à une discipline.")
        return value


class DisciplineSerializer(serializers.ModelSerializer):
    """
    Serializer pour afficher une discipline avec ses catégories et le nombre de compétiteurs.
    """
    categories = CategorieSerializer(many=True, read_only=True)

    class Meta:
        model = Discipline
        fields = ['id', 'nom', 'regle', 'accessibilite', 'categories']

    def validate_nom(self, value):
        """ Unicité du nom et nettoyage des espaces """
        nom_nettoye = value.strip()
        
        if not nom_nettoye:
            raise serializers.ValidationError("Le nom de la discipline ne peut pas être vide")

        if len(nom_nettoye) > 100 or len(nom_nettoye) < 2:
            raise serializers.ValidationError("Le nom de la discipline doit être compris entre 2 et 100 caractères.")

        if not nom_nettoye[0].isalnum():
            raise serializers.ValidationError("Le nom de la discipline doit commencer par une lettre ou un chiffre valide.")
    def get_nombre_competiteurs(self, obj):
        """ Compte le total des compétiteurs dans toutes les catégories de la discipline """
        return sum(cat.competiteurs.count() for cat in obj.categories.all())

    def validate_nom(self, value):
        """ Unicité du nom et nettoyage des espaces """
        nom_nettoye = value.strip().lower()
        if not nom_nettoye:
            raise serializers.ValidationError("Le nom de la discipline ne peut pas être vide")

        if len(nom_nettoye) > 100 or len(nom_nettoye) < 2:
            raise serializers.ValidationError("Le nom de la discipline ne peut dépasser 100 caractères ou être inférieur à 2 caractères.")

        queryset = Discipline.objects.all()
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.filter(nom__iexact=value.strip()).exists():
            raise serializers.ValidationError(f"Une discipline nommée '{value.strip()}' existe déjà.")

        return value.strip()

        if queryset.filter(nom__iexact=nom_nettoye).exists():
            raise serializers.ValidationError(f"Une discipline nommée '{nom_nettoye}' existe déjà.")

        return nom_nettoye
