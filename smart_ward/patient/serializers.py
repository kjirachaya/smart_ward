from rest_framework import serializers
from .models import Telemetry, Patient, OperatorUser, Bed

class TelemetrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Telemetry
        exclude = ['create_at']

class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = '__all__'

class OperatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = OperatorUser
        fields = '__all__'

class BedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bed
        fields = '__all__'

from rest_framework import serializers
from .models import Chat, ChatMessage


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        exclude = ("chat",)


class ChatSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    class Meta:
        model = Chat
        fields = ["messages", "short_id"]
