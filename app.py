from flask import Flask, render_template, Response, request, jsonify
import numpy as np
import cv2
import time
import os

app = Flask(__name__)

# --- CONFIGURACIÓN ---
UPLOAD_FOLDER = 'referencias'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# --- ALMACENAMIENTO EN MEMORIA ---
latest_frame = None
status_data = {
    "CONEXION": ("Esperando agente...", "#ffc107"),
    "PANTALLA": ("Desconocido", "#6c757d"),
    "IMAGEN": ("N/A", "#6c757d"),
    "REFERENCIAS": (f"{len(os.listdir(UPLOAD_FOLDER))} cargadas", "#6c757d")
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload_frame', methods=['POST'])
def upload_frame():
    global latest_frame, status_data
    try:
        image_file = request.files['frame']
        image_data = np.frombuffer(image_file.read(), np.uint8)
        latest_frame = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
        status_data["CONEXION"] = ("Recibiendo", "#28a745")
        return jsonify(success=True)
    except Exception as e:
        status_data["CONEXION"] = ("Error", "#dc3545")
        return jsonify(success=False, error=str(e))

# --- NUEVA RUTA PARA SUBIR REFERENCIAS ---
@app.route('/upload_reference', methods=['POST'])
def upload_reference():
    global status_data
    if 'reference_image' not in request.files:
        return jsonify(success=False, error="No se encontró el archivo")
    
    file = request.files['reference_image']
    if file.filename == '':
        return jsonify(success=False, error="No se seleccionó ningún archivo")

    if file:
        filename = file.filename
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Aquí se recargaría la lógica de análisis con la nueva imagen
        print(f"Nueva referencia guardada: {filename}")
        status_data["REFERENCIAS"] = (f"{len(os.listdir(UPLOAD_FOLDER))} cargadas", "#28a745")
        
        return jsonify(success=True, filename=filename)

def frame_generator():
    while True:
        if latest_frame is not None:
            (flag, encodedImage) = cv2.imencode(".jpg", latest_frame)
            if flag:
                yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + 
                      bytearray(encodedImage) + b'\r\n')
        time.sleep(0.1)

@app.route('/video_feed')
def video_feed():
    return Response(frame_generator(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/status')
def status():
    return jsonify(status_data)
