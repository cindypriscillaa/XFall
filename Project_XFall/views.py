import json
import datetime
import base64
from django.db import IntegrityError
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Cameras, CamerasUsersRelation, EmergencyServices, Notifications, Roles, Users
from django.core.exceptions import ObjectDoesNotExist
from firebase_admin import messaging
from firebase_admin.messaging import Message
from django.core.files.base import ContentFile 

import os
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "C:/Users/LAPTOP/XFall/xfall-secretkey.json"

class NotifyFallViews(APIView):
    def post(self, request):
        body_json = request.body.decode('utf-8')
        body = json.loads(body_json)
        count = 0
        list = []

        if float(body['prob']) < 0.5:
            return Response({"Status": "Success", "Messages": {"English": "No fall detected.", "Indonesia": "Tidak ada jatuh yang terdeteksi."}, "Data": body}, status=status.HTTP_200_OK)

        now = datetime.datetime.now()
        adm = Roles.objects.get(name="Admin")

        ## Get Camera Detail
        try: 
            cam = Cameras.objects.get(id=body['camera_id'])
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)

        ## Check Relation and Admin ID
        try:
            list = CamerasUsersRelation.objects.all().filter(camera_id=body['camera_id'])
            datas = CamerasUsersRelation.objects.all().filter(camera_id=body['camera_id']).count()
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)
        
        try: 
            while (count != datas):
                user = Users.objects.get(id=list[count].user_id)
                if user.role_id == adm.id:
                    adminID = user.id
                count = count+1
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)
        
        ## Get Admin Detail
        try: 
            admin = Users.objects.get(id=adminID, is_verified=1)
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)
        
        ## Save Notification and Screen Capture Image
        imgName = '{}{}{}'.format(admin.username, "_", now.strftime('%y%m%d%H%M%S'))
        format, imgstr = body['img'].split(';base64,') 
        ext = format.split('/')[-1] 
        try:
            data = ContentFile(base64.b64decode(imgstr), name=imgName + "." + ext)
            notif = Notifications(status="ON", created_date = now, updated_date = now, 
                created_by = "superadmin", updated_by = "superadmin", camera_id=cam.id, fall_image=data)  
            notif.save()
        except:
            return Response({"Status": "Error", "Messages": {"English": "Failed to save notification.", "Indonesia": "Gagal dalam menyimpan notifikasi."}}, status=status.HTTP_400_BAD_REQUEST)

        ## Check data fall 20 menit sebelumnya
        try:
            list = Notifications.objects.all().filter(camera=body['cameraId'])
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)

        try: 
            stats = list.latest('created_date').status
            date = list.latest('created_date').created_date
            
            lastDate = date.replace(tzinfo=None)
            diff = now - lastDate 
            
            if stats == "ON" and (int(round(diff.total_seconds()/60, 0))) < 20:
                return Response({"Status": "Success", "Messages": {"English": "Fall detected (same event as previous notification).", "Indonesia": "Terdeteksi jatuh (kejadian yang sama dengan notifikasi yang lalu)."}, "Data": body}, status=status.HTTP_200_OK)
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)

        user = Roles.objects.get(name="User")

        ## Get All Emergency Contacts
        try:
            CamerasUsersRelation.objects.all().filter(camera_id=body['camera_id'])
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)

        try: 
            contacts = Users.objects.all().filter(role_id=user.id, is_verified=1)
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)
        count = contacts.count()

        ## Get Emergency Services Detail
        try: 
            services = EmergencyServices.objects.get(id=cam.emergency_services_id)
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)

        message = messaging.Message(
            data={
                "push_notif_type": "FALL",
                "notification_id": str(notif.id),
                "notification_title": "Jatuh - Rumah " + str(cam.name),
                "notification_body": "Ada kejadian jatuh di rumah",
                "camera_id": body['camera_id'],
                "camera_name": cam.name,
                "camera_image": str(notif.fall_image),
                "home_number": str(admin.phone_number),
                "service_number": str(services.phone_number)
            },
            topic="testing",
            android=messaging.AndroidConfig(priority="high"),
        )
        
        messaging.send(message)

        result = json.dumps( {"Messages" : {"English": "Successfully send notification to emergency contacts.", "Indonesia": "Berhasil mengirim notifikasi kepada kontak darurat."}, 
                    "Emergency_Contacts": [{'username': o.username,
                    'profile_image': str(o.profile_image),
                    'phone_number': o.phone_number } for o in contacts]}) ## TO-DO: LOGGING

        if count != 0:
          return HttpResponse(result, content_type='application/json', status=status.HTTP_200_OK) 

        return Response({"Status": "Error", "Messages": {"English": "No emergency contacts found.", "Indonesia": "Data kontak darurat tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)

class TestSaveImage(APIView):
    def get(self, request):
        image = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAMgAAADIBAMAAABfdrOtAAAACXBIWXMAAA7DAAAOwwHHb6hkAAAAD1BMVEVHcEwAAAAAAAAAAAAAAADTrAj/AAAABXRSTlMA/7x4OWjJfMIAAANTSURBVHja7VrbcaswEE1ADYAoAAEFAKYAwPRf0/WNxzbEIO0LTSbZ82kDZx9nhbTLx4dCoVAoFAqFQqFQSGO5XvrqMiwnUlz77I68Hk6iMA+KL9TjKW64bIN8OJ/jDJZrtgNhltTtkeStaM53OW4sktnvsgNYOY45O0RzdrBEA+ZxRMwVszW9qraOybgyrRjqZbxh6Vc8hbAj1XP1XSpZV+bdNXG1WjaS0qq3f/SCAksP6+5ZoaVYsb/b+/TRiqV9J/KJVOoTn7WdULwez2l9+bIy2rLeOmXqK/U5Evwbt6TYQDQLiZSUAV1YiZSMIYWP/JTYoKstv0pKzhXQvLdBXwt23nPfJY6decATAHaAVscG8E4bueIqAde0XJIR4G3JVHBg+XNMkgmSVMfU8ASRZydCUghYwjVShqSBbP5yJkkJkaBlriogklxJfhCJjLqKc9XV/ZqKj7hAnrzUJ3AS7pvx5NcvZJPA3khAtkQJe8cN2NxN3M0dfJvKIQlvuA3/FBTl6BDlEBQ8rUkc56AHU07eIx2xE1izgNdcgbU9uG0ibwPHCDW8orSink219jgj/H5qjPbgqwdYH9ELNDpfLdtm92wtMxN4ddHrXQ6RPnq6N/ZbjwMFHPk+EPj/y3Jx0sOgdDPJqG44YbSxduW8qVaUcVOUwVmcEeCxK4KOXI/DNUTgEPMlzbwQ8SV1fhKJUbYJcIiUSp8FYcXF+7Z28ZO/DVZeD/ex7LV3ggHrNhSrZ5kNjZVSr/1m7rLOFkdhzvcxzPrtyNhxJ4HczgK5X2W9CWmPnPskbOfMdeXliAXUas50xBeKlyUlr0ZakMotq0Ya4MJDqZUJqJtnwApG2gdo7ggqTuChph+4EHeSZ/+BY+++QSMxWqX4xe/aAibTkeL1iBZwRZpJ+kpxUTakepyR/pMaOR0yk5RvJdC9MkpzLUUb1uFFPKHfdgn+/YhvX+Jbt4bQUXbYSjEEQU5Y5ykdZfQ9E6F+0d6TPhPBfsBC+uAFaZkhzcImnLxoYyrkSIg2pjK4u2hjKqT/n7QdNC6TxGkubj7b0UhwthFHxjgS4jQX9x1DDBJDPG6kGOX/aBJDIBmJJK2820piqi/gz7L3+zhdKYVCoVAoFAqFQvGX8Q8dFNioansTYQAAAABJRU5ErkJggg=='
        imgName = '{}{}'.format("_", datetime.datetime.now().strftime('%y%m%d%H%M%S'))
        format, imgstr = image.split(';base64,') 
        ext = format.split('/')[-1] 
        try:
            data = ContentFile(base64.b64decode(imgstr), name=imgName + "." + ext)
            cam = Cameras.objects.get(id=2)
            notif = Notifications(status="ON", created_date = datetime.datetime.now(),
                updated_date = datetime.datetime.now(), created_by = "superadmin", updated_by = "superadmin", camera_id=cam.id, fall_image=data)  
            notif.save()
        except:
            return Response({"Status": "Error", "Messages": "Failed to upload image."}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"Status": "Success", "Messages": notif}, status=status.HTTP_200_OK)