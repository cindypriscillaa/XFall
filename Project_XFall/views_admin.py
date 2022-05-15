import json
import datetime
from django.db import IntegrityError
from django.forms import ModelForm
from django.shortcuts import redirect, render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import ( 
    AdminTokenObtainPairSerializer, 
    CamerasUsersSerializer,
    ServiceSerializer, 
    UserSerializer)
from .models import Cameras, CamerasUsersRelation, EmergencyServices, Login, Roles, ServiceTypes, Users
from rest_framework_simplejwt.views import TokenObtainPairView
from django.core.exceptions import ObjectDoesNotExist
from .admin_forms import CreateAdminForm, LoginAdminForm, ServiceForm
from firebase_admin import messaging
from firebase_admin.messaging import Message

import os
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "C:/Users/LAPTOP/XFall/xfall-secretkey.json"


class AdminLoginViews(TokenObtainPairView):
    serializer_class = AdminTokenObtainPairSerializer

class AdminRegisViews(APIView):
    # renderer_classes = [TemplateHTMLRenderer]
    # template_name = 'register.html'

    def post(self, request):
      try:
        body_json = request.body.decode('utf-8')
        body = json.loads(body_json)

        try:
          if body['email'] is None:
            return Response({"Status": "Error", "Messages": "Required field is empty."}, status=status.HTTP_400_BAD_REQUEST)
          if body['username'] is None:
            return Response({"Status": "Error", "Messages": "Required field is empty."}, status=status.HTTP_400_BAD_REQUEST)
          if body['password'] is None:
            return Response({"Status": "Error", "Messages": "Required field is empty."}, status=status.HTTP_400_BAD_REQUEST)
          if body['phone_number'] is None:
            return Response({"Status": "Error", "Messages": "Required field is empty."}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
          return Response({"Status": "Error", "Messages": "Required field is empty."}, status=status.HTTP_400_BAD_REQUEST)

        cam = Cameras(name = body['camera_name'], created_date = datetime.datetime.now(),
            updated_date = datetime.datetime.now(), created_by = "superadmin", updated_by = "superadmin")
        cam.save()

        role = Roles.objects.get(name="Admin")

        body['camera'] = cam.id
        body['role'] = role.id
        body['is_verified'] = False
        body['created_date'] = datetime.datetime.now()
        body['updated_date'] = datetime.datetime.now()
        body['created_by'] = "superadmin"
        body['updated_by'] = "superadmin"
        serializer = UserSerializer(data=body)
        if serializer.is_valid():
          serializer.save()
          us = Users.objects.get(username=body['username'])
          userCamID = '{"camera": "' + str(cam.id) + '", "user": "' + str(us.id) + '"}'
          dict_userCamID = json.loads(userCamID)
          userCam = CamerasUsersSerializer(data=dict_userCamID) 
          if userCam.is_valid():
              userCam.save()
        else:
          cam.delete()
          return Response({"Status": "Error", "Messages": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"Status": "Success", "Messages": "Registration completed successfully!"}, status=status.HTTP_200_OK)
      except IntegrityError as e:
        cam.delete()
        
        if str(e).find("UNIQUE constraint failed") is not None:
          return Response({"Status": "Error", "Messages": "User already exists."}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({"Status": "Error", "Messages": "Registration failed."}, status=status.HTTP_400_BAD_REQUEST)

def RegisPageViews(request):
  form = CreateAdminForm()

  if request.method == 'POST':
    form = CreateAdminForm(request.POST)

    cam = Cameras(name = form['full_name'].value(), created_date = datetime.datetime.now(),
        updated_date = datetime.datetime.now(), created_by = "superadmin", updated_by = "superadmin")
    cam.save()

    role = Roles.objects.get(name="Admin")

    body = json.loads('{}')
    body['full_name'] = form['full_name'].value()
    body['email'] = form['email'].value()
    body['username'] = form['username'].value()
    body['password'] = form['password'].value()
    body['phone_number'] = form['phone_number'].value()

    body['camera'] = cam.id
    body['role'] = role.id
    body['is_verified'] = True
    body['created_date'] = datetime.datetime.now()# .strftime('%Y-%m-%d %H:%M:%S')
    body['updated_date'] = datetime.datetime.now()# .strftime('%Y-%m-%d %H:%M:%S')
    body['created_by'] = "superadmin"
    body['updated_by'] = "superadmin"
    serializer = UserSerializer(data=body)
    if serializer.is_valid():
      serializer.save()
      us = Users.objects.get(username=body['username'])
      userCamID = '{"camera": "' + str(cam.id) + '", "user": "' + str(us.id) + '"}'
      dict_userCamID = json.loads(userCamID)
      userCam = CamerasUsersSerializer(data=dict_userCamID) 
      if userCam.is_valid():
          userCam.save()
          return redirect("Login")
    else:
      cam.delete()
      if str(serializer.errors).find("already exists"):
        return render(request, 'alert.html', {'message':'User already exists', 'path':'/register/admin'}) #{'message':'English: User already exists. Indonesia: Pengguna sudah terdaftar.'})
   
  context = {'form': form}
  return render(request, 'register.html', context)

def LoginPageViews(request):
  form = LoginAdminForm()

  if request.method == 'POST':
    form = LoginAdminForm(request.POST)
    isNone = False

    if str(form['free'].value()).find("@") != -1 and str(form['free'].value()).find(".") != -1:
      try:
          user = Users.objects.get(email=form['free'].value(), is_verified=1)
      except ObjectDoesNotExist as e:
          isNone = True 
    else:
      try:
        user = Users.objects.get(username=form['free'].value(), is_verified=1)
      except ObjectDoesNotExist as e:
        isNone = True
    
    if isNone is True:
        return render(request, 'alert.html', {'message':"User does not exists", 'path':'/login/admin'})

    ## Check user role
    role = Roles.objects.get(name="Admin")
    if user.role_id != role.id:
        return render(request, 'alert.html', {'message':"User does not exists", 'path':'/login/admin'})

    if user.password != form['password'].value():
        return render(request, 'alert.html', {'message':"Login failed!", 'path':'/login/admin'})

    try: ## Check last login session
        list = Login.objects.all().filter(user_id=user.id)

        if list.count != 0:
            lastLogin = Login.objects.get(id=list.latest('created_date').id)
            lastLogin.login_status = "OFF"
            lastLogin.is_logged_out = True
            lastLogin.save()
    except ObjectDoesNotExist as e:
        pass

    loginSession = Login(login_status="ON",is_logged_out=False, user_id=user.id)
    loginSession.save()

    # context = {'id': 'user_id', 'value': user.id, 'action': 'set'}
    # render(request, 'localStorage.html', context)
    request.session['token'] = str(loginSession.token)
    return redirect("Dashboard")
   
  context = {'form': form}
  return render(request, 'login.html', context)

def DashboardViews(request):
  if request.session.has_key('token'):
    try: ## Check Login Session
        login = Login.objects.get(token=request.session['token'])
    except ObjectDoesNotExist as e:
        return render(request, 'alert.html', {'message':"No session found. Please login", 'path':'/login/admin'})

    ## Check Token
    if login.login_status != "ON" and login.is_logged_out != 0:
        return render(request, 'alert.html', {'message':"User already logged out", 'path':'/logout/admin'})
  else:
    return render(request, 'alert.html', {'message':"No session found. Please login", 'path':'/login/admin'})
  
  ## Get Relation
  try:
      relation = CamerasUsersRelation.objects.get(user_id=login.user_id)
  except ObjectDoesNotExist as e:
      return render(request, 'alert.html', {'message':"No data found", 'path':'/services/admin'})

  context = {'camera_id': str(relation.camera_id), 'connected_user': str(CamerasUsersRelation.objects.all().filter(camera_id=relation.camera_id).count() - 1)}
  return render(request, 'home.html', context)

def ContactViews(request):
  if request.method == 'GET':
    count = 0
    listContacts = []

    if request.session.has_key('token'):
      try: ## Check Login Session
          login = Login.objects.get(token=request.session['token'])
      except ObjectDoesNotExist as e:
          return render(request, 'alert.html', {'message':"No session found. Please login", 'path':'/login/admin'})

      ## Check Token
      if login.login_status != "ON" and login.is_logged_out != 0:
          return render(request, 'alert.html', {'message':"User already logged out", 'path':'/logout/admin'})
    else:
      return render(request, 'alert.html', {'message':"No session found. Please login", 'path':'/login/admin'})

    try:
        relation = CamerasUsersRelation.objects.get(user_id=login.user_id)
    except ObjectDoesNotExist as e:
        return render(request, 'alert.html', {'message':"No data found", 'path':'/contacts/admin'})

    try:
        related_user = CamerasUsersRelation.objects.all().filter(camera_id=relation.camera_id)
        datas = CamerasUsersRelation.objects.all().filter(camera_id=relation.camera_id).count()
    except ObjectDoesNotExist as e:
        return render(request, 'alert.html', {'message':"No data found", 'path':'/contacts/admin'})

    role = Roles.objects.get(name="User")
    try: 
      while (count != datas):
        if related_user[count].user_id != login.user_id:
          contact = Users.objects.get(id=related_user[count].user_id, role_id=role.id, is_verified=1)
        else:
          count = count+1
          continue
                              ## contact.profile_image
        contactDetail = {"img": contact.profile_image, "name": contact.full_name, "phone_number": contact.phone_number}
        listContacts.append(contactDetail)
        count = count+1
    except ObjectDoesNotExist as e:
        return render(request, 'alert.html', {'message':"No data found", 'path':'/contacts/admin'})

    if listContacts == []:
        contactDetail = {"id": "-", "name": "-", "phone_number": "-"}
        listContacts.append(contactDetail)
  
  context = {'data': listContacts, 'camera_id': relation.camera_id}
  return render(request, 'new_contacts.html', context)

def ServiceViews(request):
  if request.method == 'GET':
    count = 0
    listServices = []

    if request.session.has_key('token'):
      try: ## Check Login Session
          login = Login.objects.get(token=request.session['token'])
      except ObjectDoesNotExist as e:
          return render(request, 'alert.html', {'message':"No session found. Please login", 'path':'/login/admin'})

      ## Check Token
      if login.login_status != "ON" and login.is_logged_out != 0:
          return render(request, 'alert.html', {'message':"User already logged out", 'path':'/logout/admin'})
    else:
      return render(request, 'alert.html', {'message':"No session found. Please login", 'path':'/login/admin'})

    try:
        relation = CamerasUsersRelation.objects.get(user_id=login.user_id)
    except ObjectDoesNotExist as e:
        return render(request, 'alert.html', {'message':"No data found", 'path':'/services/admin'})

    ## Check camera's emergency services
    try:
        cam = Cameras.objects.get(id=relation.camera_id)
    except ObjectDoesNotExist as e:
        return render(request, 'alert.html', {'message':"No data found", 'path':'/services/admin'})

    try:
        services = EmergencyServices.objects.all()
        datas = EmergencyServices.objects.all().count()
    except ObjectDoesNotExist as e:
        return render(request, 'alert.html', {'message':"No data found", 'path':'/services/admin'})

    try: 
        while (count != datas):
            is_selected = False
            service = EmergencyServices.objects.get(id=services[count].id)
            if service.id == cam.emergency_services_id:
              is_selected = True
            type = ServiceTypes.objects.get(id=service.type_id)
            serviceDetail = {"id": service.id, "name": service.name, "address": service.address, "phone_number": service.phone_number, "type": type.name, "is_selected": is_selected}
            listServices.append(serviceDetail)
            count = count+1
    except ObjectDoesNotExist as e:
        return render(request, 'alert.html', {'message':"No data found", 'path':'/services/admin'})

    if listServices == []:
        contactDetail = {"id": "-", "name": "-", "address": "-", "phone_number": "-", "type": "-"}
        listServices.append(contactDetail)

  listServices.sort(key=lambda x: (x['is_selected']), reverse=True)
  context = {'data': listServices, 'camera_id': relation.camera_id}
  return render(request, 'new_services.html', context)

def EditServiceViews(request, id):
    try:
      if request.GET.get('action') is None:
        return render(request, 'alert.html', {'message':"Required field is empty", 'path':'/services/admin'})
    except KeyError as e:
      return render(request, 'alert.html', {'message':"Required field is empty", 'path':'/services/admin'})

    if request.session.has_key('token'):
      try: ## Check Login Session
          login = Login.objects.get(token=request.session['token'])
      except ObjectDoesNotExist as e:
          return render(request, 'alert.html', {'message':"No session found. Please login", 'path':'/login/admin'})

      ## Check Token
      if login.login_status != "ON" and login.is_logged_out != 0:
          return render(request, 'alert.html', {'message':"User already logged out", 'path':'/logout/admin'})
    else:
      return render(request, 'alert.html', {'message':"No session found. Please login", 'path':'/login/admin'})

    try:
        relation = CamerasUsersRelation.objects.get(user_id=login.user_id)
    except ObjectDoesNotExist as e:
        return render(request, 'alert.html', {'message':"No data found", 'path':'/services/admin'})

    if request.GET.get('action') == "1": 
      try: 
          camera = Cameras.objects.get(id=relation.camera_id)
          camera.emergency_services_id = id
          camera.save()
      except IntegrityError or ObjectDoesNotExist:
          return render(request, 'alert.html', {'message':"No data found", 'path':'/services/admin'})
    else:
      try: 
          service = EmergencyServices.objects.get(id=id)
          service.delete()
      except IntegrityError or ObjectDoesNotExist:
          return render(request, 'alert.html', {'message':"No data found", 'path':'/services/admin'})
    
    return render(request, 'alert.html', {'message':"Emergency services updated", 'path':'/services/admin'})

def DeleteContactViews(request, id):
    if request.session.has_key('token'):
      try: ## Check Login Session
          login = Login.objects.get(token=request.session['token'])
      except ObjectDoesNotExist as e:
          return render(request, 'alert.html', {'message':"No session found. Please login", 'path':'/login/admin'})

      ## Check Token
      if login.login_status != "ON" and login.is_logged_out != 0:
          return render(request, 'alert.html', {'message':"User already logged out", 'path':'/logout/admin'})
    else:
      return render(request, 'alert.html', {'message':"No session found. Please login", 'path':'/login/admin'})

    ## Get Admin Role
    try: 
        adm = Roles.objects.get(name="Admin")
    except ObjectDoesNotExist as e:
        return render(request, 'alert.html', {'message':"No data found", 'path':'/contacts/admin'})
    
    ## Get Account Detail
    try: 
        account = Users.objects.get(id=login.user_id)
    except ObjectDoesNotExist as e:
        return render(request, 'alert.html', {'message':"No data found", 'path':'/contacts/admin'})
      
    if (account.role_id != adm.id):
      return render(request, 'alert.html', {'message':"You're not allowed to access this service", 'path':'/contacts/admin'})

    ## Check Relation
    try:
        camera = CamerasUsersRelation.objects.get(user_id=login.user_id)
        relation = CamerasUsersRelation.objects.get(user_id=id, camera_id=camera.camera_id)
        relation.delete()
    except ObjectDoesNotExist as e:
        return render(request, 'alert.html', {'message':"No data found", 'path':'/contacts/admin'})

    ## Get Camera Detail
    try: 
        cam  = Cameras.objects.get(id=relation.camera_id)
    except ObjectDoesNotExist as e:
        return render(request, 'alert.html', {'message':"No data found", 'path':'/contacts/admin'})

    message = messaging.Message(
        data={
            "push_notif_type": "REMOVE_USER",
            "camera_id": str(cam.id),
            "camera_name": cam.name
        },
        topic="testing",
        android=messaging.AndroidConfig(priority="high"),
    )
    
    messaging.send(message)
    
    return render(request, 'alert.html', {'message':"Emergency contact deleted", 'path':'/contacts/admin'})

def AddServiceViews(request):
  form = ServiceForm()

  if request.session.has_key('token'):
    try: ## Check Login Session
        login = Login.objects.get(token=request.session['token'])
    except ObjectDoesNotExist as e:
        return render(request, 'alert.html', {'message':"No session found. Please login", 'path':'/login/admin'})

    ## Check Token
    if login.login_status != "ON" and login.is_logged_out != 0:
        return render(request, 'alert.html', {'message':"User already logged out", 'path':'/logout/admin'})
  else:
    return render(request, 'alert.html', {'message':"No session found. Please login", 'path':'/login/admin'})

  if request.method == 'POST':
    form = ServiceForm(request.POST)

    try: ## Check if Emergency Services exists
        EmergencyServices.objects.get(address=form['address'].value(), phone_number=form['phone_number'].value())
        return render(request, 'alert.html', {'message':"This emergency services already exists", 'path':'/new-service/admin'})
    except ObjectDoesNotExist as e:
        pass

    body = json.loads('{}')
    body['type'] = form['type'].value()
    body['name'] = form['name'].value()
    body['address'] = form['address'].value()
    body['phone_number'] = form['phone_number'].value()
    body['created_date'] = datetime.datetime.now()
    body['updated_date'] = datetime.datetime.now()
    body['created_by'] = "superadmin"
    body['updated_by'] = "superadmin"

    serializer = ServiceSerializer(data=body)
    if serializer.is_valid():
      serializer.save()
      return render(request, 'alert.html', {'message':"New service added", 'path':'/services/admin'})
    else:
      return render(request, 'alert.html', {'message':"Failed to add new service", 'path':'/services/admin'})
   
  context = {'form': form}
  return render(request, 'new_add_service.html', context)

def LogoutPageViews(request):
  try: ## Check last login session
      list = Login.objects.all().filter(user_id=1)

      if list.count != 0:
          lastLogin = Login.objects.get(id=list.latest('created_date').id)
          lastLogin.login_status = "OFF"
          lastLogin.is_logged_out = True
          lastLogin.save()
  except ObjectDoesNotExist as e:
      return render(request, 'alert.html', {'message':"Failed to logout", 'path':'/dashboard/admin'})

  return redirect("Login")
  