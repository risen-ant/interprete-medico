# reproducir_audio.py
from io import BytesIO
from gtts import gTTS

def generar_audio(texto: str, lang: str = "es") -> BytesIO:
    """
    Genera un MP3 en memoria con la síntesis de 'texto'.
    Devuelve un BytesIO listo para enviarse a st.audio.
    """
    buffer = BytesIO()
    tts = gTTS(texto, lang=lang)
    tts.write_to_fp(buffer)
    buffer.seek(0)
    return buffer