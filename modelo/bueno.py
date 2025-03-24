import tensorflow as tf
import tensorflow_hub as hub
import cv2
import numpy as np
import os
import time
from imageai.Detection import ObjectDetection

# Deshabilitar GPU para compatibilidad
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

# Cargar modelo de detección de objetos (ImageAI)
detector = ObjectDetection()
detector.setModelTypeAsRetinaNet()
detector.setModelPath("retinanet_resnet50_fpn_coco-eeacb38b.pth")
detector.useCPU()
detector.loadModel()

# Cargar modelo de estimación de poses (MoveNet Multipose)
model = hub.load('https://tfhub.dev/google/movenet/multipose/lightning/1')
movenet = model.signatures['serving_default']

# Definir las conexiones de la pose humana
EDGES = {
    (0, 1): 'm', (0, 2): 'c', (1, 3): 'm', (2, 4): 'c',
    (0, 5): 'm', (0, 6): 'c', (5, 7): 'm', (7, 9): 'm',
    (6, 8): 'c', (8, 10): 'c', (5, 6): 'y', (5, 11): 'm',
    (6, 12): 'c', (11, 12): 'y', (11, 13): 'm', (13, 15): 'm',
    (12, 14): 'c', (14, 16): 'c'
}

dangerous_objects = ["knife", "scissors", "umbrella", "baseball bat", "baseball glove", "skateboard", "surfboard", "tennis racket"]

def draw_detections(frame, detections):
    """Dibuja cajas de detección de objetos."""
    for obj in detections:
        box = obj["box_points"]
        label = f"{obj['name']} ({obj['percentage_probability']:.1f}%)"
        cv2.rectangle(frame, (box[0], box[1]), (box[2], box[3]), (255, 0, 0), 2)
        cv2.putText(frame, label, (box[0], box[1] - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

def draw_keypoints(frame, keypoints, confidence_threshold=0.1):
    """Dibuja los puntos clave de la pose."""
    y, x, _ = frame.shape
    shaped = np.squeeze(np.multiply(keypoints, [y, x, 1]))
    for kp in shaped:
        ky, kx, kp_conf = kp
        if kp_conf > confidence_threshold:
            cv2.circle(frame, (int(kx), int(ky)), 6, (0, 255, 0), -1)

def draw_connections(frame, keypoints, edges, confidence_threshold=0.1):
    """Dibuja las líneas de conexión del esqueleto."""
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
    left_wrist, right_wrist = keypoints[9], keypoints[10]
    left_hip, right_hip = keypoints[11], keypoints[12]
    left_knee, right_knee = keypoints[13], keypoints[14]

    if left_wrist[2] > 0.2 and right_wrist[2] > 0.2:
        if left_wrist[0] < left_shoulder[0] or right_wrist[0] < right_shoulder[0]:
            return "Sospechoso (1)"

    if left_knee[2] > 0.2 or right_knee[2] > 0.2:
        if left_knee[0] < left_shoulder[0] or right_knee[0] < right_shoulder[0]:
            return "Sospechoso (2)"
    
    if left_hip[2] > 0.2 or right_hip[2] > 0.2:
        if left_hip[0] < left_shoulder[0] or right_hip[0] < right_shoulder[0]:
            return "Sospechoso (3)"

    return "Normal"

def process_pose(frame):
    """Procesa la estimación de poses y mide el tiempo."""
    start_time = time.time()
    
    img = tf.image.resize_with_pad(tf.expand_dims(frame, axis=0), 192, 256)
    input_img = tf.cast(img, dtype=tf.int32)
    results = movenet(input_img)
    keypoints_with_scores = results['output_0'].numpy()[:, :, :51].reshape((6, 17, 3))
    person_count = 0
 
    for person in keypoints_with_scores:
        
        head = person[0]
        keypoint_count = sum(1 for keypoint in person if keypoint[2] > 0.33)
        if keypoint_count <= 5 or head[2] <= 0.33:
            continue
        
        pose_label = detect_pose(person)
        draw_connections(frame, person, EDGES, 0.33)
        draw_keypoints(frame, person, 0.33)

        # Posición de la etiqueta cerca de la cabeza
        if head[2] > 0.33:
            cv2.putText(frame, pose_label, (int(head[1] * frame.shape[1]), int(head[0] * frame.shape[0]) - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

    end_time = time.time()
    print(f"Tiempo de procesamiento de pose: {end_time - start_time:.4f} segundos")
    return frame, person_count

def capture_frames(camera_stream_url):
    # Inicializa el stream MJPEG
    cap = cv2.VideoCapture(camera_stream_url)

    if not cap.isOpened():
        print("Error al conectar con el stream de la cámara.")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error al leer el frame del stream.")
            break

        # Procesar pose
        frame, person_count = process_pose(frame)

        # Mostrar el video en tiempo real con las detecciones y poses
        cv2.imshow("Video en tiempo real", frame)
        print(f"Total de personas detectadas: {person_count}")

        # Salir si se presiona la tecla 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

# URL del stream de la cámara
cameraStreamUrl = "http://master:master@150.244.57.136/axis-cgi/mjpg/video.cgi?resolution=640x480"

# Procesar video y detectar objetos y poses en tiempo real
capture_frames(cameraStreamUrl)
