from django.urls import path

from . import views

app_name = 'catalogo'

urlpatterns = [
    path('catalogo/', views.catalogo, name='catalogo'),
    path('animacao/<int:pk>/', views.detalhe, name='detalhe'),
    path('animacao/nova/', views.criar_animacao, name='criar'),
    path('animacao/<int:pk>/editar/', views.editar_animacao, name='editar'),
    path('animacao/<int:pk>/curtir/', views.curtir, name='curtir'),
    path('animacao/<int:pk>/favoritar/', views.favoritar, name='favoritar'),
    path('animacao/<int:pk>/comentar/', views.comentar, name='comentar'),
]