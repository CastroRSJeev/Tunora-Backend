import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tunora.settings')
django.setup()
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
import urllib.request
import urllib.error
import bs4

User = get_user_model()
user = User.objects.first()
refresh = RefreshToken.for_user(user)

url = 'http://localhost:8000/api/songs/playlists/mine/'
try:
    req = urllib.request.Request(url, headers={'Authorization': f'Bearer {refresh.access_token}'})
    urllib.request.urlopen(req)
except urllib.error.HTTPError as e:
    html = e.read().decode('utf-8')
    soup = bs4.BeautifulSoup(html, 'html.parser')
    print("DJANGO EXCEPTION:")
    print(soup.select_one('title').text if soup.select_one('title') else "No title")
    frames = soup.select('.frame')
    if frames:
        for f in frames[-3:]:
            print(f.text.replace('\\n', ' '))
    ul = soup.select_one('.traceback')
    if ul:
        print(ul.text[:1000])
