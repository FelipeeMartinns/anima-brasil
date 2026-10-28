from django.contrib import admin

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'nome_estudio', 'bloqueado', 'visibilidade_favoritos',
        'visibilidade_curtidos', 'criado_em',
    ]
    list_filter = ['bloqueado', 'visibilidade_favoritos', 'visibilidade_curtidos']
    search_fields = ['user__username', 'nome_estudio', 'descricao']
    list_editable = ['bloqueado']