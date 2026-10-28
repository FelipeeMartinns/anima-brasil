from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db import IntegrityError, models
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.models import Profile
from catalogo.models import Animacao, Comentario, Destaque
from moderacao.models import Enquete, MensagemAdmin, OpcaoEnquete, Voto

from .forms import BloqueioForm, EnqueteForm, MensagemAdminForm, OpcoesEnqueteForm

@login_required
def minhas_mensagens(request):
    mensagens = request.user.mensagens_recebidas.select_related('remetente').all()
    nao_lidas = mensagens.filter(lida=False).count()
    paginator = Paginator(mensagens, 15)
    page_obj = paginator.get_page(request.GET.get('page'))
    context = {
        'mensagens': page_obj.object_list,
        'nao_lidas': nao_lidas,
        'page_obj': page_obj,
        'base_pagina': '?',
    }
    return render(request, 'moderacao/mensagens.html', context)


@require_POST
@login_required
def marcar_lida(request, pk):
    mensagem = get_object_or_404(MensagemAdmin, pk=pk, destinatario=request.user)
    mensagem.lida = True
    mensagem.save(update_fields=['lida'])
    return redirect('moderacao:minhas_mensagens')


def enquetes(request):
    enquetes = Enquete.objects.prefetch_related('opcoes__votos').all()
    for enquete in enquetes:
        enquete.fechar_se_expirada()

    encerradas = []
    abertas = []
    for enquete in enquetes:
        (abertas if enquete.esta_aberta else encerradas).append(_montar_enquete(enquete, request))

    context = {'abertas': abertas, 'encerradas': encerradas}
    return render(request, 'moderacao/enquetes.html', context)


def _porcentagem(opcoes):
    total = sum(opcao.total_votos for opcao in opcoes)
    for opcao in opcoes:
        opcao.percentual = (opcao.total_votos / total * 100) if total else 0
    return total


def _montar_enquete(enquete, request):
    _porcentagem(enquete.opcoes.all())
    votou = False
    voto_usuario = None
    if request.user.is_authenticated:
        voto_usuario = Voto.objects.filter(opcao__enquete=enquete, usuario=request.user).first()
        votou = voto_usuario is not None
    enquete.votou = votou
    enquete.voto_usuario = voto_usuario
    return enquete


@require_POST
def votar(request, pk):
    enquete = get_object_or_404(Enquete, pk=pk)
    enquete.fechar_se_expirada()
    if not enquete.esta_aberta:
        messages.error(request, 'Esta enquete não está mais aberta.')
        return redirect('moderacao:enquetes')

    usuario = request.user if request.user.is_authenticated else None
    if usuario is None and enquete.apenas_logados:
        messages.error(request, 'Só usuários logados podem votar nesta enquete.')
        return redirect('moderacao:enquetes')

    if usuario is not None:
        if Voto.objects.filter(opcao__enquete=enquete, usuario=usuario).exists():
            messages.info(request, 'Você já votou nesta enquete.')
            return redirect('moderacao:enquetes')
    elif request.session.get(f'votou_enquete_{enquete.pk}'):
        messages.info(request, 'Você já votou nesta enquete.')
        return redirect('moderacao:enquetes')

    opcao_id = request.POST.get('opcao')
    opcao = OpcaoEnquete.objects.filter(pk=opcao_id, enquete=enquete).first()
    if not opcao:
        messages.error(request, 'Opção inválida.')
        return redirect('moderacao:enquetes')

    try:
        Voto.objects.create(opcao=opcao, usuario=usuario)
    except IntegrityError:
        # Dois cliques (ou abas) simultâneos: constraint única já registrou o voto.
        messages.info(request, 'Você já votou nesta enquete.')
        return redirect('moderacao:enquetes')
    if usuario is None:
        request.session[f'votou_enquete_{enquete.pk}'] = True
    messages.success(request, 'Voto registrado!')
    return redirect('moderacao:enquetes')


# ---------------- Painel do administrador ----------------


@staff_member_required
def painel(request):
    total_animacoes = Animacao.objects.count()
    total_usuarios = User.objects.count()
    aguardando = Animacao.objects.filter(aprovada=False).count()
    bloqueadas = Animacao.objects.filter(bloqueada=True).count()
    perfis_bloqueados = Profile.objects.filter(bloqueado=True).count()
    enquetes_abertas = Enquete.objects.filter(status='aberta').count()

    context = {
        'total_animacoes': total_animacoes,
        'total_usuarios': total_usuarios,
        'aguardando': aguardando,
        'bloqueadas': bloqueadas,
        'perfis_bloqueados': perfis_bloqueados,
        'enquetes_abertas': enquetes_abertas,
    }
    return render(request, 'moderacao/painel.html', context)


@staff_member_required
def listar_animacoes_admin(request):
    animacoes = (
        Animacao.objects.select_related('criador')
        .prefetch_related('tags')
        .prefetch_related(
            models.Prefetch(
                'destaques',
                queryset=Destaque.objects.filter(ativo=True),
                to_attr='destaques_ativos',
            )
        )
    )
    paginator = Paginator(animacoes, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    context = {
        'animacoes': page_obj.object_list,
        'page_obj': page_obj,
        'base_pagina': '?',
    }
    return render(request, 'moderacao/listar_animacoes.html', context)


@staff_member_required
def listar_perfis_admin(request):
    perfis = Profile.objects.select_related('user').all()
    paginator = Paginator(perfis, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(
        request,
        'moderacao/listar_perfis.html',
        {'perfis': page_obj.object_list, 'page_obj': page_obj, 'base_pagina': '?'},
    )


@require_POST
@staff_member_required
def toggle_aprovacao(request, pk):
    animacao = get_object_or_404(Animacao, pk=pk)
    animacao.aprovada = not animacao.aprovada
    animacao.save(update_fields=['aprovada'])
    messages.success(request, f'Aprovação de "{animacao.titulo}" atualizada.')
    return redirect('moderacao:listar_animacoes')


@staff_member_required
def bloquear_animacao(request, pk):
    animacao = get_object_or_404(Animacao, pk=pk)
    if request.method == 'POST':
        form = BloqueioForm(request.POST)
        if form.is_valid():
            animacao.bloqueada = True
            animacao.motivo_bloqueio = form.cleaned_data['motivo']
            animacao.save(update_fields=['bloqueada', 'motivo_bloqueio'])
            messages.warning(request, f'Animação "{animacao.titulo}" bloqueada.')
            return redirect('moderacao:listar_animacoes')
    else:
        form = BloqueioForm()
    return render(request, 'moderacao/bloquear_animacao.html', {'form': form, 'animacao': animacao})


@require_POST
@staff_member_required
def desbloquear_animacao(request, pk):
    animacao = get_object_or_404(Animacao, pk=pk)
    animacao.bloqueada = False
    animacao.motivo_bloqueio = ''
    animacao.save(update_fields=['bloqueada', 'motivo_bloqueio'])
    messages.success(request, f'Animação "{animacao.titulo}" desbloqueada.')
    return redirect('moderacao:listar_animacoes')


@require_POST
@staff_member_required
def apagar_animacao(request, pk):
    animacao = get_object_or_404(Animacao, pk=pk)
    titulo = animacao.titulo
    animacao.delete()
    messages.success(request, f'Animação "{titulo}" apagada.')
    return redirect('moderacao:listar_animacoes')


@staff_member_required
def bloquear_perfil(request, username):
    profile = get_object_or_404(Profile.objects.select_related('user'), user__username=username)
    if profile.user == request.user:
        messages.error(request, 'Você não pode bloquear o seu próprio perfil.')
        return redirect('moderacao:listar_perfis')
    if profile.user.is_superuser and not request.user.is_superuser:
        messages.error(request, 'Apenas um superusuário pode bloquear outro superusuário.')
        return redirect('moderacao:listar_perfis')
    if request.method == 'POST':
        form = BloqueioForm(request.POST)
        if form.is_valid():
            profile.bloqueado = True
            profile.motivo_bloqueio = form.cleaned_data['motivo']
            profile.save(update_fields=['bloqueado', 'motivo_bloqueio'])
            messages.warning(request, f'Perfil de "{username}" bloqueado.')
            return redirect('moderacao:listar_perfis')
    else:
        form = BloqueioForm()
    return render(request, 'moderacao/bloquear_perfil.html', {'form': form, 'perfil': profile})


@require_POST
@staff_member_required
def desbloquear_perfil(request, username):
    profile = get_object_or_404(Profile.objects.select_related('user'), user__username=username)
    if profile.user.is_superuser and not request.user.is_superuser:
        messages.error(request, 'Apenas um superusuário pode desbloquear outro superusuário.')
        return redirect('moderacao:listar_perfis')
    profile.bloqueado = False
    profile.motivo_bloqueio = ''
    profile.save(update_fields=['bloqueado', 'motivo_bloqueio'])
    messages.success(request, f'Perfil de "{username}" desbloqueado.')
    return redirect('moderacao:listar_perfis')


@require_POST
@staff_member_required
def apagar_perfil(request, username):
    user = get_object_or_404(User, username=username)
    if user == request.user:
        messages.error(request, 'Você não pode apagar o seu próprio perfil.')
        return redirect('moderacao:listar_perfis')
    if user.is_superuser and not request.user.is_superuser:
        messages.error(request, 'Apenas um superusuário pode apagar outro superusuário.')
        return redirect('moderacao:listar_perfis')
    nome = user.username
    user.delete()
    messages.success(request, f'Perfil "{nome}" apagado.')
    return redirect('moderacao:listar_perfis')


@staff_member_required
def enviar_mensagem(request, username=None):
    if request.method == 'POST' and not username:
        messages.error(request, 'Selecione um destinatário para a mensagem.')
        return redirect('moderacao:listar_perfis')
    destinatario = get_object_or_404(User, username=username) if username else None
    form = MensagemAdminForm(request.POST or None, initial={'assunto': ''})
    if request.method == 'POST' and form.is_valid():
        if destinatario is None:
            messages.error(request, 'Selecione um destinatário para a mensagem.')
            return redirect('moderacao:listar_perfis')
        msg = form.save(commit=False)
        msg.remetente = request.user
        msg.destinatario = destinatario
        msg.save()
        messages.success(request, f'Mensagem enviada para {destinatario.username}.')
        return redirect('moderacao:listar_perfis')
    return render(
        request, 'moderacao/enviar_mensagem.html',
        {'form': form, 'destinatario': destinatario},
    )


@staff_member_required
def criar_enquete(request):
    form_enquete = EnqueteForm(request.POST or None)
    form_opcoes = OpcoesEnqueteForm(request.POST or None)
    if request.method == 'POST' and form_enquete.is_valid() and form_opcoes.is_valid():
        enquete = form_enquete.save(commit=False)
        enquete.criador = request.user
        enquete.save()
        textos = [
            form_opcoes.cleaned_data['opcao_1'],
            form_opcoes.cleaned_data['opcao_2'],
            form_opcoes.cleaned_data['opcao_3'],
            form_opcoes.cleaned_data['opcao_4'],
        ]
        for texto in textos:
            if texto:
                OpcaoEnquete.objects.create(enquete=enquete, texto=texto.strip())
        messages.success(request, 'Enquete criada com sucesso.')
        return redirect('moderacao:enquetes')
    return render(
        request, 'moderacao/criar_enquete.html',
        {'form_enquete': form_enquete, 'form_opcoes': form_opcoes},
    )


@require_POST
@staff_member_required
def fechar_enquete(request, pk):
    enquete = get_object_or_404(Enquete, pk=pk)
    enquete.status = 'fechada'
    enquete.save(update_fields=['status'])
    messages.success(request, 'Enquete fechada.')
    return redirect('moderacao:enquetes')


@require_POST
@staff_member_required
def criar_destaque(request, pk):
    animacao = get_object_or_404(Animacao, pk=pk)
    if not animacao.aprovada or animacao.bloqueada:
        messages.error(
            request,
            'Não é possível destacar uma animação bloqueada ou não aprovada.',
        )
        return redirect('moderacao:listar_animacoes')
    try:
        Destaque.objects.create(animacao=animacao, titulo_destaque=animacao.titulo)
        messages.success(request, 'Animação adicionada aos destaques.')
    except Exception:
        messages.error(request, 'Esta animação já está destacada na home.')
    return redirect('moderacao:listar_animacoes')


@require_POST
@staff_member_required
def remover_destaque(request, pk):
    get_object_or_404(Destaque, pk=pk).delete()
    messages.success(request, 'Destaque removido.')
    return redirect('moderacao:listar_animacoes')