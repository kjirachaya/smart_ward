from django.shortcuts import redirect
from django.urls import path
from . import views
from django.urls import path

urlpatterns = [
    path('', views.ward),
    # path('form-70/', views.form70),
    # path('form-31/', views.form31),
    path('telemetry/', views.TelemetryListCreate.as_view(), name='telemetry-list'),
    path('telemetry/<int:pk>/', views.TelemetryRetrieveUpdateDestroy.as_view(), name='telemetry-detail'),
    path('home/', lambda request: redirect('', permanent=True)),
    path('api/patient/<str:hn_number>/', views.PatientDetailView.as_view(), name='patient-detail'),
    path('api/operator/<str:staff_id>/', views.OperatorDetailView.as_view(), name='operator-detail'),
    path('ward/', views.ward),
    path('ward/add-patient', views.wardAddPatient),
    path('ward/remove-patient', views.wardRemovePatient),
    path('ward/form-31/', views.wardForm31, name='form-31'),
    path('ward/form-70/', views.wardForm70, name='form-70'),
    path('beds', views.beds),
    path('beds/add-bed', views.addBed, name='add-bed'),
    path('users', views.operatorUsers),
    path('print-form-31', views.print_form31),
    # path('home/', views.patients),
    # path("all", GetChat.as_view(), name="get-chats"),
]
