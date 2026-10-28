import urllib.parse

from django import forms
from django.core.exceptions import ValidationError

from .models import Animacao, Comentario, Tag


def _validar_url_http_https(valor):
    if not valor:
        return valor
    try:
        partes = urllib.parse.urlparse(valor)
    except ValueError as exc:
        raise ValidationError('URL inválida.') from exc
    if partes.scheme not in ('http', 'https') or not partes.netloc:
        raise ValidationError('Informe uma URL completa começando com http:// ou https://.')
    return valor


class AnimacaoForm(forms.ModelForm):
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Tags / Gêneros',
        help_text=(
            'Selecione tags existentes ou digite novas separadas por vírgula '
            'no campo abaixo.'
        ),
    )
    novas_tags = forms.CharField(
        required=False,
        label='Nova(s) tag(s)',
        help_text='Separe por vírgula. Ex: fantasia, terror, 2D',
    )

    class Meta:
        model = Animacao
        fields = [
            'titulo', 'sinopse', 'ano_lancamento', 'diretor', 'estudio',
            'classificacao', 'duracao', 'imagem', 'imagem_url', 'link', 'tags',
        ]
        widgets = {
            'sinopse': forms.Textarea(attrs={'rows': 4}),
        }

    def clean_novas_tags(self):
        raw = [t.strip() for t in self.cleaned_data['novas_tags'].split(',') if t.strip()]
        for nome in raw:
            if len(nome) > Tag._meta.get_field('nome').max_length:
                raise ValidationError(
                    f'A tag "{nome}" excede o limite de '
                    f'{Tag._meta.get_field("nome").max_length} caracteres.'
                )
        return raw

    def clean_imagem_url(self):
        return _validar_url_http_https(self.cleaned_data['imagem_url'])

    def clean_link(self):
        return _validar_url_http_https(self.cleaned_data['link'])

    def salvar_com_tags(self, usuario):
        animacao = self.save(commit=False)
        # O criador é definido somente na criação; na edição ele é preservado.
        if not animacao.pk:
            animacao.criador = usuario
        animacao.save()
        tags = list(self.cleaned_data['tags'])
        for nome in self.cleaned_data['novas_tags']:
            tag, created = Tag.objects.get_or_create(nome=nome, defaults={'criador': usuario})
            tags.append(tag)
        animacao.tags.set(tags)
        return animacao


class ComentarioForm(forms.ModelForm):
    class Meta:
        model = Comentario
        fields = ['conteudo']
        widgets = {
            'conteudo': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Escreva um comentário...'}),
        }