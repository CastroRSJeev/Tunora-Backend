import csv
import os
from django.core.management.base import BaseCommand
from songs.models import Song
from django.conf import settings

class Command(BaseCommand):
    help = 'Populate empty description fields from song_list.csv'

    def handle(self, *args, **options):
        log_file = os.path.join(settings.BASE_DIR, 'description_update_report.txt')
        with open(log_file, 'w', encoding='utf-8') as report:
            csv_file_path = os.path.join(settings.BASE_DIR, 'song_list.csv')
            
            if not os.path.exists(csv_file_path):
                msg = f'File not found: {csv_file_path}\n'
                self.stdout.write(self.style.ERROR(msg))
                report.write(msg)
                return

            # Try different encodings to handle common CSV formats
            encodings = ['utf-8', 'utf-8-sig', 'cp1252', 'latin-1']
            data = None
            
            for encoding in encodings:
                try:
                    with open(csv_file_path, mode='r', encoding=encoding) as file:
                        content = file.read()
                        data = content.splitlines()
                    self.stdout.write(self.style.SUCCESS(f"Successfully read file with {encoding} encoding."))
                    report.write(f"Successfully read file with {encoding} encoding.\n")
                    break
                except UnicodeDecodeError:
                    continue

            if data is None:
                msg = f'Could not decode file with any of these encodings: {encodings}\n'
                self.stdout.write(self.style.ERROR(msg))
                report.write(msg)
                return

            reader = csv.DictReader(data)
            
            # Check first row to see column names
            headers = [h.lower().strip() for h in reader.fieldnames] if reader.fieldnames else []
            self.stdout.write(self.style.NOTICE(f"Detected headers: {headers}"))
            report.write(f"Detected headers: {headers}\n")

            count = 0
            skipped = 0
            already_filled = 0
            not_found = 0

            for row in reader:
                normalized_row = {k.lower().strip(): v for k, v in row.items()}
                
                title = normalized_row.get('title') or normalized_row.get('song title') or normalized_row.get('name')
                artist = normalized_row.get('artist') or normalized_row.get('performer') or normalized_row.get('author')
                
                # The user wants to populate description. Let's look for 'description' or 'mood' or 'desc'
                description = normalized_row.get('description') or normalized_row.get('mood') or normalized_row.get('desc') or normalized_row.get('about')
                
                if not title or not artist:
                    skipped += 1
                    continue
                
                # Find the song in database
                try:
                    song = Song.objects.filter(title__iexact=title.strip(), artist__iexact=artist.strip()).first()
                    if song:
                        if not song.description or song.description.strip() == '':
                            if description:
                                song.description = description
                                song.save()
                                count += 1
                        else:
                            already_filled += 1
                    else:
                        not_found += 1
                except Exception as e:
                    report.write(f"Error updating song {title}: {str(e)}\n")

            report.write(f'Updated {count} descriptions.\n')
            report.write(f'Already filled: {already_filled}\n')
            report.write(f'Songs not found in DB: {not_found}\n')
            report.write(f'Skipped CSV rows (invalid): {skipped}\n')
            self.stdout.write(self.style.SUCCESS(f'Updated {count} descriptions.'))
        self.stdout.write(self.style.NOTICE(f'Already filled: {already_filled}'))
        self.stdout.write(self.style.NOTICE(f'Songs not found in DB: {not_found}'))
        self.stdout.write(self.style.NOTICE(f'Skipped CSV rows (invalid): {skipped}'))
