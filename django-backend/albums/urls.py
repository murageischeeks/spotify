from django.urls import path
from . import views

urlpatterns = [
    path('', views.album_list, name='album-list'),
    path('<int:album_id>/', views.album_detail, name='album-detail'),
]