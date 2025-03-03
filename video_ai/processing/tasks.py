import os
import re
import uuid
import yt_dlp
import whisper
import numpy as np
from datetime import datetime
from pymongo import MongoClient
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
from django.conf import settings
from django.http import JsonResponse, FileResponse
from django.views.decorators.http import require_http_methods
from transformers import pipeline

# ✅ MongoDB Setup
client = MongoClient(settings.MONGO_URI)
db = client['video_ai']
videos_collection = db['videos']
logs_collection = db['logs']

# ✅ Define Paths
MEDIA_ROOT = settings.MEDIA_ROOT
DOWNLOAD_PATH = os.path.join(MEDIA_ROOT, 'downloads')
CLIPS_PATH = os.path.join(MEDIA_ROOT, 'clips')
UPLOADS_PATH = os.path.join(MEDIA_ROOT, 'uploads')

# ✅ Ensure Directories Exist
os.makedirs(DOWNLOAD_PATH, exist_ok=True)
os.makedirs(CLIPS_PATH, exist_ok=True)
os.makedirs(UPLOADS_PATH, exist_ok=True)

# ✅ AI Model Loading (Lazy Loading to Save RAM)
def load_whisper():
    """Loads the Whisper AI model only when needed."""
    return whisper.load_model("base")

def load_classifier():
    """Loads the zero-shot classification model."""
    return pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

# ✅ AI Curation: Predefined Genres
GENRES = {
    "podcast": ["discussion", "guest", "interview"],
    "sports": ["goal", "score", "penalty", "win"],
    "news": ["breaking", "announcement", "update"],
    "marketing": ["growth", "strategy", "webinar"],
    "educational": ["lesson", "tutorial", "explanation"]
}

# ============================
# 🔥 Logging Helper
# ============================

def log_message(video_id, message):
    """Save logs to MongoDB and print for debugging."""
    try:
        logs_collection.insert_one({
            "video_id": video_id,
            "message": message,
            "timestamp": datetime.utcnow()
        })
    except Exception as e:
        print(f"Logging error: {str(e)}")

    print(f"[{datetime.utcnow()}] [{video_id}] {message}")

# ============================
# 🔥 Video Downloading
# ============================

def download_video(video_url, video_id):
    """Download video from YouTube and save locally."""
    output_path = os.path.join(DOWNLOAD_PATH, f"{video_id}.mp4")
    ydl_opts = {
        'outtmpl': output_path,
        'format': 'best',
        'noplaylist': True,
        'quiet': True,
    }

    log_message(video_id, f"Downloading YouTube video: {video_url}")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        return output_path if os.path.exists(output_path) else None
    except Exception as e:
        log_message(video_id, f"Error downloading video: {str(e)}")
        return None

# ============================
# 🔥 AI Processing Functions
# ============================

def save_clips(video_id, file_path, highlight_clips, clip_length):
    """Saves AI-detected highlight clips using timestamps and ensures correct length."""
    
    saved_clips = []

    for idx, (start_time, end_time) in enumerate(highlight_clips):
        start_time = int(start_time)  # ✅ Ensure integers
        end_time = int(end_time)      # ✅ Ensure integers
        clip_length = int(clip_length)  # ✅ Ensure integers

        if start_time >= end_time:
            log_message(video_id, f"⚠️ Skipping invalid clip range: {start_time}s to {end_time}s.")
            continue

        # ✅ If the segment is longer than `clip_length`, split into smaller clips
        for sub_start in range(start_time, end_time, clip_length):
            sub_end = min(sub_start + clip_length, end_time)
            clip_path = os.path.join(CLIPS_PATH, f"{video_id}_clip_{idx}_{sub_start}s.mp4")

            try:
                log_message(video_id, f"🎬 Clipping {video_id}_clip_{idx}_{sub_start}s.mp4 from {sub_start}s to {sub_end}s")
                ffmpeg_extract_subclip(file_path, sub_start, sub_end, clip_path)

                saved_clips.append({
                    "clip_name": f"{video_id}_clip_{idx}_{sub_start}s.mp4",
                    "download_url": f"/download/{video_id}_clip_{idx}_{sub_start}s.mp4",
                    "start_time": sub_start,
                    "end_time": sub_end
                })
            except Exception as e:
                log_message(video_id, f"❌ Error saving clip {video_id}_clip_{idx}_{sub_start}s.mp4: {str(e)}")

    # ✅ If no clips were created, return the full video
    if not saved_clips:
        log_message(video_id, "📢 No valid clips generated. Returning full video instead.")
        saved_clips.append({
            "clip_name": os.path.basename(file_path),
            "download_url": f"/download/{os.path.basename(file_path)}"
        })

    return saved_clips




from difflib import SequenceMatcher  # ✅ Used for fuzzy matching

def similar(a, b):
    """Checks how similar two strings are (for better sentence detection)."""
    return SequenceMatcher(None, a, b).ratio()

def get_highlights(video_id, transcript, whisper_segments, clip_length=30, custom_prompt=None, 
                      video_duration=None, timeframe=None):
    """Handles AI-powered highlight detection and manual clipping."""

    log_message(video_id, "Running AI highlight detection..." if custom_prompt else "Manual clipping...")

    if not whisper_segments and custom_prompt:
        log_message(video_id, "⚠️ No speech detected! Returning full video.")
        return [[0, clip_length]]

    highlights = []
    
    # ✅ Convert prompts into a list (handles both words and full sentences)
    prompt_phrases = [phrase.strip().lower() for phrase in custom_prompt.split(",")] if custom_prompt else []

    if custom_prompt:
        log_message(video_id, f"🔍 AI mode enabled: Searching FULL video for prompts: {prompt_phrases}")

        for segment in whisper_segments:
            text = segment.get('text', '').lower()

            # ✅ Check for exact phrase match OR a highly similar sentence
            for phrase in prompt_phrases:
                if phrase in text or similar(phrase, text) > 0.75:  # ✅ Fuzzy matching threshold = 75% similarity
                    log_message(video_id, f"🎯 Found relevant segment: {segment['text']}")

                    start_time = max(0, segment['start'] - 5)
                    end_time = min(start_time + clip_length, segment['end'])

                    highlights.append([start_time, end_time])

    # ✅ If highlights are found, return them
    if highlights:
        log_message(video_id, f"✅ AI found {len(highlights)} relevant moments.")
        return highlights

    # ✅ If no highlights found, return the full timeframe or video
    log_message(video_id, "⚠️ No AI highlights found! Returning FULL video instead.")
    return [[0, video_duration]] if video_duration else [[0, clip_length]]


# ============================
# 🔥 Video Processing Pipeline
# ============================

def process_video(video_id, video_url=None, file_path=None, clip_length=30, timeframe=None, speech_language="English", custom_prompt=None):
    """Processes video: AI-powered or manual clipping with proper transcription handling."""
    
    if not clip_length:
        log_message(video_id, "❌ Error: clip_length was not provided. Defaulting to 30 seconds.")
        clip_length = 30  # ✅ Default to 30s if missing

    if file_path:
        log_message(video_id, f"📂 Processing uploaded video: {file_path}")
    else:
        file_path = download_video(video_url, video_id)
        if not file_path:
            log_message(video_id, "❌ Failed to download video.")
            return

    # ✅ Ensure the downloaded file exists
    if not os.path.exists(file_path):
        log_message(video_id, f"❌ Error: Video file not found at {file_path}")
        return

    # ✅ Ensure the file is a valid video
    try:
        clip = VideoFileClip(file_path)
        video_duration = int(clip.duration)
        if clip.audio is None:
            log_message(video_id, "❌ Error: No audio detected in the video.")
            return
    except Exception as e:
        log_message(video_id, f"❌ MoviePy failed to read video. Possible corruption. Error: {str(e)}")
        return

    whisper_segments = []
    full_transcription = ""

    if custom_prompt:
        try:
            whisper_model = load_whisper()
            audio_path = file_path.replace(".mp4", ".wav")
            clip.audio.write_audiofile(audio_path, codec='pcm_s16le')

            log_message(video_id, "📝 Running Whisper transcription on FULL video...")
            whisper_output = whisper_model.transcribe(audio_path, word_timestamps=True)
            whisper_segments = whisper_output.get('segments', [])
            full_transcription = whisper_output.get('text', '')

            if not full_transcription.strip():
                log_message(video_id, "⚠️ Warning: Whisper transcription returned empty text!")

        except Exception as e:
            log_message(video_id, f"❌ Whisper transcription failed: {str(e)}")
            return

    # ✅ Ensure AI checks the full video
    highlight_clips = get_highlights(video_id, full_transcription, whisper_segments, clip_length, custom_prompt, video_duration, timeframe)

    # ✅ If AI found nothing, return the full video
    if highlight_clips == [[0, video_duration]]:
        log_message(video_id, "🎥 No AI highlights found. Returning the FULL VIDEO instead.")
        saved_clips = [{"clip_name": file_path, "download_url": f"/download/{os.path.basename(file_path)}"}]
    else:
        saved_clips = save_clips(video_id, file_path, highlight_clips, clip_length)  # ✅ Pass clip_length correctly

    videos_collection.insert_one({
        "video_id": video_id,
        "highlight_clips": saved_clips,
        "full_transcription": full_transcription,
        "status": "processed"
    })

    log_message(video_id, "✅ Processing complete.")
