from django.contrib import admin # type: ignore
from django.urls import path,include # type: ignore
from .views import contactus,email_reply


app_name = 'contact'
urlpatterns = [
    path('',contactus ,name='contact'),
    path('reply/',email_reply ,name='reply'),
]