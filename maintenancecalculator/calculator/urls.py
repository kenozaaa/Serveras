from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.contrib import admin



urlpatterns = [
    # Redirect root URL to login or home
    path('', views.login_redirect_view, name='login_redirect'),

    # Home and calculation pages
    path('home/', views.home, name='home'),
    path('calculate/', views.calculate_fees_view, name='calculate_fees'),
    path('gpt-categorize/', views.gpt_categorize_view, name='gpt-categorize'),
    path('fees-dollars/', views.view_fees_dollars, name='view_fees_dollars'),
    path('download-fees/', views.download_fees, name='download_fees'),
    path('upload-fees/', views.upload_fees, name='upload_fees'),
    path('bulk_download/', views.bulk_download, name='bulk_download'),

    # Auth views for login/logout
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)