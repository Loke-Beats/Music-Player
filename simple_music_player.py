import os
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "your-secret-key-for-music-player")

# Configure upload folder for song files
UPLOAD_FOLDER = 'uploads/songs'
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'ogg', 'flac', 'm4a'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create necessary directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('data', exist_ok=True)

# Data files
USERS_FILE = 'data/users.json'
ARTISTS_FILE = 'data/artists.json'
ALBUMS_FILE = 'data/albums.json'
SONGS_FILE = 'data/songs.json'
PLAYLISTS_FILE = 'data/playlists.json'

# Initialize data files if they don't exist
def init_data_file(file_path, default_data=None):
    if default_data is None:
        default_data = []
    
    if not os.path.exists(file_path):
        with open(file_path, 'w') as f:
            json.dump(default_data, f)
    
    return file_path

# Initialize all data files
init_data_file(USERS_FILE, [{"id": 1, "username": "admin", "password": generate_password_hash("admin"), "email": "admin@example.com", "is_admin": True}])
init_data_file(ARTISTS_FILE, [])
init_data_file(ALBUMS_FILE, [])
init_data_file(SONGS_FILE, [])
init_data_file(PLAYLISTS_FILE, [])

# Data access functions
def load_data(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

def save_data(file_path, data):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

def get_next_id(data_list):
    if not data_list:
        return 1
    return max(item.get('id', 0) for item in data_list) + 1

# Helper functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def format_duration(seconds):
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes}:{seconds:02d}"

def get_user_by_id(user_id):
    users = load_data(USERS_FILE)
    for user in users:
        if user['id'] == user_id:
            return user
    return None

def get_song_by_id(song_id):
    songs = load_data(SONGS_FILE)
    for song in songs:
        if song['id'] == song_id:
            return song
    return None

def get_album_by_id(album_id):
    albums = load_data(ALBUMS_FILE)
    for album in albums:
        if album['id'] == album_id:
            return album
    return None

def get_artist_by_id(artist_id):
    artists = load_data(ARTISTS_FILE)
    for artist in artists:
        if artist['id'] == artist_id:
            return artist
    return None

def get_playlist_by_id(playlist_id):
    playlists = load_data(PLAYLISTS_FILE)
    for playlist in playlists:
        if playlist['id'] == playlist_id:
            return playlist
    return None

def enrich_songs_with_album_artist(songs):
    albums = load_data(ALBUMS_FILE)
    artists = load_data(ARTISTS_FILE)
    
    album_dict = {album['id']: album for album in albums}
    artist_dict = {artist['id']: artist for artist in artists}
    
    for song in songs:
        album = album_dict.get(song['album_id'], {})
        song['album'] = album
        
        artist_id = album.get('artist_id')
        if artist_id:
            song['artist'] = artist_dict.get(artist_id, {})
    
    return songs

def find_songs_not_in_playlist(playlist_id):
    all_songs = load_data(SONGS_FILE)
    all_songs = enrich_songs_with_album_artist(all_songs)
    
    playlist = get_playlist_by_id(playlist_id)
    if not playlist:
        return []
    
    playlist_song_ids = playlist.get('song_ids', [])
    return [song for song in all_songs if song['id'] not in playlist_song_ids]

# Routes
@app.route('/')
def index():
    songs = load_data(SONGS_FILE)
    songs = enrich_songs_with_album_artist(songs)
    
    return render_template('index.html', songs=songs, format_duration=format_duration)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        users = load_data(USERS_FILE)
        user = None
        
        for u in users:
            if u['username'] == username:
                user = u
                break
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = user.get('is_admin', False)
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('is_admin', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('register.html')
        
        users = load_data(USERS_FILE)
        
        # Check if username or email already exists
        for user in users:
            if user['username'] == username or user['email'] == email:
                flash('Username or email already exists', 'danger')
                return render_template('register.html')
        
        # Create new user
        new_user = {
            'id': get_next_id(users),
            'username': username,
            'email': email,
            'password': generate_password_hash(password),
            'is_admin': False  # Only the first user should be admin
        }
        
        users.append(new_user)
        save_data(USERS_FILE, users)
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

# Admin Routes
@app.route('/admin')
def admin():
    if not session.get('is_admin'):
        flash('Admin access required', 'danger')
        return redirect(url_for('index'))
    
    artists = load_data(ARTISTS_FILE)
    albums = load_data(ALBUMS_FILE)
    songs = load_data(SONGS_FILE)
    songs = enrich_songs_with_album_artist(songs)
    
    return render_template('admin.html', artists=artists, albums=albums, songs=songs, format_duration=format_duration)

@app.route('/admin/artist/add', methods=['GET', 'POST'])
def add_artist():
    if not session.get('is_admin'):
        flash('Admin access required', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        name = request.form['name']
        genre = request.form['genre']
        bio = request.form['bio']
        
        artists = load_data(ARTISTS_FILE)
        
        new_artist = {
            'id': get_next_id(artists),
            'name': name,
            'genre': genre,
            'bio': bio,
            'created_at': datetime.now().isoformat()
        }
        
        artists.append(new_artist)
        save_data(ARTISTS_FILE, artists)
        
        flash('Artist added successfully', 'success')
        return redirect(url_for('admin'))
    
    return render_template('add_artist.html')

@app.route('/admin/album/add', methods=['GET', 'POST'])
def add_album():
    if not session.get('is_admin'):
        flash('Admin access required', 'danger')
        return redirect(url_for('index'))
    
    artists = load_data(ARTISTS_FILE)
    
    if request.method == 'POST':
        title = request.form['title']
        artist_id = int(request.form['artist_id'])
        release_date = request.form['release_date']
        genre = request.form['genre']
        
        albums = load_data(ALBUMS_FILE)
        
        new_album = {
            'id': get_next_id(albums),
            'title': title,
            'artist_id': artist_id,
            'release_date': release_date,
            'genre': genre,
            'created_at': datetime.now().isoformat()
        }
        
        albums.append(new_album)
        save_data(ALBUMS_FILE, albums)
        
        flash('Album added successfully', 'success')
        return redirect(url_for('admin'))
    
    return render_template('add_album.html', artists=artists)

@app.route('/admin/song/add', methods=['GET', 'POST'])
def add_song():
    if not session.get('is_admin'):
        flash('Admin access required', 'danger')
        return redirect(url_for('index'))
    
    albums = load_data(ALBUMS_FILE)
    artists = load_data(ARTISTS_FILE)
    
    # Add artist names to albums
    for album in albums:
        for artist in artists:
            if album['artist_id'] == artist['id']:
                album['artist_name'] = artist['name']
                break
    
    if request.method == 'POST':
        title = request.form['title']
        album_id = int(request.form['album_id'])
        duration = int(request.form['duration'])
        genre = request.form['genre']
        
        # Handle file upload
        file_path = None
        if 'song_file' in request.files:
            file = request.files['song_file']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Add timestamp to filename to make it unique
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                unique_filename = f"{timestamp}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(file_path)
        
        songs = load_data(SONGS_FILE)
        
        new_song = {
            'id': get_next_id(songs),
            'title': title,
            'album_id': album_id,
            'duration': duration,
            'genre': genre,
            'file_path': file_path,
            'created_at': datetime.now().isoformat()
        }
        
        songs.append(new_song)
        save_data(SONGS_FILE, songs)
        
        flash('Song added successfully', 'success')
        return redirect(url_for('admin'))
    
    return render_template('add_song.html', albums=albums)

@app.route('/uploads/songs/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Playlist management
@app.route('/playlist/create', methods=['GET', 'POST'])
def create_playlist():
    if 'user_id' not in session:
        flash('Please log in to create a playlist', 'danger')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form['title']
        
        playlists = load_data(PLAYLISTS_FILE)
        
        new_playlist = {
            'id': get_next_id(playlists),
            'title': title,
            'user_id': session['user_id'],
            'song_ids': [],
            'created_at': datetime.now().isoformat()
        }
        
        playlists.append(new_playlist)
        save_data(PLAYLISTS_FILE, playlists)
        
        flash('Playlist created successfully', 'success')
        return redirect(url_for('view_playlists'))
    
    return render_template('create_playlist.html')

@app.route('/playlists')
def view_playlists():
    if 'user_id' not in session:
        flash('Please log in to view your playlists', 'danger')
        return redirect(url_for('login'))
    
    playlists = load_data(PLAYLISTS_FILE)
    user_playlists = [p for p in playlists if p['user_id'] == session['user_id']]
    
    # Get song counts
    songs = load_data(SONGS_FILE)
    song_dict = {song['id']: song for song in songs}
    
    for playlist in user_playlists:
        playlist['song_count'] = len(playlist.get('song_ids', []))
        playlist['songs'] = [song_dict.get(song_id) for song_id in playlist.get('song_ids', []) if song_id in song_dict]
    
    return render_template('playlists.html', playlists=user_playlists)

@app.route('/playlist/<int:playlist_id>')
def view_playlist(playlist_id):
    if 'user_id' not in session:
        flash('Please log in to view playlists', 'danger')
        return redirect(url_for('login'))
    
    playlist = get_playlist_by_id(playlist_id)
    
    if not playlist:
        flash('Playlist not found', 'danger')
        return redirect(url_for('view_playlists'))
    
    # Check if the user is the owner of the playlist
    if playlist['user_id'] != session['user_id'] and not session.get('is_admin'):
        flash('You do not have permission to view this playlist', 'danger')
        return redirect(url_for('view_playlists'))
    
    # Get song details
    songs = load_data(SONGS_FILE)
    song_dict = {song['id']: song for song in songs}
    
    playlist_songs = [song_dict.get(song_id) for song_id in playlist.get('song_ids', []) if song_id in song_dict]
    playlist_songs = enrich_songs_with_album_artist(playlist_songs)
    
    return render_template('playlist.html', playlist=playlist, songs=playlist_songs, format_duration=format_duration)

@app.route('/playlist/<int:playlist_id>/add_song', methods=['GET', 'POST'])
def add_song_to_playlist(playlist_id):
    if 'user_id' not in session:
        flash('Please log in to add songs to a playlist', 'danger')
        return redirect(url_for('login'))
    
    playlists = load_data(PLAYLISTS_FILE)
    playlist = None
    
    for p in playlists:
        if p['id'] == playlist_id:
            playlist = p
            break
    
    if not playlist:
        flash('Playlist not found', 'danger')
        return redirect(url_for('view_playlists'))
    
    # Check if the user is the owner of the playlist
    if playlist['user_id'] != session['user_id'] and not session.get('is_admin'):
        flash('You do not have permission to modify this playlist', 'danger')
        return redirect(url_for('view_playlists'))
    
    if request.method == 'POST':
        song_id = int(request.form['song_id'])
        
        if song_id not in playlist.get('song_ids', []):
            if 'song_ids' not in playlist:
                playlist['song_ids'] = []
            
            playlist['song_ids'].append(song_id)
            save_data(PLAYLISTS_FILE, playlists)
            flash('Song added to playlist', 'success')
        else:
            flash('Song already in playlist', 'info')
        
        return redirect(url_for('view_playlist', playlist_id=playlist_id))
    
    # Get all songs that are not already in the playlist
    available_songs = find_songs_not_in_playlist(playlist_id)
    
    return render_template('add_song_to_playlist.html', playlist=playlist, songs=available_songs)

@app.route('/playlist/<int:playlist_id>/remove_song/<int:song_id>')
def remove_song_from_playlist(playlist_id, song_id):
    if 'user_id' not in session:
        flash('Please log in to modify playlists', 'danger')
        return redirect(url_for('login'))
    
    playlists = load_data(PLAYLISTS_FILE)
    playlist = None
    
    for i, p in enumerate(playlists):
        if p['id'] == playlist_id:
            playlist = p
            playlist_idx = i
            break
    
    if not playlist:
        flash('Playlist not found', 'danger')
        return redirect(url_for('view_playlists'))
    
    # Check if the user is the owner of the playlist
    if playlist['user_id'] != session['user_id'] and not session.get('is_admin'):
        flash('You do not have permission to modify this playlist', 'danger')
        return redirect(url_for('view_playlists'))
    
    if 'song_ids' in playlist and song_id in playlist['song_ids']:
        playlist['song_ids'].remove(song_id)
        playlists[playlist_idx] = playlist
        save_data(PLAYLISTS_FILE, playlists)
        flash('Song removed from playlist', 'success')
    
    return redirect(url_for('view_playlist', playlist_id=playlist_id))

# Initialize with sample data if files are empty
def initialize_sample_data():
    artists = load_data(ARTISTS_FILE)
    albums = load_data(ALBUMS_FILE)
    songs = load_data(SONGS_FILE)
    
    # Only add sample data if all three are empty
    if not artists and not albums and not songs:
        # Add sample artists
        artists = [
            {
                'id': 1,
                'name': 'Queen',
                'genre': 'Rock',
                'bio': 'British rock band formed in 1970',
                'created_at': datetime.now().isoformat()
            },
            {
                'id': 2,
                'name': 'Michael Jackson',
                'genre': 'Pop',
                'bio': 'King of Pop',
                'created_at': datetime.now().isoformat()
            },
            {
                'id': 3,
                'name': 'The Beatles',
                'genre': 'Rock',
                'bio': 'English rock band formed in 1960',
                'created_at': datetime.now().isoformat()
            }
        ]
        save_data(ARTISTS_FILE, artists)
        
        # Add sample albums
        albums = [
            {
                'id': 1,
                'title': 'A Night at the Opera',
                'artist_id': 1,
                'genre': 'Rock',
                'release_date': '1975-11-21',
                'created_at': datetime.now().isoformat()
            },
            {
                'id': 2,
                'title': 'Thriller',
                'artist_id': 2,
                'genre': 'Pop',
                'release_date': '1982-11-30',
                'created_at': datetime.now().isoformat()
            },
            {
                'id': 3,
                'title': 'Abbey Road',
                'artist_id': 3,
                'genre': 'Rock',
                'release_date': '1969-09-26',
                'created_at': datetime.now().isoformat()
            }
        ]
        save_data(ALBUMS_FILE, albums)
        
        # Add sample songs
        songs = [
            {
                'id': 1,
                'title': 'Bohemian Rhapsody',
                'album_id': 1,
                'duration': 354,
                'genre': 'Rock',
                'file_path': None,
                'created_at': datetime.now().isoformat()
            },
            {
                'id': 2,
                'title': 'Thriller',
                'album_id': 2,
                'duration': 357,
                'genre': 'Pop',
                'file_path': None,
                'created_at': datetime.now().isoformat()
            },
            {
                'id': 3,
                'title': 'Come Together',
                'album_id': 3,
                'duration': 259,
                'genre': 'Rock',
                'file_path': None,
                'created_at': datetime.now().isoformat()
            }
        ]
        save_data(SONGS_FILE, songs)

# Initialize sample data
initialize_sample_data()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)