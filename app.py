import os
import time
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy.orm import DeclarativeBase, relationship

# Create base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "your-secret-key-for-music-player")

# Configure database connection
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL:
    # Use PostgreSQL in production
    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
else:
    # Use SQLite in development
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///music_player.db"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Configure upload folder for song files
UPLOAD_FOLDER = 'uploads/songs'
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'ogg', 'flac', 'm4a'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Make sure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize SQLAlchemy
db = SQLAlchemy(model_class=Base)
db.init_app(app)

# Define models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Artist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    genre = db.Column(db.String(50))
    bio = db.Column(db.Text)
    
    def __repr__(self):
        return f'<Artist {self.name}>'

class Album(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'), nullable=False)
    release_date = db.Column(db.Date)
    genre = db.Column(db.String(50))
    
    # Define relationship to Artist
    artist = db.relationship('Artist', backref=db.backref('albums', lazy=True))
    
    def __repr__(self):
        return f'<Album {self.title}>'

class Song(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    album_id = db.Column(db.Integer, db.ForeignKey('album.id'), nullable=False)
    duration = db.Column(db.Integer)  # Duration in seconds
    file_path = db.Column(db.String(255))
    genre = db.Column(db.String(50))
    
    # Define relationship to Album
    album = db.relationship('Album', backref=db.backref('songs', lazy=True))
    
    def __repr__(self):
        return f'<Song {self.title}>'

class Playlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Define relationship to User
    user = db.relationship('User', backref=db.backref('playlists', lazy=True))
    
    # Define many-to-many relationship with Song
    songs = db.relationship('Song', secondary='playlist_song', backref=db.backref('playlists', lazy=True))
    
    def __repr__(self):
        return f'<Playlist {self.title}>'

# Association table for Playlist and Song (many-to-many)
playlist_song = db.Table('playlist_song',
    db.Column('playlist_id', db.Integer, db.ForeignKey('playlist.id'), primary_key=True),
    db.Column('song_id', db.Integer, db.ForeignKey('song.id'), primary_key=True)
)

# Helper functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def format_duration(seconds):
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes}:{seconds:02d}"

# Routes
@app.route('/')
def index():
    songs = Song.query.all()
    return render_template('index.html', songs=songs, format_duration=format_duration)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['is_admin'] = user.is_admin
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
        
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('Username or email already exists', 'danger')
            return render_template('register.html')
        
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed_password)
        
        # Make the first user an admin
        if User.query.count() == 0:
            new_user.is_admin = True
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

# Admin Routes
@app.route('/admin')
def admin():
    if not session.get('is_admin'):
        flash('Admin access required', 'danger')
        return redirect(url_for('index'))
    
    artists = Artist.query.all()
    albums = Album.query.all()
    songs = Song.query.all()
    
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
        
        new_artist = Artist(name=name, genre=genre, bio=bio)
        db.session.add(new_artist)
        db.session.commit()
        
        flash('Artist added successfully', 'success')
        return redirect(url_for('admin'))
    
    return render_template('add_artist.html')

@app.route('/admin/album/add', methods=['GET', 'POST'])
def add_album():
    if not session.get('is_admin'):
        flash('Admin access required', 'danger')
        return redirect(url_for('index'))
    
    artists = Artist.query.all()
    
    if request.method == 'POST':
        title = request.form['title']
        artist_id = request.form['artist_id']
        release_date = datetime.strptime(request.form['release_date'], '%Y-%m-%d').date()
        genre = request.form['genre']
        
        new_album = Album(title=title, artist_id=artist_id, release_date=release_date, genre=genre)
        db.session.add(new_album)
        db.session.commit()
        
        flash('Album added successfully', 'success')
        return redirect(url_for('admin'))
    
    return render_template('add_album.html', artists=artists)

@app.route('/admin/song/add', methods=['GET', 'POST'])
def add_song():
    if not session.get('is_admin'):
        flash('Admin access required', 'danger')
        return redirect(url_for('index'))
    
    albums = Album.query.all()
    
    if request.method == 'POST':
        title = request.form['title']
        album_id = request.form['album_id']
        duration = int(request.form['duration'])
        genre = request.form['genre']
        
        # Handle file upload
        file_path = None
        if 'song_file' in request.files:
            file = request.files['song_file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Add timestamp to filename to make it unique
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                unique_filename = f"{timestamp}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(file_path)
        
        new_song = Song(title=title, album_id=album_id, duration=duration, file_path=file_path, genre=genre)
        db.session.add(new_song)
        db.session.commit()
        
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
        
        new_playlist = Playlist(title=title, user_id=session['user_id'])
        db.session.add(new_playlist)
        db.session.commit()
        
        flash('Playlist created successfully', 'success')
        return redirect(url_for('view_playlists'))
    
    return render_template('create_playlist.html')

@app.route('/playlists')
def view_playlists():
    if 'user_id' not in session:
        flash('Please log in to view your playlists', 'danger')
        return redirect(url_for('login'))
    
    playlists = Playlist.query.filter_by(user_id=session['user_id']).all()
    return render_template('playlists.html', playlists=playlists)

@app.route('/playlist/<int:playlist_id>')
def view_playlist(playlist_id):
    playlist = Playlist.query.get_or_404(playlist_id)
    
    # Check if the user is the owner of the playlist
    if playlist.user_id != session.get('user_id') and not session.get('is_admin'):
        flash('You do not have permission to view this playlist', 'danger')
        return redirect(url_for('view_playlists'))
    
    return render_template('playlist.html', playlist=playlist, format_duration=format_duration)

@app.route('/playlist/<int:playlist_id>/add_song', methods=['GET', 'POST'])
def add_song_to_playlist(playlist_id):
    if 'user_id' not in session:
        flash('Please log in to add songs to a playlist', 'danger')
        return redirect(url_for('login'))
    
    playlist = Playlist.query.get_or_404(playlist_id)
    
    # Check if the user is the owner of the playlist
    if playlist.user_id != session['user_id'] and not session.get('is_admin'):
        flash('You do not have permission to modify this playlist', 'danger')
        return redirect(url_for('view_playlists'))
    
    if request.method == 'POST':
        song_id = request.form['song_id']
        song = Song.query.get_or_404(song_id)
        
        if song not in playlist.songs:
            playlist.songs.append(song)
            db.session.commit()
            flash('Song added to playlist', 'success')
        else:
            flash('Song already in playlist', 'info')
        
        return redirect(url_for('view_playlist', playlist_id=playlist_id))
    
    # Get all songs that are not already in the playlist
    songs = Song.query.filter(~Song.id.in_([song.id for song in playlist.songs])).all()
    return render_template('add_song_to_playlist.html', playlist=playlist, songs=songs)

@app.route('/playlist/<int:playlist_id>/remove_song/<int:song_id>')
def remove_song_from_playlist(playlist_id, song_id):
    if 'user_id' not in session:
        flash('Please log in to modify playlists', 'danger')
        return redirect(url_for('login'))
    
    playlist = Playlist.query.get_or_404(playlist_id)
    
    # Check if the user is the owner of the playlist
    if playlist.user_id != session['user_id'] and not session.get('is_admin'):
        flash('You do not have permission to modify this playlist', 'danger')
        return redirect(url_for('view_playlists'))
    
    song = Song.query.get_or_404(song_id)
    
    if song in playlist.songs:
        playlist.songs.remove(song)
        db.session.commit()
        flash('Song removed from playlist', 'success')
    
    return redirect(url_for('view_playlist', playlist_id=playlist_id))

# Create database initialization function
def create_tables():
    with app.app_context():
        db.create_all()
        
        # Check if admin user exists, if not, create one
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                email='admin@example.com',
                password=generate_password_hash('admin'),
                is_admin=True
            )
            db.session.add(admin_user)
            
            # Add sample data
            artist1 = Artist(name='Queen', genre='Rock', bio='British rock band formed in 1970')
            artist2 = Artist(name='Michael Jackson', genre='Pop', bio='King of Pop')
            artist3 = Artist(name='The Beatles', genre='Rock', bio='English rock band formed in 1960')
            
            db.session.add_all([artist1, artist2, artist3])
            db.session.commit()
            
            album1 = Album(title='A Night at the Opera', artist_id=artist1.id, release_date=datetime.strptime('1975-11-21', '%Y-%m-%d').date(), genre='Rock')
            album2 = Album(title='Thriller', artist_id=artist2.id, release_date=datetime.strptime('1982-11-30', '%Y-%m-%d').date(), genre='Pop')
            album3 = Album(title='Abbey Road', artist_id=artist3.id, release_date=datetime.strptime('1969-09-26', '%Y-%m-%d').date(), genre='Rock')
            
            db.session.add_all([album1, album2, album3])
            db.session.commit()
            
            song1 = Song(title='Bohemian Rhapsody', album_id=album1.id, duration=354, genre='Rock')
            song2 = Song(title='Thriller', album_id=album2.id, duration=357, genre='Pop')
            song3 = Song(title='Come Together', album_id=album3.id, duration=259, genre='Rock')
            
            db.session.add_all([song1, song2, song3])
            db.session.commit()

# Initialize the database
create_tables()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)