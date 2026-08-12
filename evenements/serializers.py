from .models import Evenement
from rest_framework import serializers


class EvenementSerializer(serializers.ModelSerializer):
    discipline = serializers.CharField(
        source = 'categorie.discipline.nom',
        read_only = True),
    site = serializers.CharField(
        source = 'site.nom',
        read_only = True
    )
    class Meta:
        model = Evenement
        fields = ['image','discipline','categorie','date','heure']


class DetailEventSerializer(serializers.ModelSerializer):
    class Meta:
        models = Evenement
        fields = '__All__'
        
from .models import Discipline, Categorie

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
        if self.isinstance:
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

            nom_nettoye = value.strip().lower()
            if not nom_nettoye:
                raise  serializers.ValidationError("Le nom de la discipline ne peut pas être vide")

            if len(nom_nettoye)>100 or len(nom_nettoye)<2:
                raise serializers.ValidationError("Le nom de la discipline ne peut dépasser 100 caractères ou inférieur à 2 caractères.")

            if nom_nettoye[0].isalnum():
                raise serializers.ValidationError("Veuillez entrer une discipline qui existante.")

            queryset = Discipline.objects.all()
            if self.isinstance:
              queryset = queryset.exclude(pk=self.instance.pk)

            if queryset.filter(nom__iexact=value.strip()).exists():
                raise serializers.ValidationError(f"Une discipline nommée '{value.strip()}' existe déjà. ")

            return value.strip()


