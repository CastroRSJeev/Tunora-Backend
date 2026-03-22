from rest_framework import serializers
from .models import Song

class SongSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    uploaded_by = serializers.SerializerMethodField()

    class Meta:
        model = Song
        fields = ['id', 'title', 'artist', 'genre', 'cover_url', 'audio_url', 'duration', 'description', 'created_at', 'uploaded_by']

    def get_uploaded_by(self, obj):
        if obj.uploaded_by:
            return {'id': str(obj.uploaded_by.id), 'username': obj.uploaded_by.username}
        return None
