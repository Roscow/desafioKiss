from django.shortcuts import render

from django.http import HttpResponse


def index(request):
    contexto = {'mensaje': 'Hola desde Django!'}
    return render(request, 'temarioApp/base.html', contexto)


def crear_curso(request):
    if request.method == "POST":
        pass
    return render(request, 'temarioApp/crear_curso.html')