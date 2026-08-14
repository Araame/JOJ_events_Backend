import uuid
import qrcode
from io import BytesIO
from django.core.files import File
from django.db import models


def get_type_billet_choices():
    """Retourne les choix de types de billets depuis les zones de l'application sites."""
    try:
        from sites.models import Zone
        noms = Zone.objects.values_list('nom', flat=True).distinct()
        return [(nom, nom) for nom in noms]
    except Exception:
        return []


class StatutBillet(models.TextChoices):
    EN_ATTENTE = 'EN_ATTENTE', 'En attente'
    VALIDE = 'VALIDE', 'Validé'
    UTILISE = 'UTILISE', 'Utilisé'
    EXPIRE = 'EXPIRE', 'Expiré'
    ANNULE = 'ANNULE', 'Annulé'


class StatutPaiement(models.TextChoices):
    EN_ATTENTE = 'EN_ATTENTE', 'En attente'
    EN_COURS = 'EN_COURS', 'En cours'
    REUSSI = 'REUSSI', 'Réussi'
    ECHOUE = 'ECHOUE', 'Échoué'


class MethodePaiement(models.TextChoices):
    ORANGE_MONEY = 'ORANGE_MONEY', 'Orange Money'
    WAVE = 'WAVE', 'Wave'
    CARTE = 'CARTE', 'Carte bancaire'
    MOCK = 'MOCK', 'Simulation (dev)'


# Prix par type de billet — calculé côté serveur uniquement
PRIX_PAR_TYPE = {
    'STANDARD': 5000,
    'VIP': 15000,
    'PRESSE': 0,
}

def get_zones_pour_type(type_billet):
    """
    Retourne la liste des noms de zones accessibles pour un type de billet,
    en lisant dynamiquement les zones de l'application sites.
    """
    from sites.models import Zone
    return list(Zone.objects.filter(nom=type_billet).values_list('nom', flat=True))


class Spectateur(models.Model):
    """Informations du spectateur saisies au moment de la réservation. Pas de compte requis."""
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    email = models.EmailField()
    tel = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.prenom} {self.nom} — {self.email}"


class Transaction(models.Model):
    numero_transaction = models.CharField(max_length=100, unique=True)
    mode_paiement = models.CharField(max_length=50)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    telephone = models.CharField(max_length=20)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.numero_transaction} — {self.montant} FCFA"


class Billet(models.Model):
    spectateur = models.ForeignKey(
        Spectateur,
        on_delete=models.CASCADE,
        related_name='billets'
    )
    evenement = models.ForeignKey(
        'evenements.Evenement',
        on_delete=models.CASCADE,
        related_name='billets'
    )
    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='billets' 
    )
    type_billet = models.CharField(max_length=100, choices=get_type_billet_choices)
    statut = models.CharField(max_length=20, choices=StatutBillet.choices, default=StatutBillet.EN_ATTENTE)
    code_unique = models.UUIDField(editable=False, unique=True, null=True, blank=True)
    zones_accessibles = models.JSONField(default=list)
    place = models.CharField(max_length=50, blank=True)
    date_commande = models.DateTimeField(auto_now_add=True)
    
    # Ajout du champ QR Code
    qr_code = models.ImageField(
        upload_to='qr_codes/',
        blank=True,
        null=True,
        help_text="QR Code du billet"
    )

    class Meta:
        ordering = ['-date_commande']

    def __str__(self):
        return f"Billet {self.type_billet} — {self.evenement} [{self.statut}]"

    def generate_qr_code(self):
        """Génère un QR Code pour le billet."""
        import json
        qr_data = {
            'billet_id': str(self.code_unique),
            'evenement': self.evenement.titre if self.evenement else '',
            'spectateur': f"{self.spectateur.prenom} {self.spectateur.nom}",
            'type': self.type_billet,
            'place': self.place,
        }
        
        qr_text = json.dumps(qr_data)
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_text)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        
        filename = f"qr_{self.code_unique}.png"
        self.qr_code.save(filename, File(buffer), save=False)

    def save(self, *args, **kwargs):
        if not self.code_unique:
            self.code_unique = uuid.uuid4()
        if not self.pk and not self.zones_accessibles:
            self.zones_accessibles = get_zones_pour_type(self.type_billet)
        
        super().save(*args, **kwargs)
        
        # Générer le QR Code après la première sauvegarde
        if not self.qr_code:
            self.generate_qr_code()
            # Use update_fields to avoid a duplicate INSERT on the same pk
            super().save(update_fields=['qr_code'])


class Payment(models.Model):
    reference = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    billet = models.OneToOneField(
        Billet,
        on_delete=models.CASCADE,
        related_name='payment'
    )
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    methode = models.CharField(max_length=20, choices=MethodePaiement.choices)
    statut = models.CharField(
        max_length=20,
        choices=StatutPaiement.choices,
        default=StatutPaiement.EN_ATTENTE
    )
    reference_prestataire = models.CharField(max_length=255, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_creation']

    def __str__(self):
        return f"Payment {self.reference} — {self.montant} FCFA [{self.statut}]"