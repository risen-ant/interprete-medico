# app.py — interfaz visual mejorada con login de usuario (sin contraseña) y almacenamiento por alias
import streamlit as st
from PIL import Image
import easyocr
import numpy as np
from fpdf import FPDF
from datetime import datetime
import os
from utils_ai_API import explicar_informe

st.set_page_config(page_title="Intérprete Médico", layout="wide")

# Inicialización de sesión
if "usuario" not in st.session_state:
    st.session_state.usuario = None
if "perfil" not in st.session_state:
    st.session_state.perfil = None
if "respuesta_generada" not in st.session_state:
    st.session_state.respuesta_generada = ""
if "historial" not in st.session_state:
    st.session_state.historial = []

st.title("🧬 Intérprete Médico Personalizado")

# Login simple
if st.session_state.usuario is None:
    alias = st.text_input("Introduce tu nombre o alias para comenzar")
    if st.button("Entrar") and alias.strip():
        st.session_state.usuario = alias.strip()
        st.rerun()
    st.stop()

# Perfil
st.subheader("1️⃣ Perfil del usuario")
with st.form("perfil_usuario"):
    edad = st.radio("Edad", ["<18", "18–29", "30–64", "≥65"])
    estudios = st.selectbox("Estudios", ["Básicos", "Medios", "Universitarios no sanitarios", "Estudios/experiencia sanitaria"])
    detalle = st.radio("Nivel de detalle", ["Muy simple", "Intermedio", "Técnico"])
    objetivo = st.selectbox("Objetivo principal", ["Entender mi salud", "Preparar visita médica", "Presentar en trabajo/seguro", "Uso legal (baja, juicio)"])
    comorbilidades = st.multiselect("Condiciones médicas", ["Hipertensión", "Diabetes", "Colesterol alto", "Enfermedad cardiaca", "Obesidad", "Tabaquismo", "Asma", "Insuficiencia renal"])
    if st.form_submit_button("Guardar perfil"):
        st.session_state.perfil = {
            "edad": edad,
            "estudios": estudios,
            "detalle": detalle,
            "objetivo": objetivo,
            "comorbilidades": comorbilidades
        }
        st.success("✅ Perfil guardado correctamente")

# Subida de informe
st.subheader("2️⃣ Sube tu informe médico (imagen o texto)")
archivo = st.file_uploader("Selecciona un archivo (.png, .jpg, .jpeg, .txt)", type=["png", "jpg", "jpeg", "txt"])
texto_extraido = ""

if archivo:
    if archivo.type.startswith("image"):
        imagen = Image.open(archivo)
        st.image(imagen, caption="Imagen subida", use_container_width=True)
        with st.spinner("🧠 Extrayendo texto con EasyOCR..."):
            reader = easyocr.Reader(["es"], gpu=False)
            resultado = reader.readtext(np.array(imagen), detail=0)
            texto_extraido = "\n".join(resultado)
    elif archivo.type == "text/plain":
        texto_extraido = archivo.read().decode("utf-8")

    st.text_area("📄 Texto extraído", value=texto_extraido, height=300)

# Interpretación
st.subheader("3️⃣ Interpretación personalizada")
if texto_extraido and st.session_state.perfil:
    if st.button("🧠 Generar interpretación"):
        with st.spinner("Generando interpretación..."):
            respuesta = explicar_informe(texto_extraido, st.session_state.perfil)
            st.session_state.respuesta_generada = respuesta
            st.success("✅ Interpretación generada")
            st.write(respuesta)
            st.session_state.historial.append({
                "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "texto": texto_extraido,
                "resultado": respuesta
            })

# Exportar
if st.session_state.respuesta_generada:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, f"Informe generado el {datetime.now().strftime('%d/%m/%Y')}\n")
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Resultado personalizado:", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, st.session_state.respuesta_generada.encode("latin-1", "replace").decode("latin-1"))
    nombre = "informe_personalizado.pdf"
    pdf.output(nombre)
    with open(nombre, "rb") as f:
        st.download_button("📄 Descargar PDF", f, file_name=nombre, mime="application/pdf")

# Reiniciar
if st.button("🔄 Nuevo análisis"):
    st.session_state.perfil = None
    st.session_state.respuesta_generada = ""
    st.rerun()
