from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import AnimacaoForm, ComentarioForm
from .models import Animacao, Comentario, Curtida, Favorito, Tag
from .utils import animacoes_com_contadores


def catalogo(request):
    animacoes = (
        Animacao.objects.filter(aprovada=True, bloqueada=False)
        .select_related('criador')
        .prefetch_related('tags')
    )
    tags = Tag.objects.all()

    q = request.GET.get('q', '').strip()
    tag_ids = request.GET.getlist('tag')
    classificacao = request.GET.get('classificacao', '').strip()

    if q:
        animacoes = animacoes.filter(
            models_q_titulo_sinopse_diretor_estudio(q)
        )
    if tag_ids:
        tag_ids_int = [int(i) for i in tag_ids if i.isdigit()]
        animacoes = animacoes.filter(tags__id__in=tag_ids_int).distinct()
    if classificacao:
        animacoes = animacoes.filter(classificacao=classificacao)

    conteudo = request.GET.get('conteudo', '')
    if conteudo == 'curtidas' and request.user.is_authenticated:
        animacoes = animacoes.filter(curtidas__usuario=request.user)
    elif conteudo == 'favoritos' and request.user.is_authenticated:
        animacoes = animacoes.filter(favoritos__usuario=request.user)

    animacoes = animacoes_com_contadores(animacoes).order_by('-criado_em')

    paginator = Paginator(animacoes, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    qs_filtros = request.GET.copy()
    qs_filtros.pop('page', None)
    querystring = qs_filtros.urlencode()
    base_pagina = f'?{querystring}&' if querystring else '?'

    context = {
        'animacoes': page_obj.object_list,
        'tags': tags,
        'tag_selecionadas': tag_ids,
        'q': q,
        'classificacao': classificacao,
        'classificacoes': Animacao.CLASSIFICACAO_ANCAINE,
        'page_obj': page_obj,
        'base_pagina': base_pagina,
    }
    return render(request, 'catalogo/catalogo.html', context)


def models_q_titulo_sinopse_diretor_estudio(q):
    from django.db.models import Q
    return Q(titulo__icontains=q) | Q(sinopse__icontains=q) | Q(
        diretor__icontains=q) | Q(estudio__icontains=q)


def _interacao_permitida(animacao, user):
    """Apenas animações aprovadas e não bloqueadas aceitam interação pública."""
    if not animacao.aprovada or animacao.bloqueada:
        return user.is_staff or user.is_superuser
    return True


def _contexto_detalhe(animacao, request, form_comentario=None):
    comentarios = animacao.comentarios.select_related('usuario').all()

    ja_curtiu = ja_favoritou = False
    if request.user.is_authenticated:
        if form_comentario is None:
            form_comentario = ComentarioForm()
        ja_curtiu = Curtida.objects.filter(animacao=animacao, usuario=request.user).exists()
        ja_favoritou = Favorito.objects.filter(animacao=animacao, usuario=request.user).exists()

    return {
        'animacao': animacao,
        'comentarios': comentarios,
        'form_comentario': form_comentario,
        'ja_curtiu': ja_curtiu,
        'ja_favoritou': ja_favoritou,
    }


def detalhe(request, pk):
    animacao = get_object_or_404(
        Animacao.objects.select_related('criador').prefetch_related('tags'),
        pk=pk,
    )
    if animacao.bloqueada and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'catalogo/bloqueada.html', {'animacao': animacao})
    if not animacao.aprovada and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'catalogo/nao_aprovada.html', {'animacao': animacao})

    return render(request, 'catalogo/detalhe.html', _contexto_detalhe(animacao, request))


@login_required
def criar_animacao(request):
    form = AnimacaoForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        form.salvar_com_tags(request.user)
        messages.success(request, 'Animação cadastrada com sucesso!')
        return redirect('accounts:dashboard')
    return render(request, 'catalogo/form_animacao.html', {'form': form, 'acao': 'Cadastrar'})


@login_required
def editar_animacao(request, pk):
    if not request.user.is_staff and not request.user.is_superuser:
        animacao = get_object_or_404(Animacao, pk=pk, criador=request.user)
    else:
        animacao = get_object_or_404(Animacao, pk=pk)

    form = AnimacaoForm(request.POST or None, request.FILES or None, instance=animacao)
    if request.method == 'POST' and form.is_valid():
        form.salvar_com_tags(request.user)
        messages.success(request, 'Animação atualizada com sucesso.')
        return redirect('catalogo:detalhe', pk=animacao.pk)
    return render(request, 'catalogo/form_animacao.html', {'form': form, 'acao': 'Editar'})


@require_POST
@login_required
def curtir(request, pk):
    animacao = get_object_or_404(Animacao, pk=pk)
    if not _interacao_permitida(animacao, request.user):
        return JsonResponse(
            {'erro': 'Não é possível curtir uma animação bloqueada ou não aprovada.'},
            status=403,
        )
    curtida, created = Curtida.objects.get_or_create(animacao=animacao, usuario=request.user)
    if not created:
        curtida.delete()
    return JsonResponse({'curtiu': created, 'total': animacao.curtidas.count()})


@require_POST
@login_required
def favoritar(request, pk):
    animacao = get_object_or_404(Animacao, pk=pk)
    if not _interacao_permitida(animacao, request.user):
        return JsonResponse(
            {'erro': 'Não é possível favoritar uma animação bloqueada ou não aprovada.'},
            status=403,
        )
    favorito, created = Favorito.objects.get_or_create(animacao=animacao, usuario=request.user)
    if not created:
        favorito.delete()
    return JsonResponse({'favoritou': created, 'total': animacao.favoritos.count()})


@require_POST
@login_required
def comentar(request, pk):
    animacao = get_object_or_404(Animacao, pk=pk)
    if not _interacao_permitida(animacao, request.user):
        messages.error(
            request, 'Não é possível comentar em uma animação bloqueada ou não aprovada.'
        )
        return redirect('catalogo:catalogo')
    form = ComentarioForm(request.POST)
    if form.is_valid():
        comentario = form.save(commit=False)
        comentario.animacao = animacao
        comentario.usuario = request.user
        comentario.save()
        messages.success(request, 'Comentário publicado.')
        return redirect('catalogo:detalhe', pk=animacao.pk)
    return render(
        request, 'catalogo/detalhe.html',
        _contexto_detalhe(animacao, request, form),
    )