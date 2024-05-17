import json
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

class OperatorUserManager(BaseUserManager):
    def create_user(self, email, password=None):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
        user = self.create_user(email=email, password=password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

class OperatorUser(AbstractBaseUser):
    username = models.CharField(unique=True, max_length=20)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    staff_id = models.CharField(max_length=255)

    
    objects = OperatorUserManager()

    USERNAME_FIELD = 'username'

    def get_full_name(self):
        return self.first_name + ' ' + self.last_name

    def get_short_name(self):
        return self.username


class Patient(models.Model):
#   user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
  id = models.AutoField(primary_key=True)
  firstname = models.CharField(max_length=255)
  lastname = models.CharField(max_length=255)
  hn_number = models.CharField(max_length=5, unique=True, default='00000', null=True)
  bed_id = models.CharField(max_length=255, null=True, blank=True)
  id_card = models.CharField(max_length=13, default="", null=True, blank=True)
#   groups = models.ManyToManyField('auth.Group', related_name='patient_groups')

  def save(self, *args, **kwargs):
        if not self.pk:  # If the object is being created for the first time
            # Get the highest existing hn_number, if any
            last_patient = Patient.objects.order_by('-hn_number').first()
            if last_patient:
                last_hn_number = int(last_patient.hn_number)
                new_hn_number = str(last_hn_number + 1).zfill(5)  # Increment and pad with zeros
            else:
                new_hn_number = '00001'  # If there are no existing patients, start with '00001'
            self.hn_number = new_hn_number
        super().save(*args, **kwargs)

# class Operator(models.Model):
#     # user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
#     first_name = models.CharField(max_length=255)
#     last_name = models.CharField(max_length=255)
#     staff_id = models.CharField(max_length=255)
#     # groups = models.ManyToManyField('auth.Group', related_name='operator_groups')

#     def __str__(self) -> str:
#         return super().__str__()

class Telemetry(models.Model):
    patient_id = models.CharField(max_length=255)
    temp = models.CharField(max_length=255, blank=True)
    pulse = models.CharField(max_length=255, blank=True)
    respirations = models.CharField(max_length=255, blank=True)
    bp_systolic = models.CharField(max_length=255, blank=True)
    bp_diastolic = models.CharField(max_length=255, blank=True)
    map = models.CharField(max_length=255, blank=True)
    o2_sat = models.CharField(max_length=255, blank=True)
    pain_score = models.CharField(max_length=255, blank=True)
    height_of_fundus = models.CharField(max_length=255, blank=True)
    weight = models.CharField(max_length=255, blank=True)
    hight = models.CharField(max_length=255, blank=True)
    diet = models.CharField(max_length=255, blank=True)
    urination = models.CharField(max_length=255, blank=True)
    defecations = models.CharField(max_length=255, blank=True)
    intake_oral = models.CharField(max_length=255, blank=True)
    intake_parenteral = models.CharField(max_length=255, blank=True)
    intake_total = models.CharField(max_length=255, blank=True)
    output_urine = models.CharField(max_length=255, blank=True)
    output_emesis = models.CharField(max_length=255, blank=True)
    output_total = models.CharField(max_length=255, blank=True)
    total_intake = models.CharField(max_length=255, blank=True)
    total_output = models.CharField(max_length=255, blank=True)
    lochia = models.CharField(max_length=255, blank=True)
    phlebitis = models.CharField(max_length=255, blank=True)
    mews = models.CharField(max_length=255, blank=True)
    pps = models.CharField(max_length=255, blank=True)
    note = models.CharField(max_length=255, blank=True)
    create_at = models.DateTimeField(auto_now_add=True)
    atb = models.CharField(max_length=255, blank=True)
    remark = models.CharField(max_length=255, blank=True)
    measurement_time = models.DateTimeField(null=True)
    operator_id = models.CharField(max_length=255, null=True)
    # operator_by = models.ForeignKey(Operator, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.patient_id
    
class StringItem(models.Model):
    value = models.CharField(max_length=100)

    def __str__(self):
        return self.value
    
class Bed(models.Model):
    bed_id = models.CharField(max_length=255, unique=True)
    patient_id = models.CharField(max_length=255, null=True, blank=True)
    active = models.BooleanField(default=False)

class Ward(models.Model):
    ward_id = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    bed_list = models.CharField(max_length=200, default='[]')

    def set_bed_list(self, x):
        self.bed_list = json.dumps(x)

    def get_bed_list(self):
        return json.loads(self.bed_list)

from django.contrib.auth.models import User
import uuid
from django.utils import timezone


class Chat(models.Model):
    initiator = models.ForeignKey(
        User, on_delete=models.DO_NOTHING, related_name="initiator_chat"
    )
    acceptor = models.ForeignKey(
        User, on_delete=models.DO_NOTHING, related_name="acceptor_name"
    )
    short_id = models.CharField(max_length=255, default=uuid.uuid4, unique=True)


class ChatMessage(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    text = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)