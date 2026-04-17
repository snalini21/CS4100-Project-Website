"""
MIDI Player with Instrument Selection
=======================================
Plays and/or converts MIDI files using FluidSynth + a soundfont.

Install dependencies:
    brew install fluidsynth
    pip install pyfluidsynth mido

Usage:
    # Play with default instrument (piano)
    python3 midi_player.py midi.mid

    # Play with a specific instrument
    python3 midi_player.py midi.mid --instrument violin

    # Play both model outputs back to back
    python3 midi_player.py markov.mid genetic.mid --instrument trumpet

    # Convert to WAV only (no playback)
    python3 midi_player.py midi.mid --wav-only

    # Play AND save WAV
    python3 midi_player.py midi.mid --save-wav --instrument flute

Available instruments: piano, violin, guitar, flute, trumpet, organ
"""

import sys
import argparse
import os
import time
import subprocess
import fluidsynth
import mido

# ─── INSTRUMENT MAP ───────────────────────────────────────────────────────────
# General MIDI program numbers (0-indexed)
INSTRUMENTS = {
    'piano':   0,    # Acoustic Grand Piano
    'violin':  40,   # Violin
    'guitar':  25,   # Acoustic Guitar (steel)
    'flute':   73,   # Flute
    'trumpet': 56,   # Trumpet
    'organ':   19,   # Church Organ
}

SOUNDFONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'GeneralUser-GS.sf2')


# ─── FLUIDSYNTH SETUP ─────────────────────────────────────────────────────────

def init_synth(instrument_name, soundfont_path):
    """Initialize FluidSynth for live playback with the chosen instrument."""
    if not os.path.exists(soundfont_path):
        raise FileNotFoundError(
            f"Soundfont not found at '{soundfont_path}'. Make sure GeneralUser-GS.sf2 is in the midi_audio folder.")

    program = INSTRUMENTS.get(instrument_name.lower())
    if program is None:
        raise ValueError(f"Unknown instrument '{instrument_name}'. Choose from: {', '.join(INSTRUMENTS.keys())}")

    fs = fluidsynth.Synth(samplerate=44100.0)
    fs.start(driver='coreaudio')
    time.sleep(0.5)  # give CoreAudio time to initialize

    sfid = fs.sfload(soundfont_path)
    return fs, sfid, program


# ─── MIDI EVENT SENDER ────────────────────────────────────────────────────────

def send_midi_to_synth(fs, midi_path, sfid, program):
    """Send all note events from all tracks/channels to FluidSynth."""
    mid = mido.MidiFile(midi_path)

    # Register the chosen instrument on every channel (0-15) except 9 (drums)
    for ch in range(16):
        if ch != 9:
            fs.program_select(ch, sfid, 0, program)

    for msg in mid.play():
        ch = getattr(msg, 'channel', 0)
        if msg.type == 'note_on':
            if msg.velocity > 0:
                fs.noteon(ch, msg.note, msg.velocity)
            else:
                fs.noteoff(ch, msg.note)
        elif msg.type == 'note_off':
            fs.noteoff(ch, msg.note)

    # Let last notes ring out
    time.sleep(1.5)


# ─── PLAYBACK ─────────────────────────────────────────────────────────────────

def play_midi(midi_path, instrument_name, soundfont_path):
    """Play a MIDI file using FluidSynth with the selected instrument."""
    print(f"  Instrument : {instrument_name.capitalize()}")
    print(f"  File       : {os.path.basename(midi_path)}")
    print(f"  Playing...")

    fs, sfid, program = init_synth(instrument_name, soundfont_path)
    try:
        send_midi_to_synth(fs, midi_path, sfid, program)
    finally:
        fs.delete()

    print("  Done.")


# ─── WAV EXPORT ───────────────────────────────────────────────────────────────

def midi_to_wav(midi_path, output_path, instrument_name, soundfont_path):
    if not os.path.exists(soundfont_path):
        raise FileNotFoundError(f"Soundfont not found at '{soundfont_path}'")

    program = INSTRUMENTS.get(instrument_name.lower())
    if program is None:
        raise ValueError(f"Unknown instrument '{instrument_name}'.")

    print(f"  Rendering '{os.path.basename(midi_path)}' → '{os.path.basename(output_path)}'...")

    # Inject program change into a temp MIDI file so fluidsynth uses the right instrument
    mid = mido.MidiFile(midi_path)
    for track in mid.tracks:
        for ch in range(16):
            if ch != 9:
                track.insert(0, mido.Message('program_change', channel=ch, program=program, time=0))
        break  # only inject into first track

    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.mid', delete=False) as tmp:
        tmp_path = tmp.name
    mid.save(tmp_path)

    result = subprocess.run([
        'fluidsynth', '-ni', '-g', '1.0',
        '-F', output_path, '-r', '44100',
        soundfont_path, tmp_path
    ], capture_output=True, text=True)

    os.unlink(tmp_path)

    if result.returncode != 0:
        raise RuntimeError(f"fluidsynth CLI failed:\n{result.stderr}")

    print(f"  Saved → {output_path}")


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='Play and/or convert MIDI files with a chosen instrument.'
    )
    parser.add_argument('files', nargs='+', help='MIDI file(s) to process')
    parser.add_argument(
        '--instrument', '-i',
        default='piano',
        choices=list(INSTRUMENTS.keys()),
        help='Instrument to use (default: piano)'
    )
    parser.add_argument(
        '--soundfont', '-sf',
        default=SOUNDFONT,
        help='Path to .sf2 soundfont (default: GeneralUser-GS.sf2 in same folder)'
    )
    parser.add_argument(
        '--wav-only',
        action='store_true',
        help='Convert to WAV only, skip playback'
    )
    parser.add_argument(
        '--save-wav',
        action='store_true',
        help='Play AND save a .wav file alongside the MIDI'
    )
    args = parser.parse_args()

    labels = ['Markov Chain', 'Genetic Algorithm']

    for idx, filepath in enumerate(args.files):
        label = labels[idx] if idx < len(labels) else f'Model {idx + 1}'

        print(f"\n{'─' * 50}")
        print(f"  [{label}]")
        print(f"{'─' * 50}")

        if not os.path.exists(filepath):
            print(f"  Error: file not found — '{filepath}'")
            continue

        wav_path = os.path.splitext(filepath)[0] + f'_{args.instrument}.wav'

        if args.wav_only:
            midi_to_wav(filepath, wav_path, args.instrument, args.soundfont)

        elif args.save_wav:
            midi_to_wav(filepath, wav_path, args.instrument, args.soundfont)
            play_midi(filepath, args.instrument, args.soundfont)

        else:
            play_midi(filepath, args.instrument, args.soundfont)

    print("\nAll done!")


if __name__ == '__main__':
    main()

# LLM USAGE 
# Prompt:
# Used a large language model (Claude) to improve code readability, structure,
# and documentation. Prompts included requests to:
# - Add clear, descriptive comments explaining each section of the code
# - Refactor functions for better organization and modularity
# - Improve naming consistency and overall clarity
# - Provide usage examples and command-line interface guidance
#
# What we implemented:
# - Added structured section headers and inline comments throughout the code
# - Improved function organization (init_synth, playback, WAV export, etc.)
# - Standardized instrument mapping and argument parsing
# - Enhanced docstrings and usage instructions for maintainability
# - Minor refactoring for clarity without changing core functionality
#
# Note:
# The LLM was used only as a coding assistant. All logic, design decisions,
# and final verification were reviewed and approved by the developers.
# 
