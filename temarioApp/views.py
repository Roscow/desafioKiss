from django.shortcuts import render , redirect
from django.http import JsonResponse
import openai
import os
from openai import OpenAI
import requests
import markdown
from dotenv import load_dotenv
load_dotenv()
import re
import json

def extraer_json(respuesta_api):
    """
    Esta función toma la respuesta de la API de ChatGPT, busca el primer objeto JSON en el texto, 
    y lo devuelve como un diccionario de Python.
    """
    # Usar una expresión regular para encontrar el primer objeto JSON en el texto
    match = re.search(r'\{.*\}', respuesta_api, re.DOTALL)
    
    if match:
        # Intentar convertir el JSON extraído en un diccionario de Python
        json_data = match.group(0)
        try:
            return json.loads(json_data)
        except json.JSONDecodeError:
            return None
    return None

def extraer_html(respuesta_api):
    """
    Esta función toma la respuesta de la API de ChatGPT y extrae solo el contenido HTML,
    eliminando cualquier texto adicional al inicio o al final.
    """
    # Usar una expresión regular para encontrar el bloque de código HTML válido
    match = re.search(r'<.*?>.*<\/.*?>', respuesta_api, re.DOTALL)
    
    if match:
        # Devuelve solo la parte del HTML
        return match.group(0)
    else:
        # Si no encuentra HTML, devuelve la respuesta completa o un mensaje de error
        return "No se encontró HTML válido en la respuesta."
    
def index(request):
    return render(request, 'temarioApp/base.html')

def crear_temario(request):
    if request.method == "POST":
        pass
    return render(request, 'temarioApp/crear_temario.html')

def mostrar_temario(request):
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
            prompt = f"Edita este temario ... {temario_actual} ... \n\n devuelvelo completo intenta mantener la base y solo realizar la siguiente mejora o modificación: {mejora}"

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
                return render(request, 'temarioApp/mostrar_temario.html', context)
            else:
                context = {'error': f"Error en la solicitud: {response.status_code} - {response.text}"}
                return render(request, 'temarioApp/mostrar_temario.html', context)

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
            parrafo = f"Genera un temario con temas y subtemas del siguiente topico: {titulo} , con la siguiente descripcion: {descripcion} y el siguiente objetivo {objetivo} , agrega una pequeña definicion de cada tema y subtema, no es necesario agregar actividades ni ejercicios ya que eso se realizara mas adelante"
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
                return render(request, 'temarioApp/mostrar_temario.html', context)
            else:
                context = {'error': f"Error en la solicitud: {response.status_code} - {response.text}"}
                return render(request, 'temarioApp/mostrar_temario.html', context)

    # Si es GET, mostrar la página en blanco o con el temario actual (si existe)
    temario = request.session.get('temario', '')
    temario_html = request.session.get('temario_html', '')
    context = {
        'temario': temario,
        'temario_html': temario_html
    }
    return render(request, 'temarioApp/mostrar_temario.html', context)

def generar_ejercicios(request):
    # Obtener el temario enviado desde el formulario
    temario_actual = request.POST.get('contenido_editado', '')

    if not temario_actual:
        return render(request, 'temarioApp/mostrar_temario.html', {'error': 'No hay temario disponible para generar ejercicios.'})

    clave_api = os.getenv("GPT_API_KEY")
    prompt = f"Edita este temario:\n{temario_actual}\n\nDevuélvelo completo, mantén la base y agrega ejercicios prácticos detallados para cada tema."

    # Enviar el prompt a la API
    url = "https://api.openai.com/v1/chat/completions"
            
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {clave_api}",
    }
    data = {
        "model": "gpt-4",
        "messages": [
            {"role": "system", "content": "Eres un asistente que ayuda a generar ejercicios prácticos para un curso."},
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
        return render(request, 'temarioApp/mostrar_ejercicios.html', context)
    else:
        context = {'error': f"Error en la solicitud: {response.status_code} - {response.text}"}
        return render(request, 'temarioApp/mostrar_temario.html', context)

def crear_cronograma(request):
    dias = request.POST.get('dias')
    horario = request.POST.get('horario')
    temario_actual = request.POST.get('contenido_editado', '')

    if not temario_actual or not dias or not horario:
        return render(request, 'temarioApp/mostrar_ejercicios.html', {'error': 'Faltan datos para generar el cronograma.'})

    clave_api = os.getenv("GPT_API_KEY")
    prompt = f"Con base en el siguiente temario:\n{temario_actual}\n\nGenera un cronograma detallado considerando los días de impartición: {dias} y el horario: {horario}. Distribuye los temas y los ejercicios prácticos de manera equilibrada, indica el tiempo de la revision del contenido del tema y del ejercicio practico, no me devuelvas fechas, no es necesario y la dame  el cronograma en formato HTML listo para ser insertado en una página web con estilos que me permitan ver la programacion para cada dia organizada ."

    # Enviar el prompt a la API
    url = "https://api.openai.com/v1/chat/completions"
            
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {clave_api}",
    }
    data = {
        "model": "gpt-4",
        "messages": [
            {"role": "system", "content": "Eres un asistente que ayuda a crear cronogramas para cursos."},
            {"role": "user", "content": prompt}
        ],
    }
    response = requests.post(url, json=data, headers=headers)
    
    if response.status_code == 200:
        cronograma_html = response.json()["choices"][0]["message"]["content"]
        print(f"Cronograma en HTML: {cronograma_html}")
        cronograma_html = extraer_html(cronograma_html)
        temario_html = markdown.markdown(temario_actual)

        context = {
            'cronograma_html': cronograma_html,
            'temario_html': temario_html  # Asegúrate de que esta variable contiene el HTML del temario

        }
        return render(request, 'temarioApp/mostrar_cronograma.html', context)
    else:
        context = {'error': f"Error en la solicitud: {response.status_code} - {response.text}"}
        return render(request, 'temarioApp/mostrar_cronograma.html', context)
