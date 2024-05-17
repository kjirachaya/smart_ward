# Generated by Django 4.2.11 on 2024-05-17 04:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('patient', '0009_patient_id_card'),
    ]

    operations = [
        migrations.AlterField(
            model_name='patient',
            name='bed_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='patient',
            name='id_card',
            field=models.CharField(default='', max_length=13, null=True),
        ),
    ]
