from django.urls import path,include # type:ignore
from .views import about_us

urlpatterns = [
    path('', about_us, name='aboutus'),
]