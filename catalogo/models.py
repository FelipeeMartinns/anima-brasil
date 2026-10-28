from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from accounts.models import Profile
from core.validators import validar_imagem_tamanho


class Tag(models.Model):
    """Tag/gênero atribuível a uma animação.

    Tags pré-definidas pelo sistema podem ser usadas por qualquer usuário;
    usuários logados também podem criar novas tags.
    """

    nome = models.CharField('Nome', max_length=60, unique=True)
    sistema = models.BooleanField('Pré-definida pelo sistema', default=False)
    criador = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='tags_criadas', verbose_name='Criador',
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Animacao(models.Model):
    """Ficha catalográfica de uma animação independente."""

    CLASSIFICACAO_ANCAINE = [
        ('L', 'Livre'),
        ('10', '10 anos'),
        ('12', '12 anos'),
        ('14', '14 anos'),
        ('16', '16 anos'),
        ('18', '18 anos'),
    ]

    titulo = models.CharField('Título', max_length=200)
    sinopse = models.TextField('Sinopse')
    ano_lancamento = models.PositiveIntegerField(
        'Ano de lançamento',
        validators=[MinValueValidator(1900), MaxValueValidator(2100)],
    )
    diretor = models.CharField('Diretor(a)', max_length=200)
    estudio = models.CharField('Estúdio/Produtora', max_length=200)
    classificacao = models.CharField(
        'Classificação indicativa (ANCAINE)', max_length=3,
        choices=CLASSIFICACAO_ANCAINE, default='L',
    )
    duracao = models.PositiveIntegerField(
        'Duração (minutos)', validators=[MinValueValidator(1)]
    )
    imagem = models.ImageField(
        'Imagem de capa', upload_to='animacoes/', blank=True, null=True,
        validators=[validar_imagem_tamanho],
    )
    imagem_url = models.URLField('URL da imagem', blank=True, default='')
    link = models.URLField('Link onde está hospedado', blank=True, default='')

    tags = models.ManyToManyField(Tag, related_name='animacoes', verbose_name='Tags')
    criador = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='animacoes',
        verbose_name='Cadastrada por',
        help_text='Usuário/animação cadastrado no sistema.',
    )

    aprovada = models.BooleanField('Aprovada', default=True)
    bloqueada = models.BooleanField('Bloqueada', default=False)
    motivo_bloqueio = models.CharField(
        'Motivo do bloqueio', max_length=300, blank=True, default=''
    )

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-ano_lancamento', 'titulo']

    def __str__(self):
        return self.titulo

    @property
    def total_curtidas(self) -> int:
        return self.curtidas.count()

    @property
    def total_favoritos(self) -> int:
        return self.favoritos.count()

    @property
    def total_comentarios(self) -> int:
        return self.comentarios.count()


class Comentario(models.Model):
    """Comentário de um usuário numa animação."""

    animacao = models.ForeignKey(
        Animacao, on_delete=models.CASCADE, related_name='comentarios'
    )
    usuario = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='comentarios'
    )
    conteudo = models.TextField('Comentário')
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['criado_em']

    def __str__(self):
        return f'{self.usuario.username} em {self.animacao.titulo}'


class Curtida(models.Model):
    """Coração dado por um usuário numa animação."""

    animacao = models.ForeignKey(
        Animacao, on_delete=models.CASCADE, related_name='curtidas'
    )
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='curtidas')
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['animacao', 'usuario'], name='curtida_unica'),
        ]

    def __str__(self):
        return f'{self.usuario.username} curtiu {self.animacao.titulo}'


class Favorito(models.Model):
    """Favorito (marcador) dado por um usuário numa animação."""

    animacao = models.ForeignKey(
        Animacao, on_delete=models.CASCADE, related_name='favoritos'
    )
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favoritos')
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['animacao', 'usuario'], name='favorito_unico'),
        ]

    def __str__(self):
        return f'{self.usuario.username} favoritou {self.animacao.titulo}'


class Destaque(models.Model):
    """Animação destacada pelo administrador na página inicial."""

    animacao = models.ForeignKey(
        Animacao, on_delete=models.CASCADE, related_name='destaques'
    )
    titulo_destaque = models.CharField('Título do destaque', max_length=120, blank=True, default='')
    ativo = models.BooleanField('Ativo', default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']
        constraints = [
            models.UniqueConstraint(
                fields=['animacao'], condition=models.Q(ativo=True),
                name='destaque_ativo_unico',
            ),
        ]

    def __str__(self):
        return f'Destaque: {self.animacao.titulo}'