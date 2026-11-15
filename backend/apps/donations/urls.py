from django.urls import path
from .views import (
    DonationCampaignListCreateView,
    DonationCampaignDetailView,
    DonationInitiateView,
    PaymentCallbackView,
    PaymentVerifyView,
    TransparencyLogCreateView,
    CampaignApproveView,
    CampaignPayoutListCreateView,
    AdminPayoutListView,
    PayoutProcessView
)

urlpatterns = [
    path('campaigns/', DonationCampaignListCreateView.as_view(), name='donation-campaign-list-create'),
    path('campaigns/<uuid:id>/', DonationCampaignDetailView.as_view(), name='donation-campaign-detail'),
    path('campaigns/<uuid:id>/approve/', CampaignApproveView.as_view(), name='donation-campaign-approve'),
    path('campaigns/<uuid:id>/donate/', DonationInitiateView.as_view(), name='donation-campaign-donate'),
    path('campaigns/<uuid:id>/transparency/', TransparencyLogCreateView.as_view(), name='donation-campaign-transparency'),
    path('campaigns/<uuid:id>/payouts/', CampaignPayoutListCreateView.as_view(), name='donation-campaign-payouts'),
    path('payouts/', AdminPayoutListView.as_view(), name='donation-admin-payouts'),
    path('payouts/<uuid:id>/process/', PayoutProcessView.as_view(), name='donation-payout-process'),
    path('payment/callback/', PaymentCallbackView.as_view(), name='donation-payment-callback'),
    path('payment/verify/', PaymentVerifyView.as_view(), name='donation-payment-verify'),
]

