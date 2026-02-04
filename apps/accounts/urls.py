from django.urls import path
from .views import (
    CustomLoginView, CustomLogoutView, UserListView, UserCreateView, 
    UserUpdateView, UserDeleteView, UserToggleActiveView, UserPasswordChangeView
)

app_name = 'accounts'

urlpatterns = [
    # Auth
    path('portal-acceso/', CustomLoginView.as_view(), name='login'),
    path('finalizar-sesion/', CustomLogoutView.as_view(), name='logout'),
    
    # User Management
    path('users/', UserListView.as_view(), name='user_list'),
    path('users/create/', UserCreateView.as_view(), name='user_create'),
    path('users/<int:pk>/edit/', UserUpdateView.as_view(), name='user_update'),
    path('users/<int:pk>/delete/', UserDeleteView.as_view(), name='user_delete'),
    path('users/<int:pk>/toggle-active/', UserToggleActiveView.as_view(), name='user_toggle_active'),
    path('users/<int:pk>/password-change/', UserPasswordChangeView.as_view(), name='user_password_change'),
]

