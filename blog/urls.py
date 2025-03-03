from django.contrib import admin # type: ignore
from django.urls import path,include # type: ignore
from .views import blogs,login_view,register_view,logout_view,home_view
urlpatterns = [
    path('', home_view, name='dashboard'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('register/', register_view, name='register'),
    ]