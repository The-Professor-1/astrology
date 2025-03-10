from django.contrib import admin # type: ignore
from django.urls import path,include # type: ignore
from .views import login_view,logout_view,home_view
urlpatterns = [
    path('home/', home_view, name='dashboard'),
    path('', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    ]