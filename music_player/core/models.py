from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse

class Artist(models.Model):
    artist_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200)
    biography = models.TextField(blank=True)
    genre = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return str(self.name)
    
    def get_absolute_url(self):
        return reverse('artist_detail', args=[str(self.artist_id)])

class Album(models.Model):
    album_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=200)
    genre = models.CharField(max_length=100, blank=True)
    release_date = models.DateField()
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, related_name='albums')
    
    def __str__(self):
        return str(self.title)
    
    def get_absolute_url(self):
        return reverse('album_detail', args=[str(self.album_id)])

class Song(models.Model):
    DRM_TYPES = (
        ('free', 'Free'),
        ('protected', 'Protected'),
        ('premium', 'Premium')
    )
    
    song_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=200)
    duration = models.IntegerField(help_text="Duration in seconds")
    genre = models.CharField(max_length=100, blank=True)
    release_date = models.DateField()
    drm_type = models.CharField(max_length=10, choices=DRM_TYPES, default='free')
    album = models.ForeignKey(Album, on_delete=models.CASCADE, related_name='songs')
    song_file = models.FileField(upload_to='songs/', null=True, blank=True)
    
    def __str__(self):
        return str(self.title)
    
    def get_absolute_url(self):
        return reverse('song_detail', args=[str(self.song_id)])
    
    def duration_formatted(self):
        minutes = int(self.duration) // 60
        seconds = int(self.duration) % 60
        return f"{minutes}:{seconds:02d}"
        
    def has_song_file(self):
        return bool(self.song_file)

class Playlist(models.Model):
    playlist_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    distance = models.FloatField(null=True, blank=True, help_text="Distance in meters")
    creation_date = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='playlists')
    songs = models.ManyToManyField(Song, related_name='playlists', through='PlaylistSong')
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('playlist_detail', args=[str(self.playlist_id)])

class PlaylistSong(models.Model):
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE)
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    added_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('playlist', 'song')
        ordering = ['added_date']
    
    def __str__(self):
        return f"{self.playlist.title} - {self.song.title}"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    date_of_birth = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return f"Profile for {self.user.username}"
