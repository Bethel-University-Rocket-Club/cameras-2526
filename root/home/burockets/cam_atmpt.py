from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
import time
import subprocess
from gpiozero import LED

led = LED(17)
led.on()

pc2 = Picamera2()

# 1. Grab the highest sensor mode
full_res = pc2.sensor_modes[2]['size']

# 2. Configure for Video with Grayscale and Manual Exposure
config = pc2.create_video_configuration(
    main={"size": full_res, "format": "YUV420"},
    controls={
        "FrameRate": 8,
        "Saturation": 1.0,       # Grayscale
        "AeEnable": False,       # Disable Auto Exposure
        "ExposureTime": 1000,     # Lowest exposure (in microseconds)
        "AnalogueGain": -10.0,     # Lowest ISO (no digital/analog boost)
        "Sharpness": 0
    },
    encode="main"
)
pc2.configure(config)

encoder = H264Encoder(bitrate=100000000)
output_file = "out2.h264"

# 3. Start the camera
pc2.start()

# 4. Record to H.264
print(f"Recording Low-Exposure Grayscale at {full_res}...")
pc2.start_recording(encoder, output_file)

# Record for 10 seconds
time.sleep(120)

# 5. Stop and Clean up
pc2.stop_recording()
pc2.stop()
print("Done.")

# The FFmpeg command to wrap the raw H.264 into an MP4 at 8fps
input_file = "out2.h264"
output_file_mp4 = "out2.mp4"

cmd = [
    'ffmpeg', '-y',          # -y overwrites existing files
    '-r', '8',               # Set input framerate to 8fps
    '-i', input_file,        # Input file
    '-c:v', 'copy',          # Copy the video stream without re-encoding
    output_file_mp4          # Output file
]

subprocess.run(cmd)
print(f"Conversion complete: {output_file_mp4}")

network_start_cmd = [
    'sudo', 'systemctl', 'start', 'simcom-connect'
]

subprocess.run(network_start_cmd)