import face_recognition
import cv2
import numpy as np
import os

def save_captured_face(roll_number, image_data):
    # Decoding and saving the captured image during registration
    with open(f'static/faces/{roll_number}.jpg', 'wb') as f:
        f.write(image_data)

def match_face(roll_number, frame):
    registered_face_path = f'static/faces/{roll_number}.jpg'
    if not os.path.exists(registered_face_path):
        print(f"Registered face not found for roll number {roll_number}.")
        return False

    # Load the registered face image
    registered_face = face_recognition.load_image_file(registered_face_path)
    registered_encoding = face_recognition.face_encodings(registered_face)

    if not registered_encoding:
        print(f"No face encoding found in the registered face for {roll_number}.")
        return False

    registered_encoding = registered_encoding[0]

    # Convert the live frame to RGB
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    live_encodings = face_recognition.face_encodings(frame_rgb)

    if not live_encodings:
        print("No face detected in the live frame.")
        return False

    # Compare the registered encoding with the live frame encodings
    match_results = face_recognition.compare_faces([registered_encoding], live_encodings[0])
    if match_results[0]:
        print(f"Face matched successfully for roll number {roll_number}.")
    else:
        print(f"Face did not match for roll number {roll_number}.")
    return match_results[0]


