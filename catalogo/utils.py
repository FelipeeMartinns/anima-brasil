"""Utilitários de queryset do app catalogo."""

from django.db import models
from django.db.models import Count, OuterRef, Subquery

from .models import Comentario, Curtida, Favorito


def _subcontagem(modelo):
    """Subquery que conta o total de registros de `modelo` por animação.

    Usa uma subconsulta independente para que o resultado não seja afetado
    por filtros aplicados na query externa (ex.: "conteudo=curtidas").
    """
    return Subquery(
        modelo.objects.filter(animacao=OuterRef('pk'))
        .values('animacao')
        .annotate(total=Count('pk'))
        .values('total'),
        output_field=models.IntegerField(),
    )


def animacoes_com_contadores(queryset):
    """Anota n_curtidas/n_favoritos/n_comentarios sem joins que inflam as linhas."""
    return queryset.annotate(
        n_curtidas=_subcontagem(Curtida),
        n_favoritos=_subcontagem(Favorito),
        n_comentarios=_subcontagem(Comentario),
    )