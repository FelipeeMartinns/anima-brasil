from django import forms

from .models import Enquete, MensagemAdmin, OpcaoEnquete


class EnqueteForm(forms.ModelForm):
    class Meta:
        model = Enquete
        fields = ['titulo', 'descricao', 'encerra_em', 'status', 'apenas_logados']
        widgets = {
            'encerra_em': forms.DateTimeInput(
                attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        encerra = self.initial.get('encerra_em')
        if encerra:
            self.initial['encerra_em'] = encerra.strftime('%Y-%m-%dT%H:%M')


class OpcoesEnqueteForm(forms.Form):
    opcao_1 = forms.CharField(label='Opção 1', max_length=200)
    opcao_2 = forms.CharField(label='Opção 2', max_length=200)
    opcao_3 = forms.CharField(label='Opção 3 (opcional)', max_length=200, required=False)
    opcao_4 = forms.CharField(label='Opção 4 (opcional)', max_length=200, required=False)


class MensagemAdminForm(forms.ModelForm):
    class Meta:
        model = MensagemAdmin
        fields = ['assunto', 'conteudo']
        widgets = {
            'conteudo': forms.Textarea(attrs={'rows': 4}),
        }


class BloqueioForm(forms.Form):
    motivo = forms.CharField(
        label='Motivo do bloqueio', max_length=300,
        widget=forms.Textarea(attrs={'rows': 2}),
    )