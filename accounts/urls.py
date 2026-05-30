from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path("wifi/networks", views.wifi_networks, name="wifi"),
    path("wifi/connect", views.wifi_connect, name="wifi_connect"),

]