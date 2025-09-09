from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()  # Get the user model (from Laravel's users table)

class Song(models.Model):
    title = models.CharField(max_length=255)
    artist = models.ForeignKey('artists.Artist', on_delete=models.CASCADE, related_name='songs')
    album = models.ForeignKey('albums.Album', on_delete=models.SET_NULL, null=True, blank=True, related_name='songs')
    duration = models.PositiveIntegerField(help_text="Duration in seconds")
    audio_file = models.FileField(upload_to='songs/')
    total_streams = models.PositiveIntegerField(default=0)  # Total stream count
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} by {self.artist.artist_name}"
    
    @property
    def duration_formatted(self):
        minutes = self.duration // 60
        seconds = self.duration % 60
        return f"{minutes}:{seconds:02d}"

    @property
    def unique_listeners_count(self):
        """Returns number of unique users who listened to this song"""
        return self.streams.all().values('user').distinct().count()


class Stream(models.Model):
    """
    Model to track individual stream events for analytics.
    This allows us to count unique listeners.
    """
    song = models.ForeignKey(Song, on_delete=models.CASCADE, related_name='streams')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='streams')
    timestamp = models.DateTimeField(auto_now_add=True)
    duration_listened = models.PositiveIntegerField(help_text="Seconds listened", default=0)
    
    class Meta:
        ordering = ['-timestamp']
        unique_together = ['song', 'user', 'timestamp']  # Prevent duplicate records
    
    def __str__(self):
        return f"{self.user} listened to {self.song} at {self.timestamp}"
