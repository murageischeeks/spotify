from django.db import models
from artists.models import Artist

# Create your models here.
class Album(models.Model):
    """
    Model to represent an album that contains songs.
    """
    title = models.CharField(max_length=255)
    artist = models.ForeignKey(
        Artist,
        on_delete=models.CASCADE,
        related_name='albums'
    )
    cover_image = models.ImageField(
        upload_to='album_covers/',
        blank=True,
        null=True
    )
    release_date = models.DateField(blank=True, null=True)
    genre = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.artist.artist_name}"

    class Meta:
        ordering = ['-release_date']  # Newest albums first


