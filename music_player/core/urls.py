from django.urls import path
from . import views

urlpatterns = [
    # Home page
    path('', views.index, name='index'),
    
    # Authentication
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
    
    # Songs
    path('songs/', views.song_list, name='songs'),
    path('songs/<int:song_id>/', views.song_detail, name='song_detail'),
    
    # Albums
    path('albums/', views.album_list, name='albums'),
    path('albums/<int:album_id>/', views.album_detail, name='album_detail'),
    
    # Artists
    path('artists/', views.artist_list, name='artists'),
    path('artists/<int:artist_id>/', views.artist_detail, name='artist_detail'),
    
    # Playlists
    path('playlists/', views.playlist_list, name='playlists'),
    path('playlists/<int:playlist_id>/', views.playlist_detail, name='playlist_detail'),
    path('playlists/create/', views.playlist_create, name='playlist_create'),
    path('playlists/<int:playlist_id>/update/', views.playlist_update, name='playlist_update'),
    path('playlists/<int:playlist_id>/delete/', views.playlist_delete, name='playlist_delete'),
    
    # Playlist song management
    path('add-song-to-playlist/', views.add_song_to_playlist, name='add_song_to_playlist'),
    path('remove-song-from-playlist/', views.remove_song_from_playlist, name='remove_song_from_playlist'),
    
    # Search
    path('search/', views.search, name='search'),
]
