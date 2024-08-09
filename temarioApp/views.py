from django.shortcuts import render

from django.http import HttpResponse

def index(request):
    return HttpResponse("Bienvenido a la página principal de la app desafio Kiss.")

