from rest_framework import serializers
from .models import Billet, Spectateur, Transaction, TypeBillet, Payment, MethodePaiement, PRIX_PAR_TYPE
from evenements.models import Evenement


class SpectateurSerializer(serializers.ModelSerializer):
    class Meta:
        model = Spectateur
        fields = ('nom', 'prenom', 'email', 'tel')


class BilletSerializer(serializers.ModelSerializer):
    evenement_titre = serializers.CharField(source='evenement.titre', read_only=True)
    spectateur = SpectateurSerializer(read_only=True)
    prix_unitaire = serializers.SerializerMethodField()

    class Meta:
        model = Billet
        fields = (
            'id', 'code_unique', 'spectateur', 'evenement', 'evenement_titre',
            'type_billet', 'statut', 'zones_accessibles', 'place',
            'prix_unitaire', 'date_commande',
        )
        read_only_fields = fields

    def get_prix_unitaire(self, obj):
        return PRIX_PAR_TYPE.get(obj.type_billet, 0)


class LigneBilletSerializer(serializers.Serializer):
    """Une ligne : type de billet + quantité souhaitée."""
    type_billet = serializers.ChoiceField(choices=TypeBillet.choices)
    quantite = serializers.IntegerField(min_value=1, max_value=10)
    place = serializers.CharField(max_length=50, required=False, allow_blank=True)


class CommandeBilletSerializer(serializers.Serializer):
    """
    Réservation de billets par un spectateur sans compte.

    Exemple :
    {
        "spectateur": {"nom": "Diallo", "prenom": "Mamadou", "email": "m@ex.com", "tel": "771234567"},
        "evenement": 1,
        "billets": [
            {"type_billet": "STANDARD", "quantite": 2},
            {"type_billet": "VIP", "quantite": 1}
        ]
    }
    """
    spectateur = SpectateurSerializer()
    evenement = serializers.PrimaryKeyRelatedField(queryset=Evenement.objects.all())
    billets = LigneBilletSerializer(many=True, min_length=1)

    def validate_billets(self, lignes):
        types = [l['type_billet'] for l in lignes]
        if len(types) != len(set(types)):
            raise serializers.ValidationError("Chaque type de billet ne peut apparaître qu'une seule fois.")
        return lignes

    def create(self, validated_data):
        # Créer ou récupérer le spectateur
        spectateur_data = validated_data.pop('spectateur')
        spectateur, _ = Spectateur.objects.get_or_create(
            email=spectateur_data['email'],
            defaults=spectateur_data
        )
        evenement = validated_data['evenement']
        billets_crees = []
        for ligne in validated_data['billets']:
            for _ in range(ligne['quantite']):
                billet = Billet.objects.create(
                    spectateur=spectateur,
                    evenement=evenement,
                    type_billet=ligne['type_billet'],
                    place=ligne.get('place', ''),
                )
                billets_crees.append(billet)
        return billets_crees


class CommandeReponseSerializer(serializers.Serializer):
    """Réponse après une commande : billets créés + total."""
    billets = BilletSerializer(many=True)
    total = serializers.IntegerField()
    nombre_billets = serializers.IntegerField()


# --- Payment ---

class PaymentSerializer(serializers.ModelSerializer):
    billet_code = serializers.UUIDField(source='billet.code_unique', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)

    class Meta:
        model = Payment
        fields = (
            'id', 'reference', 'billet', 'billet_code',
            'montant', 'methode', 'statut', 'statut_display',
            'reference_prestataire', 'date_creation', 'date_modification',
        )
        read_only_fields = (
            'id', 'reference', 'montant', 'statut',
            'reference_prestataire', 'date_creation', 'date_modification',
        )


# Serializer pour payer plusieurs billets
class PaymentCreateSerializer(serializers.Serializer):
    """
    Initie le paiement de plusieurs billets (une commande).
    Le montant total est calculé côté serveur — non modifiable par le client.
    """
    billets = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(queryset=Billet.objects.all()),
        min_length=1,
        allow_empty=False
    )
    methode = serializers.ChoiceField(choices=MethodePaiement.choices)

    def validate_billets(self, billets):
        # Vérifier que tous les billets sont en attente
        for billet in billets:
            if billet.statut != 'EN_ATTENTE':
                raise serializers.ValidationError(
                    f"Le billet {billet.id} ne peut plus être payé (statut: {billet.statut})."
                )
            if hasattr(billet, 'payment'):
                raise serializers.ValidationError(
                    f"Un paiement existe déjà pour le billet {billet.id}."
                )
        
        # Vérifier que tous les billets appartiennent au même spectateur
        if billets:
            spectateur = billets[0].spectateur
            for billet in billets[1:]:
                if billet.spectateur != spectateur:
                    raise serializers.ValidationError(
                        "Tous les billets doivent appartenir au même spectateur."
                    )
        return billets