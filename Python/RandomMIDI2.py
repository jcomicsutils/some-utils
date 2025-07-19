from midiutil import MIDIFile
import random
import sys
import re

# Updated with clearer instrument names and fixed program numbers
INSTRUMENTS = [
    # Pianos
    ("Acoustic Grand Piano", 0),
    ("Bright Acoustic Piano", 1),
    ("Electric Grand Piano", 2),
    ("Honky-tonk Piano", 3),
    ("Electric Piano 1", 4),
    ("Electric Piano 2", 5),
    ("Harpsichord", 6),
    ("Clavinet", 7),
    
    # Chromatic Percussion
    ("Celesta", 8),
    ("Glockenspiel", 9),
    ("Music Box", 10),
    ("Vibraphone", 11),
    ("Marimba", 12),
    ("Xylophone", 13),
    ("Tubular Bells", 14),
    ("Dulcimer", 15),
    
    # Organs
    ("Drawbar Organ", 16),
    ("Percussive Organ", 17),
    ("Rock Organ", 18),
    ("Church Organ", 19),
    ("Reed Organ", 20),
    ("Accordion", 21),
    ("Harmonica", 22),
    ("Tango Accordion", 23),
    
    # Guitars
    ("Acoustic Guitar (nylon)", 24),
    ("Acoustic Guitar (steel)", 25),
    ("Electric Guitar (jazz)", 26),
    ("Electric Guitar (clean)", 27),
    ("Electric Guitar (muted)", 28),
    ("Overdriven Guitar", 29),
    ("Distortion Guitar", 30),
    ("Guitar Harmonics", 31),
    
    # Bass
    ("Acoustic Bass", 32),
    ("Electric Bass (finger)", 33),
    ("Electric Bass (pick)", 34),
    ("Fretless Bass", 35),
    ("Slap Bass 1", 36),
    ("Slap Bass 2", 37),
    ("Synth Bass 1", 38),
    ("Synth Bass 2", 39),
    
    # Strings & Orchestral
    ("Violin", 40),
    ("Viola", 41),
    ("Cello", 42),
    ("Contrabass", 43),
    ("Tremolo Strings", 44),
    ("Pizzicato Strings", 45),
    ("Orchestral Harp", 46),
    ("Timpani", 47),
    
    # Ensemble
    ("String Ensemble 1", 48),
    ("String Ensemble 2", 49),
    ("Synth Strings 1", 50),
    ("Synth Strings 2", 51),
    ("Choir Aahs", 52),
    ("Voice Oohs", 53),
    ("Synth Voice", 54),
    ("Orchestra Hit", 55),
    
    # Brass
    ("Trumpet", 56),
    ("Trombone", 57),
    ("Tuba", 58),
    ("Muted Trumpet", 59),
    ("French Horn", 60),
    ("Brass Section", 61),
    ("Synth Brass 1", 62),
    ("Synth Brass 2", 63),
    
    # Reed & Pipe
    ("Soprano Sax", 64),
    ("Alto Sax", 65),
    ("Tenor Sax", 66),
    ("Baritone Sax", 67),
    ("Oboe", 68),
    ("English Horn", 69),
    ("Bassoon", 70),
    ("Clarinet", 71),
    
    # Flutes
    ("Piccolo", 72),
    ("Flute", 73),
    ("Recorder", 74),
    ("Pan Flute", 75),
    ("Blown Bottle", 76),
    ("Shakuhachi", 77),
    ("Whistle", 78),
    ("Ocarina", 79),
    
    # Synth Lead
    ("Lead 1 (square)", 80),
    ("Lead 2 (sawtooth)", 81),
    ("Lead 3 (calliope)", 82),
    ("Lead 4 (chiff)", 83),
    ("Lead 5 (charang)", 84),
    ("Lead 6 (voice)", 85),
    ("Lead 7 (fifths)", 86),
    ("Lead 8 (bass + lead)", 87),
    
    # Ethnic
    ("Sitar", 104),
    ("Banjo", 105),
    ("Shamisen", 106),
    ("Koto", 107),
    ("Kalimba", 108),
    ("Bagpipe", 109),
    ("Fiddle", 110),
    ("Shanai", 111),
    
    # Percussive
    ("Tinkle Bell", 112),
    ("Agogo", 113),
    ("Steel Drums", 114),
    ("Woodblock", 115),
    ("Taiko Drum", 116),
    ("Melodic Tom", 117),
    ("Synth Drum", 118),
    ("Reverse Cymbal", 119),
    
    # Sound Effects
    ("Guitar Fret Noise", 120),
    ("Breath Noise", 121),
    ("Seashore", 122),
    ("Bird Tweet", 123),
    ("Telephone Ring", 124),
    ("Helicopter", 125),
    ("Applause", 126),
    ("Gunshot", 127)
]

def generate_dissonant_composition(output_file="midi.mid", length_beats=16, 
                                  microtonal=False, instrument_mode=0, tempo=90,
                                  specific_instrument=None):
    midi = MIDIFile(1)
    track = 0
    time = 0
    track_name = "midi"
    if microtonal:
        track_name += " Microtonal midi"
    if instrument_mode > 0:
        track_name += f" Multi-Instrument (Level {instrument_mode})"
    if specific_instrument is not None:
        instrument_name = next((name for name, num in INSTRUMENTS if num == specific_instrument), "Unknown")
        track_name += f" [{instrument_name}]"
    midi.addTrackName(track, time, track_name)
    midi.addTempo(track, time, tempo)

    OCTAVE_RANGE = (3, 6)
    CHORD_LENGTHS = [0.25, 0.5, 0.75, 1, 1.5]
    DISSONANT_INTERVALS = [1, 2, 6, 10, 11]
    current_channel = 0

    if microtonal:
        DISSONANT_INTERVALS += [0.5, 1.5, 6.5, 10.5]

    current_time = 0
    while current_time < length_beats:
        root = random.randint(12 * OCTAVE_RANGE[0], 12 * OCTAVE_RANGE[1])
        if microtonal and random.random() < 0.3:
            root += random.choice([0.25, 0.5, 0.75])

        chord_notes = [root]
        for _ in range(random.randint(1, 3)):
            interval = random.choice(DISSONANT_INTERVALS)
            chord_notes.append(root + interval if random.choice([True, False]) else root - interval)

        if microtonal:
            chord_notes = [max(0.0, min(127.0, n)) for n in chord_notes]
        else:
            chord_notes = list(set([max(0, min(127, int(n))) for n in chord_notes]))

        duration = random.choice(CHORD_LENGTHS)
        if current_time + duration > length_beats:
            duration = length_beats - current_time

        layers = random.randint(2, 3) if instrument_mode == 2 else 1

        # Instrumentation logic
        if microtonal:
            for note in chord_notes:
                channel = current_channel % 16
                current_channel += 1
                midi_note = int(note)
                fractional = note - midi_note
                bend_value = 8192 + int(fractional * 4096)
                midi.addPitchWheelEvent(track, channel, current_time, max(0, min(16383, bend_value)))
                
                if instrument_mode > 0:
                    _, program = random.choice(INSTRUMENTS)
                    midi.addProgramChange(track, channel, current_time, program)
                elif specific_instrument is not None:
                    midi.addProgramChange(track, channel, current_time, specific_instrument)
                
                midi.addNote(track, channel, midi_note, current_time, duration, random.randint(60, 100))
        else:
            if instrument_mode == 1:
                channel = current_channel % 16
                current_channel += 1
                program = random.choice(INSTRUMENTS)[1]
                midi.addProgramChange(track, channel, current_time, program)
                for note in chord_notes:
                    midi.addNote(track, channel, note, current_time, duration, random.randint(60, 100))
            elif instrument_mode == 2:
                for note in chord_notes:
                    channel = current_channel % 16
                    current_channel += 1
                    _, program = random.choice(INSTRUMENTS)
                    midi.addProgramChange(track, channel, current_time, program)
                    midi.addNote(track, channel, note, current_time, duration, random.randint(60, 100))
            else:
                channel = 0
                if specific_instrument is not None:
                    midi.addProgramChange(track, channel, current_time, specific_instrument)
                for note in chord_notes:
                    midi.addNote(track, channel, note, current_time, duration, random.randint(60, 100))

        current_time += duration

    with open(output_file, "wb") as f:
        midi.writeFile(f)

if __name__ == "__main__":
    filename = f"random_midi_2_{random.randint(0, 9999999):09}.mid"
    length = 16
    microtonal = False
    instrument_mode = 0
    tempo = 90
    specific_instrument = None
    
    if len(sys.argv) > 1:
        length = int(sys.argv[1])
    if len(sys.argv) > 2:
        for arg in sys.argv[2:]:
            arg_lower = arg.lower()
            if arg_lower.startswith('bpm'):
                try:
                    tempo = max(1, int(re.sub('[^0-9]', '', arg_lower[3:])))
                except ValueError:
                    print(f"Invalid BPM: {arg[3:]}, using 90")
            elif arg_lower == 'm':
                microtonal = True
            elif arg_lower.startswith('i'):
                if instrument_mode != 0:
                    print("Error: Cannot combine instrument selection with p/pp modes")
                    sys.exit(1)
                try:
                    idx = int(arg_lower[1:])
                    if 0 <= idx < len(INSTRUMENTS):
                        specific_instrument = INSTRUMENTS[idx][1]
                    else:
                        print(f"Invalid instrument index {idx}, must be 0-{len(INSTRUMENTS)-1}")
                        sys.exit(1)
                except ValueError:
                    print(f"Invalid instrument format: {arg}")
                    sys.exit(1)
            elif arg_lower == 'p':
                if specific_instrument is not None:
                    print("Error: Cannot combine p/pp modes with instrument selection")
                    sys.exit(1)
                instrument_mode = max(instrument_mode, 1)
            elif arg_lower == 'pp':
                if specific_instrument is not None:
                    print("Error: Cannot combine p/pp modes with instrument selection")
                    sys.exit(1)
                instrument_mode = 2
    
    generate_dissonant_composition(
        filename, 
        length, 
        microtonal, 
        instrument_mode, 
        tempo, 
        specific_instrument
    )
    
    instrument_info = ""
    if specific_instrument is not None:
        instrument_name = next((name for name, num in INSTRUMENTS if num == specific_instrument), "Unknown")
        instrument_info = f" with {instrument_name}"
    
    print(f"Generated {['','p','pp'][instrument_mode]}{' microtonal ' if microtonal else ' '}composition{instrument_info} at {tempo} BPM: {filename}")