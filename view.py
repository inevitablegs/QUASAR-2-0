import cv2
import numpy as np
import mediapipe as mp
from deepface import DeepFace
import os
from tqdm import tqdm  # Progress bar
from gaze2 import gaze  # Import gaze function

# Initialize MediaPipe Face Mesh
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1, refine_landmarks=True)

# Function to get facial landmarks using MediaPipe
def get_landmarks(frame):
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb_frame)

    if results.multi_face_landmarks:
        return results.multi_face_landmarks[0].landmark  # Returns first detected face's landmarks
    return None

# Function to process video (Crop + Emotion Detection + Gaze Tracking)
def process_video(input_path, output_path):
    cap = cv2.VideoCapture(input_path)

    if not cap.isOpened():
        print("Error: Could not open video.")
        return False

    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))  # Get total frames for progress bar

    print(f"Processing Video - Width: {frame_width}, Height: {frame_height}, FPS: {fps}, Total Frames: {total_frames}")

    # Define output video writer
    out = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (frame_width // 2, frame_height))

    frame_count = 0
    emotion_text = ""
    gaze_text = ""

    # Progress bar using tqdm
    with tqdm(total=total_frames, desc="Processing Video", unit="frame") as pbar:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # Step 1: Crop the right half of the frame
            right_half = frame[:, frame_width // 2:]

            # Step 2: Emotion Detection (Every second)
            if frame_count % int(fps) == 0:  # Process every second
                try:
                    analysis = DeepFace.analyze(right_half, actions=['emotion'], enforce_detection=False)
                    emotion = analysis[0]['dominant_emotion']

                    # Define confidence and stress level heuristics
                    confidence = 80 if emotion in ['happy', 'neutral', 'surprise'] else 50
                    stress_level = 90 if emotion in ['angry', 'fear', 'sad'] else 40

                    # Update text
                    emotion_text = f"Emotion: {emotion} | Confidence: {confidence}% | Stress: {stress_level}%"
                except Exception as e:
                    print("Error processing emotion:", e)

            # Step 3: Gaze Tracking using MediaPipe Face Mesh
            landmarks = get_landmarks(right_half)

            if landmarks:
                gaze_text = gaze(right_half, landmarks)  # Call gaze function with new landmarks
            else:
                gaze_text = "Gaze: No Face Detected"

            # Overlay emotion and gaze text
            cv2.putText(right_half, emotion_text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.putText(right_half, gaze_text, (20, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)

            # Write the processed frame
            out.write(right_half)
            frame_count += 1
            pbar.update(1)  # Update progress bar

    cap.release()
    out.release()
    return True


# Main Execution
input_video = "video1420092011.mp4"
final_output = "final_output2.mp4"

if process_video(input_video, final_output):
    print(f"Processing complete. Final output saved as {final_output}")