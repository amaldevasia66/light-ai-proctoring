import cv2
import face_recognition
import time

cheating_logs = []

def start_proctoring(roll_number, login_face_path):
    registered_face_path = f'static/faces/{roll_number}.jpg'

    # Load the registered and login faces
    registered_image = face_recognition.load_image_file(registered_face_path)
    login_image = face_recognition.load_image_file(login_face_path)

    registered_face_encoding = face_recognition.face_encodings(registered_image)[0]
    login_face_encoding = face_recognition.face_encodings(login_image)[0]

    results = face_recognition.compare_faces([registered_face_encoding], login_face_encoding)
    return results[0]  # True if faces match

def track_eyeball_movement():
    """ Dummy function to track eyeball movement """
    cheating_logs.append("Eyeball movement detected at: " + time.strftime("%H:%M:%S"))
    return True  # Example of eyeball movement detected

def detect_lip_movement():
    """ Dummy function to detect lip movement """
    cheating_logs.append("Lip movement detected at: " + time.strftime("%H:%M:%S"))
    return True  # Example of lip movement detected
