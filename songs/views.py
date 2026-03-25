from django.db.models import Q, Sum, Count, F
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
import cloudinary.uploader
from datetime import timedelta
from .models import Song, SongPlay, SongLike, Playlist, PlaylistSong
from .serializers import SongSerializer, PlaylistSerializer
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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def record_play(request, song_id):
    """Record a play/stream event for a song."""
    try:
        song = Song.objects.get(id=song_id)
    except Song.DoesNotExist:
        return Response({'error': 'Song not found.'}, status=status.HTTP_404_NOT_FOUND)

    duration_listened = float(request.data.get('duration_listened', 0))

    SongPlay.objects.create(
        song=song,
        user=request.user,
        duration_listened=duration_listened,
    )

    # Increment play count
    song.play_count = F('play_count') + 1
    song.save(update_fields=['play_count'])

    return Response({'status': 'recorded'}, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_like(request, song_id):
    """Toggle like status for a song."""
    try:
        song = Song.objects.get(id=song_id)
    except Song.DoesNotExist:
        return Response({'error': 'Song not found.'}, status=status.HTTP_404_NOT_FOUND)

    like, created = SongLike.objects.get_or_create(song=song, user=request.user)

    if created:
        song.like_count = F('like_count') + 1
        song.save(update_fields=['like_count'])
        song.refresh_from_db(fields=['like_count'])
        return Response({'status': 'liked', 'like_count': song.like_count}, status=status.HTTP_201_CREATED)
    else:
        like.delete()
        song.like_count = F('like_count') - 1
        song.save(update_fields=['like_count'])
        song.refresh_from_db(fields=['like_count'])
        return Response({'status': 'unliked', 'like_count': song.like_count}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def artist_analytics(request):
    """
    Comprehensive analytics for the logged-in artist.
    Returns: overview stats, top songs, daily plays (30d), genre breakdown.
    """
    if request.user.role != 'artist':
        return Response({'error': 'Only artists can access analytics.'}, status=status.HTTP_403_FORBIDDEN)

    songs = Song.objects.filter(uploaded_by=request.user)
    song_ids = songs.values_list('id', flat=True)

    # Overview stats
    total_songs = songs.count()
    total_plays = songs.aggregate(total=Sum('play_count'))['total'] or 0
    total_likes = songs.aggregate(total=Sum('like_count'))['total'] or 0

    # Total watch hours from SongPlay records
    total_seconds = SongPlay.objects.filter(song_id__in=song_ids).aggregate(
        total=Sum('duration_listened')
    )['total'] or 0
    watch_hours = round(total_seconds / 3600, 1)

    # Top songs by play count
    top_songs = songs.order_by('-play_count')[:10]
    user_liked_song_ids = set()
    if request.user.is_authenticated:
        user_liked_song_ids = set(SongLike.objects.filter(user=request.user, song__in=top_songs).values_list('song_id', flat=True))

    top_songs_data = [
        {
            'id': str(s.id),
            'title': s.title,
            'artist': s.artist,
            'cover_url': s.cover_url,
            'play_count': s.play_count,
            'like_count': s.like_count,
            'is_liked': s.id in user_liked_song_ids,
            'genre': s.genre,
        }
        for s in top_songs
    ]

    # Daily plays over last X days
    try:
        days = int(request.query_params.get('days', 30))
    except ValueError:
        days = 30
        
    time_ago = timezone.now() - timedelta(days=days)
    daily_plays = (
        SongPlay.objects
        .filter(song_id__in=song_ids, played_at__gte=time_ago)
        .annotate(date=TruncDate('played_at'))
        .values('date')
        .annotate(plays=Count('id'))
        .order_by('date')
    )

    # Fill in missing days with 0
    daily_plays_dict = {str(dp['date']): dp['plays'] for dp in daily_plays}
    daily_data = []
    for i in range(days):
        date = (timezone.now() - timedelta(days=(days - 1) - i)).date()
        daily_data.append({
            'date': str(date),
            'plays': daily_plays_dict.get(str(date), 0),
        })

    # Genre breakdown
    genre_counts = {}
    for song in songs:
        if song.genre:
            for g in song.genre.split(','):
                g = g.strip()
                if g:
                    genre_counts[g] = genre_counts.get(g, 0) + song.play_count

    genre_data = [{'genre': k, 'plays': v} for k, v in sorted(genre_counts.items(), key=lambda x: -x[1])]

    # Recent plays (last 10)
    recent_plays = SongPlay.objects.filter(song_id__in=song_ids).select_related('song', 'user').order_by('-played_at')[:10]
    recent_data = [
        {
            'song_title': rp.song.title,
            'song_cover': rp.song.cover_url,
            'listener': rp.user.username if rp.user else 'Anonymous',
            'played_at': rp.played_at.isoformat(),
            'duration_listened': rp.duration_listened,
        }
        for rp in recent_plays
    ]

    return Response({
        'overview': {
            'total_songs': total_songs,
            'total_plays': total_plays,
            'total_likes': total_likes,
            'watch_hours': watch_hours,
        },
        'top_songs': top_songs_data,
        'daily_plays': daily_data,
        'genre_breakdown': genre_data,
        'recent_plays': recent_data,
    })

