from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from django.urls import reverse

from catalogo.models import Animacao, Destaque
from .models import Enquete, MensagemAdmin, OpcaoEnquete, Voto
from . import views
from .forms import EnqueteForm


def usuario_limpo(username, **flag):
    """Cria usuário; se flag['staff'] ou flag['superuser'], aplica."""
    user = User.objects.get_or_create(username=username)[0]
    if flag.get('staff') or flag.get('superuser'):
        if flag.get('superuser'):
            user.is_superuser = True
        user.is_staff = True
        user.save(update_fields=['is_staff', 'is_superuser'])
    return user


def criar_animacao(titulo, criador, bloqueada=False, aprovada=True):
    return Animacao.objects.create(
        titulo=titulo, sinopse='s', ano_lancamento=2022, diretor='d',
        estudio='e', classificacao='L', duracao=5, criador=criador,
        aprovada=aprovada, bloqueada=bloqueada,
    )


class PainelTests(TestCase):
    def setUp(self):
        self.staff = usuario_limpo('staff_painel', staff=True)
        self.comum = usuario_limpo('comum_painel')

    def test_painel_exige_staff(self):
        resp = self.client.get(reverse('moderacao:painel'))
        self.assertEqual(resp.status_code, 302)
        self.client.force_login(self.comum)
        resp = self.client.get(reverse('moderacao:painel'))
        self.assertEqual(resp.status_code, 302)

    def test_staff_acessa_o_painel(self):
        self.client.force_login(self.staff)
        resp = self.client.get(reverse('moderacao:painel'))
        self.assertEqual(resp.status_code, 200)


class MutacoesPostTests(TestCase):
    def setUp(self):
        self.staff = usuario_limpo('staff_mut', staff=True)
        self.autor = usuario_limpo('autor_mut')
        self.anim = criar_animacao('Mut Teste', self.autor)
        self.client.force_login(self.staff)

    def test_toggle_aprovacao_get_retorna_405(self):
        url = reverse('moderacao:toggle_aprovacao', args=[self.anim.pk])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 405)

    def test_toggle_aprovacao_post_altera(self):
        url = reverse('moderacao:toggle_aprovacao', args=[self.anim.pk])
        self.client.post(url)
        self.anim.refresh_from_db()
        self.assertFalse(self.anim.aprovada)
        self.client.post(url)
        self.anim.refresh_from_db()
        self.assertTrue(self.anim.aprovada)

    def test_apagar_animacao_get_retorna_405(self):
        resp = self.client.get(reverse('moderacao:apagar_animacao', args=[self.anim.pk]))
        self.assertEqual(resp.status_code, 405)
        self.assertTrue(Animacao.objects.filter(pk=self.anim.pk).exists())

    def test_apagar_animacao_post_remove(self):
        self.client.post(reverse('moderacao:apagar_animacao', args=[self.anim.pk]))
        self.assertFalse(Animacao.objects.filter(pk=self.anim.pk).exists())


class ProtecaoPerfilTests(TestCase):
    def setUp(self):
        self.staff = usuario_limpo('staff_prot', staff=True)
        self.super = usuario_limpo('super_prot', staff=True, superuser=True)
        self.comum = usuario_limpo('comum_prot')

    def test_staff_nao_apaga_superuser(self):
        self.client.force_login(self.staff)
        self.client.post(reverse('moderacao:apagar_perfil', args=['super_prot']))
        self.assertTrue(User.objects.filter(username='super_prot').exists())

    def test_staff_nao_apaga_propria_conta(self):
        self.client.force_login(self.staff)
        self.client.post(reverse('moderacao:apagar_perfil', args=['staff_prot']))
        self.assertTrue(User.objects.filter(username='staff_prot').exists())

    def test_superuser_apaga_staff(self):
        self.client.force_login(self.super)
        self.client.post(reverse('moderacao:apagar_perfil', args=['staff_prot']))
        self.assertFalse(User.objects.filter(username='staff_prot').exists())

    def test_staff_nao_bloqueia_superuser(self):
        self.client.force_login(self.staff)
        resp = self.client.post(
            reverse('moderacao:bloquear_perfil', args=['super_prot']),
            {'motivo': 'x'},
        )
        self.assertEqual(resp.status_code, 302)
        self.super.profile.refresh_from_db()
        self.assertFalse(self.super.profile.bloqueado)

    def test_apagar_perfil_get_retorna_405(self):
        self.client.force_login(self.staff)
        resp = self.client.get(
            reverse('moderacao:apagar_perfil', args=['comum_prot'])
        )
        self.assertEqual(resp.status_code, 405)


class DestaqueTests(TestCase):
    def setUp(self):
        self.staff = usuario_limpo('staff_dest', staff=True)
        self.autor = usuario_limpo('autor_dest')
        self.client.force_login(self.staff)

    def test_nao_destaca_bloqueada(self):
        anim = criar_animacao('Destaque Bloq', self.autor, bloqueada=True)
        resp = self.client.post(reverse('moderacao:criar_destaque', args=[anim.pk]))
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(Destaque.objects.filter(animacao=anim).exists())

    def test_destaca_aprovada(self):
        anim = criar_animacao('Destaque OK', self.autor)
        self.client.post(reverse('moderacao:criar_destaque', args=[anim.pk]))
        self.assertTrue(Destaque.objects.filter(animacao=anim, ativo=True).exists())

    def test_destaque_get_retorna_405(self):
        anim = criar_animacao('Destaque Get', self.autor)
        resp = self.client.get(reverse('moderacao:criar_destaque', args=[anim.pk]))
        self.assertEqual(resp.status_code, 405)

    def test_listar_animacoes_mostra_botao_remover_destaque(self):
        anim = criar_animacao('Destaque Removível', self.autor)
        destaque = Destaque.objects.create(animacao=anim)
        resp = self.client.get(reverse('moderacao:listar_animacoes'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Destaque Removível')
        self.assertContains(
            resp,
            reverse('moderacao:remover_destaque', args=[destaque.pk]),
        )

    def test_remover_destaque_redireciona_para_lista(self):
        anim = criar_animacao('Destaque Remoção', self.autor)
        destaque = Destaque.objects.create(animacao=anim)
        resp = self.client.post(
            reverse('moderacao:remover_destaque', args=[destaque.pk])
        )
        self.assertRedirects(resp, reverse('moderacao:listar_animacoes'))
        self.assertFalse(Destaque.objects.filter(pk=destaque.pk).exists())

    def test_listar_animacoes_pagina_com_mais_de_20(self):
        for i in range(25):
            criar_animacao(f'Anim Paginada {i}', self.autor)
        resp = self.client.get(
            reverse('moderacao:listar_animacoes') + '?page=2'
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, '25 animaçãos cadastradas')
        self.assertContains(resp, 'Página 2 de 2')
        # 20 por página: a página 2 traz os 5 restantes.
        self.assertContains(resp, 'Anim Paginada', count=5)


class MensagemTests(TestCase):
    def setUp(self):
        self.staff = usuario_limpo('staff_msg', staff=True)
        self.comum = usuario_limpo('comum_msg')
        self.client.force_login(self.staff)

    def test_envio_sem_destinatario_nao_causa_integrity_error(self):
        from django.contrib.messages.storage.fallback import FallbackStorage

        factory = RequestFactory()
        req = factory.post(
            '/moderacao/perfis/mensagem/',
            {'assunto': 'oi', 'conteudo': 'ola'},
        )
        req.user = self.staff
        req.session = {}
        setattr(req, '_messages', FallbackStorage(req))
        resp = views.enviar_mensagem(req)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(MensagemAdmin.objects.count(), 0)

    def test_envio_com_destinatario_funciona(self):
        resp = self.client.post(
            reverse('moderacao:enviar_mensagem', args=['comum_msg']),
            {'assunto': 'assunto', 'conteudo': 'conteudo'},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(MensagemAdmin.objects.count(), 1)
        msg = MensagemAdmin.objects.get()
        self.assertEqual(msg.destinatario, self.comum)
        self.assertEqual(msg.remetente, self.staff)

    def test_marcar_lida_get_retorna_405(self):
        msg = MensagemAdmin.objects.create(
            remetente=self.staff, destinatario=self.comum,
            assunto='a', conteudo='c',
        )
        self.client.force_login(self.comum)
        resp = self.client.get(reverse('moderacao:marcar_lida', args=[msg.pk]))
        self.assertEqual(resp.status_code, 405)
        msg.refresh_from_db()
        self.assertFalse(msg.lida)

    def test_marcar_lida_post_funciona(self):
        msg = MensagemAdmin.objects.create(
            remetente=self.staff, destinatario=self.comum,
            assunto='a', conteudo='c',
        )
        self.client.force_login(self.comum)
        self.client.post(reverse('moderacao:marcar_lida', args=[msg.pk]))
        msg.refresh_from_db()
        self.assertTrue(msg.lida)


class EnqueteTests(TestCase):
    def setUp(self):
        admin = usuario_limpo('criador_enquete', staff=True, superuser=True)
        self.enquete = Enquete.objects.create(
            titulo='Qual o melhor gênero?', criador=admin, apenas_logados=False,
        )
        self.op1 = OpcaoEnquete.objects.create(enquete=self.enquete, texto='Comédia')
        self.op2 = OpcaoEnquete.objects.create(enquete=self.enquete, texto='Drama')

    def test_voto_anonimo_quando_permitido(self):
        url = reverse('moderacao:votar', args=[self.enquete.pk])
        self.client.post(url, {'opcao': self.op1.pk})
        self.assertEqual(Voto.objects.count(), 1)
        voto = Voto.objects.get()
        self.assertIsNone(voto.usuario)
        # Segundo voto anônimo na mesma sessão é barrado.
        self.client.post(url, {'opcao': self.op2.pk})
        self.assertEqual(Voto.objects.count(), 1)

    def test_voto_anonimo_bloqueado_quando_apenas_logados(self):
        self.enquete.apenas_logados = True
        self.enquete.save()
        resp = self.client.post(
            reverse('moderacao:votar', args=[self.enquete.pk]),
            {'opcao': self.op1.pk},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Voto.objects.count(), 0)

    def test_voto_usuario_logado_uma_unica_vez(self):
        usuario = usuario_limpo('votante')
        self.client.force_login(usuario)
        url = reverse('moderacao:votar', args=[self.enquete.pk])
        self.client.post(url, {'opcao': self.op1.pk})
        self.client.post(url, {'opcao': self.op2.pk})
        self.assertEqual(Voto.objects.filter(usuario=usuario).count(), 1)

    def test_enquete_form_cria_opcoes(self):
        form_enquete = EnqueteForm({
            'titulo': 'Nova enquete', 'descricao': '', 'encerra_em': '',
            'status': 'aberta', 'apenas_logados': False,
        })
        self.assertTrue(form_enquete.is_valid())