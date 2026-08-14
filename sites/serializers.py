from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import Site, Zone

# Create your views here.


class SiteSerializer(serializers.ModelSerializer):
    """Serializer pour site"""
    class Meta :
        model = Site
        fields = '__all__'

    def valider_nom(self, nom):
        """Valide le nom avant l'enregistrement dans la base de données"""
        site = Site.objects.filter(nom = nom).first()
        if site : 
            raise ValidationError("Ce site existe déjà en base de données")
        return 


    def valider_site(self, data):
        """Valide le site avant la sauvegarde en BD"""
        if len(data["nom"]) > 255 : 
            raise ValidationError("Le nom du site ne doit pas dépasser 255 caractères.")
        if len(data["ville"]) > 100 : 
            raise ValidationError("La ville du site ne doit pas dépasser 100 caractères.")
        if len(data["region"]) > 100 : 
            raise ValidationError("La ville du site ne doit pas dépasser 100 caractères.")
        return data

class ZoneSerializer(ModelSerializer):
    """Serializer pour Zone"""

    class Meta : 
        model = Zone
        fields = '__all__'


    def valider_zone(self, data):
        """Valider une zone avant la sauegarde dans la base de données"""
        if len(data["nom"]) > 100 : 
            raise ValidationError("Le nom de la zone ne doit pas dépasser 100 caractères.")
        return data



    def validate(self, data):
        """Vérifie si une zone n'existe pas pour ce site"""
        if Zone.objects.filter(site=data["site"], nom=data["nom"]).exists():
            raise ValidationError({"Une zone de type '{}' existe déjà pour ce site. ""Il ne peut y avoir qu'une seule zone de ce type par site.".format(data["nom"])})

        return data


