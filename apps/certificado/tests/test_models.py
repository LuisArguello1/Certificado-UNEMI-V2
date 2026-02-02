from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date
from ..models import Direccion, Modalidad, Tipo, TipoEvento, PlantillaBase, Evento, Estudiante, Certificado

class ModelTest(TestCase):
    def setUp(self):
        self.direccion = Direccion.objects.create(nombre="Dirección de Prueba", codigo="DP")
        self.modalidad = Modalidad.objects.create(nombre="Presencial", codigo="PRE")
        self.tipo = Tipo.objects.create(nombre="Curso", codigo="CUR")
        self.tipo_evento = TipoEvento.objects.create(nombre="Capacitación Docente", codigo="CAP")

    def test_direccion_creation(self):
        self.assertEqual(self.direccion.codigo, "DP")
        self.assertTrue(self.direccion.activo)

    def test_unique_active_plantilla_per_direccion(self):
        # Create first active template
        PlantillaBase.objects.create(
            direccion=self.direccion,
            nombre="Plantilla 1",
            archivo="path/to/file1.docx",
            es_activa=True
        )
        # Create second active template for same direction
        PlantillaBase.objects.create(
            direccion=self.direccion,
            nombre="Plantilla 2",
            archivo="path/to/file2.docx",
            es_activa=True
        )
        # The first one should have been deactivated automatically by the save method override
        p1 = PlantillaBase.objects.get(nombre="Plantilla 1")
        p2 = PlantillaBase.objects.get(nombre="Plantilla 2")
        self.assertFalse(p1.es_activa)
        self.assertTrue(p2.es_activa)

    def test_evento_date_validation(self):
        evento = Evento(
            direccion=self.direccion,
            modalidad=self.modalidad,
            nombre_evento="Evento Error",
            duracion_horas="10",
            fecha_inicio=date(2025, 2, 1),
            fecha_fin=date(2025, 1, 1), # End before start
            tipo=self.tipo,
            tipo_evento=self.tipo_evento
        )
        with self.assertRaises(ValidationError):
            evento.clean()

    def test_estudiante_unique_per_evento(self):
        evento = Evento.objects.create(
            direccion=self.direccion,
            modalidad=self.modalidad,
            nombre_evento="Evento Unico",
            duracion_horas="10",
            fecha_inicio=date(2025, 2, 1),
            fecha_fin=date(2025, 2, 2),
            tipo=self.tipo,
            tipo_evento=self.tipo_evento
        )
        Estudiante.objects.create(evento=evento, nombres_completos="Luis A", correo_electronico="luis@test.com")
        with self.assertRaises(Exception): # Should raise IntegrityError/UniqueConstraint
             Estudiante.objects.create(evento=evento, nombres_completos="Luis B", correo_electronico="luis@test.com")
