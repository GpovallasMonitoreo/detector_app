from flask import Flask, render_template, Response, request, jsonify
import numpy as np
import cv2
import time
import os

app = Flask(__name__)

# --- CONFIGURACIÓN Y "BASE DE DATOS" EN MEMORIA ---
# En una app real, esto estaría en una base de datos como PostgreSQL o Redis.
# Por ahora, un diccionario en memoria es suficiente.
cameras_db = {} # Guardará la configuración de las cámaras. Ej: {"cam_1": "rtsp://..."}
latest_frames = {} # Guardará el último frame recibido de cada cámara.

@app.route('/')
def index():
    """Sirve la página principal de la interfaz."""
    return render_template('index.html')

# --- API PARA LA INTERFAZ WEB ---
@app.route('/api/cameras', methods=['GET', 'POST'])
def manage_cameras():
    """Permite a la interfaz web ver y añadir cámaras."""
    if request.method == 'POST':
        data = request.json
        if not data or 'name' not in data or 'url' not in data:
            return jsonify(success=False, error="Datos incompletos"), 400
        
        cam_id = f"cam_{len(cameras_db) + 1}"
        cameras_db[cam_id] = {'name': data['name'], 'url': data['url']}
        print(f"Cámara añadida: {cameras_db[cam_id]}")
        return jsonify(success=True, camera=cameras_db[cam_id])

    # Para el método GET, simplemente devolvemos la lista de cámaras
    return jsonify(cameras_db)

# --- API PARA EL AGENTE LOCAL ---
@app.route('/api/agent/config')
def get_agent_config():
    """El agente local llamará a esta ruta para saber a qué cámara conectarse."""
    # Para esta demo, el agente siempre controlará la primera cámara de la lista.
    if cameras_db:
        first_cam_id = list(cameras_db.keys())[0]
        return jsonify(cameras_db[first_cam_id])
    return jsonify({}) # Devuelve un objeto vacío si no hay cámaras configuradas

# --- RUTAS DE VIDEO (Ligeramente modificadas) ---
@app.route('/upload_frame', methods=['POST'])
def upload_frame():
    """Recibe un frame del agente local."""
    global latest_frames
    try:
        cam_id = request.form.get('cam_id', 'cam_1') # Asumimos cam_1 si no se especifica
        image_file = request.files['frame']
        image_data = np.frombuffer(image_file.read(), np.uint8)
        latest_frames[cam_id] = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
        return jsonify(success=True)
    except Exception as e:
        print(f"Error al recibir el frame: {e}")
        return jsonify(success=False, error=str(e))

def frame_generator(cam_id='cam_1'):
    """Generador que sirve el último frame de una cámara específica."""
    placeholder_image = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.putText(placeholder_image, "Esperando Stream...", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    while True:
        frame = latest_frames.get(cam_id)
        if frame is None:
            frame = placeholder_image
        
        (flag, encodedImage) = cv2.imencode(".jpg", frame)
        if flag:
            yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + 
                  bytearray(encodedImage) + b'\r\n')
        time.sleep(0.1)

@app.route('/video_feed')
def video_feed():
    """La ruta que sirve el stream de video a la interfaz."""
    return Response(frame_generator(), mimetype='multipart/x-mixed-replace; boundary=frame')
