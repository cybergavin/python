#!/usr/bin/python

import sys
import argparse
import requests
import base64
import json
import configparser
from tabulate import tabulate
from pathlib import Path, PurePath
from urllib.parse import urlencode

# Variables
script_stem = PurePath(sys.argv[0]).stem
script_dir = Path((PurePath(sys.argv[0]).parent)).resolve(strict=True)
cfg_file = script_dir / f'{script_stem}.cfg'

# Validation
if not Path(cfg_file).exists():
    sys.exit(f'Missing configuration file {cfg_file}')

# Parse configuration
config = configparser.ConfigParser(interpolation=None)
config.read([cfg_file])
client_id = config['spotify_auth']['client_id']
client_secret = config['spotify_auth']['client_secret']
redirect_uri = config['spotify_auth']['redirect_uri']
user_id = config['spotify_auth']['user_id']
auth_url = config['spotify_url']['auth_url']
token_url = config['spotify_url']['token_url']
api_url = config['spotify_url']['api_url']
playlists_url = f'{api_url}/users/{user_id}/playlists'
search_url = f'{api_url}/search'

# Create the parser object
parser = argparse.ArgumentParser(description="Cybergavin Spotify CLI")

# Define the input parameters
parser.add_argument("-p", "--playlist", type=str, required=False, help="PLAYLIST = The 'name' of a Spotify playlist")
parser.add_argument("-t", "--track", type=str, required=False, help="TRACK = The 'name' of a song or track")
parser.add_argument("-i", "--trackid", type=str, required=False, help="TRACKID = The 'spotify id' of a song or track")
parser.add_argument("-l", "--list", required=False, action='store_true')
parser.add_argument("-s", "--search", required=False, action='store_true')
parser.add_argument("-a", "--add", required=False, action='store_true')
# parser.add_argument("-c", "--create", required=False, action='store_true')
parser.add_argument("-r", "--recent", type=int, required=False, help="RECENT = The 'number' of recently played tracks to list")

# Parse the input parameters
args = parser.parse_args()

# Access the input arguments
playlist_name = args.playlist
playlist_list = args.list
# playlist_create = args.create
track_name = args.track
track_id = args.trackid
track_search = args.search
track_add = args.add
track_recent = args.recent


def do_oauth(scope:str) -> dict:
    """Obtain authorization code for Spotify code auth workflow (user-server)"""
    params = {
    "client_id": client_id,
    "response_type": "code",
    "redirect_uri": redirect_uri,
    "scope": scope
    }
    oauth_url = f"{auth_url}?{urlencode(params)}"
    print(f"Please visit this URL to authorize the application: {oauth_url}")
    auth_code = input("Enter the authorization code: ")
    auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    headers = {"Authorization": f"Basic {auth_header}", "Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": redirect_uri,
        "scope": scope
    }
    try:
        response = requests.post(token_url, data=urlencode(data), headers=headers)
        response.raise_for_status()
    except Exception as err:
        raise SystemExit(f'Connectivity error\n {err}')
    try:
        data = response.json()
    except Exception as err:
        raise SystemExit(f'JSON parsing error\n {err}')
    try:
        access_token = data["access_token"]
    except Exception as err:
        raise SystemExit(f'JSON format error\n {err}')

    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    return headers


def do_client_credentials_auth() -> dict:
    """Obtain authorization code for Spotify client_credentials auth workflow (server-server)"""
    data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret
    }
    try:
        response = requests.post(token_url, data=data) 
        response.raise_for_status()
    except Exception as err:
        raise SystemExit(f'Connectivity error\n {err}')
    try:
        data = response.json()
    except Exception as err:
        raise SystemExit(f'JSON parsing error\n {err}')
    try:
        access_token = data["access_token"]
    except Exception as err:
        raise SystemExit(f'JSON format error\n {err}')

    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    return headers


def list_playlists() -> str:
    """List user's Spotify playlists"""
    auth_headers = do_client_credentials_auth()
    try:
        response = requests.get(playlists_url, headers=auth_headers)
        response.raise_for_status()
    except Exception as err:
        raise SystemExit(f'Connectivity error\n {err}')
    try:
        data = response.json()
    except Exception as err:
        raise SystemExit(f'JSON parsing error\n {err}')
    try:
        playlist_items = data["items"]
    except Exception as err:
        raise SystemExit(f'JSON format error\n {err}')    

    indexed_result = [[idx+1] + [playlist['name'], playlist['id']] for idx, playlist in enumerate(playlist_items)]
    print(tabulate(indexed_result, headers=["#", "Playlist", "Playlist ID"], showindex="never", tablefmt="rounded_outline"))


def search_track(song:str) -> str:
    """Search for a Spotify track (song)"""
    auth_headers = do_client_credentials_auth()
    search_params = {"q": f"track:{song}", "type": "track", "market": "US"}
    try:
        response = requests.get(search_url, params=search_params, headers=auth_headers)
        response.raise_for_status()
    except Exception as err:
        raise SystemExit(f'Connectivity error\n {err}')
    try:
        data = response.json()
    except Exception as err:
        raise SystemExit(f'JSON parsing error\n {err}')
    try:
        track_items = data["tracks"]["items"]
    except Exception as err:
        raise SystemExit(f'JSON format error\n {err}')  

    result = []
    for track in track_items:
        for artist in track["artists"]:
            result.append([artist['name'], track['name'], track['id']])
    indexed_result = [[idx+1] + row for idx, row in enumerate(result)]
    print(tabulate(indexed_result, headers=["#", "Artist", "Track", "Track ID"], showindex="never", tablefmt="rounded_outline"))



def add_track(track_id:str, playlist:str) -> str:
    """Add a track (song) using its track id to a specific Spotify playlist"""
    scope = "playlist-modify-public"
    auth_headers = do_oauth(scope)
    try:
        response = requests.get(playlists_url, headers=auth_headers)
        response.raise_for_status()
    except Exception as err:
        raise SystemExit(f'Connectivity error\n {err}')
    try:
        data = response.json()
    except Exception as err:
        raise SystemExit(f'JSON parsing error\n {err}')
    try:
        items = data["items"]
    except Exception as err:
        raise SystemExit(f'JSON format error\n {err}')  

    for p in items:
        if p["name"] == playlist:
            playlist_id = p["id"]
            break
    add_url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    data = {"uris": [f"spotify:track:{track_id}"]}
    
    try:
        response = requests.post(add_url, json=data, headers=auth_headers)
        response.raise_for_status()
    except Exception as err:
        raise SystemExit(f'Connectivity error\n {err}')
    print("Track added successfully!")  


def list_recent_tracks(num:int) -> str:
    """List recently played SPotify tracks (songs)"""
    scope = "user-read-recently-played"
    auth_headers = do_oauth(scope)
    recently_played_url = f"https://api.spotify.com/v1/me/player/recently-played?limit={num}"
    try:
        response = requests.get(recently_played_url, headers=auth_headers)
        response.raise_for_status()
    except Exception as err:
        raise SystemExit(f'Connectivity error\n {err}')
    try:
        data = response.json()
    except Exception as err:
        raise SystemExit(f'JSON parsing error\n {err}')
    try:
        items = data["items"]
    except Exception as err:
        raise SystemExit(f'JSON format error\n {err}')  

    indexed_result = [[idx+1] + [item['track']['name'], item['track']['artists'][0]['name']] for idx, item in enumerate(items)]
    print(tabulate(indexed_result, headers=["#", "Track", "Artist"], showindex="never", tablefmt="rounded_outline"))        

if (playlist_list):
    list_playlists()

if (track_search and track_name):
    search_track(track_name)

if (track_id and playlist_name):
    add_track(track_id,playlist_name)

if (track_recent):
    list_recent_tracks(track_recent)