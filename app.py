# app.py — interfaz visual con EasyOCR + audio con gTTS + login seguro

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
from auth_utils import verificar_credenciales, crear_nuevo_usuario

DATA_DIR = "usuarios_datos"
os.makedirs(DATA_DIR, exist_ok=True)

st.set_page_config(page_title="Intérprete Médico Automático", page_icon="🧬", layout="wide")

if "usuario" not in st.session_state:
    st.session_state.usuario = None

# --- LOGIN / REGISTRO SEGURO ---
if st.session_state.usuario is None:
    st.title("🔐 Iniciar sesión o registrarse")
    modo = st.radio("Selecciona una opción:", ["Iniciar sesión", "Crear cuenta"])

    if modo == "Iniciar sesión":
        usuario = st.text_input("Nombre de usuario")
        password = st.text_input("Contraseña", type="password")
        if st.button("Entrar"):
            if verificar_credenciales(usuario, password):
                st.session_state.usuario = usuario
                ruta_usuario = os.path.join(DATA_DIR, f"{usuario}.json")
                if os.path.exists(ruta_usuario):
                    with open(ruta_usuario, "r", encoding="utf-8") as f:
                        datos = json.load(f)
                        st.session_state.perfil = datos.get("perfil", None)
                        st.session_state.historial = datos.get("historial", [])
                st.success("✅ Sesión iniciada correctamente")
                st.rerun()
            else:
                st.error("❌ Usuario o contraseña incorrectos.")
        st.stop()

    elif modo == "Crear cuenta":
        usuario = st.text_input("Nuevo nombre de usuario")
        password = st.text_input("Crea una contraseña", type="password")
        confirm = st.text_input("Confirma la contraseña", type="password")
        email = st.text_input("Correo electrónico (opcional)")
        if st.button("Registrar"):
            if password != confirm:
                st.warning("⚠️ Las contraseñas no coinciden.")
            elif len(usuario.strip()) < 3 or len(password) < 4:
                st.warning("⚠️ Usuario o contraseña demasiado cortos.")
            elif crear_nuevo_usuario(usuario.strip(), password.strip(), email.strip()):
                st.success("✅ Cuenta creada. Ahora puedes iniciar sesión.")
            else:
                st.error("❌ El nombre de usuario ya existe.")
        st.stop()

# --- Función para guardar datos del usuario ---
def guardar_datos_usuario():
    if st.session_state.usuario:
        ruta = os.path.join(DATA_DIR, f"{st.session_state.usuario}.json")
        datos = {
            "perfil": st.session_state.get("perfil", None),
            "historial": st.session_state.get("historial", [])
        }
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)

# --- Inicializar estado de sesión ---
if "perfil" not in st.session_state:
    st.session_state.perfil = None
if "respuesta_generada" not in st.session_state:
    st.session_state.respuesta_generada = ""
if "historial" not in st.session_state:
    st.session_state.historial = []
if "texto_extraido" not in st.session_state:
    st.session_state.texto_extraido = ""

# --- Cerrar sesión ---
if st.sidebar.button("🔓 Cerrar sesión"):
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()

# --- INTERFAZ PRINCIPAL ---
st.title("🧬 Intérprete automático de informes médicos")
st.caption(f"Sesión iniciada como: **{st.session_state.usuario}**")

st.sidebar.header("💼 Instrucciones")
st.sidebar.markdown("""
1. Rellena tu perfil de usuario.  
2. Sube una imagen o archivo de texto.  
3. Genera una explicación personalizada.  
4. Exporta a PDF si lo deseas.
""")
st.sidebar.markdown("---")
st.sidebar.info("Este prototipo no sustituye la opinión de un profesional sanitario.")

if st.session_state.perfil:
    with st.sidebar.expander("👤 Perfil del usuario", expanded=True):
        for k, v in st.session_state.perfil.items():
            st.markdown(f"**{k.capitalize()}**: {v}")

# 1️⃣ Perfil del usuario
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

# 2️⃣ Subida de archivo y OCR
st.divider()
st.subheader("2️⃣ Sube tu informe (imagen o texto)")
archivos = st.file_uploader("Selecciona uno o varios archivos (.png, .jpg, .jpeg, .txt)",
                             type=["png", "jpg", "jpeg", "txt"],
                             accept_multiple_files=True)

if archivos:
    texto_total = ""
    col1, col2 = st.columns([1, 2])

    with st.spinner("Inicializando modelo OCR..."):
        reader = easyocr.Reader(["es"], gpu=False)

    for archivo in archivos[:3]:
        if archivo.type.startswith("image"):
            imagen = Image.open(archivo)
            if imagen.width * imagen.height > 2_000_000:
                imagen.thumbnail((1600, 1600))
                st.info(f"📐 Imagen redimensionada: {archivo.name}")
            with col1:
                st.image(imagen, caption=archivo.name, use_container_width=True)
            with st.spinner(f"Procesando {archivo.name}..."):
                try:
                    resultado = reader.readtext(np.array(imagen), detail=0)
                    texto = "\n".join(resultado)
                    texto_total += f"\n\n--- Texto extraído de {archivo.name} ---\n{texto}"
                except Exception as e:
                    st.error(f"Error OCR: {e}")
        elif archivo.type == "text/plain":
            texto = archivo.read().decode("utf-8")
            texto_total += f"\n\n--- Contenido de {archivo.name} ---\n{texto}"
            with col1:
                st.success(f"📄 Cargado: {archivo.name}")

    st.session_state.texto_extraido = texto_total.strip()
    with col2:
        st.subheader("📜 Texto extraído:")
        st.text_area("Resultado OCR / Texto leído:", value=st.session_state.texto_extraido, height=400)

# 3️⃣ Interpretación con IA
st.divider()
st.subheader("3️⃣ Interpretación personalizada")

if st.session_state.texto_extraido and st.session_state.perfil:
    if st.button("🤖 Generar explicación con IA"):
        with st.spinner("Generando explicación..."):
            try:
                respuesta = explicar_informe(st.session_state.texto_extraido, st.session_state.perfil)
                st.session_state.respuesta_generada = respuesta
                st.success("✅ Interpretación generada")
                nuevo_registro = {
                    "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "texto": st.session_state.texto_extraido,
                    "resultado": st.session_state.respuesta_generada
                }
                st.session_state.historial.append(nuevo_registro)
                guardar_datos_usuario()
            except Exception as e:
                st.error(f"Error IA: {e}")

if st.session_state.respuesta_generada:
    st.write(st.session_state.respuesta_generada)
    st.subheader("🔊 Escuchar explicación")
    if st.button("🎷 Escuchar explicación"):
        audio_bytes = generar_audio(st.session_state.respuesta_generada, lang="es")
        st.audio(audio_bytes, format="audio/mp3")

if st.session_state.historial:
    st.markdown("### 📜 Historial de informes")
    for i, item in enumerate(st.session_state.historial[::-1], 1):
        with st.expander(f"Informe #{i} – {item['fecha']}"):
            st.markdown("**Texto original del informe:**")
            st.code(item["texto"])
            st.markdown("**Resultado generado:**")
            st.write(item["resultado"])
    if st.button("🗑️ Borrar historial"):
        st.session_state.historial = []
        guardar_datos_usuario()
        st.success("Historial eliminado.")
        st.rerun()












