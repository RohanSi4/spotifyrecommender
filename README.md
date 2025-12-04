# Spotify Recommender System

A comprehensive recommendation system for Spotify that uses multiple algorithms to suggest music based on your listening history and preferences.

## Features

- **🎭 Mood-Based Recommendations**: Discover music based on your current mood (Happy, Sad, Energetic, Calm, Relaxed, Party, Focus, Workout, Romantic)
- **Content-Based Recommendations**: Uses audio features to find similar tracks
- **Spotify API Recommendations**: Leverages Spotify's built-in recommendation engine
- **Hybrid Approach**: Combines content-based and Spotify recommendations
- **Artist-Based Recommendations**: Discover music based on your favorite artists
- **Similar Artists Discovery**: Find artists similar to ones you like
- **🎨 Beautiful GUI**: Easy-to-use graphical interface with Spotify-themed design
- **Playlist Creation**: Automatically create playlists with recommendations

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up Spotify API credentials:**
   - Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
   - Create a new app
   - Get your Client ID and Client Secret
   - **Important**: Set redirect URI to `http://127.0.0.1:8888/callback` (Spotify doesn't allow `localhost`)

3. **Create `.env` file:**
   ```
   SPOTIFY_CLIENT_ID=your_client_id
   SPOTIFY_CLIENT_SECRET=your_client_secret
   SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/callback
   ```

4. **First-time authentication:**
   - Run `python spotify_token.py` to test authentication
   - You'll be redirected to authorize the app
   - After authorization, a cache file will be created

## Usage

### 🎨 GUI Application (Recommended)

Launch the web-based graphical interface:
```bash
streamlit run gui_streamlit.py
```

The GUI will open in your browser automatically. It provides three modes:
- **🎭 Mood-Based**: Select a mood and get personalized recommendations
- **🎵 Song-Based**: Enter your favorite songs and get similar tracks
- **🎤 Artist-Based**: Discover music based on artists you love

Features:
- Real-time recommendation generation
- One-click playlist creation
- Beautiful Spotify-themed interface
- Multiple recommendation algorithms
- Web-based (works on any device)

### 📝 Command Line Interface

### Mood-Based Recommendations (NEW!)
Get recommendations based on your mood:
```bash
python main.py --mode mood --mood happy --limit 20
```

Available moods: `happy`, `sad`, `energetic`, `calm`, `relaxed`, `party`, `focus`, `workout`, `romantic`

### View Your Listening Data
```bash
python main.py --collect-data
```

### Content-Based Recommendations
Find tracks similar to specific songs in your library:
```bash
python main.py --mode content --seed-tracks "Song Name 1" "Song Name 2" --limit 20
```

### Spotify API Recommendations
Use Spotify's recommendation engine:
```bash
python main.py --mode spotify --seed-tracks "Song Name" --limit 20
```

### Hybrid Recommendations (Recommended)
Combine both approaches:
```bash
python main.py --mode hybrid --seed-tracks "Song Name 1" "Song Name 2" --limit 20
```

### Artist-Based Recommendations
Get recommendations based on an artist:
```bash
python main.py --mode artist --seed-artist "Artist Name" --limit 20
```

### Discover Similar Artists
Find artists similar to your favorites:
```bash
python main.py --mode similar-artists --seed-artist "Artist Name" --limit 10
```

### Create a Playlist
Add `--create-playlist` to any recommendation command:
```bash
python main.py --mode hybrid --seed-tracks "Song Name" --create-playlist --playlist-name "My Recommendations"
```

## Examples

```bash
# Get 30 hybrid recommendations based on two songs and create a playlist
python main.py --mode hybrid --seed-tracks "Bohemian Rhapsody" "Stairway to Heaven" --limit 30 --create-playlist --playlist-name "Classic Rock Mix"

# Discover artists similar to The Beatles
python main.py --mode similar-artists --seed-artist "The Beatles" --limit 15

# Get Spotify recommendations for a song
python main.py --mode spotify --seed-tracks "Blinding Lights" --limit 20
```

## Project Structure

- `spotify_token.py`: Authentication and Spotify client setup
- `data_collector.py`: Collects user listening history and track features
- `recommender.py`: Core recommendation algorithms (including mood-based)
- `main.py`: Main application with CLI interface
- `gui_streamlit.py`: Web-based graphical user interface (Streamlit)
- `gui.py`: Desktop GUI application (tkinter - requires system dependencies)

## How It Works

1. **Data Collection**: Gathers your saved tracks, playlists, and recently played songs
2. **Feature Extraction**: Gets audio features (danceability, energy, tempo, etc.) for tracks
3. **Mood Mapping**: Maps moods to target audio features (e.g., Happy = high valence & energy)
4. **Similarity Calculation**: Uses cosine similarity or Euclidean distance to find similar tracks
5. **Recommendation Generation**: Combines multiple approaches for best results
6. **Playlist Creation**: Optionally creates a Spotify playlist with recommendations

### Mood-Based Recommendations

The mood-based system uses Spotify's audio features to match tracks to your selected mood:
- **Happy**: High valence, energy, and danceability
- **Sad**: Low valence and energy
- **Energetic**: High energy and tempo
- **Calm/Relaxed**: Low energy, high acousticness
- **Party**: High danceability, energy, and tempo
- **Focus**: Low energy, low speechiness
- **Workout**: Very high energy and tempo
- **Romantic**: Moderate energy, high valence

## Notes

- The first run will require browser authentication
- Subsequent runs use cached credentials
- Rate limiting is handled automatically
- Recommendations are based on audio features and Spotify's algorithms

