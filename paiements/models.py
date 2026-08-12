import uuid
from django.db import models


class TypeBillet(models.TextChoices):
    STANDARD = 'STANDARD', 'Standard'
    VIP = 'VIP', 'VIP'
    PRESSE = 'PRESSE', 'Presse'


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
    TypeBillet.STANDARD: 5000,
    TypeBillet.VIP: 15000,
    TypeBillet.PRESSE: 0,
}

ZONES_PAR_TYPE = {
    TypeBillet.STANDARD: ['Tribune générale', 'Zone debout'],
    TypeBillet.VIP: ['Tribune générale', 'Zone debout', 'Lounge VIP', 'Tribune VIP'],
    TypeBillet.PRESSE: ['Tribune générale', 'Zone debout', 'Zone presse', 'Salle de conférence'],
}


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
    transaction = models.OneToOneField(
        Transaction,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='billet'
    )
    type_billet = models.CharField(max_length=20, choices=TypeBillet.choices, default=TypeBillet.STANDARD)
    statut = models.CharField(max_length=20, choices=StatutBillet.choices, default=StatutBillet.EN_ATTENTE)
    code_unique = models.UUIDField(editable=False, unique=True, null=True, blank=True)
    zones_accessibles = models.JSONField(default=list)
    place = models.CharField(max_length=50, blank=True)
    date_commande = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_commande']

    def __str__(self):
        return f"Billet {self.type_billet} — {self.evenement} [{self.statut}]"

    def save(self, *args, **kwargs):
        if not self.code_unique:
            self.code_unique = uuid.uuid4()
        if not self.pk and not self.zones_accessibles:
            self.zones_accessibles = ZONES_PAR_TYPE.get(self.type_billet, [])
        super().save(*args, **kwargs)


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
