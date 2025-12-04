"""
Streamlit web GUI for Spotify Recommender System.
"""
import streamlit as st
import time
from spotify_token import get_spotify_client
from data_collector import DataCollector
from recommender import SpotifyRecommender

# Page configuration
st.set_page_config(
    page_title="Spotify Recommender System",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Spotify theme
st.markdown("""
    <style>
    .main {
        background-color: #121212;
    }
    .stApp {
        background-color: #121212;
    }
    h1 {
        color: #1DB954;
    }
    h2, h3 {
        color: #FFFFFF;
    }
    .stButton>button {
        background-color: #1DB954;
        color: white;
        border-radius: 20px;
        border: none;
        padding: 0.5rem 2rem;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #1ed760;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'spotify_client' not in st.session_state:
    st.session_state.spotify_client = None
    st.session_state.collector = None
    st.session_state.recommender = None
    st.session_state.user_tracks = []
    st.session_state.initialized = False

# Initialize Spotify connection
@st.cache_resource
def init_spotify():
    """Initialize Spotify client."""
    try:
        sp = get_spotify_client()
        collector = DataCollector(sp)
        recommender = SpotifyRecommender(sp)
        user = sp.current_user()
        return sp, collector, recommender, user
    except Exception as e:
        st.error(f"Error connecting to Spotify: {str(e)}")
        return None, None, None, None

# Main app
def main():
    st.title("🎵 Spotify Recommender System")
    
    # Initialize Spotify
    if not st.session_state.initialized:
        with st.spinner("Connecting to Spotify..."):
            sp, collector, recommender, user = init_spotify()
            if sp:
                st.session_state.spotify_client = sp
                st.session_state.collector = collector
                st.session_state.recommender = recommender
                st.session_state.initialized = True
                
                # Load user tracks in background
                with st.spinner("Loading your saved tracks..."):
                    # Note: API limit is 50 per request, but method paginates to get all tracks
                    st.session_state.user_tracks = collector.get_saved_tracks(limit=50)
                
                st.success(f"✓ Connected as: **{user['display_name']}**")
            else:
                st.error("Failed to connect to Spotify. Please check your credentials.")
                return
    
    # Sidebar
    with st.sidebar:
        st.header("🎛️ Navigation")
        page = st.radio(
            "Choose a mode:",
            ["🎭 Mood-Based", "🎵 Song-Based", "🎤 Artist-Based"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        st.markdown("### Your Stats")
        st.metric("Saved Tracks", len(st.session_state.user_tracks))
        if st.session_state.spotify_client:
            try:
                playlists = st.session_state.spotify_client.current_user_playlists(limit=1)
                st.metric("Total Playlists", playlists.get('total', 0))
            except:
                pass
    
    # Main content based on selected page
    if page == "🎭 Mood-Based":
        mood_based_page()
    elif page == "🎵 Song-Based":
        song_based_page()
    elif page == "🎤 Artist-Based":
        artist_based_page()

def mood_based_page():
    st.header("🎭 Mood-Based Recommendations")
    st.markdown("Discover music that matches your current mood!")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Mood selection
        st.subheader("Select Your Mood")
        mood_options = {
            "😊 Happy": "happy",
            "😢 Sad": "sad",
            "⚡ Energetic": "energetic",
            "😌 Calm": "calm",
            "🧘 Relaxed": "relaxed",
            "🎉 Party": "party",
            "📚 Focus": "focus",
            "💪 Workout": "workout",
            "💕 Romantic": "romantic"
        }
        
        selected_mood_label = st.selectbox(
            "Choose a mood:",
            options=list(mood_options.keys()),
            index=0
        )
        selected_mood = mood_options[selected_mood_label]
        
        # Optional seed track
        seed_track = st.text_input(
            "Seed track (optional):",
            placeholder="Enter a song name to influence recommendations"
        )
        
        # Limit
        limit = st.slider("Number of recommendations:", 5, 50, 20)
        
        if st.button("🎵 Generate Recommendations", use_container_width=True):
            generate_mood_recommendations(selected_mood, seed_track, limit)
    
    with col2:
        st.markdown("### 💡 Mood Info")
        mood_descriptions = {
            "happy": "High energy, positive vibes, danceable",
            "sad": "Low energy, melancholic, emotional",
            "energetic": "High tempo, powerful, motivating",
            "calm": "Peaceful, low energy, soothing",
            "relaxed": "Acoustic, gentle, tranquil",
            "party": "Danceable, high energy, upbeat",
            "focus": "Instrumental, low distraction, steady",
            "workout": "Very high energy, fast tempo, intense",
            "romantic": "Emotional, moderate tempo, intimate"
        }
        st.info(mood_descriptions.get(selected_mood, ""))

def song_based_page():
    st.header("🎵 Song-Based Recommendations")
    st.markdown("Get recommendations based on your favorite songs!")
    
    # Seed tracks input
    seed_text = st.text_area(
        "Enter song names (one per line or comma-separated):",
        height=150,
        placeholder="Enter your favorite songs here...\nExample:\nBohemian Rhapsody\nStairway to Heaven"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        mode = st.selectbox(
            "Recommendation mode:",
            ["hybrid", "content", "spotify"],
            help="Hybrid combines both approaches for best results"
        )
    
    with col2:
        limit = st.slider("Number of recommendations:", 5, 50, 20)
    
    if st.button("🎵 Generate Recommendations", use_container_width=True):
        if not seed_text.strip():
            st.error("Please enter at least one song name")
        else:
            generate_song_recommendations(seed_text, mode, limit)

def artist_based_page():
    st.header("🎤 Artist-Based Recommendations")
    st.markdown("Discover music based on your favorite artists!")
    
    artist_name = st.text_input(
        "Enter artist name:",
        placeholder="e.g., The Beatles, Taylor Swift, etc."
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        mode = st.selectbox(
            "Mode:",
            ["recommendations", "similar-artists"]
        )
    
    with col2:
        limit = st.slider("Number of results:", 5, 50, 20)
    
    if st.button("🎵 Generate", use_container_width=True):
        if not artist_name.strip():
            st.error("Please enter an artist name")
        else:
            generate_artist_recommendations(artist_name, mode, limit)

def generate_mood_recommendations(mood, seed_track, limit):
    """Generate mood-based recommendations."""
    with st.spinner(f"Generating {mood} mood recommendations..."):
        try:
            recommender = st.session_state.recommender
            sp = st.session_state.spotify_client
            
            seed_tracks = None
            if seed_track.strip():
                results = sp.search(q=seed_track, type='track', limit=1)
                if results['tracks']['items']:
                    seed_tracks = [results['tracks']['items'][0]['id']]
            
            recommendations = recommender.mood_based_recommendations(
                mood=mood,
                seed_tracks=seed_tracks,
                limit=limit
            )
            
            display_recommendations(recommendations, f"{mood.capitalize()} Mood Recommendations")
            
        except ValueError as e:
            st.error(f"Error: {str(e)}")
            st.info("💡 Tip: Make sure you have valid seed tracks or try a different mood.")
        except Exception as e:
            error_msg = str(e)
            if "404" in error_msg or "Invalid" in error_msg:
                st.error("❌ Could not generate recommendations. This might be due to:")
                st.markdown("- Invalid or unavailable seed tracks")
                st.markdown("- Spotify API limitations")
                st.markdown("- Try using different songs or clearing the seed track field")
            else:
                st.error(f"Error generating recommendations: {error_msg}")

def generate_song_recommendations(seed_text, mode, limit):
    """Generate song-based recommendations."""
    with st.spinner("Generating recommendations..."):
        try:
            # Parse seed tracks
            seed_tracks = []
            for line in seed_text.replace(',', '\n').split('\n'):
                line = line.strip()
                if line:
                    seed_tracks.append(line)
            
            recommender = st.session_state.recommender
            sp = st.session_state.spotify_client
            user_tracks = st.session_state.user_tracks
            
            # Find seed tracks
            found_seeds = []
            for seed_name in seed_tracks[:5]:
                # Try user's library first
                found = False
                for track in user_tracks:
                    if seed_name.lower() in track['name'].lower():
                        found_seeds.append(track)
                        found = True
                        break
                
                # Search Spotify if not found
                if not found:
                    results = sp.search(q=seed_name, type='track', limit=1)
                    if results['tracks']['items']:
                        track = results['tracks']['items'][0]
                        found_seeds.append({
                            'id': track['id'],
                            'name': track['name'],
                            'artists': [a['name'] for a in track['artists']],
                            'uri': track['uri']
                        })
            
            if not found_seeds:
                st.error("Could not find any of the seed tracks")
                return
            
            # Generate recommendations
            if mode == 'content':
                recommendations = recommender.content_based_recommendations(
                    seed_tracks=found_seeds,
                    user_tracks=user_tracks,
                    num_recommendations=limit
                )
            elif mode == 'spotify':
                seed_ids = [t['id'] for t in found_seeds]
                recommendations = recommender.get_spotify_recommendations(
                    seed_tracks=seed_ids,
                    limit=limit
                )
            else:  # hybrid
                recommendations = recommender.hybrid_recommendations(
                    seed_tracks=found_seeds,
                    user_tracks=user_tracks,
                    num_recommendations=limit
                )
            
            display_recommendations(recommendations, f"{mode.capitalize()} Recommendations")
            
        except ValueError as e:
            st.error(f"Error: {str(e)}")
            st.info("💡 Tip: Make sure you entered valid song names that exist on Spotify.")
        except Exception as e:
            error_msg = str(e)
            if "404" in error_msg or "Invalid" in error_msg:
                st.error("❌ Could not generate recommendations. This might be due to:")
                st.markdown("- Invalid or unavailable seed tracks")
                st.markdown("- Spotify API limitations")
                st.markdown("- Try using different songs or check spelling")
            else:
                st.error(f"Error generating recommendations: {error_msg}")

def generate_artist_recommendations(artist_name, mode, limit):
    """Generate artist-based recommendations."""
    with st.spinner("Generating recommendations..."):
        try:
            recommender = st.session_state.recommender
            
            if mode == 'recommendations':
                recommendations = recommender.get_artist_recommendations(
                    artist_name=artist_name,
                    limit=limit
                )
                display_recommendations(recommendations, f"Recommendations based on {artist_name}")
            else:  # similar-artists
                similar = recommender.discover_similar_artists(
                    artist_name=artist_name,
                    limit=limit
                )
                display_artists(similar, f"Artists similar to {artist_name}")
                
        except ValueError as e:
            st.error(f"Error: {str(e)}")
            st.info("💡 Tip: Make sure you entered a valid artist name that exists on Spotify.")
        except Exception as e:
            error_msg = str(e)
            if "404" in error_msg or "Invalid" in error_msg:
                st.error("❌ Could not find artist or generate recommendations.")
                st.markdown("- Check the artist name spelling")
                st.markdown("- Try a different artist")
            else:
                st.error(f"Error generating recommendations: {error_msg}")

def display_recommendations(recommendations, title):
    """Display recommendations in a nice format."""
    st.markdown("---")
    st.subheader(title)
    
    if not recommendations:
        st.warning("No recommendations found.")
        return
    
    # Create playlist button
    if st.button("📝 Create Spotify Playlist", key="create_playlist"):
        create_playlist(recommendations, title)
    
    # Display tracks
    st.markdown(f"**Found {len(recommendations)} tracks:**")
    
    for idx, track in enumerate(recommendations, 1):
        artists = ", ".join(track.get('artists', []))
        with st.container():
            col1, col2 = st.columns([1, 4])
            with col1:
                st.markdown(f"**{idx}.**")
            with col2:
                st.markdown(f"**{track.get('name', 'Unknown')}**")
                st.caption(f"by {artists}")
        st.divider()

def display_artists(artists, title):
    """Display similar artists."""
    st.markdown("---")
    st.subheader(title)
    
    if not artists:
        st.warning("No similar artists found.")
        return
    
    for idx, artist in enumerate(artists, 1):
        genres = ", ".join(artist.get('genres', [])[:3])
        with st.container():
            st.markdown(f"**{idx}. {artist['name']}**")
            if genres:
                st.caption(f"Genres: {genres}")
            st.caption(f"Popularity: {artist.get('popularity', 0)}/100")
        st.divider()

def create_playlist(recommendations, default_name):
    """Create a Spotify playlist from recommendations."""
    with st.spinner("Creating playlist..."):
        try:
            sp = st.session_state.spotify_client
            user_id = sp.current_user()["id"]
            
            playlist = sp.user_playlist_create(
                user_id,
                default_name,
                public=False,
                description="Generated by Spotify Recommender System"
            )
            
            track_uris = [track['uri'] for track in recommendations if track.get('uri')]
            
            # Add tracks in batches
            for i in range(0, len(track_uris), 100):
                batch = track_uris[i:i+100]
                sp.playlist_add_items(playlist['id'], batch)
            
            st.success(f"✓ Playlist '{default_name}' created successfully!")
            st.markdown(f"[Open in Spotify]({playlist['external_urls']['spotify']})")
            
        except Exception as e:
            st.error(f"Error creating playlist: {str(e)}")

if __name__ == "__main__":
    main()

