from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from songs.models import Song, Playlist
from songs.serializers import SongSerializer, PlaylistSerializer
from .ml import embed
import numpy as np


def _cosine(a, b):
    a, b = np.array(a), np.array(b)
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    return float(np.dot(a, b) / denom) if denom else 0.0


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ai_recommend(request):
    prompt = (request.data.get('prompt') or '').strip()
    if not prompt:
        return Response({'error': 'Prompt is required.'}, status=status.HTTP_400_BAD_REQUEST)

    query_embedding = embed(prompt)

    # Consider songs
    songs = Song.objects.exclude(embedding=None)
    scored_songs = sorted(
        [(_cosine(query_embedding, song.embedding), song) for song in songs],
        key=lambda x: x[0],
        reverse=True
    )
    top_songs = [song for _, song in scored_songs[:10]]
    song_serializer = SongSerializer(top_songs, many=True, context={'request': request})

    # Consider public playlists
    playlists = Playlist.objects.filter(is_public=True).exclude(embedding=None)
    scored_playlists = sorted(
        [(_cosine(query_embedding, pl.embedding), pl) for pl in playlists],
        key=lambda x: x[0],
        reverse=True
    )
    # Only return playlists that have some relevance score > 0.4, or just top 5
    filtered_playlists = [pl for score, pl in scored_playlists if score > 0.35][:5]
    playlist_serializer = PlaylistSerializer(filtered_playlists, many=True, context={'request': request})

    return Response({
        'results': song_serializer.data,  # keep for backward compatibility if needed
        'songs': song_serializer.data,
        'playlists': playlist_serializer.data,
        'prompt': prompt
    })
