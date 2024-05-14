from django.contrib import admin
from .models import Patient, Telemetry, OperatorUser, Bed, Ward, Chat, ChatMessage

# Register your models here.
admin.site.register(Patient)
admin.site.register(Telemetry)
admin.site.register(OperatorUser)
admin.site.register(Bed)
admin.site.register(Ward)
admin.site.register(Chat)
admin.site.register(ChatMessage)
