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
    prompt = f"Edita este temario:\n{temario_actual}\n\nDevuélvelo completo, mantén la base y agrega ejercicios prácticos detallados para cada tema."
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

def index(request):
    return render(request, 'temarioApp/base.html')

def crear_temario(request):
    return render(request, 'temarioApp/crear_temario.html')

def mostrar_temario(request):
    clave_api =  os.getenv("GPT_API_KEY")
    if request.method == 'POST':
        #es regeneracion 
        if request.POST.get('id_datos_base'):
            id_datos =request.POST.get('id_datos_base')
            print(f"el valor enviado desde formulario es: {id_datos}")
            datos = DatosBase.objects.get(id=id_datos)
            titulo = datos.titulo
            descripcion = datos.descripcion
            objetivo = datos.objetivo
            nivel = datos.nivel_del_curso
            respuesta = gpt_generacion_temario(titulo, descripcion, objetivo, nivel)
            if (respuesta is not False):
                temario_html = markdown.markdown(respuesta)
                context = { 
                    'id_datos_base': id_datos,
                    'temario': respuesta,
                    'temario_html': temario_html
                }
                return render(request, 'temarioApp/mostrar_temario.html', context)
            else:
                context = {'error': f"Error en la solicitud: {response.status_code} - {response.text}"}
                return render(request, 'temarioApp/mostrar_temario.html', context)

        #es modificacion 
        mejora = request.POST.get('mejora')
        if mejora:
            temario_actual = request.POST.get('contenido-editado')
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
                id_datos_base2 = request.POST.get('id_datos_base')
                context = { 
                    'id_datos_base': id_datos,
                    'temario': temario_generado,
                    'temario_html': temario_html
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

            #guardar los datos en la bd ...
            nuevo_curso = DatosBase(
                titulo=titulo,
                horario=horario,
                cantidad_participantes=participantes,
                instructor=instructor,
                objetivo=objetivo,
                descripcion=descripcion,
                nivel_del_curso=nivel,
                modalidad=modalidad,
                materiales_necesarios=materiales,
                fecha_creacion=timezone.now(),
                dias = dias
            )
            nuevo_curso.save()
            print(nuevo_curso.id)
            id_datos_base = nuevo_curso.id
            #generar temario 
            respuesta = gpt_generacion_temario(titulo, descripcion, objetivo, nivel )
           
            if (respuesta is not False):
                temario_html = markdown.markdown(respuesta)
                request.session['temario'] = respuesta
                request.session['temario_html'] = markdown.markdown(temario_html)
                context = { 
                    'id_datos_base': id_datos_base,
                    'temario': respuesta,
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

def mostrar_actividades(request):
    if request.method == 'POST':
        id_datos_base = request.POST.get('id_datos_base')
        contenido_editado = request.POST.get('contenido-editado')
        clave_api =  os.getenv("GPT_API_KEY")
        mejora = request.POST.get('mejora')
        if mejora:
            temario_actual = request.POST.get('contenido-editado')
            print(temario_actual)
            if not temario_actual:
                return render(request, 'temarioApp/mostrar_actividades.html', {'error': 'No hay temario disponible. Genera un curso primero.'})
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
                request.session['temario'] = temario_generado
                temario_html = markdown.markdown(temario_generado)
                context = { 
                    'id_datos_base': id_datos_base,
                    'temario': temario_generado,
                    'temario_html': temario_html
                }
                return render(request, 'temarioApp/mostrar_actividades.html', context)
            else:
                context = {'error': f"Error en la solicitud: {response.status_code} - {response.text}"}
                return render(request, 'temarioApp/mostrar_actividades.html', context)

        else:
            # Obtén la instancia de DatosBase usando id_datos_base
            datos_base = get_object_or_404(DatosBase, id=id_datos_base)
            print(datos_base)
            nuevo_temario = Temario.objects.create(
                contenido=contenido_editado,
                datos_base=datos_base
            )
            print("si se crea el objeto....")
            print(f"antes del save:{nuevo_temario}" )
            nuevo_temario.save()
            print(f"despues del save {nuevo_temario}")
            temario_ejercicios = gpt_generacion_ejercicios(contenido_editado)
            request.session['temario'] = temario_ejercicios
            temario_html = markdown.markdown(temario_ejercicios)
            context = { 
                'id_datos_base': id_datos_base,
                'temario': temario_ejercicios,
                'temario_html': temario_html
            }
            return render(request, 'temarioApp/mostrar_actividades.html', context)
    return render(request, 'temarioApp/mostrar_actividades.html')

def crear_cronograma(request):
    dias = request.POST.get('dias')
    horario = request.POST.get('horario')
    temario_actual = request.POST.get('contenido-editado', '')
    id_datos = request.POST.get('id_datos_base')
    #obtener temario
    temario_obj = Temario.objects.get(datos_base_id=id_datos)
    temario_base = temario_obj.contenido
    if not temario_actual or not dias or not horario:
        return render(request, 'temarioApp/mostrar_actividades.html', {'error': 'Faltan datos para generar el cronograma.'})

    clave_api = os.getenv("GPT_API_KEY")
    prompt = f"Con base en el siguiente temario:\n{temario_actual}\n\nGenera un cronograma detallado considerando los días de impartición: {dias} y el horario: {horario}. Distribuye los temas y los ejercicios prácticos de manera equilibrada, indica el tiempo de la revision del contenido del tema y del ejercicio practico, no me devuelvas fechas, no es necesario y la dame  el cronograma en formato HTML listo para ser insertado en una página web con estilos que me permitan ver la programacion para cada dia organizada ."

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
            'temario_base': temario_base,
            'id_datos_base': id_datos,
            'cronograma_html': cronograma_html,
            'temario_html': temario_html  # Asegúrate de que esta variable contiene el HTML del temario

        }
        return render(request, 'temarioApp/mostrar_cronograma.html', context)
    else:
        context = {'error': f"Error en la solicitud: {response.status_code} - {response.text}"}
        return render(request, 'temarioApp/mostrar_cronograma.html', context)

def confirmar_cronograma(request):
    if request.method == 'POST':
        cronograma_final = request.POST.get('cronograma_final')
        id_datos_base = request.POST.get('id_datos_base')

        # Obtén la instancia de DatosBase usando id_datos_base
        datos_base = get_object_or_404(DatosBase, id=id_datos_base)

        # Guarda el cronograma en la base de datos
        nuevo_cronograma = Cronograma.objects.create(
            cronograma=cronograma_final,
            datos_base=datos_base
        )
        nuevo_cronograma.save()

        # Generar PDF del cronograma
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="cronograma_{datos_base.titulo}.pdf"'

        # Renderizar el HTML del cronograma
        html_string = render_to_string('temarioApp/cronograma_pdf_template.html', {'cronograma': cronograma_final})

        # Convertir HTML a PDF
        html = HTML(string=html_string)
        result = html.write_pdf()

        # Escribir el PDF en la respuesta
        response.write(result)
        return response

    return render(request, 'temarioApp/mostrar_cronograma.html')