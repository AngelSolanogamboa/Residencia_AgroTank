import RPi.GPIO as GPIO
import time
import cv2
import os
import threading
import numpy as np

# ---------------- PINES DEL G1 TANK ----------------
IN1, IN2, IN3, IN4 = 20,21,19,26
ENA, ENB = 16,13

LED_R, LED_G, LED_B = 22,27,24

ECHO = 17
SERVO = 23
TRIG = 18

# BUZZER = 8


Y_MIN = 90
Y_MAX = 180
Y_CENTER = 135
STEP_Y = 10
SERVO_Y=9
# SERVO_X=7

# ---------------- CONFIGURACION GPIO ----------------
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

GPIO.setup([IN1,IN2,IN3,IN4], GPIO.OUT)

GPIO.setup(ENA, GPIO.OUT)
GPIO.setup(ENB, GPIO.OUT)

GPIO.setup([LED_R,LED_G,LED_B], GPIO.OUT)

GPIO.setup(ECHO, GPIO.IN)

GPIO.setup(SERVO, GPIO.OUT)

GPIO.setup(SERVO_Y, GPIO.OUT)

GPIO.setup(TRIG, GPIO.OUT)

GPIO.output(TRIG, False)
time.sleep(0.05)

GPIO.output(TRIG, True)
time.sleep(0.00001)

GPIO.output(TRIG, False)

servo = GPIO.PWM(SERVO, 50)
servo.start(7.5)

servo_y = GPIO.PWM(SERVO_Y, 50)
servo_y.start(7.5)



# ---------------- CONFIGURAR PWM ----------------
pwmA = GPIO.PWM(ENA,2000)
pwmB = GPIO.PWM(ENB,2000)

pwmA.start(10)
pwmB.start(10)

# ---------------- VARIABLES GLOBALES ----------------
velocidad = 5

LED_ON  = GPIO.LOW
LED_OFF = GPIO.HIGH

# Estado inicial LED
led_color = (LED_OFF, LED_OFF, LED_OFF)
led_enabled = False

# ---------------- CONTROL DE VELOCIDAD ----------------
def apply_speed():
    """
    Aplica la velocidad actual al PWM
    """
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

# ---------------- MOVIMIENTO DEL ROBOT ----------------
def forward():
    """Avanzar"""
    GPIO.output(IN1,1)
    GPIO.output(IN2,0)
    GPIO.output(IN3,1)
    GPIO.output(IN4,0)
def backward():
    """Retroceder"""
    GPIO.output(IN1,0)
    GPIO.output(IN2,1)
    GPIO.output(IN3,0)
    GPIO.output(IN4,1)
def left():
    """Girar izquierda"""
    GPIO.output(IN1,0)
    GPIO.output(IN2,0)
    GPIO.output(IN3,1)
    GPIO.output(IN4,0)
def right():
    """Girar derecha"""
    GPIO.output(IN1,1)
    GPIO.output(IN2,0)
    GPIO.output(IN3,0)
    GPIO.output(IN4,0)
def stop():
    """Detener robot"""
    GPIO.output(IN1,0)
    GPIO.output(IN2,0)
    GPIO.output(IN3,0)
    GPIO.output(IN4,0)

    # ---------------- CONTROL LED RGB ----------------
def apply_led():
    """
    Aplica el color actual del LED
    """
    GPIO.output(LED_R,led_color[0])
    GPIO.output(LED_G,led_color[1])
    GPIO.output(LED_B,led_color[2])
def set_color(r,g,b):
    """
    Cambia el color del LED
    """
    global led_color

    led_color = (
        LED_ON if r else LED_OFF,
        LED_ON if g else LED_OFF,
        LED_ON if b else LED_OFF
    )
    apply_led()

# ---------------- SENSOR ULTRASONICO ----------------
def get_distance():
    GPIO.output(TRIG, GPIO.HIGH)
    time.sleep(0.000015)
    GPIO.output(TRIG, GPIO.LOW)

    timeout = time.time() + 0.02

    while not GPIO.input(ECHO):
        if time.time() > timeout:
            return -1
        t1 = time.time()

    while GPIO.input(ECHO):
        if time.time() > timeout:
            return -1
        t2 = time.time()

    time.sleep(0.01)
    return ((t2 - t1) * 340 / 2) * 100

# ---------------- DIRECCION DEL SERVO ultrasonico  ----------------
def set_servo(angle):
    duty = 2 + (angle / 18)
    servo.ChangeDutyCycle(duty)
    # time.sleep(0.2)
    # servo.ChangeDutyCycle(0)

# ---------------- DIRECCION DEL SERVO Camara eje Y ----------------

y_angle = 135

def set_servo_Y(angle):

    # angle = max(90, min(180, angle))

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

    return y_angle


# ---------------- CAMARA STREAM ----------------
camera = None
output_frame = None
lock = threading.Lock()

net = cv2.dnn.readNet(
    "yolov4-tiny.weights",
    "yolov4-tiny.cfg"
)

# Clases
with open("classes.txt", "r") as f:
    classes = [line.strip() for line in f.readlines()]

layer_names = net.getLayerNames()

output_layers = [
    layer_names[i - 1]
    for i in net.getUnconnectedOutLayers()
]
def reiniciar_driver_camara():
    print("Reiniciando driver de cámara...")
    os.system("sudo modprobe -r uvcvideo")
    time.sleep(1)
    os.system("sudo modprobe uvcvideo")
    time.sleep(2)


def esperar_camara():
    while True:
        dispositivos = os.listdir("/dev")
        videos = [d for d in dispositivos if d.startswith("video")]

        if videos:
            print("Cámara detectada:", videos)
            return

        print("Esperando que aparezca la cámara...")
        time.sleep(2)


def iniciar_camara():
    global camera

    while True:
        try:
            if not os.path.exists("/dev/video0"):
                print("No existe /dev/video0")
                reiniciar_driver_camara()
                esperar_camara()

            camera = cv2.VideoCapture(0, cv2.CAP_V4L2)
            camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            camera.set(cv2.CAP_PROP_FPS, 30)
            camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

            if camera.isOpened():
                print("Cámara abierta correctamente")
                camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                return camera
            else:
                print("No se pudo abrir la cámara")
                time.sleep(2)

        except Exception as e:
            print("Error:", e)
            time.sleep(2)

def detectar_maleza():

    global output_frame
    global camera

    while True:

        success, frame = camera.read()

        if not success:

            print("Error frame")

            camera.release()

            camera = iniciar_camara()

            continue

        height, width, channels = frame.shape

        # ==================================
        # PREPARAR IMAGEN YOLO
        # ==================================

        blob = cv2.dnn.blobFromImage(
            frame,
            1 / 255.0,
            (320, 320),
            swapRB=True,
            crop=False
        )

        net.setInput(blob)

        outputs = net.forward(output_layers)

        boxes = []
        confidences = []
        class_ids = []

        # ==================================
        # DETECCIONES
        # ==================================

        for output in outputs:

            for detection in output:

                scores = detection[5:]

                class_id = np.argmax(scores)

                confidence = scores[class_id]

                if confidence > 0.5:

                    center_x = int(
                        detection[0] * width
                    )

                    center_y = int(
                        detection[1] * height
                    )

                    w = int(
                        detection[2] * width
                    )

                    h = int(
                        detection[3] * height
                    )

                    x = int(center_x - w / 2)

                    y = int(center_y - h / 2)

                    boxes.append([x, y, w, h])

                    confidences.append(
                        float(confidence)
                    )

                    class_ids.append(class_id)

        indexes = cv2.dnn.NMSBoxes(
            boxes,
            confidences,
            0.5,
            0.4
        )

        # ==================================
        # DIBUJAR
        # ==================================

        if len(indexes) > 0:

            for i in indexes.flatten():

                x, y, w, h = boxes[i]

                label = str(
                    classes[class_ids[i]]
                )

                confidence = confidences[i]

                cv2.rectangle(
                    frame,
                    (x, y),
                    (x + w, y + h),
                    (0, 255, 0),
                    2
                )

                cv2.putText(
                    frame,
                    f"{label} {confidence:.2f}",
                    (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 0),
                    2
                )

        with lock:

            output_frame = frame.copy()

        time.sleep(0.1)

# ==========================================
# STREAM FRAMES
# ==========================================

def gen_frames():

    global output_frame

    while True:

        with lock:

            if output_frame is None:
                continue

            ret, buffer = cv2.imencode(
                '.jpg',
                output_frame,
                [cv2.IMWRITE_JPEG_QUALITY, 70]
            )

            frame = buffer.tobytes()

        yield (
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n'
            + frame +
            b'\r\n'
        )

# ==========================================
# INICIAR SISTEMA
# ==========================================

camera = iniciar_camara()

threading.Thread(
    target=detectar_maleza,
    daemon=True
).start()

# def gen_frames():
#     global camera

#     camera = iniciar_camara()

#     while True:
#         success, frame = camera.read()

#         if not success:
#             print("Frame falló, reiniciando cámara")
#             camera.release()
#             camera = iniciar_camara()
#             continue

#         ret, buffer = cv2.imencode('.jpg', frame)
#         frame = buffer.tobytes()

#         yield (
#             b'--frame\r\n'
#             b'Content-Type: image/jpeg\r\n\r\n'
#             + frame +
#             b'\r\n'
#         )

# ---------------- MOVIMIENTO DE bocina  ----------------
# def whistle():
#     GPIO.output(BUZZER, GPIO.LOW)
#     time.sleep(0.1)
#     GPIO.output(BUZZER, GPIO.HIGH)
#     time.sleep(0.001)