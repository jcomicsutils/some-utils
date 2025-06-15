# some-utils

## About This Repository

This repository, `some-utils`, is a collection of various utility scripts and web-based tools designed for file management, data conversion, media manipulation, and content generation. The tools range from simple command-line scripts to interactive GUI applications and web pages.

## File Index

The repository is organized into several categories based on file type and function.

---

### Python Scripts (GUI Applications)

These are standalone applications built with Tkinter that provide a graphical user interface for ease of use.

#### **ArchiveUploader.py**
- **Description**: A tool to upload multiple folders to [archive.org](https://archive.org). Each selected folder is uploaded as a new, separate item on the archive.
- **How to Use**:
    1.  Fill in your `IA_ACCESS_KEY` and `IA_SECRET_KEY`.
    2.  Run the script.
    3.  Use the "Select Folders" button or drag-and-drop folders onto the listbox.
    4.  Set the number of concurrent uploads.
    5. Progress will appear in terminal.
    6.  Click "Start Upload" to begin the process. Logs and errors will appear in the respective text boxes.

#### **ArchiveUploaderToItem.py**
- **Description**: Similar to `ArchiveUploader.py`, but this version uploads files into a single, pre-existing item on [archive.org](https://archive.org).
- **How to Use**:
    1. Run the script.
    2. Check the "Upload to Existing Item" box.
    3.  Enter the identifier (not the link) of the existing `archive.org` item.
    4.  Select the folders you wish to upload.
    5.  Click "Start Upload".

#### **AudioPowerSet.py**
- **Description**: Generates all possible audio combinations from a directory of sound files. For a folder containing files A, B, and C, it will create mixes of (A+B), (A+C), (B+C), and (A+B+C).
- **How to Use**:
    1.  Select an input directory containing your source audio files.
    2.  Select an output directory where the mixed files will be saved.
    3.  Click "Start Mixing".

#### **FileUploader.py**
- **Description**: A multi-service file uploader that can upload files to [catbox](https://catbox.moe/), [lain.la](https://pomf.lain.la/), [fileditch](https://fileditch.com/), and [files.vc](https://files.vc/) simultaneously.
- **How to Use**:
    1. Configure your `ACCOUNT_ID` and `API_KEY` for `files.vc` and `CATBOX_USERHASH` for `catbox` directly in the script.
    2. Run the application.
    3. Select the services you wish to upload to.
    4. Use the "Select Folder" button to choose the directory containing files to upload.
    5. Click "Start Upload". The links for successfully uploaded files will be displayed.

#### **MergeAudioFiles.py**
- **Description**: Merges all audio files within a specified directory into a single audio file, playing them simultaneously. It can optionally process subfolders as well.
- **How to Use**:
    1. Run the script.
    2. Select a root directory.
    3. Check "Include Subfolders" if you want to process directories recursively.
    4. Click "Start Merging". Each folder's audio files will be mixed into a single `mixed_output.flac`.

#### **MoveFilesByList.py**
- **Description**: A flexible tool to move files or folders from a source to a destination based on a list. It offers three modes: direct file move, direct folder move, and a "selective" mode that moves a parent folder only if it contains the exact files specified.
- **How to Use**:
    1. Select the "Source Folder" and "Destination Folder".
    2. Choose the operation mode:
        * **Move Files**: Paste a list of filenames (with extensions).
        * **Move Folders**: Paste a list of folder names.
        * **Selective Move**: Paste a list where each folder name is followed by the filenames it should contain.
        ```
        folder1
        file
        another file
        file2
        ...
        folder2
        file in folder2
        second file in folder2
        another file in folder2
        ...
        ```
    3. Click "Perform Move Operation" to see a log of the actions taken.

#### **Other GUI Utilities**
- **`ConvertToFLAC.py`**: A simple tool that uses FFmpeg to convert all audio files in a selected directory to high-quality FLAC format, deleting the originals upon success.
- **`CreateAFile.py`**: A minimalist utility to create a new, empty file with a specified name in a chosen folder.
- **`DeleteFilesByString.py`**: Deletes files from a directory if their filename contains a specified string.
- **`DuplicateFile.py`**: Creates a specified number of copies of a single file, appending a suffix and number to each.
- **`MoveFilesByString.py`**: Moves files from a source to a destination folder if their filename contains a specified string.
- **`RemoveStringFromFilename.py`**: Scans a folder and removes a specified substring from all filenames.
- **`RenameZip.py`**: Renames `.zip` and `.7z` archives to match the name of the single top-level folder contained within them.
- **`SplitMP3Renamer.py`**: Fixes filenames for MP3s split by tools, renaming files like `song.mp3.001` to `song.001.mp3`.

---

### Python Scripts (Command-Line / Simple Utilities)

These scripts are designed to be run from the command line and do not have a graphical interface.

- **`PatternGenerator.py`**: Generates a random, tile-based pattern and saves it as a PNG image.
- **How to Use**: Run from the command line with optional arguments to customize the output.
    ```bash
    python PatternGenerator.py [--width <pixels>] [--height <pixels>] [--tile_size <pixels>] [--output <filename.png>]
    ```
    - `--width`: The width of the output image. Default: 1920.
    - `--height`: The height of the output image. Default: 1080.
    - `--tile_size`: The size of each pattern tile. Default: 60.
    - `--output`: The name of the output file. Default: `pattern.png`.

- **`RandomMIDI-1.py`, `RandomMIDI0.py`, `RandomMIDI1.py`, `RandomMIDI2.py`**: A suite of scripts for generating random and dissonant MIDI music files.
- **How to Use (`RandomMIDI-1.py`, `RandomMIDI0.py`, `RandomMIDI1.py`)**: Run the desired script from the command line. A MIDI file (e.g., `random.mid`) will be created in the same directory.
    ```bash
    python RandomMIDI1.py
    ```
- **How to Use (`RandomMIDI2.py`)**: This script is run from the command line and accepts several arguments to customize the generated MIDI file.
  ```bash
  python RandomMIDI2.py <length> [options]
  ```
  - **`<length>`** (Required): The first argument must be an integer specifying the length of the composition in bars.
  - **Options** (Optional):
      - `m`: Enables microtonal mode, creating notes between standard pitches.
      - `p`: Assigns a random instrument to each *chord*.
      - `pp`: Assigns a random instrument to each individual *note*.
      - `bpm{int}`: Sets the tempo in beats per minute (e.g., `bpm120`).
      - `i{int}`: Selects a specific instrument by its index (a list of instruments and their indexes can be found in the script).

  **Note**: You cannot use the `p` or `pp` options at the same time as the `i` option.

  **Example Usage**:
  ```bash
  # Create a 32-bar microtonal piece at 140 BPM with a random instrument per note
  python RandomMIDI2.py 32 m pp bpm140

  # Create a 16-bar piece using the "Electric Grand Piano" (instrument index 2)
  python RandomMIDI2.py 16 i2
  ``` 

- **`RYMFromFiles.py`**: Scans a directory of audio files, extracts metadata (artist, album), and formats it into a list suitable for posting on Rate Your Music (RYM).

---

### HTML/JavaScript Tools

These are browser-based tools. Simply open the `.html` file to use them.

- **`DataSonification.html`**: Converts any file into sound by mapping its raw bytes to frequencies and tones. You can select oscillator types, set tone durations, and save the result as a WAV file.
- **`IndexEditor.html`**: A web interface for editing a specific JavaScript data structure used in the `MusicIndex.html` and `ShowIndex.html` pages.
- **`IndexSorter.html`**: Alphabetically sorts the categories and items within the `linksData` array structure used by the index pages.
- **`ListDeduplicator.html`**: A simple utility to paste a list and identify or remove duplicate lines.
- **`ListToFafda.html`**: Converts a JSON list into a specific YAML format required by the `fafda` tool.
- **`NoiseGenerator.html`**: An interactive, browser-based noise synthesizer with a wide range of parameters for generating complex and chaotic sounds.
- **`PatternGenerator.html`**: A web-based version of the pattern generation script, allowing for interactive creation of unique visual patterns.
- **`RandomJapaneseStrings.html`**: Generates a specified number of random strings composed of Japanese characters (Hiragana, Katakana, Kanji).
- **`RYMTitleExtractor.html`**: Extracts all release titles from the HTML source code of a Rate Your Music (RYM) artist page.
- **`RYMToIndex.html` / `RYMToHyperlink.html`**: Tools for converting RYM-formatted lists into other formats (HTML index or standard hyperlinks).
- **`StochasticMusicGenerator.html`**: A browser-based tool for generating stochastic music with various effects and controls.
- **`TextToMIDI.html`**: Converts text input into a MIDI file, which can be played and visualized directly in the browser.
- **`TitlesAndLinksToRYM.html`**: Merges a list of titles and a list of URLs into the RYM-formatted hyperlink syntax.
- **`traktJSONtoCSV.html`**: Converts a `watchlist.json` file from Trakt.tv into a CSV file that can be imported into services like TMDb.
