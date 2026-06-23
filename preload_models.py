"""
Descarga los modelos de DeepFace durante el build de Render.
Esto evita que el primer request del usuario tarde varios minutos.
"""
import cv2
import numpy as np
import tempfile
import os
from deepface import DeepFace

print("Descargando modelos de DeepFace (esto puede tardar varios minutos)...")

img = np.zeros((100, 100, 3), dtype=np.uint8)
tmp = os.path.join(tempfile.gettempdir(), "preload_dummy.jpg")
cv2.imwrite(tmp, img)

try:
    DeepFace.analyze(
        tmp,
        actions=["age", "gender", "emotion", "race"],
        enforce_detection=False,
        silent=False,
    )
    print("Modelos descargados y listos.")
except Exception as e:
    print(f"Advertencia al precargar modelos: {e}")
finally:
    if os.path.exists(tmp):
        os.remove(tmp)
