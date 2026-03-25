from django.db import models
from django.conf import settings
from django_mongodb_backend.fields import ArrayField
import uuid

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
    play_count = models.IntegerField(default=0)
    like_count = models.IntegerField(default=0)
    is_blocked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'songs'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.artist}"


class SongPlay(models.Model):
    """Records each play/stream event for analytics."""
    song = models.ForeignKey(Song, on_delete=models.CASCADE, related_name='plays')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    played_at = models.DateTimeField(auto_now_add=True)
    duration_listened = models.FloatField(default=0, help_text="Seconds the user listened")

    class Meta:
        db_table = 'song_plays'
        ordering = ['-played_at']

    def __str__(self):
        return f"Play: {self.song.title} at {self.played_at}"

class SongLike(models.Model):
    """Records user likes for a song."""
    song = models.ForeignKey(Song, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'song_likes'
        unique_together = ('song', 'user')

    def __str__(self):
        return f"{self.user.username} likes {self.song.title}"


class Playlist(models.Model):
    """A curated playlist created by a listener (or any user)."""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='playlists')
    songs = models.ManyToManyField(Song, through='PlaylistSong', related_name='playlists', blank=True)
    is_public = models.BooleanField(default=False)
    cover_url = models.URLField(max_length=500, blank=True, default='')  # Optional custom cover
    embedding = ArrayField(models.FloatField(), size=384, blank=True, null=True)  # For AI search
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'playlists'
        ordering = ['-updated_at']

    def __str__(self):
        visibility = 'public' if self.is_public else 'private'
        return f"{self.name} by {self.owner.username} ({visibility})"


class PlaylistSong(models.Model):
    """Through model that maintains song order within a playlist."""
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE, related_name='playlist_songs')
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    position = models.IntegerField(default=0)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'playlist_songs'
        unique_together = ('playlist', 'song')
        ordering = ['position', 'added_at']

    def __str__(self):
        return f"{self.song.title} in {self.playlist.name} @ pos {self.position}"

