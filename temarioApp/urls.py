from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('crear_temario', views.crear_temario, name='crear_temario'),
    path('mostrar_temario', views.mostrar_temario, name='mostrar_temario'),
    path('generar_ejercicios', views.generar_ejercicios, name='generar_ejercicios'),
    path('crear_cronograma', views.crear_cronograma, name='crear_cronograma'),

]
