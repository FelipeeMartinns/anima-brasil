from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class MensagemAdmin(models.Model):
    """Mensagem enviada pelo administrador a um usuário."""

    remetente = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='mensagens_enviadas'
    )
    destinatario = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='mensagens_recebidas'
    )
    assunto = models.CharField('Assunto', max_length=150)
    conteudo = models.TextField('Conteúdo')
    lida = models.BooleanField('Lida', default=False)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']

    def __str__(self):
        return f'{self.assunto} para {self.destinatario.username}'


class Enquete(models.Model):
    """Enquete criada pelo administrador, com prazo e opções de voto."""

    STATUS_CHOICES = [
        ('aberta', 'Aberta'),
        ('fechada', 'Fechada'),
    ]

    titulo = models.CharField('Título', max_length=200)
    descricao = models.TextField('Descrição', blank=True, default='')
    criador = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='enquetes_criadas'
    )
    aberta_em = models.DateTimeField(auto_now_add=True)
    encerra_em = models.DateTimeField('Encerra em', null=True, blank=True)
    status = models.CharField(
        'Status', max_length=10, choices=STATUS_CHOICES, default='aberta'
    )
    apenas_logados = models.BooleanField('Votação restrita a usuários logados', default=False)

    class Meta:
        ordering = ['-aberta_em']

    def __str__(self):
        return self.titulo

    @property
    def esta_aberta(self) -> bool:
        if self.status != 'aberta':
            return False
        if self.encerra_em and timezone.now() > self.encerra_em:
            return False
        return True

    def fechar_se_expirada(self):
        if self.status == 'aberta' and self.encerra_em and timezone.now() > self.encerra_em:
            self.status = 'fechada'
            self.save(update_fields=['status'])


class OpcaoEnquete(models.Model):
    enquete = models.ForeignKey(
        Enquete, on_delete=models.CASCADE, related_name='opcoes'
    )
    texto = models.CharField('Opção', max_length=200)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f'{self.enquete.titulo} -> {self.texto}'

    @property
    def total_votos(self) -> int:
        return self.votos.count()


class Voto(models.Model):
    """Voto de um usuário numa opção da enquete (um voto por usuário por enquete)."""

    opcao = models.ForeignKey(
        OpcaoEnquete, on_delete=models.CASCADE, related_name='votos'
    )
    usuario = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='votos',
        null=True, blank=True, help_text='Votos de anônimos ficam sem usuário.',
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['opcao', 'usuario'], condition=models.Q(usuario__isnull=False),
                name='voto_usuario_unico',
            ),
        ]

    def __str__(self):
        return f'{self.usuario.username if self.usuario else "Anônimo"} votou em {self.opcao.texto}'