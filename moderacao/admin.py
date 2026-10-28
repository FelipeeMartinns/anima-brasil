from django.contrib import admin

from .models import Enquete, MensagemAdmin, OpcaoEnquete, Voto


class OpcaoEnqueteInline(admin.TabularInline):
    model = OpcaoEnquete
    extra = 1


@admin.register(Enquete)
class EnqueteAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'criador', 'status', 'aberta_em', 'encerra_em', 'total_votos']
    list_filter = ['status', 'apenas_logados']
    search_fields = ['titulo', 'descricao']
    inlines = [OpcaoEnqueteInline]
    readonly_fields = ['aberta_em']

    def total_votos(self, obj):
        return sum(opcao.total_votos for opcao in obj.opcoes.all())

    total_votos.short_description = 'Total de votos'


@admin.register(OpcaoEnquete)
class OpcaoEnqueteAdmin(admin.ModelAdmin):
    list_display = ['enquete', 'texto', 'total_votos']
    search_fields = ['texto']


@admin.register(Voto)
class VotoAdmin(admin.ModelAdmin):
    list_display = ['opcao', 'usuario', 'criado_em']
    search_fields = ['usuario__username', 'opcao__texto']


@admin.register(MensagemAdmin)
class MensagemAdminAdmin(admin.ModelAdmin):
    list_display = ['assunto', 'remetente', 'destinatario', 'lida', 'criado_em']
    list_filter = ['lida', 'criado_em']
    search_fields = ['assunto', 'conteudo', 'destinatario__username']