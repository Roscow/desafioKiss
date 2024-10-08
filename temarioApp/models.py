from django.db import models

# Create your models here.
class DatosBase(models.Model):
    titulo = models.CharField(max_length=255)
    horario = models.TextField()
    cantidad_participantes = models.IntegerField()
    instructor = models.TextField()
    objetivo = models.TextField(blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    nivel_del_curso = models.CharField(max_length=20, blank=True, null=True)
    modalidad = models.CharField(max_length=20, blank=True, null=True)
    materiales_necesarios = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(blank=True, null=True)
    dias = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'datos_base'

class Actividades(models.Model):
    temario = models.ForeignKey('Temario', models.DO_NOTHING)
    ejercicios = models.TextField()
    fecha_creacion = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'actividades'

class Temario(models.Model):
    datos_base = models.ForeignKey(DatosBase, models.DO_NOTHING)
    contenido = models.TextField()
    fecha_creacion = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'temario'


class Cronograma(models.Model):
    datos_base = models.ForeignKey('DatosBase', models.DO_NOTHING)
    temario = models.ForeignKey(Temario, on_delete=models.SET_NULL, null=True, blank=True)
    actividades = models.ForeignKey(Actividades, on_delete=models.SET_NULL, null=True, blank=True)
    cronograma = models.TextField()
    fecha_creacion = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'cronograma'





