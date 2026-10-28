from django.conf import settings
from django.core.cache import cache
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from catalogo.models import Animacao
from core.validators import validar_imagem_tamanho

from django.core.exceptions import ValidationError

from .forms import ProfileForm
from .models import Profile


def criar_usuario(username, senha='senha-teste-123', staff=False, superuser=False):
    user = User.objects.create_user(
        username=username, password=senha, email=f'{username}@teste.com'
    )
    if staff or superuser:
        user.is_staff = staff
        user.is_superuser = superuser
        user.save(update_fields=['is_staff', 'is_superuser'])
    return user


class AutenticacaoTests(TestCase):
    def setUp(self):
        cache.clear()
        self.usuario = criar_usuario('fulano')

    def tearDown(self):
        cache.clear()

    def test_login_com_sucesso_redireciona_dashboard(self):
        resp = self.client.post(reverse('accounts:login'), {
            'username': 'fulano', 'password': 'senha-teste-123',
        })
        self.assertRedirects(resp, reverse('accounts:dashboard'))
        self.assertIn('_auth_user_id', self.client.session)

    def test_login_senha_invalida_mostra_erro_e_nao_loga(self):
        resp = self.client.post(reverse('accounts:login'), {
            'username': 'fulano', 'password': 'errada',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Usuário ou senha inválidos')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_login_perfil_bloqueado_impede_logar(self):
        self.usuario.profile.bloqueado = True
        self.usuario.profile.motivo_bloqueio = 'spam'
        self.usuario.profile.save()
        resp = self.client.post(reverse('accounts:login'), {
            'username': 'fulano', 'password': 'senha-teste-123',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'bloqueado pelo administrador')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_rate_limit_bloqueia_apos_muitas_tentativas(self):
        url = reverse('accounts:login')
        for _ in range(settings.LOGIN_MAX_ATTEMPTS):
            self.client.post(url, {'username': 'fulano', 'password': 'errada'})
        # Mesmo acertando a senha, o IP já foi bloqueado.
        resp = self.client.post(url, {
            'username': 'fulano', 'password': 'senha-teste-123',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Muitas tentativas de login')
        self.assertNotIn('_auth_user_id', self.client.session)


class LogoutTests(TestCase):
    def setUp(self):
        cache.clear()
        self.usuario = criar_usuario('fulano')
        self.client.login(username='fulano', password='senha-teste-123')

    def test_logout_via_post_funciona(self):
        resp = self.client.post(reverse('accounts:logout'))
        self.assertRedirects(resp, reverse('core:index'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_logout_via_get_retorna_405(self):
        resp = self.client.get(reverse('accounts:logout'))
        self.assertEqual(resp.status_code, 405)
        self.assertIn('_auth_user_id', self.client.session)


class RegistroTests(TestCase):
    def test_registro_cria_usuario_e_perfil(self):
        resp = self.client.post(reverse('accounts:registro'), {
            'username': 'novato',
            'email': 'novato@teste.com',
            'password1': 'senha-complexa-123',
            'password2': 'senha-complexa-123',
        })
        self.assertRedirects(resp, reverse('accounts:editar_perfil'))
        self.assertTrue(User.objects.filter(username='novato').exists())
        self.assertTrue(Profile.objects.filter(user__username='novato').exists())

    def test_registro_honeypot_descarta_bot_sem_criar_conta(self):
        resp = self.client.post(reverse('accounts:registro'), {
            'website': 'http://bot.example.com',
            'username': 'botzinho',
            'email': 'bot@teste.com',
            'password1': 'senha-complexa-123',
            'password2': 'senha-complexa-123',
        })
        self.assertRedirects(resp, reverse('core:index'))
        self.assertFalse(User.objects.filter(username='botzinho').exists())


class VisibilidadePerfilTests(TestCase):
    def setUp(self):
        self.dono = criar_usuario('dono')
        self.visitante = criar_usuario('visitante')
        self.animacao, _ = Animacao.objects.get_or_create(
            titulo='Anim de Teste',
            defaults={
                'sinopse': 'sinopse', 'ano_lancamento': 2022,
                'diretor': 'Diretor', 'estudio': 'Estúdio',
                'classificacao': 'L', 'duracao': 5, 'criador': self.dono,
            },
        )
        self.dono.favoritos.create(animacao=self.animacao)
        self.dono.curtidas.create(animacao=self.animacao)

    def _ver(self, usuario=None):
        client = Client()
        if usuario:
            client.force_login(usuario)
        return client.get(
            reverse('accounts:perfil', kwargs={'username': self.dono.username})
        )

    def test_visitante_ve_atividade_publica(self):
        resp = self._ver(self.visitante)
        self.assertContains(resp, 'Minha atividade')
        self.assertContains(resp, 'Anim de Teste')

    def test_visitante_nao_ve_atividade_privada(self):
        self.dono.profile.visibilidade_favoritos = 'privado'
        self.dono.profile.visibilidade_curtidos = 'privado'
        self.dono.profile.save()
        resp = self._ver(self.visitante)
        self.assertNotContains(resp, 'Minha atividade')

    def test_dono_sempre_ve_propria_atividade(self):
        self.dono.profile.visibilidade_favoritos = 'privado'
        self.dono.profile.visibilidade_curtidos = 'privado'
        self.dono.profile.save()
        resp = self._ver(self.dono)
        self.assertContains(resp, 'Minha atividade')

    def test_visitante_nao_ve_comentario_de_perfil_bloqueado(self):
        self.dono.profile.bloqueado = True
        self.dono.profile.save()
        resp = self._ver(self.visitante)
        self.assertNotContains(resp, 'Anim de Teste')
        self.assertContains(resp, 'bloqueado')

    def test_visitante_nao_ve_atividade_de_animacao_bloqueada(self):
        self.dono.profile.visibilidade_favoritos = 'publico'
        self.dono.profile.visibilidade_curtidos = 'publico'
        self.dono.profile.save()
        bloqueada = Animacao.objects.create(
            titulo='Anim Proibida Vista', sinopse='s', ano_lancamento=2023,
            diretor='D', estudio='E', classificacao='L', duracao=5,
            criador=self.dono, aprovada=True, bloqueada=True,
        )
        self.dono.favoritos.create(animacao=bloqueada)
        self.dono.curtidas.create(animacao=bloqueada)
        resp = self._ver(self.visitante)
        self.assertContains(resp, 'Anim de Teste')
        self.assertNotContains(resp, 'Anim Proibida Vista')
        self.assertNotContains(resp, 'Proibida Vista')

    def test_dono_ve_propria_atividade_incluindo_bloqueada(self):
        self.dono.profile.visibilidade_favoritos = 'publico'
        self.dono.profile.visibilidade_curtidos = 'publico'
        self.dono.profile.save()
        bloqueada = Animacao.objects.create(
            titulo='Anim Proibida Vista', sinopse='s', ano_lancamento=2023,
            diretor='D', estudio='E', classificacao='L', duracao=5,
            criador=self.dono, aprovada=True, bloqueada=True,
        )
        self.dono.favoritos.create(animacao=bloqueada)
        self.dono.curtidas.create(animacao=bloqueada)
        resp = self._ver(self.dono)
        self.assertContains(resp, 'Anim Proibida Vista')


class FormularioPerfilTests(TestCase):
    def setUp(self):
        self.usuario = criar_usuario('fulano')

    def _form(self, plataformas):
        return ProfileForm({
            'nome_estudio': 'Estúdio X',
            'descricao': '',
            'instagram': '',
            'youtube': '',
            'site': '',
            'outras_plataformas': plataformas,
            'visibilidade_favoritos': 'publico',
            'visibilidade_curtidos': 'publico',
        }, instance=self.usuario.profile)

    def test_rejeita_url_javascript(self):
        form = self._form('https://behance.net/ok\njavascript:alert(1)')
        self.assertFalse(form.is_valid())
        self.assertIn('outras_plataformas', form.errors)

    def test_aceita_apenas_urls_http_https(self):
        form = self._form('https://behance.net/ok\nhttp://vimeo.com/x')
        self.assertTrue(form.is_valid())

    def test_rejeita_url_ftp_no_campo_site(self):
        form = self._form('')
        form.data['site'] = 'ftp://arquivo.example.com/clip.mov'
        self.assertFalse(form.is_valid())
        self.assertIn('site', form.errors)


class ValidadorUploadTests(TestCase):
    def test_rejeita_arquivo_acima_do_limite(self):
        limite = getattr(settings, 'MAX_UPLOAD_SIZE', 5 * 1024 * 1024)
        arquivo = SimpleUploadedFile(
            'grande.bin', b'x' * (limite + 1)
        )
        with self.assertRaises(ValidationError):
            validar_imagem_tamanho(arquivo)

    def test_aceita_arquivo_dentro_do_limite(self):
        limite = getattr(settings, 'MAX_UPLOAD_SIZE', 5 * 1024 * 1024)
        arquivo = SimpleUploadedFile('pequeno.bin', b'x' * (limite // 2))
        # Não deve levantar exceção.
        validar_imagem_tamanho(arquivo)