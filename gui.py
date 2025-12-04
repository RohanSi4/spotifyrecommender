"""
GUI application for Spotify Recommender System.
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
from spotify_token import get_spotify_client
from data_collector import DataCollector
from recommender import SpotifyRecommender


class SpotifyRecommenderGUI:
    """Main GUI application for Spotify recommendations."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Spotify Recommender System")
        self.root.geometry("900x700")
        self.root.configure(bg='#1DB954')  # Spotify green
        
        # Initialize Spotify client
        self.sp = None
        self.collector = None
        self.recommender = None
        self.user_tracks = []
        
        # Setup UI
        self.setup_ui()
        self.connect_spotify()
    
    def setup_ui(self):
        """Create and configure the UI elements."""
        # Main container
        main_frame = tk.Frame(self.root, bg='#121212', padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header = tk.Label(
            main_frame,
            text="🎵 Spotify Recommender System",
            font=('Arial', 24, 'bold'),
            bg='#121212',
            fg='#1DB954'
        )
        header.pack(pady=(0, 20))
        
        # Status label
        self.status_label = tk.Label(
            main_frame,
            text="Connecting to Spotify...",
            font=('Arial', 10),
            bg='#121212',
            fg='#FFFFFF'
        )
        self.status_label.pack(pady=(0, 20))
        
        # Notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Style the notebook
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TNotebook', background='#121212')
        style.configure('TNotebook.Tab', background='#1DB954', foreground='white', padding=[20, 10])
        style.map('TNotebook.Tab', background=[('selected', '#1DB954')])
        
        # Mood-based recommendations tab
        self.setup_mood_tab()
        
        # Song-based recommendations tab
        self.setup_song_tab()
        
        # Artist-based recommendations tab
        self.setup_artist_tab()
        
        # Results area (shared across tabs)
        self.setup_results_area(main_frame)
    
    def setup_mood_tab(self):
        """Setup mood-based recommendations tab."""
        mood_frame = tk.Frame(self.notebook, bg='#121212', padx=20, pady=20)
        self.notebook.add(mood_frame, text='🎭 Mood-Based')
        
        # Title
        title = tk.Label(
            mood_frame,
            text="Discover music based on your mood",
            font=('Arial', 14),
            bg='#121212',
            fg='#FFFFFF'
        )
        title.pack(pady=(0, 20))
        
        # Mood selection
        mood_label = tk.Label(
            mood_frame,
            text="Select your mood:",
            font=('Arial', 12),
            bg='#121212',
            fg='#FFFFFF'
        )
        mood_label.pack(pady=(0, 10))
        
        # Mood buttons frame
        mood_buttons_frame = tk.Frame(mood_frame, bg='#121212')
        mood_buttons_frame.pack(pady=10)
        
        self.moods = [
            ('😊 Happy', 'happy'),
            ('😢 Sad', 'sad'),
            ('⚡ Energetic', 'energetic'),
            ('😌 Calm', 'calm'),
            ('🧘 Relaxed', 'relaxed'),
            ('🎉 Party', 'party'),
            ('📚 Focus', 'focus'),
            ('💪 Workout', 'workout'),
            ('💕 Romantic', 'romantic')
        ]
        
        self.selected_mood = tk.StringVar(value='happy')
        
        # Create mood buttons in a grid
        for idx, (label, value) in enumerate(self.moods):
            row = idx // 3
            col = idx % 3
            
            btn = tk.Radiobutton(
                mood_buttons_frame,
                text=label,
                variable=self.selected_mood,
                value=value,
                font=('Arial', 11),
                bg='#1DB954',
                fg='white',
                selectcolor='#1ed760',
                activebackground='#1ed760',
                activeforeground='white',
                indicatoron=0,
                width=15,
                height=2,
                relief=tk.RAISED,
                bd=2
            )
            btn.grid(row=row, column=col, padx=5, pady=5, sticky='ew')
        
        # Configure grid weights
        for i in range(3):
            mood_buttons_frame.grid_columnconfigure(i, weight=1)
        
        # Options frame
        options_frame = tk.Frame(mood_frame, bg='#121212')
        options_frame.pack(pady=20, fill=tk.X)
        
        # Limit selection
        limit_label = tk.Label(
            options_frame,
            text="Number of recommendations:",
            font=('Arial', 10),
            bg='#121212',
            fg='#FFFFFF'
        )
        limit_label.pack(side=tk.LEFT, padx=10)
        
        self.mood_limit = tk.IntVar(value=20)
        limit_spinbox = tk.Spinbox(
            options_frame,
            from_=5,
            to=50,
            textvariable=self.mood_limit,
            width=10,
            font=('Arial', 10)
        )
        limit_spinbox.pack(side=tk.LEFT, padx=10)
        
        # Seed track input (optional)
        seed_label = tk.Label(
            options_frame,
            text="Seed track (optional):",
            font=('Arial', 10),
            bg='#121212',
            fg='#FFFFFF'
        )
        seed_label.pack(side=tk.LEFT, padx=10)
        
        self.mood_seed_track = tk.Entry(
            options_frame,
            width=25,
            font=('Arial', 10)
        )
        self.mood_seed_track.pack(side=tk.LEFT, padx=10)
        
        # Generate button
        generate_btn = tk.Button(
            mood_frame,
            text="Generate Recommendations",
            command=self.generate_mood_recommendations,
            font=('Arial', 12, 'bold'),
            bg='#1DB954',
            fg='white',
            activebackground='#1ed760',
            activeforeground='white',
            relief=tk.RAISED,
            bd=3,
            padx=20,
            pady=10,
            cursor='hand2'
        )
        generate_btn.pack(pady=20)
    
    def setup_song_tab(self):
        """Setup song-based recommendations tab."""
        song_frame = tk.Frame(self.notebook, bg='#121212', padx=20, pady=20)
        self.notebook.add(song_frame, text='🎵 Song-Based')
        
        # Title
        title = tk.Label(
            song_frame,
            text="Get recommendations based on your favorite songs",
            font=('Arial', 14),
            bg='#121212',
            fg='#FFFFFF'
        )
        title.pack(pady=(0, 20))
        
        # Seed tracks input
        seed_label = tk.Label(
            song_frame,
            text="Enter song names (one per line or comma-separated):",
            font=('Arial', 11),
            bg='#121212',
            fg='#FFFFFF'
        )
        seed_label.pack(pady=(0, 10))
        
        self.song_seed_text = scrolledtext.ScrolledText(
            song_frame,
            height=5,
            width=60,
            font=('Arial', 10),
            bg='#181818',
            fg='#FFFFFF',
            insertbackground='#1DB954'
        )
        self.song_seed_text.pack(pady=10)
        
        # Options frame
        options_frame = tk.Frame(song_frame, bg='#121212')
        options_frame.pack(pady=20, fill=tk.X)
        
        # Mode selection
        mode_label = tk.Label(
            options_frame,
            text="Recommendation mode:",
            font=('Arial', 10),
            bg='#121212',
            fg='#FFFFFF'
        )
        mode_label.pack(side=tk.LEFT, padx=10)
        
        self.song_mode = tk.StringVar(value='hybrid')
        mode_menu = ttk.Combobox(
            options_frame,
            textvariable=self.song_mode,
            values=['content', 'spotify', 'hybrid'],
            state='readonly',
            width=15,
            font=('Arial', 10)
        )
        mode_menu.pack(side=tk.LEFT, padx=10)
        
        # Limit
        limit_label = tk.Label(
            options_frame,
            text="Limit:",
            font=('Arial', 10),
            bg='#121212',
            fg='#FFFFFF'
        )
        limit_label.pack(side=tk.LEFT, padx=10)
        
        self.song_limit = tk.IntVar(value=20)
        limit_spinbox = tk.Spinbox(
            options_frame,
            from_=5,
            to=50,
            textvariable=self.song_limit,
            width=10,
            font=('Arial', 10)
        )
        limit_spinbox.pack(side=tk.LEFT, padx=10)
        
        # Generate button
        generate_btn = tk.Button(
            song_frame,
            text="Generate Recommendations",
            command=self.generate_song_recommendations,
            font=('Arial', 12, 'bold'),
            bg='#1DB954',
            fg='white',
            activebackground='#1ed760',
            activeforeground='white',
            relief=tk.RAISED,
            bd=3,
            padx=20,
            pady=10,
            cursor='hand2'
        )
        generate_btn.pack(pady=20)
    
    def setup_artist_tab(self):
        """Setup artist-based recommendations tab."""
        artist_frame = tk.Frame(self.notebook, bg='#121212', padx=20, pady=20)
        self.notebook.add(artist_frame, text='🎤 Artist-Based')
        
        # Title
        title = tk.Label(
            artist_frame,
            text="Discover music based on your favorite artists",
            font=('Arial', 14),
            bg='#121212',
            fg='#FFFFFF'
        )
        title.pack(pady=(0, 20))
        
        # Artist input
        artist_label = tk.Label(
            artist_frame,
            text="Enter artist name:",
            font=('Arial', 11),
            bg='#121212',
            fg='#FFFFFF'
        )
        artist_label.pack(pady=(0, 10))
        
        self.artist_name = tk.Entry(
            artist_frame,
            width=40,
            font=('Arial', 12),
            bg='#181818',
            fg='#FFFFFF',
            insertbackground='#1DB954'
        )
        self.artist_name.pack(pady=10)
        
        # Options frame
        options_frame = tk.Frame(artist_frame, bg='#121212')
        options_frame.pack(pady=20, fill=tk.X)
        
        # Mode selection
        mode_label = tk.Label(
            options_frame,
            text="Mode:",
            font=('Arial', 10),
            bg='#121212',
            fg='#FFFFFF'
        )
        mode_label.pack(side=tk.LEFT, padx=10)
        
        self.artist_mode = tk.StringVar(value='recommendations')
        mode_menu = ttk.Combobox(
            options_frame,
            textvariable=self.artist_mode,
            values=['recommendations', 'similar-artists'],
            state='readonly',
            width=20,
            font=('Arial', 10)
        )
        mode_menu.pack(side=tk.LEFT, padx=10)
        
        # Limit
        limit_label = tk.Label(
            options_frame,
            text="Limit:",
            font=('Arial', 10),
            bg='#121212',
            fg='#FFFFFF'
        )
        limit_label.pack(side=tk.LEFT, padx=10)
        
        self.artist_limit = tk.IntVar(value=20)
        limit_spinbox = tk.Spinbox(
            options_frame,
            from_=5,
            to=50,
            textvariable=self.artist_limit,
            width=10,
            font=('Arial', 10)
        )
        limit_spinbox.pack(side=tk.LEFT, padx=10)
        
        # Generate button
        generate_btn = tk.Button(
            artist_frame,
            text="Generate",
            command=self.generate_artist_recommendations,
            font=('Arial', 12, 'bold'),
            bg='#1DB954',
            fg='white',
            activebackground='#1ed760',
            activeforeground='white',
            relief=tk.RAISED,
            bd=3,
            padx=20,
            pady=10,
            cursor='hand2'
        )
        generate_btn.pack(pady=20)
    
    def setup_results_area(self, parent):
        """Setup results display area."""
        # Results frame
        results_frame = tk.Frame(parent, bg='#121212')
        results_frame.pack(fill=tk.BOTH, expand=True, pady=(20, 0))
        
        # Results label
        results_label = tk.Label(
            results_frame,
            text="Recommendations:",
            font=('Arial', 12, 'bold'),
            bg='#121212',
            fg='#1DB954'
        )
        results_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Results text area with scrollbar
        self.results_text = scrolledtext.ScrolledText(
            results_frame,
            height=15,
            width=80,
            font=('Arial', 10),
            bg='#181818',
            fg='#FFFFFF',
            insertbackground='#1DB954',
            wrap=tk.WORD
        )
        self.results_text.pack(fill=tk.BOTH, expand=True)
        
        # Create playlist button
        self.create_playlist_btn = tk.Button(
            results_frame,
            text="Create Spotify Playlist",
            command=self.create_playlist_from_results,
            font=('Arial', 11),
            bg='#1DB954',
            fg='white',
            activebackground='#1ed760',
            activeforeground='white',
            relief=tk.RAISED,
            bd=2,
            padx=15,
            pady=5,
            cursor='hand2',
            state=tk.DISABLED
        )
        self.create_playlist_btn.pack(pady=(10, 0))
        
        # Store current recommendations
        self.current_recommendations = []
    
    def connect_spotify(self):
        """Connect to Spotify in a separate thread."""
        def connect():
            try:
                self.sp = get_spotify_client()
                user = self.sp.current_user()
                self.collector = DataCollector(self.sp)
                self.recommender = SpotifyRecommender(self.sp)
                
                # Load user tracks in background
                # API limit is 50 per request, but method paginates to get all tracks
                self.user_tracks = self.collector.get_saved_tracks(limit=50)
                
                self.root.after(0, lambda: self.status_label.config(
                    text=f"✓ Connected as: {user['display_name']}",
                    fg='#1DB954'
                ))
            except Exception as e:
                self.root.after(0, lambda: self.status_label.config(
                    text=f"✗ Error: {str(e)}",
                    fg='#FF0000'
                ))
        
        threading.Thread(target=connect, daemon=True).start()
    
    def generate_mood_recommendations(self):
        """Generate mood-based recommendations."""
        if not self.recommender:
            messagebox.showerror("Error", "Not connected to Spotify yet. Please wait...")
            return
        
        mood = self.selected_mood.get()
        limit = self.mood_limit.get()
        seed_track_name = self.mood_seed_track.get().strip()
        
        self.status_label.config(text="Generating recommendations...", fg='#FFFFFF')
        self.results_text.delete(1.0, tk.END)
        self.create_playlist_btn.config(state=tk.DISABLED)
        
        def generate():
            try:
                seed_tracks = None
                if seed_track_name:
                    # Search for seed track
                    results = self.sp.search(q=seed_track_name, type='track', limit=1)
                    if results['tracks']['items']:
                        seed_tracks = [results['tracks']['items'][0]['id']]
                
                recommendations = self.recommender.mood_based_recommendations(
                    mood=mood,
                    seed_tracks=seed_tracks,
                    limit=limit
                )
                
                self.current_recommendations = recommendations
                
                # Display results
                self.root.after(0, lambda: self.display_results(
                    recommendations,
                    f"Mood-Based Recommendations ({mood.capitalize()})"
                ))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
                self.root.after(0, lambda: self.status_label.config(
                    text="Ready",
                    fg='#1DB954'
                ))
        
        threading.Thread(target=generate, daemon=True).start()
    
    def generate_song_recommendations(self):
        """Generate song-based recommendations."""
        if not self.recommender:
            messagebox.showerror("Error", "Not connected to Spotify yet. Please wait...")
            return
        
        seed_text = self.song_seed_text.get(1.0, tk.END).strip()
        if not seed_text:
            messagebox.showerror("Error", "Please enter at least one song name")
            return
        
        # Parse seed tracks
        seed_tracks = []
        for line in seed_text.replace(',', '\n').split('\n'):
            line = line.strip()
            if line:
                seed_tracks.append(line)
        
        mode = self.song_mode.get()
        limit = self.song_limit.get()
        
        self.status_label.config(text="Generating recommendations...", fg='#FFFFFF')
        self.results_text.delete(1.0, tk.END)
        self.create_playlist_btn.config(state=tk.DISABLED)
        
        def generate():
            try:
                # Find seed tracks in user's library or search
                found_seeds = []
                for seed_name in seed_tracks[:5]:
                    # Try to find in user's library first
                    found = False
                    for track in self.user_tracks:
                        if seed_name.lower() in track['name'].lower():
                            found_seeds.append(track)
                            found = True
                            break
                    
                    # If not found, search Spotify
                    if not found:
                        results = self.sp.search(q=seed_name, type='track', limit=1)
                        if results['tracks']['items']:
                            track = results['tracks']['items'][0]
                            found_seeds.append({
                                'id': track['id'],
                                'name': track['name'],
                                'artists': [a['name'] for a in track['artists']],
                                'uri': track['uri']
                            })
                
                if not found_seeds:
                    raise ValueError("Could not find any of the seed tracks")
                
                # Generate recommendations based on mode
                if mode == 'content':
                    recommendations = self.recommender.content_based_recommendations(
                        seed_tracks=found_seeds,
                        user_tracks=self.user_tracks,
                        num_recommendations=limit
                    )
                elif mode == 'spotify':
                    seed_ids = [t['id'] for t in found_seeds]
                    recommendations = self.recommender.get_spotify_recommendations(
                        seed_tracks=seed_ids,
                        limit=limit
                    )
                else:  # hybrid
                    recommendations = self.recommender.hybrid_recommendations(
                        seed_tracks=found_seeds,
                        user_tracks=self.user_tracks,
                        num_recommendations=limit
                    )
                
                self.current_recommendations = recommendations
                
                self.root.after(0, lambda: self.display_results(
                    recommendations,
                    f"Song-Based Recommendations ({mode.capitalize()})"
                ))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
                self.root.after(0, lambda: self.status_label.config(
                    text="Ready",
                    fg='#1DB954'
                ))
        
        threading.Thread(target=generate, daemon=True).start()
    
    def generate_artist_recommendations(self):
        """Generate artist-based recommendations."""
        if not self.recommender:
            messagebox.showerror("Error", "Not connected to Spotify yet. Please wait...")
            return
        
        artist_name = self.artist_name.get().strip()
        if not artist_name:
            messagebox.showerror("Error", "Please enter an artist name")
            return
        
        mode = self.artist_mode.get()
        limit = self.artist_limit.get()
        
        self.status_label.config(text="Generating recommendations...", fg='#FFFFFF')
        self.results_text.delete(1.0, tk.END)
        self.create_playlist_btn.config(state=tk.DISABLED)
        
        def generate():
            try:
                if mode == 'recommendations':
                    recommendations = self.recommender.get_artist_recommendations(
                        artist_name=artist_name,
                        limit=limit
                    )
                    self.current_recommendations = recommendations
                    self.root.after(0, lambda: self.display_results(
                        recommendations,
                        f"Recommendations based on {artist_name}"
                    ))
                else:  # similar-artists
                    similar = self.recommender.discover_similar_artists(
                        artist_name=artist_name,
                        limit=limit
                    )
                    self.current_recommendations = []
                    self.root.after(0, lambda: self.display_artists(
                        similar,
                        f"Artists similar to {artist_name}"
                    ))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
                self.root.after(0, lambda: self.status_label.config(
                    text="Ready",
                    fg='#1DB954'
                ))
        
        threading.Thread(target=generate, daemon=True).start()
    
    def display_results(self, recommendations, title):
        """Display recommendations in the results area."""
        self.results_text.delete(1.0, tk.END)
        
        self.results_text.insert(tk.END, f"{title}\n", 'title')
        self.results_text.insert(tk.END, "=" * 60 + "\n\n")
        
        if not recommendations:
            self.results_text.insert(tk.END, "No recommendations found.\n")
            self.status_label.config(text="Ready", fg='#1DB954')
            return
        
        for idx, track in enumerate(recommendations, 1):
            artists = ", ".join(track.get('artists', []))
            self.results_text.insert(tk.END, f"{idx}. {track.get('name', 'Unknown')}\n")
            self.results_text.insert(tk.END, f"   {artists}\n\n")
        
        self.results_text.tag_config('title', font=('Arial', 12, 'bold'), foreground='#1DB954')
        
        self.create_playlist_btn.config(state=tk.NORMAL)
        self.status_label.config(text="Ready", fg='#1DB954')
    
    def display_artists(self, artists, title):
        """Display similar artists."""
        self.results_text.delete(1.0, tk.END)
        
        self.results_text.insert(tk.END, f"{title}\n", 'title')
        self.results_text.insert(tk.END, "=" * 60 + "\n\n")
        
        if not artists:
            self.results_text.insert(tk.END, "No similar artists found.\n")
            self.status_label.config(text="Ready", fg='#1DB954')
            return
        
        for idx, artist in enumerate(artists, 1):
            genres = ", ".join(artist.get('genres', [])[:3])
            self.results_text.insert(tk.END, f"{idx}. {artist['name']}\n")
            if genres:
                self.results_text.insert(tk.END, f"   Genres: {genres}\n")
            self.results_text.insert(tk.END, f"   Popularity: {artist.get('popularity', 0)}\n\n")
        
        self.results_text.tag_config('title', font=('Arial', 12, 'bold'), foreground='#1DB954')
        self.status_label.config(text="Ready", fg='#1DB954')
    
    def create_playlist_from_results(self):
        """Create a Spotify playlist from current recommendations."""
        if not self.current_recommendations:
            messagebox.showerror("Error", "No recommendations to add to playlist")
            return
        
        # Ask for playlist name
        from tkinter import simpledialog
        playlist_name = simpledialog.askstring(
            "Playlist Name",
            "Enter playlist name:",
            initialvalue="Recommended Tracks"
        )
        
        if not playlist_name:
            return
        
        self.status_label.config(text="Creating playlist...", fg='#FFFFFF')
        
        def create():
            try:
                user_id = self.sp.current_user()["id"]
                playlist = self.sp.user_playlist_create(
                    user_id,
                    playlist_name,
                    public=False,
                    description="Generated by Spotify Recommender System"
                )
                
                track_uris = [track['uri'] for track in self.current_recommendations if track.get('uri')]
                
                # Add tracks in batches
                for i in range(0, len(track_uris), 100):
                    batch = track_uris[i:i+100]
                    self.sp.playlist_add_items(playlist['id'], batch)
                
                self.root.after(0, lambda: messagebox.showinfo(
                    "Success",
                    f"Playlist '{playlist_name}' created successfully!\n\n"
                    f"Spotify URL: {playlist['external_urls']['spotify']}"
                ))
                self.root.after(0, lambda: self.status_label.config(
                    text="Ready",
                    fg='#1DB954'
                ))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
                self.root.after(0, lambda: self.status_label.config(
                    text="Ready",
                    fg='#1DB954'
                ))
        
        threading.Thread(target=create, daemon=True).start()


def main():
    """Launch the GUI application."""
    root = tk.Tk()
    app = SpotifyRecommenderGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

