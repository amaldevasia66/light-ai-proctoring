import threading
import time
import cv2
from utils.gaze_tracking.gaze_tracking import GazeTracking
import mediapipe as mp
from datetime import datetime
# Shared variables
frame_lock = threading.Lock()
shared_frame = None
stop_threads = False

# Initialize GazeTracking for eye tracking
gaze = GazeTracking()

# MediaPipe initialization for lip detection
mp_drawing = mp.solutions.drawing_utils
mp_face_mesh = mp.solutions.face_mesh

# Variables for gaze detection
not_center_start = None
alert_cooldown_start_gaze = None
alert_triggered_gaze = False
cooldown_time = 7

# Variables for lip detection
not_touching_lips_start = None
alert_cooldown_start_lips = None
alert_triggered_lips = False


def capture_frames():
    """Continuously captures frames from the webcam."""
    print("Capturing frame...")

    global shared_frame, stop_threads
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        stop_threads = True
        return

    while not stop_threads:
        ret, frame = cap.read()
        if ret:
            with frame_lock:
                shared_frame = frame.copy()
        else:
            print("Error: Could not read frame.")
            stop_threads = True
            break
    cap.release()


def gaze_detection():
    print("Processing frame for gaze detection...")
    """Performs gaze detection using GazeTracking."""
    global not_center_start, alert_cooldown_start_gaze, alert_triggered_gaze, stop_threads

    while not stop_threads:
        with frame_lock:
            if shared_frame is None:
                time.sleep(0.01)  # Prevent busy-waiting
                continue
            frame = shared_frame.copy()

        # Perform gaze tracking
        gaze.refresh(frame)
        frame = gaze.annotated_frame()
        text = ""

        if gaze.is_blinking():
            text = "Blinking"
        elif gaze.is_right():
            text = "Looking right"
        elif gaze.is_left():
            text = "Looking left"
        elif gaze.is_center():
            text = "Looking center"

        # Pupil coordinates and alert logic
        left_pupil = gaze.pupil_left_coords()
        right_pupil = gaze.pupil_right_coords()
        pupils_detected = left_pupil is not None and right_pupil is not None

        if pupils_detected and not gaze.is_center():
            if not not_center_start:
                not_center_start = time.time()
        else:
            not_center_start = None

        if not_center_start and (time.time() - not_center_start > 7):
            if not alert_triggered_gaze and (not alert_cooldown_start_gaze or time.time() - alert_cooldown_start_gaze > cooldown_time):
                print("Cheating Detected (Eye Tracking)!")
                alert_triggered_gaze = True
                alert_cooldown_start_gaze = time.time()

        if alert_cooldown_start_gaze and time.time() - alert_cooldown_start_gaze > cooldown_time:
            alert_triggered_gaze = False

        # Overlay text on the frame
        cv2.putText(frame, text, (90, 60), cv2.FONT_HERSHEY_DUPLEX, 1.6, (147, 58, 31), 2)
        cv2.putText(frame, "Left pupil:  " + str(left_pupil), (90, 130), cv2.FONT_HERSHEY_DUPLEX, 0.9, (147, 58, 31), 1)
        cv2.putText(frame, "Right pupil: " + str(right_pupil), (90, 165), cv2.FONT_HERSHEY_DUPLEX, 0.9, (147, 58, 31), 1)

        # Display the frame
        cv2.imshow("Gaze Detection", frame)
        if cv2.waitKey(1) & 0xFF == 27:  # ESC key
            stop_threads = True
            break


def lip_detection():
    print("Processing frame for lip detection...")
    """Performs lip detection and renders face mesh using MediaPipe."""
    global not_touching_lips_start, alert_cooldown_start_lips, alert_triggered_lips, stop_threads

    with mp_face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    ) as face_mesh:
        while not stop_threads:
            with frame_lock:
                if shared_frame is None:
                    time.sleep(0.01)  # Prevent busy-waiting
                    continue
                frame = shared_frame.copy()

            # Process frame for face mesh and lip detection
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(image)

            if results.multi_face_landmarks:
                for face_landmarks in results.multi_face_landmarks:
                    mp_drawing.draw_landmarks(
                        image=frame,
                        landmark_list=face_landmarks,
                        connections=mp_face_mesh.FACEMESH_TESSELATION,
                        landmark_drawing_spec=None,
                        connection_drawing_spec=mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=1, circle_radius=1),
                    )

                    # Lip detection logic
                    upper_lip = face_landmarks.landmark[13]
                    lower_lip = face_landmarks.landmark[14]
                    lip_distance = abs(upper_lip.y - lower_lip.y)

                    if lip_distance > 0.01:
                        if not not_touching_lips_start:
                            not_touching_lips_start = time.time()
                    else:
                        not_touching_lips_start = None

                    if not_touching_lips_start and (time.time() - not_touching_lips_start > 7):
                        if not alert_triggered_lips and (not alert_cooldown_start_lips or time.time() - alert_cooldown_start_lips > cooldown_time):
                            print("Cheating Detected (Lip Detection)!")
                            alert_triggered_lips = True
                            alert_cooldown_start_lips = time.time()

                    if alert_cooldown_start_lips and time.time() - alert_cooldown_start_lips > cooldown_time:
                        alert_triggered_lips = False

            # Display the frame with face mesh
            cv2.imshow("Lip Detection and Face Mesh", cv2.flip(frame, 1))
            if cv2.waitKey(1) & 0xFF == 27:  # ESC key
                stop_threads = True
                break


def start_combined_detection(stop_detection_flag):
    """Start threads for combined detection."""
    global stop_threads
    stop_threads = stop_detection_flag

    threads = [
        threading.Thread(target=capture_frames),
        threading.Thread(target=gaze_detection),
        threading.Thread(target=lip_detection),
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    cv2.destroyAllWindows()


def detect_cheating(frame):
    print("Detecting cheating...")
    if frame is None or frame.size == 0:
        print("Invalid frame received.")
        return False, False
    """Runs both gaze and lip detection on a single frame and returns results."""
    # Gaze Detection
    gaze.refresh(frame)
    gaze_cheating = not gaze.is_center()

    # Lip Detection
    with mp_face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    ) as face_mesh:
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb_frame)

        lip_cheating = False
        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                upper_lip = face_landmarks.landmark[13]
                lower_lip = face_landmarks.landmark[14]
                lip_distance = abs(upper_lip.y - lower_lip.y)
                if lip_distance > 0.01:
                    lip_cheating = True

    # Debugging output
    print(f"Frame analyzed. Gaze Cheating: {gaze_cheating}, Lip Cheating: {lip_cheating}")
    return gaze_cheating, lip_cheating



if __name__ == "__main__":
    start_combined_detection(False)
