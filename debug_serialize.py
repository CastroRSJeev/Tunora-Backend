import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tunora.settings')
django.setup()

from songs.models import Playlist
from songs.serializers import PlaylistSerializer

try:
    p = Playlist.objects.first()
    if not p:
        print("No playlists found")
        sys.exit()
    print('serializing...')
    data = PlaylistSerializer(p).data
    print("Serialized Keys:", data.keys())
    print("Serialization Successful!")
except Exception as e:
    import traceback
    traceback.print_exc()
