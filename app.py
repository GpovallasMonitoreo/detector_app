import cv2
import numpy as np
import os
import time
from flask import Flask, render_template, Response, jsonify
import threading

# --- CONFIGURACIÓN (Similar a antes) ---
REFERENCE_FOLDER = 'referencias'
PANEL_WIDTH = 350
SIMILARITY_THRESHOLD = 15
BRIGHTNESS_OFF_THRESHOLD = 50
KEYPOINT_OFF_THRESHOLD = 40
MOTION_THRESHOLD = 1.0
VANDALISM_THRESHOLD = 2.0
STABILITY_SECONDS = 3.0

# --- Variables Globales de Estado (gestionadas por el hilo de fondo) ---
global_frame = None
status_checklist = {}
lock = threading.Lock() # Para evitar conflictos al acceder a las variables globales

# --- Inicializar la Aplicación Flask ---
app = Flask(__name__)

# --- Lógica de Visión por Computadora (Las funciones que ya conoces) ---
# (Aquí irían las funciones: check_if_screen_off, preprocess_for_matching, find_best_match, etc.)
# Por brevedad, las omito aquí, pero deben estar en tu app.py. Asumimos que están definidas.

def video_processing_thread():
    """
    Este hilo se ejecuta en segundo plano para procesar el video
    continuamente sin bloquear el servidor web.
    """
    global global_frame, status_checklist

    # Carga de referencias (simplificado)
    # En una app real, la URL del video vendría de una base de datos o configuración
    # Para esta demo, asumimos que viene de una variable de entorno o está fija.
    # VIDEO_SOURCE = os.getenv('CAM_URL', 0) 
    VIDEO_SOURCE = 0 # O tu URL RTSP
    cap = cv2.VideoCapture(VIDEO_SOURCE)
    
    # ... (El resto de tu lógica de setup: cargar referencias, etc.) ...
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("WARN: No se puede leer el frame de la cámara.")
            time.sleep(2)
            continue

        # --- Aquí va toda tu lógica de análisis de la v12 ---
        # 1. Seleccionar ROI (para esta demo, lo fijaremos en el código)
        H, W, _ = frame.shape
        # Ejemplo de ROI fijo, en una app real esto sería configurable
        roi = frame[int(H*0.2):int(H*0.8), int(W*0.2):int(W*0.8)] 

        # 2. Ejecutar todas las comprobaciones (pantalla apagada, match, vandalismo)
        # 3. Actualizar un diccionario de estado
        current_status = {
            "CONEXION": ("OK", "#28a745"), # Verde
            "PANTALLA": ("ENCENDIDA", "#28a745"),
            "IMAGEN": ("anuncio_1.jpg (25)", "#28a745"),
            "VANDALISMO": ("NO DETECTADO", "#28a745"),
            "GRABACION": ("EN ESPERA", "#ffc107") # Amarillo
        }
        
        # Actualizar las variables globales de forma segura
        with lock:
            global_frame = frame.copy()
            status_checklist = current_status.copy()

# --- Rutas de la Aplicación Web ---
@app.route('/')
def index():
    """Sirve la página principal de la interfaz."""
    return render_template('index.html')

def frame_generator():
    """Generador que produce el stream de video para la página web."""
    global global_frame
    while True:
        with lock:
            if global_frame is None:
                continue
            # Codificar el frame como JPEG
            (flag, encodedImage) = cv2.imencode(".jpg", global_frame)
            if not flag:
                continue
        
        # Producir el stream byte por byte
        yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + 
              bytearray(encodedImage) + b'\r\n')
        time.sleep(0.05) # Limita el framerate para no saturar

@app.route('/video_feed')
def video_feed():
    """La ruta que sirve el stream de video."""
    return Response(frame_generator(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/status')
def status():
    """La ruta API que sirve el estado actual en formato JSON."""
    global status_checklist
    with lock:
        return jsonify(status_checklist)

if __name__ == '__main__':
    # Iniciar el hilo de procesamiento de video
    video_thread = threading.Thread(target=video_processing_thread)
    video_thread.daemon = True
    video_thread.start()
    
    # Iniciar la aplicación web
    app.run(debug=True, host='0.0.0.0', port=5000)
