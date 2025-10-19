import os
import tkinter as tk
from tkinter import filedialog
from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3
from mutagen import MutagenError
import json
import pyperclip

def get_metadata(file_path, ext):
    """Extracts album, artist, sample rate, and duration from an audio file."""
    try:
        album = ''
        artist = ''
        sample_rate = 0
        duration = 0.0
        if ext == '.flac':
            audio = FLAC(file_path)
            album = audio.tags.get('ALBUM', [''])[0].strip()
            artist_tags = audio.tags.get('ALBUMARTIST', audio.tags.get('ARTIST', ['']))
            artist = artist_tags[0].strip() if artist_tags else ''
            sample_rate = audio.info.sample_rate
            duration = audio.info.length
        elif ext == '.mp3':
            audio_tech = MP3(file_path)
            sample_rate = audio_tech.info.sample_rate
            duration = audio_tech.info.length
            
            audio_tags = EasyID3(file_path)
            album = audio_tags.get('album', [''])[0].strip()
            artist_tags = audio_tags.get('albumartist', audio_tags.get('artist', ['']))
            artist = artist_tags[0].strip() if artist_tags else ''
        else:
            return ('', '', 0, 0.0)
        return (album, artist, sample_rate, duration)
    except MutagenError as e:
        print(f"Error reading tags from {file_path}: {e}")
        return ('', '', 0, 0.0)

def format_size(size_bytes):
    """Converts bytes to a human-readable string (MB or GB)."""
    if size_bytes == 0:
        return "0 MB"
    gb = size_bytes / (1024**3)
    if gb >= 1:
        return f"{gb:.1f} GB"
    mb = size_bytes / (1024**2)
    return f"{mb:.1f} MB"

def format_duration(total_seconds):
    """Formats total seconds into hh:mm:ss or mm:ss."""
    if not total_seconds or total_seconds < 0:
        return None
    
    total_seconds = int(total_seconds)
    minutes, seconds = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes}:{seconds:02d}"

def build_string_manually(artist_name, album_list):
    """
    Builds the JSON item string with exact formatting, including new tags.
    """
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
    for album_details in album_list:
        # Build the tags list dynamically
        tags = [f'"{album_details["format"]}"']
        if album_details.get("track_count"):
            tags.append(f'"{album_details["track_count"]} tracks"')
        if album_details.get("duration_str"):
            tags.append(f'"{album_details["duration_str"]}"')
        if album_details.get("sample_rate_khz"):
            tags.append(f'"{album_details["sample_rate_khz"]:.1f}kHz"')
        if album_details.get("size_str"):
            tags.append(f'"{album_details["size_str"]}"')
            
        tags_str = ", ".join(tags)

        album_link = (
            '      {\n'
            f'        "title": {json.dumps(album_details["title"])},\n'
            '        "url": [],\n'
            '        "description": "",\n'
            f'        "tags": [{tags_str}]\n'
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
    and then generates the JSON item string with detailed tags.
    """
    all_albums_by_artist = {}
    for root, _, files in os.walk(directory):
        # Data for the current directory (considered one album)
        album_title, album_artist, audio_format = (None, None, None)
        track_count = 0
        total_size_bytes = 0
        total_duration_seconds = 0.0
        sample_rates = []

        first_audio_file_found = False
        for file in files:
            file_path = os.path.join(root, file)
            total_size_bytes += os.path.getsize(file_path)
            
            ext = os.path.splitext(file)[1].lower()
            if ext in {'.flac', '.mp3'}:
                track_count += 1
                current_album, current_artist, current_rate, current_duration = get_metadata(file_path, ext)
                
                total_duration_seconds += current_duration
                if current_rate > 0:
                    sample_rates.append(current_rate)
                
                if not first_audio_file_found:
                    album_title = current_album
                    album_artist = current_artist
                    audio_format = ext[1:].upper()
                    first_audio_file_found = True
        
        # If we found an album in this folder, process and store it
        if first_audio_file_found and album_artist and album_title:
            if album_artist not in all_albums_by_artist:
                all_albums_by_artist[album_artist] = []
            
            min_sample_rate_khz = min(sample_rates) / 1000 if sample_rates else None

            album_data = {
                "title": album_title,
                "format": audio_format,
                "track_count": track_count,
                "size_str": format_size(total_size_bytes),
                "sample_rate_khz": min_sample_rate_khz,
                "duration_str": format_duration(total_duration_seconds),
            }
            all_albums_by_artist[album_artist].append(album_data)

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