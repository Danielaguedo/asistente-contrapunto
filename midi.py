# midi.py (decoupled - pure music21, no Streamlit)
import tempfile
from music21 import midi


def generar_midi(score, output_path=None):
    """
    Genera un archivo MIDI a partir de un objeto score de music21.
    Devuelve la ruta del archivo generado, o None si falla.
    """
    try:
        mf = midi.translate.streamToMidiFile(score)
        if output_path is None:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mid")
            output_path = tmp.name
            tmp.close()
        mf.open(output_path, "wb")
        mf.write()
        mf.close()
        return output_path
    except Exception as e:
        print(f"No se pudo generar el archivo MIDI: {e}")
        return None
