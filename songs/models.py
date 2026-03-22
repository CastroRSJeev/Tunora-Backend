from django.db import models
from django.conf import settings
from django_mongodb_backend.fields import ArrayField

class Song(models.Model):
    title = models.CharField(max_length=255)
    artist = models.CharField(max_length=255)
    genre = models.CharField(max_length=255, blank=True, default='')
    cover_url = models.URLField(max_length=500, blank=True, default='')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='songs')
    audio_url = models.URLField(max_length=500, blank=True, null=True)
    duration = models.CharField(max_length=10, blank=True, default='')
    description = models.TextField(blank=True, default='')
    embedding = ArrayField(models.FloatField(), size=384, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'songs'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.artist}"
