import cv2
import mediapipe as mp
import numpy as np
import torch
from torchvision import transforms
from slowfast.utils.parser import load_config
from slowfast.models import build_model

# Inicializa MediaPipe Pose
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
mp_drawing = mp.solutions.drawing_utils

# Cargar el modelo preentrenado SlowFast en Kinetics-400
cfg = load_config("configs/Kinetics/SLOWFAST_8x8_R50.yaml")
model = build_model(cfg)
model.eval()

# Función para extraer keypoints
def extract_keypoints(landmarks):
    keypoints = []
    for point in mp_pose.PoseLandmark:
        kp = landmarks.landmark[point]
        keypoints.append([kp.x, kp.y, kp.z])
    return np.array(keypoints).flatten()

# Cargar imagen y procesar pose
filename = "1.jpeg"
image = cv2.imread(f"./input_images/{filename}")
image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
result = pose.process(image_rgb)

if result.pose_landmarks:
    keypoints = extract_keypoints(result.pose_landmarks)
    keypoints_tensor = torch.tensor(keypoints).unsqueeze(0).float()
    
    # Realizar la predicción con SlowFast
    with torch.no_grad():
        predictions = model(keypoints_tensor)
    
    # Obtener la etiqueta de la acción
    action_label = torch.argmax(predictions, dim=1).item()
    print(f"Acción detectada: {action_label}")
    
    # Dibujar la pose en la imagen
    mp_drawing.draw_landmarks(image, result.pose_landmarks, mp_pose.POSE_CONNECTIONS)
    output_path = f"./output_images/pose_detected_{filename}"
    cv2.imwrite(output_path, image)
    print(f"Imagen guardada en {output_path}")
else:
    print("No se detectó ninguna pose en la imagen.")
