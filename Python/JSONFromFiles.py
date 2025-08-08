import os
import tkinter as tk
from tkinter import filedialog
from mutagen.flac import FLAC
from mutagen.easyid3 import EasyID3
from mutagen import MutagenError
import json
import pyperclip

def get_metadata(file_path, ext):
    """Extracts album and artist metadata from an audio file."""
    try:
        album = ''
        artist = ''
        if ext == '.flac':
            audio = FLAC(file_path)
            album = audio.tags.get('ALBUM', [''])[0].strip()
            artist_tags = audio.tags.get('ALBUMARTIST', audio.tags.get('ARTIST', ['']))
            artist = artist_tags[0].strip() if artist_tags else ''
        elif ext == '.mp3':
            audio = EasyID3(file_path)
            album = audio.get('album', [''])[0].strip()
            artist_tags = audio.get('albumartist', audio.get('artist', ['']))
            artist = artist_tags[0].strip() if artist_tags else ''
        else:
            return ('', '')
        return (album, artist)
    except MutagenError as e:
        print(f"Error reading tags from {file_path}: {e}")
        return ('', '')

def build_string_manually(artist_name, album_list):
    """
    Builds the JSON item string with exact formatting, including the final trailing comma.
    """
    # Use json.dumps on individual strings to handle special characters like quotes.
    category_line = f'    "category": {json.dumps(artist_name)},'
    
    links_content = []
    
    # 1. The static "Folder" link object
    folder_link = (
        '      {\n'
        '        "title": "Folder",\n'
        '        "url": [],\n'
        '        "description": "",\n'
        '        "tags": []\n'
        '      }'
    )
    links_content.append(folder_link)
    
    # 2. Each album link object
    for album_title, audio_format in album_list:
        album_link = (
            '      {\n'
            f'        "title": {json.dumps(album_title)},\n'
            '        "url": [],\n'
            '        "description": "",\n'
            f'        "tags": ["{audio_format}"]\n'
            '      }'
        )
        links_content.append(album_link)
        
    # Join all link objects with a comma and newline
    links_block = ',\n'.join(links_content)
    
    # Assemble the final, complete string
    final_string = (
        '{\n'
        f'{category_line}\n'
        '    "links": [\n'
        f'{links_block}\n'
        '    ]\n'
        '},'
    )
    
    return final_string


def process_directory(directory):
    """
    Processes a directory to find all albums, verifies they belong to a single artist,
    and then generates the JSON item string.
    """
    all_albums_by_artist = {}
    for root, _, files in os.walk(directory):
        # This logic assumes each sub-folder is a single, consistent album
        album_title, album_artist, audio_format = (None, None, None)
        has_audio = False
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in {'.flac', '.mp3'}:
                has_audio = True
                current_album, current_artist = get_metadata(os.path.join(root, file), ext)
                album_title = current_album
                album_artist = current_artist
                audio_format = ext[1:].upper()
                # We only need one valid file to get the album info
                break 
        
        if has_audio and album_artist and album_title:
            if album_artist not in all_albums_by_artist:
                all_albums_by_artist[album_artist] = []
            # Add album if not already in the list to avoid duplicates
            if (album_title, audio_format) not in all_albums_by_artist[album_artist]:
                all_albums_by_artist[album_artist].append((album_title, audio_format))

    if not all_albums_by_artist:
        print("No valid audio albums found in the selected directory.")
        return
        
    if len(all_albums_by_artist) > 1:
        print("Error: Found albums from multiple artists. This script can only generate an item for a single artist at a time.")
        print("Artists found:", ", ".join(all_albums_by_artist.keys()))
        return

    # If we passed the checks, there is only one artist
    artist_name = list(all_albums_by_artist.keys())[0]
    album_list = all_albums_by_artist[artist_name]
    
    # Build the final string with the exact required format
    output_str = build_string_manually(artist_name, album_list)

    print("\n--- JSON Item Output ---")
    print(output_str)
    print("------------------------")

    try:
        pyperclip.copy(output_str)
        print("\n✅ Results copied to clipboard!")
    except Exception as e:
        print(f"\n❌ Could not copy to clipboard: {e}")


def select_directory():
    """Opens a dialog to select the root directory for processing."""
    root = tk.Tk()
    root.withdraw()
    directory = filedialog.askdirectory(title="Select a Directory for ONE Artist")
    if directory:
        process_directory(directory)
    else:
        print("No directory selected.")

if __name__ == "__main__":
    select_directory()