"""
Statistics analyzer for user's Spotify music library.
"""
from spotipy import Spotify
import numpy as np
from typing import Dict, Any, List
from collections import Counter
import time


class MusicStatsAnalyzer:
    """Analyzes user's music library and provides statistics."""
    
    def __init__(self, spotify_client: Spotify):
        self.sp = spotify_client
    
    def analyze_tracks(self, tracks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze a list of tracks and return comprehensive statistics.
        
        Args:
            tracks: List of track dictionaries with 'id' and optionally 'features'
        
        Returns:
            Dictionary containing various statistics
        """
        if not tracks:
            return {}
        
        # Get audio features for tracks that don't have them
        # Filter out None/empty IDs and validate format
        track_ids = []
        for track in tracks:
            track_id = track.get('id')
            if track_id and isinstance(track_id, str) and len(track_id) > 0:
                track_ids.append(track_id)
        
        all_features = {}
        
        # Get features in smaller batches to avoid 403 errors
        # Use smaller batches and add better error handling
        batch_size = 50  # Reduced from 100 to be safer
        for i in range(0, len(track_ids), batch_size):
            batch = track_ids[i:i+batch_size]
            if not batch:
                continue
            
            try:
                # Filter out any None values
                batch = [tid for tid in batch if tid]
                if not batch:
                    continue
                
                features = self.sp.audio_features(batch)
                if features:
                    for idx, feature in enumerate(features):
                        if idx < len(batch) and feature and isinstance(feature, dict):
                            track_id = batch[idx]
                            # Validate feature has required fields
                            if feature.get('id') or feature.get('danceability') is not None:
                                all_features[track_id] = feature
                time.sleep(0.5)  # More conservative rate limiting
            except Exception as e:
                # If batch fails, try smaller batches or skip
                error_msg = str(e)
                # Log first error for debugging
                if len(all_features) == 0 and i == 0:
                    print(f"First batch error: {error_msg}")
                
                if '403' in error_msg or 'Forbidden' in error_msg:
                    # 403 means we're being rate limited or don't have permission
                    # Try even smaller batches, but limit attempts
                    if len(batch) > 5:
                        # Try even smaller batches
                        for j in range(0, len(batch), 5):  # Even smaller - 5 at a time
                            small_batch = batch[j:j+5]
                            try:
                                features = self.sp.audio_features(small_batch)
                                if features:
                                    for idx, feature in enumerate(features):
                                        if idx < len(small_batch) and feature and isinstance(feature, dict):
                                            track_id = small_batch[idx]
                                            if feature.get('id') or feature.get('danceability') is not None:
                                                all_features[track_id] = feature
                                time.sleep(0.3)
                            except:
                                continue
                    # If even small batches fail, skip this batch entirely
                else:
                    # For other errors, just skip this batch
                    continue
        
        # Collect all features
        features_list = []
        for track in tracks:
            track_id = track.get('id')
            if track_id in all_features:
                features_list.append(all_features[track_id])
            elif track.get('features'):
                features_list.append(track['features'])
        
        # Always return basic stats, even if audio features failed
        stats = {
            'total_tracks': len(tracks),
            'tracks_analyzed': len(features_list),
            'tracks_with_ids': len([t for t in tracks if t.get('id')]),
            'features_fetched': len(all_features),
            'artists': self._analyze_artists(tracks),
        }
        
        # Only add audio feature stats if we have features
        if features_list:
            stats['audio_features'] = self._analyze_audio_features(features_list)
            stats['mood_distribution'] = self._analyze_moods(features_list)
            stats['energy_levels'] = self._categorize_energy(features_list)
            stats['danceability_levels'] = self._categorize_danceability(features_list)
        else:
            stats['audio_features'] = {}
            stats['mood_distribution'] = {}
            stats['energy_levels'] = {}
            stats['danceability_levels'] = {}
        
        # Try to get genres and popularity (these might also fail)
        try:
            stats['genres'] = self._analyze_genres(tracks)
        except Exception as e:
            stats['genres'] = {'total_unique': 0, 'top_genres': []}
        
        try:
            stats['popularity'] = self._analyze_popularity(tracks)
        except Exception as e:
            stats['popularity'] = {}
        
        return stats
    
    def _analyze_audio_features(self, features_list: List[Dict]) -> Dict[str, Any]:
        """Analyze audio features and return statistics."""
        feature_names = [
            'danceability', 'energy', 'valence', 'acousticness',
            'instrumentalness', 'liveness', 'speechiness', 'tempo'
        ]
        
        stats = {}
        for feature in feature_names:
            values = [f.get(feature, 0) for f in features_list if f and f.get(feature) is not None]
            if values:
                stats[feature] = {
                    'mean': np.mean(values),
                    'median': np.median(values),
                    'std': np.std(values),
                    'min': np.min(values),
                    'max': np.max(values)
                }
        
        return stats
    
    def _analyze_artists(self, tracks: List[Dict]) -> Dict[str, Any]:
        """Analyze artist distribution."""
        all_artists = []
        for track in tracks:
            artists = track.get('artists', [])
            if isinstance(artists, list):
                all_artists.extend([a if isinstance(a, str) else a.get('name', '') for a in artists])
            elif isinstance(artists, str):
                all_artists.append(artists)
        
        artist_counts = Counter(all_artists)
        top_artists = artist_counts.most_common(10)
        
        return {
            'total_unique': len(artist_counts),
            'top_artists': top_artists,
            'most_common_count': top_artists[0][1] if top_artists else 0
        }
    
    def _analyze_genres(self, tracks: List[Dict]) -> Dict[str, Any]:
        """Analyze genre distribution (requires artist lookup)."""
        # Get unique artist IDs
        artist_ids = set()
        artist_to_track = {}
        
        for track in tracks:
            track_id = track.get('id')
            if not track_id:
                continue
            
            # Try to get artist from track
            try:
                track_info = self.sp.track(track_id)
                for artist in track_info['artists']:
                    artist_id = artist['id']
                    artist_ids.add(artist_id)
                    if artist_id not in artist_to_track:
                        artist_to_track[artist_id] = []
                    artist_to_track[artist_id].append(track_id)
            except:
                continue
        
        # Get genres for artists (in batches)
        all_genres = []
        artist_ids_list = list(artist_ids)
        
        for i in range(0, len(artist_ids_list), 50):
            batch = artist_ids_list[i:i+50]
            try:
                artists = self.sp.artists(batch)
                for artist in artists['artists']:
                    if artist and artist.get('genres'):
                        all_genres.extend(artist['genres'])
                time.sleep(0.1)
            except:
                continue
        
        genre_counts = Counter(all_genres)
        top_genres = genre_counts.most_common(10)
        
        return {
            'total_unique': len(genre_counts),
            'top_genres': top_genres
        }
    
    def _analyze_popularity(self, tracks: List[Dict]) -> Dict[str, Any]:
        """Analyze track popularity."""
        # Get popularity for tracks
        popularities = []
        track_ids = [t.get('id') for t in tracks if t.get('id')]
        
        for i in range(0, len(track_ids), 50):
            batch = track_ids[i:i+50]
            try:
                track_info = self.sp.tracks(batch)
                for track in track_info['tracks']:
                    if track and track.get('popularity') is not None:
                        popularities.append(track['popularity'])
                time.sleep(0.1)
            except:
                continue
        
        if not popularities:
            return {}
        
        return {
            'mean': np.mean(popularities),
            'median': np.median(popularities),
            'min': np.min(popularities),
            'max': np.max(popularities)
        }
    
    def _analyze_moods(self, features_list: List[Dict]) -> Dict[str, int]:
        """Categorize tracks by mood based on audio features."""
        moods = {
            'Happy': 0,
            'Sad': 0,
            'Energetic': 0,
            'Calm': 0,
            'Party': 0,
            'Romantic': 0
        }
        
        for features in features_list:
            if not features:
                continue
            
            valence = features.get('valence', 0.5)
            energy = features.get('energy', 0.5)
            danceability = features.get('danceability', 0.5)
            acousticness = features.get('acousticness', 0.5)
            
            # Categorize based on features
            if valence > 0.7 and energy > 0.6:
                moods['Happy'] += 1
            elif valence < 0.4 and energy < 0.5:
                moods['Sad'] += 1
            elif energy > 0.8:
                moods['Energetic'] += 1
            elif energy < 0.4 and acousticness > 0.5:
                moods['Calm'] += 1
            elif danceability > 0.7 and energy > 0.7:
                moods['Party'] += 1
            elif valence > 0.6 and energy < 0.6:
                moods['Romantic'] += 1
        
        return moods
    
    def _categorize_energy(self, features_list: List[Dict]) -> Dict[str, int]:
        """Categorize tracks by energy level."""
        categories = {'Low': 0, 'Medium': 0, 'High': 0}
        
        for features in features_list:
            if not features:
                continue
            energy = features.get('energy', 0.5)
            if energy < 0.4:
                categories['Low'] += 1
            elif energy < 0.7:
                categories['Medium'] += 1
            else:
                categories['High'] += 1
        
        return categories
    
    def _categorize_danceability(self, features_list: List[Dict]) -> Dict[str, int]:
        """Categorize tracks by danceability."""
        categories = {'Low': 0, 'Medium': 0, 'High': 0}
        
        for features in features_list:
            if not features:
                continue
            danceability = features.get('danceability', 0.5)
            if danceability < 0.4:
                categories['Low'] += 1
            elif danceability < 0.7:
                categories['Medium'] += 1
            else:
                categories['High'] += 1
        
        return categories

