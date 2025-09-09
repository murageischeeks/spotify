from django.core.management.base import BaseCommand
from songs.models import Song
from songs.lyrics import LyricsService

class Command(BaseCommand):
    help = 'Sync Spotify data for existing songs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='Number of songs to process'
        )
        parser.add_argument(
            '--update-existing',
            action='store_true',
            help='Update songs that already have Spotify data'
        )

    def handle(self, *args, **options):
        service = LyricsService()
        
        # Get songs to process
        if options['update_existing']:
            songs = Song.objects.all()[:options['limit']]
        else:
            songs = Song.objects.filter(
                spotify_track_id__isnull=True
            )[:options['limit']]
        
        if not songs:
            self.stdout.write(
                self.style.SUCCESS('No songs to process')
            )
            return
        
        self.stdout.write(f'Processing {len(songs)} songs...')
        
        updated_count = 0
        failed_count = 0
        
        for song in songs:
            try:
                spotify_info = service._get_spotify_track_info(song)
                
                if spotify_info:
                    # Update song with Spotify data
                    song.spotify_track_id = spotify_info['spotify_id']
                    song.spotify_preview_url = spotify_info.get('preview_url')
                    song.spotify_popularity = spotify_info.get('popularity')
                    song.spotify_external_url = spotify_info.get('external_urls', {}).get('spotify')
                    song.save()
                    
                    updated_count += 1
                    self.stdout.write(f'✓ Updated: {song.title} - {song.artist.name}')
                else:
                    failed_count += 1
                    self.stdout.write(f'✗ Not found: {song.title} - {song.artist.name}')
                    
            except Exception as e:
                failed_count += 1
                self.stdout.write(f'✗ Error processing {song.title}: {e}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nProcessing complete:\n'
                f'Updated: {updated_count}\n'
                f'Failed: {failed_count}'
            )
        )

