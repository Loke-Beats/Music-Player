from django.contrib import admin
from django.utils.html import format_html
from .models import Artist, Album, Song, Playlist, PlaylistSong, UserProfile

@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    list_display = ('name', 'genre')
    search_fields = ('name', 'genre')
    list_filter = ('genre',)
    fieldsets = (
        ('Artist Information', {
            'fields': ('name', 'genre', 'biography')
        }),
    )

@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    list_display = ('title', 'artist', 'genre', 'release_date')
    list_filter = ('genre', 'release_date', 'artist')
    search_fields = ('title', 'artist__name')
    date_hierarchy = 'release_date'

@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
    list_display = ('title', 'album', 'artist_display', 'duration_formatted', 'genre', 'release_date', 'song_file_preview')
    list_filter = ('genre', 'drm_type', 'release_date', 'album__artist')
    search_fields = ('title', 'album__title', 'album__artist__name')
    readonly_fields = ('duration_formatted',)
    
    def artist_display(self, obj):
        return obj.album.artist.name
    artist_display.short_description = 'Artist'
    
    def song_file_preview(self, obj):
        if obj.song_file:
            return format_html('<a href="{}" target="_blank">Listen</a>', obj.song_file.url)
        return "No file"
    song_file_preview.short_description = 'Song File'
    
    fieldsets = (
        ('Song Information', {
            'fields': ('title', 'album', 'duration', 'genre', 'release_date')
        }),
        ('File and Access', {
            'fields': ('song_file', 'drm_type')
        }),
    )

class PlaylistSongInline(admin.TabularInline):
    model = PlaylistSong
    extra = 1

@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'creation_date', 'song_count')
    list_filter = ('creation_date', 'user')
    search_fields = ('title', 'user__username')
    inlines = [PlaylistSongInline]
    
    def song_count(self, obj):
        return obj.songs.count()
    song_count.short_description = 'Number of Songs'

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'date_of_birth')
    search_fields = ('user__username', 'user__email')

# Customize admin site
admin.site.site_header = "Music Player Admin"
admin.site.site_title = "Music Player Admin Portal"
admin.site.index_title = "Welcome to Music Player Admin Portal"
