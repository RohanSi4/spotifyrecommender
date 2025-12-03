from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
import os

print(os.getenv("SPOTIFY_CLIENT_ID"))

sp = Spotify(
    auth_manager=SpotifyOAuth(
        client_id=os.getenv("SPOTIFY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
        redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI"),
        scope="playlist-read-private user-library-read"
    )
)

print("Authenticated as:", sp.current_user()["display_name"])

# Test call
playlists = sp.current_user_playlists(limit=5)
for pl in playlists["items"]:
    print(pl["name"], pl["tracks"]["total"])
