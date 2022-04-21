import json
from datetime import datetime
from operator import index
from django.db import IntegrityError
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import ( 
    AdminTokenObtainPairSerializer, 
    CamerasUsersSerializer, 
    UserSerializer, 
    UserTokenObtainPairSerializer )
from .models import Cameras, CamerasUsersRelation, EmergencyServices, NotificationHistories, Notifications, Roles, Users
from django.contrib.auth.models import User
from rest_framework_simplejwt.views import TokenObtainPairView
from django.core import serializers
from django.core.exceptions import ObjectDoesNotExist


class UserLoginViews(TokenObtainPairView):
    serializer_class = UserTokenObtainPairSerializer

class UserRegisViews(APIView):
    def post (self, request):
      try:
        body_json = request.body.decode('utf-8')
        body = json.loads(body_json)
        
        role = Roles.objects.get(id=2)

        body['role'] = role.id
        body['is_verified'] = False
        body['created_date'] = datetime.now().strftime("%Y-%m-%d")
        body['updated_date'] = datetime.now().strftime("%Y-%m-%d")
        body['created_by'] = "superadmin"
        body['updated_by'] = "superadmin"
        serializer = UserSerializer(data=body)
        if serializer.is_valid():
          User.objects.create_user(
            username=request.data.get('username'), 
            email=request.data.get('email'), 
            password=request.data.get('password'),
            is_superuser="False",
          )
          serializer.save()
        else:
          return Response({"Status": "Error", "Data": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"Status": "Success", "Data": serializer.data}, status=status.HTTP_200_OK)
      except IntegrityError as e:
        account = User.objects.get(username=request.data.get('username'))
        if account is not None:
            return Response({"Status": "Error", "Data": "Username already taken."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"Status": "Error", "Data": "Registration failed."}, status=status.HTTP_400_BAD_REQUEST)


class ResponseViews(APIView):
    def get (self,request):
        # input: user_id and date (date optional, "" if all notif)
        body_json = request.body.decode('utf-8')
        body = json.loads(body_json)
        count = 0 
        count2 = 0
        listCam = []
        listNotif = []
        tempResult = ""

        try:
            list = CamerasUsersRelation.objects.all().filter(user_id=body['user_id'])
            datas = CamerasUsersRelation.objects.all().filter(user_id=body['user_id']).count()
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Data": "No data found."}, status=status.HTTP_400_BAD_REQUEST)
        
        try: 
            while (count != datas):
                if count != 0:
                  tempResult = tempResult + ", "
                cam = list[count].camera
                camera = Cameras.objects.get(id=cam.id)
                listCam.append(camera)
                try:
                    list2 = Notifications.objects.all().filter(camera_id=cam.id)
                    notifDatas = Notifications.objects.all().filter(camera_id=cam.id).count()
                except ObjectDoesNotExist as e:
                    return Response({"Status": "Error", "Data": "No data found."}, status=status.HTTP_400_BAD_REQUEST)
                while (count2 != notifDatas):
                    try:
                        notif = list2[count2].id
                        if body['date'] == "":
                            listNotif.append(NotificationHistories.objects.get(notification_id=notif, created_date=body['date']))
                    except:
                        listNotif.append(NotificationHistories.objects.get(notification_id=list2[count2].id, created_date=body['date']))
                    count2 = count2+1
                
                tempResult = tempResult + json.dumps( {'camera_id': camera.id,
                    'notification_histories': [{'response': str(n.response)} for n in listNotif]} )
                count = count+1
            
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Data": "No data found."}, status=status.HTTP_400_BAD_REQUEST)
        
        if count != 0:
          result = "{ \"Notifications:\" [" + tempResult + "]\n}"
          return HttpResponse(result, content_type='application/json', status=status.HTTP_200_OK) 

        return Response({"Status": "Error", "Data": "No cameras found."}, status=status.HTTP_400_BAD_REQUEST)

    def post (self,request):
        # input: camera_id, user_id and response
        body_json = request.body.decode('utf-8')
        body = json.loads(body_json)
        count = 0 
        count2 = 0
        listCam = []
        listNotif = []
        tempResult = ""

        try:
            list = CamerasUsersRelation.objects.all().filter(user_id=body['user_id'])
            datas = CamerasUsersRelation.objects.all().filter(user_id=body['user_id']).count()
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Data": "No data found."}, status=status.HTTP_400_BAD_REQUEST)
        
        try: 
            while (count != datas):
                if count != 0:
                  tempResult = tempResult + ", "
                cam = list[count].camera
                camera = Cameras.objects.get(id=cam.id)
                listCam.append(camera)
                try:
                    list2 = Notifications.objects.all().filter(camera_id=cam.id)
                    notifDatas = Notifications.objects.all().filter(camera_id=cam.id).count()
                except ObjectDoesNotExist as e:
                    return Response({"Status": "Error", "Data": "No data found."}, status=status.HTTP_400_BAD_REQUEST)
                while (count2 != notifDatas):
                    notif = list2[count2]
                    listNotif.append(NotificationHistories.objects.get(id=notif.id))
                    count2 = count2+1
                
                tempResult = tempResult + json.dumps( {'camera_id': camera.id,
                    'notification_histories': [{'response': str(n.response)} for n in listNotif]} )
                count = count+1
            
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Data": "No data found."}, status=status.HTTP_400_BAD_REQUEST)
        
        if count != 0:
          result = "{ \"Notifications:\" [" + tempResult + "]\n}"
          return HttpResponse(result, content_type='application/json', status=status.HTTP_200_OK) 

        return Response({"Status": "Error", "Data": "No cameras found."}, status=status.HTTP_400_BAD_REQUEST)

