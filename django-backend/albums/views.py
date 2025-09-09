from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Album
from songs.models import Song
from django.db.models import Sum
import requests
from songs.lyrics import LyricsService

def _get_spotify_album_data(album_title: str, artist_name: str):
    """Get Spotify data for an album"""
    service = LyricsService()
    access_token = service._get_spotify_access_token()

    if not access_token:
        return None

    try:
        search_url = "https://api.spotify.com/v1/search"
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {
            "q": f"album:{album_title} artist:{artist_name}",
            "type": "album",
            "limit": 1
        }

        response = requests.get(search_url, headers=headers, params=params, timeout=15)

        if response.status_code == 200:
            try:
                data = response.json()
            except ValueError as e:
                print(f"Failed to parse album JSON response: {e}")
                return None

            albums = data.get('albums', {}).get('items', [])

            if albums and len(albums) > 0:
                album = albums[0]

                # Validate that album is a dictionary
                if not isinstance(album, dict):
                    print(f"Album data is not a dictionary: {type(album)}")
                    return None

                # Safely extract album information
                try:
                    return {
                        'spotify_id': album.get('id', ''),
                        'name': album.get('name', ''),
                        'artists': [artist.get('name', '') for artist in album.get('artists', []) if isinstance(artist, dict)],
                        'release_date': album.get('release_date'),
                        'total_tracks': album.get('total_tracks'),
                        'external_url': album.get('external_urls', {}).get('spotify') if isinstance(album.get('external_urls'), dict) else None,
                        'images': album.get('images', []),
                        'album_type': album.get('album_type')
                    }
                except Exception as e:
                    print(f"Error extracting album information: {e}")
                    return None

        return None

    except requests.exceptions.Timeout as e:
        print(f"Spotify album API timeout: {e}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Spotify album API request error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error fetching Spotify album data: {e}")
        return None

def album_list(request):
    """
    API endpoint to get all albums
    GET /albums/albums/
    """
    albums = Album.objects.select_related('artist').prefetch_related('songs').all()
    album_data = []

    for album in albums:
        songs = album.songs.all()
        total_streams = songs.aggregate(total=Sum('streams'))['total'] or 0
        unique_artists = set(song.artist.artist_name for song in songs)
        unique_artists.add(album.artist.artist_name)  # Include album artist

        # Get Spotify data for the album
        spotify_album_data = _get_spotify_album_data(album.title, album.artist.artist_name)

        album_data.append({
            'id': album.id,
            'title': album.title,
            'artist': {
                'id': album.artist.id,
                'name': album.artist.artist_name,
            },
            'cover_image': album.cover_image.url if album.cover_image else None,
            'release_date': album.release_date.isoformat() if album.release_date else None,
            'genre': album.genre,
            'total_songs': songs.count(),
            'total_streams': total_streams,
            'unique_artists': list(unique_artists),
            'created_at': album.created_at.isoformat(),
            'spotify_data': spotify_album_data
        })

    return JsonResponse({'albums': album_data}, safe=False)

def album_detail(request, album_id):
    """
    API endpoint to get detailed album info with all songs
    GET /albums/albums/<album_id>/
    """
    album = get_object_or_404(Album.objects.select_related('artist').prefetch_related('songs__artist'), id=album_id)

    songs_data = []
    total_streams = 0
    unique_artists = set()

    for song in album.songs.all():
        song_streams = song.total_streams
        total_streams += song_streams
        unique_artists.add(song.artist.artist_name)

        songs_data.append({
            'id': song.id,
            'title': song.title,
            'artist': {
                'id': song.artist.id,
                'name': song.artist.artist_name,
            },
            'duration': song.duration,
            'duration_formatted': song.duration_formatted,
            'streams': song_streams,
            'audio_file': song.audio_file.url if song.audio_file else None,
            'created_at': song.created_at.isoformat(),
        })

    unique_artists.add(album.artist.artist_name)  # Include album artist

    album_data = {
        'id': album.id,
        'title': album.title,
        'artist': {
            'id': album.artist.id,
            'name': album.artist.artist_name,
        },
        'cover_image': album.cover_image.url if album.cover_image else None,
        'release_date': album.release_date.isoformat() if album.release_date else None,
        'genre': album.genre,
        'total_songs': len(songs_data),
        'total_streams': total_streams,
        'unique_artists': list(unique_artists),
        'songs': songs_data,
        'created_at': album.created_at.isoformat(),
    }

    return JsonResponse(album_data)
