# Generated by Django 4.2.11 on 2024-04-29 07:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('patient', '0005_alter_bed_patient_id'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ward',
            name='bed_list',
        ),
        migrations.AddField(
            model_name='ward',
            name='bed_list',
            field=models.CharField(default=[], max_length=200),
        ),
    ]
