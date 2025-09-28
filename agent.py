import cv2
import requests
import time

# --- CONFIGURACIÓN ---
# La URL de tu aplicación en Render
RENDER_URL = "https://detector-app-ok91.onrender.com/upload_frame" 
VIDEO_SOURCE = 0 # 0 para webcam, o tu URL RTSP

cap = cv2.VideoCapture(VIDEO_SOURCE)

if not cap.isOpened():
    print(f"Error: No se pudo abrir la cámara {VIDEO_SOURCE}")
    exit()

print("Agente iniciado. Enviando frames a Render...")

while True:
    ret, frame = cap.read()
    if not ret:
        print("No se pudo leer el frame. Reintentando...")
        time.sleep(2)
        continue

    # Codificar el frame como JPEG
    _, img_encoded = cv2.imencode('.jpg', frame)
    
    try:
        # Enviar la imagen al servidor de Render
        response = requests.post(
            RENDER_URL, 
            files={'frame': ('frame.jpg', img_encoded.tobytes(), 'image/jpeg')},
            timeout=5 # Esperar máximo 5 segundos por una respuesta
        )
        if response.status_code == 200:
            print("Frame enviado exitosamente.", end='\r')
        else:
            print(f"Error del servidor: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error de conexión: {e}")

    # Controlar el framerate para no saturar el servidor
    time.sleep(0.5) # Enviar 2 frames por segundo

cap.release()
