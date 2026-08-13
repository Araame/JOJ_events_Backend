from rest_framework.serializers import ModelSerializer
from .models import Actualite

class ActualiteSerializer(ModelSerializer):
    class Meta:
        model= Actualite
        fields=[
            'titre',
            'description',
            'auteur',
            'image',
            'brouillon',
            'date_publication',
            'evenement_lie'
        ]