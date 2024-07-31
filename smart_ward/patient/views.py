from django.http import HttpResponse, JsonResponse, Http404
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
from django.utils.html import format_html

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
      'is_admin': request.user.is_superuser,
    }
    print(context)
    return HttpResponse(template.render(context, request))

def wardForm70(request):
  if request.user.is_authenticated == False:
    return redirect("login")
  template = loader.get_template('form_70.html')
  default_datetime = datetime.now(tz=timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
  if (request.GET.get('hn_number') == None):
    start_date = default_datetime - timedelta(days=2)
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
    start_date = default_datetime - timedelta(days=2)
  if request.GET.get('to_date_input') != None:
    end_date = datetime.strptime(request.GET.get('to_date_input'), "%Y-%m-%d")
  else:
    end_date = default_datetime

  signals_within_date_range = Telemetry.objects.filter(patient_id=request.GET.get('hn_number'), measurement_time__date__range=[start_date, end_date])
  
  patient = Patient.objects.filter(hn_number=request.GET.get('hn_number'))
  data = list(patient.values())

  # Serialize datetime fields to strings
  for item in data:
    if 'measurement_time' in item:
      create_at_value = item['measurement_time']
      if isinstance(create_at_value, datetime):
        item['measurement_time'] = create_at_value.strftime('%Y-%m-%d %H:%M:%S')

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
    telemetrys = signals_within_date_range.filter(patient_id=request.GET.get('hn_number'), measurement_time__range=[current_date - timedelta(hours=interval), current_date])

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

  # telemetryDateItems.reverse()
  # tempDateItems.reverse()
  # pulseDateItems.reverse()
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
    
  signals_within_date_range = Telemetry.objects.filter(patient_id=request.GET.get('hn_number'), measurement_time__date__range=[start_date, end_date]).order_by('-measurement_time')
  patient = Patient.objects.filter(hn_number=request.GET.get('hn_number'))
  data = list(patient.values())

  for item in data:
    if 'measurement_time' in item:
      create_at_value = item['measurement_time']
      if isinstance(create_at_value, datetime):
        item['measurement_time'] = create_at_value.strftime('%Y-%m-%d %H:%M:%S')

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

class OperatorDetailView(generics.RetrieveAPIView):
  queryset = OperatorUser.objects.all()
  serializer_class = OperatorSerializer
  lookup_field = 'staff_id'

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
    
def add_patient_to_db(request):
	if request.user.is_authenticated == False:
		return redirect("login")
	if request.method == 'POST':
		data = request.POST
		hn_number = data['input_hn_number']
		first_name = data['firstname']
		last_name = data['lastname']
		id_card = data['id_card']

		 # Example data
		patient_data = {
        	'firstname': first_name,
        	'lastname': last_name,
        	'hn_number': hn_number,
           'id_card': id_card
    	}
    
		create_or_get_patient(**patient_data)
    
		return redirect('/patients/ward?is_list_view=1')
              
def create_or_get_patient(**kwargs):
    try:
        # Attempt to create a new patient or get the existing one
        patient, created = Patient.objects.get_or_create(**kwargs)
        return patient, created
    except Patient.DoesNotExist:
        raise Http404("Patient not found")

def patients(request):
  patients = Patient.objects.all().values()
  print(patients)
  template = loader.get_template('patients_list.html')
  context = {
    'patients': patients,
  }
  return HttpResponse(template.render(context, request))

def get_form70_graph(request):
    #if request.user.is_authenticated == False:
    #  return JsonResponse({'error': 'Required Login'}, status=400)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Get the latest log entry for each device
        default_datetime = datetime.now(tz=timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        if (request.GET.get('hn_number') == None):
          start_date = default_datetime - timedelta(days=2)
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
          return JsonResponse({'error': 'Required HN Number'}, status=400)
        if request.GET.get('since_date_input') != None:
          start_date = datetime.strptime(request.GET.get('since_date_input'), "%Y-%m-%d")
        else:
          start_date = default_datetime - timedelta(days=2)
        if request.GET.get('to_date_input') != None:
          end_date = datetime.strptime(request.GET.get('to_date_input'), "%Y-%m-%d")
        else:
          end_date = default_datetime

        signals_within_date_range = Telemetry.objects.filter(patient_id=request.GET.get('hn_number'), measurement_time__date__range=[start_date, end_date])
  
        patient = Patient.objects.filter(hn_number=request.GET.get('hn_number'))
        data = list(patient.values())

        # Serialize datetime fields to strings
        for item in data:
          if 'measurement_time' in item:
            create_at_value = item['measurement_time']
            if isinstance(create_at_value, datetime):
              item['measurement_time'] = create_at_value.strftime('%Y-%m-%d %H:%M:%S')

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
          telemetrys = signals_within_date_range.filter(patient_id=request.GET.get('hn_number'), measurement_time__range=[current_date - timedelta(hours=interval), current_date])

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

        # telemetryDateItems.reverse()
        # tempDateItems.reverse()
        # pulseDateItems.reverse()
        widthTemp = len(telemetryDateItems) * len(setOfHr)
        context = {
          # 'hn_number': request.GET.get('hn_number'),
          # 'start_date': start_date,
          # 'end_date': end_date,
          # 'patient': patient,
          'telemetry_date_items': telemetryDateItems,
          'temp_date_items': json.dumps(tempDateItems),
          'pulse_date_items': json.dumps(pulseDateItems),
          # 'set_of_hr': setOfHr,
          # 'size_of_hr': len(setOfHr),
          # 'size_of_telemetry_date_items': widthTemp,
          # 'width_px': (35*widthTemp) + 59,
          # 'width_table_px': 35*len(setOfHr),
        }
        print(context)
        return JsonResponse(context, safe=False)
    else:
        return JsonResponse({'error': 'This endpoint only accepts AJAX requests.'}, status=400)
    
def get_form31_data(request):
	if request.headers.get('x-requested-with') == 'XMLHttpRequest':
		default_datetime = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
		if (request.GET.get('hn_number') == None):
			start_date = default_datetime - timedelta(days=7)
			end_date = default_datetime
			context = {
      			'start_date': start_date,
      			'end_date': end_date,
    		}
			return JsonResponse({'error': 'Required HN Number'}, status=400)
		if request.GET.get('since_date_input') != None:
			start_date = datetime.strptime(request.GET.get('since_date_input'), "%Y-%m-%d")
		else:
			start_date = default_datetime - timedelta(days=7)
		if request.GET.get('to_date_input') != None:
			end_date = datetime.strptime(request.GET.get('to_date_input'), "%Y-%m-%d")
		else:
			end_date = default_datetime
    
		signals_within_date_range = Telemetry.objects.filter(patient_id=request.GET.get('hn_number'), measurement_time__date__range=[start_date, end_date]).order_by('-measurement_time')
		patient = Patient.objects.filter(hn_number=request.GET.get('hn_number'))
		data = list(patient.values())

		for item in data:
			if 'measurement_time' in item:
				create_at_value = item['measurement_time']
				if isinstance(create_at_value, datetime):
					item['measurement_time'] = create_at_value.strftime('%Y-%m-%d %H:%M:%S')

		if data != None and data[0] != None:
			patient = data[0]
		else:
			patient = None

		context = {
          	'signals_html_string': get_signals_html(signals_within_date_range)
  		}
		return JsonResponse(context, safe=False)
	else:
		return JsonResponse({'error': 'This endpoint only accepts AJAX requests.'}, status=400)
   
def get_signals_html(signals):
    rows = []
    for index, signal in enumerate(signals):
        style_0 = "color: white; white;height:25px;"
        style_1 = "background-color: black;color: white; white;height:30px;"
        style = style_1 if index % 2 == 1 else style_0
        row_html = format_html(
            '<tr style="{} color: white; white;height:30px;">'
            '<td style="width: 30%;text-align: start;padding-left: 10px;">{}</td>'
            '<td style="width: 10%;text-align: center;">{}/{} </td>'
            '<td style="width: 10%;text-align: center;">{}</td>'
            '<td style="width: 10%;text-align: center;">{}</td>'
            '<td style="width: 10%;text-align: center;">{}</td>'
            '<td style="width: 10%;text-align: center;">{}</td>'
            '<td style="width: 40%;text-align: end;padding-right:10px;">{}</td>'
            '</tr>',
            style,
            signal.measurement_time.strftime("%d %B, %Y %H:%M"),
            signal.bp_systolic,
            signal.bp_diastolic,
            signal.temp,
            signal.pulse,
            signal.respirations,
            signal.o2_sat,
            signal.remark
        )
        rows.append(row_html)

    return ''.join(rows)

