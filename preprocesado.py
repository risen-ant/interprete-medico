# preprocesado.py

import cv2
import numpy as np
from PIL import Image
import io

def preprocess_image(pil_img: Image.Image) -> Image.Image:
    """
    Aplica una serie de transformaciones para "simular escaneo":
      1. Convierte a escala de grises.
      2. Reduce ruido con filtro bilateral.
      3. Realza bordes con CLAHE.
      4. Umbral adaptativo.
      5. Apertura morfológica para limpiar pequeñas manchas.
    Devuelve una nueva PIL.Image listA para OCR.
    """
    # 1) PIL -> numpy BGR
    img = np.array(pil_img.convert("RGB"))
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    # 2) Gris
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 3) Filtrado bilateral para reducir ruido manteniendo bordes
    denoised = cv2.bilateralFilter(gray, d=9, sigmaColor=75, sigmaSpace=75)

    # 4) Ecualización de contraste local (CLAHE)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(denoised)

    # 5) Umbral adaptativo
    thresh = cv2.adaptiveThreshold(
        enhanced,
        maxValue=255,
        adaptiveMethod=cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        thresholdType=cv2.THRESH_BINARY,
        blockSize=15,
        C=10
    )

    # 6) Apertura morfológica (erosión seguida de dilatación)
    kernel = np.ones((3,3), np.uint8)
    opened = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

    # 7) Devolver a PIL
    processed_pil = Image.fromarray(opened)
    return processed_pil


def preprocess_image_file(input_path: str, output_path: str = None) -> Image.Image:
    """
    Lee una imagen desde disco, la preprocesa y opcionalmente la guarda.
    """
    pil = Image.open(input_path)
    processed = preprocess_image(pil)
    if output_path:
        processed.save(output_path)
    return processed


if __name__ == "__main__":
    import sys
    if not (2 <= len(sys.argv) <= 3):
        print("Uso: python preprocesado.py <input.jpg> [<output.png>]")
        sys.exit(1)
    inp = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) == 3 else None
    preprocess_image_file(inp, out)
    print(f"Procesada '{inp}'{' -> '+out if out else ''}")