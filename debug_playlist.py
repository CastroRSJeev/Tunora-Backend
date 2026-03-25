import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tunora.settings')
django.setup()

from django.contrib.auth import get_user_model
from songs.models import Playlist

User = get_user_model()
user = User.objects.first()

if not user:
    print("No user found")
    sys.exit()

try:
    p = Playlist.objects.create(name="Test", owner=user, is_public=False)
    print("Created playlist ID:", p.id)
    print("Playlists for user:", Playlist.objects.filter(owner=user).count())
except Exception as e:
    import traceback
    traceback.print_exc()
