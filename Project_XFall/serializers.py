from rest_framework import serializers
from .models import Actions, CamerasUsersRelation, Messages, Users
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.core.exceptions import ObjectDoesNotExist

class UserSerializer(serializers.ModelSerializer):
    role = serializers.PKOnlyObject
    email = serializers.EmailField
    username = serializers.CharField(max_length=15)
    password = serializers.CharField(max_length=30)
    full_name = serializers.CharField(max_length=30)
    profile_image = serializers.ImageField
    phone_number = serializers.IntegerField
    is_verified = serializers.BooleanField
    created_date = serializers.DateTimeField()
    created_by = serializers.CharField(max_length=15)
    updated_date = serializers.DateTimeField()
    updated_by = serializers.CharField(max_length=15)

    class Meta:
        model = Users
        fields = ('__all__')

class CamerasUsersSerializer(serializers.ModelSerializer):
    user = serializers.PKOnlyObject
    camera = serializers.PKOnlyObject

    class Meta:
        model = CamerasUsersRelation
        fields = ('__all__')

class MessageSerializer(serializers.ModelSerializer):
    user = serializers.PKOnlyObject
    camera = serializers.PKOnlyObject
    content = serializers.CharField(max_length=255)
    created_date = serializers.DateTimeField()

    class Meta:
        model = Messages
        fields = ('__all__')

class ActionSerializer(serializers.ModelSerializer):
    user = serializers.PKOnlyObject
    notification = serializers.PKOnlyObject
    action = serializers.CharField(max_length=30)
    created_date = serializers.DateTimeField()

    class Meta:
        model = Actions
        fields = ('__all__')

class AdminTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        token['email'] = user.email
        return token

    def validate(self, request):
        data = super().validate(request)
        refresh = self.get_token(self.user)
        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)
        
        # Add extra responses here
        us = Users.objects.filter(username=self.user.username)
        
        if us.get(role=1) is None:
            data['Status'] = "Error"
            data['Message'] = "Login failed!"
        else:
            data['Status'] = "Success"
            data['Message'] = "Login successful!"
        
        data['username'] = self.user.username
        #data['password'] = self.user.password
        return data

class UserTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, request):
        data = super().validate(request)
        refresh = self.get_token(self.user)
        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)
        
        # Add extra responses here
        us = Users.objects.filter(username=self.user.username)
        try:
            us.get(role=2) 
        except ObjectDoesNotExist as e:
            body = request
            body['Status'] = "Error"
            body['Message'] = "Login failed!"
            return body

        data['Status'] = "Success"
        data['Message'] = "Login successful!"
        
        data['username'] = self.user.username
        #data['password'] = self.user.password
        return data