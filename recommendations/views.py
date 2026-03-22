from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from songs.models import Song
from songs.serializers import SongSerializer
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

    # Only consider songs that have been embedded
    songs = Song.objects.exclude(embedding=None)

    scored = sorted(
        [(_cosine(query_embedding, song.embedding), song) for song in songs],
        key=lambda x: x[0],
        reverse=True
    )

    top_songs = [song for _, song in scored[:10]]
    serializer = SongSerializer(top_songs, many=True)
    return Response({'results': serializer.data, 'prompt': prompt})
