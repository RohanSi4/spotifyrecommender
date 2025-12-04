"""
Recommendation engine with multiple algorithms for Spotify tracks.
"""
from spotipy import Spotify
import numpy as np
from typing import List, Dict, Any, Optional
from collections import Counter
import time


class SpotifyRecommender:
    """Main recommendation engine for Spotify tracks."""
    
    def __init__(self, spotify_client: Spotify):
        self.sp = spotify_client
        self.audio_features_keys = [
            'danceability', 'energy', 'key', 'loudness', 'mode',
            'speechiness', 'acousticness', 'instrumentalness',
            'liveness', 'valence', 'tempo'
        ]
    
    def _normalize_features(self, features: Dict[str, Any]) -> np.ndarray:
        """Normalize audio features for comparison."""
        if not features:
            return np.zeros(len(self.audio_features_keys))
        
        # Extract features, handling missing values
        feature_vector = []
        for key in self.audio_features_keys:
            value = features.get(key, 0)
            # Normalize tempo (typically 60-200 BPM) to 0-1 scale
            if key == 'tempo':
                value = (value - 60) / 140 if value else 0
            # Normalize loudness (typically -60 to 0 dB) to 0-1 scale
            elif key == 'loudness':
                value = (value + 60) / 60 if value else 0
            # Key is already 0-11, normalize to 0-1
            elif key == 'key':
                value = value / 11 if value is not None else 0
            # Other features are already 0-1
            else:
                value = value if value is not None else 0
            
            feature_vector.append(value)
        
        return np.array(feature_vector)
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two feature vectors."""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def _euclidean_distance(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate Euclidean distance between two feature vectors."""
        return np.linalg.norm(vec1 - vec2)
    
    def content_based_recommendations(
        self,
        seed_tracks: List[Dict[str, Any]],
        user_tracks: List[Dict[str, Any]],
        num_recommendations: int = 20,
        similarity_metric: str = 'cosine'
    ) -> List[Dict[str, Any]]:
        """
        Content-based recommendations based on audio features.
        
        Args:
            seed_tracks: Tracks to base recommendations on
            user_tracks: User's existing tracks to exclude from recommendations
            num_recommendations: Number of recommendations to return
            similarity_metric: 'cosine' or 'euclidean'
        """
        if not seed_tracks:
            return []
        
        # Get audio features for seed tracks
        seed_ids = [track['id'] for track in seed_tracks if track.get('id')]
        seed_features = self.sp.audio_features(seed_ids)
        
        # Calculate average feature vector for seed tracks
        seed_vectors = []
        for features in seed_features:
            if features:
                seed_vectors.append(self._normalize_features(features))
        
        if not seed_vectors:
            return []
        
        avg_seed_vector = np.mean(seed_vectors, axis=0)
        
        # Get user's existing track IDs to exclude
        user_track_ids = {track['id'] for track in user_tracks if track.get('id')}
        
        # Find similar tracks from user's library
        track_scores = []
        for track in user_tracks:
            if track['id'] in user_track_ids or not track.get('features'):
                continue
            
            track_vector = self._normalize_features(track['features'])
            
            if similarity_metric == 'cosine':
                similarity = self._cosine_similarity(avg_seed_vector, track_vector)
            else:  # euclidean
                distance = self._euclidean_distance(avg_seed_vector, track_vector)
                similarity = 1 / (1 + distance)  # Convert distance to similarity
            
            track_scores.append({
                'track': track,
                'score': similarity
            })
        
        # Sort by similarity score
        track_scores.sort(key=lambda x: x['score'], reverse=True)
        
        return [item['track'] for item in track_scores[:num_recommendations]]
    
    def get_spotify_recommendations(
        self,
        seed_tracks: List[str] = None,
        seed_artists: List[str] = None,
        seed_genres: List[str] = None,
        limit: int = 20,
        **target_features
    ) -> List[Dict[str, Any]]:
        """
        Get recommendations using Spotify's built-in recommendation API.
        
        Args:
            seed_tracks: List of track IDs
            seed_artists: List of artist IDs
            seed_genres: List of genre names
            limit: Number of recommendations (max 100)
            **target_features: Target audio features (e.g., target_energy=0.8)
        """
        # Spotify API requires at least one seed and max 5 total seeds
        # Filter out None/empty lists and limit to 5 total
        seeds_used = 0
        max_seeds = 5
        
        final_seed_tracks = None
        final_seed_artists = None
        final_seed_genres = None
        
        if seed_tracks:
            available = max_seeds - seeds_used
            if available > 0:
                final_seed_tracks = seed_tracks[:min(len(seed_tracks), available)]
                seeds_used += len(final_seed_tracks)
        
        if seed_artists and seeds_used < max_seeds:
            available = max_seeds - seeds_used
            if available > 0:
                final_seed_artists = seed_artists[:min(len(seed_artists), available)]
                seeds_used += len(final_seed_artists)
        
        if seed_genres and seeds_used < max_seeds:
            available = max_seeds - seeds_used
            if available > 0:
                final_seed_genres = seed_genres[:min(len(seed_genres), available)]
                seeds_used += len(final_seed_genres)
        
        # Ensure we have at least one seed
        if not final_seed_tracks and not final_seed_artists and not final_seed_genres:
            raise ValueError("At least one seed (track, artist, or genre) is required for recommendations")
        
        recommendations = self.sp.recommendations(
            seed_tracks=final_seed_tracks,
            seed_artists=final_seed_artists,
            seed_genres=final_seed_genres,
            limit=min(limit, 100),
            **target_features
        )
        
        tracks = []
        for track in recommendations['tracks']:
            tracks.append({
                'id': track['id'],
                'name': track['name'],
                'artists': [artist['name'] for artist in track['artists']],
                'album': track['album']['name'],
                'uri': track['uri'],
                'popularity': track['popularity']
            })
        
        return tracks
    
    def hybrid_recommendations(
        self,
        seed_tracks: List[Dict[str, Any]],
        user_tracks: List[Dict[str, Any]],
        num_recommendations: int = 20,
        spotify_weight: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Hybrid approach combining content-based and Spotify's recommendations.
        
        Args:
            seed_tracks: Tracks to base recommendations on
            user_tracks: User's existing tracks
            num_recommendations: Number of recommendations
            spotify_weight: Weight for Spotify recommendations (0-1)
        """
        # Get Spotify recommendations
        seed_ids = [track['id'] for track in seed_tracks[:5] if track.get('id')]
        
        # Ensure we have valid seed IDs
        if not seed_ids:
            # If no valid seed IDs, fall back to content-based only
            return self.content_based_recommendations(
                seed_tracks=seed_tracks,
                user_tracks=user_tracks,
                num_recommendations=num_recommendations
            )
        
        try:
            spotify_recs = self.get_spotify_recommendations(
                seed_tracks=seed_ids,
                limit=num_recommendations * 2
            )
        except Exception as e:
            # If Spotify API fails, fall back to content-based only
            return self.content_based_recommendations(
                seed_tracks=seed_tracks,
                user_tracks=user_tracks,
                num_recommendations=num_recommendations
            )
        
        # Get content-based recommendations
        content_recs = self.content_based_recommendations(
            seed_tracks=seed_tracks,
            user_tracks=user_tracks,
            num_recommendations=num_recommendations * 2
        )
        
        # Combine and rank
        all_recs = {}
        
        # Add Spotify recommendations
        for track in spotify_recs:
            track_id = track['id']
            if track_id not in all_recs:
                all_recs[track_id] = {
                    'track': track,
                    'score': spotify_weight * track.get('popularity', 50) / 100
                }
        
        # Add content-based recommendations
        for track in content_recs:
            track_id = track['id']
            if track_id in all_recs:
                all_recs[track_id]['score'] += (1 - spotify_weight) * 0.8
            else:
                all_recs[track_id] = {
                    'track': track,
                    'score': (1 - spotify_weight) * 0.8
                }
        
        # Sort by combined score
        sorted_recs = sorted(all_recs.values(), key=lambda x: x['score'], reverse=True)
        
        return [item['track'] for item in sorted_recs[:num_recommendations]]
    
    def get_artist_recommendations(
        self,
        artist_name: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get recommendations based on an artist."""
        # Search for artist
        results = self.sp.search(q=f'artist:{artist_name}', type='artist', limit=1)
        
        if not results['artists']['items']:
            return []
        
        artist_id = results['artists']['items'][0]['id']
        
        # Get artist's top tracks
        top_tracks = self.sp.artist_top_tracks(artist_id)
        seed_tracks = [track['id'] for track in top_tracks['tracks'][:3]]
        
        # Get recommendations
        return self.get_spotify_recommendations(
            seed_artists=[artist_id],
            seed_tracks=seed_tracks,
            limit=limit
        )
    
    def discover_similar_artists(
        self,
        artist_name: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Discover artists similar to a given artist."""
        results = self.sp.search(q=f'artist:{artist_name}', type='artist', limit=1)
        
        if not results['artists']['items']:
            return []
        
        artist_id = results['artists']['items'][0]['id']
        similar_artists = self.sp.artist_related_artists(artist_id)
        
        artists = []
        for artist in similar_artists['artists'][:limit]:
            artists.append({
                'id': artist['id'],
                'name': artist['name'],
                'genres': artist['genres'],
                'popularity': artist['popularity']
            })
        
        return artists
    
    def get_mood_features(self, mood: str) -> Dict[str, float]:
        """
        Map mood to target audio features for Spotify recommendations.
        
        Args:
            mood: One of: happy, sad, energetic, calm, party, focus, workout, romantic
        
        Returns:
            Dictionary of target audio features
        """
        mood_mappings = {
            'happy': {
                'target_valence': 0.8,
                'target_energy': 0.7,
                'target_danceability': 0.7,
                'min_valence': 0.6
            },
            'sad': {
                'target_valence': 0.2,
                'target_energy': 0.3,
                'target_danceability': 0.3,
                'max_valence': 0.4
            },
            'energetic': {
                'target_energy': 0.9,
                'target_tempo': 140,
                'target_danceability': 0.7,
                'min_energy': 0.7
            },
            'calm': {
                'target_energy': 0.3,
                'target_acousticness': 0.6,
                'target_valence': 0.5,
                'max_energy': 0.5
            },
            'relaxed': {
                'target_energy': 0.2,
                'target_acousticness': 0.7,
                'target_tempo': 80,
                'max_energy': 0.4,
                'max_tempo': 100
            },
            'party': {
                'target_danceability': 0.9,
                'target_energy': 0.9,
                'target_tempo': 130,
                'min_danceability': 0.7,
                'min_energy': 0.7
            },
            'focus': {
                'target_energy': 0.4,
                'target_speechiness': 0.1,
                'target_instrumentalness': 0.5,
                'max_energy': 0.6,
                'max_speechiness': 0.2
            },
            'workout': {
                'target_energy': 0.95,
                'target_tempo': 150,
                'target_danceability': 0.8,
                'min_energy': 0.8,
                'min_tempo': 120
            },
            'romantic': {
                'target_valence': 0.6,
                'target_energy': 0.4,
                'target_acousticness': 0.5,
                'target_tempo': 100,
                'min_valence': 0.5
            }
        }
        
        mood_lower = mood.lower()
        if mood_lower not in mood_mappings:
            # Default to happy if mood not recognized
            return mood_mappings['happy']
        
        return mood_mappings[mood_lower]
    
    def mood_based_recommendations(
        self,
        mood: str,
        seed_tracks: List[str] = None,
        seed_artists: List[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get recommendations based on mood using Spotify's target features.
        
        Uses a hybrid approach:
        1. Spotify API with mood-based target features
        2. Content-based filtering from user's library if seed tracks provided
        
        Args:
            mood: Mood name (happy, sad, energetic, calm, relaxed, party, focus, workout, romantic)
            seed_tracks: Optional list of track IDs to seed recommendations
            seed_artists: Optional list of artist IDs to seed recommendations
            limit: Number of recommendations
        """
        # Get mood-based target features
        mood_features = self.get_mood_features(mood)
        
        # If we have seed tracks, use them; otherwise try to get seeds
        if not seed_tracks and not seed_artists:
            # Strategy 1: Use popular genres based on mood (most reliable)
            mood_genres = {
                'happy': ['pop', 'dance', 'indie-pop'],
                'sad': ['indie', 'alternative', 'singer-songwriter'],
                'energetic': ['rock', 'electronic', 'hip-hop'],
                'calm': ['ambient', 'classical', 'jazz'],
                'relaxed': ['acoustic', 'folk', 'chill'],
                'party': ['dance', 'electronic', 'house'],
                'focus': ['classical', 'ambient', 'instrumental'],
                'workout': ['rock', 'electronic', 'hip-hop'],
                'romantic': ['pop', 'r-n-b', 'soul']
            }
            seed_genres = mood_genres.get(mood.lower(), ['pop'])
            
            # Try to get recommendations with genres first (most reliable)
            try:
                return self.get_spotify_recommendations(
                    seed_genres=seed_genres,
                    limit=limit,
                    **mood_features
                )
            except Exception as e:
                # If genres fail, try to get user's top tracks
                try:
                    top_tracks = self.sp.current_user_top_tracks(limit=5, time_range='medium_term')
                    if top_tracks and top_tracks.get('items') and len(top_tracks['items']) > 0:
                        seed_tracks = [track['id'] for track in top_tracks['items'] if track.get('id')]
                except:
                    pass
        
        # Ensure we have valid seed tracks
        if seed_tracks:
            seed_tracks = [tid for tid in seed_tracks if tid]  # Filter out None/empty
        
        if not seed_tracks and not seed_artists:
            # Last resort: use a default genre
            seed_genres = ['pop']
            return self.get_spotify_recommendations(
                seed_genres=seed_genres,
                limit=limit,
                **mood_features
            )
        
        # Get recommendations with mood-based features
        recommendations = self.get_spotify_recommendations(
            seed_tracks=seed_tracks if seed_tracks else None,
            seed_artists=seed_artists if seed_artists else None,
            limit=limit * 2,  # Get more to filter
            **mood_features
        )
        
        # Filter and rank by mood match
        mood_filtered = []
        for track in recommendations:
            # Get audio features for this track
            features = self.sp.audio_features([track['id']])[0]
            if not features:
                continue
            
            # Calculate mood match score
            match_score = self._calculate_mood_match(features, mood_features, mood)
            track['mood_score'] = match_score
            mood_filtered.append(track)
        
        # Sort by mood match score
        mood_filtered.sort(key=lambda x: x.get('mood_score', 0), reverse=True)
        
        return mood_filtered[:limit]
    
    def _calculate_mood_match(
        self,
        features: Dict[str, Any],
        target_features: Dict[str, float],
        mood: str
    ) -> float:
        """Calculate how well a track matches the target mood."""
        if not features:
            return 0.0
        
        score = 1.0
        mood_lower = mood.lower()
        
        # Weight different features based on mood
        if mood_lower in ['happy', 'sad', 'romantic']:
            # Valence is most important
            target_val = target_features.get('target_valence', 0.5)
            actual_val = features.get('valence', 0.5)
            score *= 1 - abs(target_val - actual_val)
        
        if mood_lower in ['energetic', 'workout', 'party']:
            # Energy is most important
            target_energy = target_features.get('target_energy', 0.5)
            actual_energy = features.get('energy', 0.5)
            score *= 1 - abs(target_energy - actual_energy)
        
        if mood_lower in ['calm', 'relaxed', 'focus']:
            # Low energy is important
            target_energy = target_features.get('target_energy', 0.3)
            actual_energy = features.get('energy', 0.5)
            score *= 1 - abs(target_energy - actual_energy)
        
        if mood_lower in ['party', 'workout']:
            # Danceability matters
            target_dance = target_features.get('target_danceability', 0.7)
            actual_dance = features.get('danceability', 0.5)
            score *= 1 - abs(target_dance - actual_dance) * 0.5
        
        # Check min/max constraints
        for key, value in target_features.items():
            if key.startswith('min_'):
                feature_key = key.replace('min_', '')
                if features.get(feature_key, 0) < value:
                    score *= 0.5
            elif key.startswith('max_'):
                feature_key = key.replace('max_', '')
                if features.get(feature_key, 1) > value:
                    score *= 0.5
        
        return max(0.0, min(1.0, score))

