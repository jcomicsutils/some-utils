import random
from midiutil import MIDIFile
from datetime import datetime

def main():
    # Prompt for BPM with default value 120
    bpm_input = input("Enter BPM (default 120): ")
    try:
        bpm = int(bpm_input) if bpm_input.strip() != "" else 120
    except ValueError:
        print("Invalid BPM input. Using default BPM of 120.")
        bpm = 120

    # Prompt for duration with default value 30.0 seconds
    duration_input = input("Enter total duration in seconds (default 30.0): ")
    try:
        total_duration_sec = float(duration_input) if duration_input.strip() != "" else 30.0
    except ValueError:
        print("Invalid duration input. Using default duration of 30.0 seconds.")
        total_duration_sec = 30.0

    # Convert total duration from seconds to beats (beats = seconds * (bpm / 60))
    total_beats = total_duration_sec * (bpm / 60.0)

    # Create a MIDI file with one track
    track = 0
    mid = MIDIFile(1)
    mid.addTempo(track, 0, bpm)

    note_time = 0.0  # in beats
    # Generate notes until the total beats are reached
    while note_time < total_beats:
        pitch = random.randint(21, 108)  # Full piano range
        note_duration_sec = random.uniform(0.1, 0.5)  # duration in seconds
        note_duration_beats = note_duration_sec * (bpm / 60.0)  # convert duration to beats
        
        # Adjust note duration if it would exceed the total length
        if note_time + note_duration_beats > total_beats:
            note_duration_beats = total_beats - note_time
            if note_duration_beats < 0.001:
                break
        
        velocity = random.randint(50, 100)  # random velocity
        mid.addNote(track, 0, pitch, note_time, note_duration_beats, velocity)
        
        # Increment note_time by a random gap (converted to beats)
        gap_sec = random.uniform(0.1, 0.3)
        gap_beats = gap_sec * (bpm / 60.0)
        # Ensure a minimal gap to maintain strictly increasing times
        gap_beats = max(gap_beats, 0.001)
        note_time += gap_beats
        
        # Add a tiny epsilon to guarantee strictly increasing event times
        note_time += 0.0001

    # Determine the final event time and schedule a dummy note slightly after it
    final_time = max(note_time, total_beats)
    dummy_time = final_time + 0.01
    mid.addNote(track, 0, 60, dummy_time, 0.01, 0)  # dummy note (inaudible)

    # Create a timestamp for the filename to avoid overwriting
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"random_midi_1_{timestamp}.mid"

    # Save the MIDI file
    with open(output_filename, "wb") as midi_file:
        mid.writeFile(midi_file)

    print(f"MIDI file '{output_filename}' has been created with BPM={bpm} and duration={total_duration_sec} seconds.")

if __name__ == '__main__':
    main()