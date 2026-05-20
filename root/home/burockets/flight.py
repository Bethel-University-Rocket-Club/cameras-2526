from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from adafruit_bmp280 import Adafruit_BMP280_I2C
from busio import I2C
import socket
import select
import time
import subprocess
from gpiozero import LED

time.sleep(5)

system_status_ready = False

launch_time = None
launched = False
landed = False

UDP_IP = "0.0.0.0"
UDP_PORT = 5005

LEFT_LED = LED(6)
RIGHT_LED = LED(5)

def all_off():
        LEFT_LED.off()
        RIGHT_LED.off()

def all_on():
        LEFT_LED.on()
        RIGHT_LED.on()

def roll_control_ready():
        LEFT_LED.on()

def cameras_ready():
        RIGHT_LED.on()

def rolling_CW():
        RIGHT_LED.on()
        LEFT_LED.off()

def rolling_CCW():
        LEFT_LED.on()
        RIGHT_LED.off()

def no_rolling():
        all_off()

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))
sock.setblocking(False)

def get_roll_status():
        message = ""
        while True:
                try:
                        ready, _, _ = select.select([sock], [], [], 0.01)
                        if not ready:
                                break
                        data, addr = sock.recvfrom(1024)
                        message = data.decode()
                        print(message, end="", flush=True)
                        #if launch_time is not None:
                        #       print(f" at {(time.time_ns() - launch_time) / 1_000_000_000}s")
                        #print()
                except BlockingIOError:
                        break
        match message:
                case "ROLL_CONTROL_READY":
                        roll_control_ready()
                case "CW":
                        rolling_CW()
                case "CCW":
                        rolling_CCW()
                case "ROLL_END":
                        no_rolling()
                case _:
                        ...

all_off()

while True:
        get_roll_status()
