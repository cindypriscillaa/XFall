from datetime import datetime
from email.policy import default
from django.db import models

class ServiceTypes(models.Model):
    name = models.CharField(max_length=30)
    created_date = models.DateField(blank=True)
    created_by = models.CharField(max_length=15, blank=True)
    updated_date = models.DateField(blank=True)
    updated_by = models.CharField(max_length=15, blank=True)

    class Meta:
        db_table = "services_types"
    
class EmergencyServices(models.Model):
    type = models.ForeignKey(ServiceTypes, on_delete=models.CASCADE)
    name = models.CharField(max_length=30)
    address = models.CharField(max_length=150)
    phone_number = models.PositiveIntegerField(default="021")
    created_date = models.DateField(blank=True)
    created_by = models.CharField(max_length=15, blank=True) 
    updated_date = models.DateField(blank=True)
    updated_by = models.CharField(max_length=15, blank=True) 

    class Meta:
        db_table = "emergency_services"

class Cameras(models.Model):
    emergency_services = models.ForeignKey(EmergencyServices, blank=True, null=True, on_delete=models.DO_NOTHING)
    status = models.CharField(max_length=15, default="OFF")
    created_date = models.DateField(datetime.now)
    created_by = models.CharField(max_length=15, default="system")
    updated_date = models.DateField(datetime.now)
    updated_by = models.CharField(max_length=15, default="system")

    class Meta:
        db_table = "cameras"

class Roles(models.Model):
    name = models.CharField(max_length=30)
    created_date = models.DateField(blank=True)
    created_by = models.CharField(max_length=15, blank=True) 
    updated_date = models.DateField(blank=True)
    updated_by = models.CharField(max_length=15, blank=True) 

    class Meta:
        db_table = "roles"

class Users(models.Model):
    #camera = models.ForeignKey(Cameras, on_delete=models.CASCADE)
    role = models.ForeignKey(Roles, on_delete=models.CASCADE)
    email = models.EmailField(blank=True)
    username = models.CharField(max_length=15, unique=True)
    password = models.CharField(max_length=30)
    profile_image = models.ImageField(upload_to='uploads/', blank=True)
    phone_number = models.PositiveIntegerField(default="64", blank=True)
    is_verified = models.BooleanField(default=False)
    created_date = models.DateField(blank=True)
    created_by = models.CharField(max_length=15, blank=True) 
    updated_date = models.DateField(blank=True)
    updated_by = models.CharField(max_length=15, blank=True) 

    class Meta:
        db_table = "users"


class CamerasUsersRelation(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    camera = models.ForeignKey(Cameras, on_delete=models.CASCADE)

    class Meta:
        db_table = "users_cameras"

class Notifications(models.Model):
    camera = models.ForeignKey(Cameras, on_delete=models.CASCADE)
    status = models.CharField(max_length=30)
    created_date = models.DateTimeField(blank=False, default=datetime.now)
    created_by = models.CharField(max_length=15, blank=True) 
    updated_date = models.DateTimeField(blank=False, default=datetime.now)
    updated_by = models.CharField(max_length=15, blank=True) 

    class Meta:
        db_table = "notifications"

class NotificationHistories(models.Model):
    notification = models.ForeignKey(Notifications, on_delete=models.CASCADE)
    user = models.ForeignKey(Users, on_delete=models.CASCADE, blank=True, null=True)
    response = models.CharField(max_length=30)
    created_date = models.DateTimeField(blank=False, default=datetime.now)
    created_by = models.CharField(max_length=15, blank=True) 
    updated_date = models.DateTimeField(blank=False, default=datetime.now)
    updated_by = models.CharField(max_length=15, blank=True) 

    class Meta:
        db_table = "notification_histories"

# class UserPushToken(models.Model):
#     token = models.CharField(max_length=1000)

#     def __str__(self):
#         return self.token
