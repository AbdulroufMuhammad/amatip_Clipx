from django.http import JsonResponse, FileResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import render, redirect
import uuid
import os
import json
import threading
from django.conf import settings
from pymongo import MongoClient
from processing.tasks import process_video
import os
import uuid
import json
import threading
from django.conf import settings
from django.http import JsonResponse, FileResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from pymongo import MongoClient
from processing.tasks import process_video  
# Database Connection
# MongoDB Setup
client = MongoClient(settings.MONGO_URI)
db = client['video_ai']
videos_collection = db['videos']
logs_collection = db['logs']



VIDEO_STORAGE = {}

# ========== RENDERING PAGES ========== #
def home_view(request):
    """Render the landing page."""
    return render(request, "index.html")

def processing_page(request):
    """Render process.html with video details."""
    video_id = request.GET.get("video_id")
    video_url = request.GET.get("url")

    if video_id:
        video_data = VIDEO_STORAGE.get(video_id)
        if not video_data:
            return redirect("home")
        video_url = video_data["url"]

    if not video_url:
        return redirect("home")

    return render(request, "process.html", {"video_id": video_id, "video_url": video_url})

def download_page(request):
    """Render the download page (placeholder)."""
    return render(request, "download.html")

# ========== VIDEO UPLOAD & PROCESSING ========== #



@csrf_exempt
@require_http_methods(["POST"])
def submit_video(request):
    """
    Handles video submission via URL.
    - Accepts POST request with 'url', 'clip_length', and 'clip_ranges'.
    - Starts video processing in a separate thread without checking the database.
    """
    try:
        data = json.loads(request.body)
        video_url = data.get('url')
        clip_length = data.get('clip_length', 30)
        clip_ranges = data.get('clip_ranges', None)  # ✅ Allows manual time ranges

        if not video_url:
            return JsonResponse({"error": "Missing video URL"}, status=400)

        clip_length = int(clip_length)

        # ✅ Validate `clip_ranges` if provided
        if clip_ranges:
            if not isinstance(clip_ranges, list) or not all(isinstance(i, list) and len(i) == 2 for i in clip_ranges):
                return JsonResponse({"error": "Invalid clip_ranges format. Expected list of [start, end] pairs."}, status=400)

            validated_ranges = []
            for start, end in clip_ranges:
                try:
                    start, end = float(start), float(end)
                    if start >= end or start < 0:
                        return JsonResponse({"error": f"Invalid range [{start}, {end}]. Start must be less than end and non-negative."}, status=400)
                    validated_ranges.append([start, end])
                except ValueError:
                    return JsonResponse({"error": "Clip ranges must contain valid numbers."}, status=400)

            clip_ranges = validated_ranges  # Update with validated values

        video_id = str(uuid.uuid4())  # Generate a new video ID for this request

        # ✅ Start video processing in a separate thread, pass video_url directly
        processing_thread = threading.Thread(target=process_video, args=(video_id, video_url, clip_length, clip_ranges))
        processing_thread.start()

        return JsonResponse({
            "video_id": video_id,
            "message": "Processing started in background"
        }, content_type="application/json")

    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON format")
    except ValueError:
        return JsonResponse({"error": "Invalid clip length format"}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"Unexpected error: {str(e)}"}, status=500)


# @require_http_methods(["GET"])
# def get_status(request, video_id):
#     """
#     Retrieves the status of a submitted video.
#     """
#     try:
#         video_data = videos_collection.find_one({"video_id": video_id}, {"_id": 0})

#         if not video_data:
#             return JsonResponse({"error": "Video not found"}, status=404)

#         return JsonResponse(video_data, content_type="application/json")

#     except Exception as e:
#         return JsonResponse({"error": f"Unexpected error: {str(e)}"}, status=500)


@require_http_methods(["GET"])
def get_logs(request, video_id):
    """
    Fetches processing logs for a given video.
    """
    try:
        logs = list(logs_collection.find({"video_id": video_id}, {"_id": 0}))

        if not logs:
            return JsonResponse({"error": "No logs found for this video"}, status=404)

        return JsonResponse({"logs": logs}, content_type="application/json")

    except Exception as e:
        return JsonResponse({"error": f"Unexpected error: {str(e)}"}, status=500)


@require_http_methods(["GET"])
def list_clips(request, video_id):
    """
    Lists all clips generated for a given video.
    """
    try:
        video_data = videos_collection.find_one({"video_id": video_id}, {"_id": 0, "highlight_clips": 1})

        if not video_data or "highlight_clips" not in video_data:
            return JsonResponse({"error": "No clips found for this video"}, status=404)

        return JsonResponse({"clips": video_data["highlight_clips"]}, content_type="application/json")

    except Exception as e:
        return JsonResponse({"error": f"Unexpected error: {str(e)}"}, status=500)


@require_http_methods(["GET"])
def download_clip(request, clip_name):
    """
    Provides a download link for a generated video clip.
    """
    try:
        clip_path = os.path.join(settings.MEDIA_ROOT, "clips", clip_name)

        if os.path.exists(clip_path):
            return FileResponse(open(clip_path, "rb"), as_attachment=True)

        return JsonResponse({"error": "Clip not found"}, status=404)

    except Exception as e:
        return JsonResponse({"error": f"Unexpected error: {str(e)}"}, status=500)


@require_http_methods(["GET"])
def get_video_results(request, video_id):
    """
    Fetch processed video data.
    """
    try:
        video_data = videos_collection.find_one({"video_id": video_id}, {"_id": 0})

        if not video_data:
            return JsonResponse({"error": "Video not found"}, status=404)

        return JsonResponse({
            "video_id": video_id,
            "total_duration": video_data.get("total_duration", None),
            "transcript": video_data.get("full_transcription", "Not available"),
            "summary": video_data.get("summary", "Not available"),
            "highlight_clips": video_data.get("highlight_clips", [])
        }, content_type="application/json")

    except Exception as e:
        return JsonResponse({"error": f"Unexpected error: {str(e)}"}, status=500)


@require_http_methods(["GET"])
def get_clips_and_transcription(request, video_id):
    """
    Returns all clips and their corresponding transcriptions for a given video.
    """
    try:
        video_data = videos_collection.find_one({"video_id": video_id}, {"_id": 0, "highlight_clips": 1})

        if not video_data or "highlight_clips" not in video_data:
            return JsonResponse({"error": "No clips found for this video"}, status=404)

        return JsonResponse({
            "video_id": video_id,
            "clips": video_data["highlight_clips"]
        }, content_type="application/json")

    except Exception as e:
        return JsonResponse({"error": f"Unexpected error: {str(e)}"}, status=500)


@require_http_methods(["GET"])
def get_full_transcription(request, video_id):
    """
    Returns the full transcription of a processed video.
    """
    try:
        video_data = videos_collection.find_one({"video_id": video_id}, {"_id": 0, "full_transcription": 1})

        if not video_data or "full_transcription" not in video_data:
            return JsonResponse({"error": "Full transcription not found for this video"}, status=404)

        return JsonResponse({
            "video_id": video_id,
            "full_transcription": video_data["full_transcription"]
        }, content_type="application/json")

    except Exception as e:
        return JsonResponse({"error": f"Unexpected error: {str(e)}"}, status=500)

# video_ai/views.py

@csrf_exempt
@require_http_methods(["POST"])
def upload_video(request):
    """Handles video uploads and URL submissions."""
    video_id = str(uuid.uuid4())
    video_url = None

    # Check if the video is being uploaded through the form
    if "video" in request.FILES:
        video_file = request.FILES["video"]
        video_path = os.path.join("media/uploads", video_file.name)

        with open(video_path, "wb+") as destination:
            for chunk in video_file.chunks():
                destination.write(chunk)

        video_url = f"/{video_path}"
    # Check if a URL was provided instead of an upload
    elif "url" in request.POST and request.POST["url"].strip():
        video_url = request.POST["url"]
    else:
        return JsonResponse({"error": "Please upload a video or enter a URL."}, status=400)

    VIDEO_STORAGE[video_id] = {"url": video_url}
    return JsonResponse({"redirect": f"/process/?video_id={video_id}"})
