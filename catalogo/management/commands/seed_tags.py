"""Popula tags pré-definidas do sistema. Uso: python manage.py seed_tags"""

from django.core.management.base import BaseCommand, CommandError

from catalogo.models import Tag


class Command(BaseCommand):
    help = 'Cria as tags pré-definidas do sistema (gêneros).'

    # Corrige rota de dados legados: 'Abstracto' era um typo.
    DEFEITOS = {
        'Abstracto': 'Abstrato',
    }

    TAGS = [
        'Animação 2D',
        'Animação 3D',
        'Stop Motion',
        'Experimental',
        'Pixilation',
        'Cutout',
        'Rotoscopia',
        'Motion Graphics',
        'Infantil',
        'Aventura',
        'Fantasia',
        'Ficção Científica',
        'Terror',
        'Comédia',
        'Drama',
        'Documentário',
        'Musical',
        'Educativo',
        'Faroeste',
        'Romance',
        'Humor Negro',
        'Política',
        'Social',
        'Poético',
        'Surrealismo',
        'Abstrato',
    ]

    def handle(self, *args, **options):
        for antigo, novo in self.DEFEITOS.items():
            antiga = Tag.objects.filter(nome=antigo).first()
            if antiga and not Tag.objects.filter(nome=novo).exists():
                antiga.nome = novo
                antiga.save(update_fields=['nome'])
                self.stdout.write(self.style.WARNING(
                    f'Renomeada tag "{antigo}" para "{novo}".'
                ))

        criadas = 0
        for nome in self.TAGS:
            _, created = Tag.objects.get_or_create(
                nome=nome, defaults={'sistema': True}
            )
            if created:
                criadas += 1
        self.stdout.write(self.style.SUCCESS(
            f'{criadas} tags criadas. Total: {Tag.objects.count()}'
        ))