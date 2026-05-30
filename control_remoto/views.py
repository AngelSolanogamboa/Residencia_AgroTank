from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, StreamingHttpResponse
from . import robot
@login_required
def dashboard(request):
    return render(request, 'dashboard.html')
def move(request, direction):
    if direction == "forward":
        robot.forward()
    elif direction == "back":
        robot.backward()
    elif direction == "left":
        robot.left()
    elif direction == "right":
        robot.right()
    elif direction == "stop":
        robot.stop()
    return JsonResponse({"status": "ok"})
def speed(request, level):
    robot.set_speed(level)
    return JsonResponse({
        "speed": level
    })
def led(request, color):
    if color == "red":
        robot.set_color(0,1,1)
    elif color == "green":
        robot.set_color(1,0,1)
    elif color == "blue":
        robot.set_color(1,1,0)
    elif color == "white":
        robot.set_color(0,0,0)
    return JsonResponse({"status": "ok"})

def video_stream(request):
    return StreamingHttpResponse(
        robot.gen_frames(),
        content_type='multipart/x-mixed-replace; boundary=frame'
    )
def status(request):
    return JsonResponse({
        "speed": robot.velocidad
    })
def servo(request, angle):
    robot.set_servo(angle)
    return JsonResponse({
        "angle": angle
    })
def subir_servo_y(request):
    angle = robot.subir_Y()
    return JsonResponse({
        "angle": angle
    })
def bajar_servo_y(request):
    angle = robot.bajar_Y()
    return JsonResponse({
        "angle": angle
    })
def centrar_servo_yx(request):
    angle = robot.centrar_Y()
    return JsonResponse({
        "angle": angle
    })
def derecha_servo_x(request):
    angle = robot.subir_X()
    return JsonResponse({
        "angle": angle
    })
def izquierda_servo_x(request):
    angle = robot.bajar_X()
    return JsonResponse({
        "angle": angle
    })
def detectar(request):
    resultados = robot.grabar_y_detectar()
    total = robot.resumir_resultados(resultados)
    return JsonResponse({
        "detecciones": total
    })

