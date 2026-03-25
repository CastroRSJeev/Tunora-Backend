from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('verify-otp/', views.verify_otp_view, name='verify-otp'),
    path('resend-otp/', views.resend_otp_view, name='resend-otp'),
    path('login/', views.login_view, name='login'),
    path('refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('logout/', views.logout_view, name='logout'),
    path('me/', views.me_view, name='me'),
    path('onboarding/', views.onboarding_view, name='onboarding'),
    path('forgot-password/', views.forgot_password_view, name='forgot-password'),
    path('verify-reset-otp/', views.verify_reset_otp_view, name='verify-reset-otp'),
    path('reset-password/', views.reset_password_view, name='reset-password'),
    path('verify-admin-otp/', views.verify_admin_login_otp, name='verify-admin-otp'),
    
    # Admin Management
    path('admin/stats/', views.admin_dashboard_stats, name='admin-stats'),
    path('admin/users/', views.admin_list_users, name='admin-list-users'),
    path('admin/users/<str:user_id>/toggle-ban/', views.admin_toggle_user_ban, name='admin-toggle-ban'),
    path('admin/songs/', views.admin_list_songs, name='admin-list-songs'),
    path('admin/songs/<str:song_id>/toggle-block/', views.admin_toggle_song_block, name='admin-toggle-block'),
]
