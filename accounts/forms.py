import urllib.parse

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import Profile


def _url_http_https(valor):
    if not valor:
        return valor
    try:
        partes = urllib.parse.urlparse(valor)
    except ValueError as exc:
        raise ValidationError('URL inválida.') from exc
    if partes.scheme not in ('http', 'https') or not partes.netloc:
        raise ValidationError('Informe uma URL completa começando com http:// ou https://.')
    return valor


class RegistroForm(UserCreationForm):
    email = forms.EmailField(required=True, label='E-mail')

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class LoginForm(forms.Form):
    username = forms.CharField(label='Usuário')
    password = forms.CharField(label='Senha', widget=forms.PasswordInput)


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            'nome_estudio', 'descricao', 'avatar',
            'instagram', 'youtube', 'site', 'outras_plataformas',
            'visibilidade_favoritos', 'visibilidade_curtidos',
        ]
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 4}),
            'outras_plataformas': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_outras_plataformas(self):
        """Aceita somente URLs http/https por linha (evita javascript: etc)."""
        linhas = self.cleaned_data.get('outras_plataformas', '').splitlines()
        validas = []
        for linha in linhas:
            url = linha.strip()
            if not url:
                continue
            if not (url.startswith('http://') or url.startswith('https://')):
                raise ValidationError(
                    f'"{url}" não é uma URL válida. Use apenas links http:// ou https://.'
                )
            validas.append(url)
        return '\n'.join(validas)

    def clean_instagram(self):
        return _url_http_https(self.cleaned_data.get('instagram'))

    def clean_youtube(self):
        return _url_http_https(self.cleaned_data.get('youtube'))

    def clean_site(self):
        return _url_http_https(self.cleaned_data.get('site'))