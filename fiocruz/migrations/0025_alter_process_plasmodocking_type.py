# Generated by Django 4.2.4 on 2024-03-14 19:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fiocruz', '0024_process_plasmodocking_delete_arquivos_virtauls'),
    ]

    operations = [
        migrations.AlterField(
            model_name='process_plasmodocking',
            name='type',
            field=models.CharField(choices=[('vivax', 'Vivax'), ('falciparum', 'Falciparum')], default='Falciparum', max_length=20),
        ),
    ]
