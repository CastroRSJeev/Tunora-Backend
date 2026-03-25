import urllib.request
import urllib.error

url = 'http://localhost:8000/api/songs/playlists/mine/'
try:
    req = urllib.request.Request(url, headers={'Authorization': 'Bearer test'})
    resp = urllib.request.urlopen(req)
    print(resp.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print(f"Error {e.code}:")
    print(e.read().decode('utf-8')[:2000])
except Exception as e:
    print("Other error:", e)
