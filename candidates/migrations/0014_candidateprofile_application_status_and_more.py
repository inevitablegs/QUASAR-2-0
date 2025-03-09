# Generated by Django 5.1.6 on 2025-03-09 02:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('candidates', '0013_candidateprofile_address_candidateprofile_experience_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='candidateprofile',
            name='application_status',
            field=models.CharField(choices=[('Pending', 'Pending'), ('Accepted', 'Accepted'), ('Rejected', 'Rejected')], default='Pending', max_length=10),
        ),
        migrations.AddField(
            model_name='candidateprofile',
            name='hiring_recommendation',
            field=models.IntegerField(default=0),
        ),
    ]
