import requests
import os
from django.conf import settings
from django.http import JsonResponse
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .lyrics import get_song_lyrics, refresh_lyrics_cache
import json


# Use absolute imports instead of relative imports
from songs.models import Song  # Import from your songs app
from .streams import get_stream_analytics, get_top_songs


def get_song_details_with_spotify_data(request, song_id=None):
    """
    Function that gets song data from our database and enriches it with
    Spotify API data. Can work for a single song or all songs.
    """

    # 1. Get song(s) from our database
    if song_id:
        # Get single song
        try:
            songs = [Song.objects.select_related('artist', 'album').get(id=song_id)]
        except Song.DoesNotExist:
            return JsonResponse({'error': 'Song not found'}, status=404)
    else:
        # Get all songs
        songs = Song.objects.select_related('artist', 'album').all()

    # 2. Initialize Spotify service
    from .lyrics import LyricsService
    lyrics_service = LyricsService()

    # 3. Prepare the output data
    song_data = []

    for song in songs:
        # 4. Get basic song info from our database
        song_info = {
            'id': song.id,
            'title': song.title,
            'duration': song.duration,
            'duration_formatted': song.duration_formatted,
            'artist': {
                'id': song.artist.id,
                'name': song.artist.artist_name,
            },
            'streams': song.total_streams,
            'created_at': song.created_at.isoformat()
        }

        # 5. Add album info if available
        if song.album:
            song_info['album'] = {
                'id': song.album.id,
                'title': song.album.title,
                'release_date': song.album.release_date.isoformat() if song.album.release_date else None,
            }

        # 6. Get comprehensive data from Spotify API
        try:
            spotify_info = lyrics_service._get_comprehensive_spotify_data(song)
            if spotify_info and isinstance(spotify_info, dict):
                # Safely extract Spotify data with fallbacks
                spotify_data = {
                    'spotify_id': spotify_info.get('spotify_id', ''),
                    'preview_url': spotify_info.get('preview_url'),
                    'external_url': spotify_info.get('external_urls', {}).get('spotify') if isinstance(spotify_info.get('external_urls'), dict) else None,
                    'popularity': spotify_info.get('popularity'),
                    'album_image': None,
                    'duration_ms': spotify_info.get('duration_ms'),
                    'audio_features': spotify_info.get('audio_features', {})
                }

                # Safely extract album image
                album_data = spotify_info.get('album', {})
                if isinstance(album_data, dict):
                    images = album_data.get('images', [])
                    if images and len(images) > 0:
                        spotify_data['album_image'] = images[0].get('url')

                song_info['spotify_data'] = spotify_data
            else:
                song_info['spotify_data'] = None
        except Exception as e:
            # Log error but don't break the response
            print(f"Error fetching Spotify data for {song.title}: {e}")
            song_info['spotify_data'] = None

        song_data.append(song_info)

    # 7. Return JSON response
    return JsonResponse({'songs': song_data}, safe=False)


def get_spotify_api_key():
    """
    Helper function to read Spotify API key from external file
    """
    try:
        file_path = os.path.join(settings.BASE_DIR, 'apis', 'spotify.txt')
        with open(file_path, 'r') as file:
            return file.read().strip()
    except FileNotFoundError:
        print("Spotify API key file not found")
        return None


def get_spotify_song_data(song_title, artist_name, api_key):
    """
    Function to fetch additional data from Spotify API
    """
    if not api_key:
        return None
    
    try:
        # Spotify API search endpoint
        url = "https://api.spotify.com/v1/search"
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        params = {
            "q": f"track:{song_title} artist:{artist_name}",
            "type": "track",
            "limit": 1
        }
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract relevant data from Spotify response
        if data.get('tracks', {}).get('items'):
            track = data['tracks']['items'][0]
            return {
                'spotify_id': track['id'],
                'preview_url': track.get('preview_url'),
                'external_url': track['external_urls']['spotify'],
                'popularity': track['popularity'],
                'album_image': track['album']['images'][0]['url'] if track['album']['images'] else None
            }
    
    except requests.exceptions.RequestException as e:
        print(f"Spotify API error: {e}")
    
    return None

def song_stream_analytics(request, song_id=None):
    """
    API endpoint to get streaming analytics
    Usage:
    - /songs/analytics/ → all songs
    - /songs/analytics/1/ → specific song
    - /songs/analytics/?period=week → filter by time period
    """
    time_period = request.GET.get('period')  # today, week, month
    
    analytics = get_stream_analytics(song_id, time_period)
    
    if analytics is None:
        return JsonResponse({'error': 'Song not found'}, status=404)
    
    return JsonResponse({'analytics': analytics})


def top_songs(request):
    """
    API endpoint to get top songs by streams
    """
    limit = int(request.GET.get('limit', 10))
    time_period = request.GET.get('period')
    
    top_songs = get_top_songs(limit, time_period)
    
    return JsonResponse({'top_songs': top_songs})
    
@require_http_methods(["GET"])
def get_lyrics_view(request, song_id):
    """
    API endpoint to get lyrics for a song
    GET /songs/{song_id}/lyrics/
    """
    try:
        lyrics_data = get_song_lyrics(song_id)
        return JsonResponse(lyrics_data)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["POST"])
@login_required
@csrf_exempt
def refresh_lyrics_view(request, song_id):
    """
    API endpoint to force refresh lyrics
    POST /songs/{song_id}/lyrics/refresh/
    """
    try:
        lyrics_data = refresh_lyrics_cache(song_id)
        return JsonResponse(lyrics_data)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

