import tensorflow as tf
import tensorflow_hub as hub
import cv2
import numpy as np
import os
import time
from flask import Flask, Response, jsonify
from flask_cors import CORS

CONFIDENCE_THRESHOLD = 0.25

status_data = {
    "people_detected": None,
    "suspicious_people_detected": None,
    "dangerous_objects_detected": None
}

# Deshabilitar GPU para compatibilidad
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

app = Flask(__name__)
CORS(app)

# Cargar modelo de estimación de poses (MoveNet Multipose)
pose_model = hub.load('https://tfhub.dev/google/movenet/multipose/lightning/1')
movenet = pose_model.signatures['serving_default']

# Cargar el modelo de detección de objetos (SSD MobileNet)
detector_model = tf.saved_model.load("ssd_mobilenet_v2_fpnlite_640x640_coco17_tpu-8/saved_model")

# Definir las conexiones de la pose humana
EDGES = {
    (0, 1): 'm', (0, 2): 'c', (1, 3): 'm', (2, 4): 'c',
    (0, 5): 'm', (0, 6): 'c', (5, 7): 'm', (7, 9): 'm',
    (6, 8): 'c', (8, 10): 'c', (5, 6): 'y', (5, 11): 'm',
    (6, 12): 'c', (11, 12): 'y', (11, 13): 'm', (13, 15): 'm',
    (12, 14): 'c', (14, 16): 'c'
}

# Definir objetos peligrosos
dangerous_objects = ["knife", "scissors", "umbrella", "baseball bat", "baseball glove", "skateboard", "surfboard", "tennis racket"]

def draw_detections(frame, detections):
    """Dibuja cajas de detección de objetos."""
    for obj in detections:
        box = obj["box_points"]
        label = f"{obj['name']} ({obj['percentage_probability']:.1f}%)"
        cv2.rectangle(frame, (box[0], box[1]), (box[2], box[3]), (255, 0, 0), 2)
        cv2.putText(frame, label, (box[0], box[1] - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

def draw_keypoints(frame, keypoints, confidence_threshold=CONFIDENCE_THRESHOLD):
    """Dibuja los puntos clave de la pose humana."""
    y, x, _ = frame.shape
    shaped = np.squeeze(np.multiply(keypoints, [y, x, 1]))
    for kp in shaped:
        ky, kx, kp_conf = kp
        if kp_conf > confidence_threshold:
            cv2.circle(frame, (int(kx), int(ky)), 6, (0, 255, 0), -1)

def draw_connections(frame, keypoints, edges, confidence_threshold=CONFIDENCE_THRESHOLD):
    """Dibuja las conexiones entre los puntos clave de la pose humana."""
    y, x, _ = frame.shape
    shaped = np.squeeze(np.multiply(keypoints, [y, x, 1]))
    for edge, color in edges.items():
        p1, p2 = edge
        y1, x1, c1 = shaped[p1]
        y2, x2, c2 = shaped[p2]
        if c1 > confidence_threshold and c2 > confidence_threshold:
            cv2.line(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 0, 255), 4)

def detect_pose(keypoints):
    """Detecta comportamientos sospechosos basados en la pose."""
    left_shoulder, right_shoulder = keypoints[5], keypoints[6]
    left_elbow, right_elbow = keypoints[7], keypoints[8]
    left_wrist, right_wrist = keypoints[9], keypoints[10]
    left_hip, right_hip = keypoints[11], keypoints[12]
    left_knee, right_knee = keypoints[13], keypoints[14]

    if left_wrist[2] > 0.2 and right_wrist[2] > 0.2:
        if left_wrist[0] < left_shoulder[0] or right_wrist[0] < right_shoulder[0] or left_elbow[0] < left_shoulder[0] or right_elbow[0] < right_shoulder[0]:
            return "Sospechoso (1)"

    if left_knee[2] > 0.2 or right_knee[2] > 0.2:
        if left_knee[0] < left_shoulder[0] or right_knee[0] < right_shoulder[0]:
            return "Sospechoso (2)"
    
    if left_hip[2] > 0.2 or right_hip[2] > 0.2:
        if left_hip[0] < left_shoulder[0] or right_hip[0] < right_shoulder[0]:
            return "Sospechoso (3)"

    return "Normal"

def detect_objects(frame):
    """Detecta objetos peligrosos en el frame usando el modelo SSD MobileNet."""
    input_tensor = tf.convert_to_tensor(frame)
    input_tensor = input_tensor[tf.newaxis,...]

    # Detectar objetos
    detections = detector_model(input_tensor)

    # Extraer resultados
    boxes = detections['detection_boxes'][0].numpy()
    classes = detections['detection_classes'][0].numpy().astype(np.int32)
    scores = detections['detection_scores'][0].numpy()

    # Filtrar objetos peligrosos
    detected_objects = []
    for i in range(len(scores)):
        if scores[i] > 0.33:  # Solo objetos con alta probabilidad
            class_id = classes[i]
            if class_id == 1:  # Clase 1: persona
                label = "person"
                box = boxes[i]
                detected_objects.append({
                    "name": label,
                    "box_points": [int(box[1] * frame.shape[1]), int(box[0] * frame.shape[0]),
                                   int(box[3] * frame.shape[1]), int(box[2] * frame.shape[0])],
                    "percentage_probability": scores[i] * 100
                })
            elif class_id in dangerous_objects:
                label = dangerous_objects[class_id - 1]
                box = boxes[i]
                detected_objects.append({
                    "name": label,
                    "box_points": [int(box[1] * frame.shape[1]), int(box[0] * frame.shape[0]),
                                   int(box[3] * frame.shape[1]), int(box[2] * frame.shape[0])],
                    "percentage_probability": scores[i] * 100
                })
    return detected_objects

def process_pose_and_objects(frame, object_detection=False):
    """Procesa el frame para detectar poses y objetos peligrosos."""
    start_time = time.time()

    # Valores por defecto
    dangerous_objects_count = None
    suspicious_person_count = 0
    person_count = None

    if object_detection:
        detected_objects = detect_objects(frame)
        draw_detections(frame, detected_objects)
        dangerous_objects_count = sum(1 for obj in detected_objects if obj['name'] != "person")
        person_count = sum(1 for obj in detected_objects if obj['name'] == "person")
        print(f"Objetos peligrosos detectados: {dangerous_objects_count}")
        print(f"Personas detectadas: {person_count}")

    # Estimación de poses
    img = tf.image.resize_with_pad(tf.expand_dims(frame, axis=0), 192, 256)
    input_img = tf.cast(img, dtype=tf.int32)
    results = movenet(input_img)
    keypoints_with_scores = results['output_0'].numpy()[:, :, :51].reshape((6, 17, 3))

    for person in keypoints_with_scores:
        head = person[0]
        keypoint_count = sum(1 for keypoint in person if keypoint[2] > CONFIDENCE_THRESHOLD)
        if keypoint_count <= 5 or head[2] <= CONFIDENCE_THRESHOLD:
            continue
        
        pose_label = detect_pose(person)
        if "Sospechoso" in pose_label:
            suspicious_person_count += 1
        draw_connections(frame, person, EDGES, CONFIDENCE_THRESHOLD)
        draw_keypoints(frame, person, CONFIDENCE_THRESHOLD)

        if head[2] > CONFIDENCE_THRESHOLD:
            cv2.putText(frame, pose_label, (int(head[1] * frame.shape[1]), int(head[0] * frame.shape[0]) - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

    end_time = time.time()
    return frame, dangerous_objects_count, suspicious_person_count, person_count

def generate_video(camera_stream_url):
    """Genera el stream de video y procesa los frames."""
    cap = cv2.VideoCapture(camera_stream_url)

    if not cap.isOpened():
        return

    frame_count = 0
    last_dangerous_objects_count = 0
    last_suspicious_person_count = 0
    last_person_count = 0

    freeze_frame = None
    freeze_until = 0  # timestamp hasta el que se congela

    while True:
        now = time.time()

        if freeze_frame is not None and now < freeze_until:
            # Reenviar frame congelado
            frame_to_send = freeze_frame
        else:
            # Leer nuevo frame
            ret, frame = cap.read()
            if not ret:
                cap.release()
                cap = cv2.VideoCapture(camera_stream_url)
                continue

            frame, dangerous_objects_count, suspicious_person_count, person_count = process_pose_and_objects(frame, object_detection=(frame_count % 200 == 0))

            # Actualizar status
            status_data["dangerous_objects_detected"] = dangerous_objects_count if dangerous_objects_count is not None else last_dangerous_objects_count
            status_data["people_detected"] = person_count if person_count is not None else last_person_count
            status_data["suspicious_people_detected"] = suspicious_person_count if suspicious_person_count is not None else last_suspicious_person_count
            last_dangerous_objects_count = status_data["dangerous_objects_detected"]
            last_suspicious_person_count = status_data["suspicious_people_detected"]
            last_person_count = status_data["people_detected"]

            frame_to_send = frame

            if frame_count % 200 == 0:
                print(f"[FRAME {frame_count}] Congelando frame por 5 segundos")
                print(f"Objetos peligrosos: {dangerous_objects_count}")
                print(f"Personas: {person_count}")
                print(f"Sospechosas: {suspicious_person_count}")
                freeze_frame = frame.copy()
                freeze_until = now + 5  # Congela por 5 segundos

        _, buffer = cv2.imencode('.jpg', frame_to_send)
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

        frame_count += 1


        if frame_count % 500 == 0:
            cap.release()
            cap = cv2.VideoCapture(camera_stream_url)


@app.route('/status')
def status():
    """Devuelve el estado actual del sistema."""
    return jsonify(status_data)


@app.route('/video_feed')
def video_feed():
    """Devuelve el stream de video procesado."""
    # URL del stream de la cámara
    cameraStreamUrl = "http://master:master@150.244.57.136/axis-cgi/mjpg/video.cgi?resolution=640x480"
    return Response(generate_video(cameraStreamUrl), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
