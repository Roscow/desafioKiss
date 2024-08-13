from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('crear_temario', views.crear_temario, name='crear_temario'),
    path('mostrar_temario', views.mostrar_temario, name='mostrar_temario'),
    path('mostrar_actividades', views.mostrar_actividades, name='mostrar_actividades'),
    path('crear_cronograma', views.crear_cronograma, name='crear_cronograma'),
    path('confirmar_cronograma/', views.confirmar_cronograma, name='confirmar_cronograma'),

]
