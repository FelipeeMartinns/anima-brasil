from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('cadastro/', views.registrar, name='registro'),
    path('login/', views.entrar, name='login'),
    path('logout/', views.sair, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('perfil/editar/', views.editar_perfil, name='editar_perfil'),
    path('perfil/<str:username>/', views.perfil_publico, name='perfil'),
]