from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from video_ai.views import (  # Directly import views
    home_view, processing_page, download_page,
    submit_video, upload_video, get_logs, list_clips, download_clip,
    get_video_results, get_full_transcription
)

urlpatterns = [
    # ✅ Admin panel
    path('admin/', admin.site.urls),

    # ✅ Page Views
    path('', home_view, name='home'),
    path('process/', processing_page, name='processing_page'),
    path('download/', download_page, name='download_page'),

    # ✅ API Endpoints
    path('upload/', upload_video, name='upload_video'),  # ✅ New Upload Video Endpoint
    path('submit/', submit_video, name='submit_video'),
    path('logs/<str:video_id>/', get_logs, name='get_logs'),
    path('clips/<str:video_id>/', list_clips, name='list_clips'),
    path('download/<str:clip_name>/', download_clip, name='download_clip'),
    path('video-results/<str:video_id>/', get_video_results, name='get_video_results'),
    path('full-transcription/<str:video_id>/', get_full_transcription, name='get_full_transcription'),
]

# ✅ Serve media files in development mode
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
