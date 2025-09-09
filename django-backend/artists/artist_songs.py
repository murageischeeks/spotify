# artists/artist_songs.py
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from songs.models import Song, Genre
from .models import Artist
import json
import os
import logging
import mimetypes
from mutagen import File as MutagenFile
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.mp4 import MP4

logger = logging.getLogger(__name__)

# Allowed audio formats
ALLOWED_AUDIO_FORMATS = {
    'audio/mpeg': ['.mp3'],
    'audio/flac': ['.flac'],
    'audio/mp4': ['.m4a'],
    'audio/wav': ['.wav'],
    'audio/ogg': ['.ogg']
}

@require_http_methods(["GET"])
@login_required
def get_artist_songs(request):
    """
    Get all songs by the authenticated artist
    GET /artists/songs/
    """
    if request.user.role != 'artist':
        return JsonResponse({
            'success': False,
            'error': 'Access denied. Artist account required.'
        }, status=403)
    
    try:
        artist = request.user.artist_profile
        
        # Get all songs by this artist
        songs = Song.objects.filter(artist=artist).select_related('genre').order_by('-created_at')
        
        songs_data = []
        total_streams = 0
        
        for song in songs:
            song_streams = song.streams or 0
            total_streams += song_streams
            
            songs_data.append({
                'id': song.id,
                'title': song.title,
                'genre': song.genre.name if song.genre else None,
                'duration': song.duration,
                'streams': song_streams,
                'audio_file': song.audio_file.url if song.audio_file else None,
                'cover_image': song.cover_image.url if song.cover_image else None,
                'lyrics': song.lyrics,
                'release_date': song.release_date.isoformat() if song.release_date else None,
                'created_at': song.created_at.isoformat(),
                'updated_at': song.updated_at.isoformat()
            })
        
        return JsonResponse({
            'success': True,
            'data': {
                'artist': {
                    'id': artist.id,
                    'artist_name': artist.artist_name,
                    'total_songs': songs.count(),
                    'total_streams': total_streams
                },
                'songs': songs_data
            }
        })
        
    except Artist.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Artist profile not found'
        }, status=404)
    except Exception as e:
        logger.error(f"Error retrieving artist songs: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to retrieve songs'
        }, status=500)

@require_http_methods(["POST"])
@login_required
@csrf_exempt
def upload_song(request):
    """
    Upload a new song
    POST /artists/songs/upload/
    """
    if request.user.role != 'artist':
        return JsonResponse({
            'success': False,
            'error': 'Access denied. Artist account required.'
        }, status=403)
    
    try:
        artist = request.user.artist_profile
        
        # Get form data
        title = request.POST.get('title')
        genre_id = request.POST.get('genre_id')
        lyrics = request.POST.get('lyrics', '')
        release_date = request.POST.get('release_date')
        
        # Validate required fields
        if not title:
            return JsonResponse({
                'success': False,
                'error': 'Song title is required'
            }, status=400)
        
        # Check if audio file is provided
        if 'audio_file' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'Audio file is required'
            }, status=400)
        
        audio_file = request.FILES['audio_file']
        
        # Validate audio file format
        if not validate_audio_file(audio_file):
            return JsonResponse({
                'success': False,
                'error': 'Invalid audio format. Supported formats: MP3, FLAC, M4A, WAV, OGG'
            }, status=400)
        
        # Get audio metadata
        duration = get_audio_duration(audio_file)
        
        # Validate genre if provided
        genre = None
        if genre_id:
            try:
                genre = Genre.objects.get(id=genre_id)
            except Genre.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid genre selected'
                }, status=400)
        
        # Create song
        song = Song.objects.create(
            title=title,
            artist=artist,
            genre=genre,
            duration=duration,
            lyrics=lyrics,
            release_date=release_date if release_date else None,
            audio_file=audio_file,
            cover_image=request.FILES.get('cover_image')
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Song uploaded successfully',
            'song': {
                'id': song.id,
                'title': song.title,
                'artist': artist.artist_name,
                'genre': genre.name if genre else None,
                'duration': song.duration,
                'audio_file': song.audio_file.url,
                'cover_image': song.cover_image.url if song.cover_image else None,
                'created_at': song.created_at.isoformat()
            }
        })
        
    except Artist.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Artist profile not found'
        }, status=404)
    except Exception as e:
        logger.error(f"Error uploading song: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to upload song'
        }, status=500)

@require_http_methods(["GET", "PUT", "DELETE"])
@login_required
def manage_song(request, song_id):
    """
    Get, update, or delete a specific song
    GET /artists/songs/{song_id}/ - Get song details
    PUT /artists/songs/{song_id}/ - Update song
    DELETE /artists/songs/{song_id}/ - Delete song
    """
    if request.user.role != 'artist':
        return JsonResponse({
            'success': False,
            'error': 'Access denied. Artist account required.'
        }, status=403)
    
    try:
        artist = request.user.artist_profile
        
        # Get song and verify ownership
        try:
            song = Song.objects.get(id=song_id, artist=artist)
        except Song.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Song not found or access denied'
            }, status=404)
        
        if request.method == 'GET':
            return JsonResponse({
                'success': True,
                'song': {
                    'id': song.id,
                    'title': song.title,
                    'genre': {
                        'id': song.genre.id,
                        'name': song.genre.name
                    } if song.genre else None,
                    'duration': song.duration,
                    'streams': song.streams,
                    'lyrics': song.lyrics,
                    'release_date': song.release_date.isoformat() if song.release_date else None,
                    'audio_file': song.audio_file.url if song.audio_file else None,
                    'cover_image': song.cover_image.url if song.cover_image else None,
                    'created_at': song.created_at.isoformat(),
                    'updated_at': song.updated_at.isoformat()
                }
            })
        
        elif request.method == 'PUT':
            # Update song
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                
                # Update text fields
                if 'title' in data:
                    song.title = data['title']
                if 'lyrics' in data:
                    song.lyrics = data['lyrics']
                if 'release_date' in data:
                    song.release_date = data['release_date'] if data['release_date'] else None
                if 'genre_id' in data:
                    if data['genre_id']:
                        try:
                            genre = Genre.objects.get(id=data['genre_id'])
                            song.genre = genre
                        except Genre.DoesNotExist:
                            return JsonResponse({
                                'success': False,
                                'error': 'Invalid genre selected'
                            }, status=400)
                    else:
                        song.genre = None
                
                song.save()
                
            else:
                # Handle form data (for file uploads)
                if 'title' in request.POST:
                    song.title = request.POST['title']
                if 'lyrics' in request.POST:
                    song.lyrics = request.POST['lyrics']
                if 'release_date' in request.POST:
                    song.release_date = request.POST['release_date'] if request.POST['release_date'] else None
                if 'genre_id' in request.POST:
                    genre_id = request.POST['genre_id']
                    if genre_id:
                        try:
                            genre = Genre.objects.get(id=genre_id)
                            song.genre = genre
                        except Genre.DoesNotExist:
                            return JsonResponse({
                                'success': False,
                                'error': 'Invalid genre selected'
                            }, status=400)
                    else:
                        song.genre = None
                
                # Handle file updates
                if 'audio_file' in request.FILES:
                    new_audio = request.FILES['audio_file']
                    if validate_audio_file(new_audio):
                        # Delete old audio file
                        if song.audio_file:
                            old_path = song.audio_file.path
                            if os.path.exists(old_path):
                                os.remove(old_path)
                        
                        song.audio_file = new_audio
                        song.duration = get_audio_duration(new_audio)
                    else:
                        return JsonResponse({
                            'success': False,
                            'error': 'Invalid audio format'
                        }, status=400)
                
                if 'cover_image' in request.FILES:
                    new_cover = request.FILES['cover_image']
                    # Delete old cover image if exists
                    if song.cover_image:
                        old_cover_path = song.cover_image.path
                        if os.path.exists(old_cover_path):
                            os.remove(old_cover_path)
                    song.cover_image = new_cover
                
                song.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Song updated successfully',
                'song': {
                    'id': song.id,
                    'title': song.title,
                    'genre': song.genre.name if song.genre else None,
                    'duration': song.duration,
                    'lyrics': song.lyrics,
                    'release_date': song.release_date.isoformat() if song.release_date else None
                }
            })
        
        elif request.method == 'DELETE':
            # Delete song files
            if song.audio_file:
                audio_path = song.audio_file.path
                if os.path.exists(audio_path):
                    os.remove(audio_path)
            
            if song.cover_image:
                cover_path = song.cover_image.path
                if os.path.exists(cover_path):
                    os.remove(cover_path)
            
            song.delete()
            
            return JsonResponse({
                'success': True,
                'message': 'Song deleted successfully'
            })
        
    except Artist.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Artist profile not found'
        }, status=404)
    except Exception as e:
        logger.error(f"Error managing song: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to process request'
        }, status=500)

# Helper functions
def validate_audio_file(file):
    """Validate audio file format"""
    file_extension = os.path.splitext(file.name)[1].lower()
    content_type = file.content_type
    
    for allowed_type, extensions in ALLOWED_AUDIO_FORMATS.items():
        if content_type == allowed_type and file_extension in extensions:
            return True
    
    # Fallback: check file signature if content type is unreliable
    try:
        file.seek(0)
        header = file.read(4)
        file.seek(0)
        
        # MP3 signature check
        if header.startswith(b'ID3') or header.startswith(b'\xFF\xFB'):
            return True
        # FLAC signature check
        elif header == b'fLaC':
            return True
        # WAV signature check
        elif header == b'RIFF':
            return True
    except:
        pass
    
    return False

def get_audio_duration(file):
    """Extract audio duration using mutagen"""
    try:
        file.seek(0)
        
        if file.name.lower().endswith('.mp3'):
            audio = MP3(file)
        elif file.name.lower().endswith('.flac'):
            audio = FLAC(file)
        elif file.name.lower().endswith(('.m4a', '.mp4')):
            audio = MP4(file)
        else:
            # Default to 0 if format not specifically handled
            return 0
        
        return int(audio.info.length)
    except Exception as e:
        logger.error(f"Error extracting audio duration: {e}")
        return 0