from django.urls import path
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView
)

from Project_XFall import views_admin, views_user

from . import views
urlpatterns=[
  path('login/admin', views_admin.AdminLoginViews.as_view()),
  path('register/admin', views_admin.AdminRegisViews.as_view()),
  path('login', views_user.UserLoginViews.as_view()),
  path('register', views_user.UserRegisViews.as_view()),
  path('services', views.EmergencyServiceViews.as_view()),
  path('contacts', views.EmergencyContactViews.as_view()),
  path('cameras', views.CameraViews.as_view()),
  path('responses', views_user.ResponseViews.as_view()),
  path('trigger', views.TriggerViews.as_view()),

  #path('home-page/', views.home_page),
  #path('trial/', views.UserViews.as_view()),
  #path('api/token/', views.MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
  path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
  path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
  
]