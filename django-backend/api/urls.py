from django.urls import path
from . import views

from . import views

urlpatterns = [
    path('', views.api_overview, name='api-overview'),
    path('spotify-test/', views.test_spotify_connection, name='spotify-test'),
]