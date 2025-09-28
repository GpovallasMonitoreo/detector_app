from flask import Flask, render_template, Response, request, jsonify
import numpy as np
import cv2

app = Flask(__name__)

# Almacenamiento simple en memoria para el último frame recibido
latest_frame = None

@app.route('/')
def index():
    """Sirve la página principal de la interfaz."""
    return render_template('index.html')

@app.route('/upload_frame', methods=['POST'])
def upload_frame():
    """Recibe un frame del agente local."""
    global latest_frame
    try:
        # Lee la imagen enviada en la petición
        image_file = request.files['frame']
        image_data = np.frombuffer(image_file.read(), np.uint8)
        latest_frame = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
        return jsonify(success=True)
    except Exception as e:
        print(f"Error al recibir el frame: {e}")
        return jsonify(success=False, error=str(e))

def frame_generator():
    """Generador que sirve el último frame recibido al frontend."""
    while True:
        if latest_frame is not None:
            (flag, encodedImage) = cv2.imencode(".jpg", latest_frame)
            if flag:
                yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + 
                      bytearray(encodedImage) + b'\r\n')
        # Si no hay frames, podemos enviar una imagen de "esperando"
        # O simplemente esperar.
        time.sleep(0.1)

@app.route('/video_feed')
def video_feed():
    """La ruta que sirve el stream de video a la interfaz."""
    return Response(frame_generator(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
