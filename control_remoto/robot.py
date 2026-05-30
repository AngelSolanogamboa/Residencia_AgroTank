import os
import time
import cv2
import RPi.GPIO as GPIO
from roboflow import Roboflow

# =====================================================
# PINES
# =====================================================

IN1, IN2, IN3, IN4 = 20, 21, 19, 26
ENA, ENB = 16, 13

LED_R, LED_G, LED_B = 22, 27, 24

ECHO = 17
TRIG = 18

SERVO = 23
SERVO_X = 11
SERVO_Y = 9
BUZZER = 8

# =====================================================
# GPIO
# =====================================================

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

GPIO.setup([IN1, IN2, IN3, IN4], GPIO.OUT)

GPIO.setup(ENA, GPIO.OUT)
GPIO.setup(ENB, GPIO.OUT)

GPIO.setup([LED_R, LED_G, LED_B], GPIO.OUT)

GPIO.setup(ECHO, GPIO.IN)
GPIO.setup(TRIG, GPIO.OUT)

GPIO.setup(SERVO, GPIO.OUT)
GPIO.setup(SERVO_X, GPIO.OUT)
GPIO.setup(SERVO_Y, GPIO.OUT)

GPIO.setup(BUZZER, GPIO.OUT)

GPIO.output(TRIG, False)

# =====================================================
# PWM
# =====================================================

pwmA = GPIO.PWM(ENA, 2000)
pwmB = GPIO.PWM(ENB, 2000)

pwmA.start(10)
pwmB.start(10)

servo = GPIO.PWM(SERVO, 50)
servo.start(7.5)

servo_y = GPIO.PWM(SERVO_Y, 50)
servo_y.start(0)

servo_x = GPIO.PWM(SERVO_X, 50)
servo_x.start(0)

# =====================================================
# VARIABLES
# =====================================================

velocidad = 2

LED_ON = GPIO.LOW
LED_OFF = GPIO.HIGH

led_color = (LED_OFF, LED_OFF, LED_OFF)

y_angle = 135
x_angle = 135

camera = None
latest_frame = None

# =====================================================
# VELOCIDAD
# =====================================================

def apply_speed():
    duty = velocidad * 10
    pwmA.ChangeDutyCycle(duty)
    pwmB.ChangeDutyCycle(duty)

def set_speed(level):
    global velocidad
    level = int(level)
    if velocidad == level:
        return
    velocidad = level
    apply_speed()

# =====================================================
# MOVIMIENTO
# =====================================================

def forward():
    GPIO.output(IN1, 1)
    GPIO.output(IN2, 0)
    GPIO.output(IN3, 1)
    GPIO.output(IN4, 0)


def backward():
    GPIO.output(IN1, 0)
    GPIO.output(IN2, 1)
    GPIO.output(IN3, 0)
    GPIO.output(IN4, 1)

def left():
    GPIO.output(IN1, 0)
    GPIO.output(IN2, 0)
    GPIO.output(IN3, 1)
    GPIO.output(IN4, 0)

def right():
    GPIO.output(IN1, 1)
    GPIO.output(IN2, 0)
    GPIO.output(IN3, 0)
    GPIO.output(IN4, 0)


def stop():
    GPIO.output(IN1, 0)
    GPIO.output(IN2, 0)
    GPIO.output(IN3, 0)
    GPIO.output(IN4, 0)

# =====================================================
# LED RGB
# =====================================================

def apply_led():
    GPIO.output(LED_R, led_color[0])
    GPIO.output(LED_G, led_color[1])
    GPIO.output(LED_B, led_color[2])

def set_color(r, g, b):
    global led_color
    led_color = (
        LED_ON if r else LED_OFF,
        LED_ON if g else LED_OFF,
        LED_ON if b else LED_OFF
    )
    apply_led()

# =====================================================
# SERVOS
# =====================================================

def set_servo(angle):
    duty = 2 + (angle / 18)
    servo.ChangeDutyCycle(duty)

def set_servo_Y(angle):
    duty = 2 + (angle / 18)
    servo_y.ChangeDutyCycle(duty)

def subir_Y():
    global y_angle
    y_angle = min(180, y_angle + 5)
    set_servo_Y(y_angle)
    return y_angle

def bajar_Y():
    global y_angle
    y_angle = max(90, y_angle - 5)
    set_servo_Y(y_angle)
    return y_angle

def centrar_Y():
    global y_angle
    y_angle = 150
    set_servo_Y(y_angle)
    global x_angle
    x_angle = 150
    set_servo_X(x_angle)
    return y_angle, x_angle

def set_servo_X(angle):
    duty = 2 + (angle / 18)
    servo_x.ChangeDutyCycle(duty)


def subir_X():
    global x_angle
    x_angle = min(225, x_angle + 5)
    set_servo_X(x_angle)
    return x_angle

def bajar_X():
    global x_angle
    x_angle = max(45, x_angle - 5)
    set_servo_X(x_angle)
    return x_angle

    
# =====================================================
# CAMARA
# =====================================================

def reiniciar_driver_camara():
    print("Reiniciando driver cámara")
    os.system("sudo modprobe -r uvcvideo")
    time.sleep(1)
    os.system("sudo modprobe uvcvideo")


def esperar_camara():

    while True:
        if os.path.exists("/dev/video0"):
            print("Cámara detectada")
            return
        print("Esperando cámara...")


def iniciar_camara():

    global camera
    while True:
        try:
            if not os.path.exists("/dev/video0"):
                reiniciar_driver_camara()
                esperar_camara()
            camera = cv2.VideoCapture(
                0,
                cv2.CAP_V4L2
            )
            camera.set(
                cv2.CAP_PROP_BUFFERSIZE,
                1
            )
            camera.set(
                cv2.CAP_PROP_FPS,
                30
            )
            camera.set(
                cv2.CAP_PROP_FRAME_WIDTH,
                640
            )
            camera.set(
                cv2.CAP_PROP_FRAME_HEIGHT,
                480
            )
            if camera.isOpened():
                print("Cámara iniciada")
                return camera
            print("No se pudo abrir cámara")
        except Exception as e:
            print("Error cámara:", e)

camera = iniciar_camara()

# =====================================================
# STREAM
# =====================================================

def gen_frames():

    global camera
    global latest_frame

    while True:

        success, frame = camera.read()

        if not success:

            print("Frame falló")

            camera.release()

            camera = iniciar_camara()

            continue

        latest_frame = frame.copy()

        _, buffer = cv2.imencode(
            '.jpg',
            frame
        )

        frame = buffer.tobytes()

        yield (
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n'
            + frame +
            b'\r\n'
        )

# =====================================================
# VIDEO IA
# =====================================================

def grabar_video(
    nombre="media/video_maleza.mp4",
    duracion=5
    ):

    global latest_frame
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(
        nombre,
        fourcc,
        20.0,
        (640, 480)
    )
    inicio = time.time()
    while True:
        if latest_frame is None:
            continue
        out.write(
            latest_frame.copy()
        )
        if time.time() - inicio >= duracion:
            break
    out.release()
    print("Video guardado:", nombre)
    return nombre

def detectar_maleza_video(ruta_video):

    rf = Roboflow(
        api_key="zuuT8WGEkZKI4kgW5Kqa"
    )
    project = rf.workspace().project(
        "deteccion-de-maleza-tzw1i"
    )
    model = project.version(1).model
    cap = cv2.VideoCapture(ruta_video)
    resultados = []
    contador = 0
    while True:
        success, frame = cap.read()
        if not success:
            break
        if contador % 30 == 0:
            nombre_frame = (
                f"media/frame_{contador}.jpg"
            )
            cv2.imwrite(nombre_frame, frame)
            prediction = model.predict(
                nombre_frame,
                confidence=40,
                overlap=30
            ).json()
            resultados.append(prediction)
            os.remove(nombre_frame)
        contador += 1
    cap.release()
    return resultados

def grabar_y_detectar():
    ruta = grabar_video()
    return detectar_maleza_video(ruta)

def resumir_resultados(results):

    for frame in results:
        if "predictions" not in frame:
            continue
        if not frame["predictions"]:
            continue
        pred = frame["predictions"][0]
        clase = pred["class"]
        confianza = round(
            pred["confidence"] * 100
        )
        x = float(pred["x"])
        image = frame.get("image", {})
        width = float(
            image.get("width", 640)
        )
        if width * 0.3 < x < width * 0.7:
            posicion = "centro"
        elif x <= width * 0.3:
            posicion = "izquierda"
        else:
            posicion = "derecha"
        return {
            "clase": clase,
            "confianza": confianza,
            "posicion": posicion
        }
    return None

