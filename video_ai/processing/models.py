from datetime import datetime
from mongoengine import Document, fields
import uuid

class Video(Document):
    video_id = fields.UUIDField(default=uuid.uuid4, unique=True)
    url = fields.URLField()
    status = fields.StringField(max_length=50, default="pending")
    created_at = fields.DateTimeField(default=datetime.utcnow)

class VideoLog(Document):
    video_id = fields.UUIDField()
    message = fields.StringField()
    timestamp = fields.DateTimeField(default=datetime.utcnow)
