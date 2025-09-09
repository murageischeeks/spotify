from django.http import JsonResponse

def playlist_list(request):
    """
    API endpoint to get all playlists
    GET /playlists/playlists/
    """
    # Placeholder - playlists model is empty
    return JsonResponse({'playlists': [], 'message': 'Playlists feature not implemented yet'})

def playlist_detail(request, playlist_id):
    """
    API endpoint to get playlist details
    GET /playlists/playlists/<playlist_id>/
    """
    # Placeholder - playlists model is empty
    return JsonResponse({'error': 'Playlist not found', 'message': 'Playlists feature not implemented yet'}, status=404)
