from django.urls import path
from .views import DashboardMetricsView

urlpatterns = [
    path('dashboard/', DashboardMetricsView.as_view(), name='dashboard_metrics'),
]
