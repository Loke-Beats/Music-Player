from django.contrib import admin
from .models import Artist, Album, Song, Playlist, PlaylistSong, UserProfile

@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    list_display = ('name', 'genre')
    search_fields = ('name', 'genre')

@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    list_display = ('title', 'artist', 'genre', 'release_date')
    list_filter = ('genre', 'release_date')
    search_fields = ('title', 'artist__name')

@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
    list_display = ('title', 'album', 'duration_formatted', 'genre', 'release_date')
    list_filter = ('genre', 'drm_type', 'release_date')
    search_fields = ('title', 'album__title', 'album__artist__name')

class PlaylistSongInline(admin.TabularInline):
    model = PlaylistSong
    extra = 1

@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'creation_date')
    list_filter = ('creation_date',)
    search_fields = ('title', 'user__username')
    inlines = [PlaylistSongInline]

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'date_of_birth')
    search_fields = ('user__username',)
