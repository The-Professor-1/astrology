from django.contrib import admin # type: ignore
from django.urls import path,include # type: ignore
from calculator.views import nameandnosender,calculate,wealth_view,calculators_list,life_luck,behavior_view,place_view,marriage_luck_view,military_prophecy,love_prophecy,legal_prophecy,marriage_length_prophecy,enemy_behavior,patient_prophecy,pregnancy_prophecy,birth_prophecy,servant_behavior

urlpatterns = [
    path('',calculate ,name='calculate'),
    path('send_transaction_number/',nameandnosender,name='nameandnosender'),
    path('wealth/',wealth_view,name='wealth_calculator'),
    path('calculators/',calculators_list,name="calculator_list"),
    path('behavior/',behavior_view,name='behavior_calculator'),
    path('place/',place_view,name='place_calculator'),
    path('marriage_luck/',marriage_luck_view,name='marriage_luck_calculator'),
     path('birth/',birth_prophecy,name='birth_prophecy'),
    path('pregnancy/',pregnancy_prophecy,name="pregnancy_prophecy"),
    path('love/',love_prophecy,name='love_prophecy'),
    path('patient/',patient_prophecy,name='patient_prophecy'),
    path('legal/',legal_prophecy,name='legal_prophecy'),
     path('marriage_length/',marriage_length_prophecy,name='marriage_length_prophecy'),
    path('enemy/',enemy_behavior,name="enemy_behavior"),
    path('life/',life_luck,name='life_luck'),
    path('war_prophecy/',military_prophecy,name='military_prophecy'),
    path('servant_behavior/',servant_behavior,name='servant_behavior'),
]