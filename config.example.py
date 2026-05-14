"""Copy this file to config.py and adjust to your environment.

config.py is gitignored — it contains your device's LAN IP and is
machine-specific, so it should not be committed.
"""

# IP of your GeekMagic SmallTV-Ultra on your local network.
# Find it in your router's DHCP table, or in the device's network screen.
DEVICE_IP = "192.168.178.90"

# Photo Album rotation interval (seconds). The device alternates between
# images in /image/ every i_i seconds when autoplay is enabled.
SCREEN_ROTATE_SECONDS = 8

# How often the live loop (run.py) re-renders + re-uploads all GIFs.
# 120s is a reasonable cadence — Anthropic's usage endpoint also caches
# server-side, so polling faster doesn't get you fresher numbers.
DATA_REFRESH_SECONDS = 120

# Local output directory for rendered GIFs.
OUT_DIR = "out"

# Remote directory on the device. Stock firmware exposes /image/ as the
# Photo Album source.
REMOTE_DIR = "/image"
