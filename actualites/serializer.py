from rest_framework.serializers import ModelSerializer
from .models import Actualite
from rest_framework import serializers
from .models import Actualite
from evenements.models import Evenement
from django.utils import timezone
MIN_TITLE_LENGTH = 5
MAX_TITLE_LENGTH = 200
MIN_DESCRIPTION_LENGTH = 20

class ActualiteSerializer(ModelSerializer):
    
    def validate_titre(self, value):
        """Valide le titre"""
        if not value or not value.strip():
            raise serializers.ValidationError("Le titre ne peut pas être vide.")
        
        if len(value) < MIN_TITLE_LENGTH:
            raise serializers.ValidationError(
                f"Le titre doit contenir au moins {MIN_TITLE_LENGTH} caractères."
            )
        
        if len(value) > MAX_TITLE_LENGTH:
            raise serializers.ValidationError(
                f"Le titre ne peut pas dépasser {MAX_TITLE_LENGTH} caractères."
            )
        
        return value
    
    def validate_description(self, value):
        """Valide la description"""
        if not value or not value.strip():
            raise serializers.ValidationError("La description ne peut pas être vide.")
        
        if len(value) < MIN_DESCRIPTION_LENGTH:
            raise serializers.ValidationError(
                f"La description doit contenir au moins {MIN_DESCRIPTION_LENGTH} caractères."
            )
        
        return value
    
    def validate_evenement_lie(self, value):
        """Valide l'événement lié"""
        if value is None:
            raise serializers.ValidationError("L'événement lié est obligatoire.")
        
        if not Evenement.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("L'événement spécifié n'existe pas.")
        
        return value
    
    def validate_date_publication(self, value):
        """Valide la date de publication"""
        if value and value < timezone.now():
            raise serializers.ValidationError(
                "La date de publication ne peut pas être dans le passé."
            )
        
        return value
    
    def validate(self, data):
        """Validation globale"""
        if not data.get('brouillon', True) and not data.get('date_publication'):
            raise serializers.ValidationError({
                'date_publication': "La date de publication est obligatoire pour une actualité publiée."
            })
        
        return data
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
        read_only_fields = ['auteur']    