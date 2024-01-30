# Generated by Django 4.2.4 on 2024-01-29 08:43

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ("fiocruz", "0019_alter_macro_prepare_ligantepdb_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="usercustom",
            name="created_at",
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name="usercustom",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name="usercustom",
            name="deleted",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="usercustom",
            name="role",
            field=models.CharField(
                choices=[("USER", "User"), ("ADMIN", "Admin")],
                default="USER",
                max_length=255,
            ),
        ),
    ]
