from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, View
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.core.files.storage import FileSystemStorage
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, Http404, JsonResponse
import uuid
from django.shortcuts import get_object_or_404
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


class CursoListView(LoginRequiredMixin, ListView):
    model = Curso
    template_name = 'curso/admin/curso_list.html'
    context_object_name = 'cursos'
    paginate_by = 10
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            from apps.core.services.menu_service import MenuService
            context['menu_items'] = MenuService.get_menu_items(self.request.path, self.request.user)
        except ImportError:
            context['menu_items'] = []
            
        context['breadcrumbs'] = [{'name': 'Cursos'}]
        context['page_title'] = 'Lista de Cursos'
        return context


class CursoCreateView(LoginRequiredMixin, ExcelProcessMixin, CreateView):
    model = Curso
    form_class = CursoForm
    template_name = 'curso/admin/curso_form.html'
    success_url = reverse_lazy('curso:list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            from apps.core.services.menu_service import MenuService
            context['menu_items'] = MenuService.get_menu_items(self.request.path, self.request.user)
        except ImportError:
            context['menu_items'] = []
            
        context['breadcrumbs'] = [
            {'name': 'Cursos', 'url': reverse('curso:list')},
            {'name': 'Crear Curso'}
        ]
        context['page_title'] = 'Crear Nuevo Curso'
        context['plantillas_disponibles'] = PlantillaCertificado.objects.all()
        return context

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


class CursoUpdateView(LoginRequiredMixin, ExcelProcessMixin, UpdateView):
    model = Curso
    form_class = CursoForm
    template_name = 'curso/admin/curso_form.html'
    success_url = reverse_lazy('curso:list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            from apps.core.services.menu_service import MenuService
            context['menu_items'] = MenuService.get_menu_items(self.request.path, self.request.user)
        except ImportError:
            context['menu_items'] = []
            
        context['breadcrumbs'] = [
            {'name': 'Cursos', 'url': reverse('curso:list')},
            {'name': 'Editar Curso'}
        ]
        context['page_title'] = f'Editar: {self.object.nombre}'
        context['plantillas_disponibles'] = PlantillaCertificado.objects.all()
        return context

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


class CursoDeleteView(LoginRequiredMixin, DeleteView):
    model = Curso
    template_name = 'curso/admin/curso_confirm_delete.html'
    success_url = reverse_lazy('curso:list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            from apps.core.services.menu_service import MenuService
            context['menu_items'] = MenuService.get_menu_items(self.request.path, self.request.user)
        except ImportError:
            context['menu_items'] = []
            
        context['breadcrumbs'] = [
            {'name': 'Cursos', 'url': reverse('curso:list')},
            {'name': 'Eliminar Curso'}
        ]
        context['page_title'] = 'Eliminar Curso'
        return context


class CursoToggleStatusView(LoginRequiredMixin, View):
    def post(self, request, pk):
        try:
            curso = Curso.objects.get(pk=pk)
            # Toggle logic: disponible <-> oculto
            if curso.estado == 'disponible':
                curso.estado = 'oculto'
                is_active = False
            else:
                curso.estado = 'disponible'
                is_active = True
                
            curso.save(update_fields=['estado'])
            
            return HttpResponse(
                json.dumps({'success': True, 'is_active': is_active, 'message': 'Estado actualizado correctamente.'}),
                content_type='application/json'
            )
        except Curso.DoesNotExist:
            return HttpResponse(
                json.dumps({'success': False, 'error': 'Curso no encontrado.'}),
                content_type='application/json',
                status=404
            )
        except Exception as e:
            return HttpResponse(
                json.dumps({'success': False, 'error': str(e)}),
                content_type='application/json',
                status=500
            )


# --- Vistas de Plantillas ---

class PlantillaListView(LoginRequiredMixin, ListView):
    model = PlantillaCertificado
    template_name = 'curso/admin/plantilla_list.html'
    context_object_name = 'plantillas'
    paginate_by = 10
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            from apps.core.services.menu_service import MenuService
            context['menu_items'] = MenuService.get_menu_items(self.request.path, self.request.user)
        except ImportError:
            context['menu_items'] = []
            
        context['breadcrumbs'] = [{'name': 'Plantillas de Certificados'}]
        context['page_title'] = 'Plantillas de Certificados'
        return context


class PlantillaCreateView(LoginRequiredMixin, CreateView):
    model = PlantillaCertificado
    form_class = PlantillaCertificadoForm
    template_name = 'curso/admin/plantilla_form.html'
    success_url = reverse_lazy('curso:plantilla_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            from apps.core.services.menu_service import MenuService
            context['menu_items'] = MenuService.get_menu_items(self.request.path, self.request.user)
        except ImportError:
            context['menu_items'] = []
            
        context['breadcrumbs'] = [
            {'name': 'Plantillas', 'url': reverse('curso:plantilla_list')},
            {'name': 'Crear Plantilla'}
        ]
        context['page_title'] = 'Crear Nueva Plantilla'
        return context

    def form_valid(self, form):
        messages.success(self.request, "Plantilla creada correctamente.")
        return super().form_valid(form)


class PlantillaUpdateView(LoginRequiredMixin, UpdateView):
    model = PlantillaCertificado
    form_class = PlantillaCertificadoForm
    template_name = 'curso/admin/plantilla_form.html'
    success_url = reverse_lazy('curso:plantilla_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            from apps.core.services.menu_service import MenuService
            context['menu_items'] = MenuService.get_menu_items(self.request.path, self.request.user)
        except ImportError:
            context['menu_items'] = []
            
        context['breadcrumbs'] = [
            {'name': 'Plantillas', 'url': reverse('curso:plantilla_list')},
            {'name': 'Editar Plantilla'}
        ]
        context['page_title'] = f'Editar: {self.object.nombre}'
        return context

    def form_valid(self, form):
        messages.success(self.request, "Plantilla actualizada correctamente.")
        return super().form_valid(form)


class PlantillaDeleteView(LoginRequiredMixin, DeleteView):
    model = PlantillaCertificado
    template_name = 'curso/admin/plantilla_confirm_delete.html'
    success_url = reverse_lazy('curso:plantilla_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            from apps.core.services.menu_service import MenuService
            context['menu_items'] = MenuService.get_menu_items(self.request.path, self.request.user)
        except ImportError:
            context['menu_items'] = []
            
        context['breadcrumbs'] = [
            {'name': 'Plantillas', 'url': reverse('curso:plantilla_list')},
            {'name': 'Eliminar Plantilla'}
        ]
        context['page_title'] = 'Eliminar Plantilla'
        return context


# --- Configuración de Certificado por Curso ---

class CursoCertificateConfigView(LoginRequiredMixin, UpdateView):
    model = Curso
    form_class = CursoCertificateConfigForm
    template_name = 'curso/admin/curso_certificate_config.html'

    def get_success_url(self):
        return reverse_lazy('curso:estudiantes', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            from apps.core.services.menu_service import MenuService
            context['menu_items'] = MenuService.get_menu_items(self.request.path, self.request.user)
        except ImportError:
            context['menu_items'] = []
            
        context['breadcrumbs'] = [
            {'name': 'Cursos', 'url': reverse('curso:list')},
            {'name': self.object.nombre, 'url': reverse('curso:estudiantes', kwargs={'pk': self.object.pk})},
            {'name': 'Configurar Certificado'}
        ]
        context['page_title'] = f'Configurar Certificado - {self.object.nombre}'
        # Tomar el primer estudiante para la previsualización real
        context['preview_student'] = self.object.estudiantes.first()
        return context

    def form_valid(self, form):
        messages.success(self.request, "Configuración del certificado guardada.")
        return super().form_valid(form)


# --- Gestión de Estudiantes y Certificados ---

class CursoEstudiantesView(LoginRequiredMixin, ListView):
    model = Estudiante
    template_name = 'curso/admin/curso_estudiantes.html'
    context_object_name = 'estudiantes'

    def get_queryset(self):
        # Optimization: Prefetch verification to avoid N+1 queries when listing certificates
        return Estudiante.objects.filter(curso_id=self.kwargs['pk']).prefetch_related('certificados')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        curso = Curso.objects.get(pk=self.kwargs['pk'])
        try:
            from apps.core.services.menu_service import MenuService
            context['menu_items'] = MenuService.get_menu_items(self.request.path, self.request.user)
        except ImportError:
            context['menu_items'] = []
            
        context['breadcrumbs'] = [
            {'name': 'Cursos', 'url': reverse('curso:list')},
            {'name': curso.nombre}
        ]
        context['page_title'] = f'Estudiantes - {curso.nombre}'
        context['curso'] = curso
        # Verificar si hay al menos un certificado generado para habilitar el ZIP
        # Optimized check
        context['estudiantes_con_cert'] = Certificado.objects.filter(
            estudiante__curso_id=curso.pk, 
            archivo_generado__isnull=False
        ).exclude(archivo_generado='').exists()
        return context


# --- CRUD de Estudiantes (Admin) ---

class EstudianteCreateView(LoginRequiredMixin, CreateView):
    model = Estudiante
    form_class = EstudianteForm
    template_name = 'curso/admin/estudiante_form.html'

    def get_success_url(self):
        return reverse_lazy('curso:estudiantes', kwargs={'pk': self.kwargs['pk']})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        curso = Curso.objects.get(pk=self.kwargs['pk'])
        try:
            from apps.core.services.menu_service import MenuService
            context['menu_items'] = MenuService.get_menu_items(self.request.path, self.request.user)
        except ImportError:
            context['menu_items'] = []
            
        context['breadcrumbs'] = [
            {'name': 'Cursos', 'url': reverse('curso:list')},
            {'name': curso.nombre, 'url': reverse('curso:estudiantes', kwargs={'pk': curso.pk})},
            {'name': 'Registrar Estudiante'}
        ]
        context['page_title'] = 'Registrar Nuevo Estudiante'
        return context

    def form_valid(self, form):
        form.instance.curso_id = self.kwargs['pk']
        messages.success(self.request, "Estudiante registrado con éxito.")
        return super().form_valid(form)

class EstudianteUpdateView(LoginRequiredMixin, UpdateView):
    model = Estudiante
    form_class = EstudianteForm
    template_name = 'curso/admin/estudiante_form.html'
    
    def get_success_url(self):
        return reverse_lazy('curso:estudiantes', kwargs={'pk': self.object.curso.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            from apps.core.services.menu_service import MenuService
            context['menu_items'] = MenuService.get_menu_items(self.request.path, self.request.user)
        except ImportError:
            context['menu_items'] = []
            
        context['breadcrumbs'] = [
            {'name': 'Cursos', 'url': reverse('curso:list')},
            {'name': self.object.curso.nombre, 'url': reverse('curso:estudiantes', kwargs={'pk': self.object.curso.pk})},
            {'name': 'Editar Estudiante'}
        ]
        context['page_title'] = f'Editar: {self.object.nombre_completo}'
        return context

    def form_valid(self, form):
        messages.success(self.request, "Datos del estudiante actualizados.")
        return super().form_valid(form)

class EstudianteDeleteView(LoginRequiredMixin, DeleteView):
    model = Estudiante
    template_name = 'curso/admin/estudiante_confirm_delete.html'
    
    def get_success_url(self):
        return reverse_lazy('curso:estudiantes', kwargs={'pk': self.object.curso.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            from apps.core.services.menu_service import MenuService
            context['menu_items'] = MenuService.get_menu_items(self.request.path, self.request.user)
        except ImportError:
            context['menu_items'] = []
            
        context['breadcrumbs'] = [
            {'name': 'Cursos', 'url': reverse('curso:list')},
            {'name': self.object.curso.nombre, 'url': reverse('curso:estudiantes', kwargs={'pk': self.object.curso.pk})},
            {'name': 'Eliminar Estudiante'}
        ]
        context['page_title'] = 'Eliminar Estudiante'
        return context

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Estudiante eliminado del curso.")
        return super().delete(request, *args, **kwargs)

class GenerarCertificadoView(UpdateView):
    """
    Genera el certificado para un estudiante específico.
    """
    def post(self, request, pk):
        from ..services.certificate_service import CertificateService
        # Optimization: Select related to avoid extra query for course
        estudiante = get_object_or_404(Estudiante.objects.select_related('curso'), pk=pk)
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
        # Optimization: Use iterator() for large datasets if needed, though for generation step by step 
        # standard iteration is mostly IO bound by PDF generation.
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
        
        # Optimization: Fetch ONLY students that effectively have certificates 
        # and prefetch those certificates to avoid N+1.
        # This is much faster than getting all students and then filtering in python
        # or doing query per student.
        estudiantes_con_cert = Estudiante.objects.filter(
            curso=curso,
            certificados__archivo_generado__isnull=False
        ).prefetch_related('certificados').distinct()
        
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as zip_file:
            for estudiante in estudiantes_con_cert:
                # With prefetch, this does not hit DB again
                certificado = estudiante.certificados.all()[0]
                
                if certificado.archivo_generado:
                    # Nombre del archivo dentro del ZIP
                    nombre_est = estudiante.nombre_completo.replace(" ", "_").upper()
                    zip_path = f"{nombre_est}_{estudiante.cedula}.pdf"
                    
                    try:
                         # We need full path on disk
                        zip_file.write(certificado.archivo_generado.path, zip_path)
                    except ValueError:
                         # File might be missing on disk even if DB record exists
                        pass
        
        if buffer.tell() == 0:
            messages.warning(request, "No hay certificados generados válidos para descargar.")
            return redirect('curso:estudiantes', pk=pk)
            
        buffer.seek(0)
        response = HttpResponse(buffer.read(), content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="Certificados_{curso.nombre.replace(" ", "_")}.zip"'
        return response

@method_decorator(csrf_exempt, name='dispatch')
class CertificateImageUploadView(LoginRequiredMixin, View):
    def post(self, request):
        if 'image' not in request.FILES:
            return JsonResponse({'error': 'No image provided'}, status=400)
        
        image = request.FILES['image']
        fs = FileSystemStorage()
        
        # Save with unique name to avoid overwrite issues
        filename = fs.save(f'certificate_assets/{uuid.uuid4()}_{image.name}', image)
        file_url = fs.url(filename)
        
        return JsonResponse({'url': file_url})
