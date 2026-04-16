import subprocess

try:
    subprocess.run(["ffmpeg", "-version"], check=True)
    print("FFmpeg is installed and accessible.")
except FileNotFoundError:
    print("FFmpeg is not found. Check installation and PATH.")
