from django.contrib import admin # type: ignore
from django.urls import path,include # type: ignore
from .views import home_view

app_name = 'blog'
urlpatterns = [
    path('', home_view, name='dashboard'),
    path('contact/', include('contactus.urls'),name='contact'),
    ]