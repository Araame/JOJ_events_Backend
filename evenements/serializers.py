# Critères d'acceptation
# GET /api/résultats/ retourne la liste des résultats
# GET /api/résultats/{id}/ retourne le détail
# GET /api/résultats/{id}/équipe/ retourne les événements associés
# Les données incluent évènement, dicipline, équipe si disponible



from rest_framework.serializers import ModelSerializer, SerializerMethodField
from .models import Resultat, Competiteur

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
