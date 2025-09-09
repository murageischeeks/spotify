from django.urls import path
from . import views

urlpatterns = [
    path('', views.playlist_list, name='playlist-list'),
    path('<int:playlist_id>/', views.playlist_detail, name='playlist-detail'),
]