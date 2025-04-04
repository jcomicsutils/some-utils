from midiutil import MIDIFile
import random
from datetime import datetime

def create_dissonant_composition(output_file, bpm=60, duration_seconds=120):
    # Calculate total beats needed
    beats_per_second = bpm / 60  # Beats per second
    total_beats = duration_seconds * beats_per_second  # Total beats for the duration
    
    midi = MIDIFile(1)
    track = 0
    time = 0
    midi.addTrackName(track, time, "Atonal Piano")
    midi.addTempo(track, time, bpm)
    midi.addProgramChange(track, 0, 0, 0)

    # Musical parameters
    clusters = [
        [36, 37, 48, 49],  # Low cluster
        [42, 43, 54, 55],  # Mid-low cluster
        [60, 61, 72, 73],  # Middle cluster
        [78, 79, 90, 91]   # High cluster
    ]
    tritones = [[65, 71], [58, 63], [70, 65], [53, 58]]
    chromatic_scales = [list(range(48, 72)), list(range(60, 84)), list(range(36, 60))]  # Chromatic scales in different ranges
    
    current_beat = 0
    while current_beat < total_beats:
        # Add cluster chords (with more variation)
        if random.random() > 0.4:  # 60% chance of clusters
            cluster = random.choice(clusters)
            duration = random.choice([0.25, 0.5, 1, 1.5, 2])
            volume = random.randint(50, 100)
            for note in cluster:
                midi.addNote(track, 0, note + random.randint(-1, 1),  # Slight pitch variation
                           current_beat, duration, volume)
            current_beat += duration
        
        # Add tritone intervals (with rhythmic variation)
        if random.random() > 0.5:  # 50% chance of tritones
            tritone = random.choice(tritones)
            duration = random.choice([0.125, 0.25, 0.5])
            offset = random.choice([0, 0.125, 0.25])  # Rhythmic offset
            midi.addNote(track, 0, tritone[0], current_beat + offset, 
                        duration, random.randint(70, 110))
            midi.addNote(track, 0, tritone[1], current_beat + offset + 0.125, 
                        duration, random.randint(70, 110))
            current_beat += duration + offset
        
        # Add chromatic runs (with more variation)
        if random.random() > 0.7:  # 30% chance of runs
            scale = random.choice(chromatic_scales)
            start_note = random.choice(scale)
            run_length = random.randint(8, 24)
            direction = random.choice([1, -1])  # Ascending or descending
            for i in range(run_length):
                note = start_note + (i * direction)
                if 0 <= note <= 127:  # Ensure note is within MIDI range
                    midi.addNote(track, 0, note, 
                                current_beat + i*0.125, 
                                0.125, random.randint(80, 120))
            current_beat += run_length * 0.125
        
        # Add some silence (with more variation)
        if random.random() > 0.5:  # 50% chance of rest
            rest_duration = random.choice([0.125, 0.25, 0.5, 1, 1.5])
            current_beat += rest_duration

    # Add final cluster collapse (with more variation)
    end_time = total_beats - random.choice([2, 4, 6])  # Random end time
    for velocity in range(40, 120, random.choice([10, 15, 20])):
        cluster = random.choice(clusters)
        spread = random.uniform(0.05, 0.2)  # Random spread
        for note in cluster:
            midi.addNote(track, 0, note, end_time, 
                       random.choice([2, 3, 4]), velocity)
            end_time += spread  # Spread cluster

    # Save file
    with open(output_file, "wb") as f:
        midi.writeFile(f)

# Get user input
bpm = int(input("Enter the BPM (e.g., 40-200): "))
duration_seconds = float(input("Enter the duration in seconds (e.g., 120): "))

# Generate timestamped filename
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_filename = f"random_midi_0_{timestamp}.mid"

# Generate composition
print(f"Creating {duration_seconds} second composition at {bpm} BPM...")
create_dissonant_composition(output_filename, bpm, duration_seconds)
print(f"Done! File saved as {output_filename}")