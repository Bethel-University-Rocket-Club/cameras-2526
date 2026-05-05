from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
import socket
import select
import time
import subprocess
import board
import neopixel
system_status_ready = False

launch_time = None
launched = False
landed = False

UDP_IP = "0.0.0.0"
UDP_PORT = 5005

LED_PIN = board.D18
NUM_LEDS = 3

PIXELS = neopixel.NeoPixel(
        LED_PIN,
        NUM_LEDS,
        brightness = 1.0,
        auto_write = False,
        pixel_order = neopixel.GRB
)

BLUE = (0, 0, 255)
GREEN = (255, 0, 0)
RED = (0, 255, 0)
OFF = (0, 0, 0)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))
sock.setblocking(False)

print(f"Listening for UDP packets on port {UDP_PORT}...")

# pc2 = Picamera2()

# 1. Grab the highest sensor mode
# full_res = pc2.sensor_modes[2]['size']

# 2. Configure for Video with Grayscale and Manual Exposure
'''
config = pc2.create_video_configuration(
    main={"size": full_res, "format": "YUV420"},
    controls={
        "FrameRate": 8,
        "Saturation": 0.0,       # Grayscale
        "AeEnable": False,       # Disable Auto Exposure
        "ExposureTime": 75,     # Lowest exposure (in microseconds)
        "AnalogueGain": -10.0,     # Lowest ISO (no digital/analog boost)
        "Sharpness": 5
    },
    encode="main"
)
pc2.configure(config)

encoder = H264Encoder(bitrate=100000000)
output_file = "test.h264"
'''
def clear_leds():
        PIXELS.fill(OFF)
        PIXELS.show()

def get_test_picture():
        system_status_ready = True

#based off of roll-control data
def has_launched():
        global launched
        launch_time = time.time_ns()
        return launched

#based off of roll-control data
def has_landed():
        global landed
        return landed

def get_roll_status():
        global launched, landed
        message = ""
        while True:
                try:
                        ready, _, _ = select.select([sock], [], [], 0.01)
                        if not ready:
                                break
                        data, addr = sock.recvfrom(1024)
                        message = data.decode()
                        print(message, end="")
                        if launch_time is not None:
                                print(f" at {(time.time_ns() - launch_time) / 1_000_000_000}s")
                        print()
                except BlockingIOError:
                        break
        match message:
                case "ROLL_CONTROL_READY":
                        #LED 0 to Green
                        PIXELS[0] = RED
                case "ROLL_CW":
                        #LED 0 on, 1,2 off - blue
                        PIXELS[0] = BLUE
                        PIXELS[1] = OFF
                        PIXELS[2] = OFF
                case "ROLL_CCW":
                        #LED 1 on, 0,2 off - blue
                        PIXELS[1] = BLUE
                        PIXELS[0] = OFF
                        PIXELS[2] = OFF
                case "ROLL_END":
                        #LED 2 on - blue, 0,1 off
                        PIXELS[2] = BLUE
                        PIXELS[1] = OFF
                        PIXELS[0] = OFF
                case "LAUNCHED":
                        launched = True
                        clear_leds()
                case "LANDED":
                        landed = True
                        clear_leds()
                case _:
                        #LED 0 to Red
                        PIXELS[0] = RED
        PIXELS.show()

clear_leds()

if get_test_picture():
        #LED 1 to Green
        PIXELS[1] = GREEN
else:
        #LED 1 to RED
        PIXELS[1] = RED


PIXELS.show()
get_test_picture()

while not has_launched():
        get_roll_status()
#LED 0,1,2 off
print("start")
# 3. Start the camera
# pc2.start()

# 4. Record to H.2640
'''
print(f"Recording Low-Exposure Grayscale at {full_res}...")
pc2.start_recording(encoder, output_file)
'''
while not has_landed():
        get_roll_status()

# 5. Stop and Clean up
'''
pc2.stop_recording()
pc2.stop()
'''
print("Done.")

# The FFmpeg command to wrap the raw H.264 into an MP4 at 8fps
'''
input_file = "test.h264"
output_file_mp4 = "test.mp4"

ffmpeg_convert_cmd = [
    'ffmpeg', '-y',          # -y overwrites existing files
    '-r', '8',               # Set input framerate to 8fps
    '-i', input_file,        # Input file
    '-c:v', 'copy',          # Copy the video stream without re-encoding
    output_file_mp4          # Output file
]

subprocess.run(ffmpeg_convert_cmd)

print(f"Conversion complete: {output_file_mp4}")
'''
network_start_cmd = [
    'sudo', 'systemctl', 'start', 'simcom-connect'
]

subprocess.run(network_start_cmd)