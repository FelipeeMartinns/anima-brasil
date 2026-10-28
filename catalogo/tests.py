from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .forms import AnimacaoForm
from .models import Animacao, Comentario, Tag


def criar_animacao(
    titulo='Animação Teste', aprovada=True, bloqueada=False, criador=None, **extra
):
    autor = criador or User.objects.get_or_create(username='autor_teste')[0]
    anim = Animacao.objects.create(
        titulo=titulo,
        sinopse=extra.get('sinopse', 'sinopse'),
        ano_lancamento=extra.get('ano_lancamento', 2022),
        diretor=extra.get('diretor', 'Diretor'),
        estudio=extra.get('estudio', 'Estúdio'),
        classificacao=extra.get('classificacao', 'L'),
        duracao=extra.get('duracao', 5),
        criador=autor,
        aprovada=aprovada,
        bloqueada=bloqueada,
    )
    return anim


def dados_form_animacao(**extra):
    base = {
        'titulo': 'Animação Form Teste',
        'sinopse': 'sinopse',
        'ano_lancamento': 2023,
        'diretor': 'Diretor',
        'estudio': 'Estúdio',
        'classificacao': 'L',
        'duracao': 8,
        'imagem_url': '',
        'link': '',
        'tags': [],
        'novas_tags': '',
    }
    base.update(extra)
    return base


class CatalogoTests(TestCase):
    def setUp(self):
        self.autor = User.objects.get_or_create(username='autor')[0]
        self.ok = criar_animacao('Aprovada Visible', criador=self.autor)
        self.bloqueada = criar_animacao(
            'Bloqueada Vista', criador=self.autor, aprovada=True, bloqueada=True
        )
        self.nao_aprovada = criar_animacao(
            'Em Analise Vista', criador=self.autor, aprovada=False
        )

    def test_catalogo_lista_apenas_aprovadas(self):
        resp = self.client.get(reverse('catalogo:catalogo'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Aprovada Visible')
        self.assertNotContains(resp, 'Bloqueada Vista')
        self.assertNotContains(resp, 'Em Analise Vista')

    def test_detalhe_bloqueada_mostra_tela_bloqueada(self):
        resp = self.client.get(reverse('catalogo:detalhe', args=[self.bloqueada.pk]))
        self.assertContains(resp, 'foi bloqueada pela moderação')

    def test_detalhe_nao_aprovada_mostra_tela_analise(self):
        resp = self.client.get(reverse('catalogo:detalhe', args=[self.nao_aprovada.pk]))
        self.assertNotContains(resp, self.ok.titulo)
        self.assertEqual(resp.status_code, 200)

    def test_staff_ve_detalhe_de_bloqueada(self):
        staff = User.objects.get_or_create(username='staff')[0]
        staff.is_staff = True
        staff.save()
        self.client.force_login(staff)
        resp = self.client.get(reverse('catalogo:detalhe', args=[self.bloqueada.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, 'foi bloqueada pela moderação')


class CriarEditarTests(TestCase):
    def setUp(self):
        self.autor = User.objects.get_or_create(username='autor')[0]
        self.admin = User.objects.get_or_create(username='admin_tests')[0]
        self.admin.is_superuser = True
        self.admin.is_staff = True
        self.admin.save()
        self.client.force_login(self.autor)

    def test_criar_animacao_definie_criador(self):
        resp = self.client.post(
            reverse('catalogo:criar'),
            dados_form_animacao(novas_tags='fantasia, 2D'),
        )
        self.assertRedirects(resp, reverse('accounts:dashboard'))
        anim = Animacao.objects.get(titulo='Animação Form Teste')
        self.assertEqual(anim.criador, self.autor)
        self.assertTrue(anim.tags.filter(nome='2D').exists())

    def test_tag_muito_longa_nao_gera_erro_500(self):
        resp = self.client.post(
            reverse('catalogo:criar'),
            dados_form_animacao(novas_tags='x' * 61),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'excede o limite')
        self.assertFalse(Animacao.objects.filter(titulo='Animação Form Teste').exists())

    def test_tag_com_60_caracteres_aceita(self):
        resp = self.client.post(
            reverse('catalogo:criar'),
            dados_form_animacao(novas_tags='y' * 60),
        )
        self.assertRedirects(resp, reverse('accounts:dashboard'))

    def test_rejeita_imagem_url_ftp(self):
        resp = self.client.post(
            reverse('catalogo:criar'),
            dados_form_animacao(imagem_url='ftp://cdn.example.com/a.png'),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'http:// ou https://')
        self.assertFalse(
            Animacao.objects.filter(titulo='Animação Form Teste').exists()
        )

    def test_aceita_imagem_url_https(self):
        resp = self.client.post(
            reverse('catalogo:criar'),
            dados_form_animacao(imagem_url='https://cdn.example.com/a.png'),
        )
        self.assertRedirects(resp, reverse('accounts:dashboard'))

    def test_rejeita_link_ftp(self):
        resp = self.client.post(
            reverse('catalogo:criar'),
            dados_form_animacao(link='ftp://arquivo.example.com/clip.mov'),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'http:// ou https://')
        self.assertFalse(
            Animacao.objects.filter(titulo='Animação Form Teste').exists()
        )

    def test_edicao_por_admin_preserva_criador(self):
        anim = criar_animacao(
            'Original', criador=self.autor
        )
        self.client.force_login(self.admin)
        dados = dados_form_animacao(titulo='Original Editado')
        resp = self.client.post(
            reverse('catalogo:editar', args=[anim.pk]), dados
        )
        self.assertRedirects(resp, reverse('catalogo:detalhe', args=[anim.pk]))
        anim.refresh_from_db()
        self.assertEqual(anim.criador, self.autor)
        self.assertEqual(anim.titulo, 'Original Editado')


class InteracoesTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.get_or_create(username='interator')[0]
        self.autor = User.objects.get_or_create(username='autor2')[0]
        self.ok = criar_animacao('Interagir OK', criador=self.autor)
        self.bloqueada = criar_animacao(
            'Interagir Bloq', criador=self.autor, bloqueada=True
        )
        self.client.force_login(self.usuario)

    def test_curtir_alterna(self):
        url = reverse('catalogo:curtir', args=[self.ok.pk])
        r1 = self.client.post(url)
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r1.json()['curtiu'], True)
        r2 = self.client.post(url)
        self.assertEqual(r2.json()['curtiu'], False)

    def test_curtir_requer_login(self):
        self.client.logout()
        resp = self.client.post(reverse('catalogo:curtir', args=[self.ok.pk]))
        self.assertEqual(resp.status_code, 302)

    def test_curtir_bloqueada_retorna_403(self):
        resp = self.client.post(reverse('catalogo:curtir', args=[self.bloqueada.pk]))
        self.assertEqual(resp.status_code, 403)
        self.assertIn('erro', resp.json())

    def test_favoritar_bloqueada_retorna_403(self):
        resp = self.client.post(reverse('catalogo:favoritar', args=[self.bloqueada.pk]))
        self.assertEqual(resp.status_code, 403)
        self.assertIn('erro', resp.json())

    def test_comentar_bloqueada_nao_cria_comentario(self):
        url = reverse('catalogo:comentar', args=[self.bloqueada.pk])
        resp = self.client.post(url, {'conteudo': 'spam'})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            Comentario.objects.filter(animacao=self.bloqueada).count(), 0
        )

    def test_comentar_aprovada_publica(self):
        url = reverse('catalogo:comentar', args=[self.ok.pk])
        resp = self.client.post(url, {'conteudo': 'ótima!'})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            Comentario.objects.filter(animacao=self.ok).count(), 1
        )