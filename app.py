import streamlit as st
import os
from dotenv import load_dotenv
import google.generativeai as genai
import spotipy
from spotipy.oauth2 import SpotifyOAuth

load_dotenv()

# Setup Gemini API
GOOGLE_API_KEY = os.getenv("GEMINI_PRO_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-pro")

# Setup Spotify API
SPOTIPY_CLIENT_ID = os.getenv("SPOTIFY_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIFY_SECRET")
SPOTIPY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")
SPOTIPY_SCOPE = "playlist-modify-private"

# Spotify Authentication
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET,
    redirect_uri=SPOTIPY_REDIRECT_URI,
    scope=SPOTIPY_SCOPE
))

def get_gemini_response(prompt):
    """Gets a response from Gemini."""
    try:
      response = model.generate_content(prompt)
      return response.text
    except Exception as e:
      st.error(f"Error from Gemini: {e}")
      return None

def search_spotify_tracks(query):
    """Searches Spotify for tracks based on the given query."""
    try:
        results = sp.search(q=query, type='track', limit=10)
        tracks = results.get('tracks', {}).get('items', [])
        if tracks:
            return [track['uri'] for track in tracks]
        else:
            return []
    except Exception as e:
        st.error(f"Error searching Spotify: {e}")
        return []


def create_spotify_playlist(user_id, track_uris, playlist_name):
    """Creates a new playlist on Spotify and adds tracks."""
    try:
        playlist = sp.user_playlist_create(user_id, name=playlist_name, public=False)
        if playlist:
             sp.playlist_add_items(playlist['id'], track_uris)
             return playlist['external_urls']['spotify']
        else:
             return None
    except Exception as e:
      st.error(f"Error creating playlist: {e}")
      return None


def main():
    st.title("🎶 Gemini Spotify Playlist Generator")

    # Get user ID
    user_id = sp.me()['id']

    # User Input
    user_prompt = st.text_area("Enter a description for your playlist (e.g., 'happy songs for a workout', 'chill music for studying'):")
    num_songs = st.slider("Number of songs:", 5, 20, 10)
    
    if st.button("Generate Playlist"):
         if user_prompt:
          with st.spinner("Generating playlist..."):
              # 1. Get Gemini response
              gemini_prompt = f"""
              Generate a comma-separated list of music track keywords to search for on Spotify based on this playlist description:
              '{user_prompt}'. Include no more than {num_songs} keywords.
              """
              gemini_response = get_gemini_response(gemini_prompt)

              if gemini_response:
                  keywords = [keyword.strip() for keyword in gemini_response.split(",")]

              # 2. Search Spotify
                  all_track_uris = []
                  for keyword in keywords:
                     track_uris = search_spotify_tracks(keyword)
                     all_track_uris.extend(track_uris)
              
                  if len(all_track_uris) > num_songs:
                    all_track_uris = all_track_uris[:num_songs]
                  
              
              # 3. Create playlist
                  if all_track_uris:
                     playlist_name = f"Gemini Playlist - {user_prompt[:20]}..."
                     playlist_url = create_spotify_playlist(user_id, all_track_uris, playlist_name)

                     if playlist_url:
                        st.success(f"Playlist created! [Click here to view playlist]({playlist_url})")
                     else:
                         st.error("Failed to create playlist on spotify.")
                  else:
                      st.warning("No tracks found based on the given keywords.")
              else:
                  st.error("Failed to get valid keywords from Gemini.")
         else:
             st.warning("Please enter a playlist description.")

if __name__ == "__main__":
    main()