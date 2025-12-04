"""
Streamlit web GUI for Spotify Recommender System.
"""
import streamlit as st
import time
from spotify_token import get_spotify_client
from data_collector import DataCollector
from recommender import SpotifyRecommender
from stats_analyzer import MusicStatsAnalyzer
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

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
                st.session_state.stats_analyzer = MusicStatsAnalyzer(sp)
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
            ["📊 Your Stats", "🎭 Mood-Based", "🎵 Song-Based", "🎤 Artist-Based"],
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
    if page == "📊 Your Stats":
        stats_page()
    elif page == "🎭 Mood-Based":
        mood_based_page()
    elif page == "🎵 Song-Based":
        song_based_page()
    elif page == "🎤 Artist-Based":
        artist_based_page()

def stats_page():
    """Display comprehensive music statistics."""
    st.header("📊 Your Music Statistics")
    
    user_tracks = st.session_state.user_tracks
    
    # Show if stats are already available
    if 'music_stats' in st.session_state and st.session_state.music_stats:
        tracks_analyzed = st.session_state.music_stats.get('tracks_analyzed', 0)
        if tracks_analyzed > 0:
            st.success(f"✅ Statistics available for {tracks_analyzed} tracks!")
    
    if not user_tracks:
        st.warning("No tracks found. Please make sure you have saved tracks in your Spotify library.")
        return
    
    # Get analyzer (already initialized in main)
    analyzer = st.session_state.get('stats_analyzer')
    if not analyzer:
        st.error("Stats analyzer not initialized. Please refresh the page.")
        return
    
    # Options for analysis
    st.markdown("### Analysis Options")
    col1, col2 = st.columns(2)
    with col1:
        analyze_all = st.checkbox("Analyze all tracks", value=False, 
                                  help="If unchecked, analyzes first 100 tracks (faster)")
    with col2:
        if len(user_tracks) > 100:
            st.info(f"📊 You have {len(user_tracks)} tracks. Analyzing all may take several minutes.")
    
    # Analyze button
    if st.button("🔄 Analyze My Music", type="primary", use_container_width=True):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            status_text.text("Starting analysis...")
            progress_bar.progress(10)
            
            # Use sample if not analyzing all
            tracks_to_analyze = user_tracks if analyze_all else user_tracks[:100]
            if not analyze_all:
                status_text.text(f"Analyzing sample of {len(tracks_to_analyze)} tracks...")
            else:
                status_text.text(f"Analyzing all {len(tracks_to_analyze)} tracks (this may take several minutes)...")
            
            progress_bar.progress(20)
            stats = analyzer.analyze_tracks(tracks_to_analyze)
            progress_bar.progress(90)
            
            status_text.text("Finalizing statistics...")
            # Store stats even if empty
            st.session_state.music_stats = stats
            progress_bar.progress(100)
            
            # Show success message before rerun
            status_text.success(f"✅ Analysis complete! Analyzed {stats.get('tracks_analyzed', 0)} tracks.")
            
            # Small delay to show message
            time.sleep(1)
            
            # Clear progress elements
            progress_bar.empty()
            status_text.empty()
            
            # Force rerun to show stats
            st.rerun()
        except Exception as e:
            st.error(f"Error during analysis: {str(e)}")
            st.exception(e)  # Show full error for debugging
            st.info("💡 Tip: Some tracks might not be accessible. The analysis will continue with available tracks.")
            # Try to show partial stats if available
            if 'music_stats' in st.session_state:
                st.warning("Showing partial results from previous analysis.")
    
    # Display stats if available (check if key exists, even if empty)
    if 'music_stats' in st.session_state:
        stats = st.session_state.music_stats
        
        # Debug: Show what we have
        with st.expander("🔍 Debug Info", expanded=False):
            st.write(f"Stats type: {type(stats)}")
            st.write(f"Stats keys: {list(stats.keys()) if isinstance(stats, dict) else 'N/A'}")
            st.write(f"Tracks analyzed: {stats.get('tracks_analyzed', 'N/A') if isinstance(stats, dict) else 'N/A'}")
            st.json(stats)
        
        # Check if stats is valid
        if not stats or not isinstance(stats, dict):
            st.warning("Analysis completed but no statistics were generated. Please try again.")
            return
        
        # Check if we have any meaningful data
        tracks_analyzed = stats.get('tracks_analyzed', 0)
        total_tracks = stats.get('total_tracks', 0)
        features_fetched = stats.get('features_fetched', 0)
        
        # Show warning if audio features failed but still show basic stats
        if tracks_analyzed == 0 and total_tracks > 0:
            st.warning("⚠️ Audio features could not be fetched, but showing basic statistics.")
            st.info(f"📊 Found {total_tracks} tracks, but couldn't analyze audio features. This might be due to API rate limiting.")
            
            # Still show basic stats even without audio features
            st.markdown("---")
            
            # Overview metrics
            st.subheader("📈 Overview")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Tracks", f"{total_tracks:,}")
            with col2:
                st.metric("Unique Artists", f"{stats.get('artists', {}).get('total_unique', 0):,}")
            with col3:
                st.metric("Genres", f"{stats.get('genres', {}).get('total_unique', 0):,}")
            with col4:
                pop = stats.get('popularity', {})
                if pop and pop.get('mean'):
                    st.metric("Avg Popularity", f"{pop.get('mean', 0):.0f}/100")
            
            # Top Artists
            if stats.get('artists') and stats['artists'].get('top_artists'):
                st.markdown("---")
                st.subheader("🎤 Top Artists")
                artists = stats.get('artists', {})
                top_artists = artists['top_artists'][:10]
                
                # Create bar chart
                artist_df = pd.DataFrame(top_artists, columns=['Artist', 'Tracks'])
                fig = go.Figure(data=go.Bar(
                    x=artist_df['Tracks'],
                    y=artist_df['Artist'],
                    orientation='h',
                    marker_color='#1DB954',
                    text=artist_df['Tracks'],
                    textposition='outside'
                ))
                fig.update_layout(
                    title="Top 10 Artists by Track Count",
                    xaxis_title="Number of Tracks",
                    yaxis_title="Artist",
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='white'),
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Top Genres
            if stats.get('genres') and stats['genres'].get('top_genres'):
                st.markdown("---")
                st.subheader("🎼 Top Genres")
                genres = stats.get('genres', {})
                top_genres = genres['top_genres'][:10]
                
                genre_df = pd.DataFrame(top_genres, columns=['Genre', 'Count'])
                fig = go.Figure(data=go.Bar(
                    x=genre_df['Count'],
                    y=genre_df['Genre'],
                    orientation='h',
                    marker_color='#1DB954',
                    text=genre_df['Count'],
                    textposition='outside'
                ))
                fig.update_layout(
                    title="Top 10 Genres",
                    xaxis_title="Number of Tracks",
                    yaxis_title="Genre",
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='white'),
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Popularity Stats
            if stats.get('popularity'):
                st.markdown("---")
                st.subheader("📊 Track Popularity")
                pop = stats.get('popularity', {})
                if pop.get('mean') is not None:
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Average", f"{pop.get('mean', 0):.0f}/100")
                    with col2:
                        st.metric("Median", f"{pop.get('median', 0):.0f}/100")
                    with col3:
                        st.metric("Highest", f"{pop.get('max', 0):.0f}/100")
                    with col4:
                        st.metric("Lowest", f"{pop.get('min', 0):.0f}/100")
            
            st.info("💡 **Note:** Audio features (danceability, energy, mood) require additional API permissions. Your basic statistics are still available!")
            return
        
        if tracks_analyzed == 0:
            st.warning("⚠️ No tracks were successfully analyzed. This might be due to:")
            st.markdown("- API rate limiting")
            st.markdown("- Track access permissions")
            st.markdown("- Invalid track IDs")
            st.markdown("\n**Try:** Analyzing a smaller sample or check your Spotify connection.")
            return
        
        # Overview metrics
        st.markdown("---")
        st.subheader("📈 Overview")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Tracks", f"{stats.get('total_tracks', 0):,}")
        with col2:
            st.metric("Tracks Analyzed", f"{stats.get('tracks_analyzed', 0):,}")
        with col3:
            artists = stats.get('artists', {})
            st.metric("Unique Artists", f"{artists.get('total_unique', 0):,}")
        with col4:
            genres = stats.get('genres', {})
            st.metric("Genres", f"{genres.get('total_unique', 0):,}")
        
        # Audio Features
        st.markdown("---")
        st.subheader("🎵 Audio Features")
        
        audio_features = stats.get('audio_features', {})
        if audio_features:
            # Create feature comparison chart
            feature_names = ['danceability', 'energy', 'valence', 'acousticness']
            feature_means = [audio_features.get(f, {}).get('mean', 0) * 100 for f in feature_names]
            
            fig = go.Figure(data=go.Bar(
                x=feature_names,
                y=feature_means,
                marker_color='#1DB954',
                text=[f"{v:.1f}%" for v in feature_means],
                textposition='outside'
            ))
            fig.update_layout(
                title="Average Audio Features (0-100%)",
                xaxis_title="Feature",
                yaxis_title="Value (%)",
                yaxis_range=[0, 100],
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Feature details in columns
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 🎶 Musical Characteristics")
                if 'danceability' in audio_features:
                    d = audio_features['danceability']
                    st.metric("Danceability", f"{d['mean']*100:.1f}%", 
                             f"Range: {d['min']*100:.0f}% - {d['max']*100:.0f}%")
                if 'energy' in audio_features:
                    e = audio_features['energy']
                    st.metric("Energy", f"{e['mean']*100:.1f}%",
                             f"Range: {e['min']*100:.0f}% - {e['max']*100:.0f}%")
                if 'valence' in audio_features:
                    v = audio_features['valence']
                    st.metric("Positivity (Valence)", f"{v['mean']*100:.1f}%",
                             f"Range: {v['min']*100:.0f}% - {v['max']*100:.0f}%")
            
            with col2:
                st.markdown("#### 🎼 Sound Characteristics")
                if 'acousticness' in audio_features:
                    a = audio_features['acousticness']
                    st.metric("Acousticness", f"{a['mean']*100:.1f}%",
                             f"Range: {a['min']*100:.0f}% - {a['max']*100:.0f}%")
                if 'instrumentalness' in audio_features:
                    i = audio_features['instrumentalness']
                    st.metric("Instrumentalness", f"{i['mean']*100:.1f}%",
                             f"Range: {i['min']*100:.0f}% - {i['max']*100:.0f}%")
                if 'tempo' in audio_features:
                    t = audio_features['tempo']
                    st.metric("Average Tempo", f"{t['mean']:.0f} BPM",
                             f"Range: {t['min']:.0f} - {t['max']:.0f} BPM")
        
        # Mood Distribution
        st.markdown("---")
        st.subheader("🎭 Mood Distribution")
        moods = stats.get('mood_distribution', {})
        if moods:
            mood_df = pd.DataFrame(list(moods.items()), columns=['Mood', 'Count'])
            mood_df = mood_df[mood_df['Count'] > 0]  # Only show moods with tracks
            
            if not mood_df.empty:
                fig = px.pie(
                    mood_df, 
                    values='Count', 
                    names='Mood',
                    color_discrete_sequence=['#1DB954', '#1ed760', '#b3b3b3', '#535353', '#121212', '#ffffff'],
                    hole=0.4
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='white'),
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Top Artists
        st.markdown("---")
        st.subheader("🎤 Top Artists")
        artists = stats.get('artists', {})
        if artists and artists.get('top_artists'):
            top_artists = artists['top_artists'][:10]
            artist_df = pd.DataFrame(top_artists, columns=['Artist', 'Tracks'])
            
            fig = go.Figure(data=go.Bar(
                x=artist_df['Tracks'],
                y=artist_df['Artist'],
                orientation='h',
                marker_color='#1DB954',
                text=artist_df['Tracks'],
                textposition='outside'
            ))
            fig.update_layout(
                title="Top 10 Artists by Track Count",
                xaxis_title="Number of Tracks",
                yaxis_title="Artist",
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Energy & Danceability Distribution
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("⚡ Energy Levels")
            energy_levels = stats.get('energy_levels', {})
            if energy_levels:
                energy_df = pd.DataFrame(list(energy_levels.items()), columns=['Level', 'Count'])
                fig = px.bar(
                    energy_df,
                    x='Level',
                    y='Count',
                    color='Level',
                    color_discrete_map={'Low': '#1DB954', 'Medium': '#1ed760', 'High': '#b3b3b3'},
                    text='Count'
                )
                fig.update_traces(textposition='outside')
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='white'),
                    showlegend=False,
                    height=300
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("💃 Danceability Levels")
            dance_levels = stats.get('danceability_levels', {})
            if dance_levels:
                dance_df = pd.DataFrame(list(dance_levels.items()), columns=['Level', 'Count'])
                fig = px.bar(
                    dance_df,
                    x='Level',
                    y='Count',
                    color='Level',
                    color_discrete_map={'Low': '#1DB954', 'Medium': '#1ed760', 'High': '#b3b3b3'},
                    text='Count'
                )
                fig.update_traces(textposition='outside')
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='white'),
                    showlegend=False,
                    height=300
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Top Genres
        genres = stats.get('genres', {})
        if genres and genres.get('top_genres'):
            st.markdown("---")
            st.subheader("🎼 Top Genres")
            top_genres = genres['top_genres'][:10]
            genre_df = pd.DataFrame(top_genres, columns=['Genre', 'Count'])
            
            fig = go.Figure(data=go.Bar(
                x=genre_df['Count'],
                y=genre_df['Genre'],
                orientation='h',
                marker_color='#1DB954',
                text=genre_df['Count'],
                textposition='outside'
            ))
            fig.update_layout(
                title="Top 10 Genres",
                xaxis_title="Number of Tracks",
                yaxis_title="Genre",
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Popularity
        popularity = stats.get('popularity', {})
        if popularity:
            st.markdown("---")
            st.subheader("📊 Track Popularity")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Average", f"{popularity.get('mean', 0):.0f}/100")
            with col2:
                st.metric("Median", f"{popularity.get('median', 0):.0f}/100")
            with col3:
                st.metric("Highest", f"{popularity.get('max', 0):.0f}/100")
            with col4:
                st.metric("Lowest", f"{popularity.get('min', 0):.0f}/100")

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
            user_tracks = st.session_state.user_tracks
            
            seed_tracks = None
            if seed_track.strip():
                # User provided a seed track - search for it
                try:
                    results = sp.search(q=seed_track, type='track', limit=1)
                    if results['tracks']['items']:
                        seed_tracks = [results['tracks']['items'][0]['id']]
                    else:
                        st.warning(f"Could not find '{seed_track}' on Spotify. Using mood-based genres instead.")
                except Exception as e:
                    st.warning(f"Error searching for track: {str(e)}. Using mood-based genres instead.")
            
            # If no seed track, mood_based_recommendations will use genres automatically
            recommendations = recommender.mood_based_recommendations(
                mood=mood,
                seed_tracks=seed_tracks,
                limit=limit
            )
            
            display_recommendations(recommendations, f"{mood.capitalize()} Mood Recommendations")
            
        except ValueError as e:
            st.error(f"Error: {str(e)}")
            st.info("💡 Tip: Make sure you have valid seed tracks or try a different mood.")
            # Debug section
            with st.expander("🔍 Debug Info", expanded=True):
                st.write(f"**Error Type:** ValueError")
                st.write(f"**Error Message:** {str(e)}")
                st.write(f"**Mood:** {mood}")
                st.write(f"**Seed Track Provided:** {bool(seed_track.strip())}")
                st.write(f"**Seed Tracks:** {seed_tracks}")
        except Exception as e:
            error_msg = str(e)
            error_type = type(e).__name__
            
            st.error("❌ Could not generate recommendations")
            
            # Debug section
            with st.expander("🔍 Debug Info", expanded=True):
                st.write(f"**Error Type:** {error_type}")
                st.write(f"**Error Message:** {error_msg}")
                st.write(f"**Mood:** {mood}")
                st.write(f"**Seed Track Input:** '{seed_track}'")
                st.write(f"**Seed Track Provided:** {bool(seed_track.strip())}")
                st.write(f"**Seed Tracks IDs:** {seed_tracks}")
                st.write(f"**User Tracks Available:** {len(user_tracks) if user_tracks else 0}")
                
                # Show full traceback
                import traceback
                st.write("**Full Traceback:**")
                st.code(traceback.format_exc())
            
            if "404" in error_msg or "Invalid" in error_msg:
                st.info("**Possible causes:**")
                st.markdown("- Invalid or unavailable seed tracks")
                st.markdown("- Spotify API limitations")
                st.markdown("- Try using different songs or clearing the seed track field")
            else:
                st.info(f"**Unexpected error:** {error_msg}")

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
            not_found = []
            
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
                    try:
                        results = sp.search(q=seed_name, type='track', limit=1)
                        if results['tracks']['items']:
                            track = results['tracks']['items'][0]
                            found_seeds.append({
                                'id': track['id'],
                                'name': track['name'],
                                'artists': [a['name'] for a in track['artists']],
                                'uri': track['uri']
                            })
                            found = True
                    except:
                        pass
                
                if not found:
                    not_found.append(seed_name)
            
            if not found_seeds:
                st.error(f"Could not find any of the seed tracks: {', '.join(not_found) if not_found else 'all tracks'}")
                st.info("💡 Tip: Try using exact song names or check spelling.")
                return
            
            if not_found:
                st.warning(f"Could not find: {', '.join(not_found)}. Using found tracks: {len(found_seeds)}")
            
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
            # Debug section
            with st.expander("🔍 Debug Info", expanded=True):
                st.write(f"**Error Type:** ValueError")
                st.write(f"**Error Message:** {str(e)}")
                st.write(f"**Mode:** {mode}")
                st.write(f"**Seed Text:** {seed_text[:200]}...")
                st.write(f"**Found Seeds:** {len(found_seeds)}")
                st.write(f"**Seed IDs:** {[s.get('id') for s in found_seeds]}")
        except Exception as e:
            error_msg = str(e)
            error_type = type(e).__name__
            
            st.error("❌ Could not generate recommendations")
            
            # Debug section
            with st.expander("🔍 Debug Info", expanded=True):
                st.write(f"**Error Type:** {error_type}")
                st.write(f"**Error Message:** {error_msg}")
                st.write(f"**Mode:** {mode}")
                st.write(f"**Seed Text:** {seed_text[:200]}...")
                st.write(f"**Found Seeds Count:** {len(found_seeds)}")
                st.write(f"**Found Seed IDs:** {[s.get('id') for s in found_seeds]}")
                st.write(f"**Not Found:** {not_found if 'not_found' in locals() else 'N/A'}")
                
                # Show full traceback
                import traceback
                st.write("**Full Traceback:**")
                st.code(traceback.format_exc())
            
            if "404" in error_msg or "Invalid" in error_msg:
                st.info("**Possible causes:**")
                st.markdown("- Invalid or unavailable seed tracks")
                st.markdown("- Spotify API limitations")
                st.markdown("- Try using different songs or check spelling")
            else:
                st.info(f"**Unexpected error:** {error_msg}")

def generate_artist_recommendations(artist_name, mode, limit):
    """Generate artist-based recommendations."""
    with st.spinner("Generating recommendations..."):
        try:
            recommender = st.session_state.recommender
            sp = st.session_state.spotify_client
            
            # First verify artist exists
            try:
                results = sp.search(q=f'artist:{artist_name}', type='artist', limit=1)
                if not results['artists']['items']:
                    st.error(f"Could not find artist '{artist_name}' on Spotify.")
                    st.info("💡 Tip: Try using the exact artist name or check spelling.")
                    return
            except Exception as e:
                st.error(f"Error searching for artist: {str(e)}")
                return
            
            if mode == 'recommendations':
                recommendations = recommender.get_artist_recommendations(
                    artist_name=artist_name,
                    limit=limit
                )
                if not recommendations:
                    st.warning(f"Could not generate recommendations for {artist_name}. Try a different artist.")
                    return
                display_recommendations(recommendations, f"Recommendations based on {artist_name}")
            else:  # similar-artists
                similar = recommender.discover_similar_artists(
                    artist_name=artist_name,
                    limit=limit
                )
                if not similar:
                    st.warning(f"Could not find similar artists for {artist_name}. Try a different artist.")
                    return
                display_artists(similar, f"Artists similar to {artist_name}")
                
        except ValueError as e:
            st.error(f"Error: {str(e)}")
            st.info("💡 Tip: Make sure you entered a valid artist name that exists on Spotify.")
            # Debug section
            with st.expander("🔍 Debug Info", expanded=True):
                st.write(f"**Error Type:** ValueError")
                st.write(f"**Error Message:** {str(e)}")
                st.write(f"**Mode:** {mode}")
                st.write(f"**Artist Name:** {artist_name}")
        except Exception as e:
            error_msg = str(e)
            error_type = type(e).__name__
            
            st.error("❌ Could not generate recommendations")
            
            # Debug section
            with st.expander("🔍 Debug Info", expanded=True):
                st.write(f"**Error Type:** {error_type}")
                st.write(f"**Error Message:** {error_msg}")
                st.write(f"**Mode:** {mode}")
                st.write(f"**Artist Name:** {artist_name}")
                
                # Show full traceback
                import traceback
                st.write("**Full Traceback:**")
                st.code(traceback.format_exc())
            
            if "404" in error_msg or "Invalid" in error_msg:
                st.info("**Possible causes:**")
                st.markdown("- Check the artist name spelling")
                st.markdown("- Try a different artist")
            else:
                st.info(f"**Unexpected error:** {error_msg}")

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

