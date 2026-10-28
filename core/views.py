from django.shortcuts import render

from catalogo.models import Animacao, Destaque, Tag
from catalogo.utils import animacoes_com_contadores
from moderacao.models import Enquete


def index(request):
    destaques = Destaque.objects.select_related('animacao').filter(
        ativo=True, animacao__aprovada=True, animacao__bloqueada=False
    )[:3]
    animacoes = animacoes_com_contadores(
        Animacao.objects.filter(aprovada=True, bloqueada=False)
        .select_related('criador')
        .prefetch_related('tags')
        .order_by('-criado_em')[:12]
    )
    tags = Tag.objects.all()[:20]
    enquete = None
    for candidata in (
        Enquete.objects.filter(status='aberta')
        .select_related('criador')
        .prefetch_related('opcoes', 'opcoes__votos')
    ):
        candidata.fechar_se_expirada()
        enquete = candidata
        break

    context = {
        'destaques': destaques,
        'animacoes': animacoes,
        'tags': tags,
        'enquete': enquete,
    }
    return render(request, 'core/index.html', context)