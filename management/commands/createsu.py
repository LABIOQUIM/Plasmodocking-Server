from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from decouple import config

class Command(BaseCommand):
    help = 'Cria um superusuário padrão'

    def handle(self, *args, **kwargs):
        username = config("SUPER_USER_USERNAME")
        password = config("SUPER_USER_PASSWORD")
        email = config("SUPER_USER_EMAIL")
        
        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(self.style.SUCCESS(f'Superuser "{username}" criado com sucesso!'))
        else:
            self.stdout.write(self.style.WARNING(f'Superuser "{username}" já existe.'))
