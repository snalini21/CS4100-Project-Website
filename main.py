from fastapi import FastAPI, HTTPException
import io
from fastapi.responses import Response, StreamingResponse
from models.generate_chords_from_model import load_model_and_generate
from models.genetic_algo import generate_progression
from models.markov_model import MarkovChordModel
import music21
import time

app = FastAPI()


def _generate_sequence(model_type, length, dataset_type='no_repeats'):
    # if using LSTM, have length be an integer multiple of 16
    # dataset_type should be repeats or no_repeats
    out = []
    if model_type.lower() == 'lstm':
        MODEL_PATH = f"models/model_states/chord_model{"_no_repeats" * (dataset_type == "no_repeats")}_epoch_10.pth"
        DATA_PATH = f"models/data/chord_bases_{"_no_repeats" * (dataset_type == "no_repeats")}processed.pt"
        my_seed = ["I", "V", "vi", "IV", "I", "V", "I", "I"]

        for _ in range(length // 16):  # each generation round generates 16
            out.extend(load_model_and_generate(MODEL_PATH, DATA_PATH, my_seed))

        return out

    elif model_type.lower() == 'genetic' or model_type.lower() == 'ga':
        filepath = f'models/data/chord_bases{"_no_repeats" * (dataset_type == "no_repeats")}.txt'
        ga_prog, _ = generate_progression(filepath=filepath, length=length)
        out.extend(ga_prog)
        return out

    elif model_type.lower() == 'markov':
        model = MarkovChordModel()
        filepath = f'models/data/chord_bases{"_no_repeats" * (dataset_type == "no_repeats")}.txt'
        model.load_progressions(filepath)
        model.train()

        progression = model.generate(start="I", length=length)
        return progression

    else:
        raise Exception('Please have the model type be lstm, genetic, ga, or markov (case insensitive)')


def _generate_chord_rh(key_name, progression):
    stream1 = music21.stream.base.Part()
    list_of_roots = []
    k = music21.key.Key(key_name)

    for root in progression:
        c = music21.roman.RomanNumeral(root, k)
        stream1.append(c)
        list_of_roots.append(c)

    return stream1, list_of_roots


def _generate_arpeggio_lh(list_of_roots):
    stream2 = music21.stream.base.Part()

    for l in list_of_roots:
        # rewritten to use relative duration of the input note in list_of_roots
        duration = l.duration.augmentOrDiminish(0.25)
        n = music21.note.Note(l.pitches[0], duration=duration)  # lowest note in chord

        # minus 12 midi pitches moves it down 1 octave
        n1 = music21.note.Note(n.pitch.midi - 12, duration=duration)
        n2, n3 = n1.transpose('M3'), n1.transpose('P5')

        for n in [n1, n2, n3]:
            stream2.append(n)

        stream2.append(music21.note.Note(n2.pitch, duration=duration))

    return stream2


def correct_notes_in_key(final_stream, k):
    k = music21.key.Key(k)
    for n in final_stream.recurse().notes:
        if isinstance(n, music21.chord.Chord):
            for no in n.notes:
                nStep = no.pitch.step
                rightAccidental = k.accidentalByStep(nStep)
                no.pitch.accidental = rightAccidental
                # need to treat chords separately and iterate through notes in one
        else:
            n_step = n.pitch.step
            right_accidental = k.accidentalByStep(n_step)
            n.pitch.accidental = right_accidental

    return final_stream


def _generate_midi(progression, key):
    stream1, list_of_roots = _generate_chord_rh(key, progression)
    stream2 = _generate_arpeggio_lh(list_of_roots)

    final_stream = music21.stream.base.Score()
    k = music21.key.Key(key)
    final_stream.insert(0, k)  # key signature

    final_stream.append(stream1)
    final_stream.append(stream2)

    final_stream = correct_notes_in_key(final_stream, key)
    return final_stream


@app.get('/midi')
def return_midi(model_type = 'ga', key: str = 'C', length: int = 16, dataset_type='no_repeats'):
    """
    Usage:
    :param model_type: ga, genetic, lstm, or markov (case insensitive)
    :param key: c, C, c#, c#, cb, Cb etc (for every key, majors/minors and sharps/flats)
    :param length: length of generated sequence; if using lstm, make it an integer multiple of 16
    :param dataset_type: no_repeats will use the dataset with repeats removed, any other value will use the default one
                Try to keep the other one to 'repeats' though for readability
    :return: midi file with generated music
    """
    try:
        a = _generate_sequence(model_type=model_type, length=length, dataset_type=dataset_type)
    except:
        raise HTTPException(status_code=404,
                            detail='Please have the model type be lstm, genetic, ga, or markov (case insensitive)')
    midi_stream = _generate_midi(a, key=key)
    mf = music21.midi.translate.streamToMidiFile(midi_stream)
    midi_data = mf.writestr()

    filename = f'{int(time.time())}.mid'
    return StreamingResponse(
        io.BytesIO(midi_data),
        media_type="audio/midi",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


def main():
    """
    sample usage:
    # a = _generate_sequence('lstm', 16)
    # b = _generate_sequence('genetic', 16)
    # c = _generate_sequence('markov', 16)
    """
    a = _generate_sequence('ga', 16, dataset_type='repeats')
    midi = _generate_midi(a, 'E')
    filepath = f'./midis/{int(time.time())}.mid'
    midi.write('midi', filepath)


if __name__ == '__main__':
    main()





