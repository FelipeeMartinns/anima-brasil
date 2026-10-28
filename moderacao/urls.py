from django.urls import path

from . import views

app_name = 'moderacao'

urlpatterns = [
    path('caixa-de-mensagens/', views.minhas_mensagens, name='minhas_mensagens'),
    path('mensagens/<int:pk>/lida/', views.marcar_lida, name='marcar_lida'),
    path('enquetes/', views.enquetes, name='enquetes'),
    path('enquetes/<int:pk>/votar/', views.votar, name='votar'),

    path('moderacao/painel/', views.painel, name='painel'),
    path('moderacao/animacoes/', views.listar_animacoes_admin, name='listar_animacoes'),
    path('moderacao/animacoes/<int:pk>/aprovar/', views.toggle_aprovacao, name='toggle_aprovacao'),
    path('moderacao/animacoes/<int:pk>/bloquear/', views.bloquear_animacao, name='bloquear_animacao'),
    path('moderacao/animacoes/<int:pk>/desbloquear/', views.desbloquear_animacao, name='desbloquear_animacao'),
    path('moderacao/animacoes/<int:pk>/apagar/', views.apagar_animacao, name='apagar_animacao'),
    path('moderacao/animacoes/<int:pk>/destaque/', views.criar_destaque, name='criar_destaque'),

    path('moderacao/perfis/', views.listar_perfis_admin, name='listar_perfis'),
    path('moderacao/perfis/<str:username>/bloquear/', views.bloquear_perfil, name='bloquear_perfil'),
    path('moderacao/perfis/<str:username>/desbloquear/', views.desbloquear_perfil, name='desbloquear_perfil'),
    path('moderacao/perfis/<str:username>/apagar/', views.apagar_perfil, name='apagar_perfil'),
    path('moderacao/perfis/<str:username>/mensagem/', views.enviar_mensagem, name='enviar_mensagem'),

    path('moderacao/enquetes/nova/', views.criar_enquete, name='criar_enquete'),
    path('moderacao/enquetes/<int:pk>/fechar/', views.fechar_enquete, name='fechar_enquete'),
    path('moderacao/destaques/<int:pk>/remover/', views.remover_destaque, name='remover_destaque'),
]