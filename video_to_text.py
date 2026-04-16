import os
import yt_dlp
import subprocess
from pydub import AudioSegment
import speech_recognition as sr
from transformers import pipeline

# Define FFmpeg and FFprobe paths
FFMPEG_PATH = "C:/ffmpeg/bin/ffmpeg.exe"
FFPROBE_PATH = "C:/ffmpeg/bin/ffprobe.exe"

# Ensure FFmpeg is accessible
os.environ["IMAGEIO_FFMPEG_EXE"] = FFMPEG_PATH
os.environ["FFMPEG_BINARY"] = FFMPEG_PATH
os.environ["FFPROBE_BINARY"] = FFPROBE_PATH

# Set paths for Pydub
AudioSegment.converter = FFMPEG_PATH
AudioSegment.ffprobe = FFPROBE_PATH

# Check FFmpeg installation
try:
    subprocess.run([FFMPEG_PATH, "-version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print("✅ FFmpeg is installed and accessible.")
except FileNotFoundError:
    print("❌ FFmpeg is not found! Check installation and PATH.")
    exit(1)

# 1. Download the YouTube video in MP4 format
def download_video(url):
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',  # fallback to best available
        'outtmpl': 'downloaded_video.%(ext)s',
        'ffmpeg_location': FFMPEG_PATH,
        'merge_output_format': 'mp4',
        'noprogress': True,
        'quiet': False,
        'restrictfilenames': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            downloaded_filename = ydl.prepare_filename(info).rsplit(".", 1)[0] + ".mp4"
        print(f"✅ Video downloaded successfully as '{downloaded_filename}'")
        return downloaded_filename
    except Exception as e:
        print(f"❌ Error downloading video: {e}")
        return None

# 2. Extract audio from MP4 and convert to WAV
def extract_audio(video_path):
    wav_path = "audio.wav"
    try:
        audio = AudioSegment.from_file(video_path, format="mp4")
        audio = audio.set_channels(1).set_frame_rate(16000).set_sample_width(2)
        audio.export(wav_path, format="wav")
        print("✅ Audio extracted and converted to WAV format.")
        return wav_path
    except Exception as e:
        print(f"❌ Error extracting audio: {e}")
        return None

# 3. Transcribe audio to text
def transcribe_audio(wav_path):
    if not os.path.exists(wav_path):
        print("❌ Error: 'audio.wav' not found!")
        return ""
    
    recognizer = sr.Recognizer()
    audio = AudioSegment.from_wav(wav_path)
    chunk_length_ms = 30000  # 30 seconds
    chunks = [audio[i:i + chunk_length_ms] for i in range(0, len(audio), chunk_length_ms)]
    full_text = ""

    for i, chunk in enumerate(chunks):
        chunk_wav = f"chunk_{i}.wav"
        chunk.export(chunk_wav, format="wav")
        with sr.AudioFile(chunk_wav) as source:
            audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data)
            full_text += text + " "
            print(f"📝 Chunk {i + 1} Transcribed: {text}")
        except sr.UnknownValueError:
            print(f"⚠️ Chunk {i + 1}: Could not understand the audio.")
        except sr.RequestError as e:
            print(f"❌ Speech Recognition error: {e}")
            return ""
    return full_text.strip()

# 4. Summarize transcribed text
def generate_summary(text):
    if not text:
        print("❌ No text to summarize!")
        return
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
    max_input_length = 1024
    if len(text) > max_input_length:
        text = text[:max_input_length]
    try:
        summary = summarizer(text, max_length=150, min_length=30, do_sample=False)
        print("\n📄 Summary: ", summary[0]['summary_text'])
    except Exception as e:
        print(f"❌ Error generating summary: {e}")

# Main function
def main():
    video_url = input("Enter YouTube video URL: ").strip()
    if not video_url:
        print("❌ Invalid URL! Please enter a valid YouTube link.")
        return
    
    video_file = download_video(video_url)
    if not video_file:
        return
    
    wav_file = extract_audio(video_file)
    if not wav_file:
        return
    
    transcribed_text = transcribe_audio(wav_file)
    if transcribed_text:
        print("\n📝 FULL TRANSCRIPTION:\n", transcribed_text)
        generate_summary(transcribed_text)

if __name__ == "__main__":
    main()
