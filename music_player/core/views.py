from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from .models import User, Artist, Album, Song, Playlist, PlaylistSong, UserProfile
from .forms import PlaylistForm, UserProfileForm

def index(request):
    """Home page view"""
    recent_songs = Song.objects.all().order_by('-release_date')[:8]
    
    # Different content for authenticated vs. non-authenticated users
    if request.user.is_authenticated:
        playlists = Playlist.objects.filter(user=request.user).order_by('-creation_date')[:4]
    else:
        playlists = []
        
    context = {
        'recent_songs': recent_songs,
        'playlists': playlists,
    }
    return render(request, 'core/index.html', context)

def register(request):
    """User registration view"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create a user profile
            UserProfile.objects.create(user=user)
            login(request, user)
            messages.success(request, 'Registration successful')
            return redirect('index')
        else:
            messages.error(request, 'Registration failed. Please correct the errors.')
    else:
        form = UserCreationForm()
    
    return render(request, 'core/register.html', {'form': form})

def login_view(request):
    """User login view"""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}')
                return redirect('index')
        else:
            messages.error(request, 'Invalid username or password')
    else:
        form = AuthenticationForm()
    
    return render(request, 'core/login.html', {'form': form})

@login_required
def logout_view(request):
    """User logout view"""
    logout(request)
    messages.info(request, 'You have successfully logged out')
    return redirect('index')

@login_required
def profile(request):
    """User profile view/edit"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=profile)
    
    user_playlists = Playlist.objects.filter(user=request.user)
    
    context = {
        'form': form,
        'playlists': user_playlists
    }
    return render(request, 'core/profile.html', context)

def song_list(request):
    """List all songs"""
    songs = Song.objects.all().order_by('title')
    return render(request, 'core/songs.html', {'songs': songs})

def song_detail(request, song_id):
    """View a song's details"""
    song = get_object_or_404(Song, song_id=song_id)
    
    # If user is logged in, get their playlists for adding the song
    user_playlists = []
    if request.user.is_authenticated:
        user_playlists = Playlist.objects.filter(user=request.user)
    
    return render(request, 'core/song_detail.html', {'song': song, 'playlists': user_playlists})

def album_list(request):
    """List all albums"""
    albums = Album.objects.all().order_by('title')
    return render(request, 'core/albums.html', {'albums': albums})

def album_detail(request, album_id):
    """View an album's details"""
    album = get_object_or_404(Album, album_id=album_id)
    return render(request, 'core/album_detail.html', {'album': album})

def artist_list(request):
    """List all artists"""
    artists = Artist.objects.all().order_by('name')
    return render(request, 'core/artists.html', {'artists': artists})

def artist_detail(request, artist_id):
    """View an artist's details"""
    artist = get_object_or_404(Artist, artist_id=artist_id)
    return render(request, 'core/artist_detail.html', {'artist': artist})

@login_required
def playlist_list(request):
    """List all playlists of the current user"""
    playlists = Playlist.objects.filter(user=request.user).order_by('-creation_date')
    return render(request, 'core/playlists.html', {'playlists': playlists})

@login_required
def playlist_detail(request, playlist_id):
    """View a playlist's details"""
    playlist = get_object_or_404(Playlist, playlist_id=playlist_id)
    
    # Only allow the owner to view the playlist
    if playlist.user != request.user:
        messages.error(request, 'You do not have permission to view this playlist')
        return redirect('playlists')
    
    return render(request, 'core/playlist_detail.html', {'playlist': playlist})

@login_required
def playlist_create(request):
    """Create a new playlist"""
    if request.method == 'POST':
        form = PlaylistForm(request.POST)
        if form.is_valid():
            playlist = form.save(commit=False)
            playlist.user = request.user
            playlist.save()
            messages.success(request, 'Playlist created successfully')
            return redirect('playlist_detail', playlist_id=playlist.playlist_id)
    else:
        form = PlaylistForm()
    
    return render(request, 'core/playlist_form.html', {'form': form, 'action': 'Create'})

@login_required
def playlist_update(request, playlist_id):
    """Update an existing playlist"""
    playlist = get_object_or_404(Playlist, playlist_id=playlist_id)
    
    # Only allow the owner to edit the playlist
    if playlist.user != request.user:
        messages.error(request, 'You do not have permission to edit this playlist')
        return redirect('playlists')
    
    if request.method == 'POST':
        form = PlaylistForm(request.POST, instance=playlist)
        if form.is_valid():
            form.save()
            messages.success(request, 'Playlist updated successfully')
            return redirect('playlist_detail', playlist_id=playlist.playlist_id)
    else:
        form = PlaylistForm(instance=playlist)
    
    return render(request, 'core/playlist_form.html', {'form': form, 'action': 'Update'})

@login_required
def playlist_delete(request, playlist_id):
    """Delete a playlist"""
    playlist = get_object_or_404(Playlist, playlist_id=playlist_id)
    
    # Only allow the owner to delete the playlist
    if playlist.user != request.user:
        messages.error(request, 'You do not have permission to delete this playlist')
        return redirect('playlists')
    
    if request.method == 'POST':
        playlist.delete()
        messages.success(request, 'Playlist deleted successfully')
        return redirect('playlists')
    
    return render(request, 'core/playlist_form.html', {'playlist': playlist, 'action': 'Delete'})

@login_required
def add_song_to_playlist(request):
    """Add a song to a playlist (AJAX)"""
    if request.method == 'POST':
        song_id = request.POST.get('song_id')
        playlist_id = request.POST.get('playlist_id')
        
        try:
            song = Song.objects.get(song_id=song_id)
            playlist = Playlist.objects.get(playlist_id=playlist_id, user=request.user)
            
            # Check if song is already in the playlist
            if not PlaylistSong.objects.filter(playlist=playlist, song=song).exists():
                PlaylistSong.objects.create(playlist=playlist, song=song)
                return JsonResponse({'status': 'success', 'message': f'Added "{song.title}" to playlist "{playlist.title}"'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Song is already in this playlist'})
                
        except (Song.DoesNotExist, Playlist.DoesNotExist):
            return JsonResponse({'status': 'error', 'message': 'Song or playlist not found'})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

@login_required
def remove_song_from_playlist(request):
    """Remove a song from a playlist (AJAX)"""
    if request.method == 'POST':
        song_id = request.POST.get('song_id')
        playlist_id = request.POST.get('playlist_id')
        
        try:
            song = Song.objects.get(song_id=song_id)
            playlist = Playlist.objects.get(playlist_id=playlist_id, user=request.user)
            
            # Check if song is in the playlist
            playlist_song = PlaylistSong.objects.filter(playlist=playlist, song=song)
            if playlist_song.exists():
                playlist_song.delete()
                return JsonResponse({'status': 'success', 'message': f'Removed "{song.title}" from playlist "{playlist.title}"'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Song is not in this playlist'})
                
        except (Song.DoesNotExist, Playlist.DoesNotExist):
            return JsonResponse({'status': 'error', 'message': 'Song or playlist not found'})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

def search(request):
    """Search for songs, albums, and artists"""
    query = request.GET.get('q', '')
    
    if query:
        songs = Song.objects.filter(Q(title__icontains=query) | Q(genre__icontains=query))
        albums = Album.objects.filter(Q(title__icontains=query) | Q(genre__icontains=query))
        artists = Artist.objects.filter(Q(name__icontains=query) | Q(genre__icontains=query))
    else:
        songs = []
        albums = []
        artists = []
    
    context = {
        'query': query,
        'songs': songs,
        'albums': albums,
        'artists': artists,
    }
    return render(request, 'core/search.html', context)
