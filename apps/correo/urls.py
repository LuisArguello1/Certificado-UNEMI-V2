from django.urls import path
from .views import campaign_views as views

app_name = 'correo'

urlpatterns = [
    # Gestión de campana
    path('', views.CampaignListView.as_view(), name='list'),
    path('crear/', views.CreateCampaignView.as_view(), name='create'),
    path('editar/<int:pk>/', views.EditCampaignView.as_view(), name='edit'),
    path('preview/<int:pk>/', views.PreviewCampaignView.as_view(), name='preview'),
    path('enviar/<int:pk>/', views.SendCampaignView.as_view(), name='send'),
    path('detalle/<int:pk>/', views.CampaignDetailView.as_view(), name='detail'),
    path('reintentar/<int:pk>/', views.RetrySendView.as_view(), name='retry'),
]
