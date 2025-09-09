from django.urls import path
from .views import (
    get_song_details_with_spotify_data,
    get_lyrics_view,
    refresh_lyrics_view,
    song_stream_analytics,
    top_songs
)

urlpatterns = [
    path('', get_song_details_with_spotify_data, name='all-songs'),
    path('<int:song_id>/', get_song_details_with_spotify_data, name='single-song'),
    path('<int:song_id>/lyrics/', get_lyrics_view, name='song-lyrics'),
    path('<int:song_id>/lyrics/refresh/', refresh_lyrics_view, name='refresh-lyrics'),
    path('analytics/', song_stream_analytics, name='song-analytics'),
    path('analytics/<int:song_id>/', song_stream_analytics, name='single-song-analytics'),
    path('top-songs/', top_songs, name='top-songs'),
]