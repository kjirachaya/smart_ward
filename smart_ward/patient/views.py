from django.http import HttpResponse
from django.template import loader
from .models import Patient, Telemetry, OperatorUser, Ward, Bed, User
from datetime import datetime, timedelta
from django.core.serializers import serialize
from django.core.serializers.json import DjangoJSONEncoder
import json
from rest_framework import generics
from .serializers import TelemetrySerializer, PatientSerializer, OperatorSerializer, BedSerializer
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import redis
from django.core import serializers
from django.utils import timezone
import pytz
from django.conf import settings
from django.utils.timezone import make_aware
import socketio
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
import csv

sio = socketio.Server(async_mode=None, client_manager=socketio.RedisManager("redis://127.0.0.1:6379"))

def home(request):
  template = loader.get_template('index.html')
  return HttpResponse(template.render())

def checkLogin(request, page, context):
    if request.user.is_authenticated == False:
        return redirect("/login?next=" + page)

    return render(request, page, context) 

def print_form31(request):
    if request.user.is_authenticated == False:
      return redirect("login")
    # Create the HttpResponse object with the appropriate CSV header.
    date_display = datetime.now().strftime('%Y-%m-%d-%H:%M:%S')
    file_name = "form-31-" + date_display + ".csv"
    response = HttpResponse(
        content_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="' + file_name +'"'},
    )

    default_datetime = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    if (request.GET.get('hn_number') == None):
      return
    if request.GET.get('since_date_input') != None:
      start_date = datetime.strptime(request.GET.get('since_date_input'), "%Y-%m-%d")
    else:
      start_date = default_datetime - timedelta(days=7)
    if request.GET.get('to_date_input') != None:
      end_date = datetime.strptime(request.GET.get('to_date_input'), "%Y-%m-%d")
    else:
      end_date = default_datetime
    
    signals_within_date_range = Telemetry.objects.filter(patient_id=request.GET.get('hn_number'), create_at__date__range=[start_date, end_date])
    patient = Patient.objects.filter(hn_number=request.GET.get('hn_number'))

    writer = csv.writer(response)
    writer.writerow(["Name", patient[0].firstname])
    writer.writerow(["HN Number", patient[0].hn_number])
    writer.writerow(["Date Time", "BP", "T.", "P.", "R.", "O2Sat", "Remark"])
    for item in signals_within_date_range.values():
       create_at_value = item['create_at']
       time_display = item['create_at']
       if isinstance(create_at_value, datetime):
         time_display = item['create_at'].strftime("%m/%d/%Y, %H:%M:%S")
       writer.writerow([time_display, item['bp_systolic'], item['temp'], item['pulse'], item['respirations'], item['o2_sat'], item['remark']])

    return response

def print_form70(request):
    if request.user.is_authenticated == False:
      return redirect("login")
    # Create the HttpResponse object with the appropriate CSV header.
    date_display = datetime.now().strftime('%Y-%m-%d-%H:%M:%S')
    file_name = "form-31-" + date_display + ".csv"
    response = HttpResponse(
        content_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="' + file_name +'"'},
    )

    default_datetime = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    if (request.GET.get('hn_number') == None):
      return
    if request.GET.get('since_date_input') != None:
      start_date = datetime.strptime(request.GET.get('since_date_input'), "%Y-%m-%d")
    else:
      start_date = default_datetime - timedelta(days=7)
    if request.GET.get('to_date_input') != None:
      end_date = datetime.strptime(request.GET.get('to_date_input'), "%Y-%m-%d")
    else:
      end_date = default_datetime
    
    signals_within_date_range = Telemetry.objects.filter(patient_id=request.GET.get('hn_number'), create_at__date__range=[start_date, end_date])
    patient = Patient.objects.filter(hn_number=request.GET.get('hn_number'))

    writer = csv.writer(response)
    writer.writerow(["Name", patient[0].firstname])
    writer.writerow(["HN Number", patient[0].hn_number])
    writer.writerow(["TIME", ])
    writer.writerow(["Date Time", "BP", "T.", "P.", "R.", "O2Sat", "Remark"])
    for item in signals_within_date_range.values():
       create_at_value = item['create_at']
       time_display = item['create_at']
       if isinstance(create_at_value, datetime):
         time_display = item['create_at'].strftime("%m/%d/%Y, %H:%M:%S")
       writer.writerow([time_display, item['bp_systolic'], item['temp'], item['pulse'], item['respirations'], item['o2_sat'], item['remark']])

    return response

def operatorUsers(request):
  if request.user.is_authenticated == False:
    return redirect("login")
  template = loader.get_template('users.html')
  users = User.objects.filter(groups__name='operator')
  context = {
    'users': users,
  }
  print(users.values())
  return HttpResponse(template.render(context, request))

def beds(request):
  if request.user.is_authenticated == False:
    return redirect("login")
  template = loader.get_template('beds.html')
  beds = Bed.objects.all().values()
  bed_items = []
  for bed in beds:
    bed_items.append(convertToJson(bed))
  context = {
    'bed_items': bed_items,
    'bed_count': len(beds),
  }
  print(bed_items)
  return HttpResponse(template.render(context, request))

def addBed(request):
  print(request)
  if request.method == 'POST':
    print(request.POST)
    data = request.POST
    input_bed_id = data['input-bed-id']
    print(input_bed_id)
    bed_instance = Bed.objects.create(bed_id=input_bed_id)
    sio.emit("update_bed", "update_bed", room="bed")
  
  return redirect("/patients/beds")

def wardAddPatient(request):
  if request.user.is_authenticated == False:
    return redirect("login")
  if request.method == 'POST':
    data = request.POST
    input_hn_number = data['input-hn-number']
    input_bed_id = data['input-bed-id']
    print(input_hn_number)
    print(input_bed_id)
    bed = get_object_or_404(Bed, bed_id=input_bed_id)
    patient = get_object_or_404(Patient, hn_number=input_hn_number)
    print(patient.bed_id)
    if (patient.bed_id != None):
      bed.save()
    else:
      bed.patient_id = patient.id
      bed.save()
      patient.bed_id = bed.bed_id
      patient.save()
  
  return redirect("/patients/ward")

def wardRemovePatient(request):
  if request.user.is_authenticated == False:
    return redirect("login")
  if request.method == 'POST':
    data = request.POST
    input_bed_id = data['input-bed-id']
    print(input_bed_id)
    # Retrieve the model instance based on the bed_id
    bed = get_object_or_404(Bed, bed_id=input_bed_id)
    patient_id = bed.patient_id
    patient = get_object_or_404(Patient, id=patient_id)
    patient.bed_id = None
    patient.save()

        # Update the attribute of the model instance
    bed.patient_id = None
    bed.save()
  
  return redirect("/patients/ward")

def ward(request):
  if request.user.is_authenticated == False:
    return redirect("login")
  is_list_view = False
  template = loader.get_template('ward.html')
  if (request.GET.get('is_list_view') != None):
    if (request.GET.get('is_list_view') == "1"):
      is_list_view = True
  
  if is_list_view == False:
    bed_items = []
    beds = Bed.objects.all().values()
    print(beds)
    for bed in beds:
      bed_items.append(convertToJson(bed))

    context = {
      'bed_items': bed_items,
      'is_list_view': is_list_view,
    }
    print(context)
    return HttpResponse(template.render(context, request))
  else:
    patients = Patient.objects.all().values()
    context = {
      'patient_items': patients,
      'is_list_view': is_list_view,
    }
    print(context)
    return HttpResponse(template.render(context, request))

def wardForm70(request):
  if request.user.is_authenticated == False:
    return redirect("login")
  template = loader.get_template('form_70.html')
  default_datetime = datetime.now(tz=timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
  if (request.GET.get('hn_number') == None):
    start_date = default_datetime - timedelta(days=7)
    end_date = default_datetime
    context = {
      'start_date': start_date,
      'end_date': end_date,
      'size_of_telemetry_date_items': 0,
      'set_of_hr': [],
      'size_of_hr': 0,
      'telemetry_date_items': [],
      'temp_date_items': json.dumps(None),
      'pulse_date_items': json.dumps(None),
    }
    return HttpResponse(template.render(context, request))
  if request.GET.get('since_date_input') != None:
    start_date = datetime.strptime(request.GET.get('since_date_input'), "%Y-%m-%d")
  else:
    start_date = default_datetime - timedelta(days=7)
  if request.GET.get('to_date_input') != None:
    end_date = datetime.strptime(request.GET.get('to_date_input'), "%Y-%m-%d")
  else:
    end_date = default_datetime

  signals_within_date_range = Telemetry.objects.filter(patient_id=request.GET.get('hn_number'), create_at__date__range=[start_date, end_date])
  
  patient = Patient.objects.filter(hn_number=request.GET.get('hn_number'))
  data = list(patient.values())

  # Serialize datetime fields to strings
  for item in data:
    if 'create_at' in item:
      create_at_value = item['create_at']
      if isinstance(create_at_value, datetime):
        item['create_at'] = create_at_value.strftime('%Y-%m-%d %H:%M:%S')

  if data != None and data[0] != None:
    patient = data[0]
  else:
    patient = None
  
  current_date = start_date + timedelta(hours=2)
  interval = 4 # hr
  diffTime = timedelta(hours=interval)
  telemetryDateItems = []
  tempDateItems = []
  pulseDateItems = []
  setOfHr = set()
  telemetryDateItems = []
  telemetryTempDataItems = []
  while current_date <= (end_date + timedelta(days=1)):

    settings.TIME_ZONE  # 'UTC'
    telemetrys = signals_within_date_range.filter(patient_id=request.GET.get('hn_number'), create_at__range=[current_date - timedelta(hours=interval), current_date])

    setOfHr.add(current_date.strftime("%H"))
    hour = current_date.strftime("%H")
    if (hour.startswith("0")):
      hour = hour.strip('0')
    if (len(telemetrys) > 0):
        
      telemetryTempDataItems.append(
        {
          "date": current_date.strftime("%m/%d/%Y, %H:%M:%S"),
          "date_display": current_date.strftime("%d/%m/%Y"),
          "value": telemetrys.values().reverse()[0],
          "hr": hour,
        }
      )
      tempDateItems.append({
        "key": current_date.strftime("%H"),
        "data": telemetrys.values().reverse()[0]['temp']
        })
      pulseDateItems.append({
        "key": current_date.strftime("%H"),
        "data": telemetrys.values().reverse()[0]['pulse']
        })
    else:
      telemetryTempDataItems.append(
        {
          "date": current_date.strftime("%m/%d/%Y, %H:%M:%S"),
          "date_display": current_date.strftime("%d/%m/%Y"),
          "value": None,
          "hr": hour,
        }
      )
      tempDateItems.append({
        "key": current_date.strftime("%H"), 
        "data": ""})
      pulseDateItems.append({
        "key": current_date.strftime("%H"), 
        "data": ""})
    
    if ((current_date + timedelta(hours=interval)).day != current_date.day):
      telemetryDateItems.append({
        "date_display": current_date.strftime("%d/%m/%Y"),
        "telemetry": telemetryTempDataItems, 
      })
      telemetryTempDataItems = []
    
    telemetrys = []
    current_date += diffTime

  telemetryDateItems.reverse()
  tempDateItems.reverse()
  pulseDateItems.reverse()
  widthTemp = len(telemetryDateItems) * len(setOfHr)
  context = {
    'hn_number': request.GET.get('hn_number'),
    'signals_within_date_range': signals_within_date_range,
    'start_date': start_date,
    'end_date': end_date,
    'patient': patient,
    'telemetry_date_items': telemetryDateItems,
    'temp_date_items': json.dumps(tempDateItems),
    'pulse_date_items': json.dumps(pulseDateItems),
    'set_of_hr': setOfHr,
    'size_of_hr': len(setOfHr),
    'size_of_telemetry_date_items': widthTemp,
    'width_px': (35*widthTemp) + 59,
    'width_table_px': 35*len(setOfHr),
  }
  return HttpResponse(template.render(context, request))

def wardForm31(request):
  if request.user.is_authenticated == False:
    return redirect("login")
  template = loader.get_template('form_31.html')
  default_datetime = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
  if (request.GET.get('hn_number') == None):
    start_date = default_datetime - timedelta(days=7)
    end_date = default_datetime
    context = {
      'start_date': start_date,
      'end_date': end_date,
    }
    return HttpResponse(template.render(context, request))
  if request.GET.get('since_date_input') != None:
    start_date = datetime.strptime(request.GET.get('since_date_input'), "%Y-%m-%d")
  else:
    start_date = default_datetime - timedelta(days=7)
  if request.GET.get('to_date_input') != None:
    end_date = datetime.strptime(request.GET.get('to_date_input'), "%Y-%m-%d")
  else:
    end_date = default_datetime
    
  signals_within_date_range = Telemetry.objects.filter(patient_id=request.GET.get('hn_number'), create_at__date__range=[start_date, end_date])
  patient = Patient.objects.filter(hn_number=request.GET.get('hn_number'))
  data = list(patient.values())

  for item in data:
    if 'create_at' in item:
      create_at_value = item['create_at']
      if isinstance(create_at_value, datetime):
        item['create_at'] = create_at_value.strftime('%Y-%m-%d %H:%M:%S')

  if data != None and data[0] != None:
    patient = data[0]
  else:
    patient = None

  context = {
    'hn_number': request.GET.get('hn_number'),
    'signals_within_date_range': signals_within_date_range,
    'start_date': start_date,
    'end_date': end_date,
    'patient': patient,
  }
  return HttpResponse(template.render(context, request))

def convertToJson(bed):
  print(bed)
  json = {}
  patientObject = Patient.objects.filter(id=bed['patient_id']).values()
  _patient = {}
  for patient in patientObject:
    _patient = {
      'id': patient['id'],
      'hn_number': patient['hn_number']
    }
  json = {
    'bed_id': bed['bed_id'],
    'patient': _patient
  }
  print(json)
  return json

class PatientDetailView(generics.RetrieveAPIView):
  queryset = Patient.objects.all()
  serializer_class = PatientSerializer
  lookup_field = 'hn_number'

## for ForeignKey

# class YourModelCreateView(generics.CreateAPIView):
#     queryset = YourModel.objects.all()
#     serializer_class = YourModelSerializer

#     def perform_create(self, serializer):
#         related_model_data = self.request.data.get('related_model')  # Get data for the related model
#         # Additional actions can be performed here, such as creating the related object
#         # or performing any necessary processing before creating the main object
#         related_model_instance = RelatedModel.objects.create(**related_model_data)
#         serializer.save(related_model=related_model_instance)

class OperatorDetailView(generics.RetrieveAPIView):
  queryset = OperatorUser.objects.all()
  serializer_class = OperatorSerializer

  def get_queryset(self):
        queryset = self.queryset
        params = self.request.query_params
        # Filter queryset based on query parameters
        if 'staff_id' in params:
            queryset = queryset.filter(id=params['staff_id'])
        if 'first_name' in params:
            queryset = queryset.filter(username=params['first_name'])
        if 'last_name' in params:
            queryset = queryset.filter(email=params['last_name'])
        # Add more filters for other parameters as needed
        return queryset


class TelemetryListCreate(generics.ListCreateAPIView):
    queryset = Telemetry.objects.all()
    serializer_class = TelemetrySerializer

    def perform_create(self, serializer):
        instance = serializer.save(create_at=timezone.now())
        patient_id = serializer.data['patient_id']
        sio.emit("update_form70", patient_id, room="form70")
        sio.emit("update_form31", patient_id, room="form31")

class TelemetryRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = Telemetry.objects.all()
    serializer_class = TelemetrySerializer

def patients(request):
  patients = Patient.objects.all().values()
  print(patients)
  template = loader.get_template('patients_list.html')
  context = {
    'patients': patients,
  }
  return HttpResponse(template.render(context, request))

# def form70(request):
#   template = loader.get_template('patients_form_70.html')
#   default_datetime = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
#   print(request.GET)
#   if (request.GET.get('hn_number') == None):
#     start_date = default_datetime - timedelta(days=7)
#     end_date = default_datetime
#     context = {
#       'start_date': start_date,
#       'end_date': end_date,
#     }
#     print(context)
#     return HttpResponse(template.render(context, request))
#   if request.GET.get('since_date_input') != None:
#     start_date = datetime.strptime(request.GET.get('since_date_input'), "%d %b %Y")
#   else:
#     start_date = default_datetime - timedelta(days=7)
#   if request.GET.get('to_date_input') != None:
#     end_date = datetime.strptime(request.GET.get('to_date_input'), "%d %b %Y")
#   else:
#     end_date = default_datetime
#   print(start_date)
#   signals_within_date_range = Telemetry.objects.filter(patient_id=request.GET.get('hn_number'), create_at__date__range=[start_date, end_date])
#   # Retrieve time series data from your database or other source
#   # print(signals_within_date_range.values())
#   # Define the step size (4 hour in this case)
#   step4 = timedelta(hours=4)
#   step8 = timedelta(hours=8)
#   step12 = timedelta(hours=12)
#   step16 = timedelta(hours=16)
#   step24 = timedelta(hours=24-1)

#   current_date = start_date
#   temp_time_series_data = []
#   pulse_time_series_data = []
#   time_series_data_4_hour = []
#   while current_date <= (end_date + timedelta(days=1)):
#     print(current_date.strftime("%Y-%m-%d %H:%M:%S"))  # Print the date and time
#     dataIn4Hour = signals_within_date_range.filter(
#       create_at__date__range=[current_date.date(), current_date.date()],  # Filter by date range
#       create_at__hour__range=[current_date.hour, current_date.hour + 3],
#       create_at__minute__range=[0, 59]).values()
#     if (current_date + step4) <= (end_date + timedelta(days=1)):
#       if dataIn4Hour:
#         # Convert queryset data to a list of dictionaries
#         # print(dataIn4Hour.last())
#         # data = list(dataIn4Hour)

#         # # Serialize datetime fields to strings
#         # for item in data:
#         #   if 'create_at' in item:
#         #     create_at_value = item['create_at']
#         #     if isinstance(create_at_value, datetime):
#         #       item['create_at'] = create_at_value.strftime('%Y-%m-%d %H:%M:%S')

#         # Convert the list of dictionaries to JSON
#         # json_data = json.dumps(data[0], cls=DjangoJSONEncoder)
#         time_series_data_4_hour.append({
#           'current_date': current_date.strftime("%Y-%m-%d"), 
#           'hour': current_date.hour + 2,
#           'value': dataIn4Hour.last(),
#         })
#         for signal in signals_within_date_range:
#           print(signal.temp)
#           temp_time_series_data.append((current_date, signal.temp))
#           pulse_time_series_data.append((current_date, signal.pulse))
#       else:
#         time_series_data_4_hour.append({
#           'current_date': current_date.strftime("%Y-%m-%d"), 
#           'hour': current_date.hour + 2,
#           'value': None,
#         })
#         temp_time_series_data.append((current_date, None))
#         pulse_time_series_data.append((current_date, None))
#     current_date += step4

#   current_date = start_date
#   time_series_data_8_hour = []
#   while current_date <= (end_date + timedelta(days=1)):
#     print(current_date.strftime("%Y-%m-%d %H:%M:%S"))  # Print the date and time
#     dataIn8Hour = signals_within_date_range.filter(
#       create_at__date__range=[current_date.date(), current_date.date()],  # Filter by date range
#       create_at__hour__range=[current_date.hour, current_date.hour + 7],
#       create_at__minute__range=[0, 59]).values()
#     if (current_date + step8) <= (end_date + timedelta(days=1)):
#       if dataIn8Hour:
#         # data = list(dataIn8Hour)

#         # for item in data:
#         #   if 'create_at' in item:
#         #     create_at_value = item['create_at']
#         #     if isinstance(create_at_value, datetime):
#         #       item['create_at'] = create_at_value.strftime('%Y-%m-%d %H:%M:%S')

#         time_series_data_8_hour.append({
#           'current_date': current_date.strftime("%Y-%m-%d"), 
#           'hour': current_date.hour + 2,
#           'value': dataIn8Hour.last(),
#         })
#       else:
#         time_series_data_8_hour.append({
#           'current_date': current_date.strftime("%Y-%m-%d"), 
#           'hour': current_date.hour + 2,
#           'value': None,
#         })
#     current_date += step8

#   current_date = start_date
#   time_series_data_12_hour = []
#   while current_date <= (end_date + timedelta(days=1)):
#     print(current_date.strftime("%Y-%m-%d %H:%M:%S"))  # Print the date and time
#     dataIn12Hour = signals_within_date_range.filter(
#       create_at__date__range=[current_date.date(), current_date.date()],  # Filter by date range
#       create_at__hour__range=[current_date.hour, current_date.hour + 11],
#       create_at__minute__range=[0, 59]).values()
#     if (current_date + step12) <= (end_date + timedelta(days=1)):
#       if dataIn12Hour:
#         # data = list(dataIn12Hour)

#         # for item in data:
#         #   if 'create_at' in item:
#         #     create_at_value = item['create_at']
#         #     if isinstance(create_at_value, datetime):
#         #       item['create_at'] = create_at_value.strftime('%Y-%m-%d %H:%M:%S')

#         time_series_data_12_hour.append({
#           'current_date': current_date.strftime("%Y-%m-%d"), 
#           'hour': current_date.hour + 2,
#           'value': dataIn12Hour.last(),
#         })
#       else:
#         time_series_data_12_hour.append({
#           'current_date': current_date.strftime("%Y-%m-%d"), 
#           'hour': current_date.hour + 2,
#           'value': None,
#         })
#     current_date += step12

#   current_date = start_date
#   time_series_data_16_hour = []
#   while current_date <= (end_date + timedelta(days=1)):
#     print(current_date.strftime("%Y-%m-%d %H:%M:%S"))  # Print the date and time
#     dataIn16Hour = signals_within_date_range.filter(
#       create_at__date__range=[current_date.date(), current_date.date()],  # Filter by date range
#       create_at__hour__range=[current_date.hour, current_date.hour + 15],
#       create_at__minute__range=[0, 59]).values()
#     if (current_date + step16) <= (end_date + timedelta(days=1)):
#       if dataIn16Hour:
#         # data = list(dataIn16Hour)

#         # for item in data:
#         #   if 'create_at' in item:
#         #     create_at_value = item['create_at']
#         #     if isinstance(create_at_value, datetime):
#         #       item['create_at'] = create_at_value.strftime('%Y-%m-%d %H:%M:%S')

#         time_series_data_16_hour.append({
#           'current_date': current_date.strftime("%Y-%m-%d"), 
#           'hour': current_date.hour + 2,
#           'value': dataIn16Hour.last(),
#         })
#       else:
#         time_series_data_16_hour.append({
#           'current_date': current_date.strftime("%Y-%m-%d"), 
#           'hour': current_date.hour + 2,
#           'value': None,
#         })
#     current_date += step16


#   temp_time_series_data_iso = [(dt.strftime('%Y-%m-%dT%H:%M:%S'), value) for dt, value in temp_time_series_data]
#   temp_time_series_data_json = json.dumps(temp_time_series_data_iso)

#   pulse_time_series_data_iso = [(dt.strftime('%Y-%m-%dT%H:%M:%S'), value) for dt, value in pulse_time_series_data]
#   pulse_time_series_data_json = json.dumps(pulse_time_series_data_iso)

#   patient = Patient.objects.filter(hn_number=request.GET.get('hn_number'))
#   data = list(patient.values())

#   # Serialize datetime fields to strings
#   for item in data:
#     if 'create_at' in item:
#       create_at_value = item['create_at']
#       if isinstance(create_at_value, datetime):
#         item['create_at'] = create_at_value.strftime('%Y-%m-%d %H:%M:%S')

#   if data[0] is None:
#     # data[0] is null (None)
#     # print("data[0] is null")
#     patient = None
#   else:
#     # data[0] is not null
#     patient = data[0],
#     # print("data[0] is not null")

#   context = {
#     'hn_number': request.GET.get('hn_number'),
#     'time_series_data_4_hour': time_series_data_4_hour,
#     'time_series_data_8_hour': time_series_data_8_hour,
#     'time_series_data_12_hour': time_series_data_12_hour,
#     'time_series_data_16_hour': time_series_data_16_hour,
#     'temp_time_series_data_json': temp_time_series_data_json,
#     'pulse_time_series_data_json': pulse_time_series_data_json,
#     'start_date': start_date,
#     'end_date': end_date,
#     'patient': patient,
#   }
#   return HttpResponse(template.render(context, request))

# def form31(request):
#   template = loader.get_template('patients_form_31.html')
#   default_datetime = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
#   print(request.GET)
#   if (request.GET.get('hn_number') == None):
#     start_date = default_datetime - timedelta(days=7)
#     end_date = default_datetime
#     context = {
#       'start_date': start_date,
#       'end_date': end_date,
#     }
#     print(context)
#     return HttpResponse(template.render(context, request))
#   if request.GET.get('since_date_input') != None:
#     start_date = datetime.strptime(request.GET.get('since_date_input'), "%d %b %Y")
#   else:
#     start_date = default_datetime - timedelta(days=7)
#   if request.GET.get('to_date_input') != None:
#     end_date = datetime.strptime(request.GET.get('to_date_input'), "%d %b %Y")
#   else:
#     end_date = default_datetime
    
#   # Filter data records within the specified date range
#   signals_within_date_range = Telemetry.objects.filter(patient_id=request.GET.get('hn_number'), create_at__date__range=[start_date, end_date])
#   print(signals_within_date_range)
#   patient = Patient.objects.filter(hn_number=request.GET.get('hn_number'))
#   data = list(patient.values())

#   # Serialize datetime fields to strings
#   for item in data:
#     if 'create_at' in item:
#       create_at_value = item['create_at']
#       if isinstance(create_at_value, datetime):
#         item['create_at'] = create_at_value.strftime('%Y-%m-%d %H:%M:%S')

#   print(data)
#   if data and data[0] is None:
#     # data[0] is null (None)
#     # print("data[0] is null")
#     patient = data[0]
#   else:
#     # data[0] is not null
#     patient = None
    
#     # print("data[0] is not null")

#   context = {
#     'hn_number': request.GET.get('hn_number'),
#     'signals_within_date_range': signals_within_date_range,
#     'start_date': start_date,
#     'end_date': end_date,
#     'patient': patient,
#   }
#   print("context")
#   print(context)
#   return HttpResponse(template.render(context, request))

# from rest_framework.generics import GenericAPIView
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.response import Response
# from rest_framework import status
# from .serializers import ChatSerializer
# from .models import Chat



# class GetChat(GenericAPIView):
#     permission_classes = [IsAuthenticated]
#     serializer_class = ChatSerializer

#     def get(self, request):
#         # chat, created = Chat.objects.get_or_create(initiator__id=request.user.pk)
#         # serializer = self.serializer_class(instance=chat)
#         # return Response({"message": "Chat gotten", "data": serializer.data}, status=status.HTTP_200_OK)
#         return Response({"message": "Chat gotten", "data": "Hello"}, status=status.HTTP_200_OK)
