from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import requests
import base64
import os
from django.conf import settings

def api_overview(request):
    """
    API overview endpoint
    GET /api/
    """
    endpoints = {
        'albums': {
            'list': '/albums/',
            'detail': '/albums/<album_id>/',
        },
        'artists': {
            'list': '/artists/',
            'detail': '/artists/<artist_id>/',
        },
        'songs': {
            'list': '/songs/',
            'detail': '/songs/<song_id>/',
            'lyrics': '/songs/<song_id>/lyrics/',
            'analytics': '/songs/analytics/',
            'top_songs': '/songs/top-songs/',
        },
        'playlists': {
            'list': '/playlists/',
            'detail': '/playlists/<playlist_id>/',
        },
        'api': {
            'overview': '/api/',
            'spotify_test': '/api/spotify-test/',
        },
    }

    return JsonResponse({
        'api_version': '1.0',
        'endpoints': endpoints,
        'message': 'Welcome to Spotify Clone API'
    })

@require_http_methods(["GET"])
def test_spotify_connection(request):
    """
    Test Spotify API connection
    GET /api/spotify-test/
    """
    try:
        # Load Spotify credentials
        base_dir = settings.BASE_DIR
        spotify_file_path = os.path.join(base_dir, 'apis', 'spotify.txt')

        if not os.path.exists(spotify_file_path):
            return JsonResponse({
                'success': False,
                'error': 'Spotify credentials file not found',
                'message': 'Please create apis/spotify.txt with your Spotify client_id and client_secret'
            }, status=404)

        # Read credentials
        with open(spotify_file_path, 'r', encoding='utf-8') as file:
            lines = file.read().strip().split('\n')

        credentials = {}
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                credentials[key.strip().lower()] = value.strip()

        # Check if we have required credentials
        if 'client_id' not in credentials or 'client_secret' not in credentials:
            return JsonResponse({
                'success': False,
                'error': 'Missing Spotify credentials',
                'message': 'Please ensure apis/spotify.txt contains both client_id and client_secret'
            }, status=400)

        client_id = credentials['client_id']
        client_secret = credentials['client_secret']

        # Test 1: Get access token
        auth_string = f"{client_id}:{client_secret}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')

        token_url = "https://accounts.spotify.com/api/token"
        headers = {
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {"grant_type": "client_credentials"}

        token_response = requests.post(token_url, headers=headers, data=data, timeout=10)

        if token_response.status_code != 200:
            return JsonResponse({
                'success': False,
                'error': 'Failed to get access token',
                'status_code': token_response.status_code,
                'response': token_response.text
            }, status=400)

        token_data = token_response.json()
        access_token = token_data.get('access_token')

        if not access_token:
            return JsonResponse({
                'success': False,
                'error': 'No access token in response',
                'response': token_data
            }, status=400)

        # Test 2: Search for a test track
        search_url = "https://api.spotify.com/v1/search"
        search_headers = {"Authorization": f"Bearer {access_token}"}
        search_params = {
            "q": "track:blinding lights artist:the weeknd",
            "type": "track",
            "limit": 1
        }

        search_response = requests.get(search_url, headers=search_headers, params=search_params, timeout=10)

        if search_response.status_code != 200:
            return JsonResponse({
                'success': False,
                'error': 'Search request failed',
                'status_code': search_response.status_code,
                'response': search_response.text
            }, status=400)

        search_data = search_response.json()
        tracks = search_data.get('tracks', {}).get('items', [])

        if not tracks:
            return JsonResponse({
                'success': False,
                'error': 'No tracks found in search',
                'response': search_data
            }, status=400)

        track = tracks[0]

        return JsonResponse({
            'success': True,
            'message': 'Spotify API connection successful!',
            'credentials_loaded': True,
            'access_token_obtained': True,
            'search_successful': True,
            'test_track': {
                'name': track.get('name'),
                'artists': [artist['name'] for artist in track.get('artists', [])],
                'album': track.get('album', {}).get('name'),
                'spotify_id': track.get('id'),
                'popularity': track.get('popularity'),
                'preview_url': track.get('preview_url'),
                'external_url': track.get('external_urls', {}).get('spotify')
            }
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': 'Unexpected error occurred'
        }, status=500)
