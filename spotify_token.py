"""
Spotify authentication module.
"""
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def get_spotify_client() -> Spotify:
    """
    Initialize and return a Spotify client with authentication.
    
    Returns:
        Authenticated Spotify client
    """
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI")
    
    if not all([client_id, client_secret, redirect_uri]):
        raise ValueError(
            "Missing required environment variables. "
            "Please set SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, and SPOTIFY_REDIRECT_URI"
        )
    
    # Expanded scope for full functionality
    scope = (
        "playlist-read-private "
        "playlist-read-collaborative "
        "playlist-modify-public "
        "playlist-modify-private "
        "user-library-read "
        "user-read-recently-played "
        "user-top-read"
    )
    
    sp = Spotify(
        auth_manager=SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope=scope,
            cache_path=".spotify_cache"
        )
    )
    
    return sp


if __name__ == "__main__":
    # Test authentication
    sp = get_spotify_client()
    user = sp.current_user()
    print(f"✓ Authenticated as: {user['display_name']}")
    
    # Test call
    playlists = sp.current_user_playlists(limit=5)
    print(f"\nYour Playlists:")
    for pl in playlists["items"]:
        print(f"  - {pl['name']} ({pl['tracks']['total']} tracks)")
