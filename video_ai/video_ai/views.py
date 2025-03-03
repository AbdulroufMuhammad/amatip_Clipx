import os
import uuid
import json
import threading
from datetime import datetime

from django.conf import settings
from django.http import JsonResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.shortcuts import render
from pymongo import MongoClient
from processing.tasks import process_video

# ============================
# ✅ MongoDB Setup
# ============================
client = MongoClient(settings.MONGO_URI)
db = client["video_ai"]
videos_collection = db["videos"]
logs_collection = db["logs"]

# ============================
# ✅ Define Paths
# ============================
MEDIA_ROOT = settings.MEDIA_ROOT
DOWNLOAD_PATH = os.path.join(MEDIA_ROOT, "downloads")
CLIPS_PATH = os.path.join(MEDIA_ROOT, "clips")
UPLOADS_PATH = os.path.join(MEDIA_ROOT, "uploads")

# Ensure directories exist
os.makedirs(DOWNLOAD_PATH, exist_ok=True)
os.makedirs(CLIPS_PATH, exist_ok=True)
os.makedirs(UPLOADS_PATH, exist_ok=True)

# ============================
# ✅ Logging Helper
# ============================
def log_message(video_id, message):
    """ Save logs to MongoDB and print for debugging. """
    logs_collection.insert_one({
        "video_id": video_id,
        "message": message,
        "timestamp": datetime.utcnow(),
    })
    print(f"[{datetime.utcnow()}] [{video_id}] {message}")

# ============================
# ✅ VIDEO UPLOAD FUNCTIONALITY
# ============================

@csrf_exempt
@require_http_methods(["POST"])
def upload_video(request):
    """Handles direct video uploads."""
    if "video" not in request.FILES:
        return JsonResponse({"error": "No video file provided"}, status=400)

    video_file = request.FILES["video"]
    file_ext = os.path.splitext(video_file.name)[1].lower()

    if file_ext not in [".mp4", ".mov", ".avi"]:
        return JsonResponse({"error": "Invalid file format. Only MP4, MOV, and AVI are allowed."}, status=400)

    video_id = str(uuid.uuid4())  # Unique video ID
    file_path = os.path.join(UPLOADS_PATH, f"{video_id}{file_ext}")

    # Save the uploaded file
    default_storage.save(file_path, ContentFile(video_file.read()))

    return JsonResponse({
        "video_id": video_id,
        "file_path": file_path,
        "message": "Video uploaded successfully"
    })

# ============================
# ✅ VIDEO SUBMISSION & PROCESSING
# ============================

@csrf_exempt
@require_http_methods(["POST"])
def submit_video(request):
    """Handles AI-powered video clipping or manual segmentation."""
    try:
        data = json.loads(request.body)
        video_url = data.get("video_url")
        file_path = data.get("file_path")
        clip_length = int(data.get("clip_length", 30))  # Default: 30s
        speech_language = data.get("speech_language", "English")
        prompt = data.get("custom_prompt", "").strip()
        timeframe = data.get("timeframe", None)

        if not video_url and not file_path:
            return JsonResponse({"error": "❌ Missing video input. Provide either 'video_url' or 'file_path'."}, status=400)

        video_id = str(uuid.uuid4())
        use_ai = bool(prompt)  # ✅ Auto-detect AI mode based on prompt presence

        processing_thread = threading.Thread(
            target=process_video, 
            args=(video_id, video_url, file_path, clip_length, timeframe, speech_language, prompt)
        )
        processing_thread.start()

        return JsonResponse({
            "video_id": video_id,
            "message": "🚀 Video processing started in background",
            "use_ai": use_ai,
            "clip_length": clip_length,
            "timeframe": timeframe,
            "prompt": prompt
        }, content_type="application/json")

    except json.JSONDecodeError:
        return JsonResponse({"error": "❌ Invalid JSON format"}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"❌ Unexpected error: {str(e)}"}, status=500)

# ============================
# ✅ API Endpoints
# ============================

@require_http_methods(["GET"])
def get_logs(request, video_id):
    """Fetches processing logs for a given video."""
    try:
        logs = list(logs_collection.find({"video_id": video_id}, {"_id": 0}))
        return JsonResponse({"logs": logs}, content_type="application/json") if logs else JsonResponse({"error": "No logs found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": f"Unexpected error: {str(e)}"}, status=500)

@require_http_methods(["GET"])
def list_clips(request, video_id):
    """Lists all AI-generated clips for a video, including download links and transcriptions."""
    try:
        video_data = videos_collection.find_one({"video_id": video_id}, {"_id": 0, "highlight_clips": 1})
        if video_data and "highlight_clips" in video_data:
            return JsonResponse({"clips": video_data["highlight_clips"]}, content_type="application/json")
        return JsonResponse({"error": "No clips found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": f"Unexpected error: {str(e)}"}, status=500)

@require_http_methods(["GET"])
def get_video_results(request, video_id):
    """Fetch processed video data with AI-curated highlights."""
    try:
        video_data = videos_collection.find_one({"video_id": video_id}, {"_id": 0})
        return JsonResponse(video_data, content_type="application/json") if video_data else JsonResponse({"error": "Video not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": f"Unexpected error: {str(e)}"}, status=500)

@require_http_methods(["GET"])
def get_full_transcription(request, video_id):
    """Returns the full transcription of a processed video."""
    try:
        video_data = videos_collection.find_one({"video_id": video_id}, {"_id": 0, "full_transcription": 1})
        return JsonResponse({"full_transcription": video_data["full_transcription"]}, content_type="application/json") if video_data else JsonResponse({"error": "Full transcription not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": f"Unexpected error: {str(e)}"}, status=500)

@require_http_methods(["GET"])
def download_clip(request, clip_name):
    """Provides a download link for a generated AI-clipped video."""
    try:
        clip_path = os.path.join(CLIPS_PATH, clip_name)
        return FileResponse(open(clip_path, "rb"), as_attachment=True) if os.path.exists(clip_path) else JsonResponse({"error": "Clip not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": f"Unexpected error: {str(e)}"}, status=500)

# ========== RENDERING PAGES ========== #
def home_view(request):
    """Render the landing page."""
    return render(request, "index.html")

def processing_page(request):
    """Render process.html with video details."""
    return render(request, "process.html")

def download_page(request):
    """Render the download page."""
    return render(request, "download.html")
