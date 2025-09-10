from django.core.management.base import BaseCommand
from songs.lyrics import batch_update_lyrics
from songs.models import Song

class Command(BaseCommand):
    help = 'Update lyrics for songs that don\'t have them'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='Number of songs to process'
        )

    def handle(self, *args, **options):
        # Get songs without lyrics
        songs_without_lyrics = Song.objects.filter(
            lyrics__isnull=True
        ).values_list('id', flat=True)[:options['limit']]
        
        if not songs_without_lyrics:
            self.stdout.write(
                self.style.SUCCESS('No songs without lyrics found')
            )
            return
        
        self.stdout.write(f'Updating lyrics for {len(songs_without_lyrics)} songs...')
        
        results = batch_update_lyrics(list(songs_without_lyrics))
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Updated: {results["updated"]}, '
                f'Failed: {results["failed"]}, '
                f'Already had lyrics: {results["already_had_lyrics"]}'
            )
        )