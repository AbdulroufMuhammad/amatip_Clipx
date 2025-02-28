from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from video_ai.views import home_view, upload_video, processing_page, download_page
from video_ai.views import (
    submit_video, get_logs, list_clips, download_clip, 
    get_video_results, get_clips_and_transcription, get_full_transcription
)

urlpatterns = [
    path('admin/', admin.site.urls),  # Django Admin Panel
    path('', home_view, name='home'),
    path('upload/', upload_video, name='upload_video'),
    path('process/', processing_page, name='processing_page'),
    path('download/', download_page, name='download_page'),

    # API Endpoints for video processing
    path('submit/', submit_video, name='submit_video'),  # Video Submission
    path('logs/<str:video_id>/', get_logs, name='get_logs'),  # Retrieve Logs
    path('clips/<str:video_id>/', list_clips, name='list_clips'),  # List Video Clips
    path('download/<str:clip_name>/', download_clip, name='download_clip'),  # Download Clip
    path('video-results/<str:video_id>/', get_video_results, name='get_video_results'),  # Video Processing Results
    path('clips-and-transcription/<str:video_id>/', get_clips_and_transcription, name='get_clips_and_transcription'),  # ✅ Fetch Clips + Transcription
    path('full-transcription/<str:video_id>/', get_full_transcription, name='get_full_transcription'),  # ✅ Fetch Full Transcription
]

# ✅ Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
