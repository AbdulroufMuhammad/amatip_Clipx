from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.http import JsonResponse
import uuid
import os

# Simulated storage for uploaded videos
VIDEO_STORAGE = {}

def home_view(request):
    """Render the landing page."""
    return render(request, "index.html")

def upload_video(request):
    """Handles video uploads and URL submissions."""
    if request.method == "POST":
        video_id = str(uuid.uuid4())  # Generate unique video ID
        video_url = None

        if "video" in request.FILES:
            video_file = request.FILES["video"]
            video_path = f"media/uploads/{video_file.name}"
            
            # Save file manually
            with open(video_path, "wb+") as destination:
                for chunk in video_file.chunks():
                    destination.write(chunk)

            video_url = f"/{video_path}"  # Accessible path for frontend
        elif "url" in request.POST and request.POST["url"].strip():
            video_url = request.POST["url"]
        else:
            return JsonResponse({"error": "Please upload a video or enter a URL."}, status=400)

        # Store the video info
        VIDEO_STORAGE[video_id] = {"url": video_url}

        # ✅ Return JSON with redirect URL
        return JsonResponse({"redirect": f"/process/?video_id={video_id}"})

    return JsonResponse({"error": "Only POST requests allowed"}, status=405)

def processing_status(request):
    """Handles checking the status of a video processing task."""
    video_id = request.GET.get("video_id")
    if video_id in VIDEO_STORAGE:
        return JsonResponse({
            "video_id": video_id, 
            "status": "Processing Complete", 
            "url": VIDEO_STORAGE[video_id]["url"]
        })
    return JsonResponse({"error": "Video not found"}, status=404)

def processing_page(request):
    """Render process.html with the video ID or YouTube URL."""
    video_id = request.GET.get("video_id")
    video_url = request.GET.get("url")

    if video_id:
        video_data = VIDEO_STORAGE.get(video_id)
        if not video_data:
            return redirect("home")  # Redirect if video not found
        video_url = video_data["url"]

    if not video_url:
        return redirect("home")  # Redirect if no video is provided

    return render(request, "process.html", {"video_id": video_id, "video_url": video_url})

def list_clips(request, video_id):
    """Retrieve processed video clip info."""
    clip_path = f"media/clips/{video_id}_clipped.mp4"
    thumbnail_path = f"media/clips/{video_id}_thumbnail.jpg"

    if os.path.exists(clip_path):
        return JsonResponse({
            "clip_url": f"/{clip_path}",
            "thumbnail": f"/{thumbnail_path}" if os.path.exists(thumbnail_path) else ""
        })

    return JsonResponse({"error": "Clip not found"}, status=404)

def download_page(request):
    """Render the download page (placeholder)."""
    return render(request, "download.html")
