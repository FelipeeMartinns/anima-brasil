"""Cria dados de exemplo para desenvolvimento. Uso: python manage.py seed_demo"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import Profile
from catalogo.models import Animacao, Comentario, Curtida, Destaque, Favorito, Tag
from moderacao.models import Enquete, OpcaoEnquete

User = get_user_model()


class Command(BaseCommand):
    help = 'Cria animações, usuários e enquetes de exemplo.'

    def handle(self, *args, **options):
        # Usuários
        usuario, _ = User.objects.get_or_create(
            username='animador_demo',
            defaults={'email': 'demo@demo.com', 'first_name': 'Maria'},
        )
        usuario.set_password('demo12345')
        usuario.save()
        usuario.profile.nome_estudio = 'Estúdio Demo'
        usuario.profile.descricao = 'Estúdio independente de animação brasileira.'
        usuario.profile.instagram = 'https://instagram.com/estudiodemo'
        usuario.profile.youtube = 'https://youtube.com/@estudiodemo'
        usuario.profile.save()

        # Tags
        tag_2d = Tag.objects.get_or_create(nome='Animação 2D', defaults={'sistema': True})[0]
        tag_fantasia = Tag.objects.get_or_create(nome='Fantasia', defaults={'sistema': True})[0]
        tag_stop = Tag.objects.get_or_create(nome='Stop Motion', defaults={'sistema': True})[0]
        tag_drama = Tag.objects.get_or_create(nome='Drama', defaults={'sistema': True})[0]

        animacoes = [
            {
                'titulo': 'O Menino e o Rio',
                'ano': 2023,
                'diretor': 'Maria Souza',
                'estudio': 'Estúdio Demo',
                'classificacao': 'L',
                'duracao': 12,
                'sinopse': 'Um menino do interior descobre um rio secreto '
                           'habitado por criaturas fantásticas que precisam de ajuda.',
                'tags': [tag_2d, tag_fantasia],
                'link': 'https://www.youtube.com',
            },
            {
                'titulo': 'Cidade de Papel',
                'ano': 2022,
                'diretor': 'João Oliveira',
                'estudio': 'Papelex Lab',
                'classificacao': '10',
                'duracao': 8,
                'sinopse': 'Uma cidade construída inteiramente de papel ganha vida '
                           'quando seu criador parte em viagem.',
                'tags': [tag_stop],
                'link': 'https://vimeo.com',
            },
            {
                'titulo': 'Maré Baixa',
                'ano': 2024,
                'diretor': 'Ana Costa',
                'estudio': 'Maré Animação',
                'classificacao': '12',
                'duracao': 15,
                'sinopse': 'Na vila de pescadores, a maré baixa revela memórias '
                           'de uma comunidade que luta para preservar suas tradições.',
                'tags': [tag_2d, tag_drama],
                'link': 'https://www.youtube.com',
            },
        ]

        for dados in animacoes:
            animacao, created = Animacao.objects.get_or_create(
                titulo=dados['titulo'],
                defaults={
                    'ano_lancamento': dados['ano'],
                    'diretor': dados['diretor'],
                    'estudio': dados['estudio'],
                    'classificacao': dados['classificacao'],
                    'duracao': dados['duracao'],
                    'sinopse': dados['sinopse'],
                    'link': dados['link'],
                    'criador': usuario,
                },
            )
            if created:
                animacao.tags.set(dados['tags'])
                self.stdout.write(self.style.SUCCESS(f'  + {animacao.titulo}'))

        # Interações
        if not Curtida.objects.exists():
            for animacao in Animacao.objects.all()[:3]:
                Curtida.objects.get_or_create(animacao=animacao, usuario=usuario)
                Favorito.objects.get_or_create(animacao=animacao, usuario=usuario)
            Comentario.objects.create(
                animacao=Animacao.objects.first(),
                usuario=usuario,
                conteudo='Animação incrível, finalmente a animação independiente '
                         'brasileira sendo valorizada!',
            )

        # Destaque
        primeira = Animacao.objects.first()
        Destaque.objects.get_or_create(
            animacao=primeira, defaults={'titulo_destaque': primeira.titulo}
        )

        # Enquete
        enquete, _ = Enquete.objects.get_or_create(
            titulo='Qual técnica de animação você mais admira?',
            defaults={
                'descricao': 'Ajude a comunidade a conhecer as técnicas favoritas.',
                'encerra_em': timezone.now() + timezone.timedelta(days=30),
                'criador': User.objects.get(username='admin'),
            },
        )
        for texto in ['2D tradicional', '3D', 'Stop Motion', 'Experimental']:
            OpcaoEnquete.objects.get_or_create(enquete=enquete, texto=texto)

        self.stdout.write(self.style.SUCCESS(
            f'Dados de exemplo prontos. Usuário demo: animador_demo / demo12345'
        ))