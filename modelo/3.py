import tensorflow as tf
import tensorflow_hub as hub
import cv2
import numpy as np

# Load MoveNet Multipose model
model = hub.load('https://tfhub.dev/google/movenet/multipose/lightning/1')
movenet = model.signatures['serving_default']

# Define edges between keypoints
EDGES = {
    (0, 1): 'm', (0, 2): 'c', (1, 3): 'm', (2, 4): 'c',
    (0, 5): 'm', (0, 6): 'c', (5, 7): 'm', (7, 9): 'm',
    (6, 8): 'c', (8, 10): 'c', (5, 6): 'y', (5, 11): 'm',
    (6, 12): 'c', (11, 12): 'y', (11, 13): 'm', (13, 15): 'm',
    (12, 14): 'c', (14, 16): 'c'
}

def draw_keypoints(frame, keypoints, confidence_threshold=0.1):
    y, x, _ = frame.shape
    shaped = np.squeeze(np.multiply(keypoints, [y, x, 1]))
    
    for kp in shaped:
        ky, kx, kp_conf = kp
        if kp_conf > confidence_threshold:
            cv2.circle(frame, (int(kx), int(ky)), 6, (0, 255, 0), -1)

def draw_connections(frame, keypoints, edges, confidence_threshold=0.1):
    y, x, _ = frame.shape
    shaped = np.squeeze(np.multiply(keypoints, [y, x, 1]))
    
    for edge, color in edges.items():
        p1, p2 = edge
        y1, x1, c1 = shaped[p1]
        y2, x2, c2 = shaped[p2]
        
        if c1 > confidence_threshold and c2 > confidence_threshold:
            cv2.line(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 0, 255), 4)

def loop_through_people(frame, keypoints_with_scores, edges, confidence_threshold=0.1):
    for person in keypoints_with_scores:
        draw_connections(frame, person, edges, confidence_threshold)
        draw_keypoints(frame, person, confidence_threshold)

def detect_pose(keypoints):
    """Detects the pose of a person based on keypoints."""
    left_shoulder, right_shoulder = keypoints[5], keypoints[6]
    left_wrist, right_wrist = keypoints[9], keypoints[10]
    left_hip, right_hip = keypoints[11], keypoints[12]
    left_knee, right_knee = keypoints[13], keypoints[14]
    
    shoulder_avg_y = (left_shoulder[0] + right_shoulder[0]) / 2
    hip_avg_y = (left_hip[0] + right_hip[0]) / 2
    knee_avg_y = (left_knee[0] + right_knee[0]) / 2
    
    if left_wrist[2] > 0.2 and right_wrist[2] > 0.2:
        if left_wrist[0] < left_shoulder[0] and right_wrist[0] < right_shoulder[0]:
            return "Arms Raised"
    
    if left_knee[2] > 0.2 and right_knee[2] > 0.2:
        if abs(left_knee[0] - hip_avg_y) < 0.1 and abs(right_knee[0] - hip_avg_y) < 0.1:
            return "Sitting"
        if left_knee[0] < hip_avg_y or right_knee[0] < hip_avg_y:
            return "Squatting"
    
    if hip_avg_y > shoulder_avg_y:
        return "Standing"
    
    return "Unknown"

def process_frame(frame):
    img = tf.image.resize_with_pad(tf.expand_dims(frame, axis=0), 384, 640)
    input_img = tf.cast(img, dtype=tf.int32)
    results = movenet(input_img)
    keypoints_with_scores = results['output_0'].numpy()[:, :, :51].reshape((6, 17, 3))
    
    detected_poses = []
    for person in keypoints_with_scores:
        pose = detect_pose(person)
        detected_poses.append(pose)
        
        # Get the position for labeling
        head = person[0]
        if head[2] > 0.2:  # Only label if confidence is high
            cv2.putText(frame, pose, (int(head[1] * frame.shape[1]), int(head[0] * frame.shape[0]) - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
    
    loop_through_people(frame, keypoints_with_scores, EDGES, 0.2)
    return frame, detected_poses

def process_video(input_video, output_video):
    cap = cv2.VideoCapture(input_video)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video, fourcc, 30.0, (int(cap.get(3)), int(cap.get(4))))
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        processed_frame, detected_poses = process_frame(frame)
        out.write(processed_frame)
    
    cap.release()
    out.release()
    cv2.destroyAllWindows()

def process_image(image_path):
    frame = cv2.imread(image_path)
    processed_frame, detected_poses = process_frame(frame)
    cv2.imwrite('output_image.jpg', processed_frame)
    return detected_poses

# Example usage:
process_video('novak.mp4', 'output.mp4')
#poses = process_image('./input_images/5.jpg')