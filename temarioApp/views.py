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
from django.utils import timezone  # Para manejar la fecha de creación
from django.shortcuts import render, get_object_or_404
from .models import DatosBase, Temario, Cronograma
from weasyprint import HTML
import tempfile
from django.http import HttpResponse
from django.template.loader import render_to_string


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
    
def gpt_generacion_temario(titulo, descripcion, objetivo, nivel):
    clave_api =  os.getenv("GPT_API_KEY")
    parrafo = f"Genera un temario con temas y subtemas del siguiente topico: {titulo} , con la siguiente descripcion: {descripcion} y el siguiente objetivo {objetivo} , para un nivel {nivel}, agrega una pequeña definicion de cada tema y subtema, no es necesario agregar actividades ni ejercicios ya que eso se realizara mas adelante"
    contexto = "Eres un asistente que ayuda a generar temario de cursos. Genera un markdown."
    # Enviar el historial a la API
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {clave_api}",
    }
    data = {
        "model": "gpt-4",
        "messages": [{"role": "system", "content": contexto}, {"role": "user", "content": parrafo}],
    }
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        temario_generado = response.json()["choices"][0]["message"]["content"]
        return temario_generado
    else:
        return False

def gpt_generacion_ejercicios(temario_actual):
    print("creando ejercicios gpt" )
    clave_api = os.getenv("GPT_API_KEY")
    prompt = f"basado en  este temario:\n{temario_actual}\n\n, crea actividades y  ejercicios prácticos detallados para cada tema. que me ayuden a trabajar los temas a ver."
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
        temario_actividades = response.json()["choices"][0]["message"]["content"]
        return temario_actividades
    else:
        return False

def gpt_sugerencias_mejora():
    print("creando ejercicios gpt" )
    clave_api = os.getenv("GPT_API_KEY")
    prompt = f"dame 3 sugerencias para mejorar un posible temario ,que sea conciso, sin descripcion"
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {clave_api}",
    }
    data = {
        "model": "gpt-4",
        "messages": [
            {"role": "system", "content": "Eres un asistente que ayuda a mejorar un temario"},
            {"role": "user", "content": prompt}
        ],
    }
    response = requests.post(url, json=data, headers=headers)

    if response.status_code == 200:
        sugerencia = response.json()["choices"][0]["message"]["content"]
        return sugerencia
    else:
        return False

def index(request):
    return render(request, 'temarioApp/base.html')

def crear_temario(request):
    return render(request, 'temarioApp/crear_temario.html')

def mostrar_temario(request):
    clave_api =  os.getenv("GPT_API_KEY")
    sugerir_modificaciones =f"Sugerencias:  \n{gpt_sugerencias_mejora()}" 
    if request.method == 'POST':
        print("variables pasadas a temario")
        for key, value in request.session.items():
            print(f"{key}: {value}")
       
        #es modificacion 
        mejora = request.POST.get('mejora')
        if mejora:
            temario_actual = request.POST.get('contenido-editado')
            request.session['temario'] = temario_actual
            if not temario_actual:
                return render(request, 'temarioApp/mostrar_temario.html', {'error': 'No hay temario disponible. Genera un curso primero.'})
            prompt = f"Edita este temario ... {temario_actual} ... \n\n devuelvelo completo, intenta mantener la base y solo realizar la siguiente mejora o modificación: {mejora}"
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
                    'temario_html': temario_html,
                    'sugerir_modificaciones':sugerir_modificaciones
                }
                
                return render(request, 'temarioApp/mostrar_temario.html', context)
            else:
                context = {'error': f"Error en la solicitud: {response.status_code} - {response.text}"}
                return render(request, 'temarioApp/mostrar_temario.html', context)

        else:
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

            request.session['titulo'] = request.POST.get('titulo')
            request.session['dias'] = request.POST.get('dias')
            request.session['horario'] = request.POST.get('horario')
            request.session['participantes'] = request.POST.get('participantes')
            request.session['instructor'] = request.POST.get('instructor')
            request.session['objetivo'] = request.POST.get('objetivo')
            request.session['descripcion'] = request.POST.get('descripcion')
            request.session['nivel'] = request.POST.get('nivel')
            request.session['modalidad'] = request.POST.get('modalidad')
            request.session['materiales'] = request.POST.get('materiales')
    
            #generar temario 
            respuesta = gpt_generacion_temario(titulo, descripcion, objetivo, nivel )
           
            if (respuesta is not False):
                temario_html = markdown.markdown(respuesta)
                request.session['temario'] = respuesta
                request.session['temario_html'] = markdown.markdown(temario_html)
                context = { 
                    'temario': respuesta,
                    'temario_html': temario_html,
                    'sugerir_modificaciones':sugerir_modificaciones
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

def mostrar_actividades(request):
    if request.method == 'POST':
        print("variables pasadas a actividades")
        for key, value in request.session.items():
            print(f"{key}: {value}")
        contenido_editado = request.POST.get('contenido-editado')
        clave_api =  os.getenv("GPT_API_KEY")

        mejora = request.POST.get('mejora')
        if mejora:
            temario_actual = request.POST.get('contenido-editado')
            print(temario_actual)
            if not temario_actual:
                return render(request, 'temarioApp/mostrar_actividades.html', {'error': 'No hay temario disponible. Genera un curso primero.'})
            prompt = f"realiza las siguientes mejoras para estas actividades practicas ... {temario_actual} ... \n\n devuelvelo completo, intenta mantener la base y solo realizar la siguiente mejora o modificación: {mejora}"
            url = "https://api.openai.com/v1/chat/completions"
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {clave_api}",
            }
            data = {
                "model": "gpt-4",
                "messages": [
                    {"role": "system", "content": "Eres un asistente que ayuda a generar y modificar actividade practicas de cursos."},
                    {"role": "user", "content": prompt}
                ],
            }
            response = requests.post(url, json=data, headers=headers)
            if response.status_code == 200:
                temario_generado = response.json()["choices"][0]["message"]["content"]
                request.session['actividades '] = temario_generado
                temario_html = markdown.markdown(temario_generado)
                context = { 
                    'temario': temario_generado,
                    'temario_html': temario_html
                }
                return render(request, 'temarioApp/mostrar_actividades.html', context)
            else:
                context = {'error': f"Error en la solicitud: {response.status_code} - {response.text}"}
                return render(request, 'temarioApp/mostrar_actividades.html', context)

        else:
            actividades = gpt_generacion_ejercicios(contenido_editado)
            request.session['actividades'] = actividades
            ejercicios_html = markdown.markdown(actividades)
            context = { 
                'temario': actividades,
                'temario_html': ejercicios_html,
            }
            return render(request, 'temarioApp/mostrar_actividades.html', context)
    return render(request, 'temarioApp/mostrar_actividades.html')

def crear_cronograma(request):
    print("variables pasadas a actividades")
    for key, value in request.session.items():
        print(f"{key}: {value}")
    clave_api = os.getenv("GPT_API_KEY")
    temario_actual = request.session.get('temario')
    actividades = request.session.get('actividades')
    dias = request.session.get('dias')
    horario = request.session.get('horario')

    prompt = f"Con base en el siguiente temario:\n{temario_actual}\n\n y la siguiente pauta de actividades {actividades} Genera un cronograma detallado considerando los días de impartición: {dias} y el horario: {horario}. Distribuye los temas y los ejercicios prácticos de manera equilibrada, indica el tiempo de la revision del contenido del tema y del ejercicio practico, no me devuelvas fechas, no es necesario y la dame  el cronograma en formato HTML listo para ser insertado en una página web con estilos que me permitan ver la programacion para cada dia organizada ."

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
        request.session['cronograma_html'] = cronograma_html

        temario_html = markdown.markdown(temario_actual)
        request.session['temario_html'] = temario_html

        actividades_html = markdown.markdown(actividades)
        request.session['actividades_html'] = actividades_html

        context = {
            'cronograma_html': cronograma_html,
            'temario_html': temario_html,  # Asegúrate de que esta variable contiene el HTML del temario
            'actividades_html':actividades_html
        }
        return render(request, 'temarioApp/mostrar_cronograma.html', context)
    else:
        context = {'error': f"Error en la solicitud: {response.status_code} - {response.text}"}
        return render(request, 'temarioApp/mostrar_cronograma.html', context)

def confirmar_cronograma(request):
    print("variables pasadas a pdf")
    for key, value in request.session.items():
        print(f"{key}: {value}")
    if request.method == 'POST':
        # Obtener los datos de la sesión
        cronograma_html = request.session.get('cronograma_html')
        temario_html = request.session.get('temario_html')
        actividades_html = request.session.get('actividades_html')
        
        dias = request.session.get('dias')
        horario = request.session.get('horario')
        titulo = request.session.get('titulo')
        cantidad_participantes = request.session.get('participantes')
        instructor = request.session.get('instructor')
        objetivo = request.session.get('objetivo')
        descripcion = request.session.get('descripcion')
        nivel_del_curso = request.session.get('nivel')
        modalidad = request.session.get('modalidad')
        materiales_necesarios = request.session.get('materiales')
        fecha_creacion = None  # Fecha de creación no disponible en la sesión

        # Generar PDF del cronograma
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="cronograma_{titulo}.pdf"'

        context = {
            'cronograma': cronograma_html,
            'temario': temario_html,
            'actividades': actividades_html,
            'dias': dias,
            'horario': horario,
            'titulo': titulo,
            'cantidad_participantes': cantidad_participantes,
            'instructor': instructor,
            'objetivo': objetivo,
            'descripcion': descripcion,
            'nivel_del_curso': nivel_del_curso,
            'modalidad': modalidad,
            'materiales_necesarios': materiales_necesarios,
            'fecha_creacion': fecha_creacion
        }

        # Renderizar el HTML del cronograma
        html_string = render_to_string('temarioApp/cronograma_pdf_template.html', context)

        # Convertir HTML a PDF
        html = HTML(string=html_string)
        result = html.write_pdf()

        # Escribir el PDF en la respuesta
        response.write(result)
        return response

    return render(request, 'temarioApp/mostrar_cronograma.html')
