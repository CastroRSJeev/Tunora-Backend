import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tunora.settings')
django.setup()

from songs.models import Playlist
from songs.serializers import PlaylistSerializer
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.first()

class MockRequest:
    def __init__(self, user):
        self.user = user

try:
    p = Playlist.objects.first()
    if not p:
        print("No playlists found")
        sys.exit()
    print('serializing with request...')
    request = MockRequest(user)
    data = PlaylistSerializer(p, context={'request': request}).data
    print("Serialized Keys:", data.keys())
    print("Serialization Successful!")
except Exception as e:
    import traceback
    traceback.print_exc()
