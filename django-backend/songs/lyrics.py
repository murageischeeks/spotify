import requests
import logging
from django.conf import settings
from django.core.cache import cache
from songs.models import Song
from typing import Optional, Dict, Any
import base64
import os

logger = logging.getLogger(__name__)

class LyricsService:
    """Service to handle lyrics retrieval from multiple sources"""
    
    def __init__(self):
        self.genius_api_key = getattr(settings, 'GENIUS_API_KEY', None)
        self.spotify_credentials = self._load_spotify_credentials()

    def _load_spotify_credentials(self) -> Optional[Dict[str, str]]:
        """
        Load Spotify credentials from apis/spotify.txt file
        """
        try:
            # Construct path to spotify.txt file
            base_dir = settings.BASE_DIR
            spotify_file_path = os.path.join(base_dir, 'apis', 'spotify.txt')

            if not os.path.exists(spotify_file_path):
                logger.warning(f"Spotify credentials file not found at {spotify_file_path}")
                return None

            with open(spotify_file_path, 'r', encoding='utf-8') as file:
                lines = file.read().strip().splitlines()

            credentials = {}
            for line in lines:
                if not line.strip() or line.strip().startswith("#"):
                    continue  # skip empty lines and comments
                if ':' in line:
                    key, value = line.split(':', 1)
                elif '=' in line:
                    key, value = line.split('=', 1)
                else:
                    continue
                credentials[key.strip().lower()] = value.strip()

            # Check required keys
            required_keys = ['client_id', 'client_secret']
            missing = [key for key in required_keys if key not in credentials]
            if missing:
                logger.error(
                    f"Missing required Spotify credentials: {missing}. "
                    f"Found: {list(credentials.keys())}"
                )
                return None

            logger.info("Spotify credentials loaded successfully")
            return credentials

        except Exception as e:
            logger.error(f"Error loading Spotify credentials: {e}", exc_info=True)
            return None

        
    def get_lyrics(self, song_id: int) -> Dict[str, Any]:
        """
        Get lyrics for a song, checking multiple sources
        Returns dict with lyrics data and metadata
        """
        try:
            song = Song.objects.get(id=song_id)
        except Song.DoesNotExist:
            return self._error_response("Song not found")
        
        # Create cache key
        cache_key = f"lyrics_{song_id}"
        
        # Check cache first
        cached_lyrics = cache.get(cache_key)
        if cached_lyrics:
            return cached_lyrics
        
        # Try to get lyrics from different sources
        lyrics_data = self._get_lyrics_from_sources(song)
        
        # Cache the result for 24 hours
        cache.set(cache_key, lyrics_data, 60 * 60 * 24)
        
        return lyrics_data
    
    def _get_lyrics_from_sources(self, song: Song) -> Dict[str, Any]:
        """Try multiple sources for lyrics"""
        
        # 1. Check if song already has lyrics in database
        if song.lyrics and song.lyrics.strip():
            return {
                'success': True,
                'lyrics': song.lyrics,
                'source': 'database',
                'song_title': song.title,
                'artist': song.artist.artist_name,
                'has_lyrics': True
            }
        
        # 2. Check if we have Spotify lyrics (if you have spotify integration)
        spotify_lyrics = self._get_spotify_lyrics(song)
        if spotify_lyrics:
            # Save to database for future use
            song.lyrics = spotify_lyrics
            song.save()
            return {
                'success': True,
                'lyrics': spotify_lyrics,
                'source': 'spotify',
                'song_title': song.title,
                'artist': song.artist.artist_name,
                'has_lyrics': True
            }
        
        # 3. Try external APIs
        external_lyrics = self._get_external_lyrics(song)
        if external_lyrics:
            # Save to database
            song.lyrics = external_lyrics
            song.save()
            return {
                'success': True,
                'lyrics': external_lyrics,
                'source': 'external_api',
                'song_title': song.title,
                'artist': song.artist.artist_name,
                'has_lyrics': True
            }
        
        # No lyrics found
        return {
            'success': True,
            'lyrics': None,
            'source': None,
            'song_title': song.title,
            'artist': song.artist.artist_name,
            'has_lyrics': False,
            'message': 'Lyrics not available for this song'
        }
    
    def _get_spotify_access_token(self) -> Optional[str]:
        """Get Spotify access token using client credentials flow"""
        if not self.spotify_credentials:
            return None
        
        # Check if we have a cached token
        cached_token = cache.get('spotify_access_token')
        if cached_token:
            return cached_token
        
        try:
            # Prepare credentials for basic auth
            client_id = self.spotify_credentials['client_id']
            client_secret = self.spotify_credentials['client_secret']
            
            # Create base64 encoded string
            auth_string = f"{client_id}:{client_secret}"
            auth_bytes = auth_string.encode('ascii')
            auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
            
            # Request access token
            token_url = "https://accounts.spotify.com/api/token"
            headers = {
                "Authorization": f"Basic {auth_b64}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            data = {"grant_type": "client_credentials"}
            
            response = requests.post(token_url, headers=headers, data=data, timeout=10)
            
            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data.get('access_token')
                expires_in = token_data.get('expires_in', 3600)
                
                # Cache token for slightly less time than it expires
                cache.set('spotify_access_token', access_token, expires_in - 60)
                
                return access_token
            else:
                logger.error(f"Failed to get Spotify access token: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting Spotify access token: {e}")
            return None

    def _get_spotify_track_info(self, song: Song) -> Optional[Dict[str, Any]]:
        """
        Search for track on Spotify and get track information
        Note: Spotify Web API doesn't provide lyrics, but we can get track details
        """
        access_token = self._get_spotify_access_token()
        if not access_token:
            logger.warning(f"No access token available for song {song.title}")
            return None

        try:
            # Search for the track
            search_url = "https://api.spotify.com/v1/search"
            headers = {"Authorization": f"Bearer {access_token}"}

            search_params = {
                "q": f"track:{song.title} artist:{song.artist.artist_name}",
                "type": "track",
                "limit": 1
            }

            logger.info(f"Searching Spotify for: {song.title} by {song.artist.artist_name}")
            response = requests.get(search_url, headers=headers, params=search_params, timeout=15)

            if response.status_code == 200:
                try:
                    data = response.json()
                except ValueError as e:
                    logger.error(f"Failed to parse JSON response: {e}")
                    logger.error(f"Response content: {response.text[:500]}")
                    return None

                tracks = data.get('tracks', {}).get('items', [])

                if tracks and len(tracks) > 0:
                    track = tracks[0]

                    # Validate that track is a dictionary
                    if not isinstance(track, dict):
                        logger.error(f"Track data is not a dictionary: {type(track)} - {track}")
                        return None

                    # Safely extract track information
                    try:
                        track_info = {
                            'spotify_id': track.get('id', ''),
                            'name': track.get('name', ''),
                            'artists': [artist.get('name', '') for artist in track.get('artists', []) if isinstance(artist, dict)],
                            'album': track.get('album', {}).get('name', '') if isinstance(track.get('album'), dict) else '',
                            'preview_url': track.get('preview_url'),
                            'external_urls': track.get('external_urls', {}),
                            'duration_ms': track.get('duration_ms'),
                            'popularity': track.get('popularity')
                        }

                        logger.info(f"Found Spotify track: {track_info['name']} by {track_info['artists']}")
                        return track_info

                    except Exception as e:
                        logger.error(f"Error extracting track information: {e}")
                        logger.error(f"Track data: {track}")
                        return None
                else:
                    logger.warning(f"No tracks found for {song.title} by {song.artist.artist_name}")
            else:
                logger.error(f"Spotify search failed: {response.status_code} - {response.text}")

        except requests.exceptions.Timeout as e:
            logger.error(f"Spotify API timeout: {e}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Spotify API request error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error searching Spotify: {e}")

        return None

    def _get_comprehensive_spotify_data(self, song: Song) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive Spotify data including audio features
        """
        track_info = self._get_spotify_track_info(song)
        if not track_info:
            return None

        # Check if we have a valid spotify_id
        spotify_id = track_info.get('spotify_id')
        if not spotify_id:
            logger.warning(f"No Spotify ID available for {song.title}")
            return track_info

        access_token = self._get_spotify_access_token()
        if not access_token:
            return track_info

        try:
            # Get audio features
            features_url = f"https://api.spotify.com/v1/audio-features/{spotify_id}"
            headers = {"Authorization": f"Bearer {access_token}"}

            features_response = requests.get(features_url, headers=headers, timeout=15)

            if features_response.status_code == 200:
                try:
                    features_data = features_response.json()

                    # Validate features_data is a dictionary
                    if not isinstance(features_data, dict):
                        logger.error(f"Audio features response is not a dictionary: {type(features_data)}")
                        return track_info

                    track_info['audio_features'] = {
                        'danceability': features_data.get('danceability'),
                        'energy': features_data.get('energy'),
                        'key': features_data.get('key'),
                        'loudness': features_data.get('loudness'),
                        'mode': features_data.get('mode'),
                        'speechiness': features_data.get('speechiness'),
                        'acousticness': features_data.get('acousticness'),
                        'instrumentalness': features_data.get('instrumentalness'),
                        'liveness': features_data.get('liveness'),
                        'valence': features_data.get('valence'),
                        'tempo': features_data.get('tempo'),
                        'duration_ms': features_data.get('duration_ms'),
                        'time_signature': features_data.get('time_signature')
                    }
                    logger.info(f"Retrieved audio features for {song.title}")

                except ValueError as e:
                    logger.error(f"Failed to parse audio features JSON: {e}")
                    logger.error(f"Response content: {features_response.text[:500]}")

            elif features_response.status_code == 404:
                logger.warning(f"Audio features not found for track {spotify_id}")
            else:
                logger.error(f"Failed to get audio features: {features_response.status_code}")

            return track_info

        except requests.exceptions.Timeout as e:
            logger.error(f"Audio features API timeout: {e}")
            return track_info
        except requests.exceptions.RequestException as e:
            logger.error(f"Audio features API request error: {e}")
            return track_info
        except Exception as e:
            logger.error(f"Unexpected error getting comprehensive Spotify data: {e}")
            return track_info

    def _get_spotify_lyrics(self, song: Song) -> Optional[str]:
        """
        Get lyrics from Spotify if available
        Note: Spotify Web API doesn't provide lyrics directly as of 2024
        This function gets track info and can be extended when lyrics become available
        """
        # Get track info from Spotify
        spotify_info = self._get_spotify_track_info(song)
        
        if spotify_info:
            # Store Spotify track ID in the song model if you have that field
            if hasattr(song, 'spotify_track_id'):
                song.spotify_track_id = spotify_info['spotify_id']
                song.save()
            
            # For now, Spotify doesn't provide lyrics via their public API
            # When they do, you can extend this function
            logger.info(f"Found Spotify track: {spotify_info['name']} by {', '.join(spotify_info['artists'])}")
        
        return None
    
    def _get_external_lyrics(self, song: Song) -> Optional[str]:
        """Get lyrics from external APIs"""
        
        # Try Genius API first
        if self.genius_api_key:
            genius_lyrics = self._get_genius_lyrics(song)
            if genius_lyrics:
                return genius_lyrics

        return None
    
    def _get_genius_lyrics(self, song: Song) -> Optional[str]:
        """Get lyrics from Genius API"""
        try:
            # Search for song
            search_url = "https://api.genius.com/search"
            headers = {"Authorization": f"Bearer {self.genius_api_key}"}
            
            search_params = {
                "q": f"{song.title} {song.artist.artist_name}"
            }
            
            response = requests.get(search_url, headers=headers, params=search_params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                hits = data.get('response', {}).get('hits', [])
                
                if hits:
                    # Get the first hit (most relevant)
                    song_data = hits[0]['result']
                    lyrics_url = song_data.get('url')
                    
                    if lyrics_url:
                        # Note: Genius doesn't provide lyrics directly through API
                        # You would need to scrape the lyrics page or use a lyrics library
                        # This is a simplified placeholder
                        return self._scrape_genius_lyrics(lyrics_url)
            
        except Exception as e:
            logger.error(f"Error fetching lyrics from Genius: {e}")
        
        return None
    
    
    def _scrape_genius_lyrics(self, url: str) -> Optional[str]:
        """
        Placeholder for scraping Genius lyrics
        You would implement web scraping here or use a library like lyricsgenius
        """
        # This is where you would implement lyrics scraping
        # For now, returning None as this requires additional implementation
        return None
    
    def _error_response(self, message: str) -> Dict[str, Any]:
        """Return standardized error response"""
        return {
            'success': False,
            'error': message,
            'lyrics': None,
            'source': None,
            'has_lyrics': False
        }



# Convenience functions for easy usage
def get_song_lyrics(song_id: int) -> Dict[str, Any]:
    """
    Main function to get lyrics for a song
    Usage: lyrics_data = get_song_lyrics(123)
    """
    service = LyricsService()
    return service.get_lyrics(song_id)


def refresh_lyrics_cache(song_id: int) -> Dict[str, Any]:
    """
    Force refresh lyrics from external sources
    """
    cache_key = f"lyrics_{song_id}"
    cache.delete(cache_key)
    
    service = LyricsService()
    return service.get_lyrics(song_id)


def batch_update_lyrics(song_ids: list) -> Dict[str, Any]:
    """
    Update lyrics for multiple songs
    Useful for background tasks
    """
    service = LyricsService()
    results = {
        'updated': 0,
        'failed': 0,
        'already_had_lyrics': 0
    }
    
    for song_id in song_ids:
        try:
            song = Song.objects.get(id=song_id)
            
            # Skip if already has lyrics
            if song.lyrics and song.lyrics.strip():
                results['already_had_lyrics'] += 1
                continue
            
            lyrics_data = service._get_external_lyrics(song)
            if lyrics_data:
                song.lyrics = lyrics_data
                song.save()
                results['updated'] += 1
            else:
                results['failed'] += 1
                
        except Song.DoesNotExist:
            results['failed'] += 1
            continue
    
    return results
