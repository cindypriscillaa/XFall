import json
import datetime
from django.db import IntegrityError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import ( 
    ActionSerializer,
    CamerasUsersSerializer,
    MessageSerializer, 
    UserSerializer, )
from .models import Cameras, CamerasUsersRelation, Actions, EmergencyServices, Login, MessageRecipients, Messages, Notifications, Roles, UserVerificationLogs, Users
from django.core.exceptions import ObjectDoesNotExist
from cryptography.fernet import Fernet
from firebase_admin import messaging
from firebase_admin.messaging import Message

import os
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "C:/Users/LAPTOP/XFall/xfall-secretkey.json"

# class UserLoginViews(TokenObtainPairView):
#     serializer_class = UserTokenObtainPairSerializer

def encrypt(key,plaintext):
    fernet = Fernet(key)
    enc_message = fernet.encrypt(plaintext.encode())
    return enc_message

def decrypt(key,ciphertext):
    fernet = Fernet(key)
    dec_message = fernet.decrypt(ciphertext).decode()
    return dec_message

class FernetGenerated:
    key = Fernet.generate_key()

class UserLoginViews(APIView):
    def post (self, request):
      try:
        body_json = request.body.decode('utf-8')
        body = json.loads(body_json)
        isNone = False

        try:
          if body['email_or_username'] is None or body['password'] is None:
            return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
          return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)

        try:
          user = Users.objects.get(username=body['email_or_username'])
        except ObjectDoesNotExist as e:
          isNone = True

        if isNone is True:
            isNone = False
            try:
                user = Users.objects.get(email=body['email_or_username'])
            except ObjectDoesNotExist as e:
                isNone = True            
        
        if isNone is True:
            return Response({"Status": "Error", "Messages": {"English": "User doesn't exists.", "Indonesia": "Pengguna tidak terdaftar."}}, status=status.HTTP_400_BAD_REQUEST)

        data = {"user_id": user.id, "full_name": user.full_name, "username": user.username, "email": user.email, "phone_number": user.phone_number, "profile_image": user.profile_image}

        if user.is_verified == 0:
            return Response({"Status": "Error", "Messages": {"English": "User is not verified.", "Indonesia": "User belum terverifikasi."}, "User": data}, status=status.HTTP_403_FORBIDDEN)

        ## Check user role
        role = Roles.objects.get(name="User")
        if user.role_id != role.id:
            return Response({"Status": "Error", "Messages": {"English": "User doesn't exists.", "Indonesia": "Pengguna tidak terdaftar."}}, status=status.HTTP_400_BAD_REQUEST)
        
        fernetToken = bytes(user.password, 'utf-16')
        if decrypt(FernetGenerated.key, fernetToken) != body['password']:
            return Response({"Status": "Error", "Messages": {"English": "Login failed.", "Indonesia": "Login gagal."}}, status=status.HTTP_400_BAD_REQUEST)

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
        
        return Response({"Status": "Success", "Messages": {"English": "Login successful!", "Indonesia": "Login berhasil!"}, "Token": str(loginSession.token), "User": data}, status=status.HTTP_200_OK)
      except IntegrityError as e:
        
        return Response({"Status": "Error", "Messages": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class UserLogoutViews(APIView):
    def post (self, request):
      try:
        body_json = request.body.decode('utf-8')
        body = json.loads(body_json)

        try:
          if request.headers.get('XFALL-AUTHORIZATION') is None:
            return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
          return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)

        try: ## Check Login Session
            login = Login.objects.get(token=request.headers.get('XFALL-AUTHORIZATION'))
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)

        ## Check Token
        if login.login_status != "ON" and login.is_logged_out != 0:
          return Response({"Status": "Error", "Messages": {"English": "User already logged out.", "Indonesia": "Pengguna sudah log out."}}, status=status.HTTP_400_BAD_REQUEST)

        ## Update Data for Logout
        login.login_status = "OFF"
        login.is_logged_out = True
        login.save()
        
        return Response({"Status": "Success", "Messages": {"English": "Logout successful!", "Indonesia": "Logout berhasil!"}}, status=status.HTTP_200_OK)
      except IntegrityError as e:
        
        return Response({"Status": "Error", "Messages": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class UserRegisViews(APIView):
    def post(self, request):
      try:
        body_json = request.body.decode('utf-8')
        body = json.loads(body_json)
        
        try:
          if body['full_name'] is None or body['email'] is None:
            return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)
          if body['username'] is None or body['password'] is None:
            return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)
          if body['password_confirmation'] is None or body['phone_number'] is None:
            return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
          return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)
        
        if body['password'] != body['password_confirmation']:
          return Response({"Status": "Error", "Messages": {"English": "Password and confirm password does not match.", "Indonesia": "Kata sandi dan konfirmasi kata sandi tidak cocok."}}, status=status.HTTP_400_BAD_REQUEST)

        role = Roles.objects.get(name="User")

        body['password'] = (encrypt(FernetGenerated.key, body['password'])).decode('utf-16')
        body['role'] = role.id
        body['profile_image'] = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAMgAAADIBAMAAABfdrOtAAAACXBIWXMAAA7DAAAOwwHHb6hkAAAAD1BMVEVHcEwAAAAAAAAAAAAAAADTrAj/AAAABXRSTlMA/7x4OWjJfMIAAANTSURBVHja7VrbcaswEE1ADYAoAAEFAKYAwPRf0/WNxzbEIO0LTSbZ82kDZx9nhbTLx4dCoVAoFAqFQqFQSGO5XvrqMiwnUlz77I68Hk6iMA+KL9TjKW64bIN8OJ/jDJZrtgNhltTtkeStaM53OW4sktnvsgNYOY45O0RzdrBEA+ZxRMwVszW9qraOybgyrRjqZbxh6Vc8hbAj1XP1XSpZV+bdNXG1WjaS0qq3f/SCAksP6+5ZoaVYsb/b+/TRiqV9J/KJVOoTn7WdULwez2l9+bIy2rLeOmXqK/U5Evwbt6TYQDQLiZSUAV1YiZSMIYWP/JTYoKstv0pKzhXQvLdBXwt23nPfJY6decATAHaAVscG8E4bueIqAde0XJIR4G3JVHBg+XNMkgmSVMfU8ASRZydCUghYwjVShqSBbP5yJkkJkaBlriogklxJfhCJjLqKc9XV/ZqKj7hAnrzUJ3AS7pvx5NcvZJPA3khAtkQJe8cN2NxN3M0dfJvKIQlvuA3/FBTl6BDlEBQ8rUkc56AHU07eIx2xE1izgNdcgbU9uG0ibwPHCDW8orSink219jgj/H5qjPbgqwdYH9ELNDpfLdtm92wtMxN4ddHrXQ6RPnq6N/ZbjwMFHPk+EPj/y3Jx0sOgdDPJqG44YbSxduW8qVaUcVOUwVmcEeCxK4KOXI/DNUTgEPMlzbwQ8SV1fhKJUbYJcIiUSp8FYcXF+7Z28ZO/DVZeD/ex7LV3ggHrNhSrZ5kNjZVSr/1m7rLOFkdhzvcxzPrtyNhxJ4HczgK5X2W9CWmPnPskbOfMdeXliAXUas50xBeKlyUlr0ZakMotq0Ya4MJDqZUJqJtnwApG2gdo7ggqTuChph+4EHeSZ/+BY+++QSMxWqX4xe/aAibTkeL1iBZwRZpJ+kpxUTakepyR/pMaOR0yk5RvJdC9MkpzLUUb1uFFPKHfdgn+/YhvX+Jbt4bQUXbYSjEEQU5Y5ykdZfQ9E6F+0d6TPhPBfsBC+uAFaZkhzcImnLxoYyrkSIg2pjK4u2hjKqT/n7QdNC6TxGkubj7b0UhwthFHxjgS4jQX9x1DDBJDPG6kGOX/aBJDIBmJJK2820piqi/gz7L3+zhdKYVCoVAoFAqFQvGX8Q8dFNioansTYQAAAABJRU5ErkJggg=='
        body['is_verified'] = False
        body['created_date'] = datetime.datetime.now()
        body['updated_date'] = datetime.datetime.now()
        body['created_by'] = "superadmin"
        body['updated_by'] = "superadmin"
        serializer = UserSerializer(data=body)
        if serializer.is_valid():
          serializer.save()
        else:
          return Response({"Status": "Error", "Messages": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = Users.objects.get(email=body['email'], username=body['username'])
        except ObjectDoesNotExist as e:
            pass

        return Response({"Status": "Success", "Messages": {"English": "Registration successful!", "Indonesia": "Registrasi berhasil!"}, "User_ID": user.id}, status=status.HTTP_200_OK)
      except IntegrityError as e:
        if str(e).find("UNIQUE constraint failed") is not None:
          return Response({"Status": "Error", "Messages": {"English": "User already exists.", "Indonesia": "Pengguna sudah terdaftar."}}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({"Status": "Error", "Messages": {"English": "Registration failed.", "Indonesia": "Registrasi gagal."}}, status=status.HTTP_400_BAD_REQUEST)

class UserPasswordViews(APIView):
    def post (self, request): ## Forgot Password
      try:
        body_json = request.body.decode('utf-8')
        body = json.loads(body_json)

        try:
          if request.headers.get('XFALL-AUTHORIZATION') is None:
            return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)
          if body['email'] is None:
            return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)
          if body['password'] is None:
            return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)
          if body['password_confirmation'] is None:
            return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
          return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)
        
        if body['password'] != body['password_confirmation']:
          return Response({"Status": "Error", "Messages": {"English": "Password and confirm password does not match.", "Indonesia": "Kata sandi dan konfirmasi kata sandi tidak cocok."}}, status=status.HTTP_400_BAD_REQUEST)

        try: ## hanya cek ke user dengan role_id user
            account = Users.objects.get(email=body['email'], is_verified=1)
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)
          
        if (account.role_id != 2):
            return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)
        
        try: ## Check Login Session
            login = Login.objects.get(token=request.headers.get('XFALL-AUTHORIZATION'))
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)

        ## Check Token
        if login.login_status != "ON" and login.is_logged_out != 0:
          return Response({"Status": "Error", "Messages": {"English": "You're not allowed to access this service.", "Indonesia": "Anda tidak berhak mengakses layanan ini."}}, status=status.HTTP_400_BAD_REQUEST)

        account.password = (encrypt(FernetGenerated.key, body['password'])).decode('utf-16')
        account.updated_date = datetime.datetime.now()
        account.save()

        return Response({"Status": "Success", "Messages": {"English": "Password changed successfully!", "Indonesia": "Kata sandi berhasil diubah!"}}, status=status.HTTP_200_OK)
      except IntegrityError as e:
        return Response({"Status": "Error", "Messages": {"English": "Failed to change password.", "Indonesia": "Gagal mengubah kata sandi."}}, status=status.HTTP_400_BAD_REQUEST)

    def put (self, request): ## Change Password
      try:
        body_json = request.body.decode('utf-8')
        body = json.loads(body_json)

        try:
          if request.headers.get('XFALL-AUTHORIZATION') is None:
            return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)
          if body['old_password'] is None:
            return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)
          if body['new_password'] is None:
            return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)
          if body['password_confirmation'] is None:
            return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
          return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)
        
        if body['new_password'] != body['password_confirmation']:
          return Response({"Status": "Error", "Messages": {"English": "Password and confirm password does not match.", "Indonesia": "Kata sandi dan konfirmasi kata sandi tidak cocok."}}, status=status.HTTP_400_BAD_REQUEST)

        try: ## Check Login Session
            login = Login.objects.get(token=request.headers.get('XFALL-AUTHORIZATION'))
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)

        ## Check Token
        if login.login_status != "ON" and login.is_logged_out != 0:
          return Response({"Status": "Error", "Messages": {"English": "You're not allowed to access this service.", "Indonesia": "Anda tidak berhak mengakses layanan ini."}}, status=status.HTTP_400_BAD_REQUEST)

        try: ## Check Role
            account = Users.objects.get(id=login.user_id, is_verified=1)
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)
          
        if (account.role_id != 2):
            return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)

        ## Check Old Password
        fernetToken = bytes(account.password, 'utf-16') 
        if decrypt(FernetGenerated.key, fernetToken) != body['old_password']: 
            return Response({"Status": "Error", "Messages": {"English": "Old password invalid.", "Indonesia": "Password lama tidak sesuai"}}, status=status.HTTP_400_BAD_REQUEST)
        
        account.password = (encrypt(FernetGenerated.key, body['new_password'])).decode()
        account.updated_date = datetime.datetime.now()
        account.save()

        return Response({"Status": "Success", "Messages": {"English": "Password changed successfully!", "Indonesia": "Kata sandi berhasil diubah!"}}, status=status.HTTP_200_OK)
      except IntegrityError as e:
        return Response({"Status": "Error", "Messages": {"English": "Failed to change password.", "Indonesia": "Gagal mengubah kata sandi."}}, status=status.HTTP_400_BAD_REQUEST)

class UserProfileViews(APIView):
    def put (self, request):
      try:
        body_json = request.body.decode('utf-8')
        body = json.loads(body_json)

        try:
          if request.headers.get('XFALL-AUTHORIZATION') is None:
            return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)
          if body['username'] is None:
            return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)
          if body['email'] is None:
            return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)
          if body['phone_number'] is None:
            return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
          return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)
      
        try: ## Check Login Session
            login = Login.objects.get(token=request.headers.get('XFALL-AUTHORIZATION'))
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)

        ## Check Token
        if login.login_status != "ON" and login.is_logged_out != 0:
          return Response({"Status": "Error", "Messages": {"English": "You're not allowed to access this service.", "Indonesia": "Anda tidak berhak mengakses layanan ini."}}, status=status.HTTP_400_BAD_REQUEST)

        try: ## Check Role
            account = Users.objects.get(id=login.user_id, is_verified=1)
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)
          
        if (account.role_id != 2):
            return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)

        try: ## Check Username availability
            user = Users.objects.get(username=body['username'], is_verified=1)
            if user.id != login.user_id:
              return Response({"Status": "Error", "Messages": {"English": "Username already taken.", "Indonesia": "Username sudah digunakan."}}, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist as e:
            pass

        try: ## Check Email availability
            user = Users.objects.get(email=body['email'], is_verified=1)
            if user.id != login.user_id:
              return Response({"Status": "Error", "Messages": {"English": "Email already taken.", "Indonesia": "Email sudah digunakan."}}, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist as e:
            pass
        
        account.username = body['username']
        account.email = body['email']
        account.phone_number = body['phone_number']
        account.updated_date = datetime.datetime.now()
        account.save()

        return Response({"Status": "Success", "Messages": {"English": "Profile updated!", "Indonesia": "Profile terupdate!"}}, status=status.HTTP_200_OK)
      except IntegrityError as e:
        return Response({"Status": "Error", "Messages": {"English": "Failed to update profile.", "Indonesia": "Update profile gagal."}}, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        try:
          if request.headers.get('XFALL-AUTHORIZATION') is None:
            return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
          return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)

        try: ## Check Login Session
            login = Login.objects.get(token=request.headers.get('XFALL-AUTHORIZATION'))
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)

        ## Check Token
        if login.login_status != "ON" and login.is_logged_out != 0:
          return Response({"Status": "Error", "Messages": {"English": "You're not allowed to access this service.", "Indonesia": "Anda tidak berhak mengakses layanan ini."}}, status=status.HTTP_400_BAD_REQUEST)

        try:
            account = Users.objects.get(id=login.user_id, is_verified=1)
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)
        
        detail = {"full_name": account.full_name, "username": account.username, "email": account.email, "phone_number": account.phone_number, "profile_image": account.profile_image}

        return Response({"Status": "Success", "Messages": {"English": "User's detail collected.", "Indonesia": "Detail pengguna berhasil diperoleh."}, "User": detail}, status=status.HTTP_200_OK)

class UserCameraViews(APIView):
    def post(self, request):
        body_json = request.body.decode('utf-8')
        body = json.loads(body_json)

        try:
          if request.headers.get('XFALL-AUTHORIZATION') is None:
            return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)
          if body['camera_id'] is None:
            return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
          return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)

        try: ## Check Login Session
            login = Login.objects.get(token=request.headers.get('XFALL-AUTHORIZATION'))
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)

        ## Check Token
        if login.login_status != "ON" and login.is_logged_out != 0:
          return Response({"Status": "Error", "Messages": {"English": "You're not allowed to access this service.", "Indonesia": "Anda tidak berhak mengakses layanan ini."}}, status=status.HTTP_400_BAD_REQUEST)

        try: ## Get User Detail
            user = Users.objects.get(id=login.user_id, is_verified=1)
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)
          
        if (user.role_id != 2): ## Role must be User
            return Response({"Status": "Error", "Messages": {"English": "You're not allowed to access this service.", "Indonesia": "Anda tidak berhak mengakses layanan ini."}}, status=status.HTTP_400_BAD_REQUEST)

        try: ## Check if already exists
            relation = CamerasUsersRelation.objects.get(user_id=login.user_id, camera_id=body['camera_id'])
            if relation is not None:
              return Response({"Status": "Error", "Messages": {"English": "Camera already added.", "Indonesia": "Kamera telah ditambahkan."}}, status=status.HTTP_400_BAD_REQUEST)  
        except ObjectDoesNotExist as e:
            pass

        userCamID = '{"camera": "' + body['camera_id'] + '", "user": "' + str(user.id) + '"}'
        dict_userCamID = json.loads(userCamID)
        userCam = CamerasUsersSerializer(data=dict_userCamID) 
        if userCam.is_valid():
            userCam.save()
        else:
            return Response({"Status": "Error", "Messages": userCam.errors}, status=status.HTTP_400_BAD_REQUEST)

        try: ## Get Camera Detail
            camera = Cameras.objects.get(id=body['camera_id'])
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)

        message = {"English": "You're now connected to " + camera.name, "Indonesia": "Anda telah terhubung dengan " + camera.name}
        return Response({"Status": "Success", "Messages": message}, status=status.HTTP_200_OK)

    def get(self, request):
        count = 0
        listCam = []

        try:
          if request.headers.get('XFALL-AUTHORIZATION') is None:
            return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)
          if request.GET.get('type') is None:
            return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
          return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)

        ## Check Type
        if request.GET.get('type') != "all" and request.GET.get('type') != "half":
          return Response({"Status": "Error", "Messages": {"English": "Invalid type.", "Indonesia": "Tipe tidak sesuai."}}, status=status.HTTP_400_BAD_REQUEST)

        try: ## Check Login Session
            login = Login.objects.get(token=request.headers.get('XFALL-AUTHORIZATION'))
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)

        ## Check Token
        if login.login_status != "ON" and login.is_logged_out != 0:
          return Response({"Status": "Error", "Messages": {"English": "You're not allowed to access this service.", "Indonesia": "Anda tidak berhak mengakses layanan ini."}}, status=status.HTTP_400_BAD_REQUEST)

        try:
            list = CamerasUsersRelation.objects.all().filter(user_id=login.user_id)
            datas = CamerasUsersRelation.objects.all().filter(user_id=login.user_id).count()
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)
        
        try: 
            if request.GET.get('type') == "all":
              while (count != datas):
                  cam = Cameras.objects.get(id=list[count].camera.id)
                  camObj = {"id": str(cam.id), "status": cam.status, "num_of_contacts": str(CamerasUsersRelation.objects.all().filter(camera_id=cam.id).count() - 1)}
                  listCam.append(camObj)
                  count = count+1
            elif request.GET.get('type') == "half":
              while (count != datas and count < 5):
                  cam = Cameras.objects.get(id=list[count].camera.id)
                  camObj = {"id": str(cam.id), "status": cam.status, "num_of_contacts": str(CamerasUsersRelation.objects.all().filter(camera_id=cam.id).count() - 1)}
                  listCam.append(camObj)
                  count = count+1
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)
        
        if listCam.__len__ != 0:
          return Response({"Status": "Success", "Messages": {"English": "Camera list collected.", "Indonesia": "List kamera berhasil diperoleh."}, "Camera_List": listCam}, status=status.HTTP_200_OK)

        return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)

class UserCameraDetailViews(APIView):
    def get(self, request):
        try:
          if request.headers.get('XFALL-AUTHORIZATION') is None:
            return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)
          if request.GET.get('cameraId') is None:
            return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
          return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)

        try: ## Check Login Session
            login = Login.objects.get(token=request.headers.get('XFALL-AUTHORIZATION'))
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)

        ## Check Token
        if login.login_status != "ON" and login.is_logged_out != 0:
          return Response({"Status": "Error", "Messages": {"English": "You're not allowed to access this service.", "Indonesia": "Anda tidak berhak mengakses layanan ini."}}, status=status.HTTP_400_BAD_REQUEST)

        try:
            CamerasUsersRelation.objects.get(user_id=login.user_id, camera_id=request.GET.get('cameraId'))
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            camera = Cameras.objects.get(id=request.GET.get('cameraId'))
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)
                                                                        
        detail = {"id": str(camera.id), "name": camera.name, "address": camera.address, "num_of_contact": str(CamerasUsersRelation.objects.all().filter(camera_id=camera.id).count() - 1)}

        return Response({"Status": "Success", "Messages": {"English": "Camera detail collected.", "Indonesia": "Detail kamera berhasil diperoleh."}, "Camera": detail}, status=status.HTTP_200_OK)

class EmergencyContactViews(APIView):
    def get(self, request):
        count = 0
        listCam = []

        userRole = Roles.objects.get(name="User")

        try:
          if request.headers.get('XFALL-AUTHORIZATION') is None:
            return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
          return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)

        try: ## Check Login Session
            login = Login.objects.get(token=request.headers.get('XFALL-AUTHORIZATION'))
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)

        ## Check Token
        if login.login_status != "ON" and login.is_logged_out != 0:
          return Response({"Status": "Error", "Messages": {"English": "You're not allowed to access this service.", "Indonesia": "Anda tidak berhak mengakses layanan ini."}}, status=status.HTTP_400_BAD_REQUEST)

        try:
            list = CamerasUsersRelation.objects.all().filter(user_id=login.user_id)
            datas = CamerasUsersRelation.objects.all().filter(user_id=login.user_id).count()
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)
        
        try: 
            while (count != datas):
                countUser = 0
                listUser = []
                cam = Cameras.objects.get(id=list[count].camera.id)
                relation = CamerasUsersRelation.objects.all().filter(camera_id=cam.id)
                totalUser = CamerasUsersRelation.objects.all().filter(camera_id=cam.id).count()
                while (countUser != totalUser):
                  users = None
                  try:
                    users = Users.objects.get(id=relation[countUser].user_id, role=userRole.id, is_verified=1)
                  except:
                    countUser = countUser+1
                    continue
                  userObj = {'full_name': users.full_name,'phone_number': users.phone_number, 'profile_image': users.profile_image}
                  listUser.append(userObj)
                  countUser = countUser+1
                
                camObj = {"name": cam.name, "contact_list": listUser}
                listCam.append(camObj)
                count = count+1
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)
        
        if listCam.__len__ != 0:
          return Response({"Status": "Success", "Messages": {"English": "Emergency contact list collected.", "Indonesia": "List kontak darurat berhasil diperoleh."}, "Camera_List": listCam}, status=status.HTTP_200_OK)

        return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)

class EmergencyServiceViews(APIView):
    def get(self, request):
        count = 0
        listID = []
        listSelected = []
        listServices = []

        try:
          if request.headers.get('XFALL-AUTHORIZATION') is None:
            return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
          return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)

        try: ## Check Login Session
            login = Login.objects.get(token=request.headers.get('XFALL-AUTHORIZATION'))
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)

        ## Check Token
        if login.login_status != "ON" and login.is_logged_out != 0:
          return Response({"Status": "Error", "Messages": {"English": "You're not allowed to access this service.", "Indonesia": "Anda tidak berhak mengakses layanan ini."}}, status=status.HTTP_400_BAD_REQUEST)

        try:
            list = CamerasUsersRelation.objects.all().filter(user_id=login.user_id)
            datas = CamerasUsersRelation.objects.all().filter(user_id=login.user_id).count()
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)

        try: 
            while (count != datas):
                cam = Cameras.objects.get(id=list[count].camera_id)
                service = EmergencyServices.objects.get(id=cam.emergency_services_id)
                listID.append(service.id)
                selectedService = {"camera_name": cam.name, "name": service.name, "phone_number": service.phone_number, "address": service.address}
                listSelected.append(selectedService)
                count = count+1
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)

        try:
            list = EmergencyServices.objects.all()
            datas = EmergencyServices.objects.all().count()
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)

        count = 0
        try: 
            while (count != datas):
              if list[count].id not in listID:
                eService = EmergencyServices.objects.get(id=list[count].id)
                services = {'name': eService.name, 'phone_number': eService.phone_number, 'address': eService.address}
                listServices.append(services)
                count = count+1
              else:
                count = count+1
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)
        
        if listServices.__len__ != 0:
          return Response({"Status": "Success", "Messages": {"English": "Emergency services list collected.", "Indonesia": "List layanan darurat berhasil diperoleh."}, "Selected_Service": listSelected, "Service_List": listServices}, status=status.HTTP_200_OK)

        return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)

class UserNotificationsViews(APIView):
    def get (self,request):
        count = 0 
        listNotif = []

        try:
          if request.headers.get('XFALL-AUTHORIZATION') is None:
            return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)
          if request.GET.get('type') is None:
            return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
          return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)

        ## Check Type
        if request.GET.get('type') != "all" and request.GET.get('type') != "today":
          return Response({"Status": "Error", "Messages": {"English": "Invalid type.", "Indonesia": "Tipe tidak sesuai."}}, status=status.HTTP_400_BAD_REQUEST)

        try: ## Check Login Session
            login = Login.objects.get(token=request.headers.get('XFALL-AUTHORIZATION'))
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)

        ## Check Token
        if login.login_status != "ON" and login.is_logged_out != 0:
          return Response({"Status": "Error", "Messages": {"English": "You're not allowed to access this service.", "Indonesia": "Anda tidak berhak mengakses layanan ini."}}, status=status.HTTP_400_BAD_REQUEST)

        try:
            list = CamerasUsersRelation.objects.all().filter(user_id=login.user_id)
            datas = CamerasUsersRelation.objects.all().filter(user_id=login.user_id).count()
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)
        
        try: 
            while (count != datas):
                countNotif = 0
                cam = Cameras.objects.get(id=list[count].camera.id)
                notifs = Notifications.objects.all().filter(camera_id=cam.id)
                totalNotif = Notifications.objects.all().filter(camera_id=cam.id).count()

                while (countNotif != totalNotif):
                  notif = None
                  done = False
                  go_home = False
                  call_home = False
                  call_service = False
                  try:
                    notif = Notifications.objects.get(id=notifs[countNotif].id)
                  except:
                    countNotif = countNotif+1
                    continue
                  
                  if request.GET.get('type') == "today":
                      if str(datetime.datetime.now().date()) not in str(notif.created_date):
                        countNotif = countNotif+1
                        continue
                      
                  try:
                      if go_home is not True:
                        go_home = Actions.objects.get(notification_id=notif.id, action="GO_HOME")
                        go_home = True
                  except:
                      go_home = False

                  try:
                      if call_home is not True:
                        call_home = Actions.objects.get(notification_id=notif.id, action="CALL_HOME")
                        call_home = True
                  except:
                      call_home = False

                  try:
                      if call_service is not True:
                        call_service = Actions.objects.get(notification_id=notif.id, action="CALL_SERVICE")
                        call_service = True
                  except:
                      call_service = False
                  
                  if notif.status == "OFF":
                      done = True
                  detailNotif = {"id": notif.id, "camera_id": notif.camera_id, "camera_name": cam.name, 
                      "is_go_home": go_home, "is_call_home": call_home, "is_call_service": call_service, 
                      "is_done": done, "created_date": notif.created_date.strftime('%Y-%m-%d %H:%M:%S')}
                  listNotif.append(detailNotif)
                  countNotif = countNotif+1

                count = count+1
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)

        listNotif.sort(key=lambda x: (x['is_done'], x['created_date']))
        if listNotif.__len__ != 0:
          return Response({"Status": "Success", "Messages": {"English": "Notification list collected.", "Indonesia": "List notifikasi berhasil diperoleh."}, "Notification_List": listNotif}, status=status.HTTP_200_OK)

        return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)

class UserNotificationViews(APIView):
    def get (self,request):
        count = 0 
        listNotif = []

        try:
          if request.headers.get('XFALL-AUTHORIZATION') is None:
            return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)
          if request.GET.get('cameraId') is None:
            return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
          return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)

        try: ## Check Login Session
            login = Login.objects.get(token=request.headers.get('XFALL-AUTHORIZATION'))
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)

        ## Check Token
        if login.login_status != "ON" and login.is_logged_out != 0:
          return Response({"Status": "Error", "Messages": {"English": "You're not allowed to access this service.", "Indonesia": "Anda tidak berhak mengakses layanan ini."}}, status=status.HTTP_400_BAD_REQUEST)

        try:
            notifs = Notifications.objects.all().filter(camera_id=request.GET.get('cameraId'))
            datas = Notifications.objects.all().filter(camera_id=request.GET.get('cameraId')).count()
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)
        
        try: 
            while (count != datas):
                list = Actions.objects.all().filter(notification_id=notifs[count].id)
                totalActions = Actions.objects.all().filter(notification_id=notifs[count].id).count()
                countAction = 0
                go_home = ""
                call_home = ""
                call_service = ""
                
                while (countAction != totalActions):
                  action = Actions.objects.get(id=list[countAction].id)

                  if action.action == "GO_HOME":
                    go_home = action.user.full_name
                  if action.action == "CALL_HOME":
                    call_home = action.user.full_name
                  if action.action == "CALL_SERVICE":
                    call_service = action.user.full_name
                  
                  countAction = countAction+1
                
                if notifs[count].status == "ON":
                  done = False
                else:
                  done = True

                detailAction = {"id": notifs[count].id, "go_home": go_home, "call_home": call_home, "call_service": call_service, 
                      "done": done, "created_date": notifs[count].created_date.strftime('%Y-%m-%d %H:%M:%S')}
                listNotif.append(detailAction)
                count = count+1
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)

        listNotif.sort(key=lambda x: (x['done'], x['created_date']))
        if listNotif.__len__ != 0:
          return Response({"Status": "Success", "Messages": {"English": "Notification action list collected.", "Indonesia": "List tindakan notifikasi berhasil diperoleh."}, "Action_List": listNotif}, status=status.HTTP_200_OK)

        return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)

class UserChatViews(APIView):
    def post(self, request):
        body_json = request.body.decode('utf-8')
        body = json.loads(body_json)
        count = 0
        now = datetime.datetime.now()

        try:
          if request.headers.get('XFALL-AUTHORIZATION') is None:
            return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)
          if body['camera_id'] is None:
            return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)
          if body['message'] is None:
            return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
          return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)

        try: ## Check Login Session
            login = Login.objects.get(token=request.headers.get('XFALL-AUTHORIZATION'))
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)

        ## Check Token
        if login.login_status != "ON" and login.is_logged_out != 0:
          return Response({"Status": "Error", "Messages": {"English": "You're not allowed to access this service.", "Indonesia": "Anda tidak berhak mengakses layanan ini."}}, status=status.HTTP_400_BAD_REQUEST)

        try: ## Get User Detail
            user = Users.objects.get(id=login.user_id, is_verified=1)
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)
          
        if (user.role_id != 2): ## Role must be User
            return Response({"Status": "Error", "Messages": {"English": "You're not allowed to access this service.", "Indonesia": "Anda tidak berhak mengakses layanan ini."}}, status=status.HTTP_400_BAD_REQUEST)

        try: ## Check if no relation
            CamerasUsersRelation.objects.get(user_id=login.user_id, camera_id=body['camera_id'])
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)

        message = json.loads('{"camera": "' + body['camera_id'] + '", "content": "' + body['message'] + '", "created_date": "' + str(now) + '", "user": "' + str(login.user_id) + '"}')
        messageSerial = MessageSerializer(data=message) 
        if messageSerial.is_valid():
            messageSerial.save()
        else:
            return Response({"Status": "Error", "Messages": messageSerial.errors}, status=status.HTTP_400_BAD_REQUEST)

        try: ## Check emergency contact list
            list = CamerasUsersRelation.objects.all().filter(camera_id=body['camera_id'])
            datas = CamerasUsersRelation.objects.all().filter(camera_id=body['camera_id']).count()
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)

        try: ## Get Camera Object
            cam = Cameras.objects.get(id=body['camera_id'])
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)

        while count != datas:
          try: ## Get User Detail
            user = Users.objects.get(id=list[count].user_id, is_verified=1, role_id=2)
          except ObjectDoesNotExist as e:
            count = count+1
            continue
          
          try: ## Check if object message recipients already created
              checkRecipients = MessageRecipients.objects.get(camera_id=body['camera_id'], recipient=user.id)
              checkRecipients.is_read = False
              checkRecipients.save()
          except ObjectDoesNotExist as e:
              ## Add message recipient
              recipient = MessageRecipients(recipient = user, camera = cam, is_read=False)
              recipient.save()
          
          count=count+1

        try: ## Get Message ID
            msg = Messages.objects.get(camera=cam.id, content=body['message'], created_date=now, user=user.id)
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)

        content = body['message'][0:50]
        messageToEmergencyContacts = messaging.Message(
            data={
                "push_notif_type": "CHAT",
                "chat_id": str(msg.id),
                "camera_id": body['camera_id'],
                "camera_name": cam.name,
                "sender_name": user.full_name,
                "content": content
            },
            topic="testing",
            android=messaging.AndroidConfig(priority="normal"),
        )
        
        messaging.send(messageToEmergencyContacts)

        return Response({"Status": "Success", "Messages": {"English": "Message sent.", "Indonesia": "Pesan terkirim."}, "msg": str(messageToEmergencyContacts)}, status=status.HTTP_200_OK)

    def get (self,request):
        count = 0 
        listMessage = []

        try:
          if request.headers.get('XFALL-AUTHORIZATION') is None:
            return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)
          if request.GET.get('cameraId') is None:
            return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
          return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)

        try: ## Check Login Session
            login = Login.objects.get(token=request.headers.get('XFALL-AUTHORIZATION'))
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)

        ## Check Token
        if login.login_status != "ON" and login.is_logged_out != 0:
          return Response({"Status": "Error", "Messages": {"English": "You're not allowed to access this service.", "Indonesia": "Anda tidak berhak mengakses layanan ini."}}, status=status.HTTP_400_BAD_REQUEST)

        try:
            messages = Messages.objects.all().filter(camera_id=request.GET.get('cameraId'))
            datas = Messages.objects.all().filter(camera_id=request.GET.get('cameraId')).count()
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)
        
        try: 
            while (count != datas):
                msg = Messages.objects.get(id=messages[count].id)
                try: ## Get User Detail
                  user = Users.objects.get(id=messages[count].user_id, is_verified=1, role_id=2)
                except ObjectDoesNotExist as e:
                  count = count+1
                  continue

                detail = {"message_id": msg.id, "sender_username": user.username, "sender_full_name": user.full_name, "sender_image": user.profile_image,
                      "content": msg.content, "created_date": msg.created_date.strftime('%Y-%m-%d %H:%M:%S')}
                listMessage.append(detail)
                count = count+1
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)

        listMessage.sort(key=lambda x: x['created_date'])
        if listMessage.__len__ != 0:
          return Response({"Status": "Success", "Messages": {"English": "Message list collected.", "Indonesia": "List pesan berhasil diperoleh."}, "Message_List": listMessage}, status=status.HTTP_200_OK)

        return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)

class UserChatsViews(APIView):
    def get (self,request):
        count = 0 
        listChat = []

        try:
          if request.headers.get('XFALL-AUTHORIZATION') is None:
            return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
          return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)

        try: ## Check Login Session
            login = Login.objects.get(token=request.headers.get('XFALL-AUTHORIZATION'))
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)

        ## Check Token
        if login.login_status != "ON" and login.is_logged_out != 0:
          return Response({"Status": "Error", "Messages": {"English": "You're not allowed to access this service.", "Indonesia": "Anda tidak berhak mengakses layanan ini."}}, status=status.HTTP_400_BAD_REQUEST)

        try:
            list = CamerasUsersRelation.objects.all().filter(user_id=login.user_id)
            datas = CamerasUsersRelation.objects.all().filter(user_id=login.user_id).count()
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)
        
        try: 
            while (count != datas):
                countReader = 0
                num_of_unreads = 0

                try: ## Get Camera Detail
                  cam = Cameras.objects.get(id=list[count].camera_id)
                except ObjectDoesNotExist as e:
                  return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)

                try: ## Get Last Chat
                  chat = Messages.objects.filter(camera_id=list[count].camera_id).latest('created_date')
                except ObjectDoesNotExist as e:
                  detail = {"camera_id": str(cam.id), "camera_name": cam.name, "last_chat": "", 
                      "updated_date": "", "num_of_unreads": ""}
                  listChat.append(detail)
                  count = count+1
                  continue

                try:
                  recipients = MessageRecipients.objects.all().filter(camera_id=list[count].camera_id)
                  totalRecipients = MessageRecipients.objects.all().filter(camera_id=list[count].camera_id).count()
                except ObjectDoesNotExist as e:
                  return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)

                while (countReader != totalRecipients):
                  # try: ## Get User Detail
                  #   user = Users.objects.get(id=totalRecipients[countReader].recipient_id, is_verified=1, role_id=2)
                  # except ObjectDoesNotExist as e:
                  #   countReader = countReader+1
                  #   continue

                  if recipients[countReader].is_read == False:
                    num_of_unreads = num_of_unreads + 1
                  
                  countReader = countReader+1

                detail = {"camera_id": str(cam.id), "camera_name": cam.name, "last_chat": chat.content, 
                      "updated_date": chat.created_date.strftime('%Y-%m-%d %H:%M:%S'), "num_of_unreads": str(num_of_unreads)}
                listChat.append(detail)
                count = count+1
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)

        listChat.sort(key=lambda x: x['updated_date'])
        if listChat.__len__ != 0:
          return Response({"Status": "Success", "Messages": {"English": "Chat list collected.", "Indonesia": "List obrolan berhasil diperoleh."}, "Chat_List": listChat}, status=status.HTTP_200_OK)

        return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)

class UserActionViews(APIView):
    def post(self, request):
        body_json = request.body.decode('utf-8')
        body = json.loads(body_json)

        try:
          if request.headers.get('XFALL-AUTHORIZATION') is None:
            return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)
          if body['camera_id'] is None:
            return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)
          if body['notification_id'] is None:
            return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)
          if body['action'] is None:
            return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
          return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)
        
        ## Check Action
        if body['action'] != "GO_HOME" and body['action'] != "CALL_HOME" and body['action'] != "CALL_SERVICE":
          return Response({"Status": "Error", "Messages": {"English": "Invalid action.", "Indonesia": "Tindakan tidak sesuai."}}, status=status.HTTP_400_BAD_REQUEST)

        try: ## Check Login Session
            login = Login.objects.get(token=request.headers.get('XFALL-AUTHORIZATION'))
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)

        ## Check Token
        if login.login_status != "ON" and login.is_logged_out != 0:
          return Response({"Status": "Error", "Messages": {"English": "You're not allowed to access this service.", "Indonesia": "Anda tidak berhak mengakses layanan ini."}}, status=status.HTTP_400_BAD_REQUEST)

        try: ## Get User Detail
            user = Users.objects.get(id=login.user_id, is_verified=1)
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)
          
        if (user.role_id != 2): ## Role must be User
            return Response({"Status": "Error", "Messages": {"English": "You're not allowed to access this service.", "Indonesia": "Anda tidak berhak mengakses layanan ini."}}, status=status.HTTP_400_BAD_REQUEST)

        try: ## Check if no relation
            CamerasUsersRelation.objects.get(user_id=login.user_id, camera_id=body['camera_id'])
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)

        try: ## Check if no notification
            Notifications.objects.get(id=body['notification_id'])
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)

        try: ## Check if user already give action
            Actions.objects.get(notification_id=body['notification_id'], user_id=login.user_id)
            return Response({"Status": "Error", "Messages": {"English": "You already give an action.", "Indonesia": "Anda sudah memberikan tindakan."}}, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist as e:
            pass

        try: ## Check if action already used by other user
            act = Actions.objects.get(notification_id=body['notification_id'], action=body['action'])
            if act.user_id != login.user_id:
              actor = Users.objects.get(id=act.user_id)
              return Response({"Status": "Error", "Messages": {"English": "Action has been performed by "+actor.full_name, "Indonesia": "Tindakan telah dilakukan oleh "+actor.full_name}}, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist as e:
            pass

        action = json.loads('{"notification": "' + body['notification_id'] + '", "action": "' + body['action'] + '", "user": "' + str(login.user_id) + '", "created_date": "' + str(datetime.datetime.now()) +'"}')
        actionSerial = ActionSerializer(data=action) 
        if actionSerial.is_valid():
            actionSerial.save()
        else:
            return Response({"Status": "Error", "Messages": actionSerial.errors}, status=status.HTTP_400_BAD_REQUEST)

        try: ## Get Camera Detail
            cam  = Cameras.objects.get(id=body['camera_id'])
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)

        message = messaging.Message(
            data={
                "push_notif_type": "ACTION",
                "action_type": body['action'],
                "actor_name": str(login.user_id),
                "camera_id": body['camera_id'],
                "camera_name": cam.name
            },
            topic="testing",
            android=messaging.AndroidConfig(priority="normal"),
        )
        
        messaging.send(message)

        return Response({"Status": "Success", "Messages": {"English": "Action sent.", "Indonesia": "Tindakan terkirim."}, "msg": str(message)}, status=status.HTTP_200_OK)

class UserVerificationViews(APIView):
    def post(self, request):
        body_json = request.body.decode('utf-8')
        body = json.loads(body_json)

        try:
          if body['user_id'] is None:
            return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)
          if body['verification_code'] is None:
            return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)
          if request.GET.get('type') is None:
            return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
          return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)
        
        ## Check Type
        if request.GET.get('type') != "verify" and request.GET.get('type') != "send":
          return Response({"Status": "Error", "Messages": {"English": "Invalid type.", "Indonesia": "Tipe tidak sesuai."}}, status=status.HTTP_400_BAD_REQUEST)

        try: ## Get User Detail
            user = Users.objects.get(id=body['user_id'])
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Messages": {"English": "No data found.", "Indonesia": "Data tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)
          
        if user.role_id != 2: ## Role must be User
            return Response({"Status": "Error", "Messages": {"English": "You're not allowed to access this service.", "Indonesia": "Anda tidak berhak mengakses layanan ini."}}, status=status.HTTP_400_BAD_REQUEST)

        if request.GET.get('type') == "send":
          try:
              verif = UserVerificationLogs(user_id=user.id, verification_code=body['verification_code'], expired_time=datetime.datetime.now() + datetime.timedelta(minutes=5))
              verif.save()
          except:
              return Response({"Status": "Error", "Messages": {"English": "Failed to save verification log.", "Indonesia": "Gagal untuk menyimpan log verifikasi."}}, status=status.HTTP_400_BAD_REQUEST)

          return Response({"Status": "Error", "Messages": {"English": "Verification log successfully inserted.", "Indonesia": "Log verifikasi berhasil dimasukkan."}}, status=status.HTTP_200_BAD_REQUEST)
        else:
          try: ## Get Verification Log
              verif = UserVerificationLogs.objects.get(user_id=user.id, verification_code=body['verification_code'])
          except:
              return Response({"Status": "Error", "Messages": {"English": "OTP code invalid.", "Indonesia": "Kode OTP tidak valid."}}, status=status.HTTP_400_BAD_REQUEST)
          
          if verif.expired_time < datetime.datetime.now():
              return Response({"Status": "Error", "Messages": {"English": "OTP code invalid.", "Indonesia": "Kode OTP tidak valid."}}, status=status.HTTP_400_BAD_REQUEST)
          
          if user.is_verified == 0:
            user.is_verified = "1"
            user.save()

          return Response({"Status": "Success", "Messages": {"English": "User verified!", "Indonesia": "Pengguna terverifikasi!"}}, status=status.HTTP_200_OK)

class UserProfileNumberViews(APIView):
    def get(self, request):
        try:
          if request.GET.get('email') is None:
            return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)
          if request.GET.get('username') is None:
            return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
          return Response({"Status": "Error", "Messages": {"English": "Required field is empty.", "Indonesia": "Field yang harus diisi kosong."}}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = Users.objects.get(email=request.GET.get('email'), username=request.GET.get('username'))
        except ObjectDoesNotExist as e:
            return Response({"Status": "Error", "Messages": {"English": "Email or username is not found.", "Indonesia": "Email atau username tidak ditemukan."}}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({"Status": "Success", "Messages": {"English": "User's detail collected.", "Indonesia": "Detail pengguna berhasil diperoleh."}, "Phone_Number": user.phone_number}, status=status.HTTP_200_OK)
