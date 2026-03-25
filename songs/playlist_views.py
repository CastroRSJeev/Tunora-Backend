from django.db.models import Q, Prefetch
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from rest_framework import permissions, status

from .models import Song, Playlist, PlaylistSong
from .serializers import PlaylistSerializer
from recommendations.ml import embed


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_playlist(request):
    """Create a new playlist for the authenticated user."""
    name = request.data.get('name', '').strip()
    description = request.data.get('description', '').strip()
    is_public = request.data.get('is_public', False)

    if not name:
        return Response({'error': 'Playlist name is required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        embedding = embed(f"{name} {description}")
    except Exception:
        embedding = None

    playlist = Playlist.objects.create(
        name=name,
        description=description,
        is_public=bool(is_public),
        owner=request.user,
        embedding=embedding,
    )
    return Response(PlaylistSerializer(playlist, context={'request': request}).data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_playlists(request):
    """List all playlists owned by the authenticated user."""
    playlists = Playlist.objects.filter(owner=request.user).prefetch_related(
        Prefetch('playlist_songs', queryset=PlaylistSong.objects.select_related('song'))
    )
    return Response(PlaylistSerializer(playlists, many=True, context={'request': request}).data)


@api_view(['GET'])
@permission_classes([AllowAny])
def public_playlists(request):
    """List/search public playlists."""
    query = request.query_params.get('q', '').strip()
    playlists = Playlist.objects.filter(is_public=True)
    if query:
        playlists = playlists.filter(
            Q(name__icontains=query) | Q(description__icontains=query) | Q(owner__username__icontains=query)
        )
    playlists = playlists.order_by('-updated_at')[:50].prefetch_related(
        Prefetch('playlist_songs', queryset=PlaylistSong.objects.select_related('song'))
    )
    return Response(PlaylistSerializer(playlists, many=True, context={'request': request}).data)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticatedOrReadOnly])
def playlist_detail(request, playlist_id):
    """Get, update, or delete a specific playlist."""
    try:
        playlist = Playlist.objects.get(id=playlist_id)
    except Playlist.DoesNotExist:
        return Response({'error': 'Playlist not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        if not playlist.is_public and playlist.owner != request.user:
            return Response({'error': 'This playlist is private.'}, status=status.HTTP_403_FORBIDDEN)
        return Response(PlaylistSerializer(playlist, context={'request': request}).data)

    if playlist.owner != request.user:
        return Response({'error': 'Not authorized.'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'PATCH':
        for field in ('name', 'description'):
            val = request.data.get(field)
            if val is not None:
                setattr(playlist, field, val.strip())
        if 'is_public' in request.data:
            playlist.is_public = bool(request.data['is_public'])
        try:
            playlist.embedding = embed(f"{playlist.name} {playlist.description}")
        except Exception:
            pass
        playlist.save()
        return Response(PlaylistSerializer(playlist, context={'request': request}).data)

    if request.method == 'DELETE':
        playlist.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def playlist_add_song(request, playlist_id):
    """Add a song to a playlist. Only owner can add."""
    try:
        playlist = Playlist.objects.get(id=playlist_id, owner=request.user)
    except Playlist.DoesNotExist:
        return Response({'error': 'Playlist not found or not yours.'}, status=status.HTTP_404_NOT_FOUND)

    song_id = str(request.data.get('song_id', '')).strip()
    if not song_id:
        return Response({'error': 'song_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        song = Song.objects.get(id=song_id)
    except (Song.DoesNotExist, ValueError):
        return Response({'error': 'Song not found.'}, status=status.HTTP_404_NOT_FOUND)

    if PlaylistSong.objects.filter(playlist=playlist, song=song).exists():
        return Response({'error': 'Song already in playlist.'}, status=status.HTTP_400_BAD_REQUEST)

    max_pos = playlist.playlist_songs.count()
    PlaylistSong.objects.create(playlist=playlist, song=song, position=max_pos)
    playlist.save()  # bumps updated_at

    return Response(PlaylistSerializer(playlist, context={'request': request}).data, status=status.HTTP_201_CREATED)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def playlist_remove_song(request, playlist_id, song_id):
    """Remove a song from a playlist. Only owner can remove."""
    try:
        playlist = Playlist.objects.get(id=playlist_id, owner=request.user)
    except Playlist.DoesNotExist:
        return Response({'error': 'Playlist not found or not yours.'}, status=status.HTTP_404_NOT_FOUND)

    deleted, _ = PlaylistSong.objects.filter(playlist=playlist, song_id=song_id).delete()
    if not deleted:
        return Response({'error': 'Song not in playlist.'}, status=status.HTTP_404_NOT_FOUND)

    playlist.save()  # bumps updated_at
    return Response(PlaylistSerializer(playlist, context={'request': request}).data)
