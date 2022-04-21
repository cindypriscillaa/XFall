import json
from datetime import datetime
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
from .models import Cameras, CamerasUsersRelation, EmergencyServices, Roles, Users
from django.contrib.auth.models import User
from rest_framework_simplejwt.views import TokenObtainPairView
from django.core import serializers
from django.core.exceptions import ObjectDoesNotExist


class AdminLoginViews(TokenObtainPairView):
    serializer_class = AdminTokenObtainPairSerializer

class AdminRegisViews(APIView):
    def post(self, request):
      try:
        body_json = request.body.decode('utf-8')
        body = json.loads(body_json)
        cam = Cameras(created_date = datetime.now().strftime("%Y-%m-%d"),
            updated_date = datetime.now().strftime("%Y-%m-%d"), created_by = "superadmin", updated_by = "superadmin")
        cam.save()
        
        role = Roles.objects.get(id=1)

        body['camera'] = cam.id
        body['role'] = role.id
        body['is_verified'] = False
        body['created_date'] = datetime.now().strftime("%Y-%m-%d")
        body['updated_date'] = datetime.now().strftime("%Y-%m-%d")
        body['created_by'] = "superadmin"
        body['updated_by'] = "superadmin"
        serializer = UserSerializer(data=body)
        if serializer.is_valid():
          serializer.save()
          user = User.objects.create_user(
            username=request.data.get('username'), 
            email=request.data.get('email'), 
            password=request.data.get('password'),
            is_superuser="True",
          )
          us = Users.objects.get(username=body['username'])
          userCamID = '{"camera": "' + str(cam.id) + '", "user": "' + str(us.id) + '"}'
          dict_userCamID = json.loads(userCamID)
          userCam = CamerasUsersSerializer(data=dict_userCamID) 
          if userCam.is_valid():
              userCam.save()
        else:
          cam.delete()
          return Response({"Status": "Error", "Data": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"Status": "Success", "Data": serializer.data}, status=status.HTTP_200_OK)
      except IntegrityError as e:
        cam.delete()
        try:
            account = User.objects.get(username=request.data.get('username'))
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Data": "Registration failed."}, status=status.HTTP_400_BAD_REQUEST)
        
        if account is not None:
          return Response({"Status": "Error", "Data": "Username already taken."}, status=status.HTTP_400_BAD_REQUEST)