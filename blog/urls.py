from django.contrib import admin # type: ignore
from django.urls import path,include # type: ignore
from .views import login_view,logout_view,home_view

app_name = 'blog'
urlpatterns = [
    path('', home_view, name='dashboard'),
    path('logout/', logout_view, name='logout'),
    ]