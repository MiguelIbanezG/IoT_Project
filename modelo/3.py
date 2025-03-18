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
    left_wrist, right_wrist = keypoints[9], keypoints[10]
    left_hip, right_hip = keypoints[11], keypoints[12]
    left_knee, right_knee = keypoints[13], keypoints[14]

    if left_wrist[2] > 0.2 and right_wrist[2] > 0.2:
        if left_wrist[0] < left_hip[0] and right_wrist[0] < right_hip[0]:
            return "Sospechoso (1)"

    if left_knee[2] > 0.2 or right_knee[2] > 0.2:
        if left_knee[0] < left_hip[0] or right_knee[0] < right_hip[0]:
            return "Sospechoso (2)"

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
        pose_label = detect_pose(person)
        draw_connections(frame, person, EDGES, 0.2)
        draw_keypoints(frame, person, 0.2)

        # Posición de la etiqueta cerca de la cabeza
        head = person[0]
        if head[2] > 0.2:
            person_count += 1
            cv2.putText(frame, pose_label, (int(head[1] * frame.shape[1]), int(head[0] * frame.shape[0]) - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    end_time = time.time()
    print(f"Tiempo de procesamiento de pose: {end_time - start_time:.4f} segundos")
    return frame, person_count

def process_image(image_path, output_path):
    """Ejecuta detección de objetos y estimación de poses en la misma imagen con medición de tiempo."""
    total_person = 0
    frame = cv2.imread(image_path)

    # Medir tiempo de detección de objetos
    start_det = time.time()
    detections = detector.detectObjectsFromImage(input_image=image_path, minimum_percentage_probability=35)
    end_det = time.time()
    print(f"Tiempo de detección de objetos: {end_det - start_det:.4f} segundos")
    
    for obj in detections:
        if obj["name"] in dangerous_objects:
            print(f"Objeto peligroso detectado: {obj['name']}")
            cv2.putText(frame, f"{obj['name']}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        if obj["name"] == "person":
            total_person += 1

    # Procesar pose y medir tiempo
    start_pose = time.time()
    frame, person_count = process_pose(frame)
    end_pose = time.time()
    
    total_time = end_pose - start_det
    print(f"Tiempo total de procesamiento: {total_time:.4f} segundos")
    print(f"Total de personas detectadas: {total_person}")
    print(f"Total de personas procesadas: {person_count}")
    # Guardar imagen procesada
    cv2.imwrite(output_path, frame)
    return output_path

# Ejemplo de uso
input_path = "./processed_images/10.jpg"
output_path = "./output_image.jpg"
result = process_image(input_path, output_path)
print(f"Imagen procesada guardada en: {result}")
