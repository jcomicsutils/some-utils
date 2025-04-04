import os
import tkinter as tk
from tkinter import filedialog
from mutagen.flac import FLAC
from mutagen.easyid3 import EasyID3
from mutagen import MutagenError
import pyperclip

def get_metadata(file_path, ext):
    try:
        album = ''
        artist = ''
        if ext == '.flac':
            audio = FLAC(file_path)
            album = audio.tags.get('ALBUM', [''])[0].strip()
            artist = audio.tags.get('ALBUMARTIST', audio.tags.get('ARTIST', ['']))
            artist = artist[0].strip() if artist else ''
        elif ext == '.mp3':
            audio = EasyID3(file_path)
            album = audio.get('album', [''])[0].strip()
            artist = audio.get('albumartist', audio.get('artist', ['']))
            artist = artist[0].strip() if artist else ''
        else:
            return ('', '')
        return (album, artist)
    except MutagenError as e:
        print(f"Error reading tags from {file_path}: {e}")
        return ('', '')

def process_directory(directory):
    results = {}
    for root, _, files in os.walk(directory):
        audio_files = []
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in {'.flac', '.mp3'}:
                audio_files.append(file)
        
        if not audio_files:
            continue

        album_title = None
        album_artist = None
        audio_format = None
        error = None

        for file in audio_files:
            ext = os.path.splitext(file)[1].lower()
            current_format = ext[1:].upper()
            file_path = os.path.join(root, file)
            current_album, current_artist = get_metadata(file_path, ext)

            if album_title is None:
                album_title = current_album
                album_artist = current_artist
                audio_format = current_format
            else:
                if current_format != audio_format:
                    error = f"Error: Multiple audio formats in {root}"
                    break
                if current_album != album_title:
                    error = f"Error: Multiple album titles in {root}"
                    break
                if current_artist != album_artist:
                    error = f"Error: Multiple album artists in {root}"
                    break

        if error:
            print(error)
        else:
            if album_artist not in results:
                results[album_artist] = []
            results[album_artist].append((album_title, audio_format))

    # Prepare output
    output_lines = []
    print("\nResults:")
    for artist, albums in results.items():
        header = f"[b]{artist} [, Folder][/b]\n"
        print(header)
        output_lines.append(header)
        for album, fmt in albums:
            line = f"[, {album}, {fmt}]"
            print(line)
            output_lines.append(line)
        output_lines.append("")  # Add a blank line between artists
    
    # Copy to clipboard
    output_str = '\n'.join(output_lines)
    try:
        pyperclip.copy(output_str)
        print("\nResults copied to clipboard!")
    except Exception as e:
        print(f"\nFailed to copy to clipboard: {e}")

def select_directory():
    root = tk.Tk()
    root.withdraw()
    directory = filedialog.askdirectory(title="Select Directory")
    if directory:
        process_directory(directory)
    else:
        print("No directory selected")

if __name__ == "__main__":
    select_directory()
