from midiutil import MIDIFile
import random
import math
from datetime import datetime

def microtonal_pitch(base_note, bend_amount=0.25):
    """Generate microtonal pitch bend events (approximation)"""
    return base_note + bend_amount * random.choice([-1, 1])

def create_dissonant_composition(output_file, bpm=60, duration_seconds=120):
    beats_per_second = bpm / 60
    total_beats = max(1, duration_seconds * beats_per_second)  # Ensure at least 1 beat
    min_spacing = max(0.5, 60 / bpm)  # Ensure spacing is reasonable at low BPM

    midi = MIDIFile(2)
    time = 0
    notes_added = {0: 0, 1: 0}

    for track in [0, 1]:
        midi.addTrackName(track, time, f"Atonal Piano {track+1}")
        midi.addTempo(track, time, max(1, bpm))  # Prevent BPM from going too low
        midi.addProgramChange(track, 0, 0, random.choice([0, 16, 19]))

    current_beat = 0
    while current_beat < total_beats:
        section_type = random.randint(0, 6)
        section_length = random.uniform(min_spacing, min(10, total_beats - current_beat))

        # CHAOTIC CLUSTERS
        if section_type == 0:
            cluster_duration = random.uniform(0.5, 2.5)
            num_clusters = random.randint(1, 6)
            for _ in range(num_clusters):
                root = random.randint(24, 96)
                cluster = [
                    root + interval 
                    for interval in random.sample([0, 1, 2, 3, 4, 5], random.randint(3, 6))
                ]
                velocity = random.randint(20, 127)
                for note in cluster:
                    for track in [0, 1]:
                        midi.addNote(track, 0, int(microtonal_pitch(note)), 
                                     current_beat + random.uniform(0, 0.5), 
                                     max(0.1, cluster_duration * random.uniform(0.5, 1.5)),
                                     velocity)
                        notes_added[track] += 1
            current_beat += cluster_duration

        # POLYRHYTHMIC TRITONES
        elif section_type == 1:
            duration = random.uniform(0.5, 2)
            base_note = random.randint(40, 80)
            interval = random.choice([[0, 6], [1, 8], [6, 11], [4, 7]])
            for track in [0, 1]:
                midi.addNote(track, 0, base_note + interval[0], current_beat, duration, random.randint(50, 110))
                midi.addNote(track, 0, base_note + interval[1], current_beat + 0.125, duration, random.randint(50, 110))
                notes_added[track] += 2
            current_beat += duration

        # STOCHASTIC SILENCE (Ensures beats progress even if silent)
        elif section_type == 3:
            silence_duration = random.uniform(min_spacing, min(4, total_beats - current_beat))
            current_beat += silence_duration

        # GLISSANDO MADNESS
        elif section_type == 5:
            for i in range(random.randint(12, 48)):
                note = random.randint(40, 80) + i
                midi.addNote(0, 0, note, current_beat + i * 0.03125, 0.03125, max(10, 127 - i * 5))
                notes_added[0] += 1
            current_beat += 1

        # Ensure we always reach the total duration
        current_beat = min(current_beat + section_length, total_beats)

    # Ensure at least one note per track
    for track in range(2):
        if notes_added[track] == 0:
            print(f"Warning: No notes in track {track}. Adding a placeholder note.")
            midi.addNote(track, 0, 60, total_beats - 1, 0.5, 1)  # Silent note
            notes_added[track] += 1

    # Save file safely
    try:
        with open(output_file, "wb") as f:
            midi.writeFile(f)
    except Exception as e:
        print(f"Error saving MIDI file: {e}")

# User input
bpm = int(input("Enter BPM (1-300): "))
duration = float(input("Enter duration in seconds: "))

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
output_file = f"random_midi_-1_{timestamp}.mid"

print(f"Creating {duration}s of chaos at {bpm} BPM...")
create_dissonant_composition(output_file, bpm, duration)
print(f"Chaos saved to {output_file}")
