from django.shortcuts import render , redirect
from django.http import JsonResponse
import openai
import os
from openai import OpenAI
import requests
import markdown
from dotenv import load_dotenv
load_dotenv()


def index(request):
    contexto = {'mensaje': 'Hola desde Django!'}
    return render(request, 'temarioApp/base.html', contexto)

def crear_curso(request):
    if request.method == "POST":
        pass
    return render(request, 'temarioApp/crear_curso.html')

def mostrar_curso(request):
    clave_api =  os.getenv("GPT_API_KEY")

    if request.method == 'POST':
        # Obtener la mejora solicitada, si existe
        mejora = request.POST.get('mejora')

        if mejora:
            # Obtener el temario actual generado de la sesión
            temario_actual = request.session.get('temario')

            if not temario_actual:
                return render(request, 'temarioApp/mostrar_curso.html', {'error': 'No hay temario disponible. Genera un curso primero.'})

            # Crear un prompt combinando el temario actual con la mejora solicitada
            prompt = f"{temario_actual}\n\nRealiza la siguiente mejora o modificación: {mejora}"

            # Enviar el prompt a la API
            url = "https://api.openai.com/v1/chat/completions"
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {clave_api}",
            }
            data = {
                "model": "gpt-4",
                "messages": [
                    {"role": "system", "content": "Eres un asistente que ayuda a generar y modificar temarios de cursos."},
                    {"role": "user", "content": prompt}
                ],
            }
            response = requests.post(url, json=data, headers=headers)

            if response.status_code == 200:
                temario_generado = response.json()["choices"][0]["message"]["content"]

                # Actualizar el temario en la sesión
                request.session['temario'] = temario_generado
                temario_html = markdown.markdown(temario_generado)

                context = { 
                    'temario': temario_generado,
                    'temario_html': temario_html
                }
                return render(request, 'temarioApp/mostrar_curso.html', context)
            else:
                context = {'error': f"Error en la solicitud: {response.status_code} - {response.text}"}
                return render(request, 'temarioApp/mostrar_curso.html', context)

        else:
            # Capturar datos del formulario de generación de curso
            titulo = request.POST.get('titulo')
            dias = request.POST.get('dias')
            horario = request.POST.get('horario')
            participantes = request.POST.get('participantes')
            instructor = request.POST.get('instructor')
            objetivo = request.POST.get('objetivo')
            descripcion = request.POST.get('descripcion')
            nivel = request.POST.get('nivel')
            modalidad = request.POST.get('modalidad')
            materiales = request.POST.get('materiales')

            # Crear el primer mensaje y contexto para la API
            #parrafo = f"Genera un temario con temas, subtemas, y duración de cada uno, distribución de los temas por día, horario y actividades prácticas. Para un curso titulado '{titulo}', que se llevará a cabo durante {dias} días, en el horario {horario}, para {participantes} participantes. El objetivo es {objetivo}, el curso es de nivel {nivel} y modalidad {modalidad}. La descripción es {descripcion}. Los materiales necesarios son {materiales}."
            parrafo = f"Genera un temario con temas y subtemas del siguiente topico: {titulo} , con la siguiente descripcion: {descripcion} y el siguiente objetivo {objetivo} , agrega una pequeña definicion de cada tema y subtema"
            contexto = "Eres un asistente que ayuda a generar temario de cursos. Genera un markdown."

            # Inicializar el historial de conversación con el contexto y el primer mensaje del usuario
            request.session['historial_chat'] = [
                {"role": "system", "content": contexto},
                {"role": "user", "content": parrafo}
            ]

            # Enviar el historial a la API
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {clave_api}",
            }
            data = {
                "model": "gpt-4",
                "messages": request.session['historial_chat'],
            }
            response = requests.post(url, json=data, headers=headers)

            if response.status_code == 200:
                temario_generado = response.json()["choices"][0]["message"]["content"]

                # Almacenar el temario generado en la sesión
                request.session['temario'] = temario_generado
                temario_html = markdown.markdown(temario_generado)

                context = { 
                    'temario': temario_generado,
                    'temario_html': temario_html
                }
                return render(request, 'temarioApp/mostrar_curso.html', context)
            else:
                context = {'error': f"Error en la solicitud: {response.status_code} - {response.text}"}
                return render(request, 'temarioApp/mostrar_curso.html', context)

    # Si es GET, mostrar la página en blanco o con el temario actual (si existe)
    temario = request.session.get('temario', '')
    temario_html = request.session.get('temario_html', '')
    context = {
        'temario': temario,
        'temario_html': temario_html
    }
    return render(request, 'temarioApp/mostrar_curso.html', context)
