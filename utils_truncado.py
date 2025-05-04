# utils_truncado.py

import tiktoken

def truncar_texto_por_tokens(texto: str, max_tokens: int = 3000, modelo: str = "gpt-3.5-turbo") -> str:
    """
    Recorta un texto en base al número de tokens máximos para el modelo.
    Retorna el texto recortado.
    """
    encoding = tiktoken.encoding_for_model(modelo)
    tokens = encoding.encode(texto)
    if len(tokens) > max_tokens:
        tokens = tokens[:max_tokens]
    return encoding.decode(tokens)

