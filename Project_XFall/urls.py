from django.urls import path, re_path
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView
)
from XFall import settings
from django.conf.urls.static import static
from Project_XFall import views_admin, views_user
from . import views

urlpatterns=[
  ## Login Admin Related
  path('dashboard/admin', views_admin.DashboardViews, name="Dashboard"),
  path('register/admin', views_admin.RegisPageViews, name="Registration"),
  path('login/admin', views_admin.LoginPageViews, name="Login"),
  path('logout/admin', views_admin.LogoutPageViews, name="Logout"),
  path('contacts/admin', views_admin.ContactViews, name="Contacts"),
  path('services/admin', views_admin.ServiceViews, name="Services"),
  path('services/admin/<int:id>', views_admin.EditServiceViews, name="Set Services"),
  path('services/new/admin', views_admin.AddServiceViews, name="Add Service"),
  path('contacts/admin/<int:id>', views_admin.DeleteContactViews, name="Delete Contact"),

  ## Send Notification Related
  path('notify/fall-detected', views.NotifyFallViews.as_view()),
  # path('notify/user-removed', views.NotifyRelationViews.as_view()),
  path('test', views.TestSaveImage.as_view()),

  ## User Account Related
  path('login', views_user.UserLoginViews.as_view()),
  path('logout', views_user.UserLogoutViews.as_view()),
  path('register', views_user.UserRegisViews.as_view()),
  path('password', views_user.UserPasswordViews.as_view()),
  path('profile', views_user.UserProfileViews.as_view()),
  path('otp', views_user.UserVerificationViews.as_view()),
  path('profile-number', views_user.UserProfileNumberViews.as_view()),

  ## Service Related
  path('action', views_user.UserActionViews.as_view()),
  path('camera', views_user.UserCameraViews.as_view()),
  path('camera-detail', views_user.UserCameraDetailViews.as_view()),
  path('chat', views_user.UserChatViews.as_view()),
  path('chats', views_user.UserChatsViews.as_view()),
  path('contacts', views_user.EmergencyContactViews.as_view()),
  path('notification', views_user.UserNotificationViews.as_view()),
  path('notifications', views_user.UserNotificationsViews.as_view()),
  path('services', views_user.EmergencyServiceViews.as_view()),

  # path('services', views.EmergencyServiceViews.as_view()),
  # path('contacts', views.EmergencyContactViews.as_view()),
  # path('cameras', views.CameraViews.as_view()),
  # path('responses', views_user.ResponseViews.as_view()),
  # path('trigger', views.TriggerViews.as_view()),

  #path('home-page/', views.home_page),
  #path('trial/', views.UserViews.as_view()),
  #path('api/token/', views.MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
  path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
  path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
  
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)