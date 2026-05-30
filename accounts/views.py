from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .services import scan_wifi, connect_wifi
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)
            return redirect('control')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')

    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


def wifi_networks(request):
    data = scan_wifi()
    return JsonResponse(data)


@csrf_exempt
def wifi_connect(request):
    if request.method == "POST":
        body = json.loads(request.body)

        ssid = body.get("ssid")
        password = body.get("password")

        result = connect_wifi(ssid, password)

        return JsonResponse(result)

    return JsonResponse({"message": "Método no permitido"})