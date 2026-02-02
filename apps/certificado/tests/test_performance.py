import time
from django.test import TransactionTestCase
from django.contrib.auth.models import User
from ..models import Direccion, Modalidad, Tipo, TipoEvento, Evento, Estudiante, Certificado
from datetime import date

class PerformanceTest(TransactionTestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester')
        self.direccion = Direccion.objects.create(nombre="D1", codigo="D1")
        self.modalidad = Modalidad.objects.create(nombre="M1", codigo="M1")
        self.tipo = Tipo.objects.create(nombre="T1", codigo="T1")
        self.tipo_evento = TipoEvento.objects.create(nombre="TE1", codigo="TE1")
        
        self.evento = Evento.objects.create(
            direccion=self.direccion,
            modalidad=self.modalidad,
            nombre_evento="Performance Event",
            duracion_horas="40",
            fecha_inicio=date(2025, 1, 1),
            fecha_fin=date(2025, 1, 10),
            tipo=self.tipo,
            tipo_evento=self.tipo_evento,
            created_by=self.user
        )

    def test_bulk_insertion_performance(self):
        num_students = 500
        start_time = time.time()
        
        estudiantes_objs = [
            Estudiante(
                evento=self.evento,
                nombres_completos=f"Estudiante {i}",
                correo_electronico=f"student{i}@test.com"
            )
            for i in range(num_students)
        ]
        Estudiante.objects.bulk_create(estudiantes_objs)
        
        end_time = time.time()
        duration = end_time - start_time
        print(f"\n--- PERFORMANCE RESULT ---")
        print(f"Inserción masiva de {num_students} estudiantes: {duration:4f} segundos")
        print(f"--------------------------\n")
        self.assertLess(duration, 2.0) # Should be fast

    def test_certificate_query_performance(self):
        # Insert some students and certificates
        num_certs = 200
        estudiantes = [
            Estudiante(evento=self.evento, nombres_completos=f"E{i}", correo_electronico=f"e{i}@t.com")
            for i in range(num_certs)
        ]
        Estudiante.objects.bulk_create(estudiantes)
        
        db_students = Estudiante.objects.all()
        certs = [
            Certificado(estudiante=s, estado='completed')
            for s in db_students
        ]
        Certificado.objects.bulk_create(certs)
        
        start_time = time.time()
        # Query testing reverse relation optimization
        results = Certificado.objects.select_related('estudiante', 'estudiante__evento').all()
        count = len(results)
        end_time = time.time()
        
        duration = end_time - start_time
        print(f"\n--- PERFORMANCE RESULT ---")
        print(f"Consulta optimizada de {count} certificados: {duration:.4f} segundos")
        print(f"--------------------------\n")
        self.assertLess(duration, 0.5)
