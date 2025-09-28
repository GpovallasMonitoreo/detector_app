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

# --- ALMACENAMIENTO EN MEMORIA Y PLACEHOLDER ---
latest_frame = None
# Creamos una imagen negra de "Señal Perdida" para mostrarla cuando haya errores
placeholder_image = np.zeros((480, 640, 3), dtype=np.uint8)
cv2.putText(placeholder_image, "SEÑAL PERDIDA DEL AGENTE", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

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
        
        # --- PUNTO DE DIAGNÓSTICO CLAVE ---
        decoded_frame = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
        
        if decoded_frame is None:
            # Si la decodificación falla, lo imprimimos en los logs de Render
            print("ERROR CRITICO: cv2.imdecode fallo y no pudo decodificar la imagen recibida.")
            return jsonify(success=False, error="imdecode failed")
        
        latest_frame = decoded_frame
        status_data["CONEXION"] = ("Recibiendo", "#28a745")
        return jsonify(success=True)
        
    except Exception as e:
        status_data["CONEXION"] = ("Error en Servidor", "#dc3545")
        # Imprimimos cualquier otro error para poder verlo en los logs
        print(f"Error en /upload_frame: {e}")
        return jsonify(success=False, error=str(e))

@app.route('/upload_reference', methods=['POST'])
def upload_reference():
    # ... (Esta función no necesita cambios) ...
    global status_data
    if 'reference_image' not in request.files: return jsonify(success=False, error="No se encontró el archivo")
    file = request.files['reference_image']
    if file.filename == '': return jsonify(success=False, error="No se seleccionó ningún archivo")
    if file:
        filename = file.filename; filepath = os.path.join(UPLOAD_FOLDER, filename); file.save(filepath)
        print(f"Nueva referencia guardada: {filename}")
        status_data["REFERENCIAS"] = (f"{len(os.listdir(UPLOAD_FOLDER))} cargadas", "#28a745")
        return jsonify(success=True, filename=filename)

def frame_generator():
    while True:
        frame_to_send = None
        if latest_frame is not None:
            frame_to_send = latest_frame
        else:
            # Si no hay un frame válido, enviamos nuestra imagen de "Señal Perdida"
            frame_to_send = placeholder_image

        (flag, encodedImage) = cv2.imencode(".jpg", frame_to_send)
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
