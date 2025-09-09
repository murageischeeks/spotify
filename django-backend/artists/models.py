# artists/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.contrib.auth import get_user_model
from django.core.validators import EmailValidator, MinLengthValidator
from django.utils import timezone
from datetime import datetime, timedelta
import uuid

class CustomUser(AbstractUser):
    """Extended User model with role-based authentication"""
    ROLE_CHOICES = [
        ('user', 'User'),
        ('artist', 'Artist'),
        ('admin', 'Admin'),
    ]
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    email = models.EmailField(unique=True, validators=[EmailValidator()])
    is_verified = models.BooleanField(default=False)
    verification_token = models.UUIDField(default=uuid.uuid4, editable=False)
    
    # Resolve reverse accessor conflicts
    groups = models.ManyToManyField(
        Group,
        related_name='custom_users',
        blank=True,
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='custom_users',
        blank=True,
    )
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

class Artist(models.Model):
    """
    Model to represent a music artist or band.
    """
    user = models.OneToOneField(
        'CustomUser', 
        on_delete=models.CASCADE, 
        related_name='artist_profile'
    )
    artist_name = models.CharField(
        max_length=255, 
        unique=True,
        help_text="Stage/Artist name"
    )
    bio = models.TextField(
        blank=True, 
        null=True,
        help_text="Artist biography/description displayed in About section",
        max_length=2000
    )
    profile_image = models.ImageField(
        upload_to='artist_profile_images/',
        blank=True,
        null=True,
        help_text="Upload a profile picture for the artist"
    )
    
    # Contact and social media
    email = models.EmailField(
        validators=[EmailValidator()],
        help_text="Public contact email"
    )
    website = models.URLField(blank=True, null=True)
    instagram = models.CharField(max_length=100, blank=True, null=True)
    twitter = models.CharField(max_length=100, blank=True, null=True)
    facebook = models.CharField(max_length=100, blank=True, null=True)
    
    # Stats and verification
    monthly_listeners = models.IntegerField(default=0)
    total_streams = models.BigIntegerField(default=0)
    is_verified = models.BooleanField(default=False)
    verification_date = models.DateTimeField(blank=True, null=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.artist_name

    class Meta:
        ordering = ['artist_name']
    
    def get_total_streams(self):
        """Calculate total streams across all songs"""
        from songs.models import Song
        total = Song.objects.filter(artist=self).aggregate(
            total=models.Sum('total_streams')
        )['total']
        return total or 0
    
    def update_monthly_listeners(self):
        """Update monthly listeners count based on recent streams"""
        from songs.models import Stream
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        # Get unique users who streamed this artist's songs in the last 30 days
        unique_listeners = Stream.objects.filter(
            song__artist=self,
            timestamp__gte=thirty_days_ago
        ).values('user').distinct().count()
        
        self.monthly_listeners = unique_listeners
        self.save()
        return unique_listeners

class ArtistVerificationRequest(models.Model):
    """Model to handle artist verification requests"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    artist = models.OneToOneField(
        Artist, 
        on_delete=models.CASCADE,
        related_name='verification_request'
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    submitted_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(blank=True, null=True)
    processed_by = models.ForeignKey(
        'CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_verifications'
    )
    notes = models.TextField(blank=True, null=True)
    
    # Supporting documents
    identity_document = models.FileField(
        upload_to='verification_docs/',
        blank=True,
        null=True,
        help_text="Upload identity document for verification"
    )
    proof_of_artistry = models.FileField(
        upload_to='verification_docs/',
        blank=True,
        null=True,
        help_text="Upload proof of being the artist (social media, press, etc.)"
    )

class MonthlyListenerSnapshot(models.Model):
    """Store monthly snapshots of listener data for historical tracking"""
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, related_name='listener_snapshots')
    month = models.DateField()
    listener_count = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['artist', 'month']
        ordering = ['-month']