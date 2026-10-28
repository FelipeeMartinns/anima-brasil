"""Cria um usuário administrador inicial. Uso: python manage.py seed_admin

Cria (ou atualiza) o superuser admin/admin123 para desenvolvimento.
"""

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Cria o usuário administrador inicial para desenvolvimento.'

    def handle(self, *args, **options):
        username = 'admin'
        email = 'admin@animabrasil.com.br'
        password = 'admin123'

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f'Usuário "{username}" já existe.'))
            return

        User.objects.create_superuser(username=username, email=email, password=password)
        self.stdout.write(self.style.SUCCESS(
            f'Superusuário "{username}" criado (login: {username} / senha: {password}).'
        ))