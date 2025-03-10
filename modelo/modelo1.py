import os
import time
import shutil
import cv2
import mediapipe as mp
import numpy as np
from imageai.Detection import ObjectDetection

# Configurar la detección de objetos
detector = ObjectDetection()
detector.setModelTypeAsRetinaNet()
detector.setModelPath("retinanet_resnet50_fpn_coco-eeacb38b.pth")
detector.useCPU()
detector.loadModel()

# Configurar MediaPipe Pose
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
mp_drawing = mp.solutions.drawing_utils

INPUT_FOLDER = "./input_images"
OUTPUT_FOLDER = "./output_images"
PROCESSED_FOLDER = "./processed_images"
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

def determinar_estado(landmarks):
    try:
        hip_left = landmarks.landmark[mp_pose.PoseLandmark.LEFT_HIP]
        hip_right = landmarks.landmark[mp_pose.PoseLandmark.RIGHT_HIP]
        knee_left = landmarks.landmark[mp_pose.PoseLandmark.LEFT_KNEE]
        knee_right = landmarks.landmark[mp_pose.PoseLandmark.RIGHT_KNEE]
        ankle_left = landmarks.landmark[mp_pose.PoseLandmark.LEFT_ANKLE]
        ankle_right = landmarks.landmark[mp_pose.PoseLandmark.RIGHT_ANKLE]
        shoulder_left = landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER]
        shoulder_right = landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER]
        wrist_left = landmarks.landmark[mp_pose.PoseLandmark.LEFT_WRIST]
        wrist_right = landmarks.landmark[mp_pose.PoseLandmark.RIGHT_WRIST]
        nose = landmarks.landmark[mp_pose.PoseLandmark.NOSE]

        base = abs(nose.y - (ankle_left.y + ankle_right.y) / 2)
        base_01 = 0.1 * base
        base_02 = 0.2 * base

        if (hip_left.y - shoulder_left.y) < base_02 or (hip_right.y - shoulder_right.y) < base_02:
            return "Tumbado"
        
        if (knee_left.y - hip_left.y) < base_02 or (knee_right.y - hip_right.y) < base_02:# and (ankle_left.y > knee_left.y or ankle_right.y > knee_right.y):
            return "Arrodillado"
        
        if knee_left.y > hip_left.y and knee_right.y > hip_right.y:
            return "De_pie"
        
        if ((wrist_left.y - nose.y < base_02) or (wrist_right.y - nose.y < base_02)) and ((wrist_left.x - nose.x < base_02) or (wrist_right.x - nose.x < base_02)):
            return "Tapándose_la_cara"
        
        if wrist_left.y < shoulder_left.y or wrist_right.y < shoulder_right.y:
            return "Agresivo"
        
        if abs(ankle_left.y - ankle_right.y) > base_02 and (wrist_left.y < shoulder_left.y or wrist_right.y < shoulder_right.y):
            return "Corriendo_o_Saltando"
        
        return "Relajado"
    except Exception as e:
        print(f"Error al determinar estado: {e}")
        return "Desconocido"

while True:
    try:
        images = [f for f in os.listdir(INPUT_FOLDER) if f.endswith(('.jpg', '.png', '.jpeg'))]
        
        for filename in images:
            print(f"Procesando imagen: {filename}")
            input_path = os.path.join(INPUT_FOLDER, filename)
            output_path = os.path.join(OUTPUT_FOLDER, f"processed_{filename}")

            detections = detector.detectObjectsFromImage(input_image=input_path, output_image_path=output_path, minimum_percentage_probability=35)
            image_detectada = cv2.imread(output_path)

            person_counter = 1
            for eachObject in detections:
                if eachObject['name'] == 'person':
                    x1, y1, x2, y2 = eachObject['box_points']
                    cropped_image = image_detectada[y1:y2, x1:x2]
                    cropped_image_rgb = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2RGB)
                    result = pose.process(cropped_image_rgb)
                    estado = "Desconocido"

                    if result.pose_landmarks:
                        mp_drawing.draw_landmarks(cropped_image, result.pose_landmarks, mp_pose.POSE_CONNECTIONS)
                        estado = determinar_estado(result.pose_landmarks)
                        font = cv2.FONT_HERSHEY_SIMPLEX
                        cv2.putText(cropped_image, estado, (10, 30), font, 1, (0, 255, 0), 2, cv2.LINE_AA)
                    
                    print(f"Estado de la persona {person_counter}: {estado}")

                    if estado != "Desconocido":
                        output_persona_path = os.path.join(OUTPUT_FOLDER, f'persona_{person_counter}_pose_annotated_{estado}.jpeg')
                        cv2.imwrite(output_persona_path, cropped_image)
                        print(f"Imagen guardada: {output_persona_path}")
                    person_counter += 1
            
            # Mover imagen procesada
            shutil.move(input_path, os.path.join(PROCESSED_FOLDER, filename))
        
        time.sleep(5)  # Espera 5 segundos antes de revisar nuevamente
    
    except KeyboardInterrupt:
        print("Proceso interrumpido por el usuario.")
        break  # Termina el bucle de manera ordenada si se presiona Ctrl+C
