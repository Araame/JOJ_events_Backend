# paiements/migrations/0002_add_payment_model.py
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('paiements', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reference', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('montant', models.DecimalField(decimal_places=2, max_digits=10)),
                ('methode', models.CharField(choices=[('ORANGE_MONEY', 'Orange Money'), ('WAVE', 'Wave'), ('CARTE', 'Carte bancaire'), ('MOCK', 'Simulation (dev)')], max_length=20)),
                ('statut', models.CharField(choices=[('EN_ATTENTE', 'En attente'), ('EN_COURS', 'En cours'), ('REUSSI', 'Réussi'), ('ECHOUE', 'Échoué')], default='EN_ATTENTE', max_length=20)),
                ('reference_prestataire', models.CharField(blank=True, max_length=255)),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
                ('date_modification', models.DateTimeField(auto_now=True)),
                ('billet', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='payment', to='paiements.billet')),
            ],
            options={
                'ordering': ['-date_creation'],
            },
        ),
    ]
