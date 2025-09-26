import os
import re
import sys
import hashlib
from collections import Counter
from typing import Optional, Dict, List, Tuple

try:
    # Mutagen is a powerful third-party library for handling audio metadata.
    # It needs to be installed separately.
    # You can install it by running: pip install mutagen
    from mutagen import File as MutagenFile, MutagenError
except ImportError:
    print("Error: The 'mutagen' library is required.")
    print("Please install it by running: pip install mutagen")
    sys.exit(1)

# --- Configuration ---
SUPPORTED_EXTENSIONS = ('.mp3', '.flac', '.m4a', '.ogg')
SUPPORTED_IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tif', '.tiff')
PATH_LENGTH_LIMIT_BYTES = 230

def sanitize_filename(name: str, is_path_component: bool = False) -> str:
    """Cleans a string to be a valid filename or folder name."""
    if is_path_component:
        name = name.replace('/', ' ').replace('\\', ' ')
    else:
        name = name.replace('/', ' - ').replace('\\', ' - ')
    
    name = re.sub(r'[<>:"|?*]', '', name)
    name = re.sub(r'\s+', ' ', name)
    name = name.strip(' .')
    return name

def get_audio_metadata(file_path: str) -> Optional[Dict[str, str]]:
    """Extracts metadata from a given audio file, returning a dict even if no tags are present."""
    try:
        audio = MutagenFile(file_path, easy=True)

        # Initialize all tags to None
        album = artist = albumartist = title = date = track = disc = year = invalid_year_tag = None

        # If the file loaded and has tags, extract them
        if audio:
            album = audio.get('album', [None])[0]
            artist = audio.get('artist', [None])[0]
            albumartist = audio.get('albumartist', [None])[0]
            title = audio.get('title', [None])[0]
            date = audio.get('date', [None])[0]
            track = audio.get('tracknumber', [None])[0]
            disc = audio.get('discnumber', [None])[0]
        
        # Process date tag if it exists
        if date:
            date_str = str(date).strip()
            if re.fullmatch(r'\d{4}', date_str):
                year = date_str
            else:
                invalid_year_tag = date_str
        
        # Always return a dictionary for valid files, even if tags are missing
        return {
            'album': str(album) if album else None, 'year': str(year) if year else None,
            'artist': str(artist) if artist else None, 'title': str(title) if title else None,
            'track': str(track) if track else None, 'disc': str(disc) if disc else None,
            'albumartist': str(albumartist) if albumartist else None,
            'invalid_year_tag': invalid_year_tag
        }
    except MutagenError as e:
        # Only return None if the file itself cannot be read or parsed
        print(f"  [Warning] Could not read metadata from {os.path.basename(file_path)}: {e}")
        return None

def get_cover_art_info(file_path: str) -> Tuple[int, Optional[str]]:
    """Gets cover art count and a hash of the first art piece from a file."""
    try:
        audio = MutagenFile(file_path)
        if not audio: return 0, None

        pictures = []
        if hasattr(audio, 'pictures') and audio.pictures:  # FLAC, OGG
            pictures = audio.pictures
        elif 'APIC:' in audio:  # MP3
            pictures = audio.tags.getall('APIC:')
        elif 'covr' in audio:  # M4A
            pictures = audio['covr']

        count = len(pictures)
        hash_val = None
        if count > 0:
            pic_data = pictures[0].data if hasattr(pictures[0], 'data') else pictures[0]
            hash_val = hashlib.md5(pic_data).hexdigest()
        return count, hash_val
    except (MutagenError, KeyError, IndexError):
        return 0, None

def remove_redundant_disc_tags(info: Dict, final_name: str):
    """Removes the 'discnumber' tag from files and updates the in-memory metadata."""
    print(f"  -> Removing redundant discnumber tag from files in '{final_name}'...")
    for md in info['files_metadata']:
        filename = md['filename']
        file_path = os.path.join(info['path'], filename)
        try:
            audio = MutagenFile(file_path, easy=True)
            if audio and 'discnumber' in audio:
                del audio['discnumber']
                audio.save()
                md['disc'] = None
        except Exception as e:
            print(f"    [Error] Could not update tags for {filename}: {e}")

def flatten_container_folder(dirpath: str, dirnames: List[str]) -> bool:
    """Moves files from subfolders into the parent, then deletes empty subfolders."""
    print(f"  -> Flattening '{os.path.basename(dirpath)}'...")
    try:
        for subfolder_name in dirnames:
            subfolder_path = os.path.join(dirpath, subfolder_name)
            for filename in os.listdir(subfolder_path):
                source_path = os.path.join(subfolder_path, filename)
                dest_path = os.path.join(dirpath, filename)
                
                if os.path.exists(dest_path):
                    name, ext = os.path.splitext(filename)
                    counter = 1
                    while os.path.exists(dest_path):
                        dest_path = os.path.join(dirpath, f"{name} ({counter}){ext}")
                        counter += 1
                
                os.rename(source_path, dest_path)
            os.rmdir(subfolder_path)
        print(f"  -> Flattening complete.")
        return True
    except OSError as e:
        print(f"  [Error] Failed to flatten folder: {e}")
        return False

def analyze_album_folder(dirpath: str, filenames: List[str]) -> Optional[Dict]:
    """Analyzes a single folder, collects all file metadata, and returns a summary."""
    audio_files_with_ext = [f for f in filenames if f.lower().endswith(SUPPORTED_EXTENSIONS)]
    if not audio_files_with_ext: return None

    print(f"Analyzing: {os.path.basename(dirpath)}")
    
    files_metadata = []
    for filename in audio_files_with_ext:
        filepath = os.path.join(dirpath, filename)
        metadata = get_audio_metadata(filepath)
        if metadata:
            metadata['filename'] = filename
            count, hash_val = get_cover_art_info(filepath)
            metadata['cover_art_count'] = count
            metadata['cover_art_hash'] = hash_val
            files_metadata.append(metadata)

    if not files_metadata:
        return None

    album_tags = [md['album'] for md in files_metadata if md.get('album')]
    if album_tags:
        most_common_album, _ = Counter(album_tags).most_common(1)[0]
        years_for_album = [md.get('year') for md in files_metadata if md.get('album') == most_common_album and md.get('year')]
        year = Counter(years_for_album).most_common(1)[0][0] if years_for_album else None
    else:
        most_common_album = os.path.basename(dirpath)
        year = None

    print(f"  -> Found album: '{most_common_album}'" + (f" ({year})" if year else ""))
    
    return {
        'path': dirpath, 'album': most_common_album, 'year': year,
        'files_metadata': files_metadata,
        'has_images': any(f.lower().endswith(SUPPORTED_IMAGE_EXTENSIONS) for f in filenames)
    }

def check_cover_art(files_metadata: List[Dict]) -> List[str]:
    """Checks for issues with embedded cover art and returns general warning tags."""
    warnings = set()
    cover_hashes = set()
    files_with_art = 0
    total_files = len(files_metadata)

    for md in files_metadata:
        count = md.get('cover_art_count', 0)
        hash_val = md.get('cover_art_hash')

        if count > 1:
            warnings.add("[Multiple Covers]")
        
        if hash_val:
            cover_hashes.add(hash_val)
            files_with_art += 1

    if len(cover_hashes) > 1:
        warnings.add("[Inconsistent Covers]")

    if files_with_art < total_files:
        warnings.add("[Missing Cover]")
        
    return sorted(list(warnings))

def check_track_gaps(files_metadata: List[Dict]) -> List[str]:
    """Checks for gaps in track numbers and returns general warning tags."""
    warnings = set()
    tracks_by_disc: Dict[str, List[int]] = {}

    for md in files_metadata:
        track_str = md.get('track')
        disc_str = md.get('disc') or '1'
        
        if track_str:
            try:
                if '/' in str(track_str):
                    track_str = str(track_str).split('/')[0]
                track_num = int(track_str)
                
                if disc_str not in tracks_by_disc:
                    tracks_by_disc[disc_str] = []
                tracks_by_disc[disc_str].append(track_num)
            except (ValueError, TypeError):
                continue

    for disc, tracks in sorted(tracks_by_disc.items()):
        if not tracks:
            continue
            
        sorted_tracks = sorted(list(set(tracks)))
        
        if sorted_tracks[0] != 1:
            warnings.add("[Track Numbering Start]")
        
        expected_tracks = list(range(sorted_tracks[0], sorted_tracks[-1] + 1))
        missing_tracks = set(expected_tracks) - set(sorted_tracks)
        
        if missing_tracks:
            warnings.add("[Track Gap]")

    return sorted(list(warnings))

def check_missing_tags(files_metadata: List[Dict]) -> List[str]:
    """Checks for missing essential metadata tags."""
    warnings = set()
    for md in files_metadata:
        if not md.get('title'):
            warnings.add("[Missing Title]")
        if not md.get('artist'):
            warnings.add("[Missing Artist]")
        if not md.get('album'):
            warnings.add("[Missing Album]")
        if not md.get('albumartist'):
            warnings.add("[Missing Album Artist]")
    return sorted(list(warnings))

def check_inconsistent_album_tags(files_metadata: List[Dict]) -> List[str]:
    """Checks for inconsistent album tags within the same folder."""
    warnings = set()
    album_tags = {md.get('album') for md in files_metadata if md.get('album')}
    if len(album_tags) > 1:
        warnings.add("[Inconsistent Album]")
    return sorted(list(warnings))

def plan_file_renames(info: Dict, final_folder_name: str) -> List[Tuple[str, str]]:
    """Creates a plan to rename files within a folder based on metadata."""
    file_rename_plan = []
    has_disc = any(md.get('disc') for md in info['files_metadata'])
    has_no_disc = any(not md.get('disc') for md in info['files_metadata'])
    
    if has_disc and has_no_disc:
        return []

    proposed_new_filenames = set()
    for md in info['files_metadata']:
        old_filename = md['filename']
        track, title, artist = md.get('track'), md.get('title'), md.get('artist')

        if not track or not title:
            continue

        track_num = str(track).zfill(2)
        disc_num = str(md.get('disc')) if has_disc else ''
        _, ext = os.path.splitext(old_filename)
        
        s_title = sanitize_filename(title, is_path_component=True)
        s_artist = sanitize_filename(artist, is_path_component=True) if artist else ''
        
        if has_disc:
            base_name = f"{disc_num}-{track_num} {s_artist} - {s_title}" if s_artist else f"{disc_num}-{track_num} - {s_title}"
        else:
            base_name = f"{track_num} {s_artist} - {s_title}" if s_artist else f"{track_num} - {s_title}"
        
        new_filename = f"{base_name}{ext}"
        if len(os.path.join(final_folder_name, new_filename).encode('utf-8')) > PATH_LENGTH_LIMIT_BYTES:
            base_name = f"{disc_num}-{track_num} - {s_title}" if has_disc else f"{track_num} - {s_title}"
        
        new_filename = f"{base_name}{ext}"
        if len(os.path.join(final_folder_name, new_filename).encode('utf-8')) > PATH_LENGTH_LIMIT_BYTES:
            base_name = f"{disc_num}-{track_num}" if has_disc else track_num

        new_filename = f"{base_name}{ext}"
        final_base_name = base_name
        counter = 1
        while new_filename.lower() in proposed_new_filenames:
            new_filename = f"{final_base_name} ({counter}){ext}"
            counter += 1
        proposed_new_filenames.add(new_filename.lower())

        if old_filename != new_filename:
            old_path = os.path.join(info['path'], old_filename)
            new_path = os.path.join(info['path'], new_filename)
            file_rename_plan.append((old_path, new_path))
            
    return file_rename_plan

def organize_music_folders(root_folder: str, check_only: bool = False, force_yes: bool = False, force_no: bool = False):
    """Scans and organizes music folders and files."""
    general_warnings: List[str] = []
    warnings_by_album: Dict[str, List[str]] = {}
    
    if not os.path.isdir(root_folder):
        print(f"Error: The specified folder does not exist: {root_folder}"); return

    print("--- Phase 1: Analyzing Folders & Potential Names ---")
    
    root_folder = os.path.abspath(root_folder)
    folder_info = [] 

    for dirpath, dirnames, filenames in os.walk(root_folder):
        dirpath = os.path.abspath(dirpath)
        if dirpath == root_folder: continue

        is_true_container = False
        if dirnames:
            for subfolder_name in dirnames:
                try:
                    subfolder_path = os.path.join(dirpath, subfolder_name)
                    if any(f.lower().endswith(SUPPORTED_EXTENSIONS) for f in os.listdir(subfolder_path)):
                        is_true_container = True; break
                except OSError: continue

        if is_true_container:
            parent_name = os.path.basename(dirpath)
            choice = 'n' if check_only or force_no else 'y' if force_yes else ''
            if not choice:
                try: choice = input(f"\nContainer folder '{parent_name}' found. Flatten? (y/n): ").lower()
                except (EOFError, KeyboardInterrupt): print("\nCancelled."); choice = 'n'
            
            if choice == 'y':
                if flatten_container_folder(dirpath, dirnames):
                    dirnames[:], filenames = [], os.listdir(dirpath)
                    info = analyze_album_folder(dirpath, filenames)
                    if info: folder_info.append(info)
                continue
            else:
                general_warnings.append(f"[Container Folder] '{parent_name}' was skipped.")
                dirnames[:]=[]
                continue
        
        info = analyze_album_folder(dirpath, filenames)
        if info: folder_info.append(info)

    # --- Deeper Analysis for Duplicates ---
    for info in folder_info:
        info['base_name'] = sanitize_filename(info['album'])
    
    album_title_counts = Counter(info['album'] for info in folder_info)
    duplicate_album_titles = {album for album, count in album_title_counts.items() if count > 1}

    for info in folder_info:
        if info['album'] in duplicate_album_titles and info['year']:
            info['base_name'] = f"{info['base_name']} ({info['year']})"

    potential_base_names = [info['base_name'] for info in folder_info]
    base_name_counts = Counter(potential_base_names)
    base_names_to_number = {name for name, count in base_name_counts.items() if count > 1}

    print("\n--- Phase 2: Planning Renames & Final Checks ---")
    
    folder_rename_plan, file_rename_plan = [], []
    proposed_new_paths = set()
    numbering_counters = Counter()
    folder_info.sort(key=lambda x: x['path'])

    for info in folder_info:
        base_name = info['base_name']
        final_name = f"{base_name} ({numbering_counters[base_name] + 1})" if base_name in base_names_to_number else base_name
        if base_name in base_names_to_number: numbering_counters[base_name] += 1
            
        parent_dir = os.path.dirname(info['path'])
        final_path = os.path.join(parent_dir, final_name)
        
        current_warnings = []
        if not info['has_images']:
            current_warnings.append("[No Image]")
        
        if any(md.get('track') == '0' or md.get('disc') == '0' for md in info['files_metadata']):
            current_warnings.append("[Zero Metadata]")

        if any(md.get('invalid_year_tag') for md in info['files_metadata']):
            current_warnings.append("[Invalid Year]")
        
        current_warnings.extend(check_track_gaps(info['files_metadata']))
        current_warnings.extend(check_cover_art(info['files_metadata']))
        current_warnings.extend(check_missing_tags(info['files_metadata']))
        current_warnings.extend(check_inconsistent_album_tags(info['files_metadata']))

        all_discs = [md.get('disc') for md in info['files_metadata']]
        has_disc, has_no_disc = any(d for d in all_discs), any(d is None for d in all_discs)

        if has_disc and has_no_disc:
            current_warnings.append("[Inconsistent Disc #]")
        elif has_disc and not has_no_disc and len(set(all_discs)) == 1:
            if check_only:
                current_warnings.append("[Redundant Disc #]")
            else:
                remove_redundant_disc_tags(info, final_name)
        
        track_disc_pairs = [(md.get('track'), md.get('disc')) for md in info['files_metadata'] if md.get('track')]
        if any(count > 1 for count in Counter(track_disc_pairs).values()):
            current_warnings.append("[Duplicate Track]")

        if current_warnings:
            warnings_by_album[final_name] = sorted(list(set(current_warnings)))

        if "[Track Gap]" in current_warnings or "[Duplicate Track]" in current_warnings:
            print(f"  -> Skipping file renames for '{final_name}' due to track gap or duplicate tracks.")
        else:
            planned_files = plan_file_renames(info, final_name)
            if planned_files:
                file_rename_plan.extend(planned_files)
                for old_f, new_f in planned_files:
                    print(f"  Plan file: '{os.path.basename(old_f)}' -> '{os.path.basename(new_f)}'")

        is_being_renamed = info['path'] != final_path
        if is_being_renamed:
            if os.path.isdir(parent_dir) and final_name in os.listdir(parent_dir) or final_path in proposed_new_paths:
                print(f"  [Conflict] Folder '{final_name}' already exists. Skipping rename for '{os.path.basename(info['path'])}'.")
                continue
            folder_rename_plan.append((info['path'], final_path))
            proposed_new_paths.add(final_path)
            print(f"Plan folder: '{os.path.basename(info['path'])}' -> '{final_name}'")
        else:
            print(f"OK:   '{os.path.basename(info['path'])}' is already correct.")

    if not folder_rename_plan and not file_rename_plan and not general_warnings and not warnings_by_album:
        print("\nScan complete. No changes needed.")
    elif check_only:
        print("\nCheck-only mode is active. No files or folders will be changed.")
        print("Scan complete.")
    else:
        print("\n--- Phase 3: Executing Changes ---")
        
        if file_rename_plan:
            print("\nStep 1: Renaming files...")
            for old_path, new_path in file_rename_plan:
                try:
                    os.rename(old_path, new_path)
                    print(f"  Renamed file: '{os.path.basename(old_path)}' -> '{os.path.basename(new_path)}'")
                except OSError as e: print(f"  Error renaming file '{os.path.basename(old_path)}': {e}")

        if folder_rename_plan:
            print("\nStep 2: Renaming folders...")
            folder_rename_plan.sort(key=lambda x: len(x[0]), reverse=True)
            for old_path, new_path in folder_rename_plan:
                try:
                    os.rename(old_path, new_path)
                    print(f"  Renamed folder: '{os.path.basename(old_path)}' -> '{os.path.basename(new_path)}'")
                except OSError as e: print(f"  Error renaming folder '{os.path.basename(old_path)}': {e}")

        print("\nOrganization complete!")

    if general_warnings or warnings_by_album:
        print("\n--- Phase 4: Warnings Found ---")
        for warning in sorted(general_warnings):
            print(warning)
        for album_name, tags in sorted(warnings_by_album.items()):
            tags_str = ", ".join(tags)
            print(f"{tags_str} In '{album_name}'")

if __name__ == "__main__":
    args = sys.argv[1:]
    check_only_flags, force_yes_flags, force_no_flags = ['-c', '--check'], ['-y', '--force-yes'], ['-n', '--force-no']
    check_only_mode = any(flag in args for flag in check_only_flags)
    force_yes_mode = any(flag in args for flag in force_yes_flags)
    force_no_mode = any(flag in args for flag in force_no_flags)
    
    args = [arg for arg in args if arg not in check_only_flags + force_yes_flags + force_no_flags]
    target_folder = args[0] if args else input("Enter path to music folder: ")

    if check_only_mode: print(">>> Running in Check-Only Mode <<<")
    if force_yes_mode: print(">>> Forcing 'Yes' to all flatten prompts <<<")
    if force_no_mode: print(">>> Forcing 'No' to all flatten prompts <<<")
        
    organize_music_folders(target_folder, check_only=check_only_mode, force_yes=force_yes_mode, force_no=force_no_mode)