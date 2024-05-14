from django.urls import path
from . import views

urlpatterns = [
    path('', views.home),
    path('login/', views.sign_in, name='login'),
    path('logout/', views.sign_out, name='logout'),
]
