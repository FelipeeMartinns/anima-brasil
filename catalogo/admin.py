from django.contrib import admin
from django.utils.html import format_html

from .models import Animacao, Comentario, Curtida, Destaque, Favorito, Tag


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['nome', 'sistema', 'criador']
    list_filter = ['sistema']
    search_fields = ['nome']


@admin.register(Animacao)
class AnimacaoAdmin(admin.ModelAdmin):
    list_display = [
        'titulo', 'ano_lancamento', 'diretor', 'estudio',
        'classificacao', 'duracao', 'aprovada', 'bloqueada', 'total_curtidas',
    ]
    list_filter = ['classificacao', 'aprovada', 'bloqueada', 'tags', 'ano_lancamento']
    search_fields = ['titulo', 'diretor', 'estudio', 'sinopse']
    filter_horizontal = ['tags']
    list_editable = ['aprovada', 'bloqueada']
    readonly_fields = ['criado_em', 'atualizado_em', 'total_curtidas', 'total_favoritos', 'total_comentarios']

    def total_curtidas(self, obj):
        return obj.curtidas.count()

    total_curtidas.short_description = 'Curtidas'

    def total_favoritos(self, obj):
        return obj.favoritos.count()

    total_favoritos.short_description = 'Favoritos'

    def total_comentarios(self, obj):
        return obj.comentarios.count()

    total_comentarios.short_description = 'Comentários'


@admin.register(Comentario)
class ComentarioAdmin(admin.ModelAdmin):
    list_display = ['animacao', 'usuario', 'criado_em']
    list_filter = ['criado_em']
    search_fields = ['conteudo', 'usuario__username', 'animacao__titulo']


@admin.register(Curtida)
class CurtidaAdmin(admin.ModelAdmin):
    list_display = ['animacao', 'usuario', 'criado_em']
    search_fields = ['animacao__titulo', 'usuario__username']


@admin.register(Favorito)
class FavoritoAdmin(admin.ModelAdmin):
    list_display = ['animacao', 'usuario', 'criado_em']
    search_fields = ['animacao__titulo', 'usuario__username']


@admin.register(Destaque)
class DestaqueAdmin(admin.ModelAdmin):
    list_display = ['animacao', 'titulo_destaque', 'ativo', 'criado_em']
    list_filter = ['ativo']
    search_fields = ['animacao__titulo', 'titulo_destaque']