from django.db import models
import uuid

class Video(models.Model):
    video_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    url = models.URLField()
    status = models.CharField(max_length=50, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

class VideoLog(models.Model):
    video_id = models.UUIDField()
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
