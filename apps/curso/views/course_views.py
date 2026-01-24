from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.shortcuts import redirect
from django.http import HttpResponse, Http404
from ..models import Curso, Estudiante, PlantillaCertificado, Certificado
from ..forms.curso_form import CursoForm, PlantillaCertificadoForm, CursoCertificateConfigForm, EstudianteForm
import json
import pandas as pd
import zipfile
import io

class ExcelProcessMixin:
    """
    Mixin para procesar el archivo Excel de estudiantes.
    """
    def procesar_excel(self, curso):
        if not curso.archivo_estudiantes:
            return

        try:
            file_path = curso.archivo_estudiantes.path
            # Leemos sin encabezados inicialmente para buscar la fila de títulos
            df_raw = pd.read_excel(file_path, header=None, dtype=str)
            
            # Mapeo de columnas buscadas
            col_keywords = {
                'nombres': ['nombres', 'nombre', 'nombre completo', 'estudiante', 'nombres y apellidos', 'nombres y apellidos completos', 'alumno'],
                'cedula': ['cedula', 'cédula', 'id', 'dni', 'identificación', 'identificacion', 'nro cedula', 'identificaci'],
                'correo': ['correo', 'email', 'correo electrónico', 'correo electronico', 'e-mail']
            }

            header_row_index = -1
            found_columns = {}

            # Buscamos en las primeras 20 filas la fila que contenga los encabezados
            for i, row in df_raw.head(20).iterrows():
                row_values = [str(val).strip().lower() for val in row if pd.notna(val)]
                
                matches = {}
                for key, keywords in col_keywords.items():
                    for kw in keywords:
                        # Buscamos coincidencia exacta o parcial en los valores de la fila
                        for idx, val in enumerate(row):
                            val_clean = str(val).strip().lower()
                            if kw == val_clean or kw in val_clean:
                                matches[key] = idx
                                break
                
                # Si encontramos al menos nombre y cédula, esta es nuestra fila de cabecera
                if 'nombres' in matches and 'cedula' in matches:
                    header_row_index = i
                    found_columns = matches
                    break

            if header_row_index == -1:
                messages.warning(self.request, "No se pudo identificar la fila de encabezados. Asegúrese de que existan columnas llamadas 'Nombre' y 'Cédula'.")
                return

            # Re-leer el dataframe desde la fila encontrada
            df = pd.read_excel(file_path, skiprows=header_row_index, dtype=str)
            # Limpiar nombres de columnas para usar los índices detectados si es necesario o nombres reales
            df.columns = [str(c).strip().lower() for c in df.columns]

            # Re-mapear columnas sobre el nuevo DF
            col_nombre = None
            col_cedula = None
            col_correo = None

            for col in df.columns:
                for key, keywords in col_keywords.items():
                    for kw in keywords:
                        if kw == col or kw in col:
                            if key == 'nombres': col_nombre = col
                            if key == 'cedula': col_cedula = col
                            if key == 'correo': col_correo = col
                            break

            estudiantes_creados = 0
            # Procesar filas
            for index, row in df.iterrows():
                cedula_raw = str(row[col_cedula]).strip() if col_cedula else None
                if not cedula_raw or cedula_raw.lower() == 'nan':
                    continue

                # Normalizar cédula a 10 dígitos (Ecuador)
                if len(cedula_raw) == 9 and cedula_raw.isdigit():
                    cedula_final = '0' + cedula_raw
                else:
                    cedula_final = cedula_raw

                nombre_limpio = str(row[col_nombre]).strip() if col_nombre else "Sin Nombre"
                correo_limpio = str(row[col_correo]).strip().lower() if col_correo and pd.notna(row[col_correo]) else ""

                if cedula_final:
                    Estudiante.objects.update_or_create(
                        curso=curso,
                        cedula=cedula_final,
                        defaults={
                            'nombre_completo': " ".join(nombre_limpio.split()),
                            'correo': correo_limpio,
                        }
                    )
                    estudiantes_creados += 1

            messages.success(self.request, f"Excel procesado con éxito: {estudiantes_creados} estudiantes registrados.")

        except Exception as e:
            messages.error(self.request, f"Error al procesar el Excel: {str(e)}")


class CursoListView(ListView):
    model = Curso
    template_name = 'curso/admin/curso_list.html'
    context_object_name = 'cursos'
    paginate_by = 10


class CursoCreateView(ExcelProcessMixin, CreateView):
    model = Curso
    form_class = CursoForm
    template_name = 'curso/admin/curso_form.html'
    success_url = reverse_lazy('curso:list')

    def form_valid(self, form):
        # Limpiar nombre y responsable (sin saltos de línea)
        nombre = form.cleaned_data.get('nombre')
        responsable = form.cleaned_data.get('responsable')

        if nombre:
            form.cleaned_data['nombre'] = " ".join(str(nombre).split())

        if responsable:
            form.cleaned_data['responsable'] = " ".join(str(responsable).split())

        response = super().form_valid(form)
        self.procesar_excel(self.object)
        
        # Si se seleccionó una plantilla, ir directo al configurador
        if self.object.plantilla_certificado:
            return redirect('curso:config', pk=self.object.pk)
            
        return response


class CursoUpdateView(ExcelProcessMixin, UpdateView):
    model = Curso
    form_class = CursoForm
    template_name = 'curso/admin/curso_form.html'
    success_url = reverse_lazy('curso:list')

    def form_valid(self, form):
        # Limpiar nombre y responsable (sin saltos de línea)
        nombre = form.cleaned_data.get('nombre')
        responsable = form.cleaned_data.get('responsable')

        if nombre:
            form.cleaned_data['nombre'] = " ".join(str(nombre).split())

        if responsable:
            form.cleaned_data['responsable'] = " ".join(str(responsable).split())

        # Si se cambió el archivo de estudiantes, volver a procesar
        if 'archivo_estudiantes' in form.changed_data:
            response = super().form_valid(form)
            self.procesar_excel(self.object)
            return response

        return super().form_valid(form)


class CursoDeleteView(DeleteView):
    model = Curso
    template_name = 'curso/admin/curso_confirm_delete.html'
    success_url = reverse_lazy('curso:list')


# --- Vistas de Plantillas ---

class PlantillaListView(ListView):
    model = PlantillaCertificado
    template_name = 'curso/admin/plantilla_list.html'
    context_object_name = 'plantillas'
    paginate_by = 10


class PlantillaCreateView(CreateView):
    model = PlantillaCertificado
    form_class = PlantillaCertificadoForm
    template_name = 'curso/admin/plantilla_form.html'
    success_url = reverse_lazy('curso:plantilla_list')

    def form_valid(self, form):
        messages.success(self.request, "Plantilla creada correctamente.")
        return super().form_valid(form)


class PlantillaUpdateView(UpdateView):
    model = PlantillaCertificado
    form_class = PlantillaCertificadoForm
    template_name = 'curso/admin/plantilla_form.html'
    success_url = reverse_lazy('curso:plantilla_list')

    def form_valid(self, form):
        messages.success(self.request, "Plantilla actualizada correctamente.")
        return super().form_valid(form)


class PlantillaDeleteView(DeleteView):
    model = PlantillaCertificado
    template_name = 'curso/admin/plantilla_confirm_delete.html'
    success_url = reverse_lazy('curso:plantilla_list')


# --- Configuración de Certificado por Curso ---

class CursoCertificateConfigView(UpdateView):
    model = Curso
    form_class = CursoCertificateConfigForm
    template_name = 'curso/admin/curso_certificate_config.html'

    def get_success_url(self):
        return reverse_lazy('curso:estudiantes', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, "Configuración del certificado guardada.")
        return super().form_valid(form)


# --- Gestión de Estudiantes y Certificados ---

class CursoEstudiantesView(ListView):
    model = Estudiante
    template_name = 'curso/admin/curso_estudiantes.html'
    context_object_name = 'estudiantes'

    def get_queryset(self):
        return Estudiante.objects.filter(curso_id=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        curso = Curso.objects.get(pk=self.kwargs['pk'])
        context['curso'] = curso
        # Verificar si hay al menos un certificado generado para habilitar el ZIP
        context['estudiantes_con_cert'] = Certificado.objects.filter(
            estudiante__curso=curso, 
            archivo_generado__isnull=False
        ).exclude(archivo_generado='').exists()
        return context


# --- CRUD de Estudiantes (Admin) ---

class EstudianteCreateView(CreateView):
    model = Estudiante
    form_class = EstudianteForm
    template_name = 'curso/admin/estudiante_form.html'

    def get_success_url(self):
        return reverse_lazy('curso:estudiantes', kwargs={'pk': self.kwargs['pk']})

    def form_valid(self, form):
        form.instance.curso_id = self.kwargs['pk']
        messages.success(self.request, "Estudiante registrado con éxito.")
        return super().form_valid(form)

class EstudianteUpdateView(UpdateView):
    model = Estudiante
    form_class = EstudianteForm
    template_name = 'curso/admin/estudiante_form.html'
    
    def get_success_url(self):
        return reverse_lazy('curso:estudiantes', kwargs={'pk': self.object.curso.pk})

    def form_valid(self, form):
        messages.success(self.request, "Datos del estudiante actualizados.")
        return super().form_valid(form)

class EstudianteDeleteView(DeleteView):
    model = Estudiante
    template_name = 'curso/admin/estudiante_confirm_delete.html'
    
    def get_success_url(self):
        return reverse_lazy('curso:estudiantes', kwargs={'pk': self.object.curso.pk})

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Estudiante eliminado del curso.")
        return super().delete(request, *args, **kwargs)

class GenerarCertificadoView(UpdateView):
    """
    Genera el certificado para un estudiante específico.
    """
    def post(self, request, pk):
        from ..services.certificate_service import CertificateService
        estudiante = Estudiante.objects.get(pk=pk)
        curso = estudiante.curso

        if not curso.plantilla_certificado or not curso.configuracion_certificado:
            messages.error(request, "Debe configurar el certificado del curso antes de generarlo.")
            return redirect('curso:estudiantes', pk=curso.pk)

        certificado, created = Certificado.objects.update_or_create(
            estudiante=estudiante,
            defaults={'plantilla': curso.plantilla_certificado}
        )

        res = CertificateService.generate_pdf(certificado)
        if res:
            messages.success(request, f"Certificado generado para {estudiante.nombre_completo}")
        else:
            messages.error(request, f"Error al generar el certificado para {estudiante.nombre_completo}. Verifique la configuración.")
            
        return redirect('curso:estudiantes', pk=estudiante.curso.pk)

class GenerarTodosCertificadosView(UpdateView):
    """
    Genera certificados para TODOS los estudiantes de un curso.
    """
    def post(self, request, pk):
        from ..services.certificate_service import CertificateService
        curso = Curso.objects.get(pk=pk)
        estudiantes = Estudiante.objects.filter(curso=curso)
        
        exitos = 0
        errores = 0
        
        if not curso.plantilla_certificado or not curso.configuracion_certificado:
            messages.error(request, "Debe seleccionar una plantilla y guardar la configuración en el 'Configurador' antes de generar certificados.")
            return redirect('curso:estudiantes', pk=pk)

        for estudiante in estudiantes:
            try:
                # Usamos update_or_create para asegurar que se use la plantilla actual del curso
                certificado, created = Certificado.objects.update_or_create(
                    estudiante=estudiante,
                    defaults={'plantilla': curso.plantilla_certificado}
                )
                res = CertificateService.generate_pdf(certificado)
                if res:
                    exitos += 1
                else:
                    errores += 1
            except Exception as e:
                print(f"Error generando certificado para {estudiante}: {e}")
                errores += 1
        
        messages.success(request, f"Proceso terminado: {exitos} certificados generados. {errores} errores.")
        return redirect('curso:estudiantes', pk=pk)

class DescargarCertificadosZipView(ListView):
    """
    Empaqueta todos los certificados generados de un curso en un ZIP.
    """
    def get(self, request, pk):
        curso = Curso.objects.get(pk=pk)
        estudiantes = Estudiante.objects.filter(curso=curso)
        
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as zip_file:
            for estudiante in estudiantes:
                certificado = Certificado.objects.filter(estudiante=estudiante).first()
                if certificado and certificado.archivo_generado:
                    # Nombre del archivo dentro del ZIP
                    nombre_est = estudiante.nombre_completo.replace(" ", "_").upper()
                    zip_path = f"{nombre_est}_{estudiante.cedula}.pdf"
                    zip_file.write(certificado.archivo_generado.path, zip_path)
        
        if buffer.tell() == 0:
            messages.warning(request, "No hay certificados generados para descargar.")
            return redirect('curso:estudiantes', pk=pk)
            
        buffer.seek(0)
        response = HttpResponse(buffer.read(), content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="Certificados_{curso.nombre.replace(" ", "_")}.zip"'
        return response
