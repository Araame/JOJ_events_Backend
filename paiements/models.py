from django.db import models

class Spectateur(models.Model):
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    email = models.EmailField()
    tel = models.CharField(max_length=20)

class Transaction(models.Model):
    numero_transaction = models.CharField(max_length=100, unique=True)
    mode_paiement = models.CharField(max_length=50)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    telephone = models.CharField(max_length=20)
    date = models.DateTimeField(auto_now_add=True)

class Billet(models.Model):
    spectateur = models.ForeignKey(Spectateur, on_delete=models.CASCADE, related_name='billets')
    zone = models.ForeignKey('sites.Zone', on_delete=models.CASCADE, related_name='billets')
    evenement = models.ForeignKey('evenements.Evenement', on_delete=models.CASCADE)
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, related_name='billet')
    qr_code = models.CharField(max_length=255, unique=True)
    place = models.CharField(max_length=50)