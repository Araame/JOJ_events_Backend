# paiements/migrations/0002_add_type_billet.py
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('paiements', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='billet',
            name='type_billet',
            field=models.CharField(choices=[('STANDARD', 'Standard'), ('VIP', 'VIP'), ('PRESSE', 'Presse')], default='STANDARD', max_length=20),
        ),
        migrations.AddField(
            model_name='billet',
            name='code_unique',
            field=models.UUIDField(blank=True, editable=False, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='billet',
            name='zones_accessibles',
            field=models.JSONField(default=list),
        ),
    ]
