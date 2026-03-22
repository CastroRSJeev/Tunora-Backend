import csv
import os
from django.core.management.base import BaseCommand
from songs.models import Song
from django.conf import settings

class Command(BaseCommand):
    help = 'Import songs from song_list.csv'

    def handle(self, *args, **options):
        csv_file_path = os.path.join(settings.BASE_DIR, 'song_list.csv')
        
        if not os.path.exists(csv_file_path):
            self.stdout.write(self.style.ERROR(f'File not found: {csv_file_path}'))
            return

        # Try different encodings to handle common CSV formats
        encodings = ['utf-8', 'utf-8-sig', 'cp1252', 'latin-1']
        data = None
        
        for encoding in encodings:
            try:
                with open(csv_file_path, mode='r', encoding=encoding) as file:
                    # Read into memory to verify encoding works for the whole file
                    content = file.read()
                    data = content.splitlines()
                self.stdout.write(self.style.SUCCESS(f"Successfully read file with {encoding} encoding."))
                break
            except UnicodeDecodeError:
                continue

        if data is None:
            self.stdout.write(self.style.ERROR(f'Could not decode file with any of these encodings: {encodings}'))
            return

        reader = csv.DictReader(data)
        
        count = 0
        for row in reader:
            # Normalize headers
            normalized_row = {k.lower().strip(): v for k, v in row.items()}
            
            title = normalized_row.get('title') or normalized_row.get('song title') or normalized_row.get('name')
            artist = normalized_row.get('artist') or normalized_row.get('performer') or normalized_row.get('author')
            genre = normalized_row.get('genre') or normalized_row.get('style') or 'Unknown'
            cover_url = normalized_row.get('cover_url') or normalized_row.get('cover') or normalized_row.get('thumbnail') or normalized_row.get('image') or normalized_row.get('image_url')
            audio_url = normalized_row.get('path') or normalized_row.get('audio') or normalized_row.get('url')
            duration = normalized_row.get('duration') or normalized_row.get('length') or '3:00'
            mood = normalized_row.get('mood') or ''
            
            if not title or not artist:
                self.stdout.write(self.style.WARNING(f'Skipping row {row} due to missing title or artist'))
                continue
            
            song, created = Song.objects.get_or_create(
                title=title,
                artist=artist,
                defaults={
                    'genre': genre,
                    'cover_url': cover_url or 'https://via.placeholder.com/300',
                    'audio_url': audio_url,
                    'duration': duration,
                    'mood': mood,
                }
            )
            
            if created:
                count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Successfully imported {count} new songs.'))
