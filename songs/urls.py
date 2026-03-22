from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SongViewSet, upload_song, my_songs, edit_song, delete_song

router = DefaultRouter()
router.register(r'', SongViewSet, basename='song')

urlpatterns = [
    path('upload/', upload_song, name='song-upload'),
    path('my/', my_songs, name='song-my'),
    path('<str:song_id>/edit/', edit_song, name='song-edit'),
    path('<str:song_id>/delete/', delete_song, name='song-delete'),
    path('', include(router.urls)),
]
