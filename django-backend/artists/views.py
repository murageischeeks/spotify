from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Artist
from songs.models import Song
from django.db.models import Sum
import requests
from songs.lyrics import LyricsService

def _get_spotify_artist_data(artist_name: str):
    """Get Spotify data for an artist"""
    service = LyricsService()
    access_token = service._get_spotify_access_token()

    if not access_token:
        return None

    try:
        search_url = "https://api.spotify.com/v1/search"
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {
            "q": f"artist:{artist_name}",
            "type": "artist",
            "limit": 1
        }

        response = requests.get(search_url, headers=headers, params=params, timeout=15)

        if response.status_code == 200:
            try:
                data = response.json()
            except ValueError as e:
                print(f"Failed to parse artist JSON response: {e}")
                return None

            artists = data.get('artists', {}).get('items', [])

            if artists and len(artists) > 0:
                artist = artists[0]

                # Validate that artist is a dictionary
                if not isinstance(artist, dict):
                    print(f"Artist data is not a dictionary: {type(artist)}")
                    return None

                # Safely extract artist information
                try:
                    return {
                        'spotify_id': artist.get('id', ''),
                        'name': artist.get('name', ''),
                        'genres': artist.get('genres', []),
                        'popularity': artist.get('popularity'),
                        'followers': artist.get('followers', {}).get('total') if isinstance(artist.get('followers'), dict) else None,
                        'external_url': artist.get('external_urls', {}).get('spotify') if isinstance(artist.get('external_urls'), dict) else None,
                        'images': artist.get('images', [])
                    }
                except Exception as e:
                    print(f"Error extracting artist information: {e}")
                    return None

        return None

    except requests.exceptions.Timeout as e:
        print(f"Spotify artist API timeout: {e}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Spotify artist API request error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error fetching Spotify artist data: {e}")
        return None

def artist_list(request):
    """
    API endpoint to get all artists
    GET /artists/artists/
    """
    artists = Artist.objects.all()
    artist_data = []

    for artist in artists:
        songs = artist.songs.all()
        total_streams = songs.aggregate(total=Sum('streams'))['total'] or 0

        # Get Spotify data for the artist
        spotify_artist_data = _get_spotify_artist_data(artist.artist_name)

        artist_data.append({
            'id': artist.id,
            'artist_name': artist.artist_name,
            'bio': artist.bio,
            'profile_image': artist.profile_image.url if artist.profile_image else None,
            'monthly_listeners': artist.monthly_listeners,
            'total_streams': total_streams,
            'is_verified': artist.is_verified,
            'total_songs': songs.count(),
            'created_at': artist.created_at.isoformat(),
            'spotify_data': spotify_artist_data
        })

    return JsonResponse({'artists': artist_data}, safe=False)

def artist_detail(request, artist_id):
    """
    API endpoint to get detailed artist info with all songs
    GET /artists/artists/<artist_id>/
    """
    artist = get_object_or_404(Artist, id=artist_id)

    songs_data = []
    total_streams = 0

    for song in artist.songs.all():
        song_streams = song.total_streams
        total_streams += song_streams

        songs_data.append({
            'id': song.id,
            'title': song.title,
            'album': {
                'id': song.album.id,
                'title': song.album.title,
            } if song.album else None,
            'duration': song.duration,
            'duration_formatted': song.duration_formatted,
            'streams': song_streams,
            'audio_file': song.audio_file.url if song.audio_file else None,
            'created_at': song.created_at.isoformat(),
        })

    artist_data = {
        'id': artist.id,
        'artist_name': artist.artist_name,
        'bio': artist.bio,
        'profile_image': artist.profile_image.url if artist.profile_image else None,
        'email': artist.email,
        'website': artist.website,
        'instagram': artist.instagram,
        'twitter': artist.twitter,
        'facebook': artist.facebook,
        'monthly_listeners': artist.monthly_listeners,
        'total_streams': total_streams,
        'is_verified': artist.is_verified,
        'verification_date': artist.verification_date.isoformat() if artist.verification_date else None,
        'total_songs': len(songs_data),
        'songs': songs_data,
        'created_at': artist.created_at.isoformat(),
        'updated_at': artist.updated_at.isoformat(),
    }

    return JsonResponse(artist_data)
