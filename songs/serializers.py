from rest_framework import serializers
from .models import Song, SongLike, Playlist, PlaylistSong

class SongSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    uploaded_by = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Song
        fields = ['id', 'title', 'artist', 'genre', 'cover_url', 'audio_url', 'duration', 'description', 'created_at', 'uploaded_by', 'play_count', 'like_count', 'is_liked']

    def get_uploaded_by(self, obj):
        if obj.uploaded_by:
            return {'id': str(obj.uploaded_by.id), 'username': obj.uploaded_by.username}
        return None

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # Check cached attribute first (for optimized viewsets if we ever add annotations)
            if hasattr(obj, 'is_liked_by_user'):
                return obj.is_liked_by_user
            return obj.likes.filter(user=request.user).exists()
        return False


class PlaylistSongSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    song = SongSerializer(read_only=True)
    song_id = serializers.CharField(write_only=True)

    class Meta:
        model = PlaylistSong
        fields = ['id', 'song', 'song_id', 'position', 'added_at']


class PlaylistSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    owner = serializers.SerializerMethodField()
    songs = serializers.SerializerMethodField()
    song_count = serializers.SerializerMethodField()

    class Meta:
        model = Playlist
        fields = ['id', 'name', 'description', 'is_public', 'cover_url', 'owner', 'songs', 'song_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']

    def get_owner(self, obj):
        return {'id': str(obj.owner.id), 'username': obj.owner.username}

    def get_songs(self, obj):
        playlist_songs = obj.playlist_songs.select_related('song').order_by('position', 'added_at')
        return PlaylistSongSerializer(playlist_songs, many=True, context=self.context).data

    def get_song_count(self, obj):
        return obj.playlist_songs.count()
