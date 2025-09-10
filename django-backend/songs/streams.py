from django.utils import timezone
from songs.models import Song, Stream
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()

def track_stream(song_id, user_id, duration_listened=0):
    """
    Function to track when a user streams a song
    Returns the stream object if successful
    """
    try:
        song = Song.objects.get(id=song_id)
        user = User.objects.get(id=user_id)
        
        # Create stream record
        stream = Stream.objects.create(
            song=song,
            user=user,
            duration_listened=duration_listened
        )
        
        # Update total stream count on song
        song.streams += 1
        song.save()
        
        return stream
        
    except (Song.DoesNotExist, User.DoesNotExist):
        return None


def get_stream_analytics(song_id=None, time_period=None):
    """
    Main function to get streaming analytics
    Can be used for a specific song or all songs
    """
    if song_id:
        # Get analytics for specific song
        return get_song_stream_analytics(song_id, time_period)
    else:
        # Get analytics for all songs
        return get_all_songs_stream_analytics(time_period)


def get_song_stream_analytics(song_id, time_period=None):
    """
    Get detailed analytics for a specific song
    """
    try:
        song = Song.objects.get(id=song_id)
    except Song.DoesNotExist:
        return None
    
    # Base queryset
    streams = Stream.objects.filter(song=song)
    
    # Apply time filter if specified
    if time_period:
        if time_period == 'today':
            streams = streams.filter(timestamp__date=timezone.now().date())
        elif time_period == 'week':
            streams = streams.filter(timestamp__gte=timezone.now() - timezone.timedelta(days=7))
        elif time_period == 'month':
            streams = streams.filter(timestamp__gte=timezone.now() - timezone.timedelta(days=30))
    
    # Calculate metrics
    total_streams = streams.count()
    unique_listeners = streams.values('user').distinct().count()
    total_duration = streams.aggregate(total_duration=models.Sum('duration_listened'))['total_duration'] or 0
    
    return {
        'song_id': song.id,
        'song_title': song.title,
        'artist': song.artist.artist_name,
        'total_streams': total_streams,
        'unique_listeners': unique_listeners,
        'total_duration_listened_seconds': total_duration,
        'total_duration_listened_formatted': format_duration(total_duration),
        'time_period': time_period or 'all_time'
    }


def get_all_songs_stream_analytics(time_period=None):
    """
    Get streaming analytics for all songs, ordered by most streams
    """
    songs = Song.objects.all()
    analytics = []
    
    for song in songs:
        song_data = get_song_stream_analytics(song.id, time_period)
        if song_data:
            analytics.append(song_data)
    
    # Sort by total streams descending
    analytics.sort(key=lambda x: x['total_streams'], reverse=True)
    
    return analytics


def format_duration(seconds):
    """Convert seconds to human-readable format"""
    if seconds >= 3600:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"
    elif seconds >= 60:
        minutes = seconds // 60
        return f"{minutes}m"
    else:
        return f"{seconds}s"


def get_top_songs(limit=10, time_period=None):
    """
    Get top songs by stream count
    """
    analytics = get_all_songs_stream_analytics(time_period)
    return analytics[:limit]