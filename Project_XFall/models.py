import uuid
from datetime import datetime
from django.db import models
from pyparsing import empty

def generate_pk(prefix):
    #number = random.randint(1000, 9999)
    return '{}{}'.format(prefix, datetime.now().strftime('%y%m%d%H%M%S'))

class ServiceTypes(models.Model): ## OK
    #id = models.CharField(primary_key=True, default=generate_pk("ST"), editable=False, max_length=12, unique=True)
    name = models.CharField(max_length=30)
    created_date = models.DateTimeField(blank=True)
    created_by = models.CharField(max_length=15, blank=True)
    updated_date = models.DateTimeField(blank=True)
    updated_by = models.CharField(max_length=15, blank=True)

    class Meta:
        db_table = "services_types"
    
class EmergencyServices(models.Model): ## OK
    #id = models.CharField(primary_key=True, default=generate_pk("ES"), editable=False, max_length=12, unique=True)
    type = models.ForeignKey(ServiceTypes, on_delete=models.CASCADE)
    name = models.CharField(max_length=30)
    address = models.CharField(max_length=150)
    phone_number = models.PositiveIntegerField(default="64")
    created_date = models.DateTimeField(blank=True)
    created_by = models.CharField(max_length=15, blank=True) 
    updated_date = models.DateTimeField(blank=True)
    updated_by = models.CharField(max_length=15, blank=True) 

    class Meta:
        db_table = "emergency_services"

class Cameras(models.Model): ## OK
    #id = models.CharField(primary_key=True, default=generate_pk("CM"), editable=False, max_length=12, unique=True)
    name = models.CharField(max_length=30)
    emergency_services = models.ForeignKey(EmergencyServices, blank=True, null=True, default=None, on_delete=models.DO_NOTHING)
    status = models.CharField(max_length=15, default="OFF")
    #address = models.CharField(max_length=100) ## TO-DO
    created_date = models.DateTimeField(datetime.now)
    created_by = models.CharField(max_length=15)
    updated_date = models.DateTimeField(datetime.now)
    updated_by = models.CharField(max_length=15)

    class Meta:
        db_table = "cameras"

class Roles(models.Model): ## OK
    #id = models.CharField(primary_key=True, default=generate_pk("RL"), editable=False, max_length=12, unique=True)
    name = models.CharField(max_length=30)
    created_date = models.DateTimeField(blank=True)
    created_by = models.CharField(max_length=15, blank=True) 
    updated_date = models.DateTimeField(blank=True)
    updated_by = models.CharField(max_length=15, blank=True) 

    class Meta:
        db_table = "roles"

class Users(models.Model): ## OK
    #id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True) #contoh: b46554b6-dac2-457b-aba0-9d7b499b7f9d
    #id = models.CharField(primary_key=True, default=generate_pk("US"), editable=False, max_length=12, unique=True) 
    role = models.ForeignKey(Roles, on_delete=models.CASCADE)
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=15, unique=True)
    password = models.CharField(max_length=30)
    full_name = models.CharField(max_length=30)
    profile_image = models.ImageField(upload_to='assets/', blank=True)
    phone_number = models.PositiveIntegerField(blank=False)
    is_verified = models.BooleanField(default=False)
    created_date = models.DateTimeField(blank=True)
    created_by = models.CharField(max_length=15, blank=True) 
    updated_date = models.DateTimeField(blank=True)
    updated_by = models.CharField(max_length=15, blank=True) 

    # USERNAME_FIELD = 'full_name' ## Biar kursornya keatas
    # REQUIRED_FIELDS = ['full_name', 'email', 'username', 'password', 'phone_number']
    class Meta:
        db_table = "users"

class CamerasUsersRelation(models.Model): ## OK
    #id = models.CharField(primary_key=True, default=generate_pk("UC"), editable=False, max_length=12, unique=True)
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    camera = models.ForeignKey(Cameras, on_delete=models.CASCADE)

    class Meta:
        db_table = "users_cameras"

class Notifications(models.Model): ## OK
    #id = models.CharField(primary_key=True, default=generate_pk("NT"), editable=False, max_length=12, unique=True)
    camera = models.ForeignKey(Cameras, on_delete=models.CASCADE)
    status = models.CharField(max_length=30)
    created_date = models.DateTimeField(blank=False, default=datetime.now)
    created_by = models.CharField(max_length=15, blank=True) 
    updated_date = models.DateTimeField(blank=False, default=datetime.now)
    updated_by = models.CharField(max_length=15, blank=True) 

    class Meta:
        db_table = "notifications"

class Actions(models.Model): ## OK
    #id = models.CharField(primary_key=True, default=generate_pk("AC"), editable=False, max_length=12, unique=True)
    notification = models.ForeignKey(Notifications, on_delete=models.CASCADE)
    user = models.ForeignKey(Users, on_delete=models.CASCADE, blank=True, null=True)
    action = models.CharField(max_length=30)
    created_date = models.DateTimeField(blank=False, default=datetime.now)

    class Meta:
        db_table = "actions"

class Login(models.Model): ## OK
    #id = models.CharField(primary_key=True, default=generate_pk("LG"), editable=False, max_length=12, unique=True)
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    login_status = models.CharField(max_length=10)
    is_logged_out = models.BooleanField(default=False)
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True) 
    created_date = models.DateTimeField(blank=False, default=datetime.now)

    class Meta:
        db_table = "login"

class VerificationLogs(models.Model): ## OK
    #id = models.CharField(primary_key=True, default=generate_pk("VR"), editable=False, max_length=12, unique=True)
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    camera = models.ForeignKey(Cameras, on_delete=models.CASCADE)
    created_date = models.DateTimeField(blank=False, default=datetime.now)
    created_by = models.CharField(max_length=15, blank=True) 
    updated_date = models.DateTimeField(blank=False, default=datetime.now)
    updated_by = models.CharField(max_length=15, blank=True) 

    class Meta:
        db_table = "verification_logs"

class Messages(models.Model): ## OK
    #id = models.CharField(primary_key=True, default=generate_pk("MS"), editable=False, max_length=12, unique=True)
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    camera = models.ForeignKey(Cameras, on_delete=models.CASCADE)
    content = models.CharField(max_length=255)
    created_date = models.DateTimeField(blank=False, default=datetime.now)

    class Meta:
        db_table = "messages"

class MessageRecipients(models.Model): ## OK
    #id = models.CharField(primary_key=True, default=generate_pk("MR"), editable=False, max_length=12, unique=True)
    recipient = models.ForeignKey(Users, on_delete=models.CASCADE)
    camera = models.ForeignKey(Cameras, on_delete=models.CASCADE)
    is_read = models.BooleanField(default=False)

    class Meta:
        db_table = "message_recipients"

class UserForAdminPage(models.Model):
    full_name = models.CharField(max_length=30)
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=15)
    free = models.CharField(max_length=100)
    password = models.CharField(max_length=30)
    password_confirmation = models.CharField(max_length=30)
    phone_number = models.PositiveIntegerField(blank=False)

    USERNAME_FIELD = 'full_name' ## Biar kursornya keatas
    REQUIRED_FIELDS = ['full_name', 'email', 'username', 'password', 'phone_number']
    class Meta:
        db_table = "helper"   