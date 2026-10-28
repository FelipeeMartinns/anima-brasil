from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.db import models
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from catalogo.models import Animacao
from catalogo.utils import animacoes_com_contadores

from .forms import LoginForm, ProfileForm, RegistroForm
from .models import Profile


def _bloqueado(chave: str) -> bool:
    return cache.get(chave, 0) >= settings.LOGIN_MAX_ATTEMPTS


def _registrar_falha(chave: str) -> int:
    total = cache.get(chave, 0) + 1
    cache.set(chave, total, settings.LOGIN_LOCKOUT_SECONDS)
    return total


def _limpar_falhas(*chaves: str) -> None:
    cache.delete_many(chaves)


def registrar(request):
    if request.user.is_authenticated:
        return redirect('core:index')
    # Honeypot anti-bot: campo escondido "website". Se preenchido, simula
    # sucesso sem criar a conta (bots são descartados silenciosamente).
    if request.method == 'POST' and request.POST.get('website'):
        return redirect('core:index')
    form = RegistroForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, 'Cadastro realizado com sucesso!')
        return redirect('accounts:editar_perfil')
    return render(request, 'accounts/registro.html', {'form': form})


def entrar(request):
    if request.user.is_authenticated:
        return redirect('core:index')
    form = LoginForm(request.POST or None)
    if request.method == 'POST':
        ip = request.META.get('REMOTE_ADDR', 'desconhecido')
        chave_ip = f'login_falhas:{ip}'
        if _bloqueado(chave_ip):
            messages.error(
                request,
                'Muitas tentativas de login a partir deste endereço. '
                f'Tente novamente em {settings.LOGIN_LOCKOUT_SECONDS // 60} minutos.',
            )
            return render(request, 'accounts/login.html', {'form': form})

        chave_usuario = None
        if form.is_valid():
            username = form.cleaned_data['username']
            chave_usuario = f'login_falhas_usuario:{username.lower()}'
            if _bloqueado(chave_usuario):
                # Mensagem genérica (igual à de IP) para não revelar
                # quais contas existem.
                messages.error(
                    request,
                    'Muitas tentativas de login. '
                    f'Tente novamente em {settings.LOGIN_LOCKOUT_SECONDS // 60} minutos.',
                )
                return render(request, 'accounts/login.html', {'form': form})

            from django.contrib.auth import authenticate
            user = authenticate(
                request,
                username=username,
                password=form.cleaned_data['password'],
            )
            if user:
                _limpar_falhas(chave_ip, chave_usuario)
                if getattr(user.profile, 'bloqueado', False):
                    messages.error(
                        request,
                        'Seu perfil foi bloqueado pelo administrador. '
                        f'Motivo: {user.profile.motivo_bloqueio or "não informado."}',
                    )
                else:
                    login(request, user)
                    return redirect('accounts:dashboard')
            else:
                _registrar_falha(chave_ip)
                if chave_usuario:
                    _registrar_falha(chave_usuario)
                messages.error(request, 'Usuário ou senha inválidos.')
    return render(request, 'accounts/login.html', {'form': form})


@require_POST
@login_required
def sair(request):
    logout(request)
    messages.success(request, 'Você saiu da sua conta.')
    return redirect('core:index')


@login_required
def dashboard(request):
    animacoes = animacoes_com_contadores(
        request.user.animacoes.prefetch_related('tags')
    )
    comentarios = request.user.comentarios.select_related('animacao')[:10]
    favoritos = request.user.favoritos.select_related('animacao')
    curtidas = request.user.curtidas.select_related('animacao')
    profile = request.user.profile

    context = {
        'animacoes': animacoes,
        'comentarios': comentarios,
        'favoritos': favoritos,
        'curtidas': curtidas,
        'profile': profile,
    }
    return render(request, 'accounts/dashboard.html', context)


@login_required
def editar_perfil(request):
    profile = request.user.profile
    form = ProfileForm(request.POST or None, request.FILES or None, instance=profile)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Perfil atualizado com sucesso.')
        return redirect('accounts:perfil', username=request.user.username)
    return render(request, 'accounts/editar_perfil.html', {'form': form})


def perfil_publico(request, username):
    profile = get_object_or_404(
        Profile.objects.select_related('user').prefetch_related('user__favoritos', 'user__curtidas'),
        user__username=username,
    )
    if profile.bloqueado:
        if not (request.user.is_staff or request.user.is_superuser):
            return render(request, 'accounts/perfil_bloqueado.html', {'profile': profile})

    animacoes = animacoes_com_contadores(
        Animacao.objects.filter(criador__username=username, aprovada=True, bloqueada=False)
        .prefetch_related('tags')
    )
    comentarios = profile.user.comentarios.select_related('animacao').all()

    favoritos = curtidos = None
    esta_ativo = models.Q(animacao__aprovada=True, animacao__bloqueada=False)
    if request.user == profile.user:
        # O dono sempre vê a própria atividade, mesmo que marcada como privada.
        favoritos = profile.user.favoritos.select_related('animacao')
        curtidos = profile.user.curtidas.select_related('animacao')
    else:
        # Visitantes só veem o que o dono marcou como público e nunca
        # animações bloqueadas ou ainda não aprovadas.
        if profile.exibir_favoritos:
            favoritos = profile.user.favoritos.select_related('animacao').filter(esta_ativo)
        if profile.exibir_curtidos:
            curtidos = profile.user.curtidas.select_related('animacao').filter(esta_ativo)
        comentarios = comentarios.filter(esta_ativo)

    context = {
        'perfil': profile,
        'animacoes': animacoes,
        'comentarios': comentarios,
        'favoritos': favoritos,
        'curtidos': curtidos,
    }
    return render(request, 'accounts/perfil_publico.html', context)