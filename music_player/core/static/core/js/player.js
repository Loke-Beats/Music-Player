/**
 * Music Player JavaScript
 * Handles the music player functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // UI Elements
    const playPauseBtn = document.getElementById('playPauseBtn');
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const songProgress = document.getElementById('songProgress');
    const currentTimeEl = document.getElementById('currentTime');
    const totalTimeEl = document.getElementById('totalTime');
    const volumeControl = document.getElementById('volumeControl');
    const currentSongTitle = document.getElementById('currentSongTitle');
    const currentSongArtist = document.getElementById('currentSongArtist');
    
    // Player State
    const playerState = {
        playing: false,
        currentSongIndex: 0,
        queue: [],
        audioElement: new Audio()
    };
    
    // Initialize event listeners for player controls
    function initializePlayer() {
        // Play/Pause button
        playPauseBtn.addEventListener('click', togglePlayPause);
        
        // Previous button
        prevBtn.addEventListener('click', playPrevious);
        
        // Next button
        nextBtn.addEventListener('click', playNext);
        
        // Volume control
        volumeControl.addEventListener('input', function() {
            playerState.audioElement.volume = this.value / 100;
        });
        
        // Audio element events
        playerState.audioElement.addEventListener('timeupdate', updateProgress);
        playerState.audioElement.addEventListener('ended', playNext);
        playerState.audioElement.addEventListener('loadedmetadata', updateTotalTime);
        
        // Set initial volume
        playerState.audioElement.volume = volumeControl.value / 100;
        
        // Listen for play song clicks
        document.querySelectorAll('.play-song').forEach(function(button) {
            button.addEventListener('click', function() {
                const songId = this.dataset.songId;
                const songTitle = this.dataset.songTitle;
                const songArtist = this.dataset.songArtist;
                
                playSong({
                    id: songId,
                    title: songTitle,
                    artist: songArtist
                });
            });
        });
        
        // Listen for queue playing (from album/playlist)
        document.addEventListener('playQueue', function(e) {
            playerState.queue = e.detail;
            playerState.currentSongIndex = 0;
            
            if (playerState.queue.length > 0) {
                const currentSong = playerState.queue[playerState.currentSongIndex];
                loadSong(currentSong);
                playerState.audioElement.play()
                    .then(() => {
                        playerState.playing = true;
                        updatePlayPauseIcon();
                    })
                    .catch(error => {
                        console.error('Error playing song:', error);
                    });
            }
        });
    }
    
    // Toggle play/pause
    function togglePlayPause() {
        if (playerState.queue.length === 0) {
            // Nothing to play
            return;
        }
        
        if (playerState.playing) {
            playerState.audioElement.pause();
            playerState.playing = false;
        } else {
            playerState.audioElement.play()
                .then(() => {
                    playerState.playing = true;
                })
                .catch(error => {
                    console.error('Error playing song:', error);
                });
        }
        
        updatePlayPauseIcon();
    }
    
    // Update play/pause button icon
    function updatePlayPauseIcon() {
        if (playerState.playing) {
            playPauseBtn.innerHTML = '<i class="fas fa-pause"></i>';
        } else {
            playPauseBtn.innerHTML = '<i class="fas fa-play"></i>';
        }
    }
    
    // Play previous song
    function playPrevious() {
        if (playerState.queue.length === 0) return;
        
        // If current song is playing for more than 3 seconds, restart it
        if (playerState.audioElement.currentTime > 3) {
            playerState.audioElement.currentTime = 0;
            return;
        }
        
        playerState.currentSongIndex--;
        if (playerState.currentSongIndex < 0) {
            playerState.currentSongIndex = playerState.queue.length - 1;
        }
        
        loadSong(playerState.queue[playerState.currentSongIndex]);
        
        if (playerState.playing) {
            playerState.audioElement.play()
                .catch(error => {
                    console.error('Error playing song:', error);
                });
        }
    }
    
    // Play next song
    function playNext() {
        if (playerState.queue.length === 0) return;
        
        playerState.currentSongIndex++;
        if (playerState.currentSongIndex >= playerState.queue.length) {
            playerState.currentSongIndex = 0;
        }
        
        loadSong(playerState.queue[playerState.currentSongIndex]);
        
        if (playerState.playing) {
            playerState.audioElement.play()
                .catch(error => {
                    console.error('Error playing song:', error);
                });
        }
    }
    
    // Update progress bar and time display
    function updateProgress() {
        const { currentTime, duration } = playerState.audioElement;
        
        // Update progress bar
        const progressPercent = (currentTime / duration) * 100;
        songProgress.style.width = `${progressPercent}%`;
        
        // Update current time display
        const minutes = Math.floor(currentTime / 60);
        const seconds = Math.floor(currentTime % 60);
        currentTimeEl.textContent = `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
    }
    
    // Update total time display
    function updateTotalTime() {
        const { duration } = playerState.audioElement;
        
        if (isNaN(duration)) return;
        
        const minutes = Math.floor(duration / 60);
        const seconds = Math.floor(duration % 60);
        totalTimeEl.textContent = `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
    }
    
    // Load a song into the audio element
    function loadSong(song) {
        // For demo purposes, we'll use a generated tone since we can't actually load real mp3 files
        // In a real implementation, this would load the song URL from the server
        
        // Update UI
        currentSongTitle.textContent = song.title;
        currentSongArtist.textContent = song.artist;
        
        // Generate a simple tone based on the song ID
        const frequency = 220 + (parseInt(song.id) % 10) * 50; // Generate different pitches for different songs
        
        // Create an oscillator to generate a tone
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.type = 'sine';
        oscillator.frequency.value = frequency;
        gainNode.gain.value = 0.1;
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        oscillator.start();
        
        // Record the audio for 2 seconds
        const destination = audioContext.createMediaStreamDestination();
        gainNode.connect(destination);
        
        const mediaRecorder = new MediaRecorder(destination.stream);
        const chunks = [];
        
        mediaRecorder.ondataavailable = function(evt) {
            chunks.push(evt.data);
        };
        
        mediaRecorder.onstop = function() {
            const blob = new Blob(chunks, { type: 'audio/ogg; codecs=opus' });
            const url = URL.createObjectURL(blob);
            playerState.audioElement.src = url;
            
            // Clean up
            oscillator.stop();
            audioContext.close();
        };
        
        mediaRecorder.start();
        setTimeout(() => {
            mediaRecorder.stop();
        }, 2000);
    }
    
    // Play a specific song (called when clicking play button on a song)
    function playSong(song) {
        // Add the song to the queue and make it the current song
        playerState.queue = [song];
        playerState.currentSongIndex = 0;
        
        loadSong(song);
        
        playerState.audioElement.play()
            .then(() => {
                playerState.playing = true;
                updatePlayPauseIcon();
            })
            .catch(error => {
                console.error('Error playing song:', error);
            });
    }
    
    // Initialize the player
    initializePlayer();
});