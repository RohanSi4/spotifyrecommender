"""
Data collection module for gathering user listening history and track features.
"""
from spotipy import Spotify
import time
from typing import List, Dict, Any


class DataCollector:
    """Collects user listening data and track audio features from Spotify."""
    
    def __init__(self, spotify_client: Spotify):
        self.sp = spotify_client
        self.user_id = spotify_client.current_user()["id"]
    
    def get_saved_tracks(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user's saved tracks (liked songs).
        
        Note: Spotify API has a maximum limit of 50 per request.
        This method will paginate to fetch all tracks if needed.
        """
        # Cap limit at 50 (Spotify API maximum)
        request_limit = min(limit, 50)
        tracks = []
        results = self.sp.current_user_saved_tracks(limit=request_limit)
        
        while results:
            for item in results['items']:
                track = item['track']
                tracks.append({
                    'id': track['id'],
                    'name': track['name'],
                    'artists': [artist['name'] for artist in track['artists']],
                    'album': track['album']['name'],
                    'uri': track['uri']
                })
            
            if results['next']:
                results = self.sp.next(results)
            else:
                break
        
        return tracks
    
    def get_playlist_tracks(self, playlist_id: str) -> List[Dict[str, Any]]:
        """Get all tracks from a specific playlist."""
        tracks = []
        results = self.sp.playlist_tracks(playlist_id)
        
        while results:
            for item in results['items']:
                if item['track'] and item['track']['id']:
                    track = item['track']
                    tracks.append({
                        'id': track['id'],
                        'name': track['name'],
                        'artists': [artist['name'] for artist in track['artists']],
                        'album': track['album']['name'],
                        'uri': track['uri']
                    })
            
            if results['next']:
                results = self.sp.next(results)
            else:
                break
        
        return tracks
    
    def get_user_playlists(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get user's playlists."""
        playlists = []
        results = self.sp.current_user_playlists(limit=limit)
        
        while results:
            for playlist in results['items']:
                playlists.append({
                    'id': playlist['id'],
                    'name': playlist['name'],
                    'tracks_count': playlist['tracks']['total']
                })
            
            if results['next']:
                results = self.sp.next(results)
            else:
                break
        
        return playlists
    
    def get_recently_played(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user's recently played tracks."""
        tracks = []
        results = self.sp.current_user_recently_played(limit=limit)
        
        for item in results['items']:
            track = item['track']
            tracks.append({
                'id': track['id'],
                'name': track['name'],
                'artists': [artist['name'] for artist in track['artists']],
                'album': track['album']['name'],
                'uri': track['uri'],
                'played_at': item['played_at']
            })
        
        return tracks
    
    def get_track_audio_features(self, track_ids: List[str]) -> Dict[str, Any]:
        """Get audio features for multiple tracks (max 100 at a time)."""
        all_features = {}
        
        # Spotify API allows max 100 tracks per request
        for i in range(0, len(track_ids), 100):
            batch = track_ids[i:i+100]
            features = self.sp.audio_features(batch)
            
            for idx, feature in enumerate(features):
                if feature:
                    all_features[batch[idx]] = feature
            
            # Rate limiting - be nice to the API
            time.sleep(0.1)
        
        return all_features
    
    def collect_user_data(self, include_playlists: bool = True, 
                          include_recent: bool = True,
                          saved_tracks_limit: int = 100) -> Dict[str, Any]:
        """Collect comprehensive user listening data."""
        print("Collecting your listening data...")
        
        data = {
            'saved_tracks': self.get_saved_tracks(limit=saved_tracks_limit),
            'playlists': [],
            'recent_tracks': []
        }
        
        if include_playlists:
            print("Fetching playlists...")
            playlists = self.get_user_playlists(limit=20)
            data['playlists'] = playlists
            
            # Optionally get tracks from playlists
            # Uncomment if you want to include playlist tracks
            # for playlist in playlists[:5]:  # Limit to first 5 playlists
            #     tracks = self.get_playlist_tracks(playlist['id'])
            #     data['playlist_tracks'].extend(tracks)
        
        if include_recent:
            print("Fetching recently played tracks...")
            data['recent_tracks'] = self.get_recently_played(limit=50)
        
        # Get all unique track IDs
        all_track_ids = set()
        for track in data['saved_tracks']:
            all_track_ids.add(track['id'])
        for track in data['recent_tracks']:
            all_track_ids.add(track['id'])
        
        # Get audio features for all tracks
        print(f"Fetching audio features for {len(all_track_ids)} tracks...")
        track_ids_list = list(all_track_ids)
        audio_features = self.get_track_audio_features(track_ids_list)
        
        # Attach features to tracks
        for track in data['saved_tracks']:
            if track['id'] in audio_features:
                track['features'] = audio_features[track['id']]
        
        for track in data['recent_tracks']:
            if track['id'] in audio_features:
                track['features'] = audio_features[track['id']]
        
        print(f"Collected {len(data['saved_tracks'])} saved tracks")
        print(f"Collected {len(data['recent_tracks'])} recently played tracks")
        print(f"Found {len(data['playlists'])} playlists")
        
        return data

