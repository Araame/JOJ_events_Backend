from rest_framework import serializers
from .models import Site, Zone

# Create your views here.
class ZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Zone
        fields = ['id', 'nom']  

class SiteSerializer(serializers.ModelSerializer):
    zones = ZoneSerializer(many=True, read_only=True) 

    class Meta:
        model = Site
        fields = '__all__'  

    def create(self, validated_data):
        zones_data = validated_data.pop('zones', [])
        
        # Créer le site
        site = Site.objects.create(**validated_data)
        
        # Créer les zones associées
        for zone_data in zones_data:
            Zone.objects.create(site=site, **zone_data)
            
        return site

    def update(self, instance, validated_data):
        # Récupérer les nouvelles données des zones
        zones_data = validated_data.pop('zones', None)
        
        # Mise à jour simple du site
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Mise à jour des zones 
        if zones_data is not None:
            instance.zone_set.all().delete()
            for zone_data in zones_data:
                Zone.objects.create(site=instance, **zone_data)
                
        return instance