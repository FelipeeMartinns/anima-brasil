from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from catalogo.models import Animacao, Destaque, Tag
from moderacao.models import Enquete, OpcaoEnquete, Voto


def usuario_limpo(username):
    return User.objects.get_or_create(username=username)[0]


class IndexTests(TestCase):
    def setUp(self):
        self.autor = usuario_limpo('autor_core')
        self.ok = Animacao.objects.create(
            titulo='Home Aprovada', sinopse='s', ano_lancamento=2022,
            diretor='d', estudio='e', classificacao='L', duracao=5,
            criador=self.autor, aprovada=True, bloqueada=False,
        )
        self.bloqueada = Animacao.objects.create(
            titulo='Home Bloqueada', sinopse='s', ano_lancamento=2022,
            diretor='d', estudio='e', classificacao='L', duracao=5,
            criador=self.autor, aprovada=True, bloqueada=True,
        )
        self.nao_aprovada = Animacao.objects.create(
            titulo='Home Analise', sinopse='s', ano_lancamento=2022,
            diretor='d', estudio='e', classificacao='L', duracao=5,
            criador=self.autor, aprovada=False, bloqueada=False,
        )

    def test_index_200(self):
        resp = self.client.get(reverse('core:index'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Home Aprovada')
        self.assertNotContains(resp, 'Home Bloqueada')
        self.assertNotContains(resp, 'Home Analise')

    def test_destaque_omitido_se_bloqueada(self):
        Destaque.objects.create(animacao=self.bloqueada)
        resp = self.client.get(reverse('core:index'))
        self.assertNotContains(resp, 'Home Bloqueada')

    def test_destaque_omitido_se_nao_aprovada(self):
        Destaque.objects.create(animacao=self.nao_aprovada)
        resp = self.client.get(reverse('core:index'))
        self.assertNotContains(resp, 'Home Analise')

    def test_destaque_exibido_quando_permitido(self):
        Destaque.objects.create(animacao=self.ok)
        resp = self.client.get(reverse('core:index'))
        self.assertContains(resp, 'Home Aprovada')

    def test_tags_renderizadas_na_home(self):
        tag = Tag.objects.create(nome='Fantasia')
        self.ok.tags.add(tag)
        resp = self.client.get(reverse('core:index'))
        self.assertContains(resp, 'Fantasia')


class EnqueteIndexTests(TestCase):
    def setUp(self):
        admin = usuario_limpo('admin_core')
        self.enquete = Enquete.objects.create(
            titulo='Enquete da home', criador=admin, apenas_logados=False,
        )
        self.op1 = OpcaoEnquete.objects.create(enquete=self.enquete, texto='Opção A')

    def test_enquete_aberta_aparece_com_votos(self):
        Voto.objects.create(opcao=self.op1, usuario=None)
        resp = self.client.get(reverse('core:index'))
        self.assertContains(resp, 'Enquete da home')

    def test_enquete_fechada_nao_aparece(self):
        self.enquete.status = 'fechada'
        self.enquete.save()
        resp = self.client.get(reverse('core:index'))
        self.assertNotContains(resp, 'Enquete da home')