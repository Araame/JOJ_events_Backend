from django.urls import path
from .views import BilletListCreateView, BilletDetailView, PaymentCreateView, PaymentDetailView, ScannerBilletView

urlpatterns = [
    path('tickets/', BilletListCreateView.as_view(), name='billet-list-create'),
    path('tickets/<int:pk>/', BilletDetailView.as_view(), name='billet-detail'),
    path('payments/', PaymentCreateView.as_view(), name='payment-create'),
    path('payments/<int:pk>/', PaymentDetailView.as_view(), name='payment-detail'),
    path('scanner/<uuid:code_unique>/', ScannerBilletView.as_view(), name='scanner-billet'),
]
