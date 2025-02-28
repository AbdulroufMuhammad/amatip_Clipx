import os
import uuid
import json
import threading
import yt_dlp
import whisper
import numpy as np
from datetime import datetime
from pymongo import MongoClient
from moviepy.video.io.VideoFileClip import VideoFileClip
from django.conf import settings
from django.http import JsonResponse, FileResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

# ✅ MongoDB Setup
client = MongoClient(settings.MONGO_URI)
db = client['video_ai']
videos_collection = db['videos']
logs_collection = db['logs']

# ✅ Define Paths
DOWNLOAD_PATH = os.path.join(settings.MEDIA_ROOT, 'downloads')
CLIPS_PATH = os.path.join(settings.MEDIA_ROOT, 'clips')

# ✅ Ensure Directories Exist
os.makedirs(DOWNLOAD_PATH, exist_ok=True)
os.makedirs(CLIPS_PATH, exist_ok=True)

def log_message(video_id, message):
    """ Save logs to MongoDB and print for debugging. """
    logs_collection.insert_one({
        "video_id": video_id,
        "message": message,
        "timestamp": datetime.utcnow()
    })
    print(f"[{datetime.utcnow()}] [{video_id}] {message}")

def download_video(video_url, video_id):
    """ ✅ Downloads video from YouTube and saves locally. """
    output_path = os.path.join(DOWNLOAD_PATH, f"{video_id}.mp4")
    ydl_opts = {
        'outtmpl': output_path,
        'format': 'best',
        'noplaylist': True,
        'quiet': True,  # Reduce console spam
    }

    log_message(video_id, f"Downloading YouTube video: {video_url}")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])

        if not os.path.exists(output_path):
            raise FileNotFoundError(f"Download failed: {output_path} not found.")

        log_message(video_id, "Download complete.")
        return output_path
    except Exception as e:
        log_message(video_id, f"Error downloading video: {str(e)}")
        return None

def process_video(video_id, video_url, clip_length=30, clip_ranges=None):
    """
    ✅ Full YouTube Video Processing Pipeline:
    - Download YouTube video
    - Extract and transcribe audio (Whisper AI)
    - Split video into clips
    - Transcribe each clip
    """
    # ✅ Step 1: Download video
    file_path = download_video(video_url, video_id)
    if not file_path:
        log_message(video_id, "Failed to download video.")
        return

    # ✅ Step 2: Load Video
    try:
        log_message(video_id, "Loading video...")
        clip = VideoFileClip(file_path)
        total_duration = int(clip.duration)

        if clip.audio is None:
            log_message(video_id, "Error: No audio detected in the video.")
            return
    except Exception as e:
        log_message(video_id, f"Error loading video: {str(e)}")
        return

    # ✅ Step 3: Extract Full Audio and Transcribe Full Video
    try:
        log_message(video_id, "Extracting full audio for transcription...")
        full_audio_path = file_path.replace(".mp4", ".wav")
        clip.audio.write_audiofile(full_audio_path)

        log_message(video_id, "Transcribing full video audio...")
        model = whisper.load_model("base")
        full_transcription = model.transcribe(full_audio_path)['text']

        if not full_transcription.strip():
            full_transcription = "No speech detected."

        log_message(video_id, "Full video transcription complete.")
    except Exception as e:
        log_message(video_id, f"Error transcribing full video: {str(e)}")
        full_transcription = "Full video transcription failed."

    # ✅ Step 4: Generate Video Clips and Transcribe Each One
    highlight_clips = []

    try:
        log_message(video_id, "Generating video clips...")

        if clip_ranges:
            clip_ranges = [[max(0, min(start, total_duration)), max(min(end, total_duration), start)]
                           for start, end in clip_ranges]
        else:
            clip_ranges = [[i, min(i + clip_length, total_duration)] for i in range(0, total_duration, clip_length)]

        for start_time, end_time in clip_ranges:
            sub_clip = clip.subclipped(start_time, end_time)
            clip_filename = os.path.join(CLIPS_PATH, f"{video_id}_clip_{start_time}s_{end_time}s.mp4")
            sub_clip.write_videofile(clip_filename, codec="libx264", audio_codec="aac")

            # ✅ Extract and Transcribe Clip Audio
            audio_path = clip_filename.replace(".mp4", ".wav")
            sub_clip.audio.write_audiofile(audio_path)

            log_message(video_id, f"Transcribing clip {clip_filename}...")
            result = model.transcribe(audio_path)
            clip_transcript = result.get('text', "No speech detected.")

            highlight_clips.append({
                "clip": clip_filename,
                "start_time": start_time,
                "end_time": end_time,
                "transcript": clip_transcript
            })

    except Exception as e:
        log_message(video_id, f"Error generating clips: {str(e)}")
        return

    # ✅ Step 5: Save Processed Data
    videos_collection.insert_one({
        "video_id": video_id,
        "url": video_url,
        "total_duration": total_duration,
        "full_transcription": full_transcription,
        "highlight_clips": highlight_clips,
        "status": "processed"
    })

    log_message(video_id, "Processing complete.")

# ✅ Submit Video API
@csrf_exempt
@require_http_methods(["POST"])
def submit_video(request):
    """
    ✅ Handles YouTube Video Submission
    - Accepts POST request with YouTube `url`
    - Starts **background processing thread** (non-blocking)
    """
    try:
        data = json.loads(request.body)
        video_url = data.get('url')
        clip_length = data.get('clip_length', 30)
        clip_ranges = data.get('clip_ranges', None)

        if not video_url:
            return JsonResponse({"error": "Missing video URL"}, status=400)

        video_id = str(uuid.uuid4())  # Generate unique video ID

        processing_thread = threading.Thread(target=process_video, args=(video_id, video_url, clip_length, clip_ranges))
        processing_thread.start()

        return JsonResponse({
            "video_id": video_id,
            "message": "Processing started in background"
        })
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON format")
    except Exception as e:
        return JsonResponse({"error": f"Unexpected error: {str(e)}"}, status=500)


