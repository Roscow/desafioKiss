from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('crear_curso', views.crear_curso, name='crear_curso'),
    path('mostrar_curso/', views.mostrar_curso, name='mostrar_curso'),
]
