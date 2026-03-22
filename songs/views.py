from django.db.models import Q
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
import cloudinary.uploader
from .models import Song
from .serializers import SongSerializer
from recommendations.ml import embed

class SongViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows songs to be viewed.
    """
    serializer_class = SongSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None

    def get_queryset(self):
        queryset = Song.objects.all()
        genres = self.request.query_params.getlist('genres')
        authors = self.request.query_params.getlist('authors')

        if genres:
            genre_q = Q()
            for g in genres:
                genre_q |= Q(genre__icontains=g)  # JSONField supports icontains on serialized value
            queryset = queryset.filter(genre_q)

        if authors:
            author_q = Q()
            for a in authors:
                author_q |= Q(artist__icontains=a)
            queryset = queryset.filter(author_q)
            
        return queryset

    @action(detail=False, methods=['get'])
    def genres(self, request):
        """Get unique genres from available songs."""
        genres = Song.objects.values_list('genre', flat=True).distinct()
        unique_genres = set()
        for g in genres:
            if g:
                for part in g.split(','):
                    unique_genres.add(part.strip())
        return Response(sorted(list(unique_genres)))

    @action(detail=False, methods=['get'])
    def authors(self, request):
        """Get unique authors (artists) from available songs."""
        authors = Song.objects.values_list('artist', flat=True).distinct()
        return Response(sorted(list(set(filter(None, authors)))))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_song(request):
    """Artist-only: upload a song with cover image and audio file."""
    if request.user.role != 'artist':
        return Response({'error': 'Only artists can upload songs.'}, status=status.HTTP_403_FORBIDDEN)

    title = request.data.get('title', '').strip()
    artist = request.data.get('artist', '').strip() or request.user.username
    genre = request.data.get('genre', '').strip()
    description = request.data.get('description', '').strip()
    cover_file = request.FILES.get('cover')
    audio_file = request.FILES.get('audio')

    if not title:
        return Response({'error': 'Title is required.'}, status=status.HTTP_400_BAD_REQUEST)
    if not artist:
        return Response({'error': 'Artist name is required.'}, status=status.HTTP_400_BAD_REQUEST)
    if not audio_file:
        return Response({'error': 'Audio file is required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        audio_result = cloudinary.uploader.upload(
            audio_file,
            resource_type='video',
            folder='tunora/audio',
        )
        audio_url = audio_result.get('secure_url', '')

        cover_url = ''
        if cover_file:
            cover_result = cloudinary.uploader.upload(
                cover_file,
                folder='tunora/covers',
            )
            cover_url = cover_result.get('secure_url', '')

        song_embedding = embed(f"{genre} {description}")

        song = Song.objects.create(
            title=title,
            artist=artist,
            genre=genre,
            description=description,
            audio_url=audio_url,
            cover_url=cover_url,
            duration='',
            uploaded_by=request.user,
            embedding=song_embedding,
        )

        return Response(SongSerializer(song).data, status=status.HTTP_201_CREATED)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({'error': f'Upload failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_songs(request):
    """Return songs uploaded by the current artist."""
    if request.user.role != 'artist':
        return Response({'error': 'Only artists can access this.'}, status=status.HTTP_403_FORBIDDEN)
    songs = Song.objects.filter(uploaded_by=request.user)
    return Response(SongSerializer(songs, many=True).data)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def edit_song(request, song_id):
    """Artist-only: edit metadata of their own song. Optionally replace cover."""
    if request.user.role != 'artist':
        return Response({'error': 'Only artists can edit songs.'}, status=status.HTTP_403_FORBIDDEN)
    try:
        song = Song.objects.get(id=song_id, uploaded_by=request.user)
    except Song.DoesNotExist:
        return Response({'error': 'Song not found or not yours.'}, status=status.HTTP_404_NOT_FOUND)

    for field in ('title', 'artist', 'genre', 'description'):
        val = request.data.get(field)
        if val is not None:
            setattr(song, field, val.strip())

    cover_file = request.FILES.get('cover')
    if cover_file:
        try:
            result = cloudinary.uploader.upload(cover_file, folder='tunora/covers')
            song.cover_url = result.get('secure_url', song.cover_url)
        except Exception as e:
            return Response({'error': f'Cover upload failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    song.save()
    return Response(SongSerializer(song).data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_song(request, song_id):
    """Artist-only: delete their own song."""
    if request.user.role != 'artist':
        return Response({'error': 'Only artists can delete songs.'}, status=status.HTTP_403_FORBIDDEN)
    try:
        song = Song.objects.get(id=song_id, uploaded_by=request.user)
    except Song.DoesNotExist:
        return Response({'error': 'Song not found or not yours.'}, status=status.HTTP_404_NOT_FOUND)
    song.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
