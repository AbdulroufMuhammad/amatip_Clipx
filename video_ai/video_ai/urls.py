from django.contrib import admin
from django.urls import path
from django.http import JsonResponse
from processing.views import (
    submit_video, get_status, get_logs, list_clips, 
    download_clip, get_video_results
)

# ✅ Home View (Landing Page)
def home(request):
    return JsonResponse({"message": "Welcome to the Video Processing API!"})

# ✅ URL Patterns
urlpatterns = [
    path('admin/', admin.site.urls),  # Django Admin Panel
    path('', home, name='home'),  # API Home
    path('submit/', submit_video, name='submit_video'),  # Video Submission
    path('status/<str:video_id>/', get_status, name='get_status'),  # Get Video Status
    path('logs/<str:video_id>/', get_logs, name='get_logs'),  # Retrieve Logs
    path('clips/<str:video_id>/', list_clips, name='list_clips'),  # List Video Clips
    path('download/<str:clip_name>/', download_clip, name='download_clip'),  # Download Clip
    path('video-results/<str:video_id>/', get_video_results, name='get_video_results'),  # Video Processing Results
]
