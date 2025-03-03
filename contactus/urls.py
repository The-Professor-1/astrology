from django.contrib import admin # type: ignore
from django.urls import path,include # type: ignore
from .views import contactus

urlpatterns = [
    path('',contactus ,name='contact'),
]