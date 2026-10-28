from django.contrib.auth.models import User
from django.db import models

from core.validators import validar_imagem_tamanho


class Profile(models.Model):
    """Perfil público do usuário logado (estúdio/artista)."""

    VISIBILITY_CHOICES = [
        ('publico', 'Público'),
        ('privado', 'Privado'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    nome_estudio = models.CharField(
        'Nome do estúdio', max_length=120, blank=True, default=''
    )
    descricao = models.TextField('Descrição', blank=True, default='')
    avatar = models.ImageField(
        'Avatar', upload_to='avatares/', blank=True, null=True,
        validators=[validar_imagem_tamanho],
    )

    instagram = models.URLField('Instagram', blank=True, default='')
    youtube = models.URLField('YouTube', blank=True, default='')
    site = models.URLField('Site', blank=True, default='')
    outras_plataformas = models.TextField(
        'Outras plataformas', blank=True, default='',
        help_text='Links de outras plataformas, um por linha.',
    )

    visibilidade_favoritos = models.CharField(
        'Visibilidade dos favoritos', max_length=10,
        choices=VISIBILITY_CHOICES, default='publico',
    )
    visibilidade_curtidos = models.CharField(
        'Visibilidade dos curtidos', max_length=10,
        choices=VISIBILITY_CHOICES, default='publico',
    )

    bloqueado = models.BooleanField('Bloqueado pelo administrador', default=False)
    motivo_bloqueio = models.CharField(
        'Motivo do bloqueio', max_length=300, blank=True, default=''
    )

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nome_estudio or self.user.username

    @property
    def exibir_favoritos(self) -> bool:
        return self.visibilidade_favoritos == 'publico'

    @property
    def exibir_curtidos(self) -> bool:
        return self.visibilidade_curtidos == 'publico'
