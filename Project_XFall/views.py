import json
import random
import datetime
from subprocess import HIGH_PRIORITY_CLASS
from django.db import IntegrityError
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Cameras, CamerasUsersRelation, EmergencyServices, Notifications, Roles, Users
from django.core import serializers
from django.core.exceptions import ObjectDoesNotExist
from firebase_admin import messaging
from firebase_admin.messaging import Message, Notification

import os
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "C:/Users/LAPTOP/XFall/xfall-secretkey.json"

class EmergencyServiceViews(APIView):
    # def get(self, request):
    #     #serializer = TokenVerifySerializer
    #     #if not serializer.is_valid:
    #     #    return Response({"Status": "Error", "Data": "User not allowed to access this service."}, status=status.HTTP_400_BAD_REQUEST)
            
    #     services = EmergencyServices.objects.all()
    #     count = EmergencyServices.objects.all().count()
    #     result = serializers.serialize('json', services, fields=('name', 'address', 'phone_number'))
    #     #user = authenticate(request, username=request.data.get('username'), password=request.data.get('password'))
        
    #     if count != 0:
    #       return HttpResponse(result, content_type='application/json', status=status.HTTP_200_OK)
    #         #return Response({"Status": "Success", "Data": result}, status=status.HTTP_400_BAD_REQUEST)
    #     return Response({"Status": "Error", "Data": "No emergency services found."}, status=status.HTTP_400_BAD_REQUEST)

    def put (self,request):
        body_json = request.body.decode('utf-8')
        body = json.loads(body_json)

        try: ## hanya admin yang dapat melakukan update emergency services pada user_id
            account = Users.objects.get(id=body['user_id'])
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Data": "No data found."}, status=status.HTTP_400_BAD_REQUEST)
          
        if (account.role_id != 1):
            return Response({"Status": "Error", "Data": "You're not allowed to access this service."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            relation = CamerasUsersRelation.objects.get(user_id=body['user_id'])
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Data": "No data found."}, status=status.HTTP_400_BAD_REQUEST)
            
        try: ## yang terupdate pasti hanya 1 camera_id
            camera = Cameras.objects.get(id=relation.camera_id)
            camera.emergency_services_id = body['emergency_services_id']
            camera.save()
        except IntegrityError or ObjectDoesNotExist:
            return Response({"Status": "Error", "Data": "No data found."}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({"Status": "Success, data updated.", "Data": body}, status=status.HTTP_200_OK)

class EmergencyContactViews(APIView):
    # def get(self, request):
    #     body_json = request.body.decode('utf-8')
    #     body = json.loads(body_json)
    #     try:
    #         #relation = CamerasUsersRelation.objects.get(camera_id=body['camera_id'])
    #         CamerasUsersRelation.objects.all().filter(camera_id=body['camera_id'])
    #     except ObjectDoesNotExist as e:
    #         return Response({"Status": "Error", "Data": "No data found."}, status=status.HTTP_400_BAD_REQUEST)
        
    #     try: ## butuh test kalau listnya banyak
    #         contacts = Users.objects.all().filter(role_id=2, is_verified=1)
    #     except ObjectDoesNotExist as e:
    #         return Response({"Status": "Error", "Data": "No data found."}, status=status.HTTP_400_BAD_REQUEST)

    #     count = contacts.count()
    #     #result = serializers.serialize('json', contacts, fields=('username', 'profile_image', 'phone_number'))      
    #     result = json.dumps( {"Emergency Contacts": [{'username': o.username,
    #                 'profile_image': str(o.profile_image),
    #                 'phone_number': o.phone_number } for o in contacts]} )

    #     if count != 0:
    #       return HttpResponse(result, content_type='application/json', status=status.HTTP_200_OK) 

    #     return Response({"Status": "Error", "Data": "No emergency contacts found."}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        body_json = request.body.decode('utf-8')
        body = json.loads(body_json)

        try: ## hanya admin yang dapat melakukan delete emergency contacts
            account = Users.objects.get(id=body['admin_id'])
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Data": "No data found."}, status=status.HTTP_400_BAD_REQUEST)
          
        if (account.role_id != 1):
            return Response({"Status": "Error", "Data": "You're not allowed to access this service."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            relation = CamerasUsersRelation.objects.get(user_id=body['admin_id'], camera_id=body['camera_id'])
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Data": "You're not allowed to delete this data."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            relation = CamerasUsersRelation.objects.get(user_id=body['user_id'], camera_id=body['camera_id'])
            relation.delete()
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Data": "No data found."}, status=status.HTTP_400_BAD_REQUEST)
            
        return Response({"Status": "Success, data deleted.", "Data": body}, status=status.HTTP_200_OK)

class CameraViews(APIView):
    # def get(self, request):
    #     body_json = request.body.decode('utf-8')
    #     body = json.loads(body_json)
    #     count = 0
    #     listCam = []

    #     try:
    #         list = CamerasUsersRelation.objects.all().filter(user_id=body['user_id'])
    #         datas = CamerasUsersRelation.objects.all().filter(user_id=body['user_id']).count()
    #     except ObjectDoesNotExist as e:
    #         return Response({"Status": "Error", "Data": "No data found."}, status=status.HTTP_400_BAD_REQUEST)
        
    #     try: 
    #         while (count != datas):
    #             cam = list[count].camera
    #             listCam.append(Cameras.objects.get(id=cam.id))
    #             count = count+1
            
    #     except ObjectDoesNotExist as e:
    #         return Response({"Status": "Error", "Data": "No data found."}, status=status.HTTP_400_BAD_REQUEST)

    #     result = json.dumps( {"Cameras": [{'camera_id': c.id,
    #                 'status': str(c.status)} for c in listCam]} )
        
    #     if count != 0:
    #       return HttpResponse(result, content_type='application/json', status=status.HTTP_200_OK) 

    #     return Response({"Status": "Error", "Data": "No cameras found."}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request): ## Service Admin
        body_json = request.body.decode('utf-8')
        body = json.loads(body_json)

        try: ## hanya admin yang dapat melakukan delete emergency contacts
            account = Users.objects.get(id=body['admin_id'])
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Data": "No data found."}, status=status.HTTP_400_BAD_REQUEST)
          
        if (account.role_id != 1):
            return Response({"Status": "Error", "Data": "You're not allowed to access this service."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            relation = CamerasUsersRelation.objects.get(user_id=body['admin_id'], camera_id=body['camera_id'])
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Data": "You're not allowed to delete this data."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            relation = CamerasUsersRelation.objects.get(user_id=body['user_id'], camera_id=body['camera_id'])
            relation.delete()
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Data": "No data found."}, status=status.HTTP_400_BAD_REQUEST)
            
        return Response({"Status": "Success, data deleted.", "Data": body}, status=status.HTTP_200_OK)

class TriggerViews(APIView):
    def post(self, request):
        # body = {
        #     "cameraId": "01",
        #     "prob": "0.6",
        #     # "img": jstr
        #     # "img": self.im2json(image)
        # }
        
        # return HttpResponse(request.body, content_type='application/json', status=status.HTTP_200_OK) 

        body_json = request.body.decode('utf-8')
        body = json.loads(body_json)
        count = 0
        list = []

        if float(body['prob']) < 0.5:
            return Response({"Status": "Success, data collected", "Data": body}, status=status.HTTP_200_OK)

        now = datetime.datetime.now()

        try: 
            cam = Cameras.objects.get(id=body['cameraId'])
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Data": "No data found."}, status=status.HTTP_400_BAD_REQUEST)
        
        notif = Notifications(camera = cam, status = "ON", created_date = now,
            updated_date = now, created_by = "superadmin", updated_by = "superadmin")
        notif.save()

        ## Check data fall 20 menit sebelumnya
        try:
            list = Notifications.objects.all().filter(camera=body['cameraId'])
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Data": "No data found."}, status=status.HTTP_400_BAD_REQUEST)

        try: 
            stats = list.latest('created_date').status
            date = list.latest('created_date').created_date
            
            lastDate = date.replace(tzinfo=None)
            diff = now - lastDate 
            #return Response({"Status": "Success, data collected", "Data": str(now) + ", "+ str(lastDate) + ", " + str(diff)}, status=status.HTTP_200_OK)
            if stats == "ON" and (int(round(diff.total_seconds()/60, 0))) < 20:
                return Response({"Status": "Success, data collected", "Data": body}, status=status.HTTP_200_OK)
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Data": "No data found."}, status=status.HTTP_400_BAD_REQUEST)

        adm = Roles.objects.get(name="Admin")
        user = Roles.objects.get(name="User")

        ## Get All Emergency Contacts
        try:
            CamerasUsersRelation.objects.all().filter(camera_id=body['cameraId'])
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Data": "No data found."}, status=status.HTTP_400_BAD_REQUEST)

        try: 
            contacts = Users.objects.all().filter(role_id=user.id, is_verified=1)
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Data": "No data found."}, status=status.HTTP_400_BAD_REQUEST)
        count = contacts.count()

        ## Get Admin Detail
        try: 
            admin = Users.objects.get(role_id=adm.id, is_verified=1)
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Data": "No data found."}, status=status.HTTP_400_BAD_REQUEST)

        ## Get Emergency Services Detail
        try: 
            services = EmergencyServices.objects.get(id=cam.emergency_services_id)
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Data": "No data found."}, status=status.HTTP_400_BAD_REQUEST)

        ## Save Screen Capture Image
        imgName = '{}{}'.format(datetime.now().strftime('%y%m%d'), random.randint(10, 99))
        try:
            with open(str(admin.id) + imgName + ".jpg", "wb") as fh:
                fh.write(body['img'].decode('base64'))
        except:
            return Response({"Status": "Error", "Data": "Failed to upload image."}, status=status.HTTP_400_BAD_REQUEST)

        message = messaging.Message(
            data={
                "notificationTitle": "Jatuh - Rumah " + str(cam.name),
                "notificationBody": "Ada kejadian jatuh di rumah",
                "cameraId": body['cameraId'],
                "cameraName": cam.name,
                "cameraImage": body['img'],
                "homeNumber": admin.phone_number,
                "serviceNumber": services.phone_number
            },
            topic="testing-topic",
            android=messaging.AndroidConfig(priority="High"),
        )
        
        resp = messaging.send(message)

        result = json.dumps( {"Successfully sent message to:": [{'username': o.username,
                    'profile_image': str(o.profile_image),
                    'phone_number': o.phone_number } for o in contacts]} )
                    #"Result": str(resp)} )

        if count != 0:
          return HttpResponse(result, content_type='application/json', status=status.HTTP_200_OK) 

        return Response({"Status": "Error", "Data": "No emergency contacts found."}, status=status.HTTP_400_BAD_REQUEST)
