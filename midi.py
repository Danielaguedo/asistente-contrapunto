import streamlit as st
import tempfile
from music21 import midi

def generar_midi(score):
    """
    Genera un archivo MIDI a partir de un objeto score de music21.
    """
    try:
        mf = midi.translate.streamToMidiFile(score)
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mid")
        mf.open(temp_file.name, "wb")
        mf.write()
        mf.close()
        return temp_file.name
    except Exception as e:
        st.error(f"No se pudo generar el archivo MIDI: {str(e)}")
        return None

def reproducir_midi(score):
    """
    Reproduce un archivo MIDI generado a partir de un score.
    """
    midi_path = generar_midi(score)
    if midi_path:
        st.audio(midi_path, format="audio/midi")
    else:
        st.error("Error al generar el MIDI.")

 #def crear_boton_descarga_midi(score):
    """
    Crea un botón de descarga para el archivo MIDI generado.
    """
    midi_path = generar_midi(score)
    if midi_path:
        with open(midi_path, "rb") as f:
            midi_data = f.read()
        st.download_button(
            label="Descargar MIDI",
            data=midi_data,
            file_name="ejercicio.mid",
            mime="audio/midi"
        )
    else:
        st.error("No se pudo generar el archivo MIDI para descargar.")
