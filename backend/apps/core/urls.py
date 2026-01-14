from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import DashboardStatsView, SocialAuthCallbackView, CurrentUserView, CustomTokenObtainPairView

urlpatterns = [
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # Alias para que coincida con el frontend
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('me/', CurrentUserView.as_view(), name='current_user'),
    path('dashboard-stats/', DashboardStatsView.as_view(), name='dashboard_stats'),
    path('social/callback/', SocialAuthCallbackView.as_view(), name='social_callback'),
]
