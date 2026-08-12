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
        