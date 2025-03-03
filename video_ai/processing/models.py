from datetime import datetime
from mongoengine import Document, fields
import uuid

class Video(Document):
    """ Stores video metadata after processing. """
    video_id = fields.UUIDField(default=lambda: uuid.uuid4(), unique=True, required=True)
    url = fields.URLField(required=True)
    total_duration = fields.IntField(required=False, default=0)  # Matches tasks.py storage
    
    STATUS_CHOICES = ('pending', 'processing', 'processed', 'failed')
    status = fields.StringField(max_length=50, choices=STATUS_CHOICES, default="pending")
    
    full_transcription = fields.StringField(required=False, default="")  # Matches process_video function
    highlight_clips = fields.ListField(fields.DictField(), required=False, default=[])  # Stores AI-clipped segments

    created_at = fields.DateTimeField(default=datetime.utcnow)

    meta = {'collection': 'videos'}  # Ensures MongoDB consistency


class VideoLog(Document):
    """ Stores processing logs for debugging. """
    video_id = fields.UUIDField(required=True, index=True)  # Fast lookup
    message = fields.StringField(required=True)
    timestamp = fields.DateTimeField(default=datetime.utcnow)

    meta = {'collection': 'video_logs'}  # Matches logs_collection in tasks.py
