# Run once to backfill embeddings for all existing songs:
# cd D:/Study/PeopleLink/backend && python embed_songs.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tunora.settings')
django.setup()

from songs.models import Song
from recommendations.ml import get_model
import numpy as np

model = get_model()
songs = list(Song.objects.filter(embedding=None))
print(f"Embedding {len(songs)} songs...")

texts = [f"{s.genre} {s.description}" for s in songs]
embeddings = model.encode(texts, batch_size=32, show_progress_bar=True)

for song, emb in zip(songs, embeddings):
    song.embedding = emb.tolist()
    song.save(update_fields=['embedding'])

print("Done.")
