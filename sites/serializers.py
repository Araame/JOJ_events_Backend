from rest_framework import serializers
from .models import Site, Zone

<<<<<<< HEAD
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
=======

class SiteSerializer(serializers.ModelSerializer):
    """Serializer de gestion des sites sportifs."""

    class Meta:
        model = Site
        fields = '__all__'
        # Unicité du nom au niveau base (protection supplémentaire)
        extra_kwargs = {
            'nom': {'error_messages': {
                'unique': 'Un site portant ce nom existe déjà.',
            }},
        }

    def validate_nom(self, nom):
        """Unicité du nom de site (insensible à la casse, espaces nettoyés)."""
        nom_nettoye = nom.strip()

        if not nom_nettoye:
            raise serializers.ValidationError(
                "Le nom du site ne peut pas être vide."
            )

        # Un nom composé uniquement d'espaces est refusé
        if len(nom_nettoye) < 2:
            raise serializers.ValidationError(
                "Le nom du site doit comporter au moins 2 caractères."
            )

        queryset = Site.objects.all()
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.filter(nom__iexact=nom_nettoye).exists():
            raise serializers.ValidationError(
                f"Un site nommé '{nom_nettoye}' existe déjà."
            )

        return nom_nettoye

    def validate(self, data):
        """Cohérence globale : latitude/longitude doivent être renseignées ensemble."""
        latitude = data.get('latitude')
        longitude = data.get('longitude')

        if (latitude is None) != (longitude is None):
            raise serializers.ValidationError(
                "La latitude et la longitude doivent être fournies ensemble."
            )
        return data


class ZoneSerializer(serializers.ModelSerializer):
    """Serializer de gestion des zones d'un site."""

    class Meta:
        model = Zone
        fields = '__all__'

    def validate_nom(self, nom):
        """Nom de zone non vide."""
        nom_nettoye = nom.strip()

        if not nom_nettoye:
            raise serializers.ValidationError(
                "Le nom de la zone ne peut pas être vide."
            )

        if len(nom_nettoye) < 2:
            raise serializers.ValidationError(
                "Le nom de la zone doit comporter au moins 2 caractères."
            )

        return nom_nettoye

    def validate(self, data):
        """Unicité du nom de zone par site."""
        nom = data.get('nom', '').strip()
        site = data.get('site') or getattr(self.instance, 'site', None)

        if not site or not nom:
            return data

        queryset = Zone.objects.filter(site=site, nom__iexact=nom)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError({
                'nom': (
                    f"Une zone nommée '{nom}' existe déjà sur le site "
                    f"'{site.nom}'."
                ),
            })

        return data
>>>>>>> origin/features/api-jd
