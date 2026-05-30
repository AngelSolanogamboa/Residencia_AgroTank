from django.urls import path
from . import views

urlpatterns = [
    path('control/', views.dashboard, name='control'),

    path("move/<str:direction>/", views.move),
    path("speed/<int:level>/", views.speed),
    path("led/<str:color>/", views.led),
    path("video/", views.video_stream),
    path("status/", views.status),
    path("servo/<int:angle>/", views.servo),
    path("servo_y/subir/", views.subir_servo_y),
    path("servo_y/bajar/", views.bajar_servo_y),
    path("servo_y/centrar/", views.centrar_servo_yx),
    path("servo_x/derecha/", views.derecha_servo_x),
    path("servo_x/izquierda/", views.izquierda_servo_x),
    path("detectar/", views.detectar,name="detectar"),
]