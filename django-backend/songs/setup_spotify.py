# songs/management/commands/setup_spotify.py
# Run this command: python manage.py setup_spotify

import os
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Setup Spotify API credentials'

    def add_arguments(self, parser):
        parser.add_argument('--client-id', type=str, help='Spotify Client ID')
        parser.add_argument('--client-secret', type=str, help='Spotify Client Secret')

    def handle(self, *args, **options):
        # Create api directory if it doesn't exist
        api_dir = os.path.join(settings.BASE_DIR, 'api')
        os.makedirs(api_dir, exist_ok=True)
        
        spotify_file = os.path.join(api_dir, 'spotify.txt')
        
        # Check if file exists
        if os.path.exists(spotify_file):
            self.stdout.write(
                self.style.WARNING('spotify.txt already exists. Contents:')
            )
            with open(spotify_file, 'r') as f:
                self.stdout.write(f.read())
            
            overwrite = input('\nOverwrite existing file? (y/N): ')
            if overwrite.lower() != 'y':
                self.stdout.write('Aborted.')
                return
        
        # Get credentials
        client_id = options.get('client_id')
        client_secret = options.get('client_secret')
        
        if not client_id:
            client_id = input('Enter your Spotify Client ID: ')
        
        if not client_secret:
            client_secret = input('Enter your Spotify Client Secret: ')
        
        if not client_id or not client_secret:
            self.stdout.write(
                self.style.ERROR('Both Client ID and Client Secret are required')
            )
            return
        
        # Write to file
        with open(spotify_file, 'w') as f:
            f.write(f'client_id: {client_id}\n')
            f.write(f'client_secret: {client_secret}\n')
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {spotify_file}')
        )
        
        # Test the credentials
        self.stdout.write('Testing credentials...')
        
        try:
            from songs.lyrics import LyricsService
            service = LyricsService()
            token = service._get_spotify_access_token()
            
            if token:
                self.stdout.write(
                    self.style.SUCCESS('✓ Spotify API credentials are working!')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('✗ Failed to get access token. Check your credentials.')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Error testing credentials: {e}')
            )