from django.urls import path

from .views import AdminPaymentListView

urlpatterns = [
    path('admin/list/', AdminPaymentListView.as_view(), name='admin_payment_list'),
]
