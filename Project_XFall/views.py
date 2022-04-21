import json
import datetime
import requests
from XFall import settings
#import FCMManager as fcm
from django.utils.timezone import localtime
#from datetime import datetime
from django.db import IntegrityError
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Cameras, CamerasUsersRelation, EmergencyServices, Notifications, Roles, Users
from django.core import serializers
from django.core.exceptions import ObjectDoesNotExist
from django.core.serializers.json import Serializer, DjangoJSONEncoder
from firebase_admin import messaging
from firebase_admin.messaging import Message, Notification

import os
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "C:/Users/LAPTOP/XFall/xfall-secretkey.json"

class EmergencyServiceViews(APIView):
    def get(self, request):
        #serializer = TokenVerifySerializer
        #if not serializer.is_valid:
        #    return Response({"Status": "Error", "Data": "User not allowed to access this service."}, status=status.HTTP_400_BAD_REQUEST)
            
        services = EmergencyServices.objects.all()
        count = EmergencyServices.objects.all().count()
        result = serializers.serialize('json', services, fields=('name', 'address', 'phone_number'))
        #user = authenticate(request, username=request.data.get('username'), password=request.data.get('password'))
        
        if count != 0:
          return HttpResponse(result, content_type='application/json', status=status.HTTP_200_OK)
            #return Response({"Status": "Success", "Data": result}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"Status": "Error", "Data": "No emergency services found."}, status=status.HTTP_400_BAD_REQUEST)

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
    def get(self, request):
        body_json = request.body.decode('utf-8')
        body = json.loads(body_json)
        try:
            #relation = CamerasUsersRelation.objects.get(camera_id=body['camera_id'])
            CamerasUsersRelation.objects.all().filter(camera_id=body['camera_id'])
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Data": "No data found."}, status=status.HTTP_400_BAD_REQUEST)
        
        try: ## butuh test kalau listnya banyak
            contacts = Users.objects.all().filter(role_id=2, is_verified=1)
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Data": "No data found."}, status=status.HTTP_400_BAD_REQUEST)

        count = contacts.count()
        #result = serializers.serialize('json', contacts, fields=('username', 'profile_image', 'phone_number'))      
        result = json.dumps( {"Emergency Contacts": [{'username': o.username,
                    'profile_image': str(o.profile_image),
                    'phone_number': o.phone_number } for o in contacts]} )

        if count != 0:
          return HttpResponse(result, content_type='application/json', status=status.HTTP_200_OK) 

        return Response({"Status": "Error", "Data": "No emergency contacts found."}, status=status.HTTP_400_BAD_REQUEST)

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
    def get(self, request):
        body_json = request.body.decode('utf-8')
        body = json.loads(body_json)
        count = 0
        listCam = []

        try:
            list = CamerasUsersRelation.objects.all().filter(user_id=body['user_id'])
            datas = CamerasUsersRelation.objects.all().filter(user_id=body['user_id']).count()
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Data": "No data found."}, status=status.HTTP_400_BAD_REQUEST)
        
        try: 
            while (count != datas):
                cam = list[count].camera
                listCam.append(Cameras.objects.get(id=cam.id))
                count = count+1
            
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Data": "No data found."}, status=status.HTTP_400_BAD_REQUEST)

        result = json.dumps( {"Cameras": [{'camera_id': c.id,
                    'status': str(c.status)} for c in listCam]} )
        
        if count != 0:
          return HttpResponse(result, content_type='application/json', status=status.HTTP_200_OK) 

        return Response({"Status": "Error", "Data": "No cameras found."}, status=status.HTTP_400_BAD_REQUEST)

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


class TriggerViews(APIView):
    def post(self, request):
        # body = {
        #     "cameraId": "01",
        #     "prob": "0.6",
        #     # "img": jstr
        #     # "img": self.im2json(image)
        # }
        
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
            #if stats == "ON" and (int(round(diff.total_seconds()/60, 0))) < 20:
            #    return Response({"Status": "Success, data collected", "Data": body}, status=status.HTTP_200_OK)
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Data": "No data found."}, status=status.HTTP_400_BAD_REQUEST)

        ## Get all emergency contacts
        try:
            CamerasUsersRelation.objects.all().filter(camera_id=body['cameraId'])
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Data": "No data found."}, status=status.HTTP_400_BAD_REQUEST)
        
        try: 
            contacts = Users.objects.all().filter(role_id=2, is_verified=1)
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Data": "No data found."}, status=status.HTTP_400_BAD_REQUEST)

        count = contacts.count()
        #result = serializers.serialize('json', contacts, fields=('username', 'profile_image', 'phone_number'))      

        #allTokens = ["token from android apps"]
        #fcm.pushNotif("Hi", "This is a push message", allTokens, result)

        # headers = {'Content-Type' : 'application/json',
        #         'Authorization' : 'key='+'AAAAWIm99o0:APA91bEcduVdGC8QXGDBOnzukz0JB9LTbh8BNHRJQZ_WpTMa8OF15CK_r8-wHwjYUjoGiG1UYekxriu4sBlWIkjZBJ0Q0VnDpodPtn8zsleJdU4vp2HOF-KuqrlmlrQ_4v3vdHxdCVe5'}
        # response = requests.post('https://fcm.googleapis.com//v1/projects/xfall-fca06/messages:send',#'https://fcm.googleapis.com/fcm/send', 
        #     data = { 'to' : '/topics/XFall',
        #             'notification': {
        #                 'title': 'Pemberitahuan', 
        #                 'body': 'lalala'
        #             }
        #     }, headers=headers)
        
        # print(response.status_code, response.reason)
        # message = messaging.Message(
        #     notification=Data(title="title", body="text", image="url"),
        #     topic="testing-topic",
        # )
        message = messaging.Message(
            data={
                "id": "1",
                "notificationTitle": "Jatuh - Rumah Deka Thomas",
                "notificationBody": "Ada kejadian jatuh di rumah"
            },
            topic="testing-topic",
        )
        resp = messaging.send(message)
        # Response is a message ID string.
        print('Successfully sent message:', resp)
        result = json.dumps( {"Emergency Contacts": [{'username': o.username,
                    'profile_image': str(o.profile_image),
                    'phone_number': o.phone_number } for o in contacts],
                    "Result": str(resp)} )

        if count != 0:
          return HttpResponse(result, content_type='application/json', status=status.HTTP_200_OK) 

        return Response({"Status": "Error", "Data": "No emergency contacts found."}, status=status.HTTP_400_BAD_REQUEST)
