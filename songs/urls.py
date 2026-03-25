from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SongViewSet, upload_song, my_songs, edit_song, delete_song, record_play, artist_analytics, toggle_like
from .playlist_views import (
    create_playlist, my_playlists, public_playlists,
    playlist_detail, playlist_add_song, playlist_remove_song,
)

router = DefaultRouter()
router.register(r'', SongViewSet, basename='song')

urlpatterns = [
    path('upload/', upload_song, name='song-upload'),
    path('my/', my_songs, name='song-my'),
    path('analytics/', artist_analytics, name='artist-analytics'),
    path('<str:song_id>/edit/', edit_song, name='song-edit'),
    path('<str:song_id>/delete/', delete_song, name='song-delete'),
    path('<str:song_id>/play/', record_play, name='song-play'),
    path('<str:song_id>/like/', toggle_like, name='song-like'),

    # Playlist endpoints
    path('playlists/create/', create_playlist, name='playlist-create'),
    path('playlists/mine/', my_playlists, name='playlist-mine'),
    path('playlists/public/', public_playlists, name='playlist-public'),
    path('playlists/<str:playlist_id>/', playlist_detail, name='playlist-detail'),
    path('playlists/<str:playlist_id>/add/', playlist_add_song, name='playlist-add-song'),
    path('playlists/<str:playlist_id>/remove/<str:song_id>/', playlist_remove_song, name='playlist-remove-song'),

    path('', include(router.urls)),
]
