from django.urls import path

from .views import AdminReviewListView, AdminDeleteReviewView

urlpatterns = [
    path('admin/list/', AdminReviewListView.as_view(), name='admin_review_list'),
    path('admin/<int:pk>/delete/', AdminDeleteReviewView.as_view(), name='admin_delete_review'),
]
