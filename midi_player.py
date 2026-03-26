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

try:
    import fluidsynth
except ImportError:
    print("Missing dependency. Run:  brew install fluidsynth && pip install pyfluidsynth")
    sys.exit(1)

try:
    import mido
except ImportError:
    print("Missing dependency. Run:  pip install mido")
    sys.exit(1)

# ─── INSTRUMENT MAP ───────────────────────────────────────────────────────────
# General MIDI program numbers (0-indexed)
INSTRUMENTS = {
    'piano':    0,    # Acoustic Grand Piano
    'violin':   40,   # Violin
    'guitar':   25,   # Acoustic Guitar (steel)
    'flute':    73,   # Flute
    'trumpet':  56,   # Trumpet
    'organ':    19,   # Church Organ
}

SOUNDFONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'GeneralUser-GS.sf2')

# ─── FLUIDSYNTH SETUP ─────────────────────────────────────────────────────────

def init_synth(instrument_name, soundfont_path, driver='coreaudio', output_file=None, audio_type=None):
    """Initialize FluidSynth with the chosen instrument and driver."""
    if not os.path.exists(soundfont_path):
        print(f"Error: soundfont not found at '{soundfont_path}'")
        print("Make sure GeneralUser-GS.sf2 is in the same folder as this script.")
        sys.exit(1)

    program = INSTRUMENTS.get(instrument_name.lower())
    if program is None:
        print(f"Unknown instrument '{instrument_name}'. Choose from: {', '.join(INSTRUMENTS.keys())}")
        sys.exit(1)

    fs = fluidsynth.Synth(samplerate=44100.0)

    if output_file:
        fs.start(driver='file', outputfile=output_file, audio_type=audio_type or 'wav')
    else:
        fs.start(driver=driver)
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
        # Use the message's own channel so both hands play correctly
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

    fs, sfid, program = init_synth(instrument_name, soundfont_path, driver='coreaudio')
    try:
        send_midi_to_synth(fs, midi_path, sfid, program)
    finally:
        fs.delete()

    print("  Done.")


# ─── WAV EXPORT ───────────────────────────────────────────────────────────────

def midi_to_wav(midi_path, output_path, instrument_name, soundfont_path):
    """Render a MIDI file to a WAV using FluidSynth's file renderer."""
    print(f"  Rendering '{os.path.basename(midi_path)}' → '{os.path.basename(output_path)}'...")

    fs, sfid, program = init_synth(instrument_name, soundfont_path, output_file=output_path, audio_type='wav')
    try:
        send_midi_to_synth(fs, midi_path, sfid, program)
    finally:
        fs.delete()

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
