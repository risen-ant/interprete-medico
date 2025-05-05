# utils_ai_API.py — motor optimizado con prompt único adaptado al perfil 

import streamlit as st
from openai import OpenAI

# Clave API cargada desde los secretos de Streamlit
client = OpenAI(api_key=st.secrets["openai_api_key"])

def construir_prompt_personalizado(texto_informe: str, perfil: dict) -> str:
    edad = perfil.get("edad", "")
    estudios = perfil.get("estudios", "")
    comorbilidades = perfil.get("comorbilidades", [])
    comorbilidades_txt = ", ".join(comorbilidades) if comorbilidades else "ninguna"
    objetivo = perfil.get("objetivo", "")
    detalle = perfil.get("detalle", "")

    instrucciones = []

    if detalle == "Muy simple":
        instrucciones.append("Usa lenguaje muy sencillo y cotidiano. Evita términos técnicos.")
    elif detalle == "Intermedio":
        instrucciones.append("Usa lenguaje accesible pero incluye definiciones breves de conceptos médicos.")
    elif detalle == "Técnico":
        instrucciones.append("Usa vocabulario clínico y referencia a guías médicas si es relevante.")

    if edad == "≥65":
        instrucciones.append("Ten en cuenta que es una persona mayor. Prioriza explicaciones claras y riesgos comunes.")
    elif edad == "<18":
        instrucciones.append("Ten en cuenta que es una persona joven. Prioriza lenguaje más callejero y de jóvenes, pero sin entrar en lo vulgar.")

    if estudios == "Estudios/experiencia sanitaria":
        instrucciones.append("La persona tiene conocimientos sanitarios, puedes profundizar en los aspectos técnicos.")

    if "legal" in objetivo.lower():
        instrucciones.append("La explicación debe ser formal, objetiva y adecuada para un contexto legal.")
    elif "visita" in objetivo.lower():
        instrucciones.append("Sugiere posibles preguntas que puede hacerle a su médico en la consulta.")
    elif "trabajo" in objetivo.lower() or "seguro" in objetivo.lower():
        instrucciones.append("Enfoca la explicación en aspectos laborales y en cómo podría justificar su situación médica.")
    elif "entender" in objetivo.lower():
        instrucciones.append("Incluye recomendaciones generales de estilo de vida saludables relacionadas con los hallazgos.")

    if "Diabetes" in comorbilidades:
        instrucciones.append("Haz énfasis en resultados relacionados con glucosa, función renal y dieta.")
    if "Hipertensión" in comorbilidades:
        instrucciones.append("Destaca cualquier parámetro relacionado con presión arterial o riesgo cardiovascular.")
    if "Colesterol alto" in comorbilidades:
        instrucciones.append("Explica claramente los niveles de lípidos y su impacto en la salud.")
    if "Enfermedad cardiaca" in comorbilidades:
        instrucciones.append("Prioriza aspectos cardiovasculares y signos de riesgo o empeoramiento.")
    if "Obesidad" in comorbilidades:
        instrucciones.append("Relaciona los hallazgos con riesgos asociados al sobrepeso como hipertensión, diabetes o apnea del sueño.")
    if "Tabaquismo" in comorbilidades:
        instrucciones.append("Destaca riesgos cardiovasculares, respiratorios y cualquier marcador alterado relacionado con el tabaquismo.")
    if "Asma" in comorbilidades:
        instrucciones.append("Relaciona los hallazgos con síntomas respiratorios y controla signos de inflamación o alergia.")
    if "Insuficiencia renal" in comorbilidades:
        instrucciones.append("Haz énfasis en creatinina, filtrado glomerular y parámetros que indiquen función renal.")

    contexto = (
        f"Eres un asistente médico experto. El paciente tiene {edad} años, con estudios {estudios.lower()}. "
        f"Tiene como objetivo: {objetivo.lower()}. "
        f"Condiciones médicas relevantes: {comorbilidades_txt}. "
        f"Instrucciones: {' '.join(instrucciones)}"
    )

    return f"{contexto}\n\nTexto del informe médico:\n{texto_informe}"

def explicar_informe(texto_informe: str, perfil: dict, modelo="gpt-3.5-turbo") -> str:
    prompt_completo = construir_prompt_personalizado(texto_informe, perfil)

    system_msg = {"role": "system", "content": "Eres un asistente médico que adapta sus explicaciones al perfil clínico y social del paciente."}
    user_msg = {"role": "user", "content": prompt_completo}

    respuesta = client.chat.completions.create(
        model=modelo,
        messages=[system_msg, user_msg],
        temperature=0.7
    ).choices[0].message.content.strip()

    return respuesta






