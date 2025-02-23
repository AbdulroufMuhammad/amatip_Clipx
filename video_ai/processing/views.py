import os
import uuid
import json
import threading
from django.conf import settings
from django.http import JsonResponse, FileResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from pymongo import MongoClient
from .tasks import process_video  # ✅ Ensure correct import path

# MongoDB Setup
client = MongoClient(settings.MONGO_URI)
db = client['video_ai']
videos_collection = db['videos']
logs_collection = db['logs']

@csrf_exempt
@require_http_methods(["POST"])
def submit_video(request):
    """
    Handles video submission via URL.
    - Accepts POST request with 'url', 'clip_length', and 'clip_ranges'.
    - Starts video processing in a separate thread.
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
            
            # Convert start/end values to floats and validate their order
            validated_ranges = []
            for start, end in clip_ranges:
                try:
                    start, end = float(start), float(end)  # Convert to float if needed
                    if start >= end or start < 0:
                        return JsonResponse({"error": f"Invalid range [{start}, {end}]. Start must be less than end and non-negative."}, status=400)
                    validated_ranges.append([start, end])
                except ValueError:
                    return JsonResponse({"error": "Clip ranges must contain valid numbers."}, status=400)
            
            clip_ranges = validated_ranges  # Update with validated values

        video_id = str(uuid.uuid4())

        # ✅ Fetch total duration before processing for frontend range limit
        total_duration = None  # Default None (will be fetched later)
        processing_thread = threading.Thread(target=process_video, args=(video_id, clip_length, clip_ranges))
        processing_thread.start()

        video_data = {
            "video_id": video_id,
            "url": video_url,
            "status": "pending",
            "total_duration": total_duration,  # ✅ This will be updated after processing
            "clips": [],
        }
        videos_collection.insert_one(video_data)

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


@require_http_methods(["GET"])
def get_status(request, video_id):
    """
    Retrieves the status of a submitted video.
    - Checks MongoDB for video processing status.
    """
    try:
        video_data = videos_collection.find_one({"video_id": video_id}, {"_id": 0})

        if not video_data:
            return JsonResponse({"error": "Video not found"}, status=404)

        return JsonResponse(video_data, content_type="application/json")

    except Exception as e:
        return JsonResponse({"error": f"Unexpected error: {str(e)}"}, status=500)


@require_http_methods(["GET"])
def get_logs(request, video_id):
    """
    Fetches processing logs for a given video.
    - Returns all logs stored in MongoDB for the video.
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
    - Retrieves clips stored in MongoDB.
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
    - Checks if the clip exists and returns a file response.
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
            "total_duration": video_data.get("total_duration", None),  # ✅ Added total duration
            "transcript": video_data.get("full_transcription", "Not available"),  # ✅ Renamed to avoid confusion
            "summary": video_data.get("summary", "Not available"),
            "highlight_clips": video_data.get("highlight_clips", [])
        }, content_type="application/json")

    except Exception as e:
        return JsonResponse({"error": f"Unexpected error: {str(e)}"}, status=500)
