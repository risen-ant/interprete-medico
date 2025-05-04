# app.py — interfaz visual con EasyOCR + audio con gTTS

import streamlit as st
from PIL import Image
import easyocr
import numpy as np
from datetime import datetime
from fpdf import FPDF
import os
import json

from utils_ai_API import explicar_informe
from reproducir_audio import generar_audio

DATA_DIR = "usuarios_datos"
os.makedirs(DATA_DIR, exist_ok=True)

st.set_page_config(page_title="Intérprete Médico Automático", page_icon="🧬", layout="wide")

if "usuario" not in st.session_state:
    st.session_state.usuario = None
if st.session_state.usuario is None:
    st.title("👤 Iniciar sesión")
    alias = st.text_input("Nombre de usuario")
    if st.button("Entrar") and alias.strip():
        st.session_state.usuario = alias.strip()
        ruta_usuario = os.path.join(DATA_DIR, f"{alias.strip()}.json")
        if os.path.exists(ruta_usuario):
            with open(ruta_usuario, "r", encoding="utf-8") as f:
                datos = json.load(f)
                st.session_state.perfil = datos.get("perfil", None)
                st.session_state.historial = datos.get("historial", [])
        st.rerun()
    st.stop()

def guardar_datos_usuario():
    if st.session_state.usuario:
        ruta = os.path.join(DATA_DIR, f"{st.session_state.usuario}.json")
        datos = {
            "perfil": st.session_state.get("perfil", None),
            "historial": st.session_state.get("historial", [])
        }
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)

st.markdown("""
    <style>
        body { background-color: #f0f8ff; }
        .block-container { background-color: #f0f8ff; padding: 2rem; border-radius: 8px; }
        .stButton>button { transition: all 0.3s ease; }
        .stButton>button:hover { transform: scale(1.03); background-color: #dbeeff; }
    </style>
""", unsafe_allow_html=True)

if "aceptado" not in st.session_state:
    st.session_state.aceptado = False
if not st.session_state.aceptado:
    st.image("logo_upv.png", width=120)
    st.title(f"Bienvenido, {st.session_state.usuario}")
    st.markdown("""
    Esta herramienta permite interpretar informes médicos de forma simplificada, según tu perfil.  
    ⚠️ **Importante:** Este es un prototipo con fines educativos.  
    **No reemplaza la consulta con profesionales sanitarios.**
    """)
    if st.button("Aceptar y comenzar"):
        st.session_state.aceptado = True
        st.rerun()
    st.stop()

if "perfil" not in st.session_state:
    st.session_state.perfil = None
if "respuesta_generada" not in st.session_state:
    st.session_state.respuesta_generada = ""
if "historial" not in st.session_state:
    st.session_state.historial = []
if "texto_extraido" not in st.session_state:
    st.session_state.texto_extraido = ""

col_logo, col_title = st.columns([1, 5])
with col_logo:
    if os.path.exists("logo_upv.png"):
        st.image("logo_upv.png", width=100)
with col_title:
    st.title("Intérprete automático de informes médicos")
    st.caption(f"Usuario: {st.session_state.usuario} • Prototipo educativo desarrollado con Streamlit")

st.sidebar.header("💼 Instrucciones")
st.sidebar.markdown("""
1. Rellena tu perfil de usuario.  
2. Sube una imagen o archivo de texto.  
3. Genera una explicación personalizada.  
4. Exporta a PDF si lo deseas.
""")
st.sidebar.markdown("---")
st.sidebar.info("Este prototipo no sustituye la opinión de un profesional sanitario.")

if st.sidebar.button("🔓 Cerrar sesión"):
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()

if st.session_state.perfil:
    with st.sidebar.expander("👤 Perfil del usuario", expanded=True):
        for k, v in st.session_state.perfil.items():
            st.markdown(f"**{k.capitalize()}**: {v}")

st.subheader("1️⃣ Define tu perfil")
with st.form("perfil_usuario"):
    col1, col2, col3 = st.columns(3)
    with col1:
        edad = st.radio("Edad", ["<18", "18–29", "30–64", "≥65"])
    with col2:
        estudios = st.selectbox("Estudios", ["Básicos", "Medios", "Universitarios no sanitarios", "Estudios/experiencia sanitaria"])
    with col3:
        detalle = st.radio("Nivel de detalle", ["Muy simple", "Intermedio", "Técnico"])
    objetivo = st.selectbox("Objetivo principal", ["Entender mi salud", "Preparar visita médica", "Presentar en trabajo/seguro", "Uso legal (baja, juicio)"])
    comorbilidades = st.multiselect("Condiciones médicas", ["Hipertensión", "Diabetes", "Colesterol alto", "Enfermedad cardiaca", "Obesidad", "Tabaquismo", "Asma", "Insuficiencia renal"])

    if st.form_submit_button("Guardar perfil"):
        st.session_state.perfil = {
            "edad": edad,
            "estudios": estudios,
            "objetivo": objetivo,
            "comorbilidades": comorbilidades,
            "detalle": detalle
        }
        guardar_datos_usuario()
        st.success("Perfil guardado correctamente ✅")

st.divider()
st.subheader("2️⃣ Sube tu informe (imagen o texto)")
archivos = st.file_uploader(
    "Selecciona uno o varios archivos (.png, .jpg, .jpeg, .txt)",
    type=["png", "jpg", "jpeg", "txt"],
    accept_multiple_files=True,
    key=st.session_state.get("upload_key", "default_uploader")
)

if archivos:
    texto_total = ""
    col1, col2 = st.columns([1, 2])

    for archivo in archivos:
        if archivo.type.startswith("image"):
            imagen = Image.open(archivo)
            with col1:
                st.image(imagen, caption=f"🖼 Imagen: {archivo.name}", use_container_width=True)
            with st.spinner(f"🔍 Extrayendo texto de {archivo.name}..."):
                reader = easyocr.Reader(["es"], gpu=False)
                resultado = reader.readtext(np.array(imagen), detail=0)
                texto = "\n".join(resultado)
                texto_total += f"\n\n--- Texto extraído de {archivo.name} ---\n{texto}"
        elif archivo.type == "text/plain":
            texto = archivo.read().decode("utf-8")
            texto_total += f"\n\n--- Contenido de {archivo.name} ---\n{texto}"
            with col1:
                st.success(f"📄 Archivo de texto cargado: {archivo.name}")

    st.session_state.texto_extraido = texto_total.strip()

    with col2:
        st.subheader("📜 Texto combinado extraído:")
        st.text_area("Resultado OCR / Texto leído:", value=st.session_state.texto_extraido, height=400)

st.divider()
st.subheader("3️⃣ Interpretación personalizada")

if st.session_state.texto_extraido and st.session_state.perfil:
    if st.button("🤖 Generar explicación con IA"):
        with st.spinner("Generando explicación adaptada..."):
            try:
                respuesta = explicar_informe(st.session_state.texto_extraido, st.session_state.perfil)
                st.session_state.respuesta_generada = respuesta
                st.success("✅ Interpretación generada")

                # 🔄 Añadir al historial
                nuevo_registro = {
                    "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "texto": st.session_state.texto_extraido,
                    "resultado": st.session_state.respuesta_generada
                }
                st.session_state.historial.append(nuevo_registro)
                guardar_datos_usuario()

            except Exception as e:
                st.error(f"❌ Error al generar la interpretación: {e}")

if st.session_state.respuesta_generada:
    st.write(st.session_state.respuesta_generada)

    # 🎷 Reproducir audio si hay explicación generada
    st.subheader("🔊 Escuchar explicación")
    if st.button("🎷 Escuchar explicación"):
        audio_bytes = generar_audio(st.session_state.respuesta_generada, lang="es")
        st.audio(audio_bytes, format="audio/mp3")

if st.session_state.historial:
    st.markdown("### 📜 Historial de informes")
    for i, item in enumerate(st.session_state.historial[::-1], 1):
        with st.expander(f"📄 Informe #{i} – {item['fecha']}"):
            st.markdown("**📜 Texto original del informe:**", unsafe_allow_html=True)
            st.code(item["texto"], language="text")
            st.markdown("**✅ Resultado generado:**", unsafe_allow_html=True)
            st.write(item["resultado"])

    if st.button("🗑️ Borrar historial"):
        st.session_state.historial = []
        guardar_datos_usuario()
        st.success("Historial eliminado.")
        st.rerun()

if st.session_state.respuesta_generada:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, f"Informe generado el {datetime.now().strftime('%d/%m/%Y')}\n")
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Resultado personalizado:", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, st.session_state.respuesta_generada.encode('latin-1', 'replace').decode('latin-1'))

    nombre = "informe_personalizado.pdf"
    pdf.output(nombre)

    with open(nombre, "rb") as f:
        st.download_button("📄 Descargar como PDF", data=f, file_name=nombre, mime="application/pdf")

st.divider()
if st.button("🔄 Nuevo análisis"):
    for key in ["texto_extraido", "respuesta_generada", "audio_bytes"]:
        if key in st.session_state:
            del st.session_state[key]
    st.session_state["upload_key"] = str(datetime.now())











