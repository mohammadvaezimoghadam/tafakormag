from django.urls import path
from .views import (
    DonationCampaignListCreateView,
    DonationCampaignDetailView,
    DonationInitiateView,
    PaymentVerifyView,
    TransparencyLogCreateView
)

urlpatterns = [
    path('campaigns/', DonationCampaignListCreateView.as_view(), name='donation-campaign-list-create'),
    path('campaigns/<uuid:id>/', DonationCampaignDetailView.as_view(), name='donation-campaign-detail'),
    path('campaigns/<uuid:id>/donate/', DonationInitiateView.as_view(), name='donation-campaign-donate'),
    path('campaigns/<uuid:id>/transparency/', TransparencyLogCreateView.as_view(), name='donation-campaign-transparency'),
    path('payment/verify/', PaymentVerifyView.as_view(), name='donation-payment-verify'),
]
