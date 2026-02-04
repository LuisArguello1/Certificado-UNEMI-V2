from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from apps.core.forms.base_form import BaseFormMixin

User = get_user_model()

class CustomUserCreationForm(BaseFormMixin, UserCreationForm):
    """
    Formulario para crear usuarios desde el panel de administración (interno).
    """
    # Sobrescribir password1 y password2 para eliminar help_text
    password1 = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput,
        help_text='',  # Eliminamos el help_text por defecto
        strip=False,
    )
    password2 = forms.CharField(
        label='Confirmar contraseña',
        widget=forms.PasswordInput,
        help_text='',  # Eliminamos el help_text por defecto
        strip=False,
    )
    
    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        if password and not (len(password) >= 10 and any(c.isupper() for c in password) and any(c.isdigit() for c in password)):
            raise forms.ValidationError('La contraseña debe tener al menos 10 caracteres, una mayúscula y un número.')
        return password
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 
                 'is_only_read', 'can_modify', 'can_delete', 'can_send_email')

class CustomUserChangeForm(BaseFormMixin, UserChangeForm):
    """
    Formulario para editar usuarios existentes.
    """
    # Removemos el password field para que no sea editable directamente aquí o usamos el default link
    password = None 

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active',
                 'is_only_read', 'can_modify', 'can_delete', 'can_send_email')
