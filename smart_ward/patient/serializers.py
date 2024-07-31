from rest_framework import serializers
from .models import Telemetry, Patient, OperatorUser, Bed

class TelemetrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Telemetry
        exclude = ['create_at']

class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ['firstname', 'lastname', 'hn_number']  # Include fields as needed
        read_only_fields = ['hn_number']  # Make sure hn_number is read-only

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
