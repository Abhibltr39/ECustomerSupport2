from django.urls import path
from . import views

urlpatterns = [
    # Home
    path('', views.home, name='home'),
    
    # Auth
    path('register/', views.user_register, name='user_register'),
    path('register/company/', views.create_company, name='create_company'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # User Dashboard
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    path('dashboard/company/create/', views.create_company, name='create_company'),
    
    # Company Dashboard (with slug for security)
    path('dashboard/company/<slug:slug>/', views.company_dashboard, name='company_dashboard'),
    path('dashboard/company/<slug:slug>/profile/', views.company_profile, name='company_profile'),
    path('dashboard/company/<slug:slug>/edit/', views.edit_company, name='edit_company'),
    
    # Customer Forms (Public)
    path('form/<str:unique_id>/', views.customer_form, name='customer_form'),
    
    # Feedback (with star rating)
    path('feedback/<str:token>/', views.submit_feedback, name='submit_feedback'),
    # urls.py
    path('dashboard/company/<slug:slug>/feedback/', views.company_feedback_list, name='company_feedback'),
]