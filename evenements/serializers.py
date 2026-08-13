from .models import Evenement
from rest_framework import serializers

#serializer pour afficher la carte des events
class EvenementListSerializer(serializers.ModelSerializer):
    discipline = serializers.CharField(
        source = 'categorie.discipline.nom',
        read_only = True),
    site = serializers.CharField(
        source = 'site.nom',
        read_only = True
    )
    class Meta:
        models = Evenement
        fields = ['image','discipline','categorie','date','heure','site']
  
#serializer pour l ajout des events ,la modification et details d un event     
class EvenementSerializer(serializers.ModelSerializer):
    class Meta:
        models = Evenement
        fields = '__All__'
        