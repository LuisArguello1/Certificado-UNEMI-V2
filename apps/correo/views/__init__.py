"""
Views para la app Correo.
"""
from .campaign_views import (
    CreateCampaignView,
    PreviewCampaignView,
    SendCampaignView,
    CampaignListView,
    CampaignDetailView,
    CampaignDetailView,
    RetrySendView,
    EditCampaignView
)

__all__ = [
    'CreateCampaignView',
    'PreviewCampaignView',
    'SendCampaignView',
    'CampaignListView',
    'CampaignDetailView',
    'CampaignDetailView',
    'RetrySendView',
    'EditCampaignView'
]
