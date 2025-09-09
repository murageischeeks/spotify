#!/usr/bin/env python
"""
Script to populate the database with sample data for testing
"""
import os
import sys
import django
from datetime import datetime, timedelta
from django.utils import timezone

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'spotifybackend.settings')
django.setup()

from artists.models import Artist, CustomUser
from albums.models import Album
from songs.models import Song, Stream
from django.contrib.auth import get_user_model

User = get_user_model()

def create_sample_data():
    print("Creating sample data...")

    # Create a test user
    user, created = CustomUser.objects.get_or_create(
        email='test@example.com',
        defaults={
            'username': 'testuser',
            'role': 'user'
        }
    )
    if created:
        user.set_password('password123')
        user.save()
        print("[OK] Created test user")

    # Create separate users for each artist
    users_data = [
        {'email': 'weeknd@example.com', 'username': 'theweeknd'},
        {'email': 'dualipa@example.com', 'username': 'dualipa'},
        {'email': 'billieeilish@example.com', 'username': 'billieeilish'}
    ]

    users = [user]  # Start with the existing user
    for user_data in users_data:
        new_user, created = CustomUser.objects.get_or_create(
            email=user_data['email'],
            defaults={
                'username': user_data['username'],
                'role': 'artist'
            }
        )
        if created:
            new_user.set_password('password123')
            new_user.save()
            print(f"[OK] Created user: {new_user.username}")
        users.append(new_user)

    # Create artists
    artists_data = [
        {
            'user': users[1],  # The Weeknd
            'artist_name': 'The Weeknd',
            'bio': 'Canadian singer, songwriter, and record producer',
            'monthly_listeners': 85000000,
            'total_streams': 150000000,
            'is_verified': True
        },
        {
            'user': users[2],  # Dua Lipa
            'artist_name': 'Dua Lipa',
            'bio': 'English singer and songwriter',
            'monthly_listeners': 65000000,
            'total_streams': 120000000,
            'is_verified': True
        },
        {
            'user': users[3],  # Billie Eilish
            'artist_name': 'Billie Eilish',
            'bio': 'American singer and songwriter',
            'monthly_listeners': 70000000,
            'total_streams': 110000000,
            'is_verified': True
        }
    ]

    artists = []
    for artist_data in artists_data:
        artist, created = Artist.objects.get_or_create(
            artist_name=artist_data['artist_name'],
            defaults=artist_data
        )
        artists.append(artist)
        if created:
            print(f"[OK] Created artist: {artist.artist_name}")

    # Create albums
    albums_data = [
        {
            'title': 'After Hours',
            'artist': artists[0],  # The Weeknd
            'release_date': datetime(2020, 3, 20).date(),
            'genre': 'R&B',
            'cover_image': None
        },
        {
            'title': 'Future Nostalgia',
            'artist': artists[1],  # Dua Lipa
            'release_date': datetime(2020, 3, 27).date(),
            'genre': 'Pop',
            'cover_image': None
        },
        {
            'title': 'Happier Than Ever',
            'artist': artists[2],  # Billie Eilish
            'release_date': datetime(2021, 7, 30).date(),
            'genre': 'Alternative',
            'cover_image': None
        }
    ]

    albums = []
    for album_data in albums_data:
        album, created = Album.objects.get_or_create(
            title=album_data['title'],
            artist=album_data['artist'],
            defaults=album_data
        )
        albums.append(album)
        if created:
            print(f"[OK] Created album: {album.title}")

    # Create songs
    songs_data = [
        {
            'title': 'Blinding Lights',
            'artist': artists[0],
            'album': albums[0],
            'duration': 200,  # 3:20
            'total_streams': 1500000000,  # Reduced to fit PostgreSQL integer limit
            'audio_file': 'songs/blinding_lights.mp3'
        },
        {
            'title': 'Heartless',
            'artist': artists[0],
            'album': albums[0],
            'duration': 198,  # 3:18
            'total_streams': 800000000,
            'audio_file': 'songs/heartless.mp3'
        },
        {
            'title': 'Levitating',
            'artist': artists[1],
            'album': albums[1],
            'duration': 203,  # 3:23
            'total_streams': 1200000000,
            'audio_file': 'songs/levitating.mp3'
        },
        {
            'title': "Don't Start Now",
            'artist': artists[1],
            'album': albums[1],
            'duration': 183,  # 3:03
            'total_streams': 1000000000,
            'audio_file': 'songs/dont_start_now.mp3'
        },
        {
            'title': 'Happier Than Ever',
            'artist': artists[2],
            'album': albums[2],
            'duration': 298,  # 4:58
            'total_streams': 600000000,
            'audio_file': 'songs/happier_than_ever.mp3'
        },
        {
            'title': 'Bad Guy',
            'artist': artists[2],
            'album': None,  # Single
            'duration': 194,  # 3:14
            'total_streams': 1300000000,
            'audio_file': 'songs/bad_guy.mp3'
        }
    ]

    songs = []
    for song_data in songs_data:
        song, created = Song.objects.get_or_create(
            title=song_data['title'],
            artist=song_data['artist'],
            defaults=song_data
        )
        songs.append(song)
        if created:
            print(f"[OK] Created song: {song.title}")

    # Create some stream events for analytics
    print("Creating stream events...")
    stream_count = 0
    for song in songs:
        # Create multiple stream events for each song
        for i in range(3):  # 3 streams per song to keep it manageable
            try:
                # Use different timestamps to avoid unique constraint violations
                timestamp = timezone.now() - timedelta(days=i, hours=i, minutes=stream_count)
                Stream.objects.create(
                    song=song,
                    user=user,  # Use the user object, not email
                    timestamp=timestamp,
                    duration_listened=song.duration // 2  # Half the song
                )
                stream_count += 1
            except Exception as e:
                # Skip if there's a duplicate or other error
                print(f"Skipping stream creation for {song.title}: {e}")
                continue

    print("[OK] Created stream events")

    print("\nSUCCESS: Sample data created successfully!")
    print(f"   - {len(artists)} artists")
    print(f"   - {len(albums)} albums")
    print(f"   - {len(songs)} songs")
    print(f"   - {len(songs) * 10} stream events")

if __name__ == '__main__':
    create_sample_data()