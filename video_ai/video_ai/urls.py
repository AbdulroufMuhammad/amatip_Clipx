from django.contrib import admin
from django.urls import path
from video_ai.views import (
    home_view, upload_video, processing_status, processing_page, download_page
)
from processing.views import (
    submit_video, get_status, list_clips, download_clip
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view, name='home'),
    path('upload/', upload_video, name='upload_video'),
    path('process/', processing_page, name='processing_page'),
    path('status/', processing_status, name='processing_status'),
    path('download/', download_page, name='download_page'),

    # API Endpoints for video processing
    path('api/submit/', submit_video, name='submit_video'),
    path('api/status/<str:video_id>/', get_status, name='get_status'),
    path('api/clips/<str:video_id>/', list_clips, name='list_clips'),
    path('api/download/<str:clip_name>/', download_clip, name='download_clip'),
]
